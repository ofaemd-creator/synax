#!/usr/bin/env python3
"""
SYNAX Idle-Time Dream Mode Daemon (`src/synax/evolution/dreamer.py`)
=============================================================================
Background daemon that awakens during editor idle periods (30s inactivity)
to autonomously explore performance mutations, loop unrolling depths,
and algebraic simplifications across local `.sx` files.

SPDX-License-Identifier: Apache-2.0
=============================================================================
"""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from synax_ir import parse_sx
from .arena import EvolutionArena, EvolutionReport
from .memory import EpisodicEvolutionMemory


class SynaxDreamDaemon:
    """Autonomous background optimizer operating during idle developer moments."""

    def __init__(
        self,
        workspace_dir: Path,
        idle_threshold_seconds: float = 30.0,
        evolution_callback: Optional[Callable[[Dict], None]] = None,
    ):
        self.workspace_dir = workspace_dir
        self.idle_threshold_seconds = idle_threshold_seconds
        self.evolution_callback = evolution_callback
        self.memory = EpisodicEvolutionMemory(workspace_dir / ".synax" / "evolution_memory.json")
        self.arena = EvolutionArena(self.memory)

        self._last_activity = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def notify_activity(self) -> None:
        """Call on any editor keystroke / save to defer dream mode."""
        self._last_activity = time.time()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._dream_loop, daemon=True, name="SynaxDreamDaemon")
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _dream_loop(self) -> None:
        while self._running:
            time.sleep(2.0)
            idle_duration = time.time() - self._last_activity
            if idle_duration >= self.idle_threshold_seconds:
                self._run_single_dream_iteration()
                # Sleep between dream mutations to conserve CPU battery
                time.sleep(15.0)

    def _run_single_dream_iteration(self) -> Optional[EvolutionReport]:
        # Find candidate .sx files
        sx_files = list(self.workspace_dir.rglob("*.sx"))
        if not sx_files:
            return None

        # Pick a file to optimize
        import random
        target_file = random.choice(sx_files)
        try:
            ir = parse_sx(target_file)
            params = list(ir.param_names)
            report = self.arena.run_match(
                kernel_name=ir.name,
                intent=ir.intent_text,
                param_names=params,
                bench_n=65536,
                bench_repeats=3,
            )

            self.memory.data["dream_runs"] += 1
            self.memory.save()

            if report.winner and report.speedup > 1.05:
                payload = {
                    "type": "dream_evolution",
                    "file": str(target_file),
                    "kernel_name": ir.name,
                    "target": report.winner_target,
                    "throughput_gbs": report.peak_throughput_gbs,
                    "speedup": report.speedup,
                    "message": f"🧬 SYNAX Evrimleşti: '{ir.name}' çekirdeği arka planda %{int((report.speedup-1)*100)} hızlandırıldı ({report.peak_throughput_gbs:.1f} GB/s).",
                }
                if self.evolution_callback:
                    self.evolution_callback(payload)
                return report
        except Exception:
            pass
        return None
