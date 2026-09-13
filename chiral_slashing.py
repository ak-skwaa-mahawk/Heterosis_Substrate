import hashlib
import json
import struct
import time

class ChiralSlashingEngine:
    """
    Byzantine Fault Detection and Geometric Slashing Substrate.
    Detects double-signing (equivocation), impossible phase acceleration,
    and corrupted compute proofs, permanently blacklisting rogue node IDs.
    """
    MAX_PERMISSIBLE_SHEAR = 32.0
    DYNAMIC_PITCH = 3.1730059

    def __init__(self):
        # Maps node_id -> {seq: (core_hash, egress_receipt)}
        self.observed_sequences = {}
        # Blacklisted node IDs mapped to the cryptographic slashing voucher
        self.slashed_registry = {}

    def audit_equivocation(self, node_id: str, seq: int, core_hash: str, egress_receipt: str) -> dict:
        """
        Audits whether a node has signed two divergent states for the same sequence number.
        """
        if node_id in self.slashed_registry:
            return {"status": "REJECTED_ALREADY_SLASHED", "node_id": node_id}

        if node_id not in self.observed_sequences:
            self.observed_sequences[node_id] = {}

        if seq in self.observed_sequences[node_id]:
            prev_core_hash, prev_egress = self.observed_sequences[node_id][seq]
            if prev_core_hash != core_hash or prev_egress != egress_receipt:
                # Byzantine Equivocation detected!
                return self._slash_node(
                    node_id=node_id,
                    reason="EQUIVOCATION_DOUBLE_SIGN",
                    fault_evidence={
                        "conflicting_seq": seq,
                        "state_a": {"core_hash": prev_core_hash, "egress": prev_egress},
                        "state_b": {"core_hash": core_hash, "egress": egress_receipt}
                    }
                )

        self.observed_sequences[node_id][seq] = (core_hash, egress_receipt)
        return {"status": "VALID_NOMINAL", "node_id": node_id, "seq": seq}

    def audit_physical_bounds(self, node_id: str, state: dict) -> dict:
        """
        Audits reported physical trajectory for impossible non-Euclidean boundary violations.
        """
        if node_id in self.slashed_registry:
            return {"status": "REJECTED_ALREADY_SLASHED", "node_id": node_id}

        shear = state.get("chiral_vent", state.get("macro_leak_vent", 0.0))
        phase_vel = state.get("phase_velocity", 0.0)
        net_press = state.get("net_pressure", 0.0)

        # Fault: Fabricated phase velocity violating the dynamic pitch manifold
        expected_phase_approx = net_press * self.DYNAMIC_PITCH
        if abs(phase_vel - expected_phase_approx) > 2.0:
            return self._slash_node(
                node_id=node_id,
                reason="MANIFOLD_INVARIANT_FABRICATION",
                fault_evidence={
                    "reported_velocity": phase_vel,
                    "expected_velocity": round(expected_phase_approx, 6),
                    "net_pressure": net_press
                }
            )

        # Fault: Shear blow-out rupture
        if shear > self.MAX_PERMISSIBLE_SHEAR:
            return self._slash_node(
                node_id=node_id,
                reason="SHEAR_RUNAWAY_VIOLATION",
                fault_evidence={"reported_shear": shear, "limit": self.MAX_PERMISSIBLE_SHEAR}
            )

        return {"status": "VALID_NOMINAL", "node_id": node_id}

    def _slash_node(self, node_id: str, reason: str, fault_evidence: dict) -> dict:
        """
        Generates an immutable cryptographic slashing voucher and ejects node.
        """
        evidence_bytes = json.dumps(fault_evidence, sort_keys=True).encode("utf-8")
        evidence_hash = hashlib.sha256(evidence_bytes).hexdigest()

        slash_payload = f"SLASH:{node_id}:{reason}:{evidence_hash}:{time.time_ns()}".encode("utf-8")
        slash_voucher = hashlib.sha256(slash_payload).hexdigest()

        record = {
            "slashed_node_id": node_id,
            "fault_type": reason,
            "evidence_hash": evidence_hash,
            "evidence_details": fault_evidence,
            "slashing_voucher": slash_voucher,
            "timestamp_ns": time.time_ns()
        }

        self.slashed_registry[node_id] = record
        return {
            "status": "SLASHED_AND_BANISHED",
            "node_id": node_id,
            "voucher": slash_voucher,
            "details": record
        }

    def is_banished(self, node_id: str) -> bool:
        return node_id in self.slashed_registry

if __name__ == "__main__":
    slasher = ChiralSlashingEngine()

    print("[*] Monitoring mesh stream for Byzantine faults...")

    # 1. Nominal state sequence audit
    h_a = hashlib.sha256(b"state_alpha").hexdigest()
    e_a = hashlib.sha256(b"egress_alpha").hexdigest()
    res1 = slasher.audit_equivocation(node_id="peer_node_7", seq=1, core_hash=h_a, egress_receipt=e_a)
    print(f"Cycle 1: {res1['status']}")

    # 2. Simulate Equivocation Attack (peer_node_7 signs a different state for seq 1)
    print("\n[!] Simulating double-sign equivocation attack from 'peer_node_7'...")
    h_b = hashlib.sha256(b"state_fork").hexdigest()
    e_b = hashlib.sha256(b"egress_fork").hexdigest()
    slash_event = slasher.audit_equivocation(node_id="peer_node_7", seq=1, core_hash=h_b, egress_receipt=e_b)

    print(f"Audit Result: {slash_event['status']}")
    print(f"Slashing Voucher: {slash_event.get('voucher')}")

    # 3. Simulate Manifold Invariant Fabrication from another node
    print("\n[!] Simulating synthetic invariant tampering from 'peer_node_99'...")
    tampered_state = {
        "phase_velocity": 45.0,  # Unphysical jump
        "net_pressure": 1.0,     # 1.0 * 3.1730059 != 45.0
        "chiral_vent": 2.1
    }
    phys_slash = slasher.audit_physical_bounds(node_id="peer_node_99", state=tampered_state)
    print(f"Audit Result: {phys_slash['status']}")
    print(f"Fault Reason: {phys_slash['details']['fault_type']}")

    print(f"\n[*] Blacklist Status: 'peer_node_7' banished = {slasher.is_banished('peer_node_7')}")
    print(f"[*] Blacklist Status: 'peer_node_99' banished = {slasher.is_banished('peer_node_99')}")

    with open("SLASHING_REGISTRY.json", "w") as f:
        json.dump(slasher.slashed_registry, f, indent=2)
