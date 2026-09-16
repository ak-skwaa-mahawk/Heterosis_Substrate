import hashlib
import json
import struct
import math

class HeterosisConsensus:
    """
    Cross-Node Heterosis Consensus Engine.
    Fuses two asynchronous execution chains by calculating their phase interference,
    resolving octave dissonance, and forging an immutable hybrid block.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0

    @staticmethod
    def interlock(node_a_receipt: dict, node_b_receipt: dict) -> dict:
        """
        Takes egress receipts from two separate edge nodes,
        evaluates cross-phase shear, and outputs the consensus proof.
        """
        # Extract phase velocities and core hashes
        v_a = float(node_a_receipt.get("phase_velocity", 0.0))
        v_b = float(node_b_receipt.get("phase_velocity", 0.0))
        h_a = node_a_receipt.get("core_hash", "0" * 64)
        h_b = node_b_receipt.get("core_hash", "0" * 64)

        # Cross-sectional phase difference across the 8-octave boundary
        phase_delta = abs(v_a - v_b) % HeterosisConsensus.HARMONIC_OCTAVE

        # Hybrid Vigor (Heterosis) Ratio:
        # Measures the constructive interference of combining both streams
        heterosis_gain = 1.0 + (math.sin(phase_delta * (math.pi / 4.0)) * (HeterosisConsensus.DYNAMIC_PITCH / 10.0))

        # Synthesize fused velocity: balanced across the dynamic pitch
        fused_velocity = ((v_a + v_b) / 2.0) * heterosis_gain
        fused_shell = int(fused_velocity // HeterosisConsensus.HARMONIC_OCTAVE)

        # Pack cross-verified payload
        interlock_payload = struct.pack(
            ">ddQ",
            fused_velocity,
            heterosis_gain,
            fused_shell
        )
        fused_state_hash = hashlib.sha256(interlock_payload).hexdigest()

        # Chain-of-custody lock binding both ancestral chains
        consensus_block = f"{h_a}:{h_b}:{fused_state_hash}:{heterosis_gain:.6f}".encode("utf-8")
        heterosis_root = hashlib.sha256(consensus_block).hexdigest()

        return {
            "node_a_seq": node_a_receipt.get("seq"),
            "node_b_seq": node_b_receipt.get("seq"),
            "node_a_hash": h_a[:16] + "...",
            "node_b_hash": h_b[:16] + "...",
            "phase_delta": round(phase_delta, 6),
            "heterosis_gain": round(heterosis_gain, 6),
            "fused_velocity": round(fused_velocity, 6),
            "fused_octave_shell": fused_shell,
            "fused_state_hash": fused_state_hash,
            "heterosis_root": heterosis_root
        }

if __name__ == "__main__":
    from .mesh_substrate import MeshCoupledSubstrate

    # Simulate two independent edge runs seeded differently
    node_alpha = MeshCoupledSubstrate(seed="edge_alpha_origin")
    node_beta = MeshCoupledSubstrate(seed="edge_beta_origin")

    # Cycle both nodes independently
    state_a = node_alpha.pulse(external_drive=1.5)
    state_b = node_beta.pulse(external_drive=2.2)

    # Interlock their state receipts into a hybrid consensus root
    consensus_receipt = HeterosisConsensus.interlock(state_a, state_b)
    print(json.dumps(consensus_receipt, indent=2))
