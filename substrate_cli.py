import sys
import json
import socket
import select
import time
import os

SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"

def query_socket(payload: str = "") -> dict:
    if not os.path.exists(SOCKET_PATH):
        return {"error": f"Socket not found at {SOCKET_PATH}. Is orchestrator.py active?"}

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.settimeout(2.0)
        client.connect(SOCKET_PATH)
        
        # Guarantee a terminator is sent so recv() doesn't hang
        msg = payload.strip() if payload else "status"
        client.sendall((msg + "\n").encode("utf-8"))
        
        chunks = []
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        client.close()
        
        raw_resp = b"".join(chunks).decode("utf-8").strip()
        return json.loads(raw_resp) if raw_resp else {}
    except Exception as e:
        return {"error": f"IPC transmission failure: {e}"}

def render_dashboard(state: dict):
    if "error" in state:
        print(f"\033[91m[!]\033[0m {state['error']}")
        return

    seq = state.get("seq", 0)
    phase_vel = state.get("phase_velocity", 0.0)
    raw_vel = state.get("raw_velocity", 0.0)
    current_shell = state.get("octave_shell", int(phase_vel // 8.0) % 8)
    harmonic_phase = state.get("harmonic_phase", phase_vel % 8.0)
    filter_mode = state.get("filter_mode", "N/A")
    sentinel = state.get("sentinel_status", "NOMINAL")
    precession = state.get("precession_torque", 0.0)
    effective_shear = state.get("effective_shear", 0.0)
    core_hash = state.get("core_hash", "0" * 64)
    egress = state.get("egress_receipt", "0" * 64)

    ring_nodes = []
    for i in range(8):
        if i == current_shell:
            ring_nodes.append(f"\033[92m[{i}:ACTIVE]\033[0m")
        else:
            ring_nodes.append(f"\033[90m[{i}]\033[0m")
    ring_display = " - ".join(ring_nodes)

    print("\033[H\033[J", end="")
    print("╔═[ HETEROSIS MANIFOLD: EDGE TELEMETRY MONITOR ]══════════════════════════╗")
    print(f"║ Sequence Cycle : {seq:<8} | Execution Time: {state.get('exec_ns', 0):>8} ns                ║")
    print("╠═════════════════════════════════════════════════════════════════════════╣")
    print(f"║ 8-Octave Shell : {ring_display}    ║")
    print(f"║ Active Shell   : Shell [{current_shell}] (Phase offset: {harmonic_phase:>6.4f}/8.0)                ║")
    print(f"║ Raw Velocity   : {raw_vel:>10.6f} -> Balanced Velocity: {phase_vel:>10.6f}      ║")
    print(f"║ Acoustic Filter: {filter_mode:<18} | Shear Leak Vent: {effective_shear:>10.6f}      ║")
    print(f"║ Tripwire State : {sentinel:<18} | Precession Bias: {precession:>+10.6f}      ║")
    print("╠═════════════════════════════════════════════════════════════════════════╣")
    print(f"║ Core Hash      : {core_hash[:48]}... ║")
    print(f"║ Egress Receipt : {egress[:48]}... ║")
    print("╚═════════════════════════════════════════════════════════════════════════╝")
    print(" Commands: [Ctrl+C] Detach Monitor | In another tab: python substrate_cli.py pulse <val>")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"

    if cmd == "status":
        state = query_socket("status")
        render_dashboard(state)

    elif cmd == "pulse":
        val = sys.argv[2] if len(sys.argv) > 2 else "1.0"
        print(f"[*] Injecting physical pressure pulse ({val}) into IPC socket...")
        state = query_socket(f"pulse {val}")
        render_dashboard(state)

    elif cmd == "watch":
        try:
            while True:
                state = query_socket("status")
                render_dashboard(state)
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n[-] Telemetry monitor detached.")

    else:
        print("Usage: python substrate_cli.py [watch | status | pulse <value>]")

if __name__ == "__main__":
    main()
