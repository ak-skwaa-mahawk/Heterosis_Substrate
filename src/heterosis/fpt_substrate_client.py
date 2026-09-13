from cryptography.hazmat.primitives.asymmetric import ed25519
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


def sign_intent(intent: dict, private_key: ed25519.Ed25519PrivateKey) -> dict:
    signed_intent = json.loads(json.dumps(intent))
    fpt_auth = dict(signed_intent.get("fpt_authority", {}))
    fpt_auth.pop("signature", None)
    fpt_auth["public_key_hex"] = private_key.public_key().public_bytes_raw().hex()
    signed_intent["fpt_authority"] = fpt_auth

    canonical_bytes = json.dumps(signed_intent, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = private_key.sign(canonical_bytes)
    signed_intent["fpt_authority"]["signature"] = signature.hex()
    return signed_intent
