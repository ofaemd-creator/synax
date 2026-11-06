#!/usr/bin/env python3.11
"""
SYNAX Gemini Hybrid Cognitive Bridge (v1.0)
===========================================
Yerel `Synapse-Nano` kural motorunu Google Gemini (gemini-3.8-flash)
bilişsel yetenekleriyle birleştiren hibrit derleme köprüsü.

İşleyiş:
1. Basit/tanıdık ifadeleri sıfır gecikmeyle yerel `Synapse-Nano` çözer.
2. Yerel modelin çözemediği karmaşık veya serbest Türkçe/İngilizce niyetler
   Gemini API'sine gönderilir; Gemini niyetten doğrudan geçerli bir SYNAX AST
   sembolik ifadesi (veya doğrudan C99/NEON gövdesi) sentezler.
3. Çıktı, `SynaxSecurityGuard` güvenlik duvarından geçirildikten sonra
   yerel `synaxc` derleyicisi ile ikili makine koduna dönüştürülür.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from synapse_neural_model import SynapseNanoModel
from synax_security import SynaxSecurityGuard

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"

SYSTEM_PROMPT = """You are the cognitive frontend for SYNAX (.sx), an experimental neuro-symbolic language.
Given a user's computational intent in Turkish or English, produce ONLY a clean single-line symbolic arithmetic expression using:
- Variables: a, b
- Parameter: bias
- Allowed operators: +, -, *, /, ^2, ^3
- Allowed functions: sqrt(), abs(), sin(), cos(), exp(), log(), sigmoid(), tanh(), relu()

Do NOT wrap in markdown backticks. Do NOT include explanations. Output ONLY the raw mathematical string.
Examples:
User: "a ile b farkının karesinin karekökü ve sigmoid"
Output: sigmoid(sqrt((a - b)^2) + bias)

User: "calculate kinetic energy with velocity b and mass a"
Output: 0.5 * a * (b^2) + bias
"""

class SynaxGeminiBridge:
    def __init__(self):
        self.nano = SynapseNanoModel()

    def query_gemini_for_ast(self, intent_text: str) -> str:
        """Karmaşık niyetleri Gemini API ile sembolik ifadeye dönüştürür."""
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_PROMPT},
                        {"text": f"User intent: {intent_text}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 128
            }
        }
        
        req = urllib.request.Request(
            GEMINI_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                candidate = res_data.get("candidates", [{}])[0]
                text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                # Temizlik
                text = text.replace("```", "").replace("Output:", "").strip()
                return text
        except Exception as e:
            raise RuntimeError(f"Gemini API çağrısı başarısız: {e}")

    def parse_hybrid(self, text: str) -> dict:
        """Önce yerel Nano'yu dener, yetersizse Gemini'ye danışır."""
        # 1. Yerel deneme
        local_ast = self.nano.parse_to_ast(text, auto_evolve=True)
        local_formula = local_ast.to_human_formula()

        # Eğer yerel model çok genel bir varsayılana düştüyse (örn: a * b) ve metin karmaşıksa
        is_fallback = local_formula in ("(a * b)", "?") and len(text.split()) > 4
        
        if not is_fallback:
            return {
                "source": "LOCAL_SYNAPSE_NANO",
                "symbolic_expr": local_formula,
                "ast": local_ast,
                "c_scalar": local_ast.to_c_scalar(),
                "neon_f32x4": local_ast.to_neon_f32x4() if local_ast.can_use_pure_neon_intrinsics() else None,
                "q16_fixed_point": local_ast.to_q16_fixed_point()
            }

        # 2. Gemini Hibrit Çözümleme
        gemini_expr = self.query_gemini_for_ast(text)
        gemini_ast = self.nano.parse_to_ast(gemini_expr, auto_evolve=True)
        
        # Güvenlik kapısı
        ok, msg = SynaxSecurityGuard.verify_c_expression(gemini_ast.to_c_scalar())
        if not ok:
            raise ValueError(f"[SYNAX-SEC] Gemini tarafından üretilen ifade engellendi: {msg}")

        # Başarıyla çözülen yeni kavramı yerel hafızaya da öğret!
        concept_key = "_".join(text.lower().split()[:3])
        self.nano.teach_concept(concept_key, gemini_expr)

        return {
            "source": "GEMINI_HYBRID_BRIDGE",
            "symbolic_expr": gemini_expr,
            "ast": gemini_ast,
            "c_scalar": gemini_ast.to_c_scalar(),
            "neon_f32x4": gemini_ast.to_neon_f32x4() if gemini_ast.can_use_pure_neon_intrinsics() else None,
            "q16_fixed_point": gemini_ast.to_q16_fixed_point(),
            "memorized_as": concept_key
        }

if __name__ == "__main__":
    bridge = SynaxGeminiBridge()
    test_intent = "serebral perfüzyon basıncı için a ile b farkını al, sapma ekle ve negatifleri sıfırla"
    print(f"Test Niyeti: {test_intent}")
    res = bridge.parse_hybrid(test_intent)
    print(f"Çözümleme Kaynağı: {res['source']}")
    print(f"Sembolik İfade   : {res['symbolic_expr']}")
    print(f"C99 Kodu         : {res['c_scalar']}")
    print(f"Q16.16 MCU Kodu  : {res['q16_fixed_point']}")
    if "memorized_as" in res:
        print(f"Yerel Hafızaya Kaydedildi: {res['memorized_as']}")
