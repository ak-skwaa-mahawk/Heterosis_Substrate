"""
Heterosis Substrate: Sovereign manifold substrate with Ed25519 IPC authority.
"""

__version__ = "0.1.0"

from .fpt_substrate_client import SubstrateIPCClient, sign_intent
from .orchestrator import MasterSubstrateOrchestrator

__all__ = [
    "SubstrateIPCClient",
    "sign_intent",
    "MasterSubstrateOrchestrator",
]
