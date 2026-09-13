import hashlib
import json
import os
import struct

class ChiralDriftCompensator:
    """
    Sub-harmonic Phase Drift Compensator.
    Consumes live state metrics and stored RUN_TRACE.json histories
    to compute counter-precession torque, damping angular slip off the 3.1730059 centerline.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    INTEGRAL_DECAY = 0.92
    DAMPING_RATIO = 0.186412

    def __init__(self, target_pitch=3.1730059, damping_ratio=0.186412):
        self.CENTER_LINE = target_pitch
        self.DAMPING_RATIO = damping_ratio
        self.slip_integral = 0.0
        self.accumulated_drift = 0.0

    def calculate_precession(self, state: dict) -> dict:
        """
        Inline pipeline interface expected by orchestrator.py and audit_harness.py.
        Computes the micro-precession restoring force for real-time stepping.
        """
        seq = state.get("seq", 0)
        phase_vel = state.get("phase_velocity", 0.0)
        net_press = state.get("net_pressure", 1.0)
        leak = state.get("chiral_vent", state.get("macro_leak", 0.0))

        # Expected velocity along the dynamic pitch helix
        expected_velocity = net_press * self.DYNAMIC_PITCH
        instantaneous_slip = phase_vel - expected_velocity

        # Leaky accumulation over runtime history
        self.slip_integral = (self.slip_integral * self.INTEGRAL_DECAY) + instantaneous_slip

        # Dynamic counter-precession combining proportional slip and accumulated torque
        restoring_precession = -(0.045 * instantaneous_slip + 0.015 * self.slip_integral)
        clamped_precession = max(min(restoring_precession, 1.0), -1.0)

        # Attestation payload sealing
        comp_payload = struct.pack(">Qddd", seq, instantaneous_slip, self.slip_integral, clamped_precession)
        comp_hash = hashlib.sha256(comp_payload).hexdigest()
        receipt = hashlib.sha256(f"COMP:{seq}:{comp_hash}:{clamped_precession:.7f}".encode("utf-8")).hexdigest()

        return {
            "seq": seq,
            "instantaneous_slip": round(instantaneous_slip, 7),
            "accumulated_integral": round(self.slip_integral, 7),
            "restoring_precession": round(clamped_precession, 7),
            "compensation_receipt": receipt
        }

    def compute_counter_torque(self, current_leak: float, sequence_id: int) -> float:
        """
        Direct scalar interface for damping harmonic slip from isolated leak metrics.
        """
        drift_velocity = current_leak * (self.CENTER_LINE / self.HARMONIC_OCTAVE)
        self.accumulated_drift += drift_velocity
        torque = -(drift_velocity * self.DAMPING_RATIO) - (self.accumulated_drift * 0.01)
        return float(max(min(torque, 1.0), -1.0))

    def analyze_trace_file(self, trace_path="RUN_TRACE.json") -> float:
        """
        Audits stored state records to calculate trailing counter-precession torque.
        """
        if not os.path.exists(trace_path):
            return 0.0

        try:
            with open(trace_path, "r") as f:
                trace_data = json.load(f)
            if not trace_data:
                return 0.0

            recent_steps = trace_data[-5:]
            total_leak = sum(step.get("macro_leak", 0.0) for step in recent_steps)
            mean_leak = total_leak / len(recent_steps)
            last_seq = trace_data[-1].get("seq", 0)

            return self.compute_counter_torque(mean_leak, last_seq)
        except (json.JSONDecodeError, IOError, ZeroDivisionError):
            return 0.0

# Backward compatibility alias
DriftCompensator = ChiralDriftCompensator

if __name__ == "__main__":
    compensator = ChiralDriftCompensator()
    sample_leak = 0.412895
    torque = compensator.compute_counter_torque(sample_leak, sequence_id=1)
    print(f"[*] Calculated Counter-Precession Torque: {torque:.7f}")

    # Test inline step interface
    test_state = {"seq": 1, "phase_velocity": 3.20, "net_pressure": 1.0, "macro_leak": sample_leak}
    telemetry = compensator.calculate_precession(test_state)
    print(f"[+] Inline Precession Receipt: {telemetry['compensation_receipt'][:32]}...")
