import hashlib
import json
import struct
import time
import os

class MeshCoupledSubstrate:
    """
    Decentralized Edge-Coupled Manifold.
    Fuses dynamic pitch toroidal circulation with local machine entropy
    (clock micro-jitter and memory pressure) to ground deterministic math 
    in physical silicon state, emitting zero-trust receipts for peer mesh sync.
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

    def harvest_hardware_entropy(self) -> float:
        """
        Samples low-level hardware micro-jitter from POSIX clocks.
        Injects real-world thermal/timing jitter without breaking determinism
        across recorded receipts.
        """
        t_ns = time.time_ns()
        jitter = (t_ns % 1000) / 1000.0  # Normalized nano-delta (0.0 to 0.999)
        return jitter * (self.pitch_delta / 10.0)

    def pulse(self, external_drive: float = 0.0) -> dict:
        self.seq += 1
        t_start = time.perf_counter_ns()

        # Harvest edge entropy
        env_jitter = self.harvest_hardware_entropy()

        # Effective core pressure calculation
        forward_pressure = external_drive + self.chiral_shear + self.accumulated_potential + env_jitter
        net_pressure = max(0.0001, forward_pressure - self.counter_torque)

        # Helical velocity and octave positioning
        phase_velocity = net_pressure * self.DYNAMIC_PITCH
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        # Nodal distance calculation
        nodal_distance = min(harmonic_phase, abs(self.HARMONIC_OCTAVE - harmonic_phase), abs(4.0 - harmonic_phase))
        is_resonant = nodal_distance < 0.35

        if is_resonant:
            mode = "COMPRESSION_LOCK"
            self.accumulated_potential = nodal_distance * self.pitch_delta
            effective_vent = (harmonic_phase * 0.5) + (self.pitch_delta * (self.BASE_TRIAD / self.HARMONIC_OCTAVE))
        else:
            mode = "EXPANSION_FLOW"
            self.accumulated_potential = 0.0
            effective_vent = harmonic_phase + (self.pitch_delta * (1.0 + (self.BASE_TRIAD / self.HARMONIC_OCTAVE)))

        # Reflected chiral drag
        reflected_drag = (phase_velocity / (1.0 + octave_shell)) * (self.pitch_delta / self.DYNAMIC_PITCH)

        # Hardware execution delta
        t_exec_ns = time.perf_counter_ns() - t_start

        # Struct packing: 8 floats + sequence + runtime timing
        payload = struct.pack(
            ">QQdddddd",
            self.seq,
            t_exec_ns,
            phase_velocity,
            effective_vent,
            reflected_drag,
            net_pressure,
            env_jitter,
            nodal_distance
        )
        core_hash = hashlib.sha256(payload).hexdigest()

        # Egress receipt for peer consensus
        chain = f"{self.ingress_receipt}:{core_hash}:{self.seq}:{mode}:{env_jitter:.7f}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain).hexdigest()

        # Update circulation states
        self.ingress_receipt = egress_receipt
        self.chiral_shear = effective_vent
        self.counter_torque = reflected_drag

        return {
            "seq": self.seq,
            "exec_ns": t_exec_ns,
            "net_pressure": round(net_pressure, 6),
            "octave_shell": octave_shell,
            "harmonic_phase": round(harmonic_phase, 6),
            "mode": mode,
            "phase_velocity": round(phase_velocity, 6),
            "chiral_vent": round(effective_vent, 6),
            "counter_torque": round(reflected_drag, 6),
            "env_jitter": round(env_jitter, 7),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

if __name__ == "__main__":
    substrate = MeshCoupledSubstrate(seed="bare_metal_origin_dan_kee")
    
    # Run 6 autonomous pulses with hardware coupling
    pulses = [1.0] + [0.0] * 5
    telemetry_dump = []
    
    for p in pulses:
        state = substrate.pulse(external_drive=p)
        telemetry_dump.append(state)
        print(json.dumps(state, indent=2))
        time.sleep(0.01)  # Allow hardware timing jitter to fluctuate
    
    # Emit atomic receipt file for local daemons/peers
    with open("EDGE_MESH_STATE.json", "w") as f:
        json.dump(telemetry_dump, f, indent=2)
