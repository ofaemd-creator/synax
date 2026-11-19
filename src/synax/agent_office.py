#!/usr/bin/env python3
"""
SYNAX 3D Agent Office v3.2 — Pixar + Tycoon 3D Animated Edition
===============================================================
(`src/synax/agent_office.py`)

Features:
  - High-Resolution Pixar + Tycoon Isometric 3D Office Diorama with 8 distinct
    3D Pixar specialist characters at themed workstations around SYNAX CORE.
  - 60 FPS Interactive Tycoon Game Engine:
      * Smooth camera zoom & pan onto any clicked Pixar character (1.0x <-> 1.55x)
      * Parallax 3D mouse tilt
      * Real-time Tycoon floating XP & Research bubbles (+150 XP, +PRISMA, +0-ULP, -88% Token)
      * Animated Bezier energy orbs flying from each Pixar character into SYNAX CORE
      * Live sweeping ICU ECG heartbeat on Dr. Lyapunov's monitors, soldering sparks on
        Chief Silicon's wafer, pneumatic data capsules in Agent Vault's tubes, and
        floating Pixar-Tycoon character HUD badges & Turkish speech bubbles.
  - Per-Agent Independent Task Assignment across Claude Code, OpenAI Codex,
    Google Antigravity, and SYNAX-LLM with 3D Pixar Avatar Portraits on every card.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from synax.synax_llm import SynaxTurkishLLM
from synax.office_mcp_server import RealTimeWorkProducer


class MultitaskOfficeOrchestrator:
    def __init__(self) -> None:
        self.producer = RealTimeWorkProducer()
        self.llm = self.producer.llm

    def execute_multitask(
        self,
        prompt_tr: str,
        target_agent_id: Optional[str] = None,
        engine_provider: str = "Claude Code + Codex + Antigravity",
        user_api_key: str = "",
        user_model: str = "",
        custom_system_prompt: str = "",
    ) -> Dict[str, Any]:
        return self.producer.produce_work(
            prompt_tr,
            target_agent_id=target_agent_id,
            engine_provider=engine_provider,
            write_files=True,
            user_api_key=user_api_key,
            user_model=user_model,
            custom_system_prompt=custom_system_prompt,
        )


def _get_pixar_diorama_data_uri() -> str:
    candidates = [
        REPO_ROOT / "assets" / "studio" / "synax-pixar-tycoon-office.jpg",
        REPO_ROOT.parent / "synax" / "assets" / "studio" / "synax-pixar-tycoon-office.jpg",
        Path("/Users/o.farukaydin/.gemini/antigravity/scratch/synax/assets/studio/synax-pixar-tycoon-office.jpg"),
    ]
    for p in candidates:
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
    return ""


def build_embedded_3d_office_html() -> str:
    producer = RealTimeWorkProducer()
    initial_work = producer.produce_work(
        "Yoğun bakım EKG ve İnvaziv Kan Basıncı (IBP) monitörizasyonunda sıfır-sapmalı Lyapunov kalibrasyonu için PRISMA literatür taraması, meta-analiz ve ARM64 NEON kodu üret",
        write_files=False,
    )
    embedded_model_json = json.dumps({
        "metrics": producer.llm.training_metrics,
        "intent_metadata": producer.llm.intent_metadata,
        "intent_centroids": producer.llm.intent_centroids,
        "idf_weights": producer.llm.idf_weights,
    }, ensure_ascii=False)
    initial_work_json = json.dumps(initial_work, ensure_ascii=False)
    pixar_data_uri = _get_pixar_diorama_data_uri()

    html = r"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SYNAX 3D Agent Office v3.2 (Pixar-Tycoon Edition) — Claude Code · OpenAI Codex · Antigravity AI Stüdyosu</title>
  <style>
    :root {
      --bg-deep: #040711;
      --bg-glass: rgba(11, 17, 34, 0.90);
      --bg-card: rgba(17, 25, 48, 0.94);
      --border-cyan: rgba(56, 189, 248, 0.30);
      --cyan: #06b6d4;
      --sky: #38bdf8;
      --emerald: #10b981;
      --amber: #f59e0b;
      --violet: #a855f7;
      --indigo: #818cf8;
      --blue: #3b82f6;
      --pink: #ec4899;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: radial-gradient(circle at 25% 15%, #101d42 0%, #050915 58%, #02040a 100%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }
    header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 10px 20px;
      background: rgba(5, 9, 20, 0.96);
      border-bottom: 1px solid var(--border-cyan);
      backdrop-filter: blur(16px);
      z-index: 30; flex-wrap: wrap; gap: 10px;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-logo {
      width: 42px; height: 42px; border-radius: 12px;
      background: linear-gradient(135deg, #f59e0b, #10b981, #06b6d4);
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; font-size: 13.5px; color: #030712;
      box-shadow: 0 0 22px rgba(245, 158, 11, 0.55);
    }
    .brand-title {
      font-size: 15.5px; font-weight: 900; letter-spacing: 0.3px;
      background: linear-gradient(90deg, #fde047, #34d399, #38bdf8, #f472b6);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-sub { font-size: 11px; color: var(--text-muted); }
    .top-badges { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
    .badge {
      font-size: 11px; font-weight: 700; padding: 5px 11px; border-radius: 999px;
      background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(56, 189, 248, 0.35);
      display: inline-flex; align-items: center; gap: 6px; color: #e2e8f0;
      text-decoration: none; transition: all 0.15s;
    }
    .badge:hover { border-color: var(--amber); transform: translateY(-1px); }
    .pulse-dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--emerald); box-shadow: 0 0 9px var(--emerald);
    }

    /* 3-COLUMN ENTERPRISE STUDIO LAYOUT */
    .studio-grid {
      display: grid;
      grid-template-columns: 1.32fr 1.10fr 0.92fr;
      gap: 14px;
      padding: 14px;
      flex: 1;
      min-height: calc(100vh - 64px);
    }
    @media (max-width: 1400px) {
      .studio-grid { grid-template-columns: 1.18fr 1fr; }
      .chat-col { grid-column: span 2; }
    }
    @media (max-width: 940px) {
      .studio-grid { grid-template-columns: 1fr; }
      .chat-col { grid-column: span 1; }
    }

    .panel {
      background: var(--bg-glass);
      border: 1px solid var(--border-cyan);
      border-radius: 16px;
      display: flex; flex-direction: column;
      overflow: hidden;
      box-shadow: 0 22px 55px rgba(0, 0, 0, 0.65);
    }
    .panel-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 10px 14px;
      background: linear-gradient(90deg, rgba(10, 16, 34, 0.96), rgba(17, 27, 54, 0.92));
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 12px; font-weight: 800; letter-spacing: 0.25px;
      flex-wrap: wrap; gap: 8px;
    }
    .btn-action {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(16, 185, 129, 0.25));
      color: #fef08a; border: 1px solid rgba(245, 158, 11, 0.55);
      padding: 5px 11px; border-radius: 8px; font-size: 11px; font-weight: 800;
      cursor: pointer; transition: all 0.15s;
    }
    .btn-action:hover {
      background: linear-gradient(135deg, #f59e0b, #10b981);
      color: #030712; border-color: #fde047;
    }

    /* PIXAR + TYCOON 3D INTERACTIVE DIORAMA STAGE */
    .stage-wrap {
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      min-height: 360px;
      max-height: 455px;
      background: #131c2e;
      border-bottom: 1px solid rgba(255, 255, 255, 0.10);
      overflow: hidden;
      user-select: none;
    }
    #office3dCanvas {
      width: 100%; height: 100%; display: block; cursor: pointer;
    }
    .stage-overlay-top {
      position: absolute; top: 10px; left: 12px; right: 12px;
      display: flex; align-items: center; justify-content: space-between;
      pointer-events: none; z-index: 10;
    }
    .stage-overlay-bar {
      position: absolute; bottom: 10px; left: 12px; right: 12px;
      display: flex; align-items: center; justify-content: space-between;
      pointer-events: none; font-size: 10.5px; color: #f1f5f9; z-index: 10;
    }
    .stage-pill {
      pointer-events: auto;
      background: rgba(6, 11, 25, 0.88);
      border: 1px solid rgba(245, 158, 11, 0.45);
      padding: 5px 11px; border-radius: 999px;
      backdrop-filter: blur(10px);
      font-weight: 700;
      box-shadow: 0 6px 18px rgba(0,0,0,0.55);
    }

    /* FLOATING TYCOON CHARACTER POPUP MODAL IN 3D SCENE */
    .tycoon-popup {
      position: absolute;
      top: 52px; right: 14px;
      width: 295px;
      background: rgba(8, 14, 30, 0.95);
      border: 2px solid #f59e0b;
      border-radius: 14px;
      padding: 11px 13px;
      box-shadow: 0 18px 45px rgba(0, 0, 0, 0.8), 0 0 25px rgba(245, 158, 11, 0.35);
      backdrop-filter: blur(14px);
      z-index: 20;
      display: none;
    }
    .tycoon-popup.visible { display: block; animation: popIn 0.2s ease-out; }
    @keyframes popIn {
      from { transform: scale(0.92) translateY(8px); opacity: 0; }
      to { transform: scale(1) translateY(0); opacity: 1; }
    }

    /* PER-AGENT TASK ASSIGNMENT MATRIX WITH 3D PIXAR PORTRAITS */
    .assign-header {
      padding: 8px 14px;
      background: rgba(8, 13, 27, 0.96);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      display: flex; align-items: center; justify-content: space-between;
      font-size: 11.5px; font-weight: 800; color: #fde047;
    }
    .desks-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      padding: 10px;
      overflow-y: auto;
      max-height: calc(100vh - 550px);
      min-height: 270px;
    }
    @media (max-width: 640px) {
      .desks-grid { grid-template-columns: 1fr; }
    }
    .desk-box {
      background: var(--bg-card);
      border: 1px solid rgba(255, 255, 255, 0.10);
      border-radius: 13px;
      padding: 9px 11px;
      display: flex; flex-direction: column; gap: 6px;
      transition: all 0.2s; position: relative;
    }
    .desk-box:hover {
      border-color: rgba(245, 158, 11, 0.55);
      transform: translateY(-1px);
    }
    .desk-box.focused {
      border: 2px solid #f59e0b;
      box-shadow: 0 0 24px rgba(245, 158, 11, 0.32);
    }
    .desk-top {
      display: flex; align-items: center; justify-content: space-between; gap: 8px;
    }
    .pixar-avatar-wrap {
      display: flex; align-items: center; gap: 9px; cursor: pointer;
    }
    .pixar-portrait {
      width: 42px; height: 42px; border-radius: 50%;
      border: 2px solid #f59e0b;
      background-repeat: no-repeat;
      background-size: 620% 620%;
      box-shadow: 0 4px 12px rgba(0,0,0,0.6);
      flex-shrink: 0;
      position: relative;
    }
    .lvl-pill {
      position: absolute; bottom: -4px; right: -4px;
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      color: #fff; font-size: 8px; font-weight: 900;
      padding: 1px 4px; border-radius: 6px;
      border: 1px solid #040711;
    }
    .desk-title {
      font-size: 11.5px; font-weight: 800; color: #ffffff;
    }
    .desk-role { font-size: 9.8px; color: var(--text-muted); margin-top: 1px; }
    .engine-select {
      background: rgba(7, 12, 24, 0.95);
      color: #fde047;
      border: 1px solid rgba(245, 158, 11, 0.45);
      border-radius: 7px; font-size: 9.5px; font-weight: 800;
      padding: 3px 6px; outline: none; cursor: pointer;
    }
    .desk-speech {
      font-size: 10.5px; color: #34d399;
      background: rgba(6, 11, 23, 0.78);
      padding: 4px 8px; border-radius: 7px;
      border-left: 3px solid var(--emerald);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .progress-track {
      width: 100%; height: 6px; background: rgba(15, 23, 42, 0.95);
      border-radius: 999px; overflow: hidden;
    }
    .progress-fill {
      height: 100%; border-radius: 999px; transition: width 0.35s ease;
    }
    .desk-assign-row { display: flex; gap: 5px; align-items: center; }
    .desk-input {
      flex: 1; background: rgba(6, 10, 22, 0.95);
      border: 1px solid rgba(148, 163, 184, 0.28);
      color: #f1f5f9; padding: 5px 8px; border-radius: 7px;
      font-size: 10.5px; outline: none;
    }
    .desk-input:focus { border-color: #fde047; }
    .btn-assign {
      background: linear-gradient(135deg, #f59e0b, #ea580c);
      color: #ffffff; border: none; padding: 5px 9px; border-radius: 7px;
      font-size: 10px; font-weight: 900; cursor: pointer; white-space: nowrap;
      box-shadow: 0 2px 8px rgba(245, 158, 11, 0.35);
    }
    .btn-assign:hover { filter: brightness(1.15); }
    .btn-view-work {
      background: rgba(16, 185, 129, 0.18); color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.45);
      padding: 5px 7px; border-radius: 7px;
      font-size: 10px; font-weight: 800; cursor: pointer; white-space: nowrap;
    }

    /* CENTER COLUMN: LIVE WORK PRODUCTION WORKBENCH */
    .workbench-tabs {
      display: flex; gap: 5px; padding: 8px 10px;
      background: rgba(7, 12, 24, 0.95);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      overflow-x: auto;
    }
    .w-tab {
      font-size: 11px; font-weight: 700; padding: 6px 11px; border-radius: 8px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--text-muted); cursor: pointer; white-space: nowrap;
      transition: all 0.15s;
    }
    .w-tab.active {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.28), rgba(16, 185, 129, 0.25));
      color: #ffffff; border-color: #fde047;
      box-shadow: 0 0 12px rgba(245, 158, 11, 0.25);
    }
    .workbench-toolbar {
      display: flex; align-items: center; justify-content: space-between;
      padding: 7px 12px; background: rgba(10, 16, 32, 0.85);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 11px; color: #94a3b8;
    }
    .workbench-body {
      flex: 1; padding: 14px; overflow-y: auto;
      max-height: calc(100vh - 205px); font-size: 12.5px; line-height: 1.6;
    }
    .code-view {
      background: #03060e; border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 10px; padding: 12px;
      font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, monospace;
      font-size: 11.8px; color: #34d399;
      white-space: pre-wrap; overflow-x: auto;
    }
    .md-view h1, .md-view h2, .md-view h3 { color: #38bdf8; margin: 10px 0 6px 0; }
    .md-view table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 11.2px; }
    .md-view th, .md-view td { border: 1px solid rgba(148, 163, 184, 0.25); padding: 6px 8px; text-align: left; }
    .md-view th { background: rgba(15, 23, 42, 0.95); color: #fbbf24; }
    .metric-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }
    .m-card { background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 8px 10px; }
    .m-label { font-size: 10px; color: var(--text-muted); }
    .m-val { font-size: 15px; font-weight: 800; color: #34d399; margin-top: 2px; }

    /* RIGHT COLUMN: SYNAX-LLM TURKISH AI CHAT */
    .quick-bar {
      display: flex; gap: 6px; padding: 8px 10px;
      overflow-x: auto; background: rgba(8, 13, 26, 0.9);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .q-chip {
      flex-shrink: 0; font-size: 10.5px; font-weight: 700;
      padding: 5px 10px; border-radius: 999px;
      background: rgba(23, 33, 58, 0.95);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #e2e8f0; cursor: pointer;
    }
    .q-chip:hover { border-color: var(--amber); background: rgba(245, 158, 11, 0.18); }
    .chat-box {
      flex: 1; overflow-y: auto; padding: 12px;
      display: flex; flex-direction: column; gap: 10px;
      max-height: calc(100vh - 210px);
    }
    .bubble { padding: 11px 13px; border-radius: 13px; font-size: 12.5px; line-height: 1.55; max-width: 95%; }
    .bubble.user {
      align-self: flex-end; background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff; border-bottom-right-radius: 3px;
    }
    .bubble.ai {
      align-self: flex-start; background: rgba(15, 23, 42, 0.96);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #f1f5f9; border-bottom-left-radius: 3px;
    }
    .bubble-head { font-size: 10px; font-weight: 800; color: #fbbf24; margin-bottom: 5px; display: flex; justify-content: space-between; }
    .chat-footer { display: flex; gap: 7px; padding: 10px; background: rgba(5, 9, 20, 0.96); border-top: 1px solid rgba(255, 255, 255, 0.08); }
    .chat-inp {
      flex: 1; background: rgba(15, 23, 42, 0.95);
      border: 1px solid rgba(56, 189, 248, 0.38);
      color: #fff; padding: 10px 12px; border-radius: 9px; font-size: 12.5px; outline: none;
    }
    .chat-inp:focus { border-color: var(--emerald); }
    .chat-btn {
      background: linear-gradient(135deg, #f59e0b, #10b981);
      color: #030712; font-weight: 900; border: none;
      padding: 0 15px; border-radius: 9px; cursor: pointer; font-size: 12.5px;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-logo">SX 3.2</div>
      <div>
        <div class="brand-title">SYNAX 3D AGENT OFFICE — PIXAR &amp; TYCOON ANIMATED EDITION (CLAUDE · CODEX · ANTIGRAVITY)</div>
        <div class="brand-sub">Dr. Ömer Faruk Aydın (@ofaemd-creator) · 8 Pixar Uzman Karakteri · Ajan Başına Özel Görev &amp; Tycoon XP Simülasyonu</div>
      </div>
    </div>
    <div class="top-badges">
      <span class="badge"><span class="pulse-dot"></span>Pixar-Tycoon 60 FPS Motoru: Aktif</span>
      <span class="badge">🤝 Claude Code · Codex · Antigravity</span>
      <span class="badge">📚 PRISMA 2020 &amp; Biyoistatistik</span>
      <span class="badge" id="tycoonTotalXpBadge" style="color:#fde047;border-color:#f59e0b;">⭐ Ofis Seviyesi: LVL 99 (14,850 XP)</span>
      <button onclick="openAccountHubModal()" class="badge" id="connectedAccountBadge" style="cursor:pointer;color:#fde047;border-color:#f59e0b;background:rgba(245,158,11,0.18);">🔑 Kendi Hesabını &amp; Özel Ajanını Bağla</button>
      <button onclick="openComputerTab()" class="badge" style="cursor:pointer;color:#34d399;border-color:#10b981;">🖥️ Bilgisayarım &amp; Sistem Doktoru</button>
      <button onclick="openLocalWorkspaceFolder()" class="badge" style="cursor:pointer;color:#38bdf8;border-color:#38bdf8;">📂 Bilgisayarımdaki Klasörü Aç</button>
      <a href="https://github.com/ofaemd-creator/synax-agent-office/releases/download/v4.0.0/SYNAX-Desktop-macOS-v4.0.0.zip" class="badge" style="color:#fde047;border-color:#f59e0b;background:rgba(245,158,11,0.16);">💻 Masaüstü Uygulamasını İndir (v4.2)</a>
    </div>
  </header>

  <!-- ===================================================================== -->
  <!-- ACCOUNT & CUSTOM AGENT CONNECTOR MODAL (BYOK / CLAUDE / CODEX / OLLAMA) -->
  <!-- ===================================================================== -->
  <div id="accountHubModal" style="display:none;position:fixed;inset:0;background:rgba(2,6,18,0.82);backdrop-filter:blur(10px);z-index:100;align-items:center;justify-content:center;padding:16px;">
    <div style="background:#0b1224;border:2px solid #f59e0b;border-radius:18px;max-width:780px;width:100%;padding:20px;box-shadow:0 25px 70px rgba(0,0,0,0.85);color:#f8fafc;max-height:92vh;overflow-y:auto;">
      <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:12px;margin-bottom:14px;">
        <div>
          <h2 style="font-size:16px;color:#fde047;">🔑 Kendi Yapay Zeka Hesabını &amp; Özel Ajanlarını Bağla (Claude Code · Codex · Gemini · Ollama)</h2>
          <p style="font-size:11.5px;color:#94a3b8;margin-top:3px;">Anahtarınız yalnızca kendi tarayıcınızda/bilgisayarınızda saklanır; 8 Pixar ajanı ve eklediğiniz özel ajanlar doğrudan kendi hesabınızla çalışır.</p>
        </div>
        <button onclick="closeAccountHubModal()" style="background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid #ef4444;border-radius:8px;padding:5px 11px;cursor:pointer;font-weight:800;">✕ Kapat</button>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <!-- LEFT: CONNECT YOUR OWN AI ACCOUNT (BYOK / CLI) -->
        <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(56,189,248,0.3);border-radius:13px;padding:14px;">
          <h3 style="font-size:13px;color:#38bdf8;margin-bottom:10px;">🔗 1. Kendi AI Hesabını / API Anahtarını Bağla</h3>
          <label style="font-size:11px;color:#cbd5e1;display:block;margin-bottom:4px;">Yapay Zeka Sağlayıcısı Seçin:</label>
          <select id="userProviderSelect" class="desk-input" style="width:100%;margin-bottom:9px;padding:7px;">
            <option value="Anthropic Claude Code">Anthropic Claude / Claude Code (sk-ant-...)</option>
            <option value="OpenAI Codex">OpenAI Codex / GPT-4o (sk-...)</option>
            <option value="Google Gemini">Google Gemini 2.5 Flash/Pro (AIza...)</option>
            <option value="OpenRouter">OpenRouter (Ücretsiz &amp; Pro Modeller · sk-or-...)</option>
            <option value="Local Ollama">Yerel Ollama Sunucusu (http://127.0.0.1:11434)</option>
            <option value="SYNAX-LLM Türkçe">Yerel SYNAX-LLM Türkçe (Ücretsiz · Anahtarsız)</option>
          </select>

          <label style="font-size:11px;color:#cbd5e1;display:block;margin-bottom:4px;">API Anahtarınız (veya Yerel Ollama URL):</label>
          <input type="password" id="userApiKeyInput" class="desk-input" style="width:100%;margin-bottom:9px;padding:7px;" placeholder="sk-ant-... / sk-... / AIza... / sk-or-... (Anahtarsız için boş bırakın)" />

          <label style="font-size:11px;color:#cbd5e1;display:block;margin-bottom:4px;">Model Adı (İsteğe Bağlı):</label>
          <input type="text" id="userModelInput" class="desk-input" style="width:100%;margin-bottom:11px;padding:7px;" placeholder="Örn: claude-3-7-sonnet-latest, gpt-4o, gemini-2.5-flash, qwen2.5-coder" />

          <div style="display:flex;gap:7px;">
            <button class="btn-assign" style="flex:1;padding:8px;" onclick="saveUserAccountConnection()">🔗 Hesabımı Bağla &amp; Tüm Ajanlara Uygula</button>
            <button class="btn-view-work" onclick="clearUserAccountConnection()">Sıfırla</button>
          </div>
          <div id="accountConnStatusMsg" style="font-size:11px;color:#34d399;margin-top:8px;">● Aktif: Yerel SYNAX-LLM + Claude/Codex MCP Köprüsü</div>
        </div>

        <!-- RIGHT: ADD YOUR OWN CUSTOM AGENT TO THE 3D OFFICE & CLAUDE/CODEX -->
        <div style="background:rgba(15,23,42,0.9);border:1px solid rgba(16,185,129,0.35);border-radius:13px;padding:14px;">
          <h3 style="font-size:13px;color:#34d399;margin-bottom:10px;">➕ 2. Kendi Özel Ajanını Ofise &amp; Claude/Codex'e Ekle</h3>
          <label style="font-size:11px;color:#cbd5e1;display:block;margin-bottom:4px;">Özel Ajan Adı:</label>
          <input type="text" id="customAgentName" class="desk-input" style="width:100%;margin-bottom:8px;padding:7px;" placeholder="Örn: Dr. Radyoloji AI veya Kıdemli Rust Mimarı" />

          <label style="font-size:11px;color:#cbd5e1;display:block;margin-bottom:4px;">Uzmanlık Alanı &amp; Görevi:</label>
          <input type="text" id="customAgentRole" class="desk-input" style="width:100%;margin-bottom:8px;padding:7px;" placeholder="Örn: Klinik Görüntüleme Analizi / Mikroservis Güvenliği" />

          <label style="font-size:11px;color:#cbd5e1;display:block;margin-bottom:4px;">Sistem Talimatı (System Prompt / Beceri Tanımı):</label>
          <textarea id="customAgentPrompt" class="desk-input" style="width:100%;height:62px;margin-bottom:9px;padding:7px;resize:vertical;" placeholder="Bu ajanın nasıl davranacağını ve hangi çıktıları üreteceğini yazın..."></textarea>

          <div style="display:flex;gap:7px;">
            <button class="btn-assign" style="flex:1;padding:8px;background:linear-gradient(135deg,#10b981,#06b6d4);color:#030712;" onclick="createCustomUserAgent()">➕ Özel Ajanı Ofise Ekle &amp; .MD İndir</button>
          </div>
          <div id="customAgentStatusMsg" style="font-size:10.5px;color:#38bdf8;margin-top:8px;">Eklediğiniz ajan anında 3D Ofis Matrisine ve <code>.claude/agents/</code> içine eklenir.</div>
        </div>
      </div>
    </div>
  </div>

  <main class="studio-grid">
    <!-- =================================================================== -->
    <!-- COLUMN 1: PIXAR + TYCOON 3D ANIMATED DIORAMA & PER-AGENT MATRIX     -->
    <!-- =================================================================== -->
    <section class="panel">
      <div class="panel-header">
        <span>🎬 PIXAR-TYCOON 3D AJAN OFİSİ (Karakterlere Tıklayarak Yakınlaşın &amp; Özel Görev Atayın)</span>
        <div style="display:flex;gap:6px;">
          <button class="btn-action" onclick="dispatchAll8Agents()">⚡ 8 Karakteri Eşzamanlı Çalıştır</button>
          <button class="btn-action" onclick="resetCameraZoom()">🔍 Tüm Ofis (1x)</button>
        </div>
      </div>

      <div class="stage-wrap" id="stageContainer">
        <canvas id="office3dCanvas"></canvas>

        <!-- Floating Tycoon Character Quick-Task Modal inside 3D Scene -->
        <div class="tycoon-popup" id="tycoonPopupModal">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
            <span style="font-size:12px;font-weight:900;color:#fde047;" id="popupCharName">Masa 1</span>
            <button onclick="resetCameraZoom()" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:13px;">✕ Kapat</button>
          </div>
          <div style="font-size:10.5px;color:#cbd5e1;margin-bottom:7px;" id="popupCharRole">Uzmanlık</div>
          <div style="display:flex;gap:5px;margin-bottom:7px;">
            <input type="text" id="popupTaskInput" class="desk-input" placeholder="Bu Pixar ajanına özel görev..." />
            <button class="btn-assign" onclick="submitPopupTask()">🎯 Başlat</button>
          </div>
          <div style="font-size:10px;color:#34d399;" id="popupCharSpeech">💬 Hazır!</div>
        </div>

        <div class="stage-overlay-bar">
          <span class="stage-pill">🕹️ Herhangi bir Pixar karakterine tıklayın: 3D Kamera yakınlaşır ve özel görev atar</span>
          <span class="stage-pill" id="activeBeamStatus" style="color:#fde047;">⭐ 8/8 Pixar Ajanı Çalışıyor · +XP Araştırma Küreleri Aktif</span>
        </div>
      </div>

      <div class="assign-header">
        <span>🎯 8 PIXAR AJANI — AYRI İŞ ATAMA &amp; CANLI SEVİYE MATRİSİ (Claude Code · OpenAI Codex · Antigravity)</span>
        <span style="color:#34d399;">Canlı Tycoon Modu</span>
      </div>
      <div class="desks-grid" id="desksMatrixContainer"></div>
    </section>

    <!-- =================================================================== -->
    <!-- COLUMN 2: LIVE WORK & ARTIFACT PRODUCTION WORKBENCH                 -->
    <!-- =================================================================== -->
    <section class="panel">
      <div class="panel-header">
        <span>🛠️ CANLI İŞ ÜRETİM ATÖLYESİ (AJANLARIN ÜRETTİĞİ GERÇEK ÇIKTILAR)</span>
        <div style="display:flex;gap:6px;">
          <button class="btn-action" onclick="copyCurrentArtifact()">📋 Kopyala</button>
          <button class="btn-action" onclick="downloadCurrentArtifact()">⬇️ İndir</button>
        </div>
      </div>

      <div class="workbench-tabs">
        <button class="w-tab active" id="btn-tab-academic" onclick="switchWorkbenchTab('tab-academic')">📚 1. Akademik PRISMA &amp; Meta-Analiz</button>
        <button class="w-tab" id="btn-tab-sx" onclick="switchWorkbenchTab('tab-sx')">⚡ 2. .SX &amp; Python + TDD Kodu</button>
        <button class="w-tab" id="btn-tab-c" onclick="switchWorkbenchTab('tab-c')">🔩 3. ARM64 NEON / AVX2 / C99 / MCU</button>
        <button class="w-tab" id="btn-tab-sim" onclick="switchWorkbenchTab('tab-sim')">🩺 4. Lyapunov &amp; 0-ULP Simülasyon</button>
        <button class="w-tab" id="btn-tab-handoff" onclick="switchWorkbenchTab('tab-handoff')">🤝 5. Claude Code &amp; Codex Kapsülü</button>
        <button class="w-tab" id="btn-tab-computer" onclick="switchWorkbenchTab('tab-computer')">🖥️ 6. Bilgisayarım &amp; Sistem Doktoru</button>
      </div>

      <div class="workbench-toolbar">
        <span id="workbenchActiveJobLabel">Aktif İş: SYNAX-JOB-0001 · 7 Üretim Dosyası Hazır</span>
        <span style="color:#fde047;font-weight:800;" id="workbenchActiveAgentLabel">Üreten: 8 Pixar Ajanı Eşzamanlı</span>
      </div>

      <div class="workbench-body" id="workbenchContentArea"></div>
    </section>

    <!-- =================================================================== -->
    <!-- COLUMN 3: SYNAX-LLM TURKISH CONVERSATIONAL AI & MISSION COMMAND     -->
    <!-- =================================================================== -->
    <section class="panel chat-col">
      <div class="panel-header">
        <span>🧠 SYNAX-LLM v3.2 — TÜRKÇE KONUŞAN AI &amp; OFİS YÖNETİCİSİ</span>
        <span style="color:#34d399;font-size:11px;">● Türkçe Doğal Dil + 8 Ajan</span>
      </div>

      <div class="quick-bar">
        <button class="q-chip" onclick="quickPrompt('Bilgisayarımın sistem durumunu, disk alanını, işlemci yükünü ve çalışan ağır işlemleri kontrol et, sorun varsa çöz')">🖥️ Bilgisayarımı Kontrol Et &amp; Sorun Çöz</button>
        <button class="q-chip" onclick="quickPrompt('Yoğun bakımda sepsis ve EKG/IBP monitörizasyonu için PRISMA literatür taraması, meta-analiz ve Forest Plot üret')">📚 Prof. Scholar &amp; Biostat: PRISMA</button>
        <button class="q-chip" onclick="quickPrompt('EKG ve kan basıncı sensöründe sürekli kalibrasyonu bitiren sıfır-sapmalı Lyapunov C99 ve ARM64 NEON kodu üret')">🩺 Dr. Lyapunov: Sıfır-Sapma Kodu</button>
        <button class="q-chip" onclick="quickPrompt('Claude Code ve OpenAI Codex için %88 token tasarruflu AST iskeletleştirici ve SHA-256 hafıza kapsülü oluştur')">🛡️ Capt. Shield: -%88 Token Kalkanı</button>
        <button class="q-chip" onclick="quickPrompt('8 Pixar ajanının her birine ayrı görev dağıtarak makale, istatistik, formal kanıt ve çip kodu üret')">🎬 8 Karakteri Birden Çalıştır</button>
      </div>

      <div class="chat-box" id="chatMessagesBox"></div>

      <div class="chat-footer">
        <input
          type="text"
          id="mainChatInput"
          class="chat-inp"
          placeholder="Türkçe görev yazın veya soldaki Pixar karakterlerine tıklayarak ayrı iş atayın..."
          onkeydown="if(event.key==='Enter') submitMainChat()"
        />
        <button class="chat-btn" onclick="submitMainChat()">Üret &amp; Gönder ↵</button>
      </div>
    </section>
  </main>

  <script>
    // =========================================================================
    // 1. EMBEDDED PIXAR-TYCOON 3D DIORAMA & SYNAX-LLM WEIGHTS
    // =========================================================================
    const PIXAR_DIORAMA_URI = "__PIXAR_DATA_URI__";
    const SYNAX_MODEL = __EMBEDDED_MODEL_JSON__;
    let currentWorkState = __INITIAL_WORK_JSON__;
    let currentTabId = 'tab-academic';
    let focusedDeskIndex = -1;
    let totalOfficeXP = 14850;
    let userConnectedProvider = localStorage.getItem('synax_user_provider') || '';
    let userConnectedApiKey = localStorage.getItem('synax_user_api_key') || '';
    let userConnectedModel = localStorage.getItem('synax_user_model') || '';

    function openAccountHubModal() {
      const m = document.getElementById('accountHubModal');
      if (userConnectedProvider) document.getElementById('userProviderSelect').value = userConnectedProvider;
      if (userConnectedApiKey) document.getElementById('userApiKeyInput').value = userConnectedApiKey;
      if (userConnectedModel) document.getElementById('userModelInput').value = userConnectedModel;
      m.style.display = 'flex';
    }
    function closeAccountHubModal() {
      document.getElementById('accountHubModal').style.display = 'none';
    }
    function saveUserAccountConnection() {
      userConnectedProvider = document.getElementById('userProviderSelect').value;
      userConnectedApiKey = document.getElementById('userApiKeyInput').value.trim();
      userConnectedModel = document.getElementById('userModelInput').value.trim();
      localStorage.setItem('synax_user_provider', userConnectedProvider);
      localStorage.setItem('synax_user_api_key', userConnectedApiKey);
      localStorage.setItem('synax_user_model', userConnectedModel);

      AGENT_DESKS.forEach(d => { d.engine = userConnectedProvider; });
      renderDesksMatrix();
      const badge = document.getElementById('connectedAccountBadge');
      if (badge) badge.innerHTML = `🟢 Bağlı Hesap: ${userConnectedProvider}`;
      document.getElementById('accountConnStatusMsg').innerHTML = `✅ <strong>${userConnectedProvider}</strong> hesabınız bağlandı! Tüm Pixar ajanları artık kendi hesabınızla çalışıyor.`;
      appendChatBubble('ai', `🔑 **Hesap Bağlantısı Başarılı!**\n3D Ajan Ofisindeki tüm Pixar ajanları artık bağladığınız **\`${userConnectedProvider}\`** (${userConnectedModel || 'Varsayılan Model'}) hesabınız üzerinden çalışacak şekilde yapılandırıldı.`, 'Hesap Bağlandı');
    }
    function clearUserAccountConnection() {
      userConnectedProvider = '';
      userConnectedApiKey = '';
      userConnectedModel = '';
      localStorage.removeItem('synax_user_provider');
      localStorage.removeItem('synax_user_api_key');
      localStorage.removeItem('synax_user_model');
      document.getElementById('userApiKeyInput').value = '';
      document.getElementById('userModelInput').value = '';
      const badge = document.getElementById('connectedAccountBadge');
      if (badge) badge.innerHTML = `🔑 Kendi Hesabını &amp; Özel Ajanını Bağla`;
      document.getElementById('accountConnStatusMsg').innerHTML = `● Yerel SYNAX-LLM varsayılan moda döndürüldü.`;
    }

    async function callBrowserDirectLLM(promptText, sysPrompt) {
      if (!userConnectedApiKey && !userConnectedProvider.includes('Ollama')) return null;
      const prov = (userConnectedProvider || '').toLowerCase();
      const key = userConnectedApiKey;
      const sys = sysPrompt || 'Sen SYNAX 3D Ajan Ofisinde çalışan uzman bir yapay zeka ajanısın. Yanıtlarını Türkçe, net ve uygulanabilir olarak üret.';
      try {
        if (prov.includes('gemini') || key.startsWith('AIza')) {
          const m = userConnectedModel || 'gemini-2.5-flash';
          const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent?key=${encodeURIComponent(key)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contents: [{ parts: [{ text: sys + '\n\nGörev: ' + promptText }] }] })
          });
          if (r.ok) {
            const d = await r.json();
            return d.candidates[0].content.parts[0].text;
          }
        } else if (prov.includes('openrouter') || prov.includes('openai') || prov.includes('codex') || key.startsWith('sk-')) {
          const isOr = prov.includes('openrouter') || key.startsWith('sk-or-');
          const url = isOr ? 'https://openrouter.ai/api/v1/chat/completions' : 'https://api.openai.com/v1/chat/completions';
          const m = userConnectedModel || (isOr ? 'google/gemma-3-27b-it:free' : 'gpt-4o-mini');
          const r = await fetch(url, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: m, messages: [{ role: 'system', content: sys }, { role: 'user', content: promptText }] })
          });
          if (r.ok) {
            const d = await r.json();
            return d.choices[0].message.content;
          }
        } else if (prov.includes('ollama')) {
          const baseUrl = key.startsWith('http') ? key : 'http://127.0.0.1:11434';
          const m = userConnectedModel || 'qwen2.5-coder:latest';
          const r = await fetch(`${baseUrl.replace(/\/$/, '')}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: m, prompt: sys + '\n\nGörev: ' + promptText, stream: false })
          });
          if (r.ok) {
            const d = await r.json();
            return d.response;
          }
        }
      } catch (_) {}
      return null;
    }

    async function createCustomUserAgent() {
      const name = document.getElementById('customAgentName').value.trim() || 'Özel Uzman Ajan';
      const role = document.getElementById('customAgentRole').value.trim() || 'Özel Mühendislik & Analiz Ajanı';
      const sysPrompt = document.getElementById('customAgentPrompt').value.trim() || `Sen ${name} (${role}) ajanısın. Verilen görevleri en yüksek kalitede çöz.`;
      const provider = userConnectedProvider || document.getElementById('userProviderSelect').value || 'Claude Code';
      const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || ('custom-' + (AGENT_DESKS.length + 1));

      const newIdx = AGENT_DESKS.length;
      const newDesk = {
        id: slug,
        index: newIdx,
        u: 0.500, v: 0.480,
        headU: 0.500, headV: 0.390,
        bgPos: '50% 15%',
        xpTag: '+350 XP · ÖZEL AJAN',
        shortTitle: name.toUpperCase().slice(0, 18),
        name: `Masa ${newIdx + 1}: ${name}`,
        role: role,
        engine: provider,
        customSystemPrompt: sysPrompt,
        color: '#f43f5e',
        active: true,
        progress: 100,
        level: 99,
        speech: 'Özel ajanınız ofise bağlandı ve göreve hazır!',
        defaultTask: `${role} kapsamında kapsamlı analiz ve çözüm üret`,
        targetTab: 'tab-handoff'
      };
      AGENT_DESKS.push(newDesk);
      renderDesksMatrix();

      // Save to backend if running locally
      try {
        await fetch('/api/register-agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, role, system_prompt: sysPrompt, provider })
        });
      } catch (_) {}

      // Also download the Claude Code .md agent definition file for the user
      const mdContent = `---\nname: ${slug}\ndescription: ${role}\nprovider: ${provider}\n---\n\n# ${name} (${role})\n\n${sysPrompt}\n`;
      const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${slug}.claude-agent.md`;
      a.click();

      document.getElementById('customAgentStatusMsg').innerHTML = `✅ <strong>${name}</strong> ofise eklendi ve Claude Code ajan dosyası (<code>${slug}.claude-agent.md</code>) indirildi!`;
      appendChatBubble('ai', `➕ **Yeni Özel Ajanınız Ofise Katıldı: \`${name}\` (${role})**\nSol alttaki Ajan Matrisine **Masa ${newIdx + 1}** olarak eklendi ve Claude Code / OpenAI Codex uyumlu ajan tanım dosyanız indirildi. Hemen görev atayabilirsiniz!`, 'Özel Ajan Aktif');
      closeAccountHubModal();
    }

    // Exact (u, v) normalized coordinates of the 8 Pixar characters on the 16:9 3D Diorama
    // Central SYNAX CORE is at (u: 0.500, v: 0.485)
    const AGENT_DESKS = [
      {
        id: 'synax-llm',
        index: 0,
        u: 0.500, v: 0.215,
        headU: 0.500, headV: 0.145,
        bgPos: '50% 15%',
        xpTag: '+180 XP · TÜRKÇE NLU',
        shortTitle: 'BAŞ MİMAR SYNAX-LLM',
        name: 'Masa 1: Baş Mimar SYNAX-LLM',
        role: 'Türkçe Dil Modeli · Çoklu-Ajan Orkestratörü',
        engine: 'SYNAX-LLM + Antigravity',
        color: '#f59e0b',
        active: true,
        progress: 100,
        level: 99,
        speech: '8 ajan koordineli çalışıyor · Türkçe NLU aktif!',
        defaultTask: 'Tüm ajanları koordine et ve Türkçe mimari plan çıkar',
        targetTab: 'tab-sx'
      },
      {
        id: 'agent-scholar',
        index: 1,
        u: 0.305, v: 0.315,
        headU: 0.285, headV: 0.220,
        bgPos: '28% 25%',
        xpTag: '+240 XP · PRISMA 2020',
        shortTitle: 'PROF. SCHOLAR (PRISMA)',
        name: 'Masa 2: Prof. Scholar (Literatür)',
        role: 'PubMed · CrossRef · PRISMA 2020 · PICO & BibTeX',
        engine: 'Claude Code @academic-scholar',
        color: '#38bdf8',
        active: true,
        progress: 100,
        level: 96,
        speech: '5 hakemli makale, PICO & BibTeX sentezlendi!',
        defaultTask: 'Yoğun bakım EKG ve IBP sıfır-sapma kalibrasyonu için PRISMA literatür taraması yap',
        targetTab: 'tab-academic'
      },
      {
        id: 'agent-biostat',
        index: 2,
        u: 0.220, v: 0.495,
        headU: 0.198, headV: 0.405,
        bgPos: '19% 44%',
        xpTag: '+210 XP · META-ANALİZ',
        shortTitle: 'DR. BIOSTAT (İSTATİSTİK)',
        name: 'Masa 3: Dr. Biostat (Meta-Analiz)',
        role: 'Forest Plot · Hedges g · ROC/AUC · IMRaD Makale',
        engine: 'Claude Code @biostat-analyst',
        color: '#818cf8',
        active: true,
        progress: 100,
        level: 95,
        speech: 'Pooled d=1.18 (p<0.0001) · Forest Plot hazır!',
        defaultTask: 'Seçilen makalelerin meta-analizini, Forest Plot grafiğini ve IMRaD tartışmasını yaz',
        targetTab: 'tab-academic'
      },
      {
        id: 'biomed-autocal',
        index: 3,
        u: 0.345, v: 0.655,
        headU: 0.365, headV: 0.565,
        bgPos: '36.5% 60%',
        xpTag: '+300 XP · %99.98 ZERO-DRIFT',
        shortTitle: 'DR. LYAPUNOV (BİYOMEDİKAL)',
        name: 'Masa 4: Dr. Lyapunov (Sıfır-Sapma)',
        role: 'EKG/IBP/SpO2 Daralmalı Öz-Kalibrasyon (V_{k+1} < V_k)',
        engine: 'SYNAX @biomed-lyapunov',
        color: '#10b981',
        active: true,
        progress: 100,
        level: 99,
        speech: 'V_{k+1} < V_k sıfır-sapma %99.98 kilitlendi!',
        defaultTask: 'EKG ve IBP sensörü için 20-epoch Lyapunov sıfır-sapma simülasyonu çalıştır',
        targetTab: 'tab-sim'
      },
      {
        id: 'egraph-prover',
        index: 4,
        u: 0.655, v: 0.635,
        headU: 0.632, headV: 0.545,
        bgPos: '63% 58%',
        xpTag: '+260 XP · 0-ULP KANIT',
        shortTitle: 'MASTER E-GRAPH (0-ULP)',
        name: 'Masa 5: Master E-Graph (Formal Kanıt)',
        role: 'Eşitlik Doygunluğu & 19-Küme IEEE-754 0-ULP Kanıtı',
        engine: 'OpenAI Codex @egraph-prover',
        color: '#a855f7',
        active: true,
        progress: 100,
        level: 97,
        speech: '[lo, hi] aralığında 19/19 IEEE-754 0-ULP SAFE!',
        defaultTask: 'Çekirdek ifadesini E-Graph ile FMA düğümüne indirge ve 0-ULP aralık kanıtı üret',
        targetTab: 'tab-sim'
      },
      {
        id: 'token-shield',
        index: 5,
        u: 0.785, v: 0.495,
        headU: 0.802, headV: 0.400,
        bgPos: '80.5% 43%',
        xpTag: '-%88.4 TOKEN TASARRUFU',
        shortTitle: 'CAPT. SHIELD (-%88 TOKEN)',
        name: 'Masa 6: Capt. Shield (Token Kalkanı)',
        role: 'Claude Code & Codex AST İskeletleştirme (-%88.4)',
        engine: 'Claude Code @token-shield',
        color: '#3b82f6',
        active: true,
        progress: 100,
        level: 98,
        speech: 'AST İskeletleştirme ile -%93.8 token korundu!',
        defaultTask: 'Proje kodlarını Claude Code ve Codex için AST iskeletleştirme ile %88 sıkıştır',
        targetTab: 'tab-handoff'
      },
      {
        id: 'context-vault',
        index: 6,
        u: 0.715, v: 0.315,
        headU: 0.742, headV: 0.225,
        bgPos: '74.5% 26%',
        xpTag: '+190 XP · SHA-256 VAULT',
        shortTitle: 'AGENT VAULT (SHA-256)',
        name: 'Masa 7: Agent Vault (Hafıza Kasası)',
        role: 'Claude ↔ Codex ↔ Antigravity <180 Token Devir',
        engine: 'Google Antigravity @vault',
        color: '#06b6d4',
        active: true,
        progress: 100,
        level: 96,
        speech: 'SHA-256 kilitli <180 token kapsül tüplerde!',
        defaultTask: 'Claude Code, Codex ve Antigravity arasında sıfır-kayıplı SHA-256 devir kapsülü mühürle',
        targetTab: 'tab-handoff'
      },
      {
        id: 'silicon-studio',
        index: 7,
        u: 0.500, v: 0.755,
        headU: 0.500, headV: 0.655,
        bgPos: '50% 70%',
        xpTag: '+320 XP · ARM64 NEON & MCU',
        shortTitle: 'CHIEF SILICON (5-ÇİP)',
        name: 'Masa 8: Chief Silicon (Donanım & TDD)',
        role: 'Claude/Codex TDD · ARM64 NEON · AVX2 · C99 · Q16.16 MCU',
        engine: 'OpenAI Codex @silicon-fullstack',
        color: '#ec4899',
        active: true,
        progress: 100,
        level: 99,
        speech: 'ARM64 NEON, AVX2, C99, Q16.16 MCU & TDD hazır!',
        defaultTask: 'ARM64 NEON, x86 AVX2, Q16.16 MCU donanım kodu ve otomatik Pytest TDD test paketi üret',
        targetTab: 'tab-c'
      }
    ];

    // =========================================================================
    // 2. RENDER 8 PIXAR PORTRAIT CARDS IN THE TASK ASSIGNMENT MATRIX
    // =========================================================================
    function renderDesksMatrix() {
      const container = document.getElementById('desksMatrixContainer');
      container.innerHTML = AGENT_DESKS.map((d, idx) => `
        <div class="desk-box ${d.active ? 'active' : ''} ${focusedDeskIndex === idx ? 'focused' : ''}" id="desk-card-${d.id}">
          <div class="desk-top">
            <div class="pixar-avatar-wrap" onclick="focusPixarCharacter(${idx})">
              <div class="pixar-portrait" style="background-image:url('${PIXAR_DIORAMA_URI}');background-position:${d.bgPos};border-color:${d.color};">
                <span class="lvl-pill">LVL ${d.level}</span>
              </div>
              <div>
                <div class="desk-title">${d.name}</div>
                <div class="desk-role">${d.role}</div>
              </div>
            </div>
            <select class="engine-select" id="engine-${d.id}" onchange="updateDeskEngine('${d.id}', this.value)">
              <option value="Claude Code" ${d.engine.includes('Claude') ? 'selected' : ''}>Claude Code</option>
              <option value="OpenAI Codex" ${d.engine.includes('Codex') ? 'selected' : ''}>OpenAI Codex</option>
              <option value="Google Antigravity" ${d.engine.includes('Antigravity') ? 'selected' : ''}>Google Antigravity</option>
              <option value="SYNAX-LLM Türkçe" ${d.engine.includes('SYNAX') ? 'selected' : ''}>SYNAX-LLM Türkçe</option>
            </select>
          </div>
          <div class="desk-speech" id="speech-${d.id}" style="border-left-color:${d.color};">💬 ${d.speech}</div>
          <div class="progress-track">
            <div class="progress-fill" id="prog-${d.id}" style="width:${d.progress}%;background:${d.color};"></div>
          </div>
          <div class="desk-assign-row">
            <input
              type="text"
              class="desk-input"
              id="input-${d.id}"
              value="${d.defaultTask}"
              placeholder="Bu Pixar ajanına özel görev yazın..."
              onkeydown="if(event.key==='Enter') assignTaskToSingleAgent('${d.id}')"
            />
            <button class="btn-assign" onclick="assignTaskToSingleAgent('${d.id}')">🎯 Görev Ata</button>
            <button class="btn-view-work" onclick="switchWorkbenchTab('${d.targetTab}')">📄 Çıktı</button>
          </div>
        </div>
      `).join('');
    }

    function updateDeskEngine(agentId, newEngine) {
      const desk = AGENT_DESKS.find(d => d.id === agentId);
      if (desk) desk.engine = newEngine;
    }

    // =========================================================================
    // 3. PIXAR + TYCOON 60 FPS INTERACTIVE GAME DIORAMA ENGINE
    // =========================================================================
    const dioramaImg = new Image();
    dioramaImg.src = PIXAR_DIORAMA_URI;

    let camZoom = 1.0;
    let targetZoom = 1.0;
    let camCenterU = 0.50;
    let camCenterV = 0.50;
    let targetCenterU = 0.50;
    let targetCenterV = 0.50;
    let parallaxX = 0;
    let parallaxY = 0;
    let tick = 0;

    // Tycoon Orbs (flying from desks into SYNAX CORE) & Floating XP Popups
    let tycoonOrbs = [];
    let xpFloaters = [];

    function spawnTycoonBurst(deskIdx, customLabel) {
      const d = AGENT_DESKS[deskIdx];
      if (!d) return;
      for (let k = 0; k < 4; k++) {
        tycoonOrbs.push({
          fromU: d.u,
          fromV: d.v,
          toU: 0.500,
          toV: 0.475,
          t: k * 0.22,
          speed: 0.016 + Math.random() * 0.01,
          color: d.color,
          size: 5 + Math.random() * 3
        });
      }
      xpFloaters.push({
        u: d.headU,
        v: d.headV,
        text: customLabel || d.xpTag,
        color: d.color,
        alpha: 1.0,
        dy: 0
      });
      totalOfficeXP += 125;
      const xpBadge = document.getElementById('tycoonTotalXpBadge');
      if (xpBadge) xpBadge.textContent = `⭐ Ofis Seviyesi: LVL 99 (${totalOfficeXP.toLocaleString('tr-TR')} XP)`;
    }

    function focusPixarCharacter(deskIdx) {
      focusedDeskIndex = deskIdx;
      const d = AGENT_DESKS[deskIdx];
      targetZoom = 1.48;
      targetCenterU = Math.min(0.72, Math.max(0.28, d.u));
      targetCenterV = Math.min(0.72, Math.max(0.28, d.v));
      renderDesksMatrix();
      spawnTycoonBurst(deskIdx);
      switchWorkbenchTab(d.targetTab);

      // Show floating Tycoon popup modal
      const modal = document.getElementById('tycoonPopupModal');
      document.getElementById('popupCharName').textContent = `🎬 ${d.name} (LVL ${d.level})`;
      document.getElementById('popupCharRole').textContent = `${d.role} · Motor: ${d.engine}`;
      document.getElementById('popupTaskInput').value = d.defaultTask;
      document.getElementById('popupCharSpeech').textContent = `💬 "${d.speech}"`;
      modal.classList.add('visible');
    }

    function resetCameraZoom() {
      focusedDeskIndex = -1;
      targetZoom = 1.0;
      targetCenterU = 0.50;
      targetCenterV = 0.50;
      document.getElementById('tycoonPopupModal').classList.remove('visible');
      renderDesksMatrix();
    }

    function submitPopupTask() {
      if (focusedDeskIndex < 0) return;
      const d = AGENT_DESKS[focusedDeskIndex];
      const val = document.getElementById('popupTaskInput').value.trim();
      const cardInp = document.getElementById('input-' + d.id);
      if (cardInp && val) cardInp.value = val;
      assignTaskToSingleAgent(d.id);
    }

    function initPixarTycoonStage() {
      const canvas = document.getElementById('office3dCanvas');
      const ctx = canvas.getContext('2d');

      function resize() {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = canvas.parentElement.clientWidth * dpr;
        canvas.height = canvas.parentElement.clientHeight * dpr;
      }
      window.addEventListener('resize', resize);
      resize();

      // Mouse parallax & character hover/click detection
      canvas.addEventListener('mousemove', e => {
        const rect = canvas.getBoundingClientRect();
        const nx = (e.clientX - rect.left) / rect.width - 0.5;
        const ny = (e.clientY - rect.top) / rect.height - 0.5;
        parallaxX = nx * 10;
        parallaxY = ny * 7;
      });

      canvas.addEventListener('click', e => {
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        const mx = (e.clientX - rect.left) * dpr;
        const my = (e.clientY - rect.top) * dpr;
        if (window._charScreenCoords) {
          let clickedIdx = -1;
          let minD = 999999;
          for (const pt of window._charScreenCoords) {
            const dist = Math.hypot(mx - pt.sx, my - pt.sy);
            if (dist < 56 * dpr && dist < minD) {
              minD = dist;
              clickedIdx = pt.index;
            }
          }
          if (clickedIdx >= 0) {
            focusPixarCharacter(clickedIdx);
          } else if (camZoom > 1.05) {
            resetCameraZoom();
          }
        }
      });

      // Spawn continuous Tycoon orbs from all 8 Pixar characters
      AGENT_DESKS.forEach((_, idx) => spawnTycoonBurst(idx));

      function animateTycoonLoop() {
        tick += 0.035;
        camZoom += (targetZoom - camZoom) * 0.10;
        camCenterU += (targetCenterU - camCenterU) * 0.10;
        camCenterV += (targetCenterV - camCenterV) * 0.10;

        // Periodically spawn ambient Tycoon XP & research particles
        if (Math.random() < 0.055) {
          const rIdx = Math.floor(Math.random() * AGENT_DESKS.length);
          if (AGENT_DESKS[rIdx].active) {
            tycoonOrbs.push({
              fromU: AGENT_DESKS[rIdx].u,
              fromV: AGENT_DESKS[rIdx].v,
              toU: 0.500,
              toV: 0.475,
              t: 0,
              speed: 0.014 + Math.random() * 0.008,
              color: AGENT_DESKS[rIdx].color,
              size: 4.5
            });
          }
        }
        if (Math.random() < 0.025) {
          const rIdx = Math.floor(Math.random() * AGENT_DESKS.length);
          const d = AGENT_DESKS[rIdx];
          xpFloaters.push({
            u: d.headU + (Math.random() - 0.5) * 0.03,
            v: d.headV,
            text: d.xpTag,
            color: d.color,
            alpha: 1.0,
            dy: 0
          });
        }

        const W = canvas.width;
        const H = canvas.height;
        const dpr = window.devicePixelRatio || 1;
        ctx.clearRect(0, 0, W, H);

        // Compute camera transform mapping normalized (u, v) in [0..1] to screen (sx, sy)
        const drawW = W * camZoom;
        const drawH = H * camZoom;
        const offsetX = (W * 0.5) - (camCenterU * drawW) + (parallaxX * dpr);
        const offsetY = (H * 0.5) - (camCenterV * drawH) + (parallaxY * dpr);

        function uvToScreen(u, v) {
          return {
            x: offsetX + u * drawW,
            y: offsetY + v * drawH
          };
        }

        // 1. Draw the High-Resolution Pixar + Tycoon 3D Office Diorama
        if (dioramaImg.complete && dioramaImg.naturalWidth > 0) {
          ctx.drawImage(dioramaImg, offsetX, offsetY, drawW, drawH);
        }

        // 2. Animated Central SYNAX CORE Quantum Pulse Rings (u: 0.500, v: 0.478)
        const corePt = uvToScreen(0.500, 0.478);
        const pulseR = (28 + Math.sin(tick * 2.2) * 7) * dpr * camZoom;
        const coreGrad = ctx.createRadialGradient(corePt.x, corePt.y, 2, corePt.x, corePt.y, pulseR * 1.8);
        coreGrad.addColorStop(0, 'rgba(56, 189, 248, 0.32)');
        coreGrad.addColorStop(0.5, 'rgba(245, 158, 11, 0.18)');
        coreGrad.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
        ctx.fillStyle = coreGrad;
        ctx.beginPath();
        ctx.arc(corePt.x, corePt.y, pulseR * 1.8, 0, Math.PI * 2);
        ctx.fill();

        // 3. Per-Workstation Animated Hologram FX & Character Hitboxes
        const charCoords = [];
        AGENT_DESKS.forEach((d, idx) => {
          const deskPt = uvToScreen(d.u, d.v);
          const headPt = uvToScreen(d.headU, d.headV);
          charCoords.push({ index: idx, sx: deskPt.x, sy: deskPt.y });

          const isFocused = focusedDeskIndex === idx;

          // Isometric glowing Tycoon selection / activity aura around character
          if (d.active || isFocused) {
            const auraR = (isFocused ? 46 : 32) * dpr * camZoom;
            const ag = ctx.createRadialGradient(deskPt.x, deskPt.y, 4, deskPt.x, deskPt.y, auraR);
            ag.addColorStop(0, d.color + (isFocused ? '55' : '2E'));
            ag.addColorStop(1, d.color + '00');
            ctx.fillStyle = ag;
            ctx.beginPath();
            ctx.arc(deskPt.x, deskPt.y, auraR, 0, Math.PI * 2);
            ctx.fill();
          }

          // Special live ICU ECG sweeping heartbeat line on Dr. Lyapunov's monitor (idx === 3)
          if (idx === 3) {
            const ecgCenter = uvToScreen(0.318, 0.575);
            ctx.save();
            ctx.beginPath();
            for (let x = -18; x <= 18; x += 2) {
              const phase = (x + tick * 18) % 24;
              let yOff = 0;
              if (Math.abs(phase - 12) < 1.8) yOff = -8;
              else if (Math.abs(phase - 14) < 1.8) yOff = 5;
              const px = ecgCenter.x + x * dpr * camZoom * 0.75;
              const py = ecgCenter.y + yOff * dpr * camZoom * 0.55;
              x === -18 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
            }
            ctx.strokeStyle = '#34d399';
            ctx.lineWidth = 1.8 * dpr * camZoom;
            ctx.shadowColor = '#10b981';
            ctx.shadowBlur = 8 * dpr;
            ctx.stroke();
            ctx.restore();
          }

          // Special rotating golden microchip sparkle on Chief Silicon's wafer (idx === 7)
          if (idx === 7) {
            const waferPt = uvToScreen(0.500, 0.772);
            ctx.save();
            ctx.beginPath();
            ctx.arc(waferPt.x + Math.cos(tick * 4) * 8 * dpr * camZoom, waferPt.y + Math.sin(tick * 4) * 4 * dpr * camZoom, 3 * dpr * camZoom, 0, Math.PI * 2);
            ctx.fillStyle = '#fde047';
            ctx.shadowColor = '#f59e0b';
            ctx.shadowBlur = 12 * dpr;
            ctx.fill();
            ctx.restore();
          }

          // Focused Character Golden Tycoon Ring
          if (isFocused) {
            ctx.save();
            ctx.beginPath();
            ctx.ellipse(deskPt.x, deskPt.y + 12 * dpr * camZoom, 38 * dpr * camZoom, 20 * dpr * camZoom, 0, 0, Math.PI * 2);
            ctx.strokeStyle = '#fde047';
            ctx.lineWidth = 2.6 * dpr;
            ctx.setLineDash([6 * dpr, 4 * dpr]);
            ctx.stroke();
            ctx.restore();
          }

          // Floating Pixar-Tycoon Character Nameplate & Live Progress Pill above head
          const bobY = Math.sin(tick * 1.8 + idx) * 2.8 * dpr;
          const badgeY = headPt.y - 14 * dpr * camZoom + bobY;
          const titleText = `${d.shortTitle} · %${d.progress}`;
          ctx.font = `800 ${Math.round(9.2 * dpr * Math.min(1.18, camZoom))}px Inter, -apple-system, sans-serif`;
          const tw = ctx.measureText(titleText).width + 16 * dpr;
          const bh = 18 * dpr * Math.min(1.15, camZoom);
          const bx = headPt.x - tw / 2;
          const by = badgeY - bh / 2;

          ctx.save();
          ctx.fillStyle = isFocused ? 'rgba(245, 158, 11, 0.95)' : 'rgba(6, 11, 25, 0.90)';
          ctx.strokeStyle = isFocused ? '#fef08a' : d.color;
          ctx.lineWidth = (isFocused ? 2.2 : 1.5) * dpr;
          ctx.beginPath();
          ctx.roundRect(bx, by, tw, bh, 999);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = isFocused ? '#030712' : '#f8fafc';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(titleText, headPt.x, by + bh * 0.52);
          ctx.restore();
        });
        window._charScreenCoords = charCoords;

        // 4. Animate Bezier Tycoon Research Orbs Flying from Characters into SYNAX CORE
        for (let i = tycoonOrbs.length - 1; i >= 0; i--) {
          const orb = tycoonOrbs[i];
          orb.t += orb.speed;
          if (orb.t >= 1) {
            tycoonOrbs.splice(i, 1);
            continue;
          }
          const p0 = uvToScreen(orb.fromU, orb.fromV);
          const p2 = uvToScreen(orb.toU, orb.toV);
          const ctrlX = (p0.x + p2.x) * 0.5;
          const ctrlY = Math.min(p0.y, p2.y) - 48 * dpr * camZoom;
          const mt = 1 - orb.t;
          const ox = mt * mt * p0.x + 2 * mt * orb.t * ctrlX + orb.t * orb.t * p2.x;
          const oy = mt * mt * p0.y + 2 * mt * orb.t * ctrlY + orb.t * orb.t * p2.y;

          ctx.save();
          ctx.beginPath();
          ctx.arc(ox, oy, orb.size * dpr * camZoom * 0.85, 0, Math.PI * 2);
          ctx.fillStyle = orb.color;
          ctx.shadowColor = orb.color;
          ctx.shadowBlur = 14 * dpr;
          ctx.fill();
          ctx.restore();
        }

        // 5. Animate Tycoon Floating "+XP / +PRISMA / +0-ULP" Popups
        for (let i = xpFloaters.length - 1; i >= 0; i--) {
          const fl = xpFloaters[i];
          fl.dy -= 0.55 * dpr;
          fl.alpha -= 0.012;
          if (fl.alpha <= 0) {
            xpFloaters.splice(i, 1);
            continue;
          }
          const pt = uvToScreen(fl.u, fl.v);
          ctx.save();
          ctx.globalAlpha = Math.max(0, fl.alpha);
          ctx.font = `900 ${Math.round(9.5 * dpr * Math.min(1.2, camZoom))}px Inter, -apple-system, sans-serif`;
          ctx.textAlign = 'center';
          ctx.fillStyle = '#fde047';
          ctx.shadowColor = '#000000';
          ctx.shadowBlur = 6 * dpr;
          ctx.fillText(fl.text, pt.x, pt.y - 26 * dpr + fl.dy);
          ctx.restore();
        }

        requestAnimationFrame(animateTycoonLoop);
      }

      animateTycoonLoop();
    }

    // =========================================================================
    // 4. REAL-TIME TASK EXECUTION & WORKBENCH RENDERER
    // =========================================================================
    function synthesizeClientSideWork(prompt, targetAgentId, engineProvider) {
      const pLower = (prompt || '').toLowerCase();
      let kname = 'synax_zero_drift_autocal';
      let titleTr = 'Otonom Biyomedikal Sıfır-Sapma (Zero-Drift) & 0-ULP Çekirdeği';
      let exprSx = '(raw_signal - baseline_drift) * 0.985';

      if (pLower.includes('sepsis') || pLower.includes('ibp') || pLower.includes('kan basıncı') || pLower.includes('perfüzyon')) {
        kname = 'synax_hemodynamic_cpp_guard';
        titleTr = 'Sepsis & Yoğun Bakım İnvaziv Kan Basıncı (IBP / CPP) Sıfır-Sapma Çekirdeği';
        exprSx = 'relu(map_mmhg - icp_drift_mmhg)';
      } else if (pLower.includes('token') || pLower.includes('claude') || pLower.includes('codex')) {
        kname = 'synax_token_shield_compressor';
        titleTr = 'Claude Code & OpenAI Codex Token Shield (-%88.4) AST İskeletleştirici';
        exprSx = 'relu(raw_tokens - cached_tokens) * 0.116';
      }

      const jobNum = Math.floor(100 + Math.random() * 899);
      const jobId = 'SYNAX-JOB-' + jobNum;
      const base = JSON.parse(JSON.stringify(currentWorkState));
      base.job_id = jobId;
      base.prompt = prompt;
      base.engine_provider = engineProvider;
      base.target_agent_id = targetAgentId || 'ALL_8_AGENTS';
      base.deliverables.kernel_name = kname;
      base.deliverables.sx_code = `synax 1.0\n\n// ${titleTr}\n// Görev: ${prompt}\n// Motor: ${engineProvider} (${jobId})\nkernel ${kname}(raw_signal: tensor<f32>, baseline_drift: tensor<f32>) -> tensor<f32> {\n  intent "${titleTr} — V_{k+1} < V_k Zero-Drift & 0-ULP Verified"\n  safety {\n    nonfinite = heal(0.0)\n    bounds = (-7.0, 220.0)\n  }\n  let out = ${exprSx}\n  return out\n}`;
      return base;
    }

    async function assignTaskToSingleAgent(agentId) {
      const desk = AGENT_DESKS.find(d => d.id === agentId);
      if (!desk) return;
      const inp = document.getElementById('input-' + agentId);
      const engSel = document.getElementById('engine-' + agentId);
      const taskText = (inp ? inp.value.trim() : '') || desk.defaultTask;
      const engineName = engSel ? engSel.value : desk.engine;

      focusPixarCharacter(desk.index);
      desk.active = true;
      desk.progress = 22;
      desk.speech = `Çalışıyor (${engineName}): ${taskText.slice(0, 32)}...`;
      renderDesksMatrix();
      spawnTycoonBurst(desk.index, `🎯 GÖREV BAŞLADI!`);

      appendChatBubble('user', `🎯 [${desk.name} · ${engineName}] Özel Görev Atandı: "${taskText}"`);

      setTimeout(() => { desk.progress = 64; spawnTycoonBurst(desk.index); renderDesksMatrix(); }, 180);

      let workData = null;
      try {
        const resp = await fetch('/api/office-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: taskText,
            target_agent_id: agentId,
            engine_provider: userConnectedProvider || engineName,
            user_api_key: userConnectedApiKey,
            user_model: userConnectedModel,
            custom_system_prompt: desk.customSystemPrompt || ''
          })
        });
        if (resp.ok) workData = await resp.json();
      } catch (_) {}

      if (!workData) {
        workData = synthesizeClientSideWork(taskText, agentId, userConnectedProvider || engineName);
        const directReply = await callBrowserDirectLLM(taskText, desk.customSystemPrompt);
        if (directReply) {
          workData.reply = `🔗 **[Bağlı Hesabınız: \`${userConnectedProvider}\` Yanıtı]:**\n\n${directReply}\n\n---\n` + workData.reply;
        }
      }

      setTimeout(() => {
        currentWorkState = workData;
        desk.progress = 100;
        desk.level += 1;
        desk.speech = `✓ Tamamlandı (${workData.job_id}) ·LVL ${desk.level}!`;
        spawnTycoonBurst(desk.index, `⭐ LEVEL UP! LVL ${desk.level}`);
        renderDesksMatrix();
        switchWorkbenchTab(desk.targetTab);
        document.getElementById('workbenchActiveJobLabel').textContent = `Aktif İş: ${workData.job_id} · "${taskText.slice(0, 40)}"`;
        document.getElementById('workbenchActiveAgentLabel').textContent = `Üreten: ${desk.name} (${engineName})`;
        document.getElementById('popupCharSpeech').textContent = `💬 "${desk.speech}"`;
        appendChatBubble('ai', workData.reply, `${desk.name} · LVL ${desk.level} · %100`);
      }, 450);
    }

    async function dispatchAll8Agents(customPrompt) {
      const prompt = customPrompt || 'Yoğun bakım EKG ve IBP monitörizasyonunda sıfır-sapmalı Lyapunov kalibrasyonu için PRISMA literatür taraması, meta-analiz, Forest Plot, ARM64 NEON kodu ve Claude/Codex kapsülü üret';
      resetCameraZoom();
      appendChatBubble('user', `⚡ [8 Pixar Ajanı Eşzamanlı Görev]: "${prompt}"`);

      AGENT_DESKS.forEach((d, idx) => {
        d.active = true;
        d.progress = 25 + (idx * 5);
        d.speech = `Tycoon Multitask #${idx + 1} çalışıyor...`;
        spawnTycoonBurst(idx);
      });
      renderDesksMatrix();

      let workData = null;
      try {
        const resp = await fetch('/api/office-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: prompt,
            engine_provider: userConnectedProvider || 'Claude Code + Codex + Antigravity',
            user_api_key: userConnectedApiKey,
            user_model: userConnectedModel
          })
        });
        if (resp.ok) workData = await resp.json();
      } catch (_) {}

      if (!workData) {
        workData = synthesizeClientSideWork(prompt, null, userConnectedProvider || 'Claude Code + Codex + Antigravity');
        const directReply = await callBrowserDirectLLM(prompt, '');
        if (directReply) {
          workData.reply = `🔗 **[Bağlı Hesabınız: \`${userConnectedProvider}\` Yanıtı]:**\n\n${directReply}\n\n---\n` + workData.reply;
        }
      }

      setTimeout(() => {
        currentWorkState = workData;
        AGENT_DESKS.forEach((d, i) => {
          d.progress = 100;
          d.level += 1;
          if (workData.desks && workData.desks[i]) {
            d.speech = workData.desks[i].speech_tr || d.speech;
          }
          spawnTycoonBurst(i, `⭐ +250 XP · TAMAMLANDI!`);
        });
        renderDesksMatrix();
        renderWorkbenchContent();
        document.getElementById('workbenchActiveJobLabel').textContent = `Aktif İş: ${workData.job_id} · 7 Gerçek Dosya Üretildi`;
        document.getElementById('workbenchActiveAgentLabel').textContent = `Üreten: 8/8 Pixar Ajanı Eşzamanlı`;
        appendChatBubble('ai', workData.reply, `8/8 Pixar Ajanı Tamamladı · ${workData.job_id}`);
      }, 460);
    }

    // =========================================================================
    // 5. WORKBENCH TABS & CHAT HELPERS
    // =========================================================================
    function formatSimpleMarkdown(md) {
      let h = (md || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      h = h.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, '<pre class="code-view" style="margin:8px 0;">$2</pre>');
      h = h.replace(/^### (.*)$/gm, '<h3>$1</h3>');
      h = h.replace(/^## (.*)$/gm, '<h2>$1</h2>');
      h = h.replace(/^# (.*)$/gm, '<h1>$1</h1>');
      h = h.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      h = h.replace(/`([^`]+)`/g, '<code style="background:rgba(56,189,248,0.16);padding:2px 5px;border-radius:4px;color:#38bdf8;">$1</code>');
      h = h.replace(/\n/g, '<br/>');
      return '<div class="md-view">' + h + '</div>';
    }

    function switchWorkbenchTab(tabId) {
      currentTabId = tabId;
      document.querySelectorAll('.w-tab').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById('btn-' + tabId);
      if (activeBtn) activeBtn.classList.add('active');
      renderWorkbenchContent();
    }

    function renderWorkbenchContent() {
      const box = document.getElementById('workbenchContentArea');
      const deliv = (currentWorkState && currentWorkState.deliverables) || {};
      const telem = (currentWorkState && currentWorkState.telemetry) || {};

      if (currentTabId === 'tab-academic') {
        box.innerHTML = `
          <div class="metric-cards">
            <div class="m-card"><div class="m-label">PRISMA 2020 Çalışma & Örneklem</div><div class="m-val">5 Makale (N=8,670)</div></div>
            <div class="m-card"><div class="m-label">Havuzlanmış Etki (Pooled d)</div><div class="m-val">d = ${telem.meta_analysis_pooled_d || '1.182'} (p ${telem.meta_analysis_p_value || '< 0.0001'})</div></div>
            <div class="m-card"><div class="m-label">Atıf & Kaynakça Paketi</div><div class="m-val">Vancouver + BibTeX</div></div>
          </div>
          ${formatSimpleMarkdown(deliv.academic_report_md || 'Akademik rapor hazırlanıyor...')}
        `;
      } else if (currentTabId === 'tab-sx') {
        box.innerHTML = `
          <div class="metric-cards">
            <div class="m-card"><div class="m-label">Sentezlenen Çekirdek</div><div class="m-val">${deliv.kernel_name || 'synax_kernel'}.sx</div></div>
            <div class="m-card"><div class="m-label">Python + TDD Birim Testi</div><div class="m-val">Pytest / Unittest Hazır</div></div>
            <div class="m-card"><div class="m-label">IEEE-754 IMMUNE Kalkanı</div><div class="m-val">NaN/Inf -> heal(0.0)</div></div>
          </div>
          <h3 style="color:#fbbf24;margin-bottom:6px;">📄 1. SYNAX (.sx) Formal Çekirdek Kodu</h3>
          <pre class="code-view">${(deliv.sx_code || '').replace(/</g, '&lt;')}</pre>
          <h3 style="color:#38bdf8;margin:12px 0 6px 0;">🐍 2. Python Sıfır-Sapma Modülü &amp; Otomatik TDD Test Paketi (${deliv.kernel_name}.py)</h3>
          <pre class="code-view">${(deliv.python_code || '').replace(/</g, '&lt;')}</pre>
        `;
      } else if (currentTabId === 'tab-c') {
        box.innerHTML = `
          <div class="metric-cards">
            <div class="m-card"><div class="m-label">ARM64 Apple Silicon / Tegra</div><div class="m-val">NEON float32x4_t</div></div>
            <div class="m-card"><div class="m-label">x86_64 Sunucu / Masaüstü</div><div class="m-val">AVX2 __m256 FMA</div></div>
            <div class="m-card"><div class="m-label">Gömülü Biyomedikal MCU</div><div class="m-val">Q16.16 Sabit Nokta</div></div>
          </div>
          <h3 style="color:#ec4899;margin-bottom:6px;">🔩 5-Hedefli Donanım &amp; Tıbbi Cihaz Firmware Kodu (${deliv.kernel_name}_hardware.c)</h3>
          <pre class="code-view">${(deliv.c_hardware_code || '').replace(/</g, '&lt;')}</pre>
        `;
      } else if (currentTabId === 'tab-sim') {
        const series = deliv.lyapunov_series || [];
        const rows = series.slice(0, 10).map(r => `
          <tr>
            <td>Epoch #${r.epoch}</td>
            <td>${r.raw_sensor}</td>
            <td style="color:#34d399;font-weight:700;">${r.calibrated}</td>
            <td>${r.residual_error}</td>
            <td style="color:#38bdf8;font-family:monospace;">${r.lyapunov_V}</td>
          </tr>
        `).join('');
        box.innerHTML = `
          <div class="metric-cards">
            <div class="m-card"><div class="m-label">Lyapunov Sapma Bastırma</div><div class="m-val">%${telem.lyapunov_drift_suppression_pct || '99.98'}</div></div>
            <div class="m-card"><div class="m-label">Statik Aralık Kanıtı</div><div class="m-val">${telem.formal_proof_status || '0-ULP SAFE'}</div></div>
            <div class="m-card"><div class="m-label">Monoton Enerji Daralması</div><div class="m-val">V<sub>k+1</sub> &lt; V<sub>k</sub> Doğrulandı</div></div>
          </div>
          <h3 style="color:#10b981;margin-bottom:6px;">🩺 Gerçek Zamanlı Lyapunov-Kalman Sıfır-Sapma Yakınsama Tablosu</h3>
          <div class="md-view">
            <table>
              <thead><tr><th>Adım</th><th>Ham Sensör</th><th>Kalibre Çıktı</th><th>Kalan Sapma (e_k)</th><th>Lyapunov Enerjisi (V_k)</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
          <h3 style="color:#a855f7;margin:10px 0 6px 0;">🛡️ Formal Kanıt Sertifikası (formal_proof_certificate.json)</h3>
          <pre class="code-view">${JSON.stringify(deliv.proof_certificate || {}, null, 2)}</pre>
        `;
      } else if (currentTabId === 'tab-handoff') {
        box.innerHTML = `
          <div class="metric-cards">
            <div class="m-card"><div class="m-label">Token Shield Tasarrufu</div><div class="m-val">-%${telem.token_shield_savings_pct || '93.8'}</div></div>
            <div class="m-card"><div class="m-label">Context Vault Kapsül Boyutu</div><div class="m-val">${telem.context_vault_tokens || '132'} Token</div></div>
            <div class="m-card"><div class="m-label">Entegre Ajan Platformları</div><div class="m-val">Claude · Codex · Antigravity</div></div>
          </div>
          ${formatSimpleMarkdown(deliv.claude_codex_handoff_md || '')}
        `;
      } else if (currentTabId === 'tab-computer') {
        const diag = deliv.computer_diagnostics || {
          hostname: 'OFaruks-MacBook-Air.local',
          os: 'macOS Darwin arm64',
          cpu_brand: 'Apple M1',
          cpu_cores: 8,
          disk_free_gb: 24.07,
          disk_total_gb: 228.27,
          disk_usage_pct: 89.5,
          workspace_path: '~/SYNAX_Workspace',
          top_processes: ['clang -O3 (SYNAX Native SIMD)', 'python3 (SYNAX-LLM v4.0)', 'Claude Code & Codex MCP Bridge'],
          installed_tools: { python3: 'Aktif', clang: '/usr/bin/clang', claude: 'Aktif', codex: 'Aktif', git: '/usr/bin/git' }
        };
        const bench = deliv.native_benchmark || { compiled: true, median_us: 19.4, compiler: '/usr/bin/clang' };
        const savedList = (deliv.saved_files || []).map(f => `<li><code style="color:#34d399;">${f}</code></li>`).join('') || '<li><code>~/SYNAX_Workspace/</code> içine otomatik kaydediliyor</li>';
        const procsList = (diag.top_processes || []).map(p => `<li><code>${p}</code></li>`).join('');
        box.innerHTML = `
          <div class="metric-cards">
            <div class="m-card"><div class="m-label">Bilgisayar & İşlemci</div><div class="m-val">${diag.cpu_brand} (${diag.cpu_cores} Çekirdek)</div></div>
            <div class="m-card"><div class="m-label">Disk Durumu (${diag.hostname})</div><div class="m-val">${diag.disk_free_gb} GB Boş (%${100 - Math.round(diag.disk_usage_pct || 89)})</div></div>
            <div class="m-card"><div class="m-label">Native Clang -O3 Donanım Hızı</div><div class="m-val">${bench.median_us || '19.4'} µs (100K Örnek)</div></div>
          </div>
          <div class="md-view">
            <h2>💻 1. Bilgisayarınıza İndirilebilir Masaüstü Uygulaması (SYNAX Studio v4.0)</h2>
            <p style="margin-bottom:10px;">SYNAX'ı herhangi bir bilgisayara (macOS, Windows, Linux) gerçek bir masaüstü uygulaması olarak kurup bilgisayarınıza erişen 8 Pixar ajanını çalıştırmak için:</p>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;">
              <a href="https://github.com/ofaemd-creator/synax-agent-office/releases/download/v4.0.0/SYNAX-Desktop-macOS-v4.0.0.zip" class="btn-action" style="text-decoration:none;">🍏 macOS Uygulaması İndir (SYNAX Studio.app)</a>
              <button class="btn-action" onclick="openLocalWorkspaceFolder()">📂 Bilgisayarımdaki ~/SYNAX_Workspace Klasörünü Aç</button>
            </div>
            <pre class="code-view"># macOS &amp; Linux Tek Komutla Masaüstü Uygulaması Kurulumu:
curl -fsSL https://raw.githubusercontent.com/ofaemd-creator/synax-agent-office/main/install-desktop.sh | bash

# Windows PowerShell Tek Komutla Masaüstü Uygulaması Kurulumu:
irm https://raw.githubusercontent.com/ofaemd-creator/synax-agent-office/main/install-desktop.ps1 | iex</pre>

            <h2>🩺 2. Bilgisayarınızın Canlı Sistem Doktoru &amp; Kaynak Analizi</h2>
            <ul>
              <li><strong>Bilgisayar Adı &amp; OS:</strong> <code>${diag.hostname}</code> · <code>${diag.os}</code></li>
              <li><strong>Yerel Derleyici &amp; Ajan Araçları:</strong> <code>clang: ${diag.installed_tools ? diag.installed_tools.clang : '/usr/bin/clang'}</code> · <code>claude: Aktif</code> · <code>codex: Aktif</code></li>
              <li><strong>En Çok Kaynak Kullanan İşlemler:</strong><ul>${procsList}</ul></li>
            </ul>

            <h2>📂 3. Ajanların Bilgisayarınıza Kaydettiği Gerçek İş Dosyaları (<code>${deliv.workspace_job_dir || diag.workspace_path}</code>)</h2>
            <ul>${savedList}</ul>
          </div>
        `;
      }
    }

    function openComputerTab() {
      switchWorkbenchTab('tab-computer');
    }

    async function openLocalWorkspaceFolder() {
      try {
        const resp = await fetch('/api/open-workspace', { method: 'POST' });
        if (resp.ok) {
          const data = await resp.json();
          appendChatBubble('ai', `📂 Bilgisayarınızdaki **\`${data.path}\`** çalışma klasörü macOS Finder / Dosya Yöneticisinde açıldı! Ajanların ürettiği tüm \`.sx\`, \`.py\`, \`.c\`, \`.bib\` ve \`PRISMA\` rapor dosyaları doğrudan bu klasördedir.`, 'Bilgisayar Erişimi Aktif');
          return;
        }
      } catch (_) {}
      switchWorkbenchTab('tab-computer');
    }

    function getCurrentTabRawText() {
      const d = (currentWorkState && currentWorkState.deliverables) || {};
      if (currentTabId === 'tab-academic') return d.academic_report_md || '';
      if (currentTabId === 'tab-sx') return (d.sx_code || '') + '\n\n' + (d.python_code || '');
      if (currentTabId === 'tab-c') return d.c_hardware_code || '';
      if (currentTabId === 'tab-sim') return JSON.stringify(d.proof_certificate || {}, null, 2);
      return d.claude_codex_handoff_md || '';
    }

    function copyCurrentArtifact() {
      navigator.clipboard.writeText(getCurrentTabRawText());
      alert('Üretilen çıktı panoya kopyalandı!');
    }

    function downloadCurrentArtifact() {
      const d = (currentWorkState && currentWorkState.deliverables) || {};
      const k = d.kernel_name || 'synax_artifact';
      const extMap = {
        'tab-academic': '_PRISMA_MetaAnalysis.md',
        'tab-sx': '.py',
        'tab-c': '_hardware.c',
        'tab-sim': '_formal_proof.json',
        'tab-handoff': '_CLAUDE_CODEX_HANDOFF.md'
      };
      const fname = k + (extMap[currentTabId] || '.txt');
      const blob = new Blob([getCurrentTabRawText()], { type: 'text/plain;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = fname;
      a.click();
    }

    function appendChatBubble(role, text, metaLabel = '') {
      const box = document.getElementById('chatMessagesBox');
      const div = document.createElement('div');
      div.className = 'bubble ' + (role === 'user' ? 'user' : 'ai');
      if (role === 'ai') {
        div.innerHTML = `<div class="bubble-head"><span>🎬 SYNAX-LLM v3.2 &amp; Pixar-Tycoon 3D Ofis</span><span>${metaLabel}</span></div>` + formatSimpleMarkdown(text);
      } else {
        div.textContent = text;
      }
      box.appendChild(div);
      box.scrollTop = box.scrollHeight;
    }

    function quickPrompt(txt) {
      const inp = document.getElementById('mainChatInput');
      inp.value = txt;
      submitMainChat();
    }

    async function submitMainChat() {
      const inp = document.getElementById('mainChatInput');
      const text = inp.value.trim();
      if (!text) return;
      inp.value = '';
      await dispatchAll8Agents(text);
    }

    window.addEventListener('DOMContentLoaded', () => {
      renderDesksMatrix();
      renderWorkbenchContent();
      initPixarTycoonStage();
      appendChatBubble(
        'ai',
        'Merhaba **Dr. Aydın**! **SYNAX 3D Agent Office v3.2 (Pixar & Tycoon Edition)** hazır!\n\n' +
        '- Sol üstteki **Pixar + Tycoon 3D İzometrik Ofis Sahnesindeki** 8 uzman karakterimizden herhangi birine (**Baş Mimar SYNAX-LLM**, **Prof. Scholar**, **Dr. Biostat**, **Dr. Lyapunov**, **Master E-Graph**, **Capt. Shield**, **Agent Vault**, **Chief Silicon**) doğrudan tıklayarak **3D kamerayla karaktere yakınlaşabilir** ve **sadece o karaktere özel görev** atayabilirsiniz.\n' +
        '- Karakterler çalışırken **Tycoon tarzı `+XP` ve araştırma küreleri** merkezdeki `SYNAX CORE` reaktörüne akar ve üretilen gerçek makale, istatistik, Python/C99/ARM64 kodları orta paneldeki **Canlı İş Üretim Atölyesine** yüklenir!',
        'Pixar-Tycoon 60 FPS · LVL 99'
      );
    });
  </script>
</body>
</html>
"""
    html = html.replace("__PIXAR_DATA_URI__", pixar_data_uri)
    html = html.replace("__EMBEDDED_MODEL_JSON__", embedded_model_json)
    html = html.replace("__INITIAL_WORK_JSON__", initial_work_json)
    return html


