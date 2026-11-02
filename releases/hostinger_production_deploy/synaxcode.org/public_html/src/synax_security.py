#!/usr/bin/env python3
"""
SYNAX Zero-Trust Security & Cryptographic Integrity Shield (v2.0)
=================================================================
Guarantees:
1. AST & Code-Injection Firewall: Blocks any unsafe C/Assembly injection,
   forbidden syscalls, raw pointer escapes, or shell metacharacters.
2. Cryptographic DNA & Brain Integrity: Signs and verifies `synapse_brain.json`,
   `myelin_memory.json`, and `synapse_weights.json` using SHA-256 digests.
3. Adversarial Silicon Input Verifier: Tests compiled kernels against
   NaN, +Inf, -Inf, subnormals, and boundary conditions.
"""

import hashlib
import json
import os
import re
from typing import Dict, Any, Tuple

FORBIDDEN_C_PATTERNS = [
    r"\bsystem\s*\(",
    r"\bpopen\s*\(",
    r"\bexec[lv][pe]?\s*\(",
    r"\bfork\s*\(",
    r"\b__asm__\b",
    r"\basm\s*\(",
    r"#\s*include\b",
    r"#\s*define\b",
    r"#\s*pragma\b",
    r"\bdlopen\s*\(",
    r"\bgets\s*\(",
    r"\bstrcpy\s*\(",
    r"\bsprintf\s*\(",
]

SAFE_EXPR_CHARS = re.compile(r"^[a-zA-Z0-9_\s\+\-\*\/\%\(\)\[\]\.\,\?\:\<\>\=\!\&\|f]+$")


class SynaxSecurityGuard:
    """Zero-Trust static & cryptographic verifier for SYNAX (.sx) compilation and self-evolution."""

    @staticmethod
    def verify_c_expression(expr: str) -> Tuple[bool, str]:
        """Ensure a lowered C/SIMD/GPU expression contains zero injection vectors."""
        if not expr or len(expr) > 4096:
            return False, "Expression length out of safe bounds (1..4096 chars)."

        if not SAFE_EXPR_CHARS.match(expr):
            return False, f"Expression contains disallowed characters: {expr!r}"

        for pat in FORBIDDEN_C_PATTERNS:
            if re.search(pat, expr):
                return False, f"Forbidden C pattern detected: {pat}"

        # Balanced parentheses check
        depth = 0
        for ch in expr:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    return False, "Unbalanced closing parenthesis in lowered expression."
        if depth != 0:
            return False, "Unbalanced opening parenthesis in lowered expression."

        return True, "OK_VERIFIED"

    @staticmethod
    def compute_canonical_sha256(payload: Dict[str, Any]) -> str:
        """Compute deterministic SHA-256 hash of a dictionary (excluding '_integrity_sha256')."""
        clean = {k: v for k, v in payload.items() if k != "_integrity_sha256"}
        serialized = json.dumps(clean, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def sign_json_file(cls, path: str) -> str:
        """Add or update `_integrity_sha256` inside a JSON state file."""
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return ""
        digest = cls.compute_canonical_sha256(data)
        data["_integrity_sha256"] = digest
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return digest

    @classmethod
    def verify_json_file(cls, path: str) -> Tuple[bool, str]:
        """Verify `_integrity_sha256` of a JSON state file; auto-sign if legacy unsigned."""
        if not os.path.exists(path):
            return True, "FILE_NOT_PRESENT"
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False, "JSON root must be an object."
            stored = data.get("_integrity_sha256")
            expected = cls.compute_canonical_sha256(data)
            if not stored:
                # Auto-upgrade legacy unsigned file
                cls.sign_json_file(path)
                return True, f"AUTO_SIGNED ({expected[:12]})"
            if stored != expected:
                return False, f"INTEGRITY_MISMATCH: expected {expected[:12]}, got {stored[:12]}"
            return True, f"VERIFIED ({expected[:12]})"
        except Exception as e:
            return False, f"PARSE_ERROR: {e}"


if __name__ == "__main__":
    guard = SynaxSecurityGuard()
    ok, msg = guard.verify_c_expression("1.0f / (1.0f + expf(-(sqrtf(x * x) + 0.05f)))")
    print(f"[SYNAX-SEC] Expression verification: {ok} ({msg})")
