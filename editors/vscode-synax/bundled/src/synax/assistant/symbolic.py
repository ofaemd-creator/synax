"""Legacy symbolic explanation, separate from neural conversation."""

from __future__ import annotations
from synapse_neural_model import SynapseNanoModel
from .response import ChatResponse


def explain(model: SynapseNanoModel, text: str) -> ChatResponse:
    lower = text.lower()
    # ── 6. KLİNİK / GENEL NÖRO-SEMBOLİK ANALİZ ──
    try:
        ast = model.parse_to_ast(text, auto_evolve=True)
        formula = ast.to_human_formula()
        c_code = ast.to_c_scalar()
        neon_code = ast.to_neon_f32x4() if ast.can_use_pure_neon_intrinsics() else None
        q16_code = ast.to_q16_fixed_point()

        reply_lines = [
            "🧬 **Niyetiniz Çözümlendi ve Optimize Edildi:**\n",
            f"* **Matematiksel / Sembolik Formül:** `{formula}`",
            f"* **C11 Skaler İfade:** `{c_code}`",
        ]
        if neon_code:
            reply_lines.append(f"* **ARM64 NEON Donanım Hızlandırma:** `{neon_code}`")
        reply_lines.append(f"* **Gömülü MCU (Q16.16 Tam Sayı):** `{q16_code}`\n")

        # Klinik anahtar kelimeler varsa fizyolojik açıklama ekle
        if any(
            w in lower
            for w in (
                "basınç",
                "perfüzyon",
                "hemodinami",
                "icp",
                "map",
                "tansiyon",
                "ekg",
                "aritmi",
            )
        ):
            reply_lines.append(
                "> [!NOTE]\n"
                "> **Fizyolojik Yorum:** Bu çıktı yalnızca sembolik bir yorumdur; fizyolojik doğruluk "
                "> ve klinik uygunluk gösterilmemiştir. Sinyal kalitesi ve birimler "
                "> ayrıca değerlendirilmelidir."
            )

        reply_lines.append(
            "\n*Bu formülü kalıcı bir beceriye dönüştürmek isterseniz:* `kendine şu beceriyi edin: <isim> = <formül>`"
        )
        return ChatResponse(text="\n".join(reply_lines), action="expression_evaluated")
    except Exception as e:
        return ChatResponse(
            text=f"Komutunuzu tam olarak anlayamadım veya sözdizimsel bir hata oluştu: `{str(e)}`.\n\n"
            f"Örnek komutlar:\n"
            f"* `kendine şu beceriyi edin: serebral_oksijen = (a * 0.7 + b * 0.3) * bias`\n"
            f"* `kan basıncı ile intrakraniyal basınç farkının pozitif kısmını al`\n"
            f"* `hafızanı göster`\n"
            f"* `durum`",
            action="fallback",
        )
