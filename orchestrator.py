import hashlib
import json
import os
import select
import socket
import struct
import sys
import threading
import time

from mesh_substrate import MeshCoupledSubstrate
from drift_compensator import ChiralDriftCompensator
from tripwire_sentinel import SubstrateTripwire
from adaptive_resonator import AdaptiveResonator
from consensus_engine import HeterosisConsensus

SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"

class MasterSubstrateOrchestrator:
    """
    Unified Sovereign Orchestrator.
    Fuses POSIX nanosecond clock entropy (MeshCoupledSubstrate),
    acoustic waveguide damping (AdaptiveResonator), closed-loop precession
    compensation (ChiralDriftCompensator), boundary sentinel defense (SubstrateTripwire),
    and peer consensus interlocks over UDP port 43210.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BROADCAST_PORT = 43210
    BUFFER_SIZE = 4096

    def __init__(self, node_id: str = "sovereign_core", seed: str = "bare_metal_origin_dan_kee"):
        self.node_id = node_id
        self.substrate = MeshCoupledSubstrate(seed=seed)
        self.compensator = ChiralDriftCompensator()
        self.sentinel = SubstrateTripwire()
        self.waveguide = AdaptiveResonator()

        self.running = True
        self.state_lock = threading.Lock()
        self.active_precession = 0.0
        self.last_shear = 0.0
        self.last_drag = 0.0

        # Ensure runtime IPC socket directory exists
        sock_dir = os.path.dirname(SOCKET_PATH)
        if not os.path.exists(sock_dir):
            os.makedirs(sock_dir, exist_ok=True)
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        # Prime initial state
        self.latest_state = self.step_manifold(external_drive=1.0)

    def step_manifold(self, external_drive: float = 0.0) -> dict:
        """
        Executes a closed-loop manifold cycle:
        Precession -> Hardware Pulse -> Waveguide Damping -> Sentinel Audit -> State Commit
        """
        with self.state_lock:
            # 1. Closed-loop precession compensation on intake
            adjusted_drive = max(0.0001, external_drive + self.active_precession)

            # 2. Advance core physics coupled to hardware clock jitter
            raw_state = self.substrate.pulse(external_drive=adjusted_drive)
            raw_velocity = raw_state["phase_velocity"]

            # 3. Waveguide Transfer Filter: Damp phase velocity spikes prior to sentinel audit
            filter_res = self.waveguide.balance_step(
                phase_velocity=raw_velocity,
                macro_leak=self.last_shear,
                counter_torque=self.last_drag,
                ingress_pressure=adjusted_drive
            )

            balanced_velocity = filter_res["balanced_velocity"]
            effective_shear = filter_res["effective_shear"]
            reflected_drag = filter_res["reflected_drag"]
            filter_mode = filter_res["mode"]
            filter_seal = filter_res["harmonic_seal"]

            # 4. Tripwire Sentinel Audit against balanced velocity
            audit_target = {
                "seq": raw_state["seq"],
                "phase_velocity": balanced_velocity,
                "chiral_vent": effective_shear,
                "net_pressure": raw_state["net_pressure"]
            }
            is_safe, damping_torque, diag_code = self.sentinel.evaluate_boundary(audit_target)

            if not is_safe:
                balanced_velocity = max(0.0001, balanced_velocity + damping_torque)
                self.substrate.chiral_shear = max(0.0, self.substrate.chiral_shear + damping_torque)
                sentinel_status = f"FAULT_DAMPENED:{diag_code}"
            else:
                sentinel_status = "STABLE"

            # 5. Calculate phase drift tracking and calculate next precession bias
            comp_receipt = self.compensator.calculate_precession({
                "seq": raw_state["seq"],
                "phase_velocity": balanced_velocity,
                "net_pressure": raw_state["net_pressure"],
                "macro_leak": effective_shear
            })
            self.active_precession = comp_receipt["restoring_precession"]
            self.last_shear = effective_shear
            self.last_drag = reflected_drag

            # Update working telemetry
            final_record = {
                "seq": raw_state["seq"],
                "exec_ns": raw_state["exec_ns"],
                "ingress_drive": round(external_drive, 6),
                "adjusted_drive": round(adjusted_drive, 6),
                "net_pressure": raw_state["net_pressure"],
                "raw_velocity": round(raw_velocity, 6),
                "phase_velocity": round(balanced_velocity, 6),
                "octave_shell": filter_res["octave_shell"],
                "harmonic_phase": filter_res["harmonic_phase"],
                "filter_mode": filter_mode,
                "filter_seal": filter_seal,
                "effective_shear": round(effective_shear, 6),
                "env_jitter": raw_state.get("env_jitter", 0.0),
                "sentinel_status": sentinel_status,
                "precession_torque": round(self.active_precession, 6),
                "compensation_receipt": comp_receipt["compensation_receipt"],
                "core_hash": raw_state["core_hash"],
                "egress_receipt": raw_state["egress_receipt"]
            }

            self.latest_state = final_record

            # Atomic snapshot for local observers (CLI / watchdog)
            with open("CURRENT_STATE.json", "w") as f:
                json.dump(final_record, f, indent=2)

            return final_record

    def ipc_listener_worker(self):
        """Manages local UNIX domain socket for on-device commands and telemetry streaming."""
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(SOCKET_PATH)
        server.listen(5)
        server.setblocking(False)

        while self.running:
            try:
                readable, _, _ = select.select([server], [], [], 0.5)
                for s in readable:
                    client, _ = server.accept()
                    raw = client.recv(1024).decode("utf-8").strip()

                    if raw.startswith("pulse"):
                        parts = raw.split()
                        drive = float(parts[1]) if len(parts) > 1 else 1.0
                    else:
                        try:
                            drive = float(raw) if raw else 0.0
                        except ValueError:
                            drive = 0.0

                    if drive > 0.0:
                        result = self.step_manifold(external_drive=drive)
                    else:
                        with self.state_lock:
                            result = self.latest_state

                    client.sendall(json.dumps(result).encode("utf-8") + b"\n")
                    client.close()
            except Exception:
                continue

        server.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

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

                if payload.get("node_id") == self.node_id:
                    continue

                peer_state = payload.get("state", {})
                with self.state_lock:
                    proof = HeterosisConsensus.interlock(self.latest_state, peer_state)
                    entrainment_drive = max(0.0, proof["heterosis_gain"] - 1.0)

                if entrainment_drive > 0.001:
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

        t_ipc = threading.Thread(target=self.ipc_listener_worker, daemon=True)
        t_udp_in = threading.Thread(target=self.udp_mesh_listener_worker, daemon=True)
        t_udp_out = threading.Thread(target=self.udp_mesh_broadcaster_worker, daemon=True)

        t_ipc.start()
        t_udp_in.start()
        t_udp_out.start()

        print(f"[+] IPC socket listening: {SOCKET_PATH}")
        print(f"[+] Mesh transceiver active on UDP port {self.BROADCAST_PORT}")
        print(f"[+] Waveguide Filter Active: Dynamic Pitch = {self.DYNAMIC_PITCH}\n")

        try:
            while self.running:
                state = self.step_manifold(external_drive=0.0)
                print(f"[CYCLE {state['seq']:04d}] Vel: {state['phase_velocity']:>7.3f} | "
                      f"Mode: {state['filter_mode']:<18} | "
                      f"Sentinel: {state['sentinel_status']:<6} | "
                      f"Torque: {state['precession_torque']:>+8.5f}")
                time.sleep(2.5)
        except KeyboardInterrupt:
            print("\n[-] Shutting down Master Orchestrator gracefully...")
            self.running = False
            time.sleep(0.5)
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)

# Aliases for compatibility
SovereignOrchestrator = MasterSubstrateOrchestrator

if __name__ == "__main__":
    node_name = sys.argv[1] if len(sys.argv) > 1 else f"node_{os.getpid()}"
    orchestrator = MasterSubstrateOrchestrator(node_id=node_name)
    orchestrator.start()
