import hashlib
import json
import struct
import os
import time

class EpochLedgerVacuum:
    """
    Bare-metal state compaction and Merkle epoch sealer.
    Compresses discrete sequence traces into collapsed harmonic vouchers.
    Preserves cryptographic continuity while freeing local device storage.
    """
    EPOCH_SIZE = 8  # Enforce compression lock at full octave cycle

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
        """
        Collapses a block of 8 sequential state receipts into a single epoch voucher.
        """
        if len(trace_records) < cls.EPOCH_SIZE:
            raise ValueError(f"Insufficient state density. Need {cls.EPOCH_SIZE} states, got {len(trace_records)}")

        epoch_window = trace_records[:cls.EPOCH_SIZE]
        first_seq = epoch_window[0].get("seq", 0)
        last_seq = epoch_window[-1].get("seq", 0)

        core_hashes = [rec.get("core_hash", "0" * 64) for rec in epoch_window]
        merkle_root = cls.build_merkle_root(core_hashes)

        # Calculate integrated epoch field physics
        avg_velocity = sum(rec.get("phase_velocity", 0.0) for rec in epoch_window) / cls.EPOCH_SIZE
        total_chiral_shear = sum(rec.get("chiral_vent", rec.get("macro_leak_vent", 0.0)) for rec in epoch_window)
        
        # Binary seal packing
        seal_payload = struct.pack(
            ">QQdd",
            first_seq,
            last_seq,
            avg_velocity,
            total_chiral_shear
        )
        seal_hash = hashlib.sha256(seal_payload).hexdigest()

        # Immutable Epoch Receipt
        epoch_chain = f"{previous_epoch_seal}:{merkle_root}:{seal_hash}".encode("utf-8")
        epoch_seal = hashlib.sha256(epoch_chain).hexdigest()

        return {
            "epoch_span": f"{first_seq}-{last_seq}",
            "previous_epoch_seal": previous_epoch_seal,
            "merkle_root": merkle_root,
            "integrated_phase_velocity": round(avg_velocity, 6),
            "accumulated_epoch_shear": round(total_chiral_shear, 6),
            "state_count_collapsed": cls.EPOCH_SIZE,
            "epoch_seal": epoch_seal
        }

if __name__ == "__main__":
    from mesh_substrate import MeshCoupledSubstrate

    substrate = MeshCoupledSubstrate(seed="bare_metal_origin_dan_kee")
    
    # Generate an entire octave ring (8 cycles)
    print("[*] Cycling full 8-harmonic octave ring on bare-metal silicon...")
    raw_trace = []
    for step in range(8):
        drive = 1.0 if step == 0 else 0.0
        state = substrate.pulse(external_drive=drive)
        raw_trace.append(state)
        time.sleep(0.005)

    # Execute bare-metal vacuum compaction
    vacuum = EpochLedgerVacuum()
    epoch_voucher = vacuum.compact_epoch(raw_trace)

    print("\n[+] Epoch Sealed. Storage collapsed into sovereign Merkle voucher:")
    print(json.dumps(epoch_voucher, indent=2))

    # Persist the compact voucher
    with open("EPOCH_VOUCHER.json", "w") as f:
        json.dump(epoch_voucher, f, indent=2)
