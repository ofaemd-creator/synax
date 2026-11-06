#!/usr/bin/env python3
"""
SYNAX Neuro-Symbolic Multi-Variant Synthesizer (`src/synax/evolution/synthesizer.py`)
===================================================================================
Generates 4 diverse, competing candidate algorithms from clinical / mission intent:
  - Variant A: Baseline Safe (Strict boundary clamp & safe divisor)
  - Variant B: Algebraic Fused (Branchless arithmetic, fused operators)
  - Variant C: Dendritic Vectorized (Parallel reduction & accumulator friendly)
  - Variant D: Ranvier Saltatory (Adaptive impulse noise rejection)

Supports:
  1. Groq Cloud API (500+ tok/s real-time streaming)
  2. Local Ollama / MLX endpoint (offline air-gapped clinical operation)
  3. Built-in Deterministic Neuro-Symbolic Heuristic Synthesizer (Zero-latency fallback)

SPDX-License-Identifier: Apache-2.0
===================================================================================
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from .memory import EpisodicEvolutionMemory


class KernelCandidate:
    """Represents a generated algorithm candidate in the evolution arena."""

    def __init__(self, variant_id: str, label: str, code: str, hypothesis: str):
        self.variant_id = variant_id
        self.label = label
        self.code = code.strip()
        self.hypothesis = hypothesis
        self.immune_passed: bool = False
        self.immune_reason: str = "Not evaluated"
        self.throughput_gbs: float = 0.0
        self.latency_us: float = 0.0
        self.speedup_vs_baseline: float = 1.0

    @property
    def id(self) -> str:
        return self.variant_id

    @property
    def name(self) -> str:
        return self.label

    @property
    def description(self) -> str:
        return self.hypothesis


class SynthesisResult:
    """Represents the output of full neuro-symbolic intent synthesis."""

    def __init__(self, best_code: str, winner_id: str, candidates: List[KernelCandidate]):
        self.best_code = best_code
        self.winner_id = winner_id
        self.candidates = candidates


class NeuroSymbolicSynthesizer:
    """Autonomous generator of safe, verified candidate kernels from intent."""

    def __init__(self, memory: Optional[EpisodicEvolutionMemory] = None):
        self.memory = memory or EpisodicEvolutionMemory()

    def synthesize_from_intent(self, intent: str, kernel_name: Optional[str] = None) -> SynthesisResult:
        """Derive kernel name, parameters, and 4 verified variants from clinical intent."""
        intent_lower = intent.lower()
        if not kernel_name:
            if any(k in intent_lower for k in ("cpp", "perfuzyon", "perfusion", "intrakraniyal")):
                k_name = "cerebral_perfusion_pressure"
                params = ["map", "icp"]
            elif any(k in intent_lower for k in ("shock", "triage", "triyaj", "si")):
                k_name = "shock_index_triage"
                params = ["hr", "sbp"]
            elif any(k in intent_lower for k in ("map", "arterial", "basinc")):
                k_name = "mean_arterial_pressure"
                params = ["sbp", "dbp"]
            else:
                words = re.findall(r"[a-z0-9_]+", intent_lower)
                k_name = "_".join(words[:3]) if words else "synthesized_kernel"
                params = ["a", "b"]
        else:
            k_name = kernel_name
            params = ["a", "b"]

        candidates = self.synthesize_variants(k_name, intent, params)
        # Choose candidate that uses relu if intent mentions pozitif / difference, else variant B/A
        best_cand = candidates[0]
        for c in candidates:
            if "pozitif" in intent_lower and "relu" in c.code:
                best_cand = c
                break

        return SynthesisResult(
            best_code=best_cand.code,
            winner_id=best_cand.variant_id,
            candidates=candidates,
        )

    def synthesize_variants(
        self,
        kernel_name: str,
        intent: str,
        param_names: List[str],
        return_type: str = "tensor<f32>",
    ) -> List[KernelCandidate]:
        """Generate 4 competing kernel candidates for the given intent."""
        # 1. Attempt Groq API if key is present
        groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        if groq_key:
            try:
                candidates = self._generate_via_groq(kernel_name, intent, param_names, groq_key)
                if candidates and len(candidates) >= 2:
                    return candidates
            except Exception:
                pass

        # 2. Attempt Local Ollama if available
        ollama_url = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
        try:
            candidates = self._generate_via_ollama(kernel_name, intent, param_names, ollama_url)
            if candidates and len(candidates) >= 2:
                return candidates
        except Exception:
            pass

        # 3. Built-in Neuro-Symbolic Genetic Rule Synthesizer (Instant & 100% Offline)
        return self._generate_builtin_variants(kernel_name, intent, param_names, return_type)

    def self_correct(
        self,
        candidate: KernelCandidate,
        immune_error_feedback: str,
    ) -> KernelCandidate:
        """Heal a candidate that hit the IMMUNE verification wall."""
        code = candidate.code
        # Inject divisor protection if division by zero or NaN error occurred
        if "divisor" in immune_error_feedback.lower() or "nan" in immune_error_feedback.lower() or "inf" in immune_error_feedback.lower():
            # Ensure safety block has heal(0.0)
            if "safety" not in code:
                code = re.sub(
                    r"(kernel\s+[A-Za-z0-9_]+\s*\([^)]*\)\s*(?:->\s*[^{]+)?\{)",
                    r"\1\n    safety {\n        nonfinite = heal(0.0)\n    }",
                    code,
                )
            elif "nonfinite" not in code:
                code = re.sub(
                    r"safety\s*\{",
                    "safety {\n        nonfinite = heal(0.0)",
                    code,
                )
            # Replace raw division `/ b` with `/ max(b, 1.0)`
            code = re.sub(r"/\s*([a-zA-Z0-9_]+)", r"/ max(\1, 1.0)", code)

        return KernelCandidate(
            variant_id=f"{candidate.variant_id}_repaired",
            label=f"{candidate.label} (Self-Corrected)",
            code=code,
            hypothesis=f"Repaired based on IMMUNE feedback: {immune_error_feedback[:60]}...",
        )

    # ─────────────────────────────────────────────────────────────────
    # Built-in Heuristic & Genetic Rule Generator (Zero Latency)
    # ─────────────────────────────────────────────────────────────────
    def _generate_builtin_variants(
        self,
        kernel_name: str,
        intent: str,
        param_names: List[str],
        return_type: str,
    ) -> List[KernelCandidate]:
        p0 = param_names[0] if len(param_names) > 0 else "a"
        p1 = param_names[1] if len(param_names) > 1 else "b"
        params_decl = ", ".join(f"{p}: tensor<f32>" for p in param_names[:2])

        low = intent.lower()

        # Parse math expression pattern from intent
        if "şok" in low or "shock" in low:
            # HR / SBP
            base_expr = f"{p0} / max({p1}, 1.0)"
            clamp_lo, clamp_hi = 0.0, 10.0
        elif "map" in low or "ortalama arter" in low:
            # DBP + (SBP - DBP) / 3
            base_expr = f"{p1} + (({p0} - {p1}) / 3.0)"
            clamp_lo, clamp_hi = 0.0, 300.0
        elif "perfüzyon" in low or "perfusion" in low or "cpp" in low:
            # MAP - ICP
            base_expr = f"relu({p0} - {p1})"
            clamp_lo, clamp_hi = 0.0, 200.0
        elif "qrs" in low or "ekg" in low or "ecg" in low:
            base_expr = f"relu({p0} - {p1})"
            clamp_lo, clamp_hi = -10.0, 10.0
        elif "fark" in low or "diff" in low:
            base_expr = f"{p0} - {p1}"
            clamp_lo, clamp_hi = -500.0, 500.0
        else:
            base_expr = f"({p0} + {p1}) * 0.5"
            clamp_lo, clamp_hi = -1000.0, 1000.0

        # Variant A: Standard Safe Baseline
        code_a = f"""synax 0.5
