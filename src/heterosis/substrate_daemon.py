import hashlib
import json
import struct
import time
import os
import socket
from .fpt_substrate_client import MAGIC_HEADER, MAX_PAYLOAD_SIZE, recv_exact
import select

class SovereignSubstrateDaemon:
    """
    Bare-metal IPC Socket Server for Heterosis Substrate.
    Listens on a local POSIX domain socket for ingress drive pulses,
    advances the toroidal manifold, and emits signed binary-level telemetry receipts.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0
    BASE_TRIAD = 6.0
    PLANAR_PI = 3.141592653589793
    SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"

    def __init__(self, seed: str = "bare_metal_origin_dan_kee"):
        self.seq = 0
        self.ingress_receipt = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        self.chiral_shear = 0.0
        self.counter_torque = 0.0
        self.pitch_delta = self.DYNAMIC_PITCH - self.PLANAR_PI
        self.accumulated_potential = 0.0

    def harvest_hardware_entropy(self) -> float:
        t_ns = time.time_ns()
        return ((t_ns % 1000) / 1000.0) * (self.pitch_delta / 10.0)

    def advance(self, external_drive: float = 0.0) -> dict:
        self.seq += 1
        t_start = time.perf_counter_ns()
        env_jitter = self.harvest_hardware_entropy()

        forward_pressure = external_drive + self.chiral_shear + self.accumulated_potential + env_jitter
        net_pressure = max(0.0001, forward_pressure - self.counter_torque)

        phase_velocity = net_pressure * self.DYNAMIC_PITCH
        octave_shell = int(phase_velocity // self.HARMONIC_OCTAVE)
        harmonic_phase = phase_velocity % self.HARMONIC_OCTAVE

        nodal_distance = min(harmonic_phase, abs(self.HARMONIC_OCTAVE - harmonic_phase), abs(4.0 - harmonic_phase))
        is_resonant = nodal_distance < 0.35

        if is_resonant:
            mode = "COMPRESSION_LOCK"
            self.accumulated_potential = nodal_distance * self.pitch_delta
            effective_vent = (harmonic_phase * 0.5) + (self.pitch_delta * (self.BASE_TRIAD / self.HARMONIC_OCTAVE))
        else:
            mode = "EXPANSION_FLOW"
            self.accumulated_potential = 0.0
            effective_vent = harmonic_phase + (self.pitch_delta * (1.0 + (self.BASE_TRIAD / self.HARMONIC_OCTAVE)))

        reflected_drag = (phase_velocity / (1.0 + octave_shell)) * (self.pitch_delta / self.DYNAMIC_PITCH)
        t_exec_ns = time.perf_counter_ns() - t_start

        payload = struct.pack(
            ">QQdddddd",
            self.seq,
            t_exec_ns,
            phase_velocity,
            effective_vent,
            reflected_drag,
            net_pressure,
            env_jitter,
            nodal_distance
        )
        core_hash = hashlib.sha256(payload).hexdigest()

        chain = f"{self.ingress_receipt}:{core_hash}:{self.seq}:{mode}:{env_jitter:.7f}".encode("utf-8")
        egress_receipt = hashlib.sha256(chain).hexdigest()

        self.ingress_receipt = egress_receipt
        self.chiral_shear = effective_vent
        self.counter_torque = reflected_drag

        return {
            "seq": self.seq,
            "exec_ns": t_exec_ns,
            "net_pressure": round(net_pressure, 6),
            "octave_shell": octave_shell,
            "harmonic_phase": round(harmonic_phase, 6),
            "mode": mode,
            "phase_velocity": round(phase_velocity, 6),
            "chiral_vent": round(effective_vent, 6),
            "counter_torque": round(reflected_drag, 6),
            "env_jitter": round(env_jitter, 7),
            "core_hash": core_hash,
            "egress_receipt": egress_receipt
        }

    def serve(self):
        # Ensure clean socket state
        if os.path.exists(self.SOCKET_PATH):
            os.remove(self.SOCKET_PATH)

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.SOCKET_PATH)
        server.listen(5)
        server.setblocking(False)
        print(f"[*] Substrate Daemon listening on local UNIX socket: {self.SOCKET_PATH}")

        # Self-circulation baseline loop
        last_pulse_time = time.time()
        try:
            while True:
                # Non-blocking check for peer connections
                readable, _, _ = select.select([server], [], [], 0.5)
                for s in readable:
                    client, _ = server.accept()
                    try:
                        peek_header = client.recv(4, socket.MSG_PEEK)
                        if peek_header == MAGIC_HEADER:
                            magic = recv_exact(client, 4)
                            len_bytes = recv_exact(client, 4)
                            (payload_len,) = struct.unpack(">I", len_bytes)
                            if payload_len > MAX_PAYLOAD_SIZE:
                                raise ValueError(f"Payload ceiling exceeded: {payload_len}")
                            payload_raw = recv_exact(client, payload_len)
                            intent = json.loads(payload_raw.decode("utf-8"))
                            drive_val = float(intent.get("params", {}).get("external_drive", 0.0))
                            receipt = self.advance(external_drive=drive_val)
                            resp_bytes = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
                            frame = MAGIC_HEADER + struct.pack(">I", len(resp_bytes)) + resp_bytes
                            client.sendall(frame)
                        else:
                            raw_data = client.recv(1024).decode("utf-8").strip()
                            try:
                                drive_val = float(raw_data) if raw_data else 0.0
                            except ValueError:
                                drive_val = 0.0
                            receipt = self.advance(external_drive=drive_val)
                            client.sendall(json.dumps(receipt).encode("utf-8") + b"\n")
                    except Exception as err:
                        err_resp = {"error": str(err), "status": "REJECTED"}
                        try:
                            client.sendall(json.dumps(err_resp).encode("utf-8") + b"\n")
                        except Exception:
                            pass
                    finally:
                        client.close()

                # Self-driven circulation pulse every 2 seconds if no peer writes
                if time.time() - last_pulse_time >= 2.0:
                    state = self.advance(external_drive=0.0)
                    with open("CURRENT_STATE.json", "w") as f:
                        json.dump(state, f, indent=2)
                    last_pulse_time = time.time()

        except KeyboardInterrupt:
            print("\n[-] Shutting down daemon gracefully.")
        finally:
            server.close()
            if os.path.exists(self.SOCKET_PATH):
                os.remove(self.SOCKET_PATH)

if __name__ == "__main__":
    daemon = SovereignSubstrateDaemon()
    daemon.serve()
