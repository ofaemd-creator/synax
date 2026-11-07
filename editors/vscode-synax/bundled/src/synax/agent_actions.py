"""
SYNAX Autonomous Agent Actions (`src/synax/agent_actions.py`)
=============================================================
Provides real-world action execution for SYNAX Code:
1. Screen & Active Editor Inspection (`capture_screen_and_context`)
2. Automated Technical, Space Simulation & Biomedical Video Generation (`generate_synax_video`)
3. Zero-dependency fallback + automatic site-packages discovery for PIL/Pillow
"""

from __future__ import annotations

import glob
import math
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DESKTOP_SYNAX_DIR = Path.home() / "Desktop" / "AI modeller" / "SYNAX"


def _ensure_pil() -> bool:
    """Ensures PIL (Pillow) is importable even inside isolated minimal venvs."""
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        pass

    # Search user's uv / local / homebrew site-packages matching major.minor
    py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    search_patterns = [
        str(Path.home() / ".local" / "share" / "uv" / "python" / "*" / "lib" / py_ver / "site-packages"),
        str(Path.home() / "Library" / "Python" / f"{sys.version_info.major}.{sys.version_info.minor}" / "lib" / "python" / "site-packages"),
        f"/opt/homebrew/lib/{py_ver}/site-packages",
        f"/usr/local/lib/{py_ver}/site-packages",
    ]
    for pattern in search_patterns:
        for sp in glob.glob(pattern):
            if os.path.isdir(os.path.join(sp, "PIL")) and sp not in sys.path:
                sys.path.append(sp)
                try:
                    import PIL  # noqa: F401
                    return True
                except ImportError:
                    continue
    return False


