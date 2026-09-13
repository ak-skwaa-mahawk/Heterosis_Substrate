import hashlib
import json
import struct
import time

class ChiralSlashingEngine:
    """
    Byzantine Fault Detection and Slashing Substrate.
    Audits incoming gossip packets for double-signing (equivocation),
    manifold invariant fabrication, and runaway boundary shear.
    """
    DYNAMIC_PITCH = 3.1730059
    MAX_PERMISSIBLE_SHEAR = 32.0
    VELOCITY_TOLERANCE = 2.0

    def __init__(self):
        # node_id -> {seq: (core_hash, egress_receipt)}
        self.observed_sequences = {}
        # node_id -> slashing record
        self.slashed_registry = {}

    def audit_equivocation(self, node_id: str, seq: int, core_hash: str, egress_receipt: str) -> dict:
        """
        Detects conflicting state receipts signed for the exact same sequence ID.
        """
        if node_id in self.slashed_registry:
            return {"status": "REJECTED_ALREADY_SLASHED", "node_id": node_id}

        if node_id not in self.observed_sequences:
            self.observed_sequences[node_id] = {}

        if seq in self.observed_sequences[node_id]:
            prev_hash, prev_egress = self.observed_sequences[node_id][seq]
            if prev_hash != core_hash or prev_egress != egress_receipt:
                return self._slash_node(
                    node_id=node_id,
                    reason="EQUIVOCATION_DOUBLE_SIGN",
                    fault_evidence={
                        "conflicting_seq": seq,
                        "state_a": {"core_hash": prev_hash, "egress": prev_egress},
                        "state_b": {"core_hash": core_hash, "egress": egress_receipt}
                    }
                )

        self.observed_sequences[node_id][seq] = (core_hash, egress_receipt)
        return {"status": "VALID_NOMINAL", "node_id": node_id, "seq": seq}

    def audit_physical_bounds(self, node_id: str, state: dict) -> dict:
        """
        Verifies that reported physical trajectories satisfy non-Euclidean invariants.
        """
        if node_id in self.slashed_registry:
            return {"status": "REJECTED_ALREADY_SLASHED", "node_id": node_id}

        phase_vel = float(state.get("phase_velocity", 0.0))
        net_press = float(state.get("net_pressure", state.get("total_pressure", 1.0)))
        shear = float(state.get("chiral_vent", state.get("macro_leak", 0.0)))

        # 1. Pitch Invariant Verification
        expected_vel = net_press * self.DYNAMIC_PITCH
        if abs(phase_vel - expected_vel) > self.VELOCITY_TOLERANCE:
            return self._slash_node(
                node_id=node_id,
                reason="MANIFOLD_INVARIANT_FABRICATION",
                fault_evidence={
                    "reported_velocity": phase_vel,
                    "expected_velocity": round(expected_vel, 6),
                    "net_pressure": net_press
                }
            )

        # 2. Shear Containment Audit
        if shear > self.MAX_PERMISSIBLE_SHEAR:
            return self._slash_node(
                node_id=node_id,
                reason="SHEAR_RUNAWAY_VIOLATION",
                fault_evidence={
                    "reported_shear": shear,
                    "limit": self.MAX_PERMISSIBLE_SHEAR
                }
            )

        return {"status": "VALID_NOMINAL", "node_id": node_id}

    def _slash_node(self, node_id: str, reason: str, fault_evidence: dict) -> dict:
        """
        Mints a cryptographic slashing voucher and writes to blacklist.
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
    print(f"[*] Chiral Slashing Engine initialized (Dynamic Pitch: {slasher.DYNAMIC_PITCH})")

    # Test 1: Double-sign detection
    h1 = hashlib.sha256(b"block_state_a").hexdigest()
    e1 = hashlib.sha256(b"egress_a").hexdigest()
    h2 = hashlib.sha256(b"block_state_b").hexdigest()
    e2 = hashlib.sha256(b"egress_b").hexdigest()

    slasher.audit_equivocation("peer_node_beta", seq=1, core_hash=h1, egress_receipt=e1)
    slash_event = slasher.audit_equivocation("peer_node_beta", seq=1, core_hash=h2, egress_receipt=e2)

    print(f"\n[!] Equivocation Audit: {slash_event['status']}")
    print(f" └── Slashing Voucher: {slash_event.get('voucher')}")
    print(f" └── Blacklist Status: {slasher.is_banished('peer_node_beta')}")

    # Test 2: Invariant fabrication detection
    forged_state = {
        "phase_velocity": 48.0,  # Impossible jump: 1.0 * 3.1730059 != 48.0
        "net_pressure": 1.0,
        "macro_leak": 2.1
    }
    phys_slash = slasher.audit_physical_bounds("peer_node_gamma", state=forged_state)
    print(f"\n[!] Invariant Audit:    {phys_slash['status']}")
    print(f" └── Fault Type:       {phys_slash['details']['fault_type']}")
    print(f" └── Blacklist Status: {slasher.is_banished('peer_node_gamma')}")
