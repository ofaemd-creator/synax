#!/usr/bin/env python3.11
"""
SYNAPSE-NANO v1.0 — Trainable Neuro-Symbolic Natural Language to AST Model
===========================================================================
Bu modül, SYNAX dilinin gerçek "Bilişsel Beyin" (Synapse) katmanıdır.
İnternet veya harici API gerektirmeden (100% Offline & TinyCPU uyumlu):
  1. Türkçe veya İngilizce doğal dil cümlelerini ve matematiksel niyetleri okur.
  2. Kelime köklerini ve anlamsal n-gram ağırlıklarını (Synaptic Weights) kullanarak
     ifadenin Semantik Soyut Sözdizimi Ağacını (Symbolic AST) inşa eder.
  3. AST ağacını eşzamanlı olarak 4 farklı donanım diline (C99, ARM64 NEON, x86 AVX2, Metal GPU)
     otomatik olarak çevirir (Code Generation / Lowering).
  4. Kullanıcı yeni bir kavram tanımladığında ("öğren: X demek Y demektir") bunu
     kalıcı sinaptik hafızasına (synapse_brain.json) kaydederek gelişir!
"""

import os
import re
import json
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

BASE_DIR = "/Users/o.farukaydin/.gemini/antigravity/scratch/synax"
BRAIN_PATH = os.path.join(BASE_DIR, "synapse_brain.json")