kernel {kernel_name}({params_decl}) -> {return_type} {{
    intent "{intent}"
    safety {{
        nonfinite = heal(0.0)
        range_check = clamp({clamp_lo}, {clamp_hi})
    }}
    let result = {base_expr}
    return result
}}
"""
        cand_a = KernelCandidate(
            "var_a_baseline_safe",
            "Varyant A: Konservatif Eşik Korumalı",
            code_a,
            "Standart fizyolojik sınırlar ve register-level IMMUNE şifası ile güvenli taban hattı.",
        )

        # Variant B: Fused Branchless (ReLU / Clamped SIMD direct)
        code_b = f"""synax 0.5
kernel {kernel_name}({params_decl}) -> {return_type} {{
    intent "{intent} [Fused Branchless]"
    safety {{
        nonfinite = heal(0.0)
        range_check = clamp({clamp_lo}, {clamp_hi})
        input_bound = abs_max(1000.0)
    }}
    return clamp({base_expr}, {clamp_lo}, {clamp_hi})
}}
"""
        cand_b = KernelCandidate(
            "var_b_fused_branchless",
            "Varyant B: Dallanmasız Doğrudan SIMD Fused",
            code_b,
            "Ara değişken tahsisini kaldırıp doğrudan SIMD doyum (saturation) yazmaçlarına kilitler.",
        )

        # Variant C: Dendritic Pre-Scalable
        code_c = f"""synax 0.5
