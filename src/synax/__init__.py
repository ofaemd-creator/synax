"""
SYNAX (`import synax`) — Public Python SDK & Language Frontend (v0.5.0)
=============================================================================
Neuro-Symbolic Kernel Language, Dual-Reference IEEE-754 Verifier, Multi-Target
SIMD / LLVM IR Compiler, Semantic Lock Manager, and Adaptive Myelin Runtime.

SPDX-License-Identifier: Apache-2.0
=============================================================================
"""

from __future__ import annotations

__version__ = "0.5.0"

from .backends import AVX2Backend, LLVMIRBackend
from .formatter import format_sx as format_source
from .hardware import HardwareFingerprint, detect_hardware_fingerprint
from .interpreter import ExecutionResult, ReferenceInterpreter, SafetyRejectError
from .lexer import Lexer, SourceSpan, SynaxLexError, Token, TokenKind, tokenize
from .myelin_store import MyelinOptimizationStore
from .parser import (
    KernelDecl,
    SynaxModule,
    SynaxParseError,
    lower_to_synax_ir,
    parse_expr,
    parse_kernel,
    parse_module,
)
from .profiler_debugger import SynaxDebugger, SynaxProfiler
from .sdk import (
    check_sx,
    compile_sx,
    eval_sx,
    format_sx,
    hardware_info,
    lock_sx,
    myelin_entries,
    verify_lock,
)
from .semantic_lock import generate_lock, verify_lockfile, write_lockfile
from .type_system import SynaxType, SynaxTypeError, TypeChecker
from .updater import UpdateCheckResult, check_for_updates

# Friendly top-level aliases (`synax.check(...)`, `synax.compile(...)`)
check = check_sx
compile = compile_sx  # noqa: A001

__all__ = [
    "__version__",
    "AVX2Backend",
    "LLVMIRBackend",
    "ExecutionResult",
    "HardwareFingerprint",
    "KernelDecl",
    "Lexer",
    "MyelinOptimizationStore",
    "ReferenceInterpreter",
    "SafetyRejectError",
    "SourceSpan",
    "SynaxDebugger",
    "SynaxLexError",
    "SynaxModule",
    "SynaxParseError",
    "SynaxProfiler",
    "SynaxType",
    "SynaxTypeError",
    "Token",
    "TokenKind",
    "TypeChecker",
    "UpdateCheckResult",
    "check",
    "check_for_updates",
    "check_sx",
    "compile",
    "compile_sx",
    "detect_hardware_fingerprint",
    "eval_sx",
    "format_source",
    "format_sx",
    "generate_lock",
    "hardware_info",
    "lock_sx",
    "lower_to_synax_ir",
    "myelin_entries",
    "parse_expr",
    "parse_kernel",
    "parse_module",
    "tokenize",
    "verify_lock",
    "verify_lockfile",
    "write_lockfile",
]
