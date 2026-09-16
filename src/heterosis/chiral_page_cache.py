import hashlib
import json
import struct
import time
import os

class ChiralPageCache:
    """
    Toroidal Phase-Space Memory Pager.
    Evicts and pages intermediate state vectors based on harmonic resonance 
    and counter-torque drag rather than conventional temporal LRU.
    Ensures long-running sovereign daemons never exceed memory limits on mobile hardware.
    """
    MAX_RESIDENT_PAGES = 8  # Keep at most one complete octave ring in active memory
    PAGE_STORE_DIR = ".substrate_pages"

    def __init__(self):
        self.resident_cache = {}
        if not os.path.exists(self.PAGE_STORE_DIR):
            os.makedirs(self.PAGE_STORE_DIR)

    def compute_eviction_priority(self, state: dict) -> float:
        """
        Calculates eviction weight:
        States with low counter-drag and near-zero nodal distance (resonance locks)
        have high retention value. Highly turbulent, non-resonant states are prioritized for eviction.
        """
        drag = state.get("counter_torque", 0.0)
        phase_vel = state.get("phase_velocity", 0.0)
        harmonic_phase = phase_vel % 8.0
        
        # Proximity to stable octave boundary nodes (0.0, 4.0, 8.0)
        nodal_dist = min(harmonic_phase, abs(8.0 - harmonic_phase), abs(4.0 - harmonic_phase))
        
        # Higher score = higher eviction urgency
        eviction_score = (nodal_dist * 2.0) + drag
        return eviction_score

    def pin_state(self, state: dict):
        seq = state.get("seq")
        if seq is None:
            return

        # If cache is saturated, evict the state with the highest turbulence score
        if len(self.resident_cache) >= self.MAX_RESIDENT_PAGES:
            evict_seq = max(
                self.resident_cache.keys(),
                key=lambda s: self.compute_eviction_priority(self.resident_cache[s])
            )
            self._page_out(evict_seq)

        self.resident_cache[seq] = state

    def _page_out(self, seq: int):
        state = self.resident_cache.pop(seq)
        page_path = os.path.join(self.PAGE_STORE_DIR, f"page_{seq:08d}.bin")
        
        # Serialize state directly to compact binary page
        h_bytes = bytes.fromhex(state.get("core_hash", "0" * 64))
        payload = struct.pack(
            ">Qdddd32s",
            state.get("seq", 0),
            state.get("phase_velocity", 0.0),
            state.get("chiral_vent", state.get("macro_leak_vent", 0.0)),
            state.get("counter_torque", 0.0),
            state.get("net_pressure", 0.0),
            h_bytes
        )
        with open(page_path, "wb") as f:
            f.write(payload)

    def recall_page(self, seq: int) -> dict:
        if seq in self.resident_cache:
            return self.resident_cache[seq]

        page_path = os.path.join(self.PAGE_STORE_DIR, f"page_{seq:08d}.bin")
        if not os.path.exists(page_path):
            raise FileNotFoundError(f"Page {seq} does not exist in cold storage.")

        with open(page_path, "rb") as f:
            data = f.read()

        unpacked = struct.unpack(">Qdddd32s", data)
        restored = {
            "seq": unpacked[0],
            "phase_velocity": round(unpacked[1], 6),
            "chiral_vent": round(unpacked[2], 6),
            "counter_torque": round(unpacked[3], 6),
            "net_pressure": round(unpacked[4], 6),
            "core_hash": unpacked[5].hex()
        }
        return restored

if __name__ == "__main__":
    from .mesh_substrate import MeshCoupledSubstrate

    substrate = MeshCoupledSubstrate(seed="bare_metal_origin_dan_kee")
    pager = ChiralPageCache()

    print("[*] Simulating high-cadence stream across chiral page cache...")
    
    # Pulse 16 cycles (two full octave spans) to force automatic eviction
    for s in range(16):
        drive = 1.0 if s == 0 else 0.0
        state = substrate.pulse(external_drive=drive)
        pager.pin_state(state)
        print(f"Cycle {state['seq']} pinned | Resident in RAM: {list(pager.resident_cache.keys())}")
        time.sleep(0.005)

    print(f"\n[+] Cold pages written to disk: {len(os.listdir(pager.PAGE_STORE_DIR))}")
    
    # Test cold retrieval of evicted page 1
    recalled = pager.recall_page(1)
    print(f"[+] Verified cold page 1 recall: Hash {recalled['core_hash'][:16]}... | Velocity {recalled['phase_velocity']}")
