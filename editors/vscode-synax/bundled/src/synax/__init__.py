"""SYNAX public SDK with lazy compiler imports for independent model runtimes."""

from __future__ import annotations
from importlib import import_module
from typing import Any, Final

__version__ = "0.9.0"

_EXPORTS: Final = {
    "AVX2Backend": ("backends", "AVX2Backend"),
    "LLVMIRBackend": ("backends", "LLVMIRBackend"),
    "format_source": ("formatter", "format_sx"),
    "HardwareFingerprint": ("hardware", "HardwareFingerprint"),
    "detect_hardware_fingerprint": ("hardware", "detect_hardware_fingerprint"),
    "ExecutionResult": ("interpreter", "ExecutionResult"),
    "ReferenceInterpreter": ("interpreter", "ReferenceInterpreter"),
    "SafetyRejectError": ("interpreter", "SafetyRejectError"),
    "Lexer": ("lexer", "Lexer"),
    "SourceSpan": ("lexer", "SourceSpan"),
    "SynaxLexError": ("lexer", "SynaxLexError"),
    "Token": ("lexer", "Token"),
    "TokenKind": ("lexer", "TokenKind"),
    "tokenize": ("lexer", "tokenize"),
    "MyelinOptimizationStore": ("myelin_store", "MyelinOptimizationStore"),
    "KernelDecl": ("parser", "KernelDecl"),
    "SynaxModule": ("parser", "SynaxModule"),
    "SynaxParseError": ("parser", "SynaxParseError"),
    "lower_to_synax_ir": ("parser", "lower_to_synax_ir"),
    "parse_expr": ("parser", "parse_expr"),
    "parse_kernel": ("parser", "parse_kernel"),
    "parse_module": ("parser", "parse_module"),
    "SynaxDebugger": ("profiler_debugger", "SynaxDebugger"),
    "SynaxProfiler": ("profiler_debugger", "SynaxProfiler"),
    "SynaxJITKernel": ("python_bridge", "SynaxJITKernel"),
    "Tensor": ("python_bridge", "Tensor"),
    "kernel": ("python_bridge", "kernel"),
    "check_sx": ("sdk", "check_sx"),
    "compile_sx": ("sdk", "compile_sx"),
    "eval_sx": ("sdk", "eval_sx"),
    "format_sx": ("sdk", "format_sx"),
    "hardware_info": ("sdk", "hardware_info"),
    "lock_sx": ("sdk", "lock_sx"),
    "myelin_entries": ("sdk", "myelin_entries"),
    "verify_lock": ("sdk", "verify_lock"),
    "generate_lock": ("semantic_lock", "generate_lock"),
    "verify_lockfile": ("semantic_lock", "verify_lockfile"),
    "write_lockfile": ("semantic_lock", "write_lockfile"),
    "SynaxType": ("type_system", "SynaxType"),
    "SynaxTypeError": ("type_system", "SynaxTypeError"),
    "TypeChecker": ("type_system", "TypeChecker"),
    "UpdateCheckResult": ("updater", "UpdateCheckResult"),
    "check_for_updates": ("updater", "check_for_updates"),
    "check": ("sdk", "check_sx"),
    "compile": ("sdk", "compile_sx"),
}


def __getattr__(name: str) -> Any:
    """Resolve heterogeneous legacy SDK exports only when a caller requests them."""
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute = _EXPORTS[name]
    value = getattr(import_module(f".{module_name}", __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


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
    "Tensor",
    "kernel",
    "SynaxJITKernel",
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
