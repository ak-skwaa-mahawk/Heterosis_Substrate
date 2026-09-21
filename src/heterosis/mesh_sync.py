import hashlib
import hmac
import json
import select
import socket
import struct
import threading
import time
from .base import HeterosisSubstrate
from .consensus_engine import HeterosisConsensus
from .drift_compensator import ChiralDriftCompensator

class MeshSyncEngine:
    """
    Decentralized Peer Discovery and State Synchronization Engine.
    Executes continuous zero-broker UDP gossip, exchanges instantaneous 
    phase coordinates, and establishes cryptographic phase-locks with adjacent nodes.
    """
    BROADCAST_PORT = 43210
    BUFFER_SIZE = 4096
    MAGIC_HEADER = "HET_SYNC_v1"
    DYNAMIC_PITCH = 3.1730059

    def __init__(self, node_id: str = "node_alpha", seed: str = "bare_metal_origin_dan_kee"):
        self.node_id = node_id
        self.substrate = HeterosisSubstrate(initial_seed=seed)
        self.compensator = ChiralDriftCompensator()
        
        self.running = True
        self.active_peers = {}  # peer_id -> {last_seen, phase_velocity, shared_root}
        self.last_precession = 0.0
        self.state_lock = threading.Lock()

        # Generate initial state step
        self.latest_state = self.substrate.step(ingress_pressure=1.0)

    def _generate_handshake_tag(self, peer_id: str, nonce: str) -> str:
        """Derives a deterministic ephemeral mutual-attestation tag."""
        raw = f"{self.node_id}:{peer_id}:{nonce}:{self.DYNAMIC_PITCH}".encode("utf-8")
        return hmac.new(self.node_id.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    def process_local_pulse(self, base_ingress: float = 1.0) -> dict:
        """Processes an audited closed-loop step with real-time precession compensation."""
        with self.state_lock:
            # Pass restoring_precession directly into substrate step
            state = self.substrate.step(ingress_pressure=base_ingress, restoring_precession=self.last_precession)

            # Calculate continuous drift feedback
            telemetry = self.compensator.calculate_precession({
                "seq": state["seq"],
                "phase_velocity": state["phase_velocity"],
                "net_pressure": state["total_pressure"],
                "macro_leak": state["macro_leak"]
            })
            self.last_precession = telemetry["restoring_precession"]
            state["restoring_precession"] = self.last_precession
            state["compensation_receipt"] = telemetry["compensation_receipt"]
            self.latest_state = state
            return state

    def broadcaster_worker(self):
        """Emits periodic UDP heartbeat broadcasts announcing active state coordinates."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            with self.state_lock:
                nonce = hashlib.sha256(str(time.time_ns()).encode("utf-8")).hexdigest()[:16]
                packet = {
                    "magic": self.MAGIC_HEADER,
                    "type": "GOSSIP_HEARTBEAT",
                    "node_id": self.node_id,
                    "nonce": nonce,
                    "seq": self.latest_state["seq"],
                    "phase_velocity": self.latest_state["phase_velocity"],
                    "macro_leak": self.latest_state["macro_leak"],
                    "restoring_precession": self.latest_state.get("restoring_precession", 0.0),
                    "core_hash": self.latest_state["core_hash"],
                    "timestamp_ns": time.time_ns()
                }

            raw_bytes = json.dumps(packet).encode("utf-8")
            try:
                sock.sendto(raw_bytes, ("<broadcast>", self.BROADCAST_PORT))
            except Exception:
                try:
                    sock.sendto(raw_bytes, ("255.255.255.255", self.BROADCAST_PORT))
                except Exception:
                    pass

            time.sleep(1.5)
        sock.close()

    def listener_worker(self):
        """Listens for remote gossip packets and triggers consensus interlocks."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.bind(("", self.BROADCAST_PORT))
        except Exception as e:
            print(f"[!] Bind Failure on port {self.BROADCAST_PORT}: {e}")
            return

        sock.setblocking(False)

        while self.running:
            readable, _, _ = select.select([sock], [], [], 0.5)
            if not readable:
                continue

            try:
                data, addr = sock.recvfrom(self.BUFFER_SIZE)
                message = json.loads(data.decode("utf-8"))

                # Discard self-broadcasts and malformed packets
                if message.get("node_id") == self.node_id or message.get("magic") != self.MAGIC_HEADER:
                    continue

                msg_type = message.get("type")
                peer_id = message.get("node_id")

                if msg_type == "GOSSIP_HEARTBEAT":
                    # Peer discovered: Calculate geometric consensus interlock
                    with self.state_lock:
                        peer_state = {
                            "seq": message.get("seq"),
                            "phase_velocity": message.get("phase_velocity"),
                            "restoring_precession": message.get("restoring_precession", 0.0),
                            "core_hash": message.get("core_hash")
                        }
                        proof = HeterosisConsensus.interlock(self.latest_state, peer_state)

                    self.active_peers[peer_id] = {
                        "last_seen": time.time(),
                        "phase_velocity": message.get("phase_velocity"),
                        "restoring_precession": message.get("restoring_precession", 0.0),
                        "heterosis_gain": proof["heterosis_gain"],
                        "heterosis_root": proof["heterosis_root"]
                    }

            except Exception:
                continue

        sock.close()

    def start(self):
        """Spins up concurrent network transceiver threads."""
        t_broadcast = threading.Thread(target=self.broadcaster_worker, daemon=True)
        t_listener = threading.Thread(target=self.listener_worker, daemon=True)
        t_broadcast.start()
        t_listener.start()
        return t_broadcast, t_listener

if __name__ == "__main__":
    import sys

    node_label = sys.argv[1] if len(sys.argv) > 1 else "node_primary"
    engine = MeshSyncEngine(node_id=node_label)
    engine.start()

    print(f"[*] Node '{node_label}' online. Listening and broadcasting on port 43210...")
    try:
        for i in range(1, 5):
            st = engine.process_local_pulse(base_ingress=1.0)
            print(f"[STEP {st['seq']}] Velocity: {st['phase_velocity']:.4f} | "
                  f"Leak: {st['macro_leak']:.4f} | "
                  f"Precession: {st['restoring_precession']:>+.6f}")
            print(f"     Active Peers: {list(engine.active_peers.keys())}")
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("\n[-] Terminating mesh sync daemon...")
        engine.running = False
