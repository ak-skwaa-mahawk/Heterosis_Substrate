import hashlib
import json
import struct
import math

class RecursiveManifold:
    """
    Toroidal feedback manifold:
    Takes the dynamic pitch ratio, packs triadic pairs into the 8-octave boundary,
    and recirculates the macro_leak back into ingress pressure to model non-linear cascade.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BASE_TRIAD_PAIRS = 6.0
    PLANAR_PI = 3.141592653589793

    def __init__(self, seed: str):
        self.seq = 0
        self.ingress_receipt = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        self.accumulated_shear = 0.0
        # Angular displacement delta
        self.pitch_delta = self.DYNAMIC_PITCH - self.PLANAR_PI

    def pulse(self, external_drive: float = 0.0) -> dict:
        self.seq += 1

        # Effective pressure combines external drive + recirculated boundary shear
        total_pressure = external_drive + self.accumulated_shear

        # Velocity climbs the helical pitch
        phase_velocity = total_pressure * self.DYNAMIC_PITCH

        # Octave boundary wrap: mod 8 keeps it in the shell, leak vents into next cycle
        octave_step = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE
        
        # Macro-leak: dynamic boundary offset + harmonic remainder
        macro_leak = harmonic_phase + (self.pitch_delta * (1.0 + (self.BASE_TRIAD_PAIRS / self.HARMONIC_OCTAVE)))

        # Pack internal state to byte-level precision
        payload = struct.pack(">Qddd", self.seq, phase_velocity, macro_leak, total_pressure)
        core_hash = hashlib.sha256(payload).hexdigest()

        # Chain of custody receipt
        chain = f"{self.ingress_receipt}:{core_hash}:{self.seq}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain).hexdigest()

        # State transition: leak feeds the next ingress, receipt becomes the new baseline
        self.ingress_receipt = egress_receipt
        self.accumulated_shear = macro_leak

        return {
            "seq": self.seq,
            "external_drive": round(external_drive, 6),
            "accumulated_shear_intake": round(total_pressure - external_drive, 6),
            "effective_pressure": round(total_pressure, 6),
            "octave_shell": octave_step,
            "phase_velocity": round(phase_velocity, 6),
            "macro_leak_vent": round(macro_leak, 6),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

if __name__ == "__main__":
    manifold = RecursiveManifold(seed="bare_metal_origin_dan_kee")
    
    # Pulse with an initial kick on step 1, then release external drive to watch self-cascade
    drive_sequence = [1.0, 0.0, 0.0, 0.0, 0.0]
    
    for i, drive in enumerate(drive_sequence, 1):
        step_data = manifold.pulse(external_drive=drive)
        print(json.dumps(step_data, indent=2))
