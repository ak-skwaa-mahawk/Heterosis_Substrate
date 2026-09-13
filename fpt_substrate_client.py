import json
import socket
import struct
from typing import Dict, Any

SOCKET_PATH = "/data/data/com.termux/files/usr/tmp/heterosis.sock"
MAGIC_HEADER = b"HET1"
MAX_PAYLOAD_SIZE = 65536

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

            magic = sock.recv(4)
            if magic != MAGIC_HEADER:
                raise ValueError("Invalid server framing magic")

            len_bytes = sock.recv(4)
            if len(len_bytes) < 4:
                raise ConnectionError("Truncated frame length from server")
            (payload_len,) = struct.unpack(">I", len_bytes)

            data = bytearray()
            while len(data) < payload_len:
                chunk = sock.recv(min(4096, payload_len - len(data)))
                if not chunk:
                    raise ConnectionError("Socket closed prematurely while reading response")
                data.extend(chunk)

            return json.loads(data.decode("utf-8"))
