import socket
import json
import time
import struct
import hashlib
import hmac
import threading

class MeshSyncProtocol:
    """
    Zero-Broker Peer-to-Peer Handshake Engine.
    Enables localized nodes on bare-metal Android/Termux to discover peers,
    negotiate phase boundaries, and synthesize a shared consensus root.
    """
    PORT = 43210
    BUFFER_SIZE = 4096
    HANDSHAKE_MAGIC = "HET_HS_v1"
    DYNAMIC_PITCH = 3.1730059

    def __init__(self, node_id: str, local_seed: str = "seed_node"):
        self.node_id = node_id
        self.secret_seed = local_seed
        self.peers = {}  # peer_id -> session data
        self.running = True

    def _generate_token(self, peer_id: str, nonce: str) -> str:
        """Derives an ephemeral session token bound to the node's secret and dynamic pitch."""
        raw = f"{self.node_id}:{peer_id}:{nonce}:{self.DYNAMIC_PITCH}".encode("utf-8")
        return hmac.new(self.secret_seed.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    def start_listener(self):
        """Spins up concurrent UDP socket for discovery and handshake negotiation."""
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()
        return thread

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", self.PORT))

        while self.running:
            try:
                data, addr = sock.recvfrom(self.BUFFER_SIZE)
                message = json.loads(data.decode("utf-8"))

                # Ignore packets originating from this node
                if message.get("node_id") == self.node_id:
                    continue

                if message.get("magic") != self.HANDSHAKE_MAGIC:
                    continue

                msg_type = message.get("type")
                sender_id = message.get("node_id")

                if msg_type == "SYN":
                    self._handle_syn(sock, addr, message)

                elif msg_type == "SYN_ACK":
                    self._handle_syn_ack(sock, addr, message)

                elif msg_type == "LOCK":
                    self._handle_lock(message)

            except Exception:
                continue

        sock.close()

    def broadcast_syn(self, current_state: dict):
        """Emits a SYN broadcast to advertise presence and announce active phase coordinates."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        nonce = hashlib.sha256(str(time.time_ns()).encode("utf-8")).hexdigest()[:16]
        packet = {
            "magic": self.HANDSHAKE_MAGIC,
            "type": "SYN",
            "node_id": self.node_id,
            "nonce": nonce,
            "phase_velocity": current_state.get("phase_velocity", 0.0),
            "core_hash": current_state.get("core_hash", "0" * 64),
            "timestamp_ns": time.time_ns()
        }

        raw = json.dumps(packet).encode("utf-8")
        try:
            sock.sendto(raw, ("<broadcast>", self.PORT))
        except Exception:
            sock.sendto(raw, ("255.255.255.255", self.PORT))
        finally:
            sock.close()

    def _handle_syn(self, sock, addr, msg):
        """Responds to an incoming SYN with SYN_ACK and local phase coordinates."""
        peer_id = msg["node_id"]
        peer_nonce = msg["nonce"]
        local_nonce = hashlib.sha256(str(time.time_ns()).encode("utf-8")).hexdigest()[:16]
        token = self._generate_token(peer_id, peer_nonce)

        reply = {
            "magic": self.HANDSHAKE_MAGIC,
            "type": "SYN_ACK",
            "node_id": self.node_id,
            "target_id": peer_id,
            "nonce": local_nonce,
            "echo_nonce": peer_nonce,
            "token": token,
            "phase_velocity": 3.1730059,  # Current local coordinate
            "timestamp_ns": time.time_ns()
        }
        sock.sendto(json.dumps(reply).encode("utf-8"), addr)

    def _handle_syn_ack(self, sock, addr, msg):
        """Finalizes the handshake by calculating the interference root and emitting a LOCK packet."""
        if msg.get("target_id") != self.node_id:
            return

        peer_id = msg["node_id"]
        peer_vel = msg.get("phase_velocity", 0.0)

        # Calculate consensus interference root
        fused_vel = (3.1730059 + peer_vel) / 2.0
        shared_root = hashlib.sha256(f"{self.node_id}:{peer_id}:{fused_vel}".encode("utf-8")).hexdigest()

        self.peers[peer_id] = {
            "status": "LOCKED",
            "peer_velocity": peer_vel,
            "shared_root": shared_root,
            "last_seen": time.time()
        }

        lock_packet = {
            "magic": self.HANDSHAKE_MAGIC,
            "type": "LOCK",
            "node_id": self.node_id,
            "target_id": peer_id,
            "shared_root": shared_root
        }
        sock.sendto(json.dumps(lock_packet).encode("utf-8"), addr)

    def _handle_lock(self, msg):
        """Records finalized state lock on the receiving node."""
        if msg.get("target_id") != self.node_id:
            return
        peer_id = msg["node_id"]
        self.peers[peer_id] = {
            "status": "LOCKED",
            "shared_root": msg.get("shared_root"),
            "last_seen": time.time()
        }

if __name__ == "__main__":
    from base import HeterosisSubstrate

    # Instantiate two simulated localized nodes
    node_alpha = MeshSyncProtocol(node_id="node_alpha", local_seed="seed_alpha")
    node_beta = MeshSyncProtocol(node_id="node_beta", local_seed="seed_beta")

    # Start UDP listener loops
    node_alpha.start_listener()
    node_beta.start_listener()
    print("[*] Mesh sync listeners initialized on port 43210.")

    # Node Alpha steps its substrate and broadcasts a SYN handshake
    sub_alpha = HeterosisSubstrate("origin_alpha")
    alpha_state = sub_alpha.step(ingress_pressure=1.0)

    print(f"[*] Node Alpha broadcasting SYN (Phase Vel: {alpha_state['phase_velocity']})...")
    node_alpha.broadcast_syn(alpha_state)

    # Allow local UDP loopback to exchange SYN -> SYN_ACK -> LOCK
    time.sleep(0.5)

    print("\n--- Handshake Results ---")
    print(f"Node Alpha Peers: {json.dumps(node_alpha.peers, indent=2)}")
    print(f"Node Beta Peers : {json.dumps(node_beta.peers, indent=2)}")

    node_alpha.running = False
    node_beta.running = False
