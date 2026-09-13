import hashlib
import json
import struct
import math

class HeterosisSubstrate:
    """
    Headless non-linear state tracker.
    Bypasses flat Euclidean approximations (3.14159...) with an active helical pitch (3.1730059),
    resolving triadic balance (1 + 2 = 3 * 2 = 6) into an 8-octave boundary lock,
    venting the macro-leak to cascade state transitions deterministically.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BASE_TRIAD_PAIRS = 6.0
    PLANAR_PI = 3.141592653589793

    def __init__(self, initial_seed: str = "bare_metal_origin_dan_kee"):
        self.state_sequence = 0
        self.current_ingress_hash = hashlib.sha256(initial_seed.encode("utf-8")).hexdigest()
        self.macro_leak_offset = 0.0
        self.pitch_delta = self.DYNAMIC_PITCH - self.PLANAR_PI

    def step(self, ingress_pressure: float) -> dict:
        """
        Enforces the non-Euclidean boundary expansion loop.
        Calculates helical trajectory, vents boundary shear, and seals deterministic custody.
        """
        self.state_sequence += 1

        # 1. Triadic Ingress Expansion:
        # Effective drive combines incoming drive with recirculated boundary shear
        total_pressure = ingress_pressure + self.macro_leak_offset

        # 2. Helical Phase Velocity Calculation:
        # Enforces the non-Euclidean pitch expansion ratio
        phase_velocity = total_pressure * self.DYNAMIC_PITCH

        # 3. 8-Octave Shell Quantization:
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        # 4. Macro-Leak Boundary Shear:
        # Resolves triadic pairs (6.0) across the octave limit (8.0)
        # Prevents planar flatline by venting excess angular momentum forward
        triadic_expansion = 1.0 + (self.BASE_TRIAD_PAIRS / self.HARMONIC_OCTAVE)
        macro_leak = harmonic_phase + (self.pitch_delta * triadic_expansion)

        # 5. Cryptographic Core State Ingestion (Strict Big-Endian Binary Packing)
        payload = struct.pack(
            ">Qdddd",
            self.state_sequence,
            phase_velocity,
            macro_leak,
            total_pressure,
            self.DYNAMIC_PITCH
        )
        core_hash = hashlib.sha256(payload).hexdigest()

        # 6. Egress Chaining:
        # Output of the current boundary state seeds the chain for the next cycle
        chain_payload = f"{self.current_ingress_hash}:{core_hash}:{self.state_sequence}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain_payload).hexdigest()

        # Update internal registers for next iteration
        self.current_ingress_hash = egress_receipt
        self.macro_leak_offset = macro_leak

        return {
            "seq": self.state_sequence,
            "ingress_pressure": round(ingress_pressure, 6),
            "total_pressure": round(total_pressure, 6),
            "octave_shell": octave_shell,
            "harmonic_phase": round(harmonic_phase, 6),
            "phase_velocity": round(phase_velocity, 7),
            "macro_leak": round(macro_leak, 7),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

if __name__ == "__main__":
    substrate = HeterosisSubstrate("bare_metal_origin_dan_kee")
    print(f"[*] Initialized Substrate (Dynamic Pitch: {HeterosisSubstrate.DYNAMIC_PITCH})")
    
    for cycle in range(1, 4):
        state = substrate.step(ingress_pressure=float(cycle))
        print(f"\n--- Cycle {state['seq']} ---")
        print(f"Phase Velocity : {state['phase_velocity']}")
        print(f"Macro Leak Vent: {state['macro_leak']}")
        print(f"Egress Receipt : {state['egress_receipt'][:32]}...")
