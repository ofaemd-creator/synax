"""Explicit SYNAX tool boundary; model text never automatically executes code."""

from __future__ import annotations
from dataclasses import dataclass
import synax
from synax.lexer import SynaxLexError
from synax.parser import SynaxParseError
from synax.type_system import SynaxTypeError


@dataclass(frozen=True, slots=True)
class CheckResult:
    text: str
    verified: bool


def check_source(source: str) -> CheckResult:
    """Run parser/type checks only; this is not a numerical or intent-equivalence proof."""
    try:
        ir = synax.check_sx(source)
        return CheckResult(
            f"SYNAX sözdizimi ve tip kontrolü geçti: {ir.name}. Sayısal doğrulama çalıştırılmadı.",
            True,
        )
    except (SynaxLexError, SynaxParseError, SynaxTypeError, ValueError) as error:
        return CheckResult(f"SYNAX kontrolü başarısız: {error}", False)
