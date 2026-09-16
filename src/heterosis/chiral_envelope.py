import hashlib
import json
import struct
import hmac
import time
import os

class ChiralEnvelope:
    """
    Zero-PKI Ephemeral State Sealer and Stream Cipher.
    Derives deterministic encryption masks from toroidal manifold harmonics.
    Binds payload confidentiality directly to synchronized phase-lock coordinates.
    """
    DYNAMIC_PITCH = 3.1730059
    HARMONIC_OCTAVE = 8.0

    @staticmethod
    def derive_harmonic_key(peer_root: str, local_velocity: float, local_shear: float, salt: str) -> bytes:
        """
        Derives an ephemeral 256-bit symmetric key by synthesizing peer consensus
        root with real-time local phase coordinates.
        """
        # Pack trajectory vector into binary seed
        trajectory_bytes = struct.pack(">dd", local_velocity, local_shear)
        seed = f"{peer_root}:{salt}".encode("utf-8") + trajectory_bytes
        
        # Double-SHA256 harmonic derivation
        intermediate = hashlib.sha256(seed).digest()
        derived_key = hashlib.sha256(intermediate + f":DYNAMIC_PITCH_{ChiralEnvelope.DYNAMIC_PITCH}".encode("utf-8")).digest()
        return derived_key

    @staticmethod
    def _keystream_generator(key: bytes, length: int) -> bytes:
        """
        Generates a continuous deterministic pseudo-random keystream using
        recursive SHA-256 state stepping.
        """
        keystream = bytearray()
        counter = 0
        while len(keystream) < length:
            counter_bytes = struct.pack(">Q", counter)
            block = hashlib.sha256(key + counter_bytes).digest()
            keystream.extend(block)
            counter += 1
        return bytes(keystream[:length])

    @classmethod
    def seal(cls, payload: bytes, peer_root: str, local_velocity: float, local_shear: float) -> dict:
        """
        Seals payload into an encrypted envelope with HMAC-SHA256 authentication.
        """
        salt = os.urandom(16).hex()
        key = cls.derive_harmonic_key(peer_root, local_velocity, local_shear, salt)
        
        # Stream XOR encryption
        keystream = cls._keystream_generator(key, len(payload))
        ciphertext = bytes([p ^ k for p, k in zip(payload, keystream)])

        # HMAC authentication tag
        auth_tag = hmac.new(key, ciphertext, hashlib.sha256).hexdigest()

        return {
            "salt": salt,
            "ciphertext": ciphertext.hex(),
            "auth_tag": auth_tag,
            "ref_velocity": round(local_velocity, 6),
            "ref_shear": round(local_shear, 6),
            "timestamp_ns": time.time_ns()
        }

    @classmethod
    def unseal(cls, envelope: dict, peer_root: str, velocity: float, shear: float) -> bytes:
        """
        Unseals and authenticates an incoming encrypted envelope.
        Fails if phase velocities differ or payload has been tampered with.
        """
        salt = envelope["salt"]
        ciphertext = bytes.fromhex(envelope["ciphertext"])
        auth_tag = envelope["auth_tag"]

        # Derive identical key using synchronized coordinates
        key = cls.derive_harmonic_key(peer_root, velocity, shear, salt)

        # Verify HMAC integrity
        computed_tag = hmac.new(key, ciphertext, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed_tag, auth_tag):
            raise PermissionError("Envelope authentication failed: Phase mismatch or corrupted cipher.")

        keystream = cls._keystream_generator(key, len(ciphertext))
        decrypted = bytes([c ^ k for c, k in zip(ciphertext, keystream)])
        return decrypted

if __name__ == "__main__":
    from .mesh_substrate import MeshCoupledSubstrate
    from consensus_engine import HeterosisConsensus

    # 1. Spin up two edge nodes and generate a shared consensus root
    node_a = MeshCoupledSubstrate(seed="node_alpha")
    node_b = MeshCoupledSubstrate(seed="node_beta")

    state_a = node_a.pulse(external_drive=1.0)
    state_b = node_b.pulse(external_drive=1.0)

    consensus = HeterosisConsensus.interlock(state_a, state_b)
    shared_root = consensus["heterosis_root"]

    print("[*] Generated Shared Peer Consensus Root:")
    print(f"    -> {shared_root}")

    # 2. Node A seals a confidential payload intended only for Node B
    secret_message = b"INIT_RESONANT_HANDSHAKE:PHASE_ANGLE_3.1730059"
    print(f"\n[*] Node A sealing payload: '{secret_message.decode()}'")
    
    envelope = ChiralEnvelope.seal(
        payload=secret_message,
        peer_root=shared_root,
        local_velocity=state_a["phase_velocity"],
        local_shear=state_a["chiral_vent"]
    )
    print(f"[+] Encrypted Ciphertext: {envelope['ciphertext']}")
    print(f"[+] Envelope Auth Tag  : {envelope['auth_tag']}")

    # 3. Node B unseals using synchronized parameters
    print("\n[*] Node B unsealing envelope using coordinated state...")
    try:
        decrypted_bytes = ChiralEnvelope.unseal(
            envelope=envelope,
            peer_root=shared_root,
            velocity=envelope["ref_velocity"],
            shear=envelope["ref_shear"]
        )
        print(f"[+] Successfully unsealed payload: '{decrypted_bytes.decode()}'")
    except PermissionError as e:
        print(f"[-] Unseal Failure: {e}")

    # 4. Tamper Test: Attempt unseal with altered phase velocity (phase dissonance)
    print("\n[*] Testing phase perturbation attack (unsealing with desynchronized velocity)...")
    try:
        ChiralEnvelope.unseal(
            envelope=envelope,
            peer_root=shared_root,
            velocity=envelope["ref_velocity"] + 0.05,  # Desynchronized phase
            shear=envelope["ref_shear"]
        )
    except PermissionError:
        print("[+] Attack Defended: Manifold rejected key derivation due to phase mismatch.")

    with open("CHIRAL_ENVELOPE_SPEC.json", "w") as f:
        json.dump(envelope, f, indent=2)
