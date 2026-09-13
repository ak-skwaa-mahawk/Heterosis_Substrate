import json
import os
import time
from orchestrator import MasterSubstrateOrchestrator
from consensus_engine import HeterosisConsensus

def run_integration_verification():
    print("╔═[ HETEROSIS MANIFOLD: INTEGRATION & INTERLOCK TEST ]═════════╗")

    # 1. Test Atomic Snapshot to CURRENT_STATE.json
    print("[*] Stage 1: Testing atomic disk state serialization...")
    node_a = MasterSubstrateOrchestrator(node_id="node_alpha", seed="seed_alpha")
    state_a = node_a.step_manifold(external_drive=1.0)

    if not os.path.exists("CURRENT_STATE.json"):
        print("[-] FAIL: CURRENT_STATE.json was not created.")
        return False

    with open("CURRENT_STATE.json", "r") as f:
        disk_state = json.load(f)

    assert disk_state["seq"] == state_a["seq"], "Sequence mismatch on disk snapshot"
    assert disk_state["core_hash"] == state_a["core_hash"], "Core hash divergence on disk snapshot"
    print(f"[+] PASS: CURRENT_STATE.json verified on local storage (Seq: {disk_state['seq']}).")

    # 2. Test Cross-Node Consensus Interlock
    print("\n[*] Stage 2: Simulating multi-node geometric consensus interlock...")
    node_b = MasterSubstrateOrchestrator(node_id="node_beta", seed="seed_beta")
    state_b = node_b.step_manifold(external_drive=1.85)

    interlock_proof = HeterosisConsensus.interlock(state_a, state_b)

    print(f" └── Node Alpha Vel  : {state_a['phase_velocity']:.6f}")
    print(f" └── Node Beta Vel   : {state_b['phase_velocity']:.6f}")
    print(f" └── Heterosis Gain  : {interlock_proof['heterosis_gain']:.6f}")
    print(f" └── Heterosis Root  : {interlock_proof['heterosis_root'][:32]}...")

    assert "heterosis_root" in interlock_proof, "Missing consensus root in interlock proof"
    assert interlock_proof["heterosis_gain"] > 0.0, "Zero or negative hybrid vigor"
    print("[+] PASS: Peer-to-peer phase interlock successfully converged.")

    print("\n[✓] ALL SUBSYSTEM TESTS VERIFIED GREEN.")
    return True

if __name__ == "__main__":
    success = run_integration_verification()
    exit(0 if success else 1)