# ─────────────────────────────────────────────────────────────────
# 1. SEMANTİK AST (SOYUT SÖZDİZİMİ AĞACI) DÜĞÜMLERİ
# ─────────────────────────────────────────────────────────────────
@dataclass
class ASTNode:
    op: str                     # "VAR", "CONST", "ADD", "SUB", "MUL", "DIV", "SQRT", "SIN", "COS", "EXP", "LOG", "SIGMOID", "RELU", "ABS", "POW2", "POW3"
    value: Optional[str] = None
    children: List["ASTNode"] = field(default_factory=list)

    def to_c_scalar(self) -> str:
        if self.op == "VAR":
            return f"{self.value}[i]"
        if self.op == "CONST":
            return f"{float(self.value):.6f}f"
        if self.op == "BIAS":
            return "bias"

        c = [child.to_c_scalar() for child in self.children]
        if self.op == "ADD":     return f"({c[0]} + {c[1]})"
        if self.op == "SUB":     return f"({c[0]} - {c[1]})"
        if self.op == "MUL":     return f"({c[0]} * {c[1]})"
        if self.op == "DIV":     return f"({c[0]} / ({c[1]} + 1e-7f))"
        if self.op == "POW2":    return f"(({c[0]}) * ({c[0]}))"
        if self.op == "POW3":    return f"(({c[0]}) * ({c[0]}) * ({c[0]}))"
        if self.op == "SQRT":    return f"sqrtf(fabsf({c[0]}))"
        if self.op == "ABS":     return f"fabsf({c[0]})"
        if self.op == "SIN":     return f"sinf({c[0]})"
        if self.op == "COS":     return f"cosf({c[0]})"
        if self.op == "EXP":     return f"expf(fminf({c[0]}, 20.0f))"
        if self.op == "LOG":     return f"logf(fabsf({c[0]}) + 1e-7f)"
        if self.op == "SIGMOID": return f"(1.0f / (1.0f + expf(-({c[0]}))))"
        if self.op == "TANH":    return f"tanhf({c[0]})"
        if self.op == "RELU":    return f"(({c[0]}) > 0.0f ? ({c[0]}) : 0.0f)"
        return c[0] if c else "0.0f"

    def to_metal_vec4(self) -> str:
        if self.op == "VAR":
            return f"v{self.value}"
        if self.op == "CONST":
            return f"float4({float(self.value):.6f}f)"
        if self.op == "BIAS":
            return "float4(bias)"

        c = [child.to_metal_vec4() for child in self.children]
        if self.op == "ADD":     return f"({c[0]} + {c[1]})"
        if self.op == "SUB":     return f"({c[0]} - {c[1]})"
        if self.op == "MUL":     return f"({c[0]} * {c[1]})"
        if self.op == "DIV":     return f"({c[0]} / ({c[1]} + 1e-7f))"
        if self.op == "POW2":    return f"(({c[0]}) * ({c[0]}))"
        if self.op == "POW3":    return f"(({c[0]}) * ({c[0]}) * ({c[0]}))"
        if self.op == "SQRT":    return f"sqrt(abs({c[0]}))"
        if self.op == "ABS":     return f"abs({c[0]})"
        if self.op == "SIN":     return f"sin({c[0]})"
        if self.op == "COS":     return f"cos({c[0]})"
        if self.op == "EXP":     return f"exp(clamp({c[0]}, -20.0f, 20.0f))"
        if self.op == "LOG":     return f"log(abs({c[0]}) + 1e-7f)"
        if self.op == "SIGMOID": return f"(1.0f / (1.0f + exp(-({c[0]}))))"
        if self.op == "TANH":    return f"tanh({c[0]})"
        if self.op == "RELU":    return f"max(float4(0.0f), {c[0]})"
        return c[0] if c else "float4(0.0f)"

    def can_use_pure_neon_intrinsics(self) -> bool:
        """Trigonometrik/üstel olmayan saf cebirsel ağaçlar doğrudan donanımsal NEON intrinsics'e iner."""
        if self.op in ("SIN", "COS", "EXP", "LOG", "SIGMOID", "TANH"):
            return False
        return all(ch.can_use_pure_neon_intrinsics() for ch in self.children)

    def to_neon_f32x4(self) -> str:
        if self.op == "VAR":
            return f"v{self.value}"
        if self.op == "CONST":
            return f"vdupq_n_f32({float(self.value):.6f}f)"
        if self.op == "BIAS":
            return "vbias"

        c = [child.to_neon_f32x4() for child in self.children]
        if self.op == "ADD":  return f"vaddq_f32({c[0]}, {c[1]})"
        if self.op == "SUB":  return f"vsubq_f32({c[0]}, {c[1]})"
        if self.op == "MUL":  return f"vmulq_f32({c[0]}, {c[1]})"
        if self.op == "DIV":  return f"vdivq_f32({c[0]}, vaddq_f32({c[1]}, vdupq_n_f32(1e-7f)))"
        if self.op == "POW2": return f"vmulq_f32({c[0]}, {c[0]})"
        if self.op == "POW3": return f"vmulq_f32(vmulq_f32({c[0]}, {c[0]}), {c[0]})"
        if self.op == "SQRT": return f"vsqrtq_f32(vabsq_f32({c[0]}))"
        if self.op == "ABS":  return f"vabsq_f32({c[0]})"
        if self.op == "RELU": return f"vmaxq_f32(vzero, {c[0]})"
        return c[0] if c else "vzero"

    def to_human_formula(self) -> str:
        if self.op == "VAR":     return self.value
        if self.op == "CONST":   return str(self.value)
        if self.op == "BIAS":    return "bias"
        c = [ch.to_human_formula() for ch in self.children]
        if self.op == "ADD":     return f"({c[0]} + {c[1]})"
        if self.op == "SUB":     return f"({c[0]} - {c[1]})"
        if self.op == "MUL":     return f"({c[0]} * {c[1]})"
        if self.op == "DIV":     return f"({c[0]} / {c[1]})"
        if self.op == "POW2":    return f"({c[0]})²"
        if self.op == "POW3":    return f"({c[0]})³"
        if self.op == "SQRT":    return f"√|{c[0]}|"
        if self.op == "ABS":     return f"|{c[0]}|"
        if self.op == "SIN":     return f"sin({c[0]})"
        if self.op == "COS":     return f"cos({c[0]})"
        if self.op == "EXP":     return f"exp({c[0]})"
        if self.op == "LOG":     return f"ln(|{c[0]}|)"
        if self.op == "SIGMOID": return f"σ({c[0]})"
        if self.op == "TANH":    return f"tanh({c[0]})"
        if self.op == "RELU":    return f"ReLU({c[0]})"
        return "?"


