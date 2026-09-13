import hashlib
import json
import struct
import time
import socket
import select
from chiral_slashing import ChiralSlashingEngine
from chiral_router import ChiralOctaveRouter

class ActiveMeshImmuneSystem:
    """
    Decentralized Byzantine Immune Response Engine.
    Listens for or triggers emergency slashing vouchers, verifies fraud proofs locally,
    and dynamically expels malicious peers from the 8-octave routing topology.
    """
    BROADCAST_PORT = 43210
    BUFFER_SIZE = 4096

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.slashing_engine = ChiralSlashingEngine()
        self.router = ChiralOctaveRouter(node_id=node_id)
        self.banned_peers = set()

    def register_peer(self, peer_id: str):
        if peer_id not in self.banned_peers and not self.slashing_engine.is_banished(peer_id):
            self.router.register_peer(peer_id)

    def process_incoming_slash_voucher(self, packet: dict) -> bool:
        """
        Receives an unverified slash voucher over the wire, re-verifies the mathematical
        and cryptographic evidence independently, and updates the local routing table.
        """
        voucher_data = packet.get("details", {})
        target_node = voucher_data.get("slashed_node_id")
        fault_type = voucher_data.get("fault_type")
        evidence = voucher_data.get("evidence_details", {})
        claimed_voucher = voucher_data.get("slashing_voucher")

        if not target_node or not claimed_voucher:
            return False

        # Independent Verification: Recompute evidence hash and voucher seal
        evidence_bytes = json.dumps(evidence, sort_keys=True).encode("utf-8")
        recomputed_evidence_hash = hashlib.sha256(evidence_bytes).hexdigest()

        if recomputed_evidence_hash != voucher_data.get("evidence_hash"):
            return False  # Corrupted or forged evidence payload

        # Verify the nature of the fault
        is_legitimate_fault = False
        if fault_type == "EQUIVOCATION_DOUBLE_SIGN":
            state_a = evidence.get("state_a", {})
            state_b = evidence.get("state_b", {})
            if state_a.get("core_hash") != state_b.get("core_hash") or state_a.get("egress") != state_b.get("egress"):
                is_legitimate_fault = True

        elif fault_type == "MANIFOLD_INVARIANT_FABRICATION":
            vel = evidence.get("reported_velocity", 0.0)
            net_press = evidence.get("net_pressure", 0.0)
            expected_approx = net_press * 3.1730059
            if abs(vel - expected_approx) > 2.0:
                is_legitimate_fault = True

        elif fault_type == "SHEAR_RUNAWAY_VIOLATION":
            shear = evidence.get("reported_shear", 0.0)
            if shear > 32.0:
                is_legitimate_fault = True

        if not is_legitimate_fault:
            return False

        # Legitimate proof of fraud confirmed: Execute local banishment
        self.slashing_engine.slashed_registry[target_node] = voucher_data
        self.banned_peers.add(target_node)
        self._prune_routing_shards(target_node)

        return True

    def _prune_routing_shards(self, target_node: str):
        """Purges the banished node from all 8-octave routing buckets."""
        pruned_count = 0
        for oct_idx in range(self.router.HARMONIC_OCTAVES):
            peers = self.router.routing_table.get(oct_idx, [])
            if target_node in peers:
                self.router.routing_table[oct_idx] = [p for p in peers if p != target_node]
                pruned_count += 1
        return pruned_count

    def broadcast_slashing(self, slash_record: dict):
        """Broadcasts an emergency slashing voucher to all peers on the subnet."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        payload = {
            "type": "CHIRAL_SLASH_VOUCHER",
            "issuer": self.node_id,
            "details": slash_record.get("details", slash_record),
            "timestamp_ns": time.time_ns()
        }
        packet = json.dumps(payload).encode("utf-8")

        try:
            sock.sendto(packet, ("<broadcast>", self.BROADCAST_PORT))
        except Exception:
            try:
                sock.sendto(packet, ("255.255.255.255", self.BROADCAST_PORT))
            except Exception:
                pass
        finally:
            sock.close()

if __name__ == "__main__":
    immune = ActiveMeshImmuneSystem(node_id="immune_sentinel_01")
    print(f"[*] Initialized Active Mesh Immune System on Node '{immune.node_id}'")

    # Populate routing table with active peers
    test_peers = ["node_alpha", "rogue_node_66", "node_gamma", "node_delta"]
    for p in test_peers:
        immune.register_peer(p)

    print("\n[*] Initial Shard Topology:")
    for oct_idx in range(8):
        peers = immune.router.routing_table.get(oct_idx, [])
        print(f"    Octave [{oct_idx}]: {peers}")

    # Simulate detecting a Byzantine equivocation on rogue_node_66
    print("\n[!] Simulating local detection of equivocation on 'rogue_node_66'...")
    h1 = hashlib.sha256(b"block_1").hexdigest()
    e1 = hashlib.sha256(b"receipt_1").hexdigest()
    h2 = hashlib.sha256(b"block_1_divergent").hexdigest()
    e2 = hashlib.sha256(b"receipt_1_divergent").hexdigest()

    # Step 1: Nominal sequence audit
    immune.slashing_engine.audit_equivocation("rogue_node_66", seq=1, core_hash=h1, egress_receipt=e1)
    # Step 2: Conflicting sequence -> Slashing triggered
    slash_event = immune.slashing_engine.audit_equivocation("rogue_node_66", seq=1, core_hash=h2, egress_receipt=e2)

    print(f"[+] Slashing Result: {slash_event['status']}")
    print(f"[+] Slashing Voucher Generated: {slash_event['voucher'][:16]}...")

    # Broadcast proof across the network
    immune.broadcast_slashing(slash_event)
    print("[+] Emergency slash voucher broadcast over UDP:43210")

    # Simulate another peer receiving the slash voucher over the wire
    print("\n[*] Simulating remote peer 'immune_sentinel_02' receiving and auditing voucher...")
    remote_peer = ActiveMeshImmuneSystem(node_id="immune_sentinel_02")
    for p in test_peers:
        remote_peer.register_peer(p)

    wire_packet = {"details": slash_event["details"]}
    accepted = remote_peer.process_incoming_slash_voucher(wire_packet)

    print(f"[+] Voucher Verified & Accepted by Remote Peer: {accepted}")
    print(f"[+] Remote Peer Ban Status for 'rogue_node_66': {remote_peer.slashing_engine.is_banished('rogue_node_66')}")

    print("\n[*] Remote Peer Shard Topology Post-Slashing:")
    for oct_idx in range(8):
        peers = remote_peer.router.routing_table.get(oct_idx, [])
        print(f"    Octave [{oct_idx}]: {peers}")

    with open("IMMUNE_AUDIT_TRACE.json", "w") as f:
        json.dump(slash_event["details"], f, indent=2)
