#!/usr/bin/env bash
set -euo pipefail

NODE_LABEL="${1:-node_primary}"
PORT="${2:-8000}"

echo "[*] Initializing Heterosis Node: ${NODE_LABEL}"
echo "[*] Launching Gateway Service on port ${PORT} with UDP Gossip on 43210..."

exec uvicorn gateway_service:app --host 0.0.0.0 --port "${PORT}" --workers 1
