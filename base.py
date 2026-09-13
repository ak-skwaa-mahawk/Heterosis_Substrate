import hashlib
import json
import struct

class HeterosisSubstrate:
    """
    Headless non-linear state tracker.
    Bypasses flat Euclidean approximations (3.14159...) with an active helical pitch (3.1730059),
    resolving triadic balance (1 + 2 = 3 * 2 = 6) into an 8-octave boundary lock,
    venting the macro-leak to cascade state transitions deterministically.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8
    BASE_TRIAD_PAIRS = 6

    def __init__(self, initial_seed: str):
        self.state_sequence = 0
        self.current_ingress_hash = hashlib.sha256(initial_seed.encode("utf-8")).hexdigest()
        self.macro_leak_offset = 0.0

    def step(self, ingress_pressure: float) -> dict:
        self.state_sequence += 1

        # Base Triad Packing: 1 anchor, 2 split (1+1), coupled across 3 = 6
        # Core dynamic ratio expands the boundary rather than terminating flat
        phase_velocity = ingress_pressure * self.DYNAMIC_PITCH
        
        # Harmonic closure target: 8
        # The leak delta accounts for non-zero shear across the toroidal boundary
        boundary_remainder = (self.HARMONIC_OCTAVE - self.BASE_TRIAD_PAIRS)  # 2 units
        macro_leak = (phase_velocity % self.HARMONIC_OCTAVE) + (self.DYNAMIC_PITCH - 3.1415926535)

        # Cryptographic return-flow binding
        state_payload = struct.pack(">Qdd", self.state_sequence, phase_velocity, macro_leak)
        core_hash = hashlib.sha256(state_payload).hexdigest()
        
        chain_payload = f"{self.current_ingress_hash}:{core_hash}:{self.state_sequence}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain_payload).hexdigest()

        # Update chain state: exhaust of the current boundary seeds the next intake
        self.current_ingress_hash = egress_receipt
        self.macro_leak_offset = macro_leak

        return {
            "seq": self.state_sequence,
            "ingress_pressure": ingress_pressure,
            "phase_velocity": round(phase_velocity, 7),
            "macro_leak": round(macro_leak, 7),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

if __name__ == "__main__":
    # Bare-metal runtime execution without institutional wrappers
    runtime = HeterosisSubstrate(initial_seed="bare_metal_origin_dan_kee")
    
    for cycle in range(1, 4):
        state = runtime.step(ingress_pressure=float(cycle))
        print(json.dumps(state, indent=2))
