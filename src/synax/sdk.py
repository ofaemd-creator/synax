#!/usr/bin/env python3
"""
SYNAX PUBLIC PYTHON SDK (`src/synax/sdk.py`)
=============================================================================
High-level programmatic Python API for embedding SYNAX (.sx) compilation,
static verification, semantic locking, formatting, and adaptive execution:

    import synax

    ir = synax.check("examples/hemodynamic_cpp.sx")
    compiled = synax.compile("examples/kapili_aktivasyon.sx")
    out = synax.eval_sx("examples/hemodynamic_cpp.sx", [82.0, 80.0], [8.5, 9.0])
=============================================================================
"""

import os
import sys
from array import array
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple, Union

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from synax_ir import SynaxIR, parse_sx
from synax_verifier import LoadedKernel
from synaxc import CompilationResult, SynaxCompiler
from .hardware import HardwareFingerprint, detect_hardware_fingerprint
from .interpreter import ExecutionResult, ReferenceInterpreter
from .myelin_store import MyelinOptimizationStore


def compile_sx(
    source_or_path: str,
    *,
    force_rebuild: bool = False,
    bench_n: int = 4_000_000,
    bench_repeats: int = 15,
    verbose: bool = False,
) -> CompilationResult:
    """Compile, 19-suite verify, benchmark, and cache a `.sx` module."""
    compiler = SynaxCompiler()
    return compiler.compile(
        source_or_path,
        force_rebuild=force_rebuild,
        bench_n=bench_n,
        bench_repeats=bench_repeats,
        verbose=verbose,
    )


def eval_sx(
    source_or_path: str,
    a: Sequence[float],
    b: Sequence[float],
    *,
    prefer_native: bool = True,
    strict_reject: bool = True,
) -> Tuple[array, int]:
    """
    Evaluate a `.sx` program on input sequences `(a, b)`, returning `(output_array, healed_count)`.
    Uses the verified native MYELIN `.dylib` when a C toolchain is available and `prefer_native=True`,
    falling back automatically to the IEEE-754 `ReferenceInterpreter`.
    """
    if len(a) != len(b):
        raise ValueError(f"Girdi uzunlukları eşit olmalı: len(a)={len(a)} != len(b)={len(b)}")

    if prefer_native:
        try:
            comp = compile_sx(source_or_path, bench_n=65536, bench_repeats=3, verbose=False)
            kernel = LoadedKernel(str(comp.winner_dylib_path), name=comp.winner_name)
            arr_a = a if isinstance(a, array) and a.typecode == "f" else array("f", a)
            arr_b = b if isinstance(b, array) and b.typecode == "f" else array("f", b)
            out, healed = kernel.run_pure(arr_a, arr_b)
            h_cnt = int(healed or 0)
            if strict_reject and comp.ir.safety.nonfinite_mode == "reject" and h_cnt > 0:
                from .interpreter import SafetyRejectError
                raise SafetyRejectError(
                    f"[IMMUNE REJECT] '{comp.ir.name}' çekirdeğinde {h_cnt} adet NaN/Inf girdi reddedildi."
                )
            return out, h_cnt
        except (OSError, RuntimeError, FileNotFoundError):
            pass

    interp = ReferenceInterpreter(source_or_path)
    res: ExecutionResult = interp.execute(a, b, strict_reject=strict_reject)
    return res.output, res.healed_count


def check_sx(source_or_path: str) -> SynaxIR:
    """Parse and statically type-check a `.sx` module, returning its canonical `SynaxIR`."""
    from .parser import lower_to_synax_ir

    return lower_to_synax_ir(source_or_path)


def format_sx(source_or_path: str) -> str:
    """Format `.sx` source code into canonical idempotent style."""
    from .formatter import format_sx as _fmt
    raw = Path(source_or_path).read_text(encoding="utf-8") if (
        "\n" not in source_or_path and os.path.exists(source_or_path)
    ) else source_or_path
    return _fmt(raw)


def lock_sx(sx_path: str, lock_path: Optional[str] = None) -> Path:
    """Generate a cryptographic `.sx.lock` Semantic Lockfile."""
    from .semantic_lock import write_lockfile
    return write_lockfile(sx_path, lock_path=lock_path)


def verify_lock(sx_path: str, lock_path: Optional[str] = None) -> Tuple[bool, str]:
    """Verify `.sx` source and compiled output against its `.sx.lock` Semantic Lockfile."""
    from .semantic_lock import verify_lockfile
    return verify_lockfile(sx_path, lock_path=lock_path)


def hardware_info() -> HardwareFingerprint:
    """Return the active host's deterministic AXON `HardwareFingerprint`."""
    return detect_hardware_fingerprint()


def myelin_entries() -> list[Dict[str, Any]]:
    """List all cryptographically verified optimization entries in MYELIN cache."""
    return MyelinOptimizationStore().list_entries()
