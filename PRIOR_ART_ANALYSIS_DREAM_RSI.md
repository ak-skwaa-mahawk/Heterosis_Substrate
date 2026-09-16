# Comparative Architectural Analysis: Heterosis Substrate vs. Dream-RSI

**Date:** September 16, 2026  
**Subject Implementation:** `heterosis-substrate` (v0.1.2)  
**Reference Preprint:** *Dream-RSI: Recursive Self-Improvement through Evolving Worlds* (Zheng et al., Google / Google DeepMind / UMD)  
**Primary Archive Checksum (SHA-256):** `94d797521114e0024da2dc4c9b98b588bfae49fc5efa0a7ba9124d7a4232b7a8`

---

## 1. Executive Summary

While *Dream-RSI* and the *Heterosis Substrate* both address recursive self-improvement (RSI) in agentic systems via decoupled feedback loops, they occupy different levels of the system hierarchy:

- **Dream-RSI** is an algorithmic meta-exploration layer that treats completed search trees as an offline world-model simulator to train search policies without online execution cost.
- **Heterosis Substrate** is a cryptographically secured runtime harness and orchestration substrate providing state consensus, drift compensation, process tripwires, and sovereign inter-process communication.

---

## 2. Granular Architectural Comparison

| Dimension | Dream-RSI (Google / DeepMind Preprint) | Heterosis Substrate (Two Mile Solutions LLC) |
| :--- | :--- | :--- |
| **Artifact Status** | Conceptual preprint (PDF, 36 pp.); no runnable code released. | Production wheel (`v0.1.2`) published on PyPI; active CLI/daemon. |
| **Operational Layer** | Search policy optimization (MCTS / tree branching exploration). | Runtime harness, IPC fabric, and distributed process orchestrator. |
| **Feedback Mechanism** | Off-policy trace simulation ("dreaming" over historical search trees). | Real-time surplus velocity balancing, octave phase tracking, egress receipts. |
| **Safety & Control** | Dead-end pruning, legal frontier ranking (heuristic). | Active tripwire sentinel, acoustic filter, chiral drift compensation. |
| **Inter-Process Fabric**| In-memory policy evaluation over tree structures. | Hardened UNIX domain socket (`HET_FPT_IPC_v1`) with signed receipts. |
| **Fault Isolation** | Trajectory termination upon benchmark failure. | Hard-fail tripwire trip states, boundary vents, deterministic state reset. |

---

## 3. Prior Art Anchoring

1. **Upstream Dream-RSI Repository:** Cloned at commit `4149ea9181ab1db80f85717ffda2c9f0f130e85b` (dated Sept 16, 2026).
2. **PyPI Package Index:** `heterosis-substrate==0.1.2` deployed and verifiable via public PyPI Simple Index and JSON endpoints.
3. **Evidence Bundle:** Cryptographically sealed archive `heterosis_prior_art_bundle_20260916.tar.gz` containing raw text extractions, git signatures, and deployment manifests.

