"""
SYNAX Deterministic Lexer & Source Diagnostics (`src/synax/lexer.py`)
=====================================================================
Tokenizes SYNAX (`.sx`) source text into an immutable stream of `Token`
objects annotated with 1-indexed `SourceSpan` coordinates.

Supports:
  - Structured SYNAX `0.1` / `0.5` keywords, identifiers, types, operators
  - Integer and IEEE-754 floating-point literals (including scientific notation `1e-6`, `3.4e38`)
  - Escaped UTF-8 string literals (`"..."`)
  - Single-line comments (`// ...` and `# ...`), optionally retained for formatting
  - Caret (`^`) source-line diagnostics via `SynaxLexError`
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SourceSpan:
    """1-based inclusive-start, exclusive-end `[col, end_col)` span in `.sx` source."""

    line: int
    col: int
    end_line: int
    end_col: int

    def merge(self, other: "SourceSpan") -> "SourceSpan":
        return SourceSpan(
            line=self.line,
            col=self.col,
            end_line=other.end_line,
            end_col=other.end_col,
        )


class TokenKind(str, Enum):
    # Structural keywords
    SYNAX = "SYNAX"
    KERNEL = "KERNEL"
    INTENT = "INTENT"
    REQUIRE = "REQUIRE"
    SAFETY = "SAFETY"
    LET = "LET"
    RETURN = "RETURN"
    OPTIMIZE = "OPTIMIZE"
    TARGET = "TARGET"
    BOOL = "BOOL"

    # Identifiers & literals
    IDENT = "IDENT"
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"

    # Operators & punctuation
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    CARET = "CARET"
    STARSTAR = "STARSTAR"
    EQ = "EQ"
    EQEQ = "EQEQ"
    ARROW = "ARROW"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LT = "LT"
    GT = "GT"
    COMMA = "COMMA"
    COLON = "COLON"
    SEMI = "SEMI"

    # Trivia & end-of-stream
    COMMENT = "COMMENT"
    EOF = "EOF"


KEYWORDS: Dict[str, TokenKind] = {
    "synax": TokenKind.SYNAX,
    "kernel": TokenKind.KERNEL,
    "intent": TokenKind.INTENT,
    "require": TokenKind.REQUIRE,
    "safety": TokenKind.SAFETY,
    "let": TokenKind.LET,
    "return": TokenKind.RETURN,
    "optimize": TokenKind.OPTIMIZE,
    "target": TokenKind.TARGET,
    "true": TokenKind.BOOL,
    "false": TokenKind.BOOL,
}

SINGLE_CHAR_TOKENS: Dict[str, TokenKind] = {
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.STAR,
    "/": TokenKind.SLASH,
    "^": TokenKind.CARET,
    "=": TokenKind.EQ,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
    "{": TokenKind.LBRACE,
    "}": TokenKind.RBRACE,
    "<": TokenKind.LT,
    ">": TokenKind.GT,
    ",": TokenKind.COMMA,
    ":": TokenKind.COLON,
    ";": TokenKind.SEMI,
}

ESCAPE_MAP: Dict[str, str] = {
    '"': '"',
    "\\": "\\",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "/": "/",
}


def format_caret_diagnostic(
    error_label: str,
    message: str,
    span: Optional[SourceSpan],
    source_line: str = "",
) -> str:
    """Format a compiler diagnostic with line/column coordinates and caret (`^`) underline."""
    if span is None:
        return f"{error_label}: {message}"

    header = f"{error_label} at line {span.line}, col {span.col}: {message}"
    if not source_line:
        return header

    clean_line = source_line.rstrip("\r\n")
    line_prefix = f"  {span.line} | "
    gutter = " " * (len(line_prefix) - 2) + "| "
    caret_offset = max(0, span.col - 1)
    if span.end_line == span.line and span.end_col > span.col:
        width = max(1, span.end_col - span.col)
    else:
        width = 1
    underline = "^" + ("~" * (width - 1))
    pointer_line = f"{gutter}{' ' * caret_offset}{underline}"
    return f"{header}\n{line_prefix}{clean_line}\n{pointer_line}"


class SynaxLexError(SyntaxError):
    """Deterministic lexical error carrying exact `SourceSpan` and caret (`^`) rendering."""

    def __init__(self, message: str, span: SourceSpan, source_line: str = ""):
        self.message = message
        self.span = span
        self.source_line = source_line
        formatted = format_caret_diagnostic("SynaxLexError", message, span, source_line)
        super().__init__(formatted)

    def format_diagnostic(self) -> str:
        return format_caret_diagnostic("SynaxLexError", self.message, self.span, self.source_line)

    def __str__(self) -> str:
        return self.format_diagnostic()


@dataclass(frozen=True)
class Token:
    """Single lexical token with kind, raw source lexeme, and 1-indexed `SourceSpan`."""

    kind: TokenKind
    text: str
    span: SourceSpan

    @property
    def is_number(self) -> bool:
        return self.kind in (TokenKind.INT, TokenKind.FLOAT)

    @property
    def string_value(self) -> str:
        """Return unescaped string contents when `kind == TokenKind.STRING`."""
        if self.kind != TokenKind.STRING or len(self.text) < 2:
            return self.text
        inner = self.text[1:-1]
        out: List[str] = []
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "\\" and i + 1 < len(inner):
                nxt = inner[i + 1]
                out.append(ESCAPE_MAP.get(nxt, nxt))
                i += 2
            else:
                out.append(ch)
                i += 1
        return "".join(out)


class Lexer:
    """Deterministic single-pass character scanner for SYNAX (`.sx`)."""

    def __init__(self, source: str, *, include_comments: bool = False):
        self.source = source
        self.include_comments = include_comments
        self._lines = source.splitlines()
        self._len = len(source)
        self._pos = 0
        self._line = 1
        self._col = 1

    def _source_line(self, line_no: int) -> str:
        if 1 <= line_no <= len(self._lines):
            return self._lines[line_no - 1]
        return ""

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self.source[idx] if idx < self._len else ""

    def _advance(self) -> str:
        ch = self.source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _error(self, message: str, start_line: int, start_col: int, end_line: Optional[int] = None, end_col: Optional[int] = None) -> SynaxLexError:
        span = SourceSpan(
            line=start_line,
            col=start_col,
            end_line=end_line if end_line is not None else self._line,
            end_col=end_col if end_col is not None else max(start_col + 1, self._col),
        )
        return SynaxLexError(message, span, self._source_line(start_line))

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self._pos < self._len:
            ch = self._peek()

            # 1. Whitespace (spaces, tabs, CR, LF)
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            start_pos = self._pos
            start_line = self._line
            start_col = self._col

            # 2. Single-line comments: `// ...` or `# ...`
            if ch == "#" or (ch == "/" and self._peek(1) == "/"):
                while self._pos < self._len and self._peek() not in ("\n", "\r"):
                    self._advance()
                if self.include_comments:
                    span = SourceSpan(start_line, start_col, self._line, self._col)
                    tokens.append(Token(TokenKind.COMMENT, self.source[start_pos:self._pos], span))
                continue

            # 3. String literals: `"..."`
            if ch == '"':
                self._advance()  # consume opening quote
                terminated = False
                while self._pos < self._len:
                    c = self._peek()
                    if c in ("\n", "\r"):
                        raise self._error(
                            "Unterminated string literal before end of line",
                            start_line,
                            start_col,
                            self._line,
                            self._col,
                        )
                    if c == "\\":
                        esc_line, esc_col = self._line, self._col
                        self._advance()  # consume '\'
                        if self._pos >= self._len:
                            raise self._error("Unterminated escape sequence in string literal", start_line, start_col)
                        esc_ch = self._advance()
                        if esc_ch not in ESCAPE_MAP:
                            raise self._error(
                                f"Invalid string escape sequence '\\{esc_ch}'",
                                esc_line,
                                esc_col,
                                self._line,
                                self._col,
                            )
                        continue
                    if c == '"':
                        self._advance()  # consume closing quote
                        terminated = True
                        break
                    self._advance()

                if not terminated:
                    raise self._error("Unterminated string literal at end of file", start_line, start_col)

                span = SourceSpan(start_line, start_col, self._line, self._col)
                tokens.append(Token(TokenKind.STRING, self.source[start_pos:self._pos], span))
                continue

            # 4. Numeric literals: integer (`42`) and float (`3.14`, `1e-6`, `3.4e38`)
            if ch.isdigit():
                is_float = False
                while self._pos < self._len and self._peek().isdigit():
                    self._advance()

                if self._peek() == "." and self._peek(1).isdigit():
                    is_float = True
                    self._advance()  # consume '.'
                    while self._pos < self._len and self._peek().isdigit():
                        self._advance()
                elif self._peek() == ".":
                    # Trailing dot without fractional digits (e.g. `1.`) or `1..2`
                    self._advance()
                    raise self._error(
                        "Invalid floating-point literal: expected digits after '.'",
                        start_line,
                        start_col,
                    )

                if self._peek() in ("e", "E"):
                    is_float = True
                    self._advance()  # consume 'e' / 'E'
                    if self._peek() in ("+", "-"):
                        self._advance()
                    if not self._peek().isdigit():
                        raise self._error(
                            "Invalid scientific notation literal: expected exponent digits",
                            start_line,
                            start_col,
                        )
                    while self._pos < self._len and self._peek().isdigit():
                        self._advance()

                # Reject malformed `1.2.3` or `123abc`
                if self._peek() == ".":
                    self._advance()
                    while self._pos < self._len and self._peek().isdigit():
                        self._advance()
                    raise self._error(
                        "Malformed numeric literal: unexpected second decimal point",
                        start_line,
                        start_col,
                    )
                if self._peek().isalpha() or self._peek() == "_":
                    while self._pos < self._len and (self._peek().isalnum() or self._peek() == "_"):
                        self._advance()
                    raise self._error(
                        f"Invalid suffix on numeric literal '{self.source[start_pos:self._pos]}'",
                        start_line,
                        start_col,
                    )

                span = SourceSpan(start_line, start_col, self._line, self._col)
                kind = TokenKind.FLOAT if is_float else TokenKind.INT
                tokens.append(Token(kind, self.source[start_pos:self._pos], span))
                continue

            # 5. Identifiers & keywords (`[A-Za-z_][A-Za-z0-9_]*` + Unicode letters)
            if ch.isalpha() or ch == "_":
                while self._pos < self._len and (self._peek().isalnum() or self._peek() == "_"):
                    self._advance()
                lexeme = self.source[start_pos:self._pos]
                kind = KEYWORDS.get(lexeme, TokenKind.IDENT)
                span = SourceSpan(start_line, start_col, self._line, self._col)
                tokens.append(Token(kind, lexeme, span))
                continue

            # 6. Multi-character operators: `->`, `==`, `**`
            two = self.source[self._pos:self._pos + 2]
            if two == "->":
                self._advance()
                self._advance()
                tokens.append(Token(TokenKind.ARROW, "->", SourceSpan(start_line, start_col, self._line, self._col)))
                continue
            if two == "==":
                self._advance()
                self._advance()
                tokens.append(Token(TokenKind.EQEQ, "==", SourceSpan(start_line, start_col, self._line, self._col)))
                continue
            if two == "**":
                self._advance()
                self._advance()
                tokens.append(Token(TokenKind.STARSTAR, "**", SourceSpan(start_line, start_col, self._line, self._col)))
                continue

            # 7. Single-character operators & delimiters
            single_kind = SINGLE_CHAR_TOKENS.get(ch)
            if single_kind is not None:
                self._advance()
                tokens.append(Token(single_kind, ch, SourceSpan(start_line, start_col, self._line, self._col)))
                continue

            # 8. Illegal character
            bad_ch = self._advance()
            raise self._error(f"Unexpected character {bad_ch!r}", start_line, start_col)

        eof_span = SourceSpan(self._line, self._col, self._line, self._col)
        tokens.append(Token(TokenKind.EOF, "", eof_span))
        return tokens


def tokenize(source: str, *, include_comments: bool = False) -> List[Token]:
    """Tokenize `.sx` source code deterministically into a list of `Token`s ending with `EOF`."""
    return Lexer(source, include_comments=include_comments).tokenize()
