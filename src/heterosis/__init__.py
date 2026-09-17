"""
Heterosis Substrate: Sovereign manifold substrate with Ed25519 IPC authority.
"""

__version__ = "0.1.4"

from .fpt_substrate_client import SubstrateIPCClient, sign_intent
from .orchestrator import MasterSubstrateOrchestrator
from .drift_compensator import ChiralDriftCompensator
from .tripwire_sentinel import SubstrateTripwire
from .consensus_engine import HeterosisConsensus
from .adaptive_resonator import AdaptiveResonator

__all__ = [
    "SubstrateIPCClient",
    "sign_intent",
    "MasterSubstrateOrchestrator",
    "ChiralDriftCompensator",
    "SubstrateTripwire",
    "HeterosisConsensus",
    "AdaptiveResonator",
]
