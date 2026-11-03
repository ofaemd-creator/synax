"""
SYNAX Cryptographic Semantic Lockfile Manager (`src/synax/semantic_lock.py`)
============================================================================
Generates, writes, and verifies tamper-evident `.sx.lock` Semantic Lockfiles
containing:
  - Canonical `ir_hash`, lowered AST, and `SafetyPolicy`
  - 32 deterministic IEEE-754 golden test vectors (clean normals, `0.0`, `-0.0`,
    `NaN`, `+Inf`, `-Inf`, `1e-40` subnormal, `3.4e38`, `-1000.0`, `2500.0`)
    encoded in lossless IEEE-754 hexadecimal format (`float.hex()` / `"nan"` /
    `"inf"` / `"-inf"`) with expected `healed` anomaly counts
  - Zero-Trust SHA-256 integrity signature (`_integrity_sha256`) from
    `SynaxSecurityGuard`
  - Optional binary verification against a compiled `LoadedKernel`
"""

from __future__ import annotations

import json
import math
import os
import sys
from array import array
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .parser import lower_to_synax_ir

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from synax_ir import SynaxIR, _f32  # noqa: E402
from synax_security import SynaxSecurityGuard  # noqa: E402
from synax_verifier import check_equivalence_pure  # noqa: E402


# 32 deterministic golden `(a, b)` vectors covering clean normals, signed zeros,
# IEEE-754 NaN / ±Inf, subnormals (`1e-40`), near-FLT_MAX (`3.4e38`), and
# biomedical / safety-bound spikes (`-1000.0`, `2500.0`).
GOLDEN_INPUT_PAIRS_32: Tuple[Tuple[float, float], ...] = (
    # 0..3: Signed zero combinations
    (0.0, 0.0),
    (-0.0, 0.0),
    (0.0, -0.0),
    (-0.0, -0.0),
    # 4..15: Clean normal values (unit, hemodynamic, fractional, negative, irrational)
    (1.0, 1.0),
    (1.0, -1.0),
    (-1.0, 1.0),
    (80.0, 8.0),
    (65.5, 12.25),
    (0.25, 0.75),
    (-2.5, -0.5),
    (3.1415927, 2.7182817),
    (120.0, 120.0),
    (1e-6, -1e-6),
    (100.0, 0.001),
    (-42.125, 17.875),
    # 16..18: Subnormals (`1e-40` in binary32)
    (1e-40, 1.0),
    (1.0, 1e-40),
    (1e-40, -1e-40),
    # 19..21: Near-FLT_MAX extremes (`3.4e38`)
    (3.4e38, 1.0),
    (1.0, -3.4e38),
    (3.4e38, 3.4e38),
    # 22..25: Threshold & out-of-bound spikes (`-1000.0`, `2500.0`)
    (-1000.0, 10.0),
    (10.0, -1000.0),
    (2500.0, 12.0),
    (80.0, 2500.0),
    # 26..31: Non-finite IEEE-754 values (`NaN`, `+Inf`, `-Inf`)
    (float("nan"), 1.0),
    (1.0, float("nan")),
    (float("nan"), float("nan")),
    (float("inf"), 1.0),
    (1.0, float("-inf")),
    (float("inf"), float("-inf")),
)

assert len(GOLDEN_INPUT_PAIRS_32) == 32


def encode_f32_hex(val: float) -> str:
    """Encode an IEEE-754 binary32 float into lossless hex / special string."""
    v = _f32(val)
    if math.isnan(v):
        return "nan"
    if math.isinf(v):
        return "inf" if v > 0 else "-inf"
    return v.hex()


def decode_f32_hex(rep: str) -> float:
    """Decode an `encode_f32_hex` string back into an exact binary32 Python float."""
    s = rep.strip().lower()
    if s == "nan":
        return float("nan")
    if s in ("inf", "+inf"):
        return float("inf")
    if s == "-inf":
        return float("-inf")
    return _f32(float.fromhex(s))


def _default_lock_path(sx_path: Union[str, Path]) -> Path:
    p = Path(sx_path)
    if p.suffix == ".sx":
        return p.with_suffix(".sx.lock")
    return Path(f"{p}.sx.lock")


