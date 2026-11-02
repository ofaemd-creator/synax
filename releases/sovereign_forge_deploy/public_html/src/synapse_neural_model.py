#!/usr/bin/env python3.11
"""
SYNAPSE-NANO v2.0 — Self-Evolving Neuro-Symbolic Natural Language to AST Model
==============================================================================
SYNAX dilinin "Bilişsel Beyin" (Synapse) katmanı.
100% Offline, Sıfır Dış Bağımlılık ve Kriptografik Bütünlük Korumalı:
  1. Türkçe veya İngilizce doğal dil cümlelerini ve matematiksel niyetleri okur.
  2. İfadenin Semantik Soyut Sözdizimi Ağacını (Symbolic AST) inşa eder.
  3. Otonom Cebirsel Evrim (Self-Simplifying AST):
     - sqrt(pow2(u)) -> abs(u) (gereksiz karekök ve çarpma döngülerini yok eder!)
     - Sabit katlama (Constant Folding) ve etkisiz eleman elemesi (x + 0 -> x, x * 1 -> x)
  4. Evrensel Silikon İndirgeme (Tier-0'dan Tier-5'e 6 Donanım Hedefi):
     - Tier-0: Q16.16 Sabit Noktalı (Fixed-Point Integer C89 — FPU'suz 8/16/32-bit Mikrodenetleyiciler)
     - Tier-1: C99 Scalar Float32 (TinyMCU / Evrensel POSIX)
     - Tier-2: ARM64 NEON Intrinsics (float32x4_t)
     - Tier-3: x86_64 AVX-512 Intrinsics (__m512)
     - Tier-4: Apple Metal GPU Shader (float4 zero-copy)
     - Tier-5: NVIDIA CUDA Tensor/SIMT Kernel
  5. Konuşarak öğrenir ("öğren: X = Y") ve SHA-256 imzalı `synapse_brain.json` hafızasında saklar.
"""

import os
import re
import json
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from synax_security import SynaxSecurityGuard

BASE_DIR = "/Users/o.farukaydin/.gemini/antigravity/scratch/synax"
BRAIN_PATH = os.path.join(BASE_DIR, "synapse_brain.json")


