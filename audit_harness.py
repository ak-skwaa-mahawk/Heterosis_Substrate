import hashlib
import json
import struct
import os
import sys
import time

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

        # 1. Base (Pass seed positionally to satisfy initial_seed)
        sub = HeterosisSubstrate("bare_metal_origin_dan_kee")
        r1 = sub.step(1.0)
        seq_val = r1.get("seq", r1.get("state_sequence", 0))
        self.assert_eq(seq_val, 1, "Base: Step 1 sequence")
        self.assert_eq(round(r1["phase_velocity"], 7), 3.1730059, "Base: Dynamic pitch multiplication")

        # 2. Manifold
        engine = RecursiveManifold("bare_metal_origin_dan_kee")
        s1 = engine.pulse(1.0)
        s2 = engine.pulse(0.0)
        self.assert_eq(s2["accumulated_shear_intake"], s1["macro_leak_vent"], "Manifold: Shear recirculation link")

        # 3. Chiral
        chiral = ChiralManifold("chiral_test")
        c1 = chiral.step(1.0)
        self.assert_true(c1["counter_torque"] > 0.0, "Chiral: Positive counter-torque generation")

        # 4. Resonance
        res = ResonanceManifold("resonance_test")
        st = res.step(1.0)
        self.assert_true(st["mode"] in ["EXPANSION_FLOW", "COMPRESSION_LOCK"], "Resonance: Mode active")

        # 5. Mesh
        mesh = MeshCoupledSubstrate("mesh_test")
        m1 = mesh.pulse(1.0)
        self.assert_true(m1["exec_ns"] > 0, "Mesh: Nanosecond execution timer active")

        # 6. Consensus
        m_a = MeshCoupledSubstrate("node_a").pulse(1.0)
        m_b = MeshCoupledSubstrate("node_b").pulse(1.8)
        proof = HeterosisConsensus.interlock(m_a, m_b)
        self.assert_true("heterosis_root" in proof, "Consensus: Root hash synthesized")

        # 7. Ledger Vacuum & ZK
        records = [mesh.pulse(1.0 if i == 0 else 0.0) for i in range(8)]
        voucher = EpochLedgerVacuum.compact_epoch(records, previous_epoch_seal="GENESIS_ZERO")
        self.assert_eq(voucher["state_count_collapsed"], 8, "Vacuum: Collapsed 8 states to 1 voucher")
        zk_attest = ManifoldProofVerifier.verify_epoch_voucher(voucher, previous_seal="GENESIS_ZERO")
        self.assert_true(zk_attest["valid"], "ZK Verifier: Algebraic and cryptographic match")

        # 8. Cache
        cache = ChiralPageCache()
        for s in range(1, 10):
            cache.pin_state({"seq": s, "phase_velocity": 3.17 * s, "core_hash": hashlib.sha256(str(s).encode()).hexdigest()})
        self.assert_eq(len(cache.resident_cache), 8, "Cache: Enforces resident ceiling")

        # 9. Sentinel
        sentinel = SubstrateTripwire()
        safe, _, _ = sentinel.evaluate_boundary({"seq": 1, "phase_velocity": 3.17, "net_pressure": 1.0})
        self.assert_true(safe, "Sentinel: Nominal bounds accepted")
        ruptured, _, _ = sentinel.evaluate_boundary({"seq": 2, "phase_velocity": 60.0, "net_pressure": 1.0})
        self.assert_true(not ruptured, "Sentinel: Critical anomaly tripped circuit breaker")

        # 10. Compensator
        comp = ChiralDriftCompensator()
        out = comp.calculate_precession({"seq": 1, "phase_velocity": 3.20, "net_pressure": 1.0})
        self.assert_true("restoring_precession" in out, "Compensator: Micro-precession vector generated")

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.render_report(elapsed)

    def render_report(self, elapsed_ms: float):
        total = len(self.results)
        passed = total - self.failures
        for name, ok, err in self.results:
            status = "\033[92m[PASS]\033[0m" if ok else "\033[91m[FAIL]\033[0m"
            print(f" {status} {name}")
            if not ok:
                print(f"        └── {err}")
        print("╠══════════════════════════════════════════════════════════════╣")
        color = "\033[92m" if self.failures == 0 else "\033[91m"
        print(f"║ AUDIT COMPLETE: {color}{passed}/{total} PASSED\033[0m in {elapsed_ms:.2f}ms")
        print("╚══════════════════════════════════════════════════════════════╝")
        if self.failures > 0:
            sys.exit(1)

if __name__ == "__main__":
    SubstrateAuditHarness().run_suite()
