import hashlib
import json
import struct
import math
import time

class AdaptiveHeterosisResonator:
    """
    Self-Perturbing Adaptive Pitch Substrate.
    Monitors phase dispersion across the 8-octave boundary shells and autonomously
    fine-tunes the helical pitch constant to optimize energy retention (Lyapunov phase-lock).
    """
    BASE_PITCH = 3.1730059
    PITCH_TUNE_RANGE = 0.0030000  # Allowed fluctuation envelope [3.1700059, 3.1760059]
    HARMONIC_OCTAVE = 8.0
    BASE_TRIAD = 6.0
    PLANAR_PI = 3.141592653589793

    def __init__(self, seed: str = "bare_metal_origin_dan_kee"):
        self.seq = 0
        self.ingress_receipt = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        self.active_pitch = self.BASE_PITCH
        self.chiral_shear = 0.0
        self.counter_torque = 0.0
        self.accumulated_potential = 0.0
        self.phase_history = []

    def tune_pitch(self, dispersion_gradient: float) -> float:
        """
        Dynamically modulates pitch constant based on boundary leakage gradients.
        Negative feedback stabilizes the system within the optimal resonance channel.
        """
        # Pitch oscillates using a bounded non-linear sigmoid damping curve
        delta_trim = math.tanh(dispersion_gradient) * self.PITCH_TUNE_RANGE
        tuned_pitch = self.BASE_PITCH - delta_trim
        return tuned_pitch

    def step(self, external_drive: float = 0.0) -> dict:
        self.seq += 1
        t_start = time.perf_counter_ns()

        # Compute dynamic pitch delta against static planar baseline
        active_pitch_delta = self.active_pitch - self.PLANAR_PI

        # Effective core pressure
        forward_pressure = external_drive + self.chiral_shear + self.accumulated_potential
        net_pressure = max(0.0001, forward_pressure - self.counter_torque)

        # Calculate phase velocity under currently tuned dynamic pitch
        phase_velocity = net_pressure * self.active_pitch
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        # Dispersion metric: variance from the harmonic center of the current shell
        shell_center = 4.0
        dispersion_gradient = (harmonic_phase - shell_center) / self.HARMONIC_OCTAVE
        self.phase_history.append(dispersion_gradient)

        # Harmonic entrainment check
        nodal_distance = min(harmonic_phase, abs(self.HARMONIC_OCTAVE - harmonic_phase), abs(4.0 - harmonic_phase))
        is_resonant = nodal_distance < 0.35

        if is_resonant:
            mode = "COMPRESSION_LOCK"
            self.accumulated_potential = nodal_distance * active_pitch_delta
            effective_vent = (harmonic_phase * 0.5) + (active_pitch_delta * (self.BASE_TRIAD / self.HARMONIC_OCTAVE))
        else:
            mode = "EXPANSION_FLOW"
            self.accumulated_potential = 0.0
            effective_vent = harmonic_phase + (active_pitch_delta * (1.0 + (self.BASE_TRIAD / self.HARMONIC_OCTAVE)))

        # Reflected chiral drag modulated by shell depth
        counter_drag = (phase_velocity / (1.0 + octave_shell)) * (active_pitch_delta / self.active_pitch)
        t_exec_ns = time.perf_counter_ns() - t_start

        # Binary struct packaging: packs the dynamically tuned pitch alongside physical telemetry
        payload = struct.pack(
            ">QQdddddd",
            self.seq,
            t_exec_ns,
            self.active_pitch,
            phase_velocity,
            effective_vent,
            counter_drag,
            net_pressure,
            dispersion_gradient
        )
        core_hash = hashlib.sha256(payload).hexdigest()

        # Chain of custody seal explicitly anchoring the tuned pitch parameter
        chain = f"{self.ingress_receipt}:{core_hash}:{self.seq}:{self.active_pitch:.7f}:{mode}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain).hexdigest()

        # Update manifold recirculation
        self.ingress_receipt = egress_receipt
        self.chiral_shear = effective_vent
        self.counter_torque = counter_drag

        # Execute adaptive feedback tuning for the upcoming cycle
        self.active_pitch = self.tune_pitch(dispersion_gradient)

        return {
            "seq": self.seq,
            "exec_ns": t_exec_ns,
            "tuned_pitch": round(self.active_pitch, 7),
            "net_pressure": round(net_pressure, 6),
            "octave_shell": octave_shell,
            "harmonic_phase": round(harmonic_phase, 6),
            "dispersion_gradient": round(dispersion_gradient, 6),
            "mode": mode,
            "phase_velocity": round(phase_velocity, 6),
            "chiral_vent": round(effective_vent, 6),
            "counter_torque": round(counter_drag, 6),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

if __name__ == "__main__":
    resonator = AdaptiveHeterosisResonator()
    print("[*] Initiating self-perturbing dynamic pitch adaptation...")

    # Single initial kick, then watch the engine tune its own pitch constant
    run_pulses = [1.2] + [0.0] * 7
    trace = []

    for p in run_pulses:
        state = resonator.step(external_drive=p)
        trace.append(state)
        print(f"Cycle {state['seq']} | Pitch: {state['tuned_pitch']} | "
              f"Shell: {state['octave_shell']} | Phase Vel: {state['phase_velocity']} | "
              f"Mode: {state['mode']}")

    with open("ADAPTIVE_RESONANCE_TRACE.json", "w") as f:
        json.dump(trace, f, indent=2)