kernel {kernel_name}({params_decl}) -> {return_type} {{
    intent "{intent} [Dendritic Parallel]"
    safety {{
        nonfinite = heal(0.0)
        range_check = clamp({clamp_lo}, {clamp_hi})
    }}
    let delta = {p0} - {p1}
    let scaled = delta * 0.33333334
    return {p1} + scaled
}}
""" if "map" in low else f"""synax 0.5
kernel {kernel_name}({params_decl}) -> {return_type} {{
    intent "{intent} [Dendritic Balanced]"
    safety {{
        nonfinite = heal(0.0)
        range_check = clamp({clamp_lo}, {clamp_hi})
    }}
    let delta = {base_expr}
    return delta
}}
"""
        cand_c = KernelCandidate(
            "var_c_dendritic_balanced",
            "Varyant C: Süperskalar Dendritik Dengelenmiş",
            code_c,
            "Apple M-serisi 4-kanallı boru hattında bölme yerine çarpma ile bağımsız şeritleri doyurur.",
        )

        # Variant D: Saltatory Ranvier Filtered
        code_d = f"""synax 0.5
kernel {kernel_name}({params_decl}) -> {return_type} {{
    intent "{intent} [Ranvier Saltatory Filter]"
    safety {{
        nonfinite = heal(0.0)
        range_check = clamp({clamp_lo}, {clamp_hi})
        input_bound = abs_max(500.0)
    }}
    let filtered_signal = {base_expr}
    return relu(filtered_signal)
}}
"""
        cand_d = KernelCandidate(
            "var_d_ranvier_saltatory",
            "Varyant D: Ranvier Düğümü Eşik Süzgeci",
            code_d,
            "Yüksek frekanslı sensör artefaktlarını atlama (saltatory) eşiği ile izole eder.",
        )

        return [cand_a, cand_b, cand_c, cand_d]

    def _generate_via_groq(
        self,
        kernel_name: str,
        intent: str,
        param_names: List[str],
        api_key: str,
    ) -> List[KernelCandidate]:
        prompt = self.memory.get_few_shot_prompt(intent)
        prompt += f"\nGenerate a valid SYNAX (.sx) kernel named '{kernel_name}' with parameters {param_names}."
        # Call Groq API via urllib (standard library, zero dependencies)
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a SYNAX compiler neuro-symbolic assistant. Return code in ```synax blocks."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            # Extract code block
            match = re.search(r"```(?:synax|sx|rust)?\n(.*?)```", content, flags=re.S)
            if match:
                code = match.group(1).strip()
                return [KernelCandidate("var_groq_ai", "Groq AI Llama-3.3", code, "Generated via real-time Groq LLM")]
        return []

    def _generate_via_ollama(
        self,
        kernel_name: str,
        intent: str,
        param_names: List[str],
        host: str,
    ) -> List[KernelCandidate]:
        prompt = self.memory.get_few_shot_prompt(intent)
        req = urllib.request.Request(
            f"{host}/api/generate",
            data=json.dumps({
                "model": "qwen2.5-coder:latest",
                "prompt": prompt,
                "stream": False,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data.get("response", "")
            match = re.search(r"```(?:synax|sx|rust)?\n(.*?)```", raw, flags=re.S)
            if match:
                code = match.group(1).strip()
                return [KernelCandidate("var_ollama_local", "Ollama Local Code", code, "Generated via local Ollama coder")]
        return []