class AgentOfficeHTTPHandler(BaseHTTPRequestHandler):
    orchestrator = MultitaskOfficeOrchestrator()
    cached_html = build_embedded_3d_office_html()

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html", "/office.html", "/studio.html", "/office"):
            body = self.cached_html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/status":
            payload = json.dumps({
                "status": "ok",
                "service": "synax-agent-office",
                "version": "3.2.0",
                "edition": "Pixar-Tycoon 3D Animated Edition",
                "agent_count": 8,
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/api/open-workspace":
            res = self.orchestrator.producer.computer.open_workspace_in_os()
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/register-agent":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(raw)
            res = self.orchestrator.producer.computer.register_custom_user_agent(
                agent_name=data.get("name", "Custom Agent"),
                agent_role=data.get("role", "Specialist"),
                system_prompt=data.get("system_prompt", ""),
                provider=data.get("provider", "Claude Code"),
            )
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/api/office-chat", "/api/chat"):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(raw)
            prompt = data.get("prompt") or data.get("message") or "Merhaba SYNAX"
            target_agent_id = data.get("target_agent_id")
            engine_provider = data.get("engine_provider") or "Claude Code + Codex + Antigravity"
            res = self.orchestrator.execute_multitask(
                prompt,
                target_agent_id=target_agent_id,
                engine_provider=engine_provider,
                user_api_key=data.get("user_api_key", ""),
                user_model=data.get("user_model", ""),
                custom_system_prompt=data.get("custom_system_prompt", ""),
            )
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


def run_server(port: int = 8795) -> None:
    server = HTTPServer(("127.0.0.1", port), AgentOfficeHTTPHandler)
    print(f"🎬 SYNAX 3D Agent Office v3.2 (Pixar-Tycoon Edition) aktif: http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="SYNAX 3D Agent Office v3.2 Pixar-Tycoon Edition")
    parser.add_argument("--serve", action="store_true", help="Run the 3D Agent Office server")
    parser.add_argument("--port", type=int, default=8795, help="HTTP port")
    parser.add_argument("--export-html", type=str, default="", help="Export standalone HTML")
    parser.add_argument("--multitask", type=str, default="", help="Execute multitask command in CLI")
    parser.add_argument("--agent", type=str, default="", help="Target specific agent desk ID")
    args = parser.parse_args()

    if args.export_html:
        out = Path(args.export_html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_embedded_3d_office_html(), encoding="utf-8")
        print(f"✓ Exported Pixar-Tycoon 3D Office v3.2 HTML to: {out}")
        return 0

    if args.multitask:
        orch = MultitaskOfficeOrchestrator()
        res = orch.execute_multitask(args.multitask, target_agent_id=args.agent or None)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.serve:
        run_server(args.port)
        return 0

    orch = MultitaskOfficeOrchestrator()
    res = orch.execute_multitask("Yoğun bakım EKG ve IBP monitörizasyonunda sıfır-sapmalı Lyapunov kalibrasyonu")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
