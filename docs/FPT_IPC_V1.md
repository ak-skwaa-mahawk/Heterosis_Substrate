# HET_FPT_IPC_v1 Specification

## 1. Scope and Boundary
This document specifies the communication protocol between FPT (Formal Provenance and Execution Authority) and Heterosis Substrate (Runtime Execution Engine).

* **FPT Responsibility:** Authorizes intent, signs authority record, supplies prior lineage anchor, records canonical external audit transactions.
* **Heterosis Responsibility:** Validates schema bounds, verifies prior lineage anchor against local state, executes bounded state transition, evaluates tripwire invariants, and emits deterministic receipts (`ACCEPTED`, `DAMPENED`, or `REJECTED`).

## 2. Framing Protocol
* **Socket:** `/data/data/com.termux/files/usr/tmp/heterosis.sock`
* **Transport:** Length-prefixed binary frame over UNIX Domain Socket.
  * `Magic` (4 bytes): `0x48 0x45 0x54 0x31` (`HET1`)
  * `Length` (4 bytes): `uint32_be` (payload byte count, max 65536 bytes)
  * `Payload`: Deterministic UTF-8 JSON (`json.dumps(..., sort_keys=True, separators=(',', ':'))`).

## 3. Schema Definitions

### 3.1 EXECUTE_INTENT Request
```json
{
  "protocol": "HET_FPT_IPC_v1",
  "command": "EXECUTE_INTENT",
  "intent_id": "string",
  "timestamp_epoch_ms": 1789383742000,
  "fpt_authority": {
    "identity_urn": "string",
    "lineage_anchor": "64-char-hex",
    "signature": "hex-or-b64"
  },
  "manifold_constraints": {
    "pressure_ingress": 1.0,
    "max_acceptable_shear": 24.0,
    "target_octave_shell": 0,
    "enforce_tripwire": true
  },
  "workload_commitment": {
    "manifest_sha256": "64-char-hex",
    "byte_size": 4096
  }
}

3.2 EXECUTE_RECEIPT Responses
​Status: ACCEPTED
json
{
  "protocol": "HET_FPT_IPC_v1",
  "message_type": "EXECUTE_RECEIPT",
  "status": "ACCEPTED",
  "intent_id": "string",
  "cycle_sequence": 2,
  "telemetry": {
    "execution_duration_ns": 24102,
    "raw_velocity": 3.173006,
    "balanced_velocity": 0.159211,
    "phase_offset": 3.173006,
    "active_shell": 0,
    "macro_leak": 0.014159,
    "precession_bias": 0.181312,
    "tripwire_state": "NOMINAL"
  },
  "lineage": {
    "prior_receipt": "64-char-hex",
    "workload_manifest": "64-char-hex",
    "core_hash": "64-char-hex",
    "egress_receipt": "64-char-hex"
  }
}

Status: DAMPENED
json
{
  "protocol": "HET_FPT_IPC_v1",
  "message_type": "EXECUTE_RECEIPT",
  "status": "DAMPENED",
  "intent_id": "string",
  "cycle_sequence": 2,
  "error": {
    "code": "PITCH_DISPARITY",
    "detail": "Tripwire clamped cycle to fault-dampened mode"
  },
  "telemetry": {
    "tripwire_state": "FAULT_DAMPENED:PITCH_DISPARITY",
    "restoring_torque": -0.841203
  },
  "lineage": {
    "prior_receipt": "64-char-hex",
    "workload_manifest": "64-char-hex",
    "core_hash": "64-char-hex",
    "egress_receipt": "64-char-hex"
  }
}

Status: REJECTED
json
{
  "protocol": "HET_FPT_IPC_v1",
  "message_type": "EXECUTE_RECEIPT",
  "status": "REJECTED",
  "intent_id": "string",
  "error": {
    "code": "LINEAGE_MISMATCH | SCHEMA_VIOLATION | BOUNDS_EXCEEDED",
    "detail": "string explanation"
  }
}