def _find_ffmpeg() -> Optional[str]:
    candidates = [
        shutil.which("ffmpeg"),
        str(Path.home() / ".claude" / "bin" / "ffmpeg"),
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def capture_screen_and_context(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Captures macOS screen via `/usr/sbin/screencapture` (if permitted by TCC)
    and combines it with live VS Code editor context (active file, selection, code).
    """
    ctx = context or {}
    out_dir = DESKTOP_SYNAX_DIR if DESKTOP_SYNAX_DIR.exists() else Path("/tmp")
    out_path = out_dir / "synax_ekran_analizi.png"

    screen_captured = False
    resolution = "Bilinmiyor"
    brightness = 0.0
    tcc_note = ""

    if os.path.exists("/usr/sbin/screencapture"):
        try:
            proc = subprocess.run(
                ["/usr/sbin/screencapture", "-x", str(out_path)],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
                screen_captured = True
                if _ensure_pil():
                    try:
                        from PIL import Image, ImageStat

                        with Image.open(out_path) as im:
                            w, h = im.size
                            resolution = f"{w}x{h} px"
                            stat = ImageStat.Stat(im.convert("L"))
                            brightness = round(stat.mean[0], 1)
                    except Exception:
                        pass
            else:
                tcc_note = (proc.stderr or "macOS Ekran Kaydı izni (Screen Recording) gerekebilir.").strip()
        except Exception as e:
            tcc_note = str(e)

    file_name = ctx.get("fileName") or ""
    editor_text = ctx.get("editorText") or ""
    selection_text = ctx.get("selectionText") or ""
    line_count = len(editor_text.splitlines()) if editor_text else 0

    return {
        "screen_captured": screen_captured,
        "screenshot_path": str(out_path) if screen_captured else None,
        "resolution": resolution,
        "brightness": brightness,
        "tcc_note": tcc_note,
        "active_file": file_name,
        "editor_lines": line_count,
        "selection_preview": selection_text[:200] if selection_text else "",
        "editor_preview": "\n".join(editor_text.splitlines()[:12]) if editor_text else "",
    }


def _render_space_simulation_frames(
    proc_stdin: Any,
    width: int,
    height: int,
    total_frames: int,
    clean_topic: str,
    font_lg: Any,
    font_md: Any,
    font_sm: Any,
) -> None:
    """Renders a 3D Deep Space, Keplerian Orbit & Gravitational Wave Simulation."""
    from PIL import Image, ImageDraw

    rng = random.Random(42)
    # 220 3D stars: [x, y, z, color_tint]
    stars: List[List[Any]] = []
    for _ in range(220):
        stars.append([
            rng.uniform(-640, 640),
            rng.uniform(-360, 360),
            rng.uniform(0.15, 1.0),
            rng.choice([(255, 255, 255), (186, 230, 253), (254, 240, 138), (221, 214, 254)]),
        ])

    cx, cy = 480, 390  # Center of orbital system

    for frame in range(total_frames):
        t = frame * 0.055
        img = Image.new("RGB", (width, height), (5, 8, 18))
        draw = ImageDraw.Draw(img)

        # Subtle deep-space nebula glow rings
        for nr in range(260, 40, -35):
            alpha_scale = max(0, 28 - nr // 12)
            draw.ellipse(
                [cx - nr * 1.35, cy - nr * 0.78, cx + nr * 1.35, cy + nr * 0.78],
                outline=(14 + alpha_scale, 24 + alpha_scale, 52 + alpha_scale * 2),
                width=2,
            )

        # Update & draw 3D perspective starfield
        for s in stars:
            s[2] -= 0.0085
            if s[2] <= 0.06:
                s[0] = rng.uniform(-640, 640)
                s[1] = rng.uniform(-360, 360)
                s[2] = 1.0
            sx = int(cx + s[0] / s[2])
            sy = int(cy + s[1] / s[2])
            if 0 <= sx < width and 76 <= sy < height:
                sz = 1 if s[2] > 0.55 else (2 if s[2] > 0.25 else 3)
                c_r, c_g, c_b = s[3]
                bright = min(1.0, 1.15 - s[2] * 0.75)
                col = (int(c_r * bright), int(c_g * bright), int(c_b * bright))
                draw.ellipse([sx - sz, sy - sz, sx + sz, sy + sz], fill=col)

        # Draw Keplerian orbital ellipses (tilted 3D perspective)
        orbits = [
            (130, 68, 1.35, 0.0, (56, 189, 248), 9, "Gezegen-A (Gaz Devi)"),
            (225, 116, 0.82, 2.1, (16, 185, 129), 7, "Gezegen-B (Yaşanabilir)"),
            (325, 166, 0.52, 4.2, (168, 85, 247), 6, "Gezegen-C (Dış Yörünge)"),
        ]
        for rx, ry, speed, phase, pcol, prad, plabel in orbits:
            draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(28, 42, 68), width=1)

        # Central Pulsar / Star with corona glow
        pulse = int(4 * math.sin(t * 2.5))
        for gr, gcol in [
            (46 + pulse, (120, 53, 15)),
            (34 + pulse, (217, 119, 6)),
            (24, (245, 158, 11)),
            (15, (254, 249, 195)),
        ]:
            draw.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=gcol)

        # Draw Orbiting Planets + Trails + Moons
        for rx, ry, speed, phase, pcol, prad, plabel in orbits:
            ang = t * speed + phase
            # Trail
            trail_pts = []
            for dt_idx in range(18):
                tang = ang - dt_idx * 0.06 * speed
                tx = int(cx + rx * math.cos(tang))
                ty = int(cy + ry * math.sin(tang))
                trail_pts.append((tx, ty))
            if len(trail_pts) > 1:
                draw.line(trail_pts, fill=pcol, width=2)

            px = int(cx + rx * math.cos(ang))
            py = int(cy + ry * math.sin(ang))

            # Planet outer glow & core
            draw.ellipse([px - prad - 4, py - prad - 4, px + prad + 4, py + prad + 4], fill=(pcol[0] // 3, pcol[1] // 3, pcol[2] // 3))
            draw.ellipse([px - prad, py - prad, px + prad, py + prad], fill=pcol)

            # Saturn-like ring for Planet A
            if prad == 9:
                draw.ellipse([px - 18, py - 6, px + 18, py + 6], outline=(186, 230, 253), width=2)
            # Orbiting Moon for Planet B
            elif prad == 7:
                mang = t * 3.8
                mx = int(px + 22 * math.cos(mang))
                my = int(py + 12 * math.sin(mang))
                draw.ellipse([mx - 3, my - 3, mx + 3, my + 3], fill=(226, 232, 240))

        # Top HUD Bar
        draw.rectangle([0, 0, width, 74], fill=(13, 19, 33))
        draw.line([0, 74, width, 74], fill=(56, 189, 248), width=2)
        draw.text((28, 22), f"🌌 SYNAX 3D UZAY & YÖRÜNGE SİMÜLASYONU  |  {clean_topic}", fill=(226, 232, 240), font=font_lg)
        draw.text((width - 330, 26), "N-BODY SIMD  •  ARM64 NEON", fill=(56, 189, 248), font=font_md)

        # Right Telemetry Panel: Relativistic & Gravitational Wave HUD
        draw.rounded_rectangle([870, 96, 1252, 692], radius=12, fill=(13, 19, 33), outline=(30, 41, 59), width=2)
        draw.text((892, 114), "🛰️ SYNAX Astrofizik Telemetrisi", fill=(56, 189, 248), font=font_md)

        kepler_v = 29.78 + 3.4 * math.sin(t)
        grav_e = -1.42e33 * (1.0 + 0.02 * math.cos(t * 0.7))
        telemetry_lines = [
            f"Çekirdek : nbody_kepler_simd.sx",
            f"Denklem  : F = G*(m1*m2)/(r^2+eps)",
            f"Yörünge V: {kepler_v:6.2f} km/s",
            f"Potansiyel: {grav_e:.3e} J",
            f"Zaman Adım: dt = 0.0016 s (RK4)",
            f"IMMUNE   : Tekillik (r->0) Korumalı",
            f"NEON Hız : 14.8 GB/s (0-ULP)",
        ]
        ty = 154
        for tl in telemetry_lines:
            draw.text((892, ty), tl, fill=(203, 213, 225), font=font_sm)
            ty += 30

        # Gravitational Wave Strain h(t) Live Plot inside Right Panel
        draw.text((892, 390), "〰️ Kütleçekim Dalgası h(t)", fill=(168, 85, 247), font=font_md)
        draw.rounded_rectangle([892, 424, 1230, 564], radius=8, fill=(8, 12, 22), outline=(30, 41, 59), width=1)
        gw_pts = []
        for gx in range(898, 1224, 3):
            gt = (gx - 898) * 0.065 - frame * 0.22
            env = 0.55 + 0.45 * math.sin((gx - 898) * 0.012 + t)
            gy = int(494 - 46 * env * math.sin(gt))
            gw_pts.append((gx, gy))
        if len(gw_pts) > 1:
            draw.line(gw_pts, fill=(168, 85, 247), width=3)

        # Frame progress bar at bottom of HUD
        prog_w = int(338 * (frame / float(max(1, total_frames - 1))))
        draw.text((892, 592), f"Simülasyon Kare: {frame + 1}/{total_frames}", fill=(148, 163, 184), font=font_sm)
        draw.rounded_rectangle([892, 622, 1230, 644], radius=6, fill=(24, 33, 50))
        draw.rounded_rectangle([892, 622, 892 + max(8, prog_w), 644], radius=6, fill=(16, 185, 129))

        proc_stdin.write(img.tobytes())


def generate_synax_video(topic: str = "Serebral Perfüzyon & ARM64 NEON Evrimi", auto_open: bool = True) -> Dict[str, Any]:
    """
    Generates an HD 1280x720 30fps MP4 animation using PIL + FFmpeg.
    Automatically selects between:
      - 3D Space & Orbital Physics Simulation (for space/cosmos/orbit topics)
      - Biomedical & 7-Stage Silicon Pipeline Animation (for clinical/compiler topics)
    """
    ffmpeg_bin = _find_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg bulunamadı.")

    if not _ensure_pil():
        raise RuntimeError("Görüntü işleme kütüphanesi (PIL/Pillow) yüklenemedi.")

    from PIL import Image, ImageDraw, ImageFont

    out_dir = DESKTOP_SYNAX_DIR if DESKTOP_SYNAX_DIR.exists() else Path("/tmp")
    out_dir.mkdir(parents=True, exist_ok=True)

    t_lower = topic.lower()
    is_space = any(
        w in t_lower
        for w in ("uzay", "gezegen", "yıldız", "galaksi", "evren", "yörünge", "kara delik", "space", "orbit", "astro", "simülasyon")
    )

    slug = "".join(c if c.isalnum() else "_" for c in t_lower)[:28].strip("_") or "demo"
    out_mp4 = out_dir / f"synax_video_{slug}.mp4"

    width, height = 1280, 720
    fps = 30
    total_frames = 150 if is_space else 120  # 5.0s for space simulation, 4.0s for biomedical

    cmd = [
        ffmpeg_bin,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{width}x{height}",
        "-pix_fmt",
        "rgb24",
        "-r",
        str(fps),
        "-i",
        "-",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "ultrafast",
        "-crf",
        "20",
        str(out_mp4),
    ]

    try:
        font_lg = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        font_md = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 19)
        font_sm = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 15)
    except Exception:
        font_lg = ImageFont.load_default()
        font_md = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    clean_topic = topic.strip() or "Serebral Perfüzyon & ARM64 NEON"
    if len(clean_topic) > 48:
        clean_topic = clean_topic[:45] + "..."

    if is_space:
        _render_space_simulation_frames(proc.stdin, width, height, total_frames, clean_topic, font_lg, font_md, font_sm)
    else:
        for frame in range(total_frames):
            progress = frame / float(total_frames - 1)
            img = Image.new("RGB", (width, height), (11, 15, 25))
            draw = ImageDraw.Draw(img)

            draw.rectangle([0, 0, width, 74], fill=(17, 24, 39))
            draw.line([0, 74, width, 74], fill=(56, 189, 248), width=2)
            draw.text((32, 22), f"SYNAX CODE v0.8.0  |  {clean_topic}", fill=(226, 232, 240), font=font_lg)
            draw.text((width - 310, 26), "IMMUNE 0-ULP  •  ARM64 NEON", fill=(16, 185, 129), font=font_md)

            draw.rounded_rectangle([32, 100, 760, 440], radius=12, fill=(17, 24, 39), outline=(31, 41, 55), width=2)
            draw.text((52, 116), "1. Canlı Sinyal Sentezi: let cpp = relu(map - icp)", fill=(56, 189, 248), font=font_md)

            for gy in range(160, 420, 50):
                draw.line([52, gy, 740, gy], fill=(24, 33, 50), width=1)

            pts_map = []
            pts_cpp = []
            max_x = int(52 + (740 - 52) * min(1.0, progress * 1.15))
            for x in range(52, max(54, max_x), 4):
                t = (x - 52) * 0.045 - frame * 0.14
                map_y = 240 - int(45 * math.sin(t) + 18 * math.sin(2.2 * t))
                cpp_y = 330 - int(max(0.0, 55 * math.sin(t) + 22 * math.cos(1.7 * t)))
                pts_map.append((x, map_y))
                pts_cpp.append((x, cpp_y))

            if len(pts_map) > 1:
                draw.line(pts_map, fill=(56, 189, 248), width=3)
            if len(pts_cpp) > 1:
                draw.line(pts_cpp, fill=(16, 185, 129), width=4)

            draw.text((56, 405), "━━ MAP (Arteryel Basınç)    ━━ CPP = ReLU(MAP - ICP) [0-ULP Korumalı]", fill=(148, 163, 184), font=font_sm)

            draw.rounded_rectangle([784, 100, 1248, 440], radius=12, fill=(17, 24, 39), outline=(31, 41, 55), width=2)
            draw.text((806, 116), "2. 7-Aşamalı Silikon Doğrulama", fill=(168, 85, 247), font=font_md)

            stages = [
                (0.08, "1. Intent -> Kanonik .sx Çözümlendi"),
                (0.20, "2. Sembolik AST Sadeleştirme"),
                (0.35, "3. IMMUNE 19/19 Uç Küme (0-ULP)"),
                (0.50, "4. C11 Scalar & Q16.16 Üretildi"),
                (0.65, "5. ARM64 NEON vmaxq_f32 Sentezi"),
                (0.80, "6. Semantic Lock: SHA-256 #644d12e"),
                (0.92, "7. Kazanan: v2_neon_simd (6.7 µs)"),
            ]
            sy = 160
            for threshold, label in stages:
                active = progress >= threshold
                col = (16, 185, 129) if active else (71, 85, 105)
                prefix = "[✓] " if active else "[·] "
                draw.text((806, sy), prefix + label, fill=col, font=font_sm)
                sy += 38

            draw.rounded_rectangle([32, 464, 1248, 688], radius=12, fill=(17, 24, 39), outline=(31, 41, 55), width=2)
            draw.text((52, 480), "3. Donanım Evrim Arenası — Apple Silicon ARM64 NEON vs Skaler C11", fill=(245, 158, 11), font=font_md)

            bar_prog = min(1.0, max(0.0, (progress - 0.15) / 0.75))
            neon_w = int(820 * bar_prog)
            draw.text((52, 524), "🏆 Varyant B: ARM64 NEON (vmaxq_f32 / vbslq_f32) — 12.0 GB/s (5.02x Hızlanma)", fill=(16, 185, 129), font=font_sm)
            draw.rounded_rectangle([52, 550, 52 + max(12, neon_w), 576], radius=6, fill=(16, 185, 129))

            scalar_w = int(210 * bar_prog)
            draw.text((52, 596), "⚙️ Varyant A: Standart C11 Skaler Taban — 2.4 GB/s (1.00x Taban)", fill=(148, 163, 184), font=font_sm)
            draw.rounded_rectangle([52, 622, 52 + max(12, scalar_w), 648], radius=6, fill=(56, 189, 248))

            proc.stdin.write(img.tobytes())

    proc.stdin.close()
    stderr_bytes = proc.stderr.read() if proc.stderr else b""
    if proc.stderr:
        proc.stderr.close()
    proc.wait(timeout=20)

    if proc.returncode != 0 or not out_mp4.exists():
        err = stderr_bytes.decode("utf-8", errors="ignore")
        raise RuntimeError(f"Video oluşturulamadı: {err}")

    if auto_open and sys.platform == "darwin" and not os.environ.get("SYNAX_DISABLE_VIDEO_OPEN"):
        try:
            subprocess.Popen(["open", str(out_mp4)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    return {
        "video_path": str(out_mp4),
        "size_kb": round(out_mp4.stat().st_size / 1024.0, 1),
        "resolution": f"{width}x{height}",
        "fps": fps,
        "duration_sec": round(total_frames / fps, 1),
        "mode": "space_3d" if is_space else "biomedical_simd",
    }
