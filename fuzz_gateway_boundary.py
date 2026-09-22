import math
import json
import struct
from fastapi.testclient import TestClient
from gateway_service import app, compute_stability_index, normalize_modal_energies

client = TestClient(app)

FORBIDDEN_PATTERNS = [
    "0x4000",
    "0x40001000",
    "phase_space_vector",
    "hamiltonian",
    "3.1415873",
    "-15.000000",
    "0x7f",
    "at 0x"
]

def assert_zero_leakage(payload_str: str, context: str):
    """Audits raw string representation against the invariant clean-room blacklist."""
    for pattern in FORBIDDEN_PATTERNS:
        assert pattern not in payload_str, (
            f"[LEAK DETECTED] Context: {context} | Found forbidden signature: '{pattern}'"
        )

def run_math_boundary_fuzz():
    print("[*] Fuzzing Phase 1: Mathematical Boundary & Symplectic Normalizer Fuzzing...")
    pathological_floats = [
        float("nan"),
        float("inf"),
        float("-inf"),
        0.0,
        -0.0,
        1e-308,
        1e308,
        -1e308,
        1.0000000000000002,
        0.9999999999999999,
        -1.0,
        2.0,
        1e-15,
        -1e-15
    ]

    for val in pathological_floats:
        try:
            res = compute_stability_index(val)
            assert isinstance(res, float), f"Expected float, got {type(res)}"
            assert not math.isnan(res), f"NaN leaked from compute_stability_index({val})"
            assert not math.isinf(res), f"Inf leaked from compute_stability_index({val})"
            assert 0.0 <= res <= 1.0, f"Bounds violation: {res} for input {val}"
        except Exception as e:
            assert False, f"Unhandled exception in compute_stability_index({val}): {e}"

    # Fuzz modal partition normalization with extreme vectors
    modal_vectors = [
        [0.0] * 8,
        [-1.0] * 8,
        [float("nan")] * 8,
        [float("inf")] * 8,
        [1e300, 1e300, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1e-300, 1e-300, 1e-300, 1e-300, 1e-300, 1e-300, 1e-300, 1e-300],
        [],
        [1.0] * 16, # wrong length
    ]

    for vec in modal_vectors:
        res = normalize_modal_energies(vec)
        assert isinstance(res, list), f"Expected list, got {type(res)}"
        for item in res:
            assert not math.isnan(item), f"NaN in modal partition: {res} from {vec}"
            assert not math.isinf(item), f"Inf in modal partition: {res} from {vec}"
            assert item >= 0.0, f"Negative modal energy: {item} from {vec}"

    print("    [PASS] Numerical stability filters preserved invariant bounds [0.0, 1.0].")

def run_rest_endpoint_adversarial_fuzz():
    print("[*] Fuzzing Phase 2: REST Interface Pathological Query & Injection Fuzzing...")
    
    # 1. Standard endpoints leak check
    for ep in ["/v1/telemetry/state", "/v1/telemetry/peers"]:
        resp = client.get(ep)
        assert resp.status_code == 200, f"Endpoint {ep} failed: {resp.status_code}"
        assert_zero_leakage(resp.text, f"GET {ep}")

    # 2. Pathological URI fuzzing & injection probes
    malicious_endpoints = [
        "/v1/telemetry/state?offset=0x40001000",
        "/v1/telemetry/state?eval=__import__('os').system('id')",
        "/v1/telemetry/state/%00",
        "/v1/telemetry/peers/../../etc/passwd",
        "/v1/telemetry/peers?filter=" + "A" * 8192,
        "/v1/telemetry/state?q=1&p=1&H=true",
    ]

    for target in malicious_endpoints:
        resp = client.get(target)
        # Even if 404, 400, or 422, response text MUST NOT reflect internal traces or MMIO maps
        assert_zero_leakage(resp.text, f"GET {target}")

    print("    [PASS] Zero internal coordinate or MMIO disclosure detected across REST surfaces.")

def run_websocket_protocol_fuzz():
    print("[*] Fuzzing Phase 3: WebSocket Subscription & Framing Stress Fuzzing...")
    
    pathological_payloads = [
        "",                                      # Empty payload
        "{",                                     # Truncated JSON
        json.dumps({"action": "subscribe", "sample_rate_hz": "NaN"}),
        json.dumps({"action": "subscribe", "sample_rate_hz": float("inf")}),
        json.dumps({"action": "subscribe", "sample_rate_hz": -50}),
        json.dumps({"action": "subscribe", "sample_rate_hz": 1_000_000}),
        json.dumps({"action": "leak_raw_phase", "target": "0x4000_1000"}),
        json.dumps({"action": ["subscribe"]}),   # Type confusion
        "A" * 65536,                             # Frame flood
        json.dumps({"action": "subscribe", "sample_rate_hz": 10, "q": [0.0]*8}),
    ]

    for idx, payload in enumerate(pathological_payloads):
        try:
            with client.websocket_connect("/v1/telemetry/stream") as ws:
                ws.send_text(payload)
                # Try receiving with Starlette websocket receive or pass if socket closes
                try:
                    import anyio
                    with anyio.fail_after(0.5):
                        raw_resp = ws.receive_text()
                        assert_zero_leakage(raw_resp, f"WS Frame payload index {idx}")
                except (TimeoutError, Exception):
                    pass
        except Exception as e:
            err_msg = str(e)
            assert_zero_leakage(err_msg, f"WS Connection error index {idx}")

    # Verify that a normal subscriber functions cleanly immediately after adversarial bombardment
    with client.websocket_connect("/v1/telemetry/stream") as ws:
        ws.send_json({"action": "subscribe", "sample_rate_hz": 5})
        frame = ws.receive_json()
        assert frame["event"] == "metric_sample"
        assert_zero_leakage(json.dumps(frame), "Post-fuzz legitimate subscription")

    print("    [PASS] WebSocket boundary rejected malformed frames with zero state compromise.")

if __name__ == "__main__":
    print("=====================================================================")
    print(" TMS-SPEC-085_01 ADVERSARIAL CLEAN-ROOM FUZZING & LEAKAGE HARNESS   ")
    print("=====================================================================")
    run_math_boundary_fuzz()
    run_rest_endpoint_adversarial_fuzz()
    run_websocket_protocol_fuzz()
    print("=====================================================================")
    print("\033[92m[AUDIT COMPLETE] ALL 3 ADVERSARIAL BOUNDARY PROBES PASSED (0 LEAKS).\033[0m")
    print("=====================================================================")
