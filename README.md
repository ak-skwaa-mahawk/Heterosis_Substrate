# Heterosis Substrate

Sovereign manifold edge substrate and hardened cryptographic IPC runtime.

## Protocol Capabilities

- **HET_FPT_IPC_v1**: Exact-byte framing (`HET1` magic bytes, `uint32_be` length, and 64KB ceiling).
- **Ed25519 Authority Ingress**: Deterministic JSON signature verification for FPT authority intents.
- **Strict Lineage & Idempotency**: Predecessor receipt chaining (`bound_egress_receipt`) and resident LRU replay protection.
- **Manifold Waveguide**: Real-time shear venting, phase balancing, and pitch discrepancy containment.

## Installation

```bash
pip install heterosis-substrate

Client Usage
python
from cryptography.hazmat.primitives.asymmetric import ed25519
from heterosis import SubstrateIPCClient, sign_intent

client = SubstrateIPCClient("/data/data/com.termux/files/usr/tmp/heterosis.sock")
priv_key = ed25519.Ed25519PrivateKey.generate()

intent = {
    "protocol": "HET_FPT_IPC_v1",
    "command": "EXECUTE_INTENT",
    "intent_id": "tx-001",
    "timestamp_epoch_ms": 1789383742000,
    "fpt_authority": {
        "identity_urn": "urn:fpt:auth:root",
        "lineage_anchor": "0" * 64,
    },
    "manifold_constraints": {
        "pressure_ingress": 1.0,
        "max_acceptable_shear": 18.0,
        "target_octave_shell": 0,
        "enforce_tripwire": True,
    },
    "workload_commitment": {
        "manifest_sha256": "0" * 64,
        "byte_size": 32,
    },
}

signed = sign_intent(intent, priv_key)
receipt = client.send_intent(signed)
print("Execution receipt:", receipt)


License

MIT

