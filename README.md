Heterosis Substrate

A lightweight Python runtime substrate for nonlinear state transitions, local fault containment, peer-state synchronization, and tamper-evident execution lineage.

Heterosis Substrate provides the lower-level execution and state-management components used by higher-level orchestration systems. Its current implementation is designed for constrained POSIX/Termux environments and combines deterministic mathematical transforms with optional node-local runtime state.

Architecture

The repository is organized around five functional layers:

1. State transition
   
   - Dynamic-pitch state evolution
   - Harmonic/octave boundary calculations
   - Chiral shear and counter-torque state
   - Sequential execution receipts

2. Control and containment
   
   - Adaptive resonator
   - Drift/precession compensator
   - Boundary tripwire
   - Fault-dampened execution mode

3. Peer synchronization
   
   - UDP peer synchronization
   - Two-node receipt interlock
   - Equivocation detection
   - Cryptographic peer/state roots

4. Lineage and verification
   
   - SHA-256 state receipts
   - Double-SHA256 seals
   - Epoch/Merkle compaction
   - Epoch voucher verification

5. Runtime services
   
   - UNIX-domain socket IPC
   - Operator CLI
   - Process supervisor
   - Optional Termux/Android integration
   - Bounded resident state cache

Core Parameters

The current implementation defines the following common parameters:

Parameter| Value| Role
Dynamic pitch| "3.1730059"| Primary state-transition multiplier
Harmonic boundary| "8.0"| Phase-shell modulus/boundary
Base triad| "6.0"| Triad/pair scaling factor
Planar reference| "π"| Reference value for pitch delta
Pitch delta| "3.1730059 - π"| Offset used by multiple transforms

These values are implementation parameters, not claims about physical constants.

State Transition Model

The base substrate and related manifold implementations advance sequential state using an external drive combined with internal state.

A representative transition is:

external drive
      │
      ▼
state pressure
      │
      ├── accumulated shear
      ├── counter torque
      └── accumulated potential
      │
      ▼
phase velocity
      │
      ├── octave shell = floor(v / 8)
      └── harmonic phase = v mod 8
      │
      ▼
boundary/shear calculation
      │
      ▼
cryptographic state receipt

The implementation uses sequential state numbers and cryptographic receipts to bind successive execution states.

Dynamic Pitch

"3.1730059" is the primary dynamic-pitch parameter used by the substrate.

"adaptive_resonator.py" provides adaptive pitch adjustment around this value. The current "AdaptiveHeterosisResonator" permits a tuning envelope of:

[3.1700059, 3.1760059]

The pitch adjustment is calculated from a bounded hyperbolic-tangent response to the measured dispersion gradient.

Harmonic Boundary and Macro-Leak

The substrate models phase inside an eight-unit harmonic boundary:

octave_shell = int(phase_velocity // 8.0)
harmonic_phase = phase_velocity % 8.0

Several manifold implementations derive a boundary remainder or shear quantity from this phase.

The repository uses names including:

- "macro_leak"
- "chiral_vent"
- "effective_shear"
- "chiral_shear"

These values represent internal software state variables. They should not be interpreted as measurements of physical acoustic, mechanical, or electrical energy unless an external physical model is explicitly connected.

Resonator and Drift Compensation

"adaptive_resonator.py" provides harmonic balancing and state-dependent shear handling.

"drift_compensator.py" implements a feedback controller based on phase-velocity slip:

expected_velocity = net_pressure × dynamic_pitch

instantaneous_slip =
    phase_velocity - expected_velocity

integrated_slip =
    previous_integrated_slip × decay
    + instantaneous_slip

The restoring precession combines proportional and accumulated slip terms and is clamped to a bounded output range.

The orchestrator feeds this compensation back into subsequent substrate state.

Boundary Sentinel

"tripwire_sentinel.py" provides runtime boundary checks.

Current configured limits include:

MAX_PERMISSIBLE_ACCELERATION = 32.0
SHEAR_DISSIPATION_LIMIT      = 24.0
VELOCITY_UPPER_BOUND          = 48.0
VELOCITY_LOWER_BOUND          = 0.0001

The sentinel evaluates telemetry and returns:

(is_safe, damping_torque, diagnostic_code)

When the orchestrator receives a boundary violation, it enters a diagnostic fault-dampened state represented as:

FAULT_DAMPENED:<diagnostic_code>

The sentinel is a software containment mechanism. It is not a certified hardware safety controller.

Cryptographic State Lineage

Execution receipts are constructed using SHA-256 hashes over binary-packed state and chained receipt material.

A representative transition contains:

previous receipt
      +
core state hash
      +
sequence
      +
active pitch
      +
execution mode
      │
      ▼
SHA-256
      │
      ▼
egress receipt

This provides tamper-evident state lineage.

The implementation does not by itself provide immutable storage. An operator can still modify, delete, or replace files containing historical receipts; detection depends on retaining and independently comparing trusted prior receipts.

Mesh Synchronization

"mesh_sync.py" implements broker-free UDP synchronization.

Current protocol parameters:

Transport: UDP
Port:      43210
Header:    HET_SYNC_v1
Buffer:    4096 bytes

The mesh layer exchanges state/phase information between nodes and can establish cryptographically linked peer state.

"mesh_substrate.py" provides the node-side state generator used by the mesh layer.

The system currently implements peer synchronization and receipt interlock; it is not a general-purpose quorum or Byzantine-fault-tolerant consensus protocol.

Two-Node Interlock

"consensus_engine.py" provides "HeterosisConsensus.interlock()".

The current implementation:

1. extracts phase velocity and core hashes from two node receipts;
2. calculates phase difference modulo the harmonic boundary;
3. derives a "heterosis_gain";
4. calculates a fused velocity;
5. hashes the fused state;
6. binds both input hashes to the fused state;
7. emits a "heterosis_root".

The resulting root is a cryptographic interlock between the two supplied execution receipts.

This should be understood as two-node receipt fusion, not as a replacement for established distributed-consensus protocols.

Equivocation Detection

"chiral_slashing.py" maintains observed node/sequence state and detects conflicting receipts for the same node and sequence number.

The subsystem can mark nodes as rejected/slashed after detected equivocation.

This provides an application-level fault-detection mechanism for conflicting state claims.

Epoch Ledger Compaction

"ledger_vacuum.py" groups execution records into epochs.

The current epoch size is:

8 states

The implementation constructs a Merkle root over state hashes and generates an epoch voucher containing aggregated execution information and ancestry.

"zk_manifold_verifier.py" validates:

- previous epoch ancestry;
- epoch sequence span;
- integrated phase velocity;
- accumulated shear;
- Merkle root;
- cryptographic epoch seal.

The verifier is an application-specific proof/verification mechanism. It is not a general-purpose zero-knowledge proof system.

Runtime IPC

The primary orchestrator exposes a UNIX-domain socket at:

/data/data/com.termux/files/usr/tmp/heterosis.sock

"substrate_cli.py" connects to this socket and sends newline-terminated commands such as:

status

The CLI reads JSON responses from the orchestrator.

The repository also contains "substrate_daemon.py", which provides a standalone POSIX-domain-socket daemon implementation.

Supervisor

"supervisor.py" launches and monitors:

orchestrator.py

Current supervisor behavior includes:

- child-process monitoring;
- crash detection;
- restart backoff;
- maximum backoff;
- signal handling;
- child termination;
- stale UNIX-socket cleanup.

Current parameters include:

CRASH_THRESHOLD_SEC = 3.0
BACKOFF_DELAY       = 1.0
MAX_BACKOFF         = 30.0

The supervisor is a process-management component, not an operating-system service manager.

Resource-Bounded Cache

"chiral_page_cache.py" maintains a resident cache ceiling of:

8 pages

Additional state can be written to:

.substrate_pages/

Eviction priority is calculated from substrate state characteristics rather than conventional temporal LRU alone.

This mechanism is intended to bound resident state for long-running constrained-device operation.

Operator and Visualization Tools

"substrate_cli.py" provides runtime status access.

"topology_projector.py" renders the current state as an ASCII terminal projection showing:

- octave shell;
- phase position;
- shear;
- counter-torque;
- mode;
- sequence;
- abbreviated state hash.

This is a diagnostic visualization layer and does not participate in the core state transition.

Verification

The repository contains two complementary verification paths.

Audit harness

Run:

python audit_harness.py

The harness exercises the major mathematical, cryptographic, mesh, cache, ledger, verifier, sentinel, and compensation components.

Among its explicit checks are:

- manifold state generation;
- mesh receipt generation;
- two-node consensus/interlock root generation;
- eight-state ledger compaction;
- epoch voucher verification;
- eight-page cache enforcement;
- nominal sentinel acceptance;
- critical anomaly detection.

Integration verification

Run:

python verify_substrate_interlock.py

This integration path exercises the orchestrator and verifies persisted state such as "CURRENT_STATE.json" together with the interlock path.

Runtime Topology

                         HIGHER-LEVEL SYSTEM
                    FPT / Synara / other caller
                               │
                               ▼
                    ┌─────────────────────┐
                    │ MasterSubstrate     │
                    │ Orchestrator        │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   MeshCoupled          AdaptiveResonator   DriftCompensator
   Substrate                   │                    │
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                       Tripwire Sentinel
                               │
                    ┌──────────┴──────────┐
                    │                     │
                  SAFE              FAULT_DAMPENED
                    │                     │
                    └──────────┬──────────┘
                               ▼
                     State / Receipt Output
                               │
             ┌─────────────────┼──────────────────┐
             ▼                 ▼                  ▼
        UNIX IPC          UDP Mesh           Ledger/Voucher
             │                 │                  │
             ▼                 ▼                  ▼
        substrate_cli    consensus root      epoch verifier

Relationship to FPT / Synara

Heterosis Substrate is intended to occupy the runtime/substrate layer.

A clean separation of responsibilities is:

Synara
  └── workload, orchestration, higher-level cognition

FPT
  └── execution authority, provenance, invariant/identity control

Heterosis Substrate
  └── state transition, runtime control, peer synchronization,
      fault containment, receipts, and constrained-device services

The substrate should not become the authority for higher-level workload policy. It should expose measurable state, execution results, diagnostic conditions, and cryptographic lineage to the layer above it.

Security Scope

The repository contains experimental cryptographic mechanisms including:

- SHA-256 state receipts;
- double-SHA256 seals;
- Merkle-style epoch roots;
- HMAC-SHA256 envelope authentication;
- a custom SHA-256-derived XOR stream construction.

These mechanisms provide integrity and lineage functions within the current software design.

The custom "ChiralEnvelope" encryption construction is not a substitute for a standardized AEAD protocol and should not be treated as production cryptography for sensitive data without independent cryptographic review.

Platform Scope

The runtime is primarily structured around Python and POSIX facilities.

Termux-specific integration currently includes:

- "/data/data/com.termux/..." socket paths;
- optional Android notification integration;
- compatibility with Termux process supervision/wake-lock workflows.

Portability to other POSIX systems should be treated as an engineering target rather than an implicit guarantee.

Design Principle

The central engineering objective is:

«Advance bounded state, inspect the result, contain anomalous transitions, synchronize peer state, and preserve verifiable execution lineage.»

The repository uses nonlinear, harmonic, chiral, and manifold terminology as names for software state transformations and control mechanisms. These terms describe the implementation model; they should not be interpreted as claims of externally validated physical laws.

Status

Heterosis Substrate is an experimental runtime and verification framework.

The current codebase demonstrates:

- nonlinear state-transition models;
- adaptive feedback;
- explicit runtime boundary checks;
- UNIX-domain IPC;
- UDP peer synchronization;
- two-node cryptographic interlock;
- equivocation detection;
- bounded state caching;
- epoch/Merkle compaction;
- execution receipts;
- integration and audit harnesses.

Production deployment should additionally require platform-specific testing, concurrency/load testing, network failure testing, security review, standardized cryptography where confidentiality is required, and independent verification of any physical-system interpretation.

The progression from d533a6e to aa718fb resolves the interface from an unvalidated prototype into a verifiable, tamper-resistant boundary.
Commit Progression & Invariant Ledger
| Commit | Architectural Boundary Established | Test Suite Delta |
|---|---|---|
| d533a6e | Raw IPC framing (HET1), dual-mode dispatcher, initial CLI interop. | Contract suite established (4 tests). |
| b52a64d | Bound workload manifest to core_hash; enforced LINEAGE_REQUIRED; added resident LRU idempotency cache. | Contract suite expanded (6 tests). |
| 069aa0f | Replaced unchecked stream reads with recv_exact(); added synthetic 1–4 byte fragmented stream regression test. | Contract suite expanded (7 tests). |
| aa718fb | Implemented Ed25519 public-key signature verification over deterministic JSON intent bodies; added tamper and missing-signature guards. | Contract suite expanded to 9 tests (all passing in 30 ms). |
Terminology Alignment: Deterministic JSON vs. RFC 8785
The byte representation being signed is:
Where \text{JSON}_{\text{deterministic}} is defined strictly as:
 * Lexicographical key sorting (sort_keys=True)
 * Whitespace elimination (separators=(',', ':'))
 * UTF-8 byte serialization
Documenting this as Deterministic UTF-8 JSON Encoding avoids overclaiming RFC 8785/JCS compliance while maintaining an exact, repeatable byte sequence for the Ed25519 verification step.
Scope & System Boundary at aa718fb
┌─────────────────────────────────────────────────────────────┐
│                      FPT AUTHORITY                          │
│  - Formulates Intent                                        │
│  - Captures Prior Egress Receipt Anchor                     │
│  - Hashes Workload Manifest (manifest_sha256)               │
│  - Signs Deterministic JSON via Ed25519 Private Key         │
└──────────────────────────────┬──────────────────────────────┘
                               │ HET_FPT_IPC_v1
                               ▼ [UNIX Domain Stream]
┌─────────────────────────────────────────────────────────────┐
│                   HETEROSIS SUBSTRATE                       │
│                                                             │
│  [Transport Layer]                                          │
│   └── recv_exact() exact-byte frame reader                  │
│                                                             │
│  [Authority & Ingress Verification]                         │
│   ├── Ed25519 Signature Verification  ──► SIGNATURE_INVALID │
│   ├── Idempotency Cache (LRU 256)     ──► idempotent_replay │
│   ├── Mandatory Lineage Verifier      ──► LINEAGE_REQUIRED  │
│   └── Boundary Guard (Shear ≤ 24.0)   ──► BOUNDS_EXCEEDED   │
│                                                             │
│  [Execution Engine]                                         │
│   ├── Manifold Pulse & Waveguide Balancing                  │
│   └── Tripwire Containment (PITCH_DISPARITY)                │
│                                                             │
│  [State Commitment]                                         │
│   ├── bound_core_hash = SHA256(packed_core + manifest)      │
│   └── bound_egress_receipt = SHA256(core_hash + prior_rcpt) │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
                        EXECUTE_RECEIPT

The system is synchronized, the working tree is clean, the supervisor daemon is active, and both verification harnesses (9/9 IPC and 13/13 Bare-Metal) execute deterministically with zero failures.
