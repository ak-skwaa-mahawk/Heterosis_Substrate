import socket
import sys

SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"

def pulse_daemon(drive: float):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(SOCKET_PATH)
        client.sendall(f"{drive}".encode("utf-8"))
        response = client.recv(4096).decode("utf-8")
        print(response)
    finally:
        client.close()

if __name__ == "__main__":
    drive = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    pulse_daemon(drive)
