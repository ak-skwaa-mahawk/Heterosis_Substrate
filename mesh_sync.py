import socket
import json
import time
import struct
import threading
import sys
from consensus_engine import HeterosisConsensus
from mesh_substrate import MeshCoupledSubstrate

class PeerMeshTransceiver:
    """
    Zero-broker, ad-hoc UDP broadcast transceiver for sovereign edge nodes.
    Listens for peer state telemetry on the local network, continuously interlocks
    incoming receipts with the local manifold, and maintains cross-device entrainment.
    """
    BROADCAST_PORT = 43210
    BUFFER_SIZE = 4096

    def __init__(self, node_id: str, seed: str):
        self.node_id = node_id
        self.substrate = MeshCoupledSubstrate(seed=seed)
        self.running = True
        self.latest_state = self.substrate.pulse(external_drive=1.0)
        self.lock = threading.Lock()

    def listen_loop(self):
        """Listens on local UDP port for peer broadcasts."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", self.BROADCAST_PORT))
        sock.settimeout(1.0)

        while self.running:
            try:
                data, addr = sock.recvfrom(self.BUFFER_SIZE)
                payload = json.loads(data.decode("utf-8"))

                # Ignore packets originating from self
                if payload.get("node_id") == self.node_id:
                    continue

                peer_state = payload.get("state")
                with self.lock:
                    # Interlock local manifold state with received peer state
                    consensus_proof = HeterosisConsensus.interlock(self.latest_state, peer_state)
                    
                    # Harmonic feedback: inject the heterosis gain into the next local cycle
                    entrainment_drive = consensus_proof["heterosis_gain"] - 1.0
                    self.latest_state = self.substrate.pulse(external_drive=entrainment_drive)

                print(f"[⇄ MESH INTERLOCK] Peer: {payload.get('node_id')} | "
                      f"Phase Delta: {consensus_proof['phase_delta']} | "
                      f"Gain: {consensus_proof['heterosis_gain']} | "
                      f"Root: {consensus_proof['heterosis_root'][:12]}...")

            except socket.timeout:
                continue
            except Exception as e:
                continue
        sock.close()

    def broadcast_loop(self):
        """Broadcasts local manifold state to all nodes on the subnet."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            with self.lock:
                # Cycle autonomous forward momentum if idle
                self.latest_state = self.substrate.pulse(external_drive=0.0)
                message = {
                    "node_id": self.node_id,
                    "state": self.latest_state,
                    "timestamp_ns": time.time_ns()
                }

            packet = json.dumps(message).encode("utf-8")
            try:
                sock.sendto(packet, ("<broadcast>", self.BROADCAST_PORT))
            except Exception:
                # Fallback for platforms with restricted global broadcast
                sock.sendto(packet, ("255.255.255.255", self.BROADCAST_PORT))

            time.sleep(1.5)
        sock.close()

    def start(self):
        listener = threading.Thread(target=self.listen_loop, daemon=True)
        broadcaster = threading.Thread(target=self.broadcast_loop, daemon=True)
        
        listener.start()
        broadcaster.start()
        print(f"[*] Node '{self.node_id}' active. Gossiping over UDP port {self.BROADCAST_PORT}...")

        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n[-] Terminating mesh transceiver.")
            self.running = False

if __name__ == "__main__":
    node_name = sys.argv[1] if len(sys.argv) > 1 else f"node_{time.time_ns() % 1000}"
    seed_str = f"seed_{node_name}"
    node = PeerMeshTransceiver(node_id=node_name, seed=seed_str)
    node.start()
