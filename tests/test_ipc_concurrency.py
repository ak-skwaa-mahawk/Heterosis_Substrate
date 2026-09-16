import os
import sys
import time
import socket
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

SOCK_PATH = "/data/data/com.termux/files/usr/tmp/heterosis_test.sock"

def test_concurrent_socket_pulses():
    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    # Start daemon pointing to test socket
    daemon = subprocess.Popen(
        [sys.executable, "-m", "heterosis.substrate_daemon"],
        env=env
    )

    default_sock = "/data/data/com.termux/files/usr/tmp/heterosis.sock"
    target_sock = default_sock

    for _ in range(50):
        if os.path.exists(target_sock):
            break
        time.sleep(0.05)

    assert os.path.exists(target_sock), "Substrate daemon failed to bind UNIX socket"

    def raw_socket_pulse(worker_id, seq):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(target_sock)
                drive = 0.05 * (seq % 8)
                s.sendall(f"{drive:.4f}\n".encode("utf-8"))
                response = s.recv(4096)
                if response:
                    data = json.loads(response.decode("utf-8"))
                    return data.get("seq") is not None or "egress_receipt" in data or "receipt" in data
            return False
        except Exception:
            return False

    tasks = [(c, s) for c in range(4) for s in range(25)]
    start = time.perf_counter_ns()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(raw_socket_pulse, c, s) for c, s in tasks]
        results = [f.result() for f in as_completed(futures)]

    dur_ms = (time.perf_counter_ns() - start) / 1e6
    successful = sum(1 for r in results if r)

    daemon.terminate()
    daemon.wait()
    if os.path.exists(target_sock):
        os.remove(target_sock)

    assert successful == len(tasks), f"Expected {len(tasks)} successes, got {successful}"
    assert dur_ms < 5000.0, f"IPC concurrency test took too long: {dur_ms:.2f} ms"

if __name__ == "__main__":
    test_concurrent_socket_pulses()
    print("All 100 concurrent IPC transactions passed.")
