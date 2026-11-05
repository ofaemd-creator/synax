#!/usr/bin/env python3
"""
SYNAX REFERENCE INTERPRETER (src/synax/interpreter.py)
=============================================================================
Exact IEEE-754 binary32 Reference Interpreter for SYNAX (.sx) programs.
Executes any `SynaxIR` (both `synax 0.1 kernel` and `niyet:/kural:`) purely
in Python without requiring a C/LLVM toolchain, serving both as:
  1. Portable fallback runtime on hosts without a native compiler, and
  2. Ground-truth semantic oracle for differential & fuzz testing.
=============================================================================
"""

import os
import sys
from array import array
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, Union

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from synax_ir import SynaxIR, parse_sx


class SafetyRejectError(RuntimeError):
    """Raised by the Reference Interpreter when `safety { nonfinite = reject }` encounters NaN/Inf."""


@dataclass
class ExecutionResult:
    output: array
    healed_count: int
    ir_hash: str
    kernel_name: str
    backend: str = "reference_interpreter_f32"


class ReferenceInterpreter:
    """Deterministic IEEE-754 single-precision interpreter for `SynaxIR`."""

    def __init__(self, ir_or_source: Union[SynaxIR, str]):
        if isinstance(ir_or_source, SynaxIR):
            self.ir = ir_or_source
        else:
            self.ir = parse_sx(ir_or_source)

    def execute(
        self,
        a: Sequence[float],
        b: Optional[Sequence[float]] = None,
        strict_reject: bool = False,
    ) -> ExecutionResult:
        b_vals = b if b is not None else [0.0] * len(a)
        if len(a) != len(b_vals):
            raise ValueError(
                f"Kanal boyut uyuşmazlığı: shape({self.ir.param_names[0]})={len(a)} != "
                f"shape({self.ir.param_names[1]})={len(b_vals)}"
            )

        if self.ir.is_reduction:
            out, total_healed = self.ir.execute_array(a, b_vals)
            if strict_reject and self.ir.safety.nonfinite_mode == "reject" and total_healed > 0:
                raise SafetyRejectError(
                    f"[IMMUNE REJECT] '{self.ir.name}' çekirdeğinde {total_healed} adet sonlu-olmayan "
                    f"(NaN/Inf) girdi tespit edildi ve yürütme reddedildi."
                )
            return ExecutionResult(
                output=out,
                healed_count=total_healed,
                ir_hash=self.ir.ir_hash,
                kernel_name=self.ir.name,
            )

        out = array("f")
        total_healed = 0
        for i in range(len(a)):
            val, h = self.ir.eval_element_f32(float(a[i]), float(b_vals[i]))
            out.append(val)
            total_healed += h

        if strict_reject and self.ir.safety.nonfinite_mode == "reject" and total_healed > 0:
            raise SafetyRejectError(
                f"[IMMUNE REJECT] '{self.ir.name}' çekirdeğinde {total_healed} adet sonlu-olmayan "
                f"(NaN/Inf) girdi tespit edildi ve yürütme reddedildi."
            )

        return ExecutionResult(
            output=out,
            healed_count=total_healed,
            ir_hash=self.ir.ir_hash,
            kernel_name=self.ir.name,
        )
