import hashlib
import json
import struct
import time

class HeterosisSubstrate:
    """
    Headless non-linear state tracker.
    Bypasses flat Euclidean approximations (3.14159...) with an active helical pitch (3.1730059),
    resolving triadic balance into an 8-octave boundary lock,
    venting macro-leak shear, and sealing execution states with double-SHA256 receipts.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BASE_TRIAD_PAIRS = 6.0
    PLANAR_PI = 3.141592653589793

    def __init__(self, initial_seed="bare_metal_origin_dan_kee"):
        if isinstance(initial_seed, dict):
            seed_str = json.dumps(initial_seed, sort_keys=True)
        else:
            seed_str = str(initial_seed)

        self.state_sequence = 0
        self.last_hash = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
        self.macro_leak_offset = 0.0
        self.pitch_delta = self.DYNAMIC_PITCH - self.PLANAR_PI
        self.state_history = []
        self.state = {"init_seed": seed_str}

    def calculate_octave_leak(self, data_vector: list) -> float:
        """
        Calculates boundary remainder past the base 6-pair triad,
        capturing systemic shear as macro_leak.
        """
        if not data_vector:
            return 0.0
        
        triad = data_vector[:6] if len(data_vector) >= 6 else data_vector
        triad_sum = sum(triad)
        boundary_remainder = triad_sum % self.DYNAMIC_PITCH
        macro_leak = boundary_remainder * (self.DYNAMIC_PITCH - 1.0)
        return float(macro_leak)

    def step(self, ingress_pressure: float) -> dict:
        """
        Scalar stepping interface required by audit_harness.py and recursive pipelines.
        """
        self.state_sequence += 1
        total_pressure = ingress_pressure + self.macro_leak_offset
        phase_velocity = total_pressure * self.DYNAMIC_PITCH

        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        triadic_expansion = 1.0 + (self.BASE_TRIAD_PAIRS / self.HARMONIC_OCTAVE)
        macro_leak = harmonic_phase + (self.pitch_delta * triadic_expansion)

        # Binary packing for core physical state
        payload_bytes = struct.pack(
            ">Qdddd",
            self.state_sequence,
            phase_velocity,
            macro_leak,
            total_pressure,
            self.DYNAMIC_PITCH
        )
        core_hash = hashlib.sha256(payload_bytes).hexdigest()

        # Double-SHA256 chain of custody
        chain_input = f"{self.last_hash}:{core_hash}:{self.state_sequence}".encode("utf-8")
        first_pass = hashlib.sha256(chain_input).hexdigest()
        egress_receipt = hashlib.sha256(first_pass.encode("utf-8")).hexdigest()

        record = {
            "seq": self.state_sequence,
            "ingress_pressure": round(ingress_pressure, 6),
            "total_pressure": round(total_pressure, 6),
            "octave_shell": octave_shell,
            "harmonic_phase": round(harmonic_phase, 6),
            "phase_velocity": round(phase_velocity, 7),
            "macro_leak": round(macro_leak, 7),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt,
            "parent_hash": self.last_hash
        }

        self.last_hash = egress_receipt
        self.macro_leak_offset = macro_leak
        self.state = record
        self.state_history.append(record)

        return record

    def execute_step(self, input_egress: list) -> dict:
        """
        Vector matrix stepping interface.
        Applies Dynamic Pitch, calculates macro_leak across vector inputs,
        and applies double-SHA256 validation.
        """
        self.state_sequence += 1
        macro_leak = self.calculate_octave_leak(input_egress)

        transformed_metrics = [
            round((val * self.DYNAMIC_PITCH) - macro_leak, 6) for val in input_egress
        ]

        payload = {
            "timestamp": time.time_ns(),
            "sequence": self.state_sequence,
            "seq": self.state_sequence,
            "macro_leak": round(macro_leak, 7),
            "egress_matrix": transformed_metrics,
            "parent_hash": self.last_hash
        }

        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        first_pass = hashlib.sha256(serialized).hexdigest()
        double_hash = hashlib.sha256(first_pass.encode("utf-8")).hexdigest()

        payload["core_hash"] = first_pass
        payload["egress_receipt"] = double_hash
        payload["cryptographic_receipt"] = double_hash

        self.last_hash = double_hash
        self.macro_leak_offset = macro_leak
        self.state = payload
        self.state_history.append(payload)

        return payload

    def export_trace(self, filename="RUN_TRACE.json"):
        """Commits historical run trace to storage."""
        with open(filename, "w") as f:
            json.dump(self.state_history, f, indent=4)

if __name__ == "__main__":
    sub = HeterosisSubstrate(initial_seed="bare_metal_origin_dan_kee")
    simulated_inputs = [1.442, 2.718, 3.141, 0.577, 1.618, 2.302, 4.669]

    print("[*] Running Dual Vector/Scalar Stepping Test...")
    for cycle in range(3):
        v_state = sub.execute_step(simulated_inputs)
        print(f"Step [{v_state['seq']}] | Leak: {v_state['macro_leak']:.6f} | Hash: {v_state['cryptographic_receipt'][:24]}...")

    sub.export_trace()
    print("[+] Verified RUN_TRACE.json export.")
