import hashlib
import json
import struct

class ManifoldProofVerifier:
    DYNAMIC_PITCH_BASE = 3.1730059
    HARMONIC_OCTAVE = 8.0

    @staticmethod
    def verify_epoch_voucher(voucher: dict, previous_seal: str) -> dict:
        merkle_root = voucher.get("merkle_root")
        reported_seal = voucher.get("epoch_seal")
        claimed_prev_seal = voucher.get("previous_epoch_seal")
        avg_vel = round(float(voucher.get("integrated_phase_velocity", 0.0)), 6)
        accum_shear = round(float(voucher.get("accumulated_epoch_shear", 0.0)), 6)
        span = voucher.get("epoch_span", "0-0")
        start_seq, end_seq = map(int, span.split("-"))

        if claimed_prev_seal != previous_seal:
            return {"valid": False, "reason": "Discontinuous ancestry"}

        expected_min_shear = (avg_vel % ManifoldProofVerifier.HARMONIC_OCTAVE) * (end_seq - start_seq + 1) * 0.15
        conservation_balance = accum_shear - expected_min_shear

        seal_payload = struct.pack(">QQdd", start_seq, end_seq, avg_vel, accum_shear)
        seal_hash = hashlib.sha256(seal_payload).hexdigest()
        expected_epoch_chain = f"{claimed_prev_seal}:{merkle_root}:{seal_hash}".encode("utf-8")
        recomputed_epoch_seal = hashlib.sha256(expected_epoch_chain).hexdigest()

        cryptographic_match = (recomputed_epoch_seal == reported_seal)
        algebraic_soundness = (conservation_balance >= -1e-5)

        valid = cryptographic_match and algebraic_soundness
        return {
            "epoch_verified": span,
            "valid": valid,
            "cryptographic_match": cryptographic_match,
            "algebraic_soundness": algebraic_soundness,
            "conservation_delta": round(conservation_balance, 6),
            "verified_seal": recomputed_epoch_seal
        }