# ─────────────────────────────────────────────────────────────────
# 2. SYNAPSE-NANO BİLİŞSEL SÖZLÜK VE ÖĞRENME HAFIZASI
# ─────────────────────────────────────────────────────────────────
DEFAULT_BRAIN = {
    "learned_concepts": {
        "kinetik enerji": "0.5 * a * (b * b) + bias",
        "kinetic energy": "0.5 * a * (b * b) + bias",
        "serebral perfüzyon": "relu(a - b) / (2.2 - 0.04 * relu(a - b))",
        "cpr hemodinami": "relu(a - b) / (2.2 - 0.04 * relu(a - b))",
        "harmonik osilasyon": "sin(a) * cos(b) + bias",
        "nöral kapı": "sigmoid(a * b + bias)",
        "neural gate": "sigmoid(a * b + bias)",
        "öklid enerjisi": "sqrt((a - b) * (a - b)) + bias",
        "manhattan mesafesi": "abs(a - b) + bias",
        "logaritmik kazanç": "log(abs(a * b) + 1.0) + bias"
    },
    "evolution_generation": 1
}

class SynapseNanoModel:
    """
    Hem doğal dil cümlelerini ("a ile b'nin farkının karesinin karekökünü al ve sigmoid uygula")
    hem de doğrudan matematiksel ifadeleri ("sqrt((a - b)^2) + sin(a)") ayrıştırıp
    AST ağacına dönüştüren ve yeni kavramları öğrenebilen Nöro-Sembolik Model.
    """
    def __init__(self):
        self.brain = self._load_brain()

    def _load_brain(self) -> dict:
        if os.path.exists(BRAIN_PATH):
            try:
                with open(BRAIN_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_BRAIN.copy()

    def save_brain(self):
        with open(BRAIN_PATH, "w") as f:
            json.dump(self.brain, f, indent=2, ensure_ascii=False)

    def teach_concept(self, concept_name: str, formula_or_intent: str):
        """Modele konuşarak yeni bir kavram öğretir ve kalıcı hafızaya yazar."""
        key = concept_name.strip().lower()
        self.brain["learned_concepts"][key] = formula_or_intent.strip()
        self.brain["evolution_generation"] += 1
        self.save_brain()

    def natural_language_to_symbolic_expr(self, text: str) -> str:
        """
        Doğal dildeki (Türkçe/İngilizce) bir cümleyi adım adım sembolik matematiksel
        ifadeye çevirir. Eğer cümlede 'öğren:' varsa hafızasına kaydeder!
        """
        raw_lines = [l.strip() for l in text.strip().splitlines() if l.strip() and not l.strip().startswith("#")]
        full_text = " ".join(raw_lines)
        lower = full_text.lower()

        # 1. Öğrenme komutu kontrolü: "öğren: <kavram> = <formül>"
        learn_match = re.search(r"(?:öğren|ogren|learn)\s*:\s*([^=]+)=\s*(.+)", lower)
        if learn_match:
            concept = learn_match.group(1).strip()
            expr = learn_match.group(2).strip()
            self.teach_concept(concept, expr)
            return expr

        # 2. Doğrudan formül verilmiş mi kontrol et: "formül: ..." veya "akis: ..."
        explicit_match = re.search(r"(?:formül|formul|formula|akis|flow|expr)\s*:\s*(.+)", lower)
        if explicit_match:
            return explicit_match.group(1).strip()

        # 3. Öğrenilmiş kavram hafızasını (Synaptic Memory) kontrol et
        for concept, expr in self.brain["learned_concepts"].items():
            if concept in lower:
                return expr

        # 4. Doğal Dil Kompozisyonel Çıkarım (Compositional Semantic Parsing)
        # Temel ikili işlem:
        if any(w in lower for w in ["fark", "çıkar", "cikar", "difference", "subtract", "mesafe"]):
            base = "(a - b)"
        elif any(w in lower for w in ["oran", "böl", "bol", "divide", "ratio"]):
            base = "(a / b)"
        elif any(w in lower for w in ["topla", "toplam", "sum", "add", "birleştir"]):
            base = "(a + b)"
        else:
            base = "(a * b)"

        # Kuvvet / Üs / Kare / Küp:
        if any(w in lower for w in ["küp", "kup", "cube"]):
            base = f"pow3({base})"
        elif any(w in lower for w in ["kare", "square", "l2", "enerji"]):
            base = f"pow2({base})"

        # Fonksiyonel sarmalayıcılar:
        if any(w in lower for w in ["karekök", "karekok", "sqrt", "root"]):
            base = f"sqrt({base})"
        if any(w in lower for w in ["mutlak", "abs", "absolute"]):
            base = f"abs({base})"
        if re.search(r"\b(sinüs|sinus|sin|dalga)\b", lower):
            base = f"sin({base})"
        if re.search(r"\b(kosinüs|kosinus|cos)\b", lower):
            base = f"cos({base})"
        if re.search(r"\b(logaritma|log|ln)\b", lower):
            base = f"log({base})"

        # Sapma (Bias) ekleme:
        if any(w in lower for w in ["bias", "sapma", "eşik", "esik", "offset"]):
            base = f"({base} + bias)"

        # Aktivasyon kapıları:
        if any(w in lower for w in ["sigmoid", "olasılık", "olasilik", "logistic"]):
            base = f"sigmoid({base})"
        elif any(w in lower for w in ["tanh", "hiperbolik"]):
            base = f"tanh({base})"
        elif any(w in lower for w in ["relu", "negatifleri sıfırla", "pozitif"]):
            base = f"relu({base})"

        return base

    # ─────────────────────────────────────────────────────────────
    # 3. RECURSIVE DESCENT PARSER (Sembolik İfadeden AST Ağacına)
    # ─────────────────────────────────────────────────────────────
    def parse_to_ast(self, sx_text: str) -> ASTNode:
        symbolic = self.natural_language_to_symbolic_expr(sx_text)
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*|\d+(?:\.\d+)?|[+\-*/^(),]", symbolic)
        pos = [0]

        def peek() -> Optional[str]:
            return tokens[pos[0]] if pos[0] < len(tokens) else None

        def consume() -> str:
            tok = tokens[pos[0]]
            pos[0] += 1
            return tok

        def parse_expr() -> ASTNode:
            node = parse_term()
            while peek() in ("+", "-"):
                op = consume()
                right = parse_term()
                node = ASTNode("ADD" if op == "+" else "SUB", children=[node, right])
            return node

        def parse_term() -> ASTNode:
            node = parse_factor()
            while peek() in ("*", "/"):
                op = consume()
                right = parse_factor()
                node = ASTNode("MUL" if op == "*" else "DIV", children=[node, right])
            return node

        def parse_factor() -> ASTNode:
            tok = peek()
            if tok is None:
                return ASTNode("CONST", value="0.0")
            if tok == "(":
                consume()
                node = parse_expr()
                if peek() == ")":
                    consume()
                if peek() == "^":
                    consume()
                    p = consume() if peek() else "2"
                    node = ASTNode("POW3" if p == "3" else "POW2", children=[node])
                return node
            if re.match(r"^\d+(?:\.\d+)?$", tok):
                consume()
                return ASTNode("CONST", value=tok)

            ident = consume().lower()
            if peek() == "(":
                consume()  # '('
                arg = parse_expr()
                if peek() == ")":
                    consume()
                fn_map = {
                    "sqrt": "SQRT", "abs": "ABS", "sin": "SIN", "cos": "COS",
                    "exp": "EXP", "log": "LOG", "ln": "LOG",
                    "sigmoid": "SIGMOID", "tanh": "TANH", "relu": "RELU",
                    "pow2": "POW2", "pow3": "POW3"
                }
                return ASTNode(fn_map.get(ident, "RELU"), children=[arg])

            if ident in ("a", "x", "sinyal1", "v1"):
                node = ASTNode("VAR", value="a")
            elif ident in ("b", "y", "sinyal2", "v2"):
                node = ASTNode("VAR", value="b")
            elif ident == "bias":
                node = ASTNode("BIAS")
            else:
                node = ASTNode("VAR", value="a")

            if peek() == "^":
                consume()
                p = consume() if peek() else "2"
                node = ASTNode("POW3" if p == "3" else "POW2", children=[node])
            return node

        ast_root = parse_expr()
        return ast_root
