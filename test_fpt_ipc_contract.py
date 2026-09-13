import json
import socket
import unittest
from fpt_substrate_client import SubstrateIPCClient, SOCKET_PATH

class TestFPTIPCContract(unittest.TestCase):
    def setUp(self):
        self.client = SubstrateIPCClient()

    def _get_current_anchor(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(SOCKET_PATH)
            sock.sendall(b"status\n")
            current = json.loads(sock.recv(4096).decode("utf-8"))
        return current.get("egress_receipt", "0" * 64)

    def test_legacy_cli_status_interop(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(SOCKET_PATH)
            sock.sendall(b"status\n")
            resp = sock.recv(4096).decode("utf-8")
            self.assertIn("seq", resp)

    def test_fpt_intent_accepted(self):
        anchor = self._get_current_anchor()
        intent = {
            "protocol": "HET_FPT_IPC_v1",
            "command": "EXECUTE_INTENT",
            "intent_id": "test-intent-acc-1",
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
        self.assertEqual(res.get("intent_id"), "test-intent-acc-1")
        self.assertIn("egress_receipt", res.get("lineage", {}))

    def test_idempotency_replay(self):
        anchor = self._get_current_anchor()
        intent = {
            "protocol": "HET_FPT_IPC_v1",
            "command": "EXECUTE_INTENT",
            "intent_id": "test-idempotent-key-01",
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
                "manifest_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
                "byte_size": 32
            }
        }
        res1 = self.client.send_intent(intent)
        seq1 = res1.get("cycle_sequence")

        # Resubmit identical intent_id
        res2 = self.client.send_intent(intent)
        self.assertTrue(res2.get("idempotent_replay", False))
        self.assertEqual(res2.get("cycle_sequence"), seq1)
        self.assertEqual(res1.get("lineage", {}).get("egress_receipt"), res2.get("lineage", {}).get("egress_receipt"))

    def test_missing_lineage_rejected(self):
        bad_intent = {
            "protocol": "HET_FPT_IPC_v1",
            "command": "EXECUTE_INTENT",
            "intent_id": "test-intent-no-anchor",
            "timestamp_epoch_ms": 1789383742000,
            "fpt_authority": {
                "identity_urn": "urn:fpt:auth:test",
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
        self.assertEqual(res.get("error", {}).get("code"), "LINEAGE_REQUIRED")

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
                "lineage_anchor": self._get_current_anchor(),
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
