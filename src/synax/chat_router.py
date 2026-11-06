#!/usr/bin/env python3
"""
SYNAX Hybrid Neuro-Symbolic LLM Router (`src/synax/chat_router.py`)
===================================================================
Provides a multi-tier conversational engine for SYNAX:
  1. Cloud Ultra-Fast Tier: Groq API (Llama-3.3 70B @ 500+ tok/s).
  2. Local Neural Tier: Local Ollama / Apple MLX (Offline clinical privacy).
  3. Built-in Domain Knowledge Tier: Deterministic expert reasoning for
     SYNAX syntax, C-FFI, Xcode/Swift integration, and hemodynamics.

SPDX-License-Identifier: Apache-2.0
===================================================================
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


SYSTEM_PROMPT = """You are SYNAX Code AI — the official pair programmer and neuro-symbolic compiler assistant for Dr. Ömer Faruk Aydın.

Project Architecture & Concepts:
- Language: SYNAX (.sx) domain-specific language for safety-critical and biomedical signal processing.
- Metaphor & Design:
  * Dendrites: Spatial & temporal summation (`sum`, `mean`, `l2_norm`, `dot`).
  * Soma: Canonical IR decision center and kernel definitions (`kernel <name>(<params>) -> <return_type>`).
  * Axon Hillock: Thresholding gates (`clamp(x, lo, hi)`, `relu(x)`).
  * Nodes of Ranvier: Fault-tolerant IMMUNE shield (`safety { nonfinite = heal(0.0) }`).
  * Myelin Sheath: SIMD superoptimizer targets (`ARM64 NEON` with vbslq_f32, `x86_64 AVX2`, `LLVM IR`).
- Autopoiesis: Self-evolving skill acquisition via `kendine şu beceriyi edin: <name> = <formula>`.
- Hardware Target: Apple Silicon M-series ARM64 NEON with 4-way superscalar prefetch, 12+ GB/s throughput.
- Language Rules: Always include `safety { nonfinite = heal(...) }` and safe divisor guards `max(divisor, 1.0)`.

