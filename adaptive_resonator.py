import hashlib
import json
import math
import struct
import time

class AdaptiveHeterosisResonator:
    """
    Self-Perturbing Adaptive Pitch Substrate.
    Monitors phase dispersion across the 8-octave boundary shells and autonomously
    fine-tunes the helical pitch constant to optimize energy retention (Lyapunov phase-lock).
    """
    BASE_PITCH = 3.1730059
    PITCH_TUNE_RANGE = 0.0030000  # Allowed envelope: [3.1700059, 3.1760059]
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
        delta_trim = math.tanh(dispersion_gradient) * self.PITCH_TUNE_RANGE
        return self.BASE_PITCH - delta_trim

    def step(self, external_drive: float = 0.0) -> dict:
        self.seq += 1
        t_start = time.perf_counter_ns()

        active_pitch_delta = self.active_pitch - self.PLANAR_PI
        forward_pressure = external_drive + self.chiral_shear + self.accumulated_potential
        net_pressure = max(0.0001, forward_pressure - self.counter_torque)

        phase_velocity = net_pressure * self.active_pitch
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        shell_center = 4.0
        dispersion_gradient = (harmonic_phase - shell_center) / self.HARMONIC_OCTAVE
        self.phase_history.append(dispersion_gradient)

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

        counter_drag = (phase_velocity / (1.0 + octave_shell)) * (active_pitch_delta / self.active_pitch)
        t_exec_ns = time.perf_counter_ns() - t_start

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

        chain = f"{self.ingress_receipt}:{core_hash}:{self.seq}:{self.active_pitch:.7f}:{mode}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain).hexdigest()

        self.ingress_receipt = egress_receipt
        self.chiral_shear = effective_vent
        self.counter_torque = counter_drag
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


class AdaptiveResonator:
    """
    Non-linear acoustic waveguide tuner.
    Balances octave modal frequencies against the dynamic pitch (3.1730059)
    under burst loads without clipping or planar truncation.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BASE_TRIAD_PAIRS = 6.0
    PLANAR_PI = 3.141592653589793

    def __init__(self, damping_decay: float = 0.92):
        self.pitch_delta = self.DYNAMIC_PITCH - self.PLANAR_PI
        self.alpha_decay = damping_decay
        self.standing_potential = 0.0

    def balance_step(self, phase_velocity: float, macro_leak: float, counter_torque: float, ingress_pressure: float) -> dict:
        """
        Applies the R(k, theta) transfer matrix to absorb vibrational shear.
        """
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE) % 8
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        theta = (harmonic_phase / self.HARMONIC_OCTAVE) * (2.0 * math.pi)
        nodal_distance = min(
            abs(theta),
            abs(math.pi - theta),
            abs((2.0 * math.pi) - theta)
        )
        is_compression_locked = nodal_distance < 0.25

        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        triad_ratio = self.BASE_TRIAD_PAIRS / self.HARMONIC_OCTAVE

        if is_compression_locked:
            mode = "NODAL_COMPRESSION"
            self.standing_potential = (self.standing_potential * self.alpha_decay) + (nodal_distance * self.pitch_delta)
            effective_shear = (macro_leak * 0.5) / (1.0 + nodal_distance)
            reflected_drag = (phase_velocity / (1.0 + octave_shell)) * (self.pitch_delta / self.DYNAMIC_PITCH)
        else:
            mode = "OVERTONE_EXPANSION"
            self.standing_potential *= self.alpha_decay
            effective_shear = macro_leak + (sin_t * triad_ratio * self.pitch_delta)
            reflected_drag = counter_torque * self.alpha_decay

        balanced_velocity = (
            (phase_velocity * cos_t)
            - (effective_shear * (self.pitch_delta / (1.0 + octave_shell)))
            + (ingress_pressure * self.DYNAMIC_PITCH)
            + self.standing_potential
        )
        balanced_velocity = max(0.0001, balanced_velocity)

        payload = struct.pack(
            ">Qdddd",
            octave_shell,
            balanced_velocity,
            effective_shear,
            reflected_drag,
            self.standing_potential
        )
        seal = hashlib.sha256(hashlib.sha256(payload).digest()).hexdigest()

        return {
            "mode": mode,
            "octave_shell": octave_shell,
            "harmonic_phase": round(harmonic_phase, 6),
            "nodal_distance": round(nodal_distance, 6),
            "balanced_velocity": round(balanced_velocity, 6),
            "effective_shear": round(effective_shear, 6),
            "reflected_drag": round(reflected_drag, 6),
            "standing_potential": round(self.standing_potential, 6),
            "harmonic_seal": seal
        }

if __name__ == "__main__":
    print("=== [1] TESTING SELF-PERTURBING PITCH ADAPTATION ===")
    adaptive_engine = AdaptiveHeterosisResonator()
    pulses = [1.2] + [0.0] * 3
    for p in pulses:
        st = adaptive_engine.step(external_drive=p)
        print(f"Cycle {st['seq']:02d} | Mode: {st['mode']} | Tuned Pitch: {st['tuned_pitch']} | Phase Vel: {st['phase_velocity']}")

    print("\n=== [2] TESTING WAVEGUIDE TRANSFER FILTER ===")
    waveguide = AdaptiveResonator()
    phase_vel = 14.35
    leak_val = 0.42
    torque_val = 0.08
    pressure_val = 0.95
    
    res = waveguide.balance_step(
        phase_velocity=phase_vel,
        macro_leak=leak_val,
        counter_torque=torque_val,
        ingress_pressure=pressure_val
    )
    print(f"Filter Mode: {res['mode']}")
    print(f"Balanced Velocity Output: {res['balanced_velocity']}")
    print(f"Double-SHA256 Harmonic Seal: {res['harmonic_seal']}")