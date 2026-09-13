import hashlib
import json
import struct

class SubstrateTripwire:
    """
    Real-time anomalous divergence detector and chiral circuit breaker.
    Combines acceleration gradient audits, static envelope bounds,
    and dynamic pitch disparity validation with 180-degree counter-torque damping.
    """
    MAX_PERMISSIBLE_ACCELERATION = 32.0
    SHEAR_DISSIPATION_LIMIT = 24.0
    VELOCITY_UPPER_BOUND = 48.0
    VELOCITY_LOWER_BOUND = 0.0001
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0

    def __init__(self):
        self.tripped = False
        self.last_velocity = 0.0
        self.incident_receipt = None
        self.violation_count = 0

    def evaluate_boundary(self, audit_target: dict) -> tuple:
        """
        Audits state telemetry against physical invariants and boundary bounds.
        Returns: (is_safe: bool, damping_torque: float, diagnostic_code: str)
        """
        seq = audit_target.get("seq", 0)
        current_vel = float(audit_target.get("phase_velocity", 0.0))
        chiral_vent = float(audit_target.get("chiral_vent", audit_target.get("macro_leak_vent", 0.0)))
        net_press = float(audit_target.get("net_pressure", 1.0))

        # 1. Absolute Velocity Envelope Check
        if current_vel > self.VELOCITY_UPPER_BOUND:
            return self._trigger_tripwire(seq, "ERR_VELOCITY_OVERFLOW", current_vel, current_vel - self.VELOCITY_UPPER_BOUND)

        if current_vel < self.VELOCITY_LOWER_BOUND:
            # Inject positive restoring torque to prevent stall
            self.violation_count += 1
            return (False, 0.1 + (self.VELOCITY_LOWER_BOUND - current_vel), "ERR_VELOCITY_STALL")

        # 2. Dynamic Acceleration Gradient Inspection
        acceleration = abs(current_vel - self.last_velocity)
        if acceleration > self.MAX_PERMISSIBLE_ACCELERATION:
            return self._trigger_tripwire(seq, "ACCEL_RUNAWAY", current_vel, acceleration)

        # 3. Shear Boundary Violation
        if chiral_vent > self.SHEAR_DISSIPATION_LIMIT:
            return self._trigger_tripwire(seq, "SHEAR_OVERFLOW", current_vel, chiral_vent)

        # 4. Dynamic Pitch Disparity Check
        expected_vel_approx = net_press * self.DYNAMIC_PITCH
        if abs(current_vel - expected_vel_approx) > 1.5:
            return self._trigger_tripwire(seq, "PITCH_DISPARITY", current_vel, net_press)

        # State within nominal stability envelope
        self.last_velocity = current_vel
        return (True, 0.0, "NOMINAL_STABILITY")

    def _trigger_tripwire(self, seq: int, reason: str, velocity: float, anomaly_val: float) -> tuple:
        self.tripped = True
        self.violation_count += 1

        # 180-degree counter-vortex damping torque
        damping_torque = -(velocity * 0.75)

        # Forge immutable binary incident receipt
        incident_bytes = struct.pack(">Qdd", seq, velocity, anomaly_val)
        fault_hash = hashlib.sha256(incident_bytes).hexdigest()
        chain = f"INCIDENT:{seq}:{reason}:{fault_hash}".encode("utf-8")
        self.incident_receipt = hashlib.sha256(chain).hexdigest()

        return (False, damping_torque, reason)

if __name__ == "__main__":
    sentinel = SubstrateTripwire()
    print("[*] Substrate Sentinel active.")

    # Nominal check
    nominal = {"seq": 1, "phase_velocity": 3.1730059, "net_pressure": 1.0, "chiral_vent": 0.5}
    safe, damp, code = sentinel.evaluate_boundary(nominal)
    print(f"Test 1 (Nominal): Safe={safe}, Code={code}, Damp={damp}")

    # Rupture check
    rupture = {"seq": 2, "phase_velocity": 60.0, "net_pressure": 1.0, "chiral_vent": 1.0}
    safe, damp, code = sentinel.evaluate_boundary(rupture)
    print(f"Test 2 (Rupture): Safe={safe}, Code={code}, Damp={damp:.4f}")
    print(f" └── Incident Receipt: {sentinel.incident_receipt}")