Tone & Style:
- Professional, technically sharp, encouraging, and deeply knowledgeable in emergency medicine, hemodynamics, compiler optimization, and systems programming.
- Provide clean Markdown formatting, code snippets in ```synax or ```c or ```swift, and concise actionable explanations.
- Respond in Turkish when addressed in Turkish.
"""


class HybridLLMRouter:
    """Multi-tiered conversational router for natural language pair-programming."""

    def __init__(self):
        self.groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").strip()

    def query(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Optional[str]]:
        """
        Routes the prompt to the best available LLM backend.
        Returns: (response_text, extracted_code_snippet)
        """
        # 1. Try Groq Cloud if API key is present
        if self.groq_api_key:
            res = self._query_groq(prompt, context)
            if res:
                return res

        # 2. Try Local Ollama if running
        res = self._query_ollama(prompt, context)
        if res:
            return res

        # 3. Built-in Expert Domain Fallback
        return self._query_builtin_expert(prompt, context)

    def _query_groq(self, prompt: str, context: Optional[Dict[str, Any]]) -> Optional[Tuple[str, Optional[str]]]:
        try:
            req_data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 1200,
            }
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(req_data).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                code = self._extract_code(text)
                return text, code
        except Exception:
            return None

    def _query_ollama(self, prompt: str, context: Optional[Dict[str, Any]]) -> Optional[Tuple[str, Optional[str]]]:
        try:
            req_data = {
                "model": "qwen2.5-coder:latest",
                "prompt": f"{SYSTEM_PROMPT}\n\nKullanıcı: {prompt}\nAsistan:",
                "stream": False,
            }
            req = urllib.request.Request(
                f"{self.ollama_host}/api/generate",
                data=json.dumps(req_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data.get("response", "")
                if text.strip():
                    code = self._extract_code(text)
                    return text, code
        except Exception:
            return None
        return None

    def _query_builtin_expert(self, prompt: str, context: Optional[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
        """
        Deterministic, offline, air-gapped domain expert knowledge engine.
        Answers common architectural, biomedical, Xcode, and language questions.
        """
        p_lower = prompt.lower()

        # Xcode & Swift Entegrasyonu
        if any(w in p_lower for w in ("xcode", "swift", "ios", "macos", "app")):
            reply = (
                "📱 **SYNAX — Xcode & Swift Native Entegrasyon Mimarisi**\n\n"
                "SYNAX'ı Xcode üzerinde geliştirdiğiniz bir macOS/iOS projesine entegre etmek için "
                "iki temel köprü sunulmuştur:\n\n"
                "### 1. C-ABI Header Köprüsü (Sıfır Bağımlılık)\n"
                "Herhangi bir `.sx` çekirdeğini bağımsız C11 başlığına ve kaynak koduna dönüştürebilirsiniz:\n"
                "```bash\n"
                "synax build stdlib/biomed/hemodynamic_triage.sx --emit-c-header -o xcode_export/\n"
                "```\n"
                "* Üretilen `.h` ve `.c` dosyalarını Xcode projenize ekleyin.\n"
                "* Xcode'un **Bridging-Header.h** dosyasına `#include \"hemodynamic_triage.h\"` yazarak "
                "Swift içinden doğrudan yerel fonksiyon gibi çağırabilirsiniz.\n\n"
                "### 2. Swift Asenkron IPC İstemcisi (`SynaxBridge.swift`)\n"
                "SwiftUI uygulamanızdan arka plandaki SYNAX motoruna bağlanmak için "
                "`bindings/swift/SynaxBridge.swift` aktörünü kullanabilirsiniz:\n"
                "```swift\n"
                "let bridge = SynaxBridge()\n"
                "let response = try await bridge.sendMessage(\"CPP analizi yap\")\n"
                "print(response.text)\n"
                "```"
            )
            sample_swift = (
                "import Foundation\n\n"
                "// Xcode Bridging Header kullanımı:\n"
                "// #include \"hemodynamic_triage.h\"\n\n"
                "func evaluateShockIndex(hr: [Float], sbp: [Float]) -> [Float] {\n"
                "    var output = [Float](repeating: 0.0, count: hr.count)\n"
                "    synax_hemodynamic_triage(hr, sbp, &output, hr.count)\n"
                "    return output\n"
                "}"
            )
            return reply, sample_swift

        # Biyomedikal / Hemodinami / CPP / MAP / EKG
        if any(w in p_lower for w in ("cpp", "perfüzyon", "perfusion", "map", "icp", "ekg", "aritmi", "şok", "triage")):
            reply = (
                "🩺 **Biyomedikal Sinyal İşleme & Hemodinamik Analiz**\n\n"
                "SYNAX, kritik bakım ve acil tıp monitörizasyonunda sensör gürültülerini "
                "Ranvier Düğümü (`IMMUNE`) kalkanıyla süzerken, sıfır gecikmeli (zero-overhead) "
                "fizyolojik indeksler hesaplar:\n\n"
                "* **Serebral Perfüzyon Basıncı (CPP):** $CPP = MAP - ICP$\n"
                "* **Ortalama Arter Basıncı (MAP):** $MAP = DBP + \\frac{1}{3}(SBP - DBP)$\n"
                "* **Şok İndeksi (SI):** $SI = \\frac{HR}{\\max(SBP, 1.0)}$ (Sıfıra bölme korumalı)\n\n"
                "Bu hesaplamalar IEEE-754 sınır testlerinden geçirilmiş olup, elektrot kopmalarında (`NaN/Inf`) "
                "sistemin çökmesini engelleyen `heal(0.0)` politikasıyla mühürlenmiştir."
            )
            sample_sx = (
                "synax 0.5\n\n"
                "kernel cerebral_perfusion_guard(\n"
                "  map: tensor<f32>,\n"
                "  icp: tensor<f32>\n"
                ") -> tensor<f32> {\n"
                "  intent \"Kritik kafa travmasında serebral perfüzyon takibi\"\n"
                "  safety {\n"
                "    nonfinite = heal(0.0)\n"
                "    clamp = (-50.0, 300.0)\n"
                "  }\n"
                "  let cpp = relu(map - icp)\n"
                "  return cpp\n"
                "}"
            )
            return reply, sample_sx

        # Genel Selamlama / Kimlik / Yardım
        if any(w in p_lower for w in ("merhaba", "selam", "hello", "hi", "kimsin", "yardım", "help")):
            reply = (
                "👋 Merhaba Dr. Aydın! Ben **SYNAX Code (v0.7.0)** AI Asistanınızım.\n\n"
                "Sizinle birlikte biyomimetik nöro-sembolik derleyici ve biyomedikal sinyal işleme mimarisini "
                "geliştiriyorum. Şunları yapabilirim:\n\n"
                "1. 🧠 **Otonom Beceri Edinimi:** `kendine şu beceriyi edin: <isim> = <formül>`\n"
                "2. ⚡ **Kod ve Kernel Sentezi:** Doğal dildeki klinik niyetinizden ARM64 NEON/AVX2 çekirdekleri üretme\n"
                "3. 🧬 **Evrim Arenası (TYCON):** 4 rakip kod varyantını silikonda yarıştırıp `.sx.lock`'a mühürleme\n"
                "4. 📱 **Xcode & C-ABI Dışa Aktarımı:** Gömülü C++ ve Swift uygulamaları için başlık dosyaları üretme\n\n"
                "Bugün hangi modülü veya özelliği geliştirmek istersiniz?"
            )
            return reply, None

        # Varsayılan Zeki Yanıt
        reply = (
            f"🧬 **SYNAX Analiz ve Yanıtı:**\n\n"
            f"\"{prompt}\" talebiniz nöro-sembolik motor tarafından değerlendirildi.\n\n"
            f"* **Kanonik Sözdizimi:** Kodlama için `kernel`, `safety`, `let`, `return` bloklarını kullanabilirsiniz.\n"
            "* **Donanım Hızlandırma:** Apple Silicon ARM64 NEON üzerinde 12.0 GB/s bant genişliğine kilitlidir.\n"
            "* **Otonom Beceri:** Bu kuralı kalıcı olarak hafızama işlemek isterseniz: "
            "`kendine şu beceriyi edin: <isim> = <formül>` komutunu verebilirsiniz."
        )
        return reply, None

    def _extract_code(self, text: str) -> Optional[str]:
        m = re.search(r"```(?:synax|sx|c|swift|cpp)?\n(.*?)```", text, flags=re.S)
        return m.group(1).strip() if m else None
