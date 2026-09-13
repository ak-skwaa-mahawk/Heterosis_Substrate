import os
import sys
import time
import json
import socket
import select
import threading

from mesh_substrate import MeshCoupledSubstrate
from drift_compensator import ChiralDriftCompensator
from tripwire_sentinel import SubstrateTripwire
from consensus_engine import HeterosisConsensus

class MasterSubstrateOrchestrator:
    """
    Sovereign Headless Orchestrator.
    Binds POSIX domain socket IPC, hardware entropy sampling, drift precession,
    sentinel tripwire defenses, and zero-broker UDP peer mesh synchronization.
    """
    SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"
    BROADCAST_PORT = 43210
    BUFFER_SIZE = 4096

    def __init__(self, node_id: str = "sovereign_core", seed: str = "bare_metal_origin_dan_kee"):
        self.node_id = node_id
        self.substrate = MeshCoupledSubstrate(seed=seed)
        self.compensator = ChiralDriftCompensator()
        self.sentinel = SubstrateTripwire()
        
        self.running = True
        self.state_lock = threading.Lock()
        self.latest_state = self.substrate.pulse(external_drive=1.0)
        self.active_precession = 0.0

    def step_manifold(self, external_drive: float = 0.0) -> dict:
        """Executes a fully audited cycle through the integrated pipeline."""
        with self.state_lock:
            # 1. Apply compensating micro-precession to intake pressure
            adjusted_drive = max(0.0, external_drive + self.active_precession)
            
            # 2. Advance core physics on bare metal
            raw_state = self.substrate.pulse(external_drive=adjusted_drive)
            
            # 3. Sentinel audit & fault checking
            is_safe, damping_torque, diag_code = self.sentinel.evaluate_boundary(raw_state)
            if not is_safe:
                # Apply emergency dampening to internal shear
                self.substrate.chiral_shear = max(0.0, self.substrate.chiral_shear + damping_torque)
                raw_state["sentinel_status"] = f"FAULT_DAMPENED:{diag_code}"
            else:
                raw_state["sentinel_status"] = "STABLE"

            # 4. Update phase drift tracking and calculate next precession bias
            comp_receipt = self.compensator.calculate_precession(raw_state)
            self.active_precession = comp_receipt["restoring_precession"]
            
            raw_state["precession_torque"] = self.active_precession
            self.latest_state = raw_state

            # Write atomic runtime state to disk for local observers
            with open("CURRENT_STATE.json", "w") as f:
                json.dump(raw_state, f, indent=2)

            return raw_state

    def ipc_listener_worker(self):
        """Manages local UNIX domain socket for on-device commands."""
        # Clean stale socket
        if os.path.exists(self.SOCKET_PATH):
            os.remove(self.SOCKET_PATH)

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.SOCKET_PATH)
        server.listen(5)
        server.setblocking(False)

        while self.running:
            try:
                readable, _, _ = select.select([server], [], [], 0.5)
                for s in readable:
                    client, _ = server.accept()
                    raw = client.recv(1024).decode("utf-8").strip()
                    try:
                        drive = float(raw) if raw else 0.0
                    except ValueError:
                        drive = 0.0

                    result = self.step_manifold(external_drive=drive)
                    client.sendall(json.dumps(result).encode("utf-8") + b"\n")
                    client.close()
            except Exception:
                continue

        server.close()
        if os.path.exists(self.SOCKET_PATH):
            os.remove(self.SOCKET_PATH)

    def udp_mesh_listener_worker(self):
        """Listens for remote peer state broadcasts and executes consensus interlocks."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.bind(("", self.BROADCAST_PORT))
        except Exception as e:
            print(f"[!] UDP Bind Failure: {e}")
            return

        sock.settimeout(1.0)

        while self.running:
            try:
                data, _ = sock.recvfrom(self.BUFFER_SIZE)
                payload = json.loads(data.decode("utf-8"))

                # Discard self-originated packets
                if payload.get("node_id") == self.node_id:
                    continue

                peer_state = payload.get("state", {})
                with self.state_lock:
                    # Synthesize hybrid vigor via consensus engine
                    proof = HeterosisConsensus.interlock(self.latest_state, peer_state)
                    entrainment_drive = max(0.0, proof["heterosis_gain"] - 1.0)

                # Feed consensus delta into next step
                self.step_manifold(external_drive=entrainment_drive)

            except socket.timeout:
                continue
            except Exception:
                continue

        sock.close()

    def udp_mesh_broadcaster_worker(self):
        """Broadcasts current manifold telemetry to local network peers."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            with self.state_lock:
                message = {
                    "node_id": self.node_id,
                    "state": self.latest_state,
                    "timestamp_ns": time.time_ns()
                }

            packet = json.dumps(message).encode("utf-8")
            try:
                sock.sendto(packet, ("<broadcast>", self.BROADCAST_PORT))
            except Exception:
                try:
                    sock.sendto(packet, ("255.255.255.255", self.BROADCAST_PORT))
                except Exception:
                    pass

            time.sleep(2.0)
        sock.close()

    def start(self):
        print(f"[*] Starting Master Substrate Orchestrator: Node '{self.node_id}'")
        
        # Spin up concurrent operational threads
        t_ipc = threading.Thread(target=self.ipc_listener_worker, daemon=True)
        t_udp_in = threading.Thread(target=self.udp_mesh_listener_worker, daemon=True)
        t_udp_out = threading.Thread(target=self.udp_mesh_broadcaster_worker, daemon=True)

        t_ipc.start()
        t_udp_in.start()
        t_udp_out.start()

        print("[+] IPC listening on UNIX socket.")
        print("[+] Mesh transceiver bound to UDP port 43210.")
        print("[+] Autonomous manifold cycle initialized.\n")

        # Main thread loop maintains sovereign internal cadence
        try:
            while True:
                # Cycle autonomous forward momentum every 3 seconds
                state = self.step_manifold(external_drive=0.0)
                print(f"[CYCLE {state['seq']:04d}] Phase Vel: {state['phase_velocity']:>8.4f} | "
                      f"Mode: {state.get('mode', 'N/A')} | "
                      f"Sentinel: {state['sentinel_status']} | "
                      f"Precession: {state['precession_torque']:>9.6f}")
                time.sleep(3.0)

        except KeyboardInterrupt:
            print("\n[-] Shutting down Master Orchestrator gracefully...")
            self.running = False
            time.sleep(0.5)

if __name__ == "__main__":
    node_name = sys.argv[1] if len(sys.argv) > 1 else f"node_{os.getpid()}"
    orchestrator = MasterSubstrateOrchestrator(node_id=node_name)
    orchestrator.start()
