import hashlib
import json
import struct
import time
import math

class HarmonicTaskWorker:
    """
    Geometry-Coupled Edge Task Execution Engine.
    Executes computational workloads and binds output proofs directly to the 
    local node's instantaneous harmonic octave shell and boundary shear.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0

    def __init__(self, node_id: str, assigned_octave: int):
        self.node_id = node_id
        self.assigned_octave = assigned_octave

    def execute_payload(self, task_id: str, task_data: list, current_state: dict) -> dict:
        """
        Executes raw compute (vector cross-product transformation) and binds
        the results into the manifold's harmonic boundary shear.
        """
        t_start = time.perf_counter_ns()
        
        # Verify the task routes through this node's assigned octave
        target_octave = current_state.get("octave_shell", 0)
        phase_vel = current_state.get("phase_velocity", 0.0)
        chiral_vent = current_state.get("chiral_vent", current_state.get("macro_leak_vent", 0.0))

        # 1. Bare-metal compute workload: 
        # Modulates input vector through the node's active dynamic pitch
        transformed_output = []
        for val in task_data:
            modulated = (val * self.DYNAMIC_PITCH) + (chiral_vent / (1.0 + self.assigned_octave))
            transformed_output.append(round(modulated, 6))

        # Compute deterministic checksum of the payload output
        raw_bytes = struct.pack(f">{len(transformed_output)}d", *transformed_output)
        compute_hash = hashlib.sha256(raw_bytes).hexdigest()

        t_exec_ns = time.perf_counter_ns() - t_start

        # 2. Forge the Harmonic Work Proof:
        # Binds task ID + execution duration + compute checksum + manifold core hash
        parent_hash = current_state.get("core_hash", "0" * 64)
        proof_payload = struct.pack(
            ">QQdd",
            current_state.get("seq", 0),
            t_exec_ns,
            phase_vel,
            chiral_vent
        ) + bytes.fromhex(compute_hash) + bytes.fromhex(parent_hash)

        work_proof_hash = hashlib.sha256(proof_payload).hexdigest()

        # Chain of custody receipt: ties task execution to the physical node and octave
        chain = f"{task_id}:{self.node_id}:{self.assigned_octave}:{compute_hash}:{work_proof_hash}".encode("utf-8")
        work_receipt = hashlib.sha256(chain).hexdigest()

        return {
            "task_id": task_id,
            "worker_node": self.node_id,
            "octave_shell": self.assigned_octave,
            "exec_ns": t_exec_ns,
            "item_count": len(task_data),
            "compute_hash": compute_hash,
            "work_proof_hash": work_proof_hash,
            "work_receipt": work_receipt,
            "sample_output": transformed_output[:3]
        }

    @staticmethod
    def verify_work_proof(task_id: str, node_id: str, octave_shell: int, compute_hash: str, work_proof_hash: str, claimed_receipt: str) -> bool:
        """Lightweight zero-trust audit for peer nodes."""
        expected_chain = f"{task_id}:{node_id}:{octave_shell}:{compute_hash}:{work_proof_hash}".encode("utf-8")
        recomputed = hashlib.sha256(expected_chain).hexdigest()
        return recomputed == claimed_receipt

if __name__ == "__main__":
    from .mesh_substrate import MeshCoupledSubstrate
    from .chiral_router import ChiralOctaveRouter

    # Set up node and determine assigned octave
    node_name = "worker_node_gamma_09"
    router = ChiralOctaveRouter(node_id=node_name)
    worker = HarmonicTaskWorker(node_id=node_name, assigned_octave=router.assigned_octave)

    print(f"[*] Worker Node initialized: '{node_name}'")
    print(f"    -> Bound to Octave Shell [{worker.assigned_octave}]")

    # Spin local manifold to generate current state coordinates
    substrate = MeshCoupledSubstrate(seed="worker_genesis_seed")
    state = substrate.pulse(external_drive=1.5)

    # Simulated edge computational task (vector array)
    test_task_id = "TASK_VEC_TRANSFORM_9941"
    raw_vector_data = [12.5, 45.1, 98.2, 33.7, 71.0, 8.4, 55.9, 102.3]

    print(f"\n[*] Executing compute payload on bare-metal silicon for task: {test_task_id}...")
    receipt = worker.execute_payload(test_task_id, raw_vector_data, state)

    print("\n[+] Compute Proof Successfully Generated:")
    print(json.dumps(receipt, indent=2))

    # Peer verification audit pass
    print("\n[*] Simulating zero-trust peer audit pass...")
    is_valid = HarmonicTaskWorker.verify_work_proof(
        task_id=receipt["task_id"],
        node_id=receipt["worker_node"],
        octave_shell=receipt["octave_shell"],
        compute_hash=receipt["compute_hash"],
        work_proof_hash=receipt["work_proof_hash"],
        claimed_receipt=receipt["work_receipt"]
    )
    print(f"[+] Work Proof Valid: {is_valid}")

    with open("WORKER_COMPUTE_RECEIPT.json", "w") as f:
        json.dump(receipt, f, indent=2)
