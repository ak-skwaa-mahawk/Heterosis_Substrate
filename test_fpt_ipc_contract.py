import json
import socket
import unittest
from fpt_substrate_client import SubstrateIPCClient, SOCKET_PATH

class TestFPTIPCContract(unittest.TestCase):
    def setUp(self):
        self.client = SubstrateIPCClient()

    def test_legacy_cli_status_interop(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(SOCKET_PATH)
            sock.sendall(b"status\n")
            resp = sock.recv(4096).decode("utf-8")
            self.assertIn("seq", resp)

    def test_fpt_intent_accepted(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(SOCKET_PATH)
            sock.sendall(b"status\n")
            current = json.loads(sock.recv(4096).decode("utf-8"))
        
        anchor = current.get("egress_receipt", "0" * 64)
        intent = {
            "protocol": "HET_FPT_IPC_v1",
            "command": "EXECUTE_INTENT",
            "intent_id": "test-intent-001",
            "timestamp_epoch_ms": 1789383742000,
            "fpt_authority": {
                "identity_urn": "urn:fpt:auth:test",
                "lineage_anchor": anchor,
                "signature": "simulated_sig"
            },
            "manifold_constraints": {
                "pressure_ingress": 1.0,
                "max_acceptable_shear": 24.0,
                "target_octave_shell": 0,
                "enforce_tripwire": True
            },
            "workload_commitment": {
                "manifest_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "byte_size": 0
            }
        }
        res = self.client.send_intent(intent)
        self.assertEqual(res.get("protocol"), "HET_FPT_IPC_v1")
        self.assertIn(res.get("status"), ["ACCEPTED", "DAMPENED"])
        self.assertEqual(res.get("intent_id"), "test-intent-001")
        self.assertIn("egress_receipt", res.get("lineage", {}))

    def test_fpt_lineage_mismatch_rejected(self):
        bad_intent = {
            "protocol": "HET_FPT_IPC_v1",
            "command": "EXECUTE_INTENT",
            "intent_id": "test-intent-bad-anchor",
            "timestamp_epoch_ms": 1789383742000,
            "fpt_authority": {
                "identity_urn": "urn:fpt:auth:test",
                "lineage_anchor": "deadbeef" * 8,
                "signature": "simulated_sig"
            },
            "manifold_constraints": {
                "pressure_ingress": 1.0,
                "max_acceptable_shear": 24.0,
                "target_octave_shell": 0,
                "enforce_tripwire": True
            },
            "workload_commitment": {
                "manifest_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "byte_size": 0
            }
        }
        res = self.client.send_intent(bad_intent)
        self.assertEqual(res.get("status"), "REJECTED")
        self.assertEqual(res.get("error", {}).get("code"), "LINEAGE_MISMATCH")

    def test_bounds_exceeded_rejected(self):
        bad_bounds_intent = {
            "protocol": "HET_FPT_IPC_v1",
            "command": "EXECUTE_INTENT",
            "intent_id": "test-intent-bad-bounds",
            "timestamp_epoch_ms": 1789383742000,
            "fpt_authority": {
                "identity_urn": "urn:fpt:auth:test",
                "lineage_anchor": "",
                "signature": "simulated_sig"
            },
            "manifold_constraints": {
                "pressure_ingress": 1.0,
                "max_acceptable_shear": 999.0,
                "target_octave_shell": 0,
                "enforce_tripwire": True
            },
            "workload_commitment": {
                "manifest_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "byte_size": 0
            }
        }
        res = self.client.send_intent(bad_bounds_intent)
        self.assertEqual(res.get("status"), "REJECTED")
        self.assertEqual(res.get("error", {}).get("code"), "BOUNDS_EXCEEDED")

if __name__ == "__main__":
    unittest.main()
