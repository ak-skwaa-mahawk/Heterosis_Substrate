import hashlib
import json
import os
import select
import shutil
import socket
import struct
import subprocess
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
    decentralized peer consensus over UDP port 43210, and native Android push notifications.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BROADCAST_PORT = 43210
    BUFFER_SIZE = 4096
    ALERT_COOLDOWN_SEC = 5.0

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
        self.last_alert_time = 0.0

        # Verify whether termux-notification binary exists on PATH
        self.has_termux_api = shutil.which("termux-notification") is not None

        # Ensure runtime IPC socket directory exists
        sock_dir = os.path.dirname(SOCKET_PATH)
        if not os.path.exists(sock_dir):
            os.makedirs(sock_dir, exist_ok=True)
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        # Prime initial state
        self.latest_state = self.step_manifold(external_drive=1.0)

    def _trigger_android_alert(self, diag_code: str, velocity: float, damping_torque: float):
        """Dispatches an asynchronous termux-notification to avoid stalling the tick rate."""
        now = time.time()
        if now - self.last_alert_time < self.ALERT_COOLDOWN_SEC:
            return

        self.last_alert_time = now

        def _notify():
            if not self.has_termux_api:
                return
            title = f"[HETEROSIS TRIPWIRE] {diag_code}"
            content = (
                f"Velocity: {velocity:.4f} | Torque: {damping_torque:.4f} | "
                f"Node: {self.node_id}"
            )
            cmd = [
                "termux-notification",
                "--id", "heterosis_sentinel",
                "-t", title,
                "-c", content,
                "--priority", "high",
                "--sound"
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0)
            except Exception:
                pass

        threading.Thread(target=_notify, daemon=True).start()

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
                # Emit hardware notification
                self._trigger_android_alert(diag_code, raw_velocity, damping_torque)
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

            # Atomic snapshot for local observers
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
        """Listens for remote peer payloads across the decentralized interlock mesh network."""
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp_sock.bind(("0.0.0.0", self.BROADCAST_PORT))
            udp_sock.setblocking(False)
        except Exception as e:
            print(f"[Orchestrator] Failed to bind UDP listener: {e}", file=sys.stderr)
            return

        while self.running:
            try:
                readable, _, _ = select.select([udp_sock], [], [], 0.5)
                for s in readable:
                    data, addr = s.recvfrom(self.BUFFER_SIZE)
                    try:
                        payload = json.loads(data.decode("utf-8"))
                        interlock_status = HeterosisConsensus.interlock(payload, self.latest_state)
                        if interlock_status.get("trigger_pulse", False):
                            self.step_manifold(external_drive=interlock_status.get("pulse_weight", 0.5))
                    except (json.JSONDecodeError, KeyError, AttributeError):
                        continue
            except Exception:
                continue

        udp_sock.close()

    def boot(self):
        """Sparks runtime worker threads to life."""
        self.running = True
        self.ipc_thread = threading.Thread(target=self.ipc_listener_worker, daemon=True)
        self.udp_thread = threading.Thread(target=self.udp_mesh_listener_worker, daemon=True)

        self.ipc_thread.start()
        self.udp_thread.start()
        print(f"[Orchestrator] Sovereign daemon live on IPC {SOCKET_PATH} and UDP {self.BROADCAST_PORT}")
        print(f"[Orchestrator] Android Notification Alerts: {'ENABLED' if self.has_termux_api else 'DISABLED (Install termux-api)'}")

    def shutdown(self):
        """Gracefully tears down daemon threads and unlinks system hooks."""
        self.running = False
        print("[Orchestrator] Halting manifold processing gracefully...")
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

if __name__ == "__main__":
    orchestrator = MasterSubstrateOrchestrator()
    orchestrator.boot()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        orchestrator.shutdown()