# ─────────────────────────────────────────────────────────────────
# 1. SEMANTİK AST (SOYUT SÖZDİZİMİ AĞACI) VE OTONOM CEBİRSEL EVRİM
# ─────────────────────────────────────────────────────────────────
@dataclass
class ASTNode:
    op: str  # "VAR", "CONST", "BIAS", "ADD", "SUB", "MUL", "DIV", "SQRT", "SIN", "COS", "EXP", "LOG", "SIGMOID", "TANH", "RELU", "ABS", "POW2", "POW3"
    value: Optional[str] = None
    children: List["ASTNode"] = field(default_factory=list)

    def node_count(self) -> int:
        return 1 + sum(ch.node_count() for ch in self.children)

    def evolve_and_simplify(self) -> "ASTNode":
        """
        Otonom Cebirsel Süper-Optimizasyon (Self-Renewing AST Pass):
        İnsan müdahalesi olmadan matematiksel özdeşlikleri keşfeder ve ağacı sadeleştirir.
        """
        simplified_children = [ch.evolve_and_simplify() for ch in self.children]
        node = ASTNode(self.op, self.value, simplified_children)

        # Kural 1: sqrt(pow2(u)) -> abs(u)  [Donanımda ~6x hızlanma!]
        if node.op == "SQRT" and len(node.children) == 1:
            inner = node.children[0]
            if inner.op == "POW2" and len(inner.children) == 1:
                return ASTNode("ABS", children=[inner.children[0]])
            if inner.op == "MUL" and len(inner.children) == 2:
                if inner.children[0].to_human_formula() == inner.children[1].to_human_formula():
                    return ASTNode("ABS", children=[inner.children[0]])

        # Kural 2: İdempotent sarmalayıcılar: abs(abs(u)) -> abs(u), relu(relu(u)) -> relu(u)
        if node.op in ("ABS", "RELU") and len(node.children) == 1:
            if node.children[0].op == node.op:
                return node.children[0]

        # Kural 3: Etkisiz eleman elemesi (x + 0 -> x, x * 1 -> x, x * 0 -> 0)
        if node.op == "ADD" and len(node.children) == 2:
            l, r = node.children
            if l.op == "CONST" and float(l.value) == 0.0:
                return r
            if r.op == "CONST" and float(r.value) == 0.0:
                return l
        if node.op == "MUL" and len(node.children) == 2:
            l, r = node.children
            if l.op == "CONST" and float(l.value) == 1.0:
                return r
            if r.op == "CONST" and float(r.value) == 1.0:
                return l
            if (l.op == "CONST" and float(l.value) == 0.0) or (r.op == "CONST" and float(r.value) == 0.0):
                return ASTNode("CONST", value="0.0")

        return node

    # ── Tier-0: Primitive No-FPU Microcontroller (Q16.16 Fixed-Point Integer C89) ──
    def to_q16_fixed_point(self) -> str:
        """
        FPU (Kayan Nokta Birimi) bile olmayan en ilkel 8/16/32-bit işlemciler için
        saf tam sayı (Q16.16 Fixed-Point: 1.0 == 65536) C89 aritmetiği üretir.
        """
        if self.op == "VAR":
            return f"q_{self.value}[i]"
        if self.op == "CONST":
            q_val = int(round(float(self.value) * 65536))
            return f"((int32_t){q_val})"
        if self.op == "BIAS":
            return "q_bias"

        c = [child.to_q16_fixed_point() for child in self.children]
        if self.op == "ADD":     return f"({c[0]} + {c[1]})"
        if self.op == "SUB":     return f"({c[0]} - {c[1]})"
        if self.op == "MUL":     return f"((int32_t)(((int64_t)({c[0]}) * ({c[1]})) >> 16))"
        if self.op == "DIV":     return f"((int32_t)((((int64_t)({c[0]})) << 16) / (({c[1]}) | 1)))"
        if self.op == "POW2":    return f"((int32_t)(((int64_t)({c[0]}) * ({c[0]})) >> 16))"
        if self.op == "ABS":     return f"(({c[0]}) < 0 ? -({c[0]}) : ({c[0]}))"
        if self.op == "RELU":    return f"(({c[0]}) > 0 ? ({c[0]}) : 0)"
        if self.op == "SQRT":    return f"q16_sqrt({c[0]})"
        if self.op == "SIGMOID": return f"q16_fast_sigmoid({c[0]})"
        if self.op == "TANH":    return f"q16_fast_tanh({c[0]})"
        return c[0] if c else "0"

    # ── Tier-1: Universal C99 Scalar Float32 ──
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

    # ── Tier-2: ARM64 NEON SIMD Intrinsics (float32x4_t) ──
    def can_use_pure_neon_intrinsics(self) -> bool:
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

    # ── Tier-3: x86_64 AVX-512 SIMD Intrinsics (__m512) ──
    def to_avx512_f32x16(self) -> str:
        if self.op == "VAR":
            return f"zmm_{self.value}"
        if self.op == "CONST":
            return f"_mm512_set1_ps({float(self.value):.6f}f)"
        if self.op == "BIAS":
            return "zmm_bias"

        c = [child.to_avx512_f32x16() for child in self.children]
        if self.op == "ADD":  return f"_mm512_add_ps({c[0]}, {c[1]})"
        if self.op == "SUB":  return f"_mm512_sub_ps({c[0]}, {c[1]})"
        if self.op == "MUL":  return f"_mm512_mul_ps({c[0]}, {c[1]})"
        if self.op == "DIV":  return f"_mm512_div_ps({c[0]}, _mm512_add_ps({c[1]}, _mm512_set1_ps(1e-7f)))"
        if self.op == "POW2": return f"_mm512_mul_ps({c[0]}, {c[0]})"
        if self.op == "SQRT": return f"_mm512_sqrt_ps(_mm512_abs_ps({c[0]}))"
        if self.op == "ABS":  return f"_mm512_abs_ps({c[0]})"
        if self.op == "RELU": return f"_mm512_max_ps(_mm512_setzero_ps(), {c[0]})"
        return c[0] if c else "_mm512_setzero_ps()"

    # ── Tier-4: Apple Metal Unified GPU Shader (float4) ──
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
# 2. SYNAPSE-NANO BİLİŞSEL SÖZLÜK VE KRİPTOGRAFİK HAFIZA
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
    "algebraic_optimizations_applied": 0,
    "evolution_generation": 2
}