def generate_lock(sx_path_or_text: Union[str, Path]) -> Dict[str, Any]:
    """
    Compile `sx_path_or_text` to `SynaxIR`, evaluate all 32 deterministic golden
    vectors via `ir.eval_element_f32`, and sign with `SynaxSecurityGuard`.
    """
    ir: SynaxIR = lower_to_synax_ir(sx_path_or_text)

    vectors: List[Dict[str, Any]] = []
    total_healed = 0

    for idx, (raw_a, raw_b) in enumerate(GOLDEN_INPUT_PAIRS_32):
        a_f32 = _f32(raw_a)
        b_f32 = _f32(raw_b)
        out_f32, healed_i = ir.eval_element_f32(a_f32, b_f32)
        total_healed += healed_i
        vectors.append(
            {
                "index": idx,
                "a_hex": encode_f32_hex(a_f32),
                "b_hex": encode_f32_hex(b_f32),
                "out_hex": encode_f32_hex(out_f32),
                "healed": int(healed_i),
            }
        )

    payload: Dict[str, Any] = {
        "lock_version": "1.0",
        "synax_version": ir.version,
        "kernel_name": ir.name,
        "syntax_format": ir.syntax_format,
        "param_names": list(ir.param_names),
        "ir_hash": ir.ir_hash,
        "canonical_ir": ir.to_canonical_dict(),
        "safety_policy": ir.safety.to_dict(),
        "canonical_ast": ir.expr.to_dict(),
        "golden_vector_count": len(vectors),
        "total_expected_healed": int(total_healed),
        "golden_vectors": vectors,
    }
    payload["_integrity_sha256"] = SynaxSecurityGuard.compute_canonical_sha256(payload)
    return payload


