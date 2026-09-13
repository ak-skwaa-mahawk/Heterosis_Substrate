import hashlib
import json
import struct
import math
import time

class ChiralOctaveRouter:
    """
    Decentralized, Geometry-Native Harmonic State Router.
    Partitions computational load and transaction routing across the 8-octave ring
    without central dispatchers, coordinators, or global locks.
    """
    HARMONIC_OCTAVES = 8
    DYNAMIC_PITCH = 3.1730059

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.node_hash = hashlib.sha256(node_id.encode("utf-8")).hexdigest()
        # Compute primary assigned octave shell
        self.assigned_octave = int(self.node_hash, 16) % self.HARMONIC_OCTAVES
        self.routing_table = {}  # Map: octave_index -> [peer_ids]

    def register_peer(self, peer_id: str):
        """Deterministically assigns a peer node to its resonant octave shell."""
        peer_hash = hashlib.sha256(peer_id.encode("utf-8")).hexdigest()
        octave_slot = int(peer_hash, 16) % self.HARMONIC_OCTAVES
        if octave_slot not in self.routing_table:
            self.routing_table[octave_slot] = []
        if peer_id not in self.routing_table[octave_slot]:
            self.routing_table[octave_slot].append(peer_id)

    def route_state(self, state: dict) -> dict:
        """
        Calculates whether the current state must execute locally
        or migrate to a peer handling the target octave boundary.
        """
        phase_vel = state.get("phase_velocity", 0.0)
        target_octave = int(phase_vel // self.HARMONIC_OCTAVES) % self.HARMONIC_OCTAVES
        harmonic_phase = phase_vel % self.HARMONIC_OCTAVES

        # Check if local node holds responsibility for this octave shell
        is_local = (target_octave == self.assigned_octave)

        # Harmonic boundary transit: detect if crossing shell threshold
        is_boundary_transit = (harmonic_phase < 0.35) or (harmonic_phase > 7.65)

        candidate_peers = self.routing_table.get(target_octave, [])

        # Select target peer using deterministic phase-offset hashing
        if is_local:
            target_node = self.node_id
            action = "PROCESS_LOCAL"
        elif candidate_peers:
            # Deterministic peer selection within target shard
            idx = int(phase_vel * 1000) % len(candidate_peers)
            target_node = candidate_peers[idx]
            action = "ROUTE_CROSS_OCTAVE"
        else:
            # Fallback: process locally if shard has no active edge peers
            target_node = self.node_id
            action = "PROCESS_LOCAL_UNCLAIMED_SHARD"

        # Pack routing manifest
        route_payload = struct.pack(
            ">QQdd",
            state.get("seq", 0),
            target_octave,
            phase_vel,
            harmonic_phase
        )
        route_hash = hashlib.sha256(route_payload).hexdigest()

        routing_manifest = {
            "seq": state.get("seq", 0),
            "origin_node": self.node_id,
            "assigned_octave": self.assigned_octave,
            "target_octave": target_octave,
            "harmonic_phase": round(harmonic_phase, 6),
            "boundary_transit": is_boundary_transit,
            "action": action,
            "dispatched_to": target_node,
            "route_hash": route_hash
        }
        return routing_manifest

if __name__ == "__main__":
    from mesh_substrate import MeshCoupledSubstrate

    # Initialize a local node assigned to a deterministic octave shell
    local_node_id = "edge_alpha_77"
    router = ChiralOctaveRouter(node_id=local_node_id)
    print(f"[*] Initialized Node '{local_node_id}' -> Assigned Octave Shell: [{router.assigned_octave}]")

    # Register simulated edge peers across the network
    peer_pool = [f"peer_device_{i}" for i in range(16)]
    for peer in peer_pool:
        router.register_peer(peer)

    print("\n[*] Octave Routing Table Topology:")
    for oct_idx in range(8):
        peers = router.routing_table.get(oct_idx, [])
        print(f"    Octave Shell {oct_idx}: {len(peers)} peers registered -> {peers[:2]}...")

    # Run state stepping across varying pressures to test routing migrations
    substrate = MeshCoupledSubstrate(seed="routing_genesis")
    print("\n[*] Stepping manifold and calculating dynamic octave dispatch...")

    routing_trace = []
    # Stepping pressure up to force rapid octave shell transitions
    drive_inputs = [1.0, 3.5, 7.2, 12.0, 18.5]

    for drive in drive_inputs:
        state = substrate.pulse(external_drive=drive)
        manifest = router.route_state(state)
        routing_trace.append(manifest)

        print(f"Seq {manifest['seq']:02d} | Phase Vel: {state['phase_velocity']:>8.4f} | "
              f"Target Octave: [{manifest['target_octave']}] | "
              f"Action: {manifest['action']:<28} | "
              f"Dispatch -> {manifest['dispatched_to']}")

    with open("OCTAVE_ROUTING_MANIFEST.json", "w") as f:
        json.dump(routing_trace, f, indent=2)