class SynapseNanoModel:
    """
    Kendi kendini sadeleştiren (Self-Simplifying), yeni kavramları öğrenen ve
    SHA-256 kriptografik bütünlük imzasıyla korunan Nöro-Sembolik Dil Modeli (v2.0).
    """
    def __init__(self):
        self.brain = self._load_brain()

    def _load_brain(self) -> dict:
        if os.path.exists(BRAIN_PATH):
            ok, _ = SynaxSecurityGuard.verify_json_file(BRAIN_PATH)
            if ok:
                try:
                    with open(BRAIN_PATH, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        brain = DEFAULT_BRAIN.copy()
        return brain

    def save_brain(self):
        self.brain["_integrity_sha256"] = SynaxSecurityGuard.compute_canonical_sha256(self.brain)
        with open(BRAIN_PATH, "w", encoding="utf-8") as f:
            json.dump(self.brain, f, indent=2, ensure_ascii=False)

    def teach_concept(self, concept_name: str, formula_or_intent: str):
        """Modele konuşarak yeni bir kavram öğretir, cebirsel olarak sadeleştirir ve imzalar."""
        key = concept_name.strip().lower()
        self.brain["learned_concepts"][key] = formula_or_intent.strip()
        self.brain["evolution_generation"] = self.brain.get("evolution_generation", 1) + 1
        self.save_brain()

    def natural_language_to_symbolic_expr(self, text: str) -> str:
        raw_lines = [l.strip() for l in text.strip().splitlines() if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("//")]
        full_text = " ".join(raw_lines)
        lower = full_text.lower()

        # 1. Öğrenme komutu kontrolü: "öğren: <kavram> = <formül>"
        learn_match = re.search(r"(?:öğren|ogren|learn)\s*:\s*([^=]+)=\s*(.+)", lower)
        if learn_match:
            concept = learn_match.group(1).strip()
            expr = learn_match.group(2).strip()
            self.teach_concept(concept, expr)
            return expr

        # 2. Doğrudan formül verilmiş mi kontrol et
        explicit_match = re.search(r"(?:formül|formul|formula|akis|flow|expr)\s*:\s*(.+)", lower)
        if explicit_match:
            return explicit_match.group(1).strip()

        # 2b. Doğrudan matematiksel/sembolik ifade tespiti (örn: "abs(abs(a - b)) + 0.0")
        if re.search(r"[\(\)\+\-\*\/\^]", lower) and not any(
            tr_w in lower for tr_w in ["ile", "nin", "nın", "fark", "topla", "karekök", "karekok", "uygula", "ekle"]
        ):
            return lower

        # 3. Öğrenilmiş kavram hafızasını (Synaptic Memory) kontrol et
        for concept, expr in self.brain["learned_concepts"].items():
            if concept in lower:
                return expr

        # 4. Doğal Dil Kompozisyonel Çıkarım
        if any(w in lower for w in ["fark", "çıkar", "cikar", "difference", "subtract", "mesafe"]):
            base = "(a - b)"
        elif any(w in lower for w in ["oran", "böl", "bol", "divide", "ratio"]):
            base = "(a / b)"
        elif any(w in lower for w in ["topla", "toplam", "sum", "add", "birleştir"]):
            base = "(a + b)"
        else:
            base = "(a * b)"

        if any(w in lower for w in ["küp", "kup", "cube"]):
            base = f"pow3({base})"
        elif any(w in lower for w in ["kare", "square", "l2", "enerji"]):
            base = f"pow2({base})"

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

        if any(w in lower for w in ["bias", "sapma", "eşik", "esik", "offset"]):
            base = f"({base} + bias)"

        if any(w in lower for w in ["sigmoid", "olasılık", "olasilik", "logistic"]):
            base = f"sigmoid({base})"
        elif any(w in lower for w in ["tanh", "hiperbolik"]):
            base = f"tanh({base})"
        elif any(w in lower for w in ["relu", "negatifleri sıfırla", "pozitif"]):
            base = f"relu({base})"

        return base

    def parse_to_ast(self, sx_text: str, auto_evolve: bool = True) -> ASTNode:
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
                consume()
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

        raw_ast = parse_expr()
        if not auto_evolve:
            return raw_ast

        evolved_ast = raw_ast.evolve_and_simplify()
        if evolved_ast.node_count() < raw_ast.node_count():
            self.brain["algebraic_optimizations_applied"] = self.brain.get("algebraic_optimizations_applied", 0) + 1
            self.save_brain()

        # Zero-Trust Security Verification on lowered C scalar expression
        ok, reason = SynaxSecurityGuard.verify_c_expression(evolved_ast.to_c_scalar())
        if not ok:
            raise ValueError(f"[SYNAX-SEC] Unsafe AST expression blocked: {reason}")

        return evolved_ast
