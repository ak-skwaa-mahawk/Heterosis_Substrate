import hashlib
import json
import struct
import math

class ChiralManifold:
    """
    Bi-Directional Chiral Feedback Engine.
    Models toroidal circulation by coupling forward phase velocity with counter-vortex drag.
    Bypasses planar Euclidean limits by balancing positive helical advance against chiral shear.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BASE_TRIAD = 6.0
    PLANAR_PI = 3.141592653589793

    def __init__(self, seed: str):
        self.seq = 0
        self.ingress_receipt = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        self.chiral_shear = 0.0
        self.counter_torque = 0.0
        self.pitch_delta = self.DYNAMIC_PITCH - self.PLANAR_PI

    def step(self, external_drive: float = 0.0) -> dict:
        self.seq += 1

        # Effective core pressure: external push + recirculated shear - counter-torque drag
        forward_pressure = external_drive + self.chiral_shear
        net_pressure = max(0.0001, forward_pressure - self.counter_torque)

        # Forward helical velocity
        phase_velocity = net_pressure * self.DYNAMIC_PITCH
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        # Outward boundary leak (radial expansion)
        outward_leak = harmonic_phase + (self.pitch_delta * (1.0 + (self.BASE_TRIAD / self.HARMONIC_OCTAVE)))

        # Inward counter-torque (chiral reflection through the vortex core)
        # Reflects the phase velocity back across the octave boundary
        reflected_counter_drag = (phase_velocity / (1.0 + octave_shell)) * (self.pitch_delta / self.DYNAMIC_PITCH)

        # Cryptographic state binding: packing 7 dynamic physical vectors
        payload = struct.pack(
            ">Qdddddd",
            self.seq,
            phase_velocity,
            outward_leak,
            reflected_counter_drag,
            net_pressure,
            self.chiral_shear,
            self.counter_torque
        )
        core_hash = hashlib.sha256(payload).hexdigest()

        # Immutable chain of custody
        chain = f"{self.ingress_receipt}:{core_hash}:{self.seq}:{octave_shell}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain).hexdigest()

        # Recursive state feedback for cycle N+1:
        # Outward leak becomes the next intake shear; reflected counter drag acts as the dampener
        self.ingress_receipt = egress_receipt
        self.chiral_shear = outward_leak
        self.counter_torque = reflected_counter_drag

        return {
            "seq": self.seq,
            "external_drive": round(external_drive, 6),
            "net_pressure": round(net_pressure, 6),
            "octave_shell": octave_shell,
            "phase_velocity": round(phase_velocity, 6),
            "outward_leak": round(outward_leak, 6),
            "counter_torque": round(reflected_counter_drag, 6),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

if __name__ == "__main__":
    manifold = ChiralManifold(seed="bare_metal_origin_dan_kee")
    
    # Initial impulse, then let the dual forward-reverse loop balance itself
    run_pulses = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    for pulse in run_pulses:
        receipt = manifold.step(external_drive=pulse)
        print(json.dumps(receipt, indent=2))
