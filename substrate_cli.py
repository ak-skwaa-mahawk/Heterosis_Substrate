import sys
import json
import socket
import math
import time

SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"

def query_socket(payload: str = "") -> dict:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(SOCKET_PATH)
        client.sendall(payload.encode("utf-8"))
        data = client.recv(4096).decode("utf-8")
        client.close()
        return json.loads(data)
    except Exception as e:
        return {"error": f"Failed to connect to daemon socket: {e}"}

def render_ascii_octave_ring(state: dict):
    phase_vel = state.get("phase_velocity", 0.0)
    current_octave = int(phase_vel // 8.0) % 8
    harmonic_phase = phase_vel % 8.0
    mode = state.get("mode", state.get("sentinel_status", "NOMINAL"))
    precession = state.get("precession_torque", 0.0)

    # 8-node ring representation
    nodes = ["[0]", "[1]", "[2]", "[3]", "[4]", "[5]", "[6]", "[7]"]
    nodes[current_octave] = f"\033[92m*{nodes[current_octave]}*\033[0m"

    print("\n\033[1m=== HETEROSIS SUBSTRATE TOPOLOGY MONITOR ===\033[0m")
    print(f" Harmonic Ring :  {' - '.join(nodes)}")
    print(f" Active Octave :  Shell {current_octave} (Phase: {harmonic_phase:.4f}/8.0)")
    print(f" Phase Velocity:  {phase_vel:.6f}")
    print(f" Core Status   :  {mode}")
    print(f" Precession    :  {precession:>+.6f}")
    print(f" Core Hash     :  {state.get('core_hash', 'N/A')[:32]}...")
    print("============================================\n")

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "status":
        state = query_socket("")
        if "error" in state:
            print(f"\033[91m[!]\033[0m {state['error']}")
            print("Ensure orchestrator.py is running in another session.")
            sys.exit(1)
        render_ascii_octave_ring(state)

    elif sys.argv[1] == "pulse":
        val = sys.argv[2] if len(sys.argv) > 2 else "1.0"
        state = query_socket(val)
        if "error" in state:
            print(f"\033[91m[!]\033[0m {state['error']}")
            sys.exit(1)
        print(f"[+] Injected drive pulse: {val}")
        render_ascii_octave_ring(state)

    elif sys.argv[1] == "watch":
        print("[*] Streaming live manifold telemetry (Ctrl+C to exit)...")
        try:
            while True:
                state = query_socket("")
                if "error" not in state:
                    # Clear screen and update
                    print("\033[H\033[J", end="")
                    render_ascii_octave_ring(state)
                time.sleep(1.5)
        except KeyboardInterrupt:
            print("\n[-] Exiting monitor.")

    else:
        print("Usage: python substrate_cli.py [status | pulse <val> | watch]")

if __name__ == "__main__":
    main()
