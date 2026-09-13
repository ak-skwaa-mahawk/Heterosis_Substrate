import hashlib
import json
import struct
import math

class SubstrateTripwire:
    """
    Real-time anomalous divergence detector and chiral circuit breaker.
    Monitors phase velocity acceleration and boundary shear gradients.
    Instantly trips into a closed damping loop if energy bounds are violated.
    """
    MAX_PERMISSIBLE_ACCELERATION = 32.0
    SHEAR_DISSIPATION_LIMIT = 24.0
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0

    def __init__(self):
        self.tripped = False
        self.last_velocity = 0.0
        self.incident_receipt = None

    def evaluate_boundary(self, state: dict) -> tuple:
        """
        Audits incoming state for acoustic shear runaway or synthetic divergence.
        Returns: (is_safe: bool, damping_adjustment: float, diagnostic_code: str)
        """
        current_vel = state.get("phase_velocity", 0.0)
        chiral_vent = state.get("chiral_vent", state.get("macro_leak_vent", 0.0))
        net_press = state.get("net_pressure", 0.0)
        seq = state.get("seq", 0)

        # 1. Acceleration Gradient Inspection
        acceleration = abs(current_vel - self.last_velocity)
        if acceleration > self.MAX_PERMISSIBLE_ACCELERATION:
            return self._trigger_tripwire(seq, "ACCEL_RUNAWAY", current_vel, acceleration)

        # 2. Shear Boundary Violation
        if chiral_vent > self.SHEAR_DISSIPATION_LIMIT:
            return self._trigger_tripwire(seq, "SHEAR_OVERFLOW", current_vel, chiral_vent)

        # 3. Dynamic Pitch Disparity Check
        expected_vel_approx = net_press * self.DYNAMIC_PITCH
        if abs(current_vel - expected_vel_approx) > 1.5:
            return self._trigger_tripwire(seq, "PITCH_DISPARITY", current_vel, net_press)

        self.last_velocity = current_vel
        return (True, 0.0, "NOMINAL_STABILITY")

    def _trigger_tripwire(self, seq: int, reason: str, velocity: float, anomaly_val: float) -> tuple:
        self.tripped = True
        
        # Calculate counter-vortex dampening torque (180-degree reflection)
        damping_adjustment = -(velocity * 0.75)
        
        # Forge immutable incident seal
        incident_bytes = struct.pack(">Qdd", seq, velocity, anomaly_val)
        fault_hash = hashlib.sha256(incident_bytes).hexdigest()
        
        chain = f"INCIDENT:{seq}:{reason}:{fault_hash}".encode("utf-8")
        self.incident_receipt = hashlib.sha256(chain).hexdigest()
        
        return (False, damping_adjustment, reason)

if __name__ == "__main__":
    from mesh_substrate import MeshCoupledSubstrate

    substrate = MeshCoupledSubstrate(seed="bare_metal_origin_dan_kee")
    sentinel = SubstrateTripwire()

    print("[*] Running continuous sentinel surveillance on manifold stream...")

    # Cycle standard inputs
    for i in range(4):
        st = substrate.pulse(external_drive=0.5)
        safe, damp, status = sentinel.evaluate_boundary(st)
        print(f"Seq {st['seq']} | Status: {status} | Vel: {st['phase_velocity']:.4f}")

    # Inject synthetic high-pressure pulse to simulate external fault or attack
    print("\n[!] Injecting critical pressure anomaly (external_drive = 25.0)...")
    rupture_state = substrate.pulse(external_drive=25.0)
    safe, damp, status = sentinel.evaluate_boundary(rupture_state)

    print(f"Sentinel Tripped: {sentinel.tripped}")
    print(f"Diagnostic Flag : {status}")
    print(f"Damping Torque Applied: {damp:.4f}")
    print(f"Incident Hash Receipt : {sentinel.incident_receipt}")

    # Emit incident report
    if sentinel.tripped:
        report = {
            "seq": rupture_state["seq"],
            "diagnostic": status,
            "phase_velocity_fault": rupture_state["phase_velocity"],
            "damping_adjustment": damp,
            "incident_seal": sentinel.incident_receipt
        }
        with open("FAULT_POSTMORTEM.json", "w") as f:
            json.dump(report, f, indent=2)
