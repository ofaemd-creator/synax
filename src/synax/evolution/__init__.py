"""
SYNAX Autonomous Neuro-Symbolic Evolution Subsystem (`src/synax/evolution`)
=============================================================================
SPDX-License-Identifier: Apache-2.0
=============================================================================
"""

from .arena import EvolutionArena, EvolutionReport
from .dreamer import SynaxDreamDaemon
from .memory import EpisodicEvolutionMemory
from .synthesizer import KernelCandidate, NeuroSymbolicSynthesizer

__all__ = [
    "EpisodicEvolutionMemory",
    "EvolutionArena",
    "EvolutionReport",
    "KernelCandidate",
    "NeuroSymbolicSynthesizer",
    "SynaxDreamDaemon",
]
