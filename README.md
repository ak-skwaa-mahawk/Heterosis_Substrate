# Heterosis Substrate

A lightweight, deterministic runtime substrate for fault-tolerant state execution, distributed gossip interlock, and tamper-evident state lineage across constrained environments.

## Core Architectural Invariants

Heterosis Substrate acts as an execution substrate underlying high-level orchestration authorities (e.g., FPT / Synara). It enforces closed-loop physical invariants across cyclic state transitions:

* **Dynamic Pitch Invariant ($P \approx 3.1730059$):** Enforces a deterministic directional multiplier preserving balance between energy ingress and internal phase velocity.
* **Octave Leak Routing:** Measures energy dispersion beyond the fundamental 8-octave manifold, routing excess shear into adaptive acoustic waveguides (`adaptive_resonator.py`).
* **Closed-Loop Precession Compensation:** Dynamically calculates restoring counter-torque vectors (`drift_compensator.py`) to prevent phase runaway without human intervention.
* **Autonomous Boundary Sentinel:** Active circuit breakers (`tripwire_sentinel.py`) clamp anomalies into `FAULT_DAMPENED` modes prior to state commitment.
* **Cryptographic State Lineage:** Sequential state transitions are anchored via POSIX nanosecond clock jitter and double-SHA256 hash chains (`core_hash` -> `egress_receipt`), providing an immutable, zero-dependency audit trace.

## System Topology

┌────────────────────────────────────────────────────────┐
│               SYNARA / COGNITIVE LAYER                 │
└───────────────────────────┬────────────────────────────┘
│ Workload Intent
┌───────────────────────────▼────────────────────────────┐
│         FPT (FORMAL PROVENANCE / EXECUTION AUTH)       │
│           Invariant Checks & Identity Anchoring        │
└───────────────────────────┬────────────────────────────┘
│ Deterministic Execution
┌───────────────────────────▼────────────────────────────┐
│                  HETEROSIS SUBSTRATE                   │
│  ┌──────────────────────┬───────────────────────────┐  │
│  │ Orchestrator Daemon  │ Supervisor Watchdog       │  │
│  │ (IPC: heterosis.sock)│ (termux-wake-lock / LMK)  │  │
│  └──────────┬───────────┴─────────────┬─────────────┘  │
│             │                         │                │
│  ┌──────────▼───────────┐ ┌───────────▼─────────────┐  │
│  │ Mesh / Waveguide Core│ │ UDP Gossip (Port 43210) │  │
│  │ Invariants & Circuit │ │ Decentralized Consensus │  │
│  └──────────┬───────────┘ └───────────┬─────────────┘  │
│             └─────────────┬───────────┘                │
│                           ▼                            │
│              Cryptographic Chain of Custody            │
│                 (Double-SHA256 Ledger)                 │
└────────────────────────────────────────────────────────┘


## Bare-Metal Service Layer

* **IPC Transport:** UNIX Domain Socket (`/data/data/com.termux/files/usr/tmp/heterosis.sock`) delivering sub-millisecond local telemetry and command execution.
* **Gossip Interlock:** Asynchronous UDP transport on port `43210` facilitating multi-node phase entrainment without centralized coordination.
* **Process Watchdog:** Resident Python supervisor with crash-backoff dynamics, stale socket unlinking, and hardware wake-lock integration.

## Verification & Audit

Run the bare-metal test harness to verify the full 13-stage mathematical, cryptographic, and circuit-breaker suite:

```bash
python audit_harness.py

Inspect live runtime telemetry:
python substrate_cli.py status

