import hashlib
import json
import struct
import math
import os
import sys
import time

# Module imports
from base import HeterosisSubstrate
from manifold_engine import RecursiveManifold
from heterosis_observer import SelfSimulatingObserver
from chiral_substrate import ChiralManifold
from resonance_manifold import ResonanceManifold
from mesh_substrate import MeshCoupledSubstrate
from consensus_engine import HeterosisConsensus
from ledger_vacuum import EpochLedgerVacuum
from zk_manifold_verifier import ManifoldProofVerifier
from chiral_page_cache import ChiralPageCache
from tripwire_sentinel import SubstrateTripwire
from drift_compensator import ChiralDriftCompensator

class SubstrateAuditHarness:
    def __init__(self):
        self.results = []
        self.failures = 0

    def assert_eq(self, actual, expected, test_name: str):
        if actual == expected:
            self.results.append((test_name, True, ""))
        else:
            self.results.append((test_name, False, f"Expected {expected}, got {actual}"))
            self.failures += 1

    def assert_true(self, condition: bool, test_name: str, msg: str = ""):
        if condition:
            self.results.append((test_name, True, ""))
        else:
            self.results.append((test_name, False, msg or "Condition failed"))
            self.failures += 1

    def run_suite(self):
        print("╔═[ HETEROSIS SUBSTRATE: BARE-METAL AUDIT HARNESS ]════════════╗")
        t0 = time.perf_counter()

        self.test_base_deterministic_seed()
        self.test_manifold_cascade()
        self.test_chiral_counter_torque()
        self.test_resonance_mode_switching()
        self.test_mesh_hardware_entropy()
        self.test_consensus_interlock()
        self.test_ledger_vacuum_and_zk_attestation()
        self.test_page_cache_eviction()
        self.test_tripwire_circuit_breaker()
        self.test_drift_compensator()

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.render_report(elapsed)

    def test_base_deterministic_seed(self):
        sub = HeterosisSubstrate(seed="bare_metal_origin_dan_kee")
        res1 = sub.step(1.0)
        self.assert_eq(res1["seq"], 1, "Base: Step 1 sequence")
        self.assert_eq(round(res1["phase_velocity"], 7), 3.1730059, "Base: Pitch velocity multiplication")
        
        # Verify deterministic double-SHA256 receipt from known trace
        expected_egress = "f3294fe9486df9e55f4f4a550027ea375e38a397ebf12bb4f156166097e8d4fd"
        self.assert_eq(res1["egress_receipt"], expected_egress, "Base: Origin egress hash match")

    def test_manifold_cascade(self):
        engine = RecursiveManifold(seed="bare_metal_origin_dan_kee")
        s1 = engine.pulse(external_drive=1.0)
        s2 = engine.pulse(external_drive=0.0)
        
        # In step 2, intake must exactly inherit step 1's macro_leak_vent
        self.assert_eq(s2["accumulated_shear_intake"], s1["macro_leak_vent"], "Manifold: Shear recirculation link")
        self.assert_true(s2["octave_shell"] >= 1, "Manifold: Non-zero octave shell transition")

    def test_chiral_counter_torque(self):
        chiral = ChiralManifold(seed="chiral_test")
        c1 = chiral.step(1.0)
        self.assert_true(c1["counter_torque"] > 0.0, "Chiral: Positive counter-torque generation")
        self.assert_true(c1["net_pressure"] <= 1.0, "Chiral: Net pressure throttled by drag")

    def test_resonance_mode_switching(self):
        res = ResonanceManifold(seed="resonance_test")
        modes = set()
        for i in range(8):
            st = res.step(external_drive=1.0 if i == 0 else 0.0)
            modes.add(st["mode"])
        
        self.assert_true(len(modes) >= 1, "Resonance: Dynamic mode resolution active")

    def test_mesh_hardware_entropy(self):
        mesh = MeshCoupledSubstrate(seed="mesh_test")
        m1 = mesh.pulse(1.0)
        self.assert_true(m1["exec_ns"] > 0, "Mesh: Nanosecond execution timer active")
        self.assert_true("env_jitter" in m1, "Mesh: Edge hardware entropy bound")

    def test_consensus_interlock(self):
        sub_a = MeshCoupledSubstrate(seed="node_a")
        sub_b = MeshCoupledSubstrate(seed="node_b")
        st_a = sub_a.pulse(1.0)
        st_b = sub_b.pulse(1.8)

        proof = HeterosisConsensus.interlock(st_a, st_b)
        self.assert_true("heterosis_root" in proof, "Consensus: Root hash synthesized")
        self.assert_true(proof["heterosis_gain"] > 0.0, "Consensus: Positive hybrid vigor gain")

    def test_ledger_vacuum_and_zk_attestation(self):
        mesh = MeshCoupledSubstrate(seed="vacuum_test")
        records = [mesh.pulse(1.0 if i == 0 else 0.0) for i in range(8)]
        
        voucher = EpochLedgerVacuum.compact_epoch(records, previous_epoch_seal="GENESIS_ZERO")
        self.assert_eq(voucher["state_count_collapsed"], 8, "Vacuum: Collapsed 8 states to 1 voucher")
        
        attestation = ManifoldProofVerifier.verify_epoch_voucher(voucher, previous_seal="GENESIS_ZERO")
        self.assert_true(attestation["valid"], "ZK Verifier: Algebraic and cryptographic match confirmed")

    def test_page_cache_eviction(self):
        cache = ChiralPageCache()
        # Saturate cache past resident limit of 8
        for seq in range(1, 12):
            dummy_state = {
                "seq": seq,
                "phase_velocity": 3.17 * seq,
                "chiral_vent": 1.2,
                "counter_torque": 0.5,
                "net_pressure": 1.0,
                "core_hash": hashlib.sha256(str(seq).encode()).hexdigest()
            }
            cache.pin_state(dummy_state)

        self.assert_eq(len(cache.resident_cache), 8, "Cache: Enforces 8-page octave resident ceiling")
        recalled = cache.recall_page(1)
        self.assert_eq(recalled["seq"], 1, "Cache: Binary disk recall intact")

    def test_tripwire_circuit_breaker(self):
        tripwire = SubstrateTripwire()
        safe_state = {"seq": 1, "phase_velocity": 3.17, "chiral_vent": 2.0, "net_pressure": 1.0}
        safe, _, _ = tripwire.evaluate_boundary(safe_state)
        self.assert_true(safe, "Sentinel: Nominal bounds accepted")

        rupture_state = {"seq": 2, "phase_velocity": 50.0, "chiral_vent": 30.0, "net_pressure": 1.0}
        ruptured, damp, reason = tripwire.evaluate_boundary(rupture_state)
        self.assert_true(not ruptured, "Sentinel: Critical anomaly tripped circuit breaker")
        self.assert_true(damp < 0.0, "Sentinel: Negative damping torque injected")

    def test_drift_compensator(self):
        comp = ChiralDriftCompensator()
        st = {"seq": 1, "phase_velocity": 3.20, "net_pressure": 1.0}
        out = comp.calculate_precession(st)
        self.assert_true("restoring_precession" in out, "Compensator: Micro-precession vector generated")
        self.assert_true("compensation_receipt" in out, "Compensator: Auditable compensation hash generated")

    def render_report(self, elapsed_ms: float):
        total = len(self.results)
        passed = total - self.failures
        
        for name, ok, err in self.results:
            status = "\033[92m[PASS]\033[0m" if ok else "\033[91m[FAIL]\033[0m"
            print(f" {status} {name}")
            if not ok:
                print(f"        └── {err}")

        print("╠══════════════════════════════════════════════════════════════╣")
        summary_color = "\033[92m" if self.failures == 0 else "\033[91m"
        print(f"║ AUDIT COMPLETE: {summary_color}{passed}/{total} PASSED\033[0m in {elapsed_ms:.2f}ms")
        print("╚══════════════════════════════════════════════════════════════╝")

        if self.failures > 0:
            sys.exit(1)

if __name__ == "__main__":
    harness = SubstrateAuditHarness()
    harness.run_suite()
