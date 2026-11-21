"""SYNAX Isolated & Restricted Code Execution Sandbox.

Enforces:
1. Static AST Security Audit (Blocking dangerous imports, reflection, shell/subprocesses, network sockets).
2. Resource Limits (Execution timeout, memory limits, CPU time).
3. Filesystem Sandboxing (Isolated disposable scratch workspace with guaranteed cleanup).
4. Explicit User Approval Checkpoints for elevated permissions.
"""

from __future__ import annotations

import ast
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class SecurityViolationError(Exception):
    """Raised when code violates sandbox security policies."""
    pass


class ASTSafetyAuditor(ast.NodeVisitor):
    """Inspects Python Abstract Syntax Trees for unauthorized system access."""

    FORBIDDEN_MODULES: Set[str] = {
        "os", "posix", "nt", "subprocess", "shutil", "socket", "http",
        "urllib", "requests", "pty", "commands", "builtin", "importlib",
        "ctypes", "winreg", "sys", "multiprocessing", "threading", "signal",
    }

    FORBIDDEN_FUNCTIONS: Set[str] = {
        "eval", "exec", "__import__", "compile", "open", "getattr", "setattr",
        "delattr", "globals", "locals", "breakpoint",
    }

    def __init__(self, allow_network: bool = False, allow_fs_read: bool = False) -> None:
        self.allow_network = allow_network
        self.allow_fs_read = allow_fs_read
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            if base_mod in self.FORBIDDEN_MODULES:
                self.violations.append(f"Forbidden import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod in self.FORBIDDEN_MODULES:
                self.violations.append(f"Forbidden import from '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_FUNCTIONS:
                # If fs_read is allowed, permit 'open' in read-only mode only if carefully audited
                if node.func.id == "open" and not self.allow_fs_read:
                    self.violations.append("Forbidden function call: 'open'")
                elif node.func.id != "open":
                    self.violations.append(f"Forbidden function call: '{node.func.id}'")
        elif isinstance(node.func, ast.Attribute):
            # Check for dangerous attribute access like os.system
            if node.func.attr in {"system", "popen", "spawn", "exec", "remove", "rmdir"}:
                self.violations.append(f"Forbidden attribute call: '.{node.func.attr}'")
        self.generic_visit(node)


@dataclass
class SandboxResult:
    """Structured result of sandboxed code execution."""
    success: bool
    returncode: int
    stdout: str
    stderr: str
    elapsed_ms: float
    violations: List[str] = field(default_factory=list)
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "elapsed_ms": self.elapsed_ms,
            "violations": self.violations,
            "requires_approval": self.requires_approval,
        }


class SynaxRestrictedSandbox:
    """A restricted execution sandbox with static verification and resource containment."""

    def __init__(
        self,
        timeout_seconds: float = 3.0,
        max_output_bytes: int = 16384,
        allow_network: bool = False,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.allow_network = allow_network

    def audit_code(self, code_str: str) -> List[str]:
        """Performs static AST analysis on code string."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return [f"SyntaxError in code: {e}"]

        auditor = ASTSafetyAuditor(allow_network=self.allow_network)
        auditor.visit(tree)
        return auditor.violations

    def execute(
        self,
        code_str: str,
        user_approved: bool = False,
    ) -> SandboxResult:
        """Executes Python code in an isolated temporary workspace with strict resource bounds."""
        violations = self.audit_code(code_str)

        if violations and not user_approved:
            return SandboxResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr="SECURITY_VIOLATION: Code contains restricted constructs and requires explicit authorization.",
                elapsed_ms=0.0,
                violations=violations,
                requires_approval=True,
            )

        # Create isolated temporary directory
        temp_dir = tempfile.mkdtemp(prefix="synax_sandbox_")
        script_path = Path(temp_dir) / "safe_script.py"

        try:
            script_path.write_text(code_str, encoding="utf-8")
            t0 = time.time()

            # Pre-exec hook to set resource limits on POSIX
            def set_limits() -> None:
                # Limit CPU time to timeout + 1 second
                try:
                    resource.setrlimit(
                        resource.RLIMIT_CPU,
                        (int(self.timeout_seconds) + 1, int(self.timeout_seconds) + 2),
                    )
                    # Limit virtual memory to 256MB
                    max_mem = 256 * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (max_mem, max_mem))
                except Exception:
                    pass

            res = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir,
                preexec_fn=set_limits if hasattr(os, "fork") else None,
            )
            elapsed_ms = round((time.time() - t0) * 1000.0, 2)

            stdout = res.stdout[:self.max_output_bytes]
            stderr = res.stderr[:self.max_output_bytes]

            return SandboxResult(
                success=(res.returncode == 0),
                returncode=res.returncode,
                stdout=stdout,
                stderr=stderr,
                elapsed_ms=elapsed_ms,
                violations=violations,
                requires_approval=False,
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                returncode=-2,
                stdout="",
                stderr=f"EXECUTION_TIMEOUT: Code execution exceeded {self.timeout_seconds} seconds limit.",
                elapsed_ms=round(self.timeout_seconds * 1000.0, 2),
                violations=violations,
                requires_approval=False,
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                returncode=-3,
                stdout="",
                stderr=f"EXECUTION_ERROR: {str(e)}",
                elapsed_ms=0.0,
                violations=violations,
                requires_approval=False,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
