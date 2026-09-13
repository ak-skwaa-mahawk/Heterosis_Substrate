import hashlib
import json
import struct
import math

class ResonanceManifold:
    """
    Triadic Phase-Locking and Harmonic Entrainment Substrate.
    Detects critical nodal crossings across the 8-octave boundary.
    Dynamically switches between kinetic dissipation and potential compression
    to maintain sustained equilibrium without external energy input.
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
        self.accumulated_potential = 0.0
        self.resonance_mode = "EXPANSION"

    def step(self, external_drive: float = 0.0) -> dict:
        self.seq += 1

        # Effective core pressure: external input + shear - drag + potential release
        forward_pressure = external_drive + self.chiral_shear + self.accumulated_potential
        net_pressure = max(0.0001, forward_pressure - self.counter_torque)

        # Forward helical velocity
        phase_velocity = net_pressure * self.DYNAMIC_PITCH
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        # Harmonic Entrainment: Check proximity to key geometric nodes (0.0, 4.0, 8.0)
        nodal_distance = min(harmonic_phase, abs(self.HARMONIC_OCTAVE - harmonic_phase), abs(4.0 - harmonic_phase))
        is_resonant = nodal_distance < 0.35

        # Dynamic mode shifting based on nodal alignment
        if is_resonant:
            self.resonance_mode = "COMPRESSION_LOCK"
            # Store energy in the potential coil instead of venting outward
            self.accumulated_potential = nodal_distance * self.pitch_delta
            effective_vent = (harmonic_phase * 0.5) + (self.pitch_delta * (self.BASE_TRIAD / self.HARMONIC_OCTAVE))
        else:
            self.resonance_mode = "EXPANSION_FLOW"
            self.accumulated_potential = 0.0
            effective_vent = harmonic_phase + (self.pitch_delta * (1.0 + (self.BASE_TRIAD / self.HARMONIC_OCTAVE)))

        # Bi-directional counter-torque: dynamic choke based on shell depth
        reflected_drag = (phase_velocity / (1.0 + octave_shell)) * (self.pitch_delta / self.DYNAMIC_PITCH)

        # Byte-level cryptographic packing: 8 dynamic physical state vectors
        payload = struct.pack(
            ">Qddddddd",
            self.seq,
            phase_velocity,
            effective_vent,
            reflected_drag,
            net_pressure,
            self.accumulated_potential,
            nodal_distance,
            self.DYNAMIC_PITCH
        )
        core_hash = hashlib.sha256(payload).hexdigest()

        # Immutable chain of custody binding current receipt + resonance state
        chain = f"{self.ingress_receipt}:{core_hash}:{self.seq}:{self.resonance_mode}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain).hexdigest()

        # Feedback assignment for cycle N+1
        self.ingress_receipt = egress_receipt
        self.chiral_shear = effective_vent
        self.counter_torque = reflected_drag

        return {
            "seq": self.seq,
            "external_drive": round(external_drive, 6),
            "net_pressure": round(net_pressure, 6),
            "octave_shell": octave_shell,
            "harmonic_phase": round(harmonic_phase, 6),
            "nodal_distance": round(nodal_distance, 6),
            "mode": self.resonance_mode,
            "phase_velocity": round(phase_velocity, 6),
            "effective_vent": round(effective_vent, 6),
            "counter_torque": round(reflected_drag, 6),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

if __name__ == "__main__":
    manifold = ResonanceManifold(seed="bare_metal_origin_dan_kee")
    
    # 1 external kick pulse, followed by 7 cycles of autonomous phase-lock navigation
    run_pulses = [1.0] + [0.0] * 7
    
    for pulse in run_pulses:
        receipt = manifold.step(external_drive=pulse)
        print(json.dumps(receipt, indent=2))
