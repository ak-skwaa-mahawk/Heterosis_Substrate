import os, sys, time, signal, shutil, subprocess
SOCKET_PATH="/data/data/com.termux/files/usr/tmp/heterosis.sock"
DAEMON_SCRIPT="orchestrator.py"
LOG_FILE="orchestrator_runtime.log"
CRASH_THRESHOLD_SEC=3.0
BACKOFF_DELAY=1.0
MAX_BACKOFF=30.0
running=True
current_proc=None

def cleanup(signum=None, frame=None):
    global running, current_proc
    running=False
    print("\n[Supervisor] Stopping daemon...")
    if current_proc and current_proc.poll() is None:
        try: current_proc.terminate(); current_proc.wait(timeout=2.0)
        except: current_proc.kill()
    if os.path.exists(SOCKET_PATH):
        try: os.remove(SOCKET_PATH)
        except OSError: pass
    if shutil.which("termux-wake-unlock"):
        subprocess.run(["termux-wake-unlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

if shutil.which("termux-wake-lock"):
    subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

backoff=BACKOFF_DELAY

while running:
    if os.path.exists(SOCKET_PATH):
        try: os.remove(SOCKET_PATH)
        except OSError: pass
    start_time=time.time()
    with open(LOG_FILE, "a") as log_fp:
        print(f"[Supervisor] Spawning {DAEMON_SCRIPT} at {time.strftime('%Y-%m-%d %H:MM:%S')}")
        current_proc=subprocess.Popen([sys.executable, DAEMON_SCRIPT], stdout=log_fp, stderr=subprocess.STDOUT)
        exit_code=current_proc.wait()
    lifetime=time.time()-start_time
    print(f"[Supervisor] Daemon exited code {exit_code} after {lifetime:.1}s")
    if running == False: break
    if lifetime < CRASH_THRESHOLD_SEC:
        print(f"[Supervisor] Backing off for {backoff:.1}s...")
        time.sleep(backoff)
        backoff=min(MAX_BACKOFF, backoff * 2.0)
    else:
        backoff=BACKOFF_DELAY
        time.sleep(0.5)
