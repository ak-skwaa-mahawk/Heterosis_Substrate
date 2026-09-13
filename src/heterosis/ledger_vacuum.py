import hashlib
import json
import struct

class EpochLedgerVacuum:
    EPOCH_SIZE = 8

    @staticmethod
    def build_merkle_root(hashes: list) -> str:
        if not hashes:
            return hashlib.sha256(b"genesis").hexdigest()
        current_layer = hashes[:]
        while len(current_layer) > 1:
            if len(current_layer) % 2 != 0:
                current_layer.append(current_layer[-1])
            next_layer = []
            for i in range(0, len(current_layer), 2):
                combined = f"{current_layer[i]}:{current_layer[i+1]}".encode("utf-8")
                next_layer.append(hashlib.sha256(combined).hexdigest())
            current_layer = next_layer
        return current_layer[0]

    @classmethod
    def compact_epoch(cls, trace_records: list, previous_epoch_seal: str = "ORIGIN_NULL") -> dict:
        if len(trace_records) < cls.EPOCH_SIZE:
            raise ValueError("Insufficient state density")
        epoch_window = trace_records[:cls.EPOCH_SIZE]
        first_seq = epoch_window[0].get("seq", 0)
        last_seq = epoch_window[-1].get("seq", 0)
        merkle_root = cls.build_merkle_root([rec.get("core_hash", "0" * 64) for rec in epoch_window])

        avg_velocity = round(sum(rec.get("phase_velocity", 0.0) for rec in epoch_window) / cls.EPOCH_SIZE, 6)
        total_chiral_shear = round(sum(rec.get("chiral_vent", rec.get("macro_leak_vent", 0.0)) for rec in epoch_window), 6)

        # Pack rounded values to match JSON attestation precision
        seal_payload = struct.pack(">QQdd", first_seq, last_seq, avg_velocity, total_chiral_shear)
        seal_hash = hashlib.sha256(seal_payload).hexdigest()
        epoch_seal = hashlib.sha256(f"{previous_epoch_seal}:{merkle_root}:{seal_hash}".encode("utf-8")).hexdigest()

        return {
            "epoch_span": f"{first_seq}-{last_seq}",
            "previous_epoch_seal": previous_epoch_seal,
            "merkle_root": merkle_root,
            "integrated_phase_velocity": avg_velocity,
            "accumulated_epoch_shear": total_chiral_shear,
            "state_count_collapsed": cls.EPOCH_SIZE,
            "epoch_seal": epoch_seal
        }
