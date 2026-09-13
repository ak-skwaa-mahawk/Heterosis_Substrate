import json
import socket
import unittest
import struct
from cryptography.hazmat.primitives.asymmetric import ed25519
from fpt_substrate_client import SubstrateIPCClient, SOCKET_PATH, sign_intent, recv_exact

class TestFPTIPCContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.priv_key = ed25519.Ed25519PrivateKey.generate()
        cls.pub_key_hex = cls.priv_key.public_key().public_bytes_raw().hex()

    def setUp(self):
        self.client = SubstrateIPCClient()

    def _get_current_anchor(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(SOCKET_PATH)
            sock.sendall(b"status\n")
            current = json.loads(sock.recv(4096).decode("utf-8"))
        return current.get("egress_receipt", "0" * 64)

    def _create_intent(self, intent_id, anchor=None, drive=1.0, shear=24.0, manifest="0"*64):
        return {
            "protocol": "HET_FPT_IPC_v1",
            "command": "EXECUTE_INTENT",
            "intent_id": intent_id,
            "timestamp_epoch_ms": 1789383742000,
            "fpt_authority": {
                "identity_urn": "urn:fpt:auth:test",
                "lineage_anchor": anchor if anchor is not None else self._get_current_anchor(),
                "public_key_hex": self.pub_key_hex
            },
            "manifold_constraints": {
                "pressure_ingress": drive,
                "max_acceptable_shear": shear,
                "target_octave_shell": 0,
                "enforce_tripwire": True
            },
            "workload_commitment": {
                "manifest_sha256": manifest,
                "byte_size": 32
            }
        }

    def test_legacy_cli_status_interop(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(SOCKET_PATH)
            sock.sendall(b"status\n")
            resp = sock.recv(4096).decode("utf-8")
            self.assertIn("seq", resp)

    def test_valid_ed25519_signature_accepted(self):
        intent = self._create_intent("test-valid-sig-1")
        signed = sign_intent(intent, self.priv_key)
        res = self.client.send_intent(signed)
        self.assertEqual(res.get("protocol"), "HET_FPT_IPC_v1")
        self.assertIn(res.get("status"), ["ACCEPTED", "DAMPENED"])
        self.assertEqual(res.get("intent_id"), "test-valid-sig-1")

    def test_missing_signature_rejected(self):
        intent = self._create_intent("test-missing-sig")
        res = self.client.send_intent(intent)
        self.assertEqual(res.get("status"), "REJECTED")
        self.assertEqual(res.get("error", {}).get("code"), "SIGNATURE_MISSING")

    def test_forged_signature_rejected(self):
        intent = self._create_intent("test-forged-sig")
        signed = sign_intent(intent, self.priv_key)
        # Adversarially tamper with constraints after signing
        signed["manifold_constraints"]["pressure_ingress"] = 2.5
        res = self.client.send_intent(signed)
        self.assertEqual(res.get("status"), "REJECTED")
        self.assertEqual(res.get("error", {}).get("code"), "SIGNATURE_INVALID")

    def test_idempotency_replay(self):
        intent = self._create_intent("test-idempotent-key-01")
        signed = sign_intent(intent, self.priv_key)
        res1 = self.client.send_intent(signed)
        seq1 = res1.get("cycle_sequence")

        res2 = self.client.send_intent(signed)
        self.assertTrue(res2.get("idempotent_replay", False))
        self.assertEqual(res2.get("cycle_sequence"), seq1)
        self.assertEqual(res1.get("lineage", {}).get("egress_receipt"), res2.get("lineage", {}).get("egress_receipt"))

    def test_missing_lineage_rejected(self):
        intent = self._create_intent("test-no-anchor")
        del intent["fpt_authority"]["lineage_anchor"]
        signed = sign_intent(intent, self.priv_key)
        res = self.client.send_intent(signed)
        self.assertEqual(res.get("status"), "REJECTED")
        self.assertEqual(res.get("error", {}).get("code"), "LINEAGE_REQUIRED")

    def test_fpt_lineage_mismatch_rejected(self):
        intent = self._create_intent("test-bad-anchor", anchor="deadbeef" * 8)
        signed = sign_intent(intent, self.priv_key)
        res = self.client.send_intent(signed)
        self.assertEqual(res.get("status"), "REJECTED")
        self.assertEqual(res.get("error", {}).get("code"), "LINEAGE_MISMATCH")

    def test_bounds_exceeded_rejected(self):
        intent = self._create_intent("test-bad-bounds", shear=999.0)
        signed = sign_intent(intent, self.priv_key)
        res = self.client.send_intent(signed)
        self.assertEqual(res.get("status"), "REJECTED")
        self.assertEqual(res.get("error", {}).get("code"), "BOUNDS_EXCEEDED")

    def test_framing_resilience_under_fragmented_stream(self):
        sample_payload = json.dumps({"protocol": "HET_FPT_IPC_v1", "status": "ACCEPTED"}).encode("utf-8")
        full_wire_bytes = b"HET1" + struct.pack(">I", len(sample_payload)) + sample_payload

        chunk_sizes = [1, 2, 1, 3, 2, 1, 4]
        fragments = []
        idx = 0
        c_i = 0
        while idx < len(full_wire_bytes):
            sz = chunk_sizes[c_i % len(chunk_sizes)]
            fragments.append(full_wire_bytes[idx:idx + sz])
            idx += sz
            c_i += 1

        class MockFragmentedSocket:
            def __init__(self, chunks):
                self.chunks = list(chunks)

            def recv(self, n):
                if not self.chunks:
                    return b""
                chunk = self.chunks.pop(0)
                if len(chunk) > n:
                    left, right = chunk[:n], chunk[n:]
                    self.chunks.insert(0, right)
                    return left
                return chunk

        mock_sock = MockFragmentedSocket(fragments)
        magic = recv_exact(mock_sock, 4)
        self.assertEqual(magic, b"HET1")
        len_bytes = recv_exact(mock_sock, 4)
        (p_len,) = struct.unpack(">I", len_bytes)
        self.assertEqual(p_len, len(sample_payload))
        payload_bytes = recv_exact(mock_sock, p_len)
        decoded = json.loads(payload_bytes.decode("utf-8"))
        self.assertEqual(decoded["status"], "ACCEPTED")

if __name__ == "__main__":
    unittest.main()
