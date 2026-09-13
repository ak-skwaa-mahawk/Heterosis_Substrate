import json
import socket
import struct
from typing import Dict, Any

SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"
MAGIC_HEADER = b"HET1"
MAX_PAYLOAD_SIZE = 65536

def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed prematurely while reading expected bytes")
        buf.extend(chunk)
    return bytes(buf)

class SubstrateIPCClient:
    def __init__(self, socket_path: str = SOCKET_PATH):
        self.socket_path = socket_path

    def send_intent(self, intent: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        serialized = json.dumps(intent, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(serialized) > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload size exceeds ceiling of {MAX_PAYLOAD_SIZE} bytes")

        frame = MAGIC_HEADER + struct.pack(">I", len(serialized)) + serialized

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(self.socket_path)
            sock.sendall(frame)

            magic = recv_exact(sock, 4)
            if magic != MAGIC_HEADER:
                raise ValueError(f"Invalid server framing magic: {magic!r}")

            len_bytes = recv_exact(sock, 4)
            (payload_len,) = struct.unpack(">I", len_bytes)
            if payload_len > MAX_PAYLOAD_SIZE:
                raise ValueError(f"Server response payload exceeds ceiling: {payload_len}")

            data = recv_exact(sock, payload_len)
            return json.loads(data.decode("utf-8"))