def write_lockfile(
    sx_path: Union[str, Path],
    lock_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Generate the cryptographic Semantic Lock for `sx_path` and write it to
    `lock_path` (defaults to `<sx_path>.lock`, e.g., `foo.sx.lock`).
    """
    src_path = Path(sx_path)
    if not src_path.exists():
        raise FileNotFoundError(f"SYNAX source file not found: {src_path}")

    out_path = Path(lock_path) if lock_path is not None else _default_lock_path(src_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lock_data = generate_lock(src_path)
    serialized = json.dumps(lock_data, indent=2, ensure_ascii=False) + "\n"
    out_path.write_text(serialized, encoding="utf-8")
    return out_path


def verify_lockfile(
    sx_path: Union[str, Path],
    lock_path: Optional[Union[str, Path]] = None,
    kernel: Optional[Any] = None,
) -> Tuple[bool, str]:
    """
    Verify a `.sx.lock` Semantic Lockfile against `sx_path` (and optionally a
    compiled `LoadedKernel`):
      1. Cryptographic `_integrity_sha256` tamper check via `SynaxSecurityGuard`
      2. Zero `ir_hash`, `SafetyPolicy`, and canonical AST drift against `.sx`
      3. Bit-exact verification of all 32 golden vectors against `ir.eval_element_f32`
      4. Optional native execution equivalence check against `kernel` (`LoadedKernel`)
    """
    target_lock: Optional[Path] = None
    if lock_path is not None:
        target_lock = Path(lock_path)
    elif isinstance(sx_path, Path) or ("\n" not in str(sx_path) and os.path.exists(str(sx_path))):
        target_lock = _default_lock_path(sx_path)
    else:
        return False, "lock_path must be provided when sx_path is raw source text."

    if not target_lock.exists():
        return False, f"LOCKFILE_MISSING: '{target_lock}' does not exist."

    try:
        lock_data = json.loads(target_lock.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"LOCKFILE_PARSE_ERROR: {exc}"

    if not isinstance(lock_data, dict):
        return False, "LOCKFILE_INVALID_ROOT: expected JSON object."

    # 1. Strict SHA-256 cryptographic integrity check (never auto-signs missing/tampered hashes)
    stored_sha = lock_data.get("_integrity_sha256")
    if not isinstance(stored_sha, str) or not stored_sha:
        return False, "INTEGRITY_MISSING: lockfile is missing '_integrity_sha256'."

    expected_sha = SynaxSecurityGuard.compute_canonical_sha256(lock_data)
    if stored_sha != expected_sha:
        return (
            False,
            f"INTEGRITY_MISMATCH: expected SHA-256 {expected_sha[:12]}, got {stored_sha[:12]}.",
        )

    # 2. Parse `.sx` and check `ir_hash` / policy / AST drift
    try:
        ir = lower_to_synax_ir(sx_path)
    except Exception as exc:
        return False, f"SOURCE_COMPILE_ERROR: {exc}"

    locked_ir_hash = lock_data.get("ir_hash")
    if ir.ir_hash != locked_ir_hash:
        return (
            False,
            f"IR_HASH_DRIFT: lockfile expects ir_hash '{locked_ir_hash}', current source has '{ir.ir_hash}'.",
        )

    if lock_data.get("safety_policy") != ir.safety.to_dict():
        return False, "SAFETY_POLICY_DRIFT: SafetyPolicy differs from locked specification."

    if lock_data.get("canonical_ast") != ir.expr.to_dict():
        return False, "CANONICAL_AST_DRIFT: lowered AST differs from locked specification."

    # 3. Verify all 32 golden vectors against `ir.eval_element_f32`
    vectors = lock_data.get("golden_vectors")
    if not isinstance(vectors, list) or len(vectors) != 32:
        got_len = len(vectors) if isinstance(vectors, list) else "non-list"
        return False, f"GOLDEN_VECTOR_COUNT_ERROR: expected 32 golden vectors, got {got_len}."

    a_batch = array("f")
    b_batch = array("f")
    expected_outs: List[float] = []
    expected_healed_per_vec: List[int] = []

    try:
        for i, vec in enumerate(vectors):
            a_val = decode_f32_hex(vec["a_hex"])
            b_val = decode_f32_hex(vec["b_hex"])
            exp_out_hex = vec["out_hex"]
            exp_healed = int(vec["healed"])

            actual_out, actual_healed = ir.eval_element_f32(a_val, b_val)
            actual_out_hex = encode_f32_hex(actual_out)

            if actual_out_hex != exp_out_hex:
                return (
                    False,
                    f"GOLDEN_VECTOR_MISMATCH at index {i}: ir.eval_element_f32 gave '{actual_out_hex}', lock expects '{exp_out_hex}'.",
                )
            if actual_healed != exp_healed:
                return (
                    False,
                    f"GOLDEN_HEALED_MISMATCH at index {i}: ir.eval_element_f32 healed={actual_healed}, lock expects {exp_healed}.",
                )

            a_batch.append(a_val)
            b_batch.append(b_val)
            expected_outs.append(decode_f32_hex(exp_out_hex))
            expected_healed_per_vec.append(exp_healed)
    except (KeyError, TypeError, ValueError) as exc:
        return False, f"GOLDEN_VECTOR_CORRUPT: {exc}"

    total_expected_healed = sum(expected_healed_per_vec)
    if lock_data.get("total_expected_healed") != total_expected_healed:
        return (
            False,
            f"TOTAL_HEALED_MISMATCH: header says {lock_data.get('total_expected_healed')}, sum is {total_expected_healed}.",
        )

    # 4. Optional native binary verification against a `LoadedKernel`
    if kernel is not None:
        try:
            cand_out, cand_healed = kernel.run_pure(a_batch, b_batch)
        except Exception as exc:
            return False, f"KERNEL_EXECUTION_ERROR: {exc}"

        ok, reason, _ = check_equivalence_pure(
            expected_outs,
            cand_out,
            rtol=1e-5,
            ref_healed=total_expected_healed,
            cand_healed=cand_healed,
        )
        if not ok:
            return False, f"KERNEL_MISMATCH: {reason}"

        if getattr(kernel, "has_tracked", False):
            for i in range(32):
                _, elem_h = kernel.run_pure(array("f", [a_batch[i]]), array("f", [b_batch[i]]))
                if elem_h is not None and elem_h != expected_healed_per_vec[i]:
                    return (
                        False,
                        f"KERNEL_ELEMENT_HEALED_MISMATCH at vector {i}: kernel healed={elem_h}, expected {expected_healed_per_vec[i]}.",
                    )

    kernel_tag = "+LoadedKernel" if kernel is not None else "IR"
    return True, f"VERIFIED_LOCK ({ir.name}, ir_hash={ir.ir_hash}, 32/32 vectors, {kernel_tag})"
