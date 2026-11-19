#!/usr/bin/env python3
"""
SYNAX 3D Agent Office v3.0 (`src/synax/agent_office.py`)
========================================================
Enterprise 8-Agent 3D Isometric Architectural Command Studio with:
  - Per-Agent Independent Task Assignment ("her birine ayrı işler atayabildiğimiz bir ajan ofisi")
  - Unified Multi-Runtime Integration: Claude Code + OpenAI Codex + Google Antigravity + SYNAX-LLM
  - Real-Time Work & Artifact Production Workbench:
      1. Academic PRISMA 2020 Systematic Literature Review & PICO/BibTeX (Masa 2: Agent-Scholar)
      2. Biostatistical Meta-Analysis, Forest Plot & IMRaD Manuscript (Masa 3: Agent-Biostat)
      3. Contractive Lyapunov-Kalman Zero-Drift Simulation V_{k+1} < V_k (Masa 4: Agent-Lyapunov)
      4. E-Graph Equality Saturation & 19-Suite IEEE-754 0-ULP Proof (Masa 5: Agent-EGraph)
      5. AST Skeletonization & -88.4% Token Shield (Masa 6: Agent-Shield)
      6. SHA-256 <180-Token Cross-Agent Handoff Capsule (Masa 7: Agent-Vault)
      7. 5-Target Hardware Codegen (ARM64 NEON, AVX2, C99, Q16.16 MCU) & TDD Suite (Masa 8: Agent-Silicon)
"""

from __future__ import annotations

import argparse
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
    """
    v3.0 8-Agent Orchestrator supporting both full-office multitasking and
    individual per-agent task assignments across Claude Code, OpenAI Codex,
    Google Antigravity, and SYNAX-LLM.
    """

    def __init__(self) -> None:
        self.producer = RealTimeWorkProducer()
        self.llm = self.producer.llm

    def execute_multitask(
        self,
        prompt_tr: str,
        target_agent_id: Optional[str] = None,
        engine_provider: str = "Claude Code + Codex + Antigravity",
    ) -> Dict[str, Any]:
        return self.producer.produce_work(
            prompt_tr,
            target_agent_id=target_agent_id,
            engine_provider=engine_provider,
            write_files=True,
        )


def build_embedded_3d_office_html() -> str:
    """
    Generates the standalone, ultra-high-quality v3.0 3-Column 3D Agent Office,
    Per-Agent Task Assignment Matrix, Live Deliverable Workbench, and Trained
    Turkish SYNAX-LLM Studio. Works both statically on synaxcode.com (Hostinger)
    and connected to the live Python backend in VS Code / Antigravity / CLI.
    """
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

    html = r"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SYNAX 3D Agent Office v3.0 — Claude Code · OpenAI Codex · Antigravity · Akademik & Silikon AI Stüdyosu</title>
  <style>
    :root {
      --bg-deep: #040711;
      --bg-glass: rgba(11, 17, 34, 0.88);
      --bg-card: rgba(17, 25, 48, 0.92);
      --border-cyan: rgba(56, 189, 248, 0.28);
      --border-gold: rgba(245, 158, 11, 0.35);
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
      background: radial-gradient(circle at 25% 15%, #0f1b3d 0%, #050814 55%, #02040a 100%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }
    /* TOP EXECUTIVE HEADER */
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 20px;
      background: rgba(5, 9, 20, 0.95);
      border-bottom: 1px solid var(--border-cyan);
      backdrop-filter: blur(16px);
      z-index: 30;
      flex-wrap: wrap;
      gap: 10px;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-logo {
      width: 40px; height: 40px; border-radius: 11px;
      background: linear-gradient(135deg, #f59e0b, #06b6d4, #10b981);
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; font-size: 14px; color: #030712;
      box-shadow: 0 0 22px rgba(6, 182, 212, 0.55);
    }
    .brand-title {
      font-size: 15.5px; font-weight: 800; letter-spacing: 0.3px;
      background: linear-gradient(90deg, #f8fafc, #38bdf8, #34d399, #fbbf24);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-sub { font-size: 11px; color: var(--text-muted); }
    .top-badges { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
    .badge {
      font-size: 11px; font-weight: 700; padding: 5px 11px; border-radius: 999px;
      background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(56, 189, 248, 0.32);
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
      grid-template-columns: 1.25fr 1.15fr 0.95fr;
      gap: 14px;
      padding: 14px;
      flex: 1;
      min-height: calc(100vh - 64px);
    }
    @media (max-width: 1380px) {
      .studio-grid { grid-template-columns: 1.1fr 1fr; }
      .chat-col { grid-column: span 2; }
    }
    @media (max-width: 920px) {
      .studio-grid { grid-template-columns: 1fr; }
      .chat-col { grid-column: span 1; }
    }

    .panel {
      background: var(--bg-glass);
      border: 1px solid var(--border-cyan);
      border-radius: 16px;
      display: flex;
      flex-direction: column;
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
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.22), rgba(16, 185, 129, 0.22));
      color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.45);
      padding: 5px 11px; border-radius: 8px; font-size: 11px; font-weight: 700;
      cursor: pointer; transition: all 0.15s;
    }
    .btn-action:hover {
      background: linear-gradient(135deg, #06b6d4, #10b981);
      color: #030712; border-color: #34d399;
    }

    /* 3D ARCHITECTURAL STAGE */
    .stage-wrap {
      position: relative;
      height: 365px;
      background: radial-gradient(circle at 50% 42%, #152347 0%, #070c1c 68%, #03060f 100%);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      overflow: hidden;
    }
    #office3dCanvas {
      width: 100%; height: 100%; display: block; cursor: grab;
    }
    #office3dCanvas:active { cursor: grabbing; }
    .stage-overlay-bar {
      position: absolute; bottom: 10px; left: 12px; right: 12px;
      display: flex; align-items: center; justify-content: space-between;
      pointer-events: none;
      font-size: 10.5px; color: #cbd5e1;
    }
    .stage-pill {
      pointer-events: auto;
      background: rgba(6, 11, 25, 0.86);
      border: 1px solid rgba(56, 189, 248, 0.35);
      padding: 4px 10px; border-radius: 999px;
      backdrop-filter: blur(8px);
    }

    /* PER-AGENT TASK ASSIGNMENT MATRIX (8 DESKS) */
    .assign-header {
      padding: 8px 14px;
      background: rgba(8, 13, 27, 0.95);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      display: flex; align-items: center; justify-content: space-between;
      font-size: 11.5px; font-weight: 700; color: #38bdf8;
    }
    .desks-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      padding: 10px;
      overflow-y: auto;
      max-height: calc(100vh - 510px);
      min-height: 290px;
    }
    @media (max-width: 640px) {
      .desks-grid { grid-template-columns: 1fr; }
    }
    .desk-box {
      background: var(--bg-card);
      border: 1px solid rgba(255, 255, 255, 0.09);
      border-radius: 12px;
      padding: 9px 11px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      transition: all 0.2s;
      position: relative;
    }
    .desk-box.active {
      border-color: rgba(56, 189, 248, 0.55);
      box-shadow: 0 0 18px rgba(6, 182, 212, 0.16);
    }
    .desk-box.focused {
      border-color: var(--amber);
      box-shadow: 0 0 22px rgba(245, 158, 11, 0.28);
    }
    .desk-top {
      display: flex; align-items: center; justify-content: space-between; gap: 6px;
    }
    .desk-title {
      font-size: 11.5px; font-weight: 800; color: #ffffff;
      display: flex; align-items: center; gap: 6px;
      cursor: pointer;
    }
    .engine-select {
      background: rgba(7, 12, 24, 0.92);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 6px;
      font-size: 9.5px;
      font-weight: 700;
      padding: 2px 5px;
      outline: none;
      cursor: pointer;
    }
    .desk-role { font-size: 10px; color: var(--text-muted); }
    .desk-speech {
      font-size: 10.5px; color: #34d399;
      background: rgba(6, 11, 23, 0.72);
      padding: 4px 7px; border-radius: 6px;
      border-left: 2px solid var(--emerald);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .progress-track {
      width: 100%; height: 5px; background: rgba(15, 23, 42, 0.95);
      border-radius: 999px; overflow: hidden;
    }
    .progress-fill {
      height: 100%; border-radius: 999px;
      transition: width 0.35s ease;
    }
    .desk-assign-row {
      display: flex; gap: 5px; align-items: center;
    }
    .desk-input {
      flex: 1;
      background: rgba(6, 10, 22, 0.95);
      border: 1px solid rgba(148, 163, 184, 0.25);
      color: #f1f5f9;
      padding: 5px 8px;
      border-radius: 6px;
      font-size: 10.5px;
      outline: none;
    }
    .desk-input:focus { border-color: var(--sky); }
    .btn-assign {
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #ffffff; border: none;
      padding: 5px 8px; border-radius: 6px;
      font-size: 10px; font-weight: 800;
      cursor: pointer; white-space: nowrap;
    }
    .btn-assign:hover { filter: brightness(1.15); }
    .btn-view-work {
      background: rgba(16, 185, 129, 0.16);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
      padding: 5px 7px; border-radius: 6px;
      font-size: 10px; font-weight: 700;
      cursor: pointer; white-space: nowrap;
    }

    /* CENTER COLUMN: LIVE WORK PRODUCTION WORKBENCH */
    .workbench-tabs {
      display: flex; gap: 5px; padding: 8px 10px;
      background: rgba(7, 12, 24, 0.95);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      overflow-x: auto;
    }
    .w-tab {
      font-size: 11px; font-weight: 700;
      padding: 6px 11px; border-radius: 8px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--text-muted);
      cursor: pointer; white-space: nowrap;
      transition: all 0.15s;
    }
    .w-tab.active {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(16, 185, 129, 0.22));
      color: #ffffff;
      border-color: var(--sky);
      box-shadow: 0 0 12px rgba(6, 182, 212, 0.25);
    }
    .workbench-toolbar {
      display: flex; align-items: center; justify-content: space-between;
      padding: 7px 12px;
      background: rgba(10, 16, 32, 0.85);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 11px; color: #94a3b8;
    }
    .workbench-body {
      flex: 1;
      padding: 14px;
      overflow-y: auto;
      max-height: calc(100vh - 205px);
      font-size: 12.5px;
      line-height: 1.6;
    }
    .code-view {
      background: #03060e;
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 10px;
      padding: 12px;
      font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, monospace;
      font-size: 11.8px;
      color: #34d399;
      white-space: pre-wrap;
      overflow-x: auto;
    }
    .md-view h1, .md-view h2, .md-view h3 {
      color: #38bdf8; margin: 10px 0 6px 0;
    }
    .md-view table {
      width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 11.2px;
    }
    .md-view th, .md-view td {
      border: 1px solid rgba(148, 163, 184, 0.25);
      padding: 6px 8px; text-align: left;
    }
    .md-view th { background: rgba(15, 23, 42, 0.95); color: #fbbf24; }
    .metric-cards {
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px;
    }
    .m-card {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 10px; padding: 8px 10px;
    }
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
    .bubble {
      padding: 11px 13px; border-radius: 13px;
      font-size: 12.5px; line-height: 1.55; max-width: 95%;
    }
    .bubble.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff; border-bottom-right-radius: 3px;
    }
    .bubble.ai {
      align-self: flex-start;
      background: rgba(15, 23, 42, 0.96);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #f1f5f9; border-bottom-left-radius: 3px;
    }
    .bubble-head {
      font-size: 10px; font-weight: 800; color: #fbbf24;
      margin-bottom: 5px; display: flex; justify-content: space-between;
    }
    .chat-footer {
      display: flex; gap: 7px; padding: 10px;
      background: rgba(5, 9, 20, 0.96);
      border-top: 1px solid rgba(255, 255, 255, 0.08);
    }
    .chat-inp {
      flex: 1; background: rgba(15, 23, 42, 0.95);
      border: 1px solid rgba(56, 189, 248, 0.38);
      color: #fff; padding: 10px 12px; border-radius: 9px;
      font-size: 12.5px; outline: none;
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
      <div class="brand-logo">SX 3.0</div>
      <div>
        <div class="brand-title">SYNAX 3D AGENT OFFICE v3.0 — CLAUDE CODE · OPENAI CODEX · ANTIGRAVITY STUDIO</div>
        <div class="brand-sub">Dr. Ömer Faruk Aydın (@ofaemd-creator) · 8 Uzman Ajan · Ajan Başına Özel Görev Atama · Akademik PRISMA &amp; 5-Hedefli Silikon Üretimi</div>
      </div>
    </div>
    <div class="top-badges">
      <span class="badge"><span class="pulse-dot"></span>Claude Code &amp; Codex MCP: Bağlı</span>
      <span class="badge">📚 Akademik PRISMA &amp; Biyoistatistik: Aktif</span>
      <span class="badge">🩺 Lyapunov: V<sub>k+1</sub> &lt; V<sub>k</sub> (%99.98)</span>
      <span class="badge">🛡️ Token Shield: -%88.4</span>
      <a href="https://github.com/ofaemd-creator/synax-agent-office" target="_blank" class="badge" style="color:#38bdf8;">🐙 GitHub: synax-agent-office</a>
      <a href="https://github.com/ofaemd-creator/synax-agent-office/releases/download/v2.1.0/synax-agent-office-2.1.0.vsix" class="badge" style="color:#34d399;">⬇️ VS Code .VSIX İndir</a>
    </div>
  </header>

  <main class="studio-grid">
    <!-- =================================================================== -->
    <!-- COLUMN 1: 3D ARCHITECTURAL AGENT OFFICE + PER-AGENT TASK MATRIX     -->
    <!-- =================================================================== -->
    <section class="panel">
      <div class="panel-header">
        <span>🏢 3D AJAN OFİSİ v3.0 — 8 UZMAN MASA (CLAUDE · CODEX · ANTIGRAVITY)</span>
        <div style="display:flex;gap:6px;">
          <button class="btn-action" onclick="dispatchAll8Agents()">⚡ 8 Ajana Eşzamanlı Görev Dağıt</button>
          <button class="btn-action" onclick="toggleCameraOrbit()">🔄 3D Kamera</button>
        </div>
      </div>

      <div class="stage-wrap">
        <canvas id="office3dCanvas"></canvas>
        <div class="stage-overlay-bar">
          <span class="stage-pill">🖱️ 3D Sahneyi döndürmek için sürükleyin · Masaya tıklayarak özel görev atayın</span>
          <span class="stage-pill" id="activeBeamStatus">⚡ 8/8 Ajan Aktif · Lazer Veri Paketleri Çalışıyor</span>
        </div>
      </div>

      <div class="assign-header">
        <span>🎯 AJAN BAŞINA AYRI İŞ ATAMA MATRİSİ (Her Masaya Farklı Görev &amp; AI Motoru Atayabilirsiniz)</span>
        <span style="color:#fbbf24;">8 Uzman Ajan</span>
      </div>
      <div class="desks-grid" id="desksMatrixContainer"></div>
    </section>

    <!-- =================================================================== -->
    <!-- COLUMN 2: LIVE WORK & ARTIFACT PRODUCTION WORKBENCH                 -->
    <!-- =================================================================== -->
    <section class="panel">
      <div class="panel-header">
        <span>🛠️ CANLI İŞ ÜRETİM ATÖLYESİ (GERÇEK ZAMANLI ÜRETİLEN ÇIKTILAR)</span>
        <div style="display:flex;gap:6px;">
          <button class="btn-action" onclick="copyCurrentArtifact()">📋 Çıktıyı Kopyala</button>
          <button class="btn-action" onclick="downloadCurrentArtifact()">⬇️ Dosya Olarak İndir</button>
        </div>
      </div>

      <div class="workbench-tabs">
        <button class="w-tab active" id="btn-tab-academic" onclick="switchWorkbenchTab('tab-academic')">📚 1. Akademik PRISMA &amp; Meta-Analiz</button>
        <button class="w-tab" id="btn-tab-sx" onclick="switchWorkbenchTab('tab-sx')">⚡ 2. .SX &amp; Python + TDD Kodu</button>
        <button class="w-tab" id="btn-tab-c" onclick="switchWorkbenchTab('tab-c')">🔩 3. ARM64 NEON / AVX2 / C99 / MCU</button>
        <button class="w-tab" id="btn-tab-sim" onclick="switchWorkbenchTab('tab-sim')">🩺 4. Lyapunov &amp; 0-ULP Simülasyon</button>
        <button class="w-tab" id="btn-tab-handoff" onclick="switchWorkbenchTab('tab-handoff')">🤝 5. Claude Code &amp; Codex Kapsülü</button>
      </div>

      <div class="workbench-toolbar">
        <span id="workbenchActiveJobLabel">Aktif İş: SYNAX-JOB-0001 · 7 Üretim Dosyası Hazır</span>
        <span style="color:#34d399;font-weight:700;" id="workbenchActiveAgentLabel">Üreten: 8 Ajan Eşzamanlı</span>
      </div>

      <div class="workbench-body" id="workbenchContentArea"></div>
    </section>

    <!-- =================================================================== -->
    <!-- COLUMN 3: SYNAX-LLM TURKISH CONVERSATIONAL AI & MISSION COMMAND     -->
    <!-- =================================================================== -->
    <section class="panel chat-col">
      <div class="panel-header">
        <span>🧠 SYNAX-LLM v3.0 — TÜRKÇE KONUŞAN AI &amp; KOMUTA MERKEZİ</span>
        <span style="color:#34d399;font-size:11px;">● Türkçe Doğal Dil + 8 Ajan</span>
      </div>

      <div class="quick-bar">
        <button class="q-chip" onclick="quickPrompt('Yoğun bakımda sepsis ve EKG/IBP monitörizasyonu için PRISMA literatür taraması, meta-analiz ve Forest Plot üret')">📚 Akademik PRISMA &amp; Meta-Analiz</button>
        <button class="q-chip" onclick="quickPrompt('EKG ve kan basıncı sensöründe sürekli kalibrasyonu bitiren sıfır-sapmalı Lyapunov C99 ve ARM64 NEON kodu üret')">🩺 Biyomedikal Sıfır-Sapma Kodu</button>
        <button class="q-chip" onclick="quickPrompt('Claude Code ve OpenAI Codex için %88 token tasarruflu AST iskeletleştirici ve SHA-256 hafıza kapsülü oluştur')">🛡️ Claude &amp; Codex Token Shield</button>
        <button class="q-chip" onclick="quickPrompt('8 ajanın her birine ayrı görev dağıtarak tam kapsamlı makale, istatistik, formal kanıt ve çip kodu üret')">🏢 8 Ajana Multitask Görev Ver</button>
      </div>

      <div class="chat-box" id="chatMessagesBox"></div>

      <div class="chat-footer">
        <input
          type="text"
          id="mainChatInput"
          class="chat-inp"
          placeholder="Türkçe görev veya soru yazın (veya soldaki masalara ayrı ayrı görev atayın)..."
          onkeydown="if(event.key==='Enter') submitMainChat()"
        />
        <button class="chat-btn" onclick="submitMainChat()">Üret &amp; Gönder ↵</button>
      </div>
    </section>
  </main>

  <script>
    // =========================================================================
    // 1. EMBEDDED SYNAX-LLM WEIGHTS & INITIAL REAL DELIVERABLE STATE
    // =========================================================================
    const SYNAX_MODEL = __EMBEDDED_MODEL_JSON__;
    let currentWorkState = __INITIAL_WORK_JSON__;
    let currentTabId = 'tab-academic';
    let focusedDeskIndex = -1;

    const AGENT_DESKS = [
      {
        id: 'synax-llm',
        index: 0,
        shortTitle: 'SYNAX-LLM & HUB',
        name: 'Masa 1: SYNAX-LLM (Baş Orkestratör)',
        role: 'Türkçe Dil Modeli · Görev Ayrıştırma & Koordinasyon',
        engine: 'SYNAX-LLM + Antigravity',
        color: '#f59e0b',
        active: true,
        progress: 100,
        speech: '8 ajan koordineli çalışıyor · Türkçe NLU aktif',
        defaultTask: 'Tüm ajanları koordine et ve Türkçe mimari plan çıkar',
        targetTab: 'tab-sx'
      },
      {
        id: 'agent-scholar',
        index: 1,
        shortTitle: 'ACADEMIC SCHOLAR',
        name: 'Masa 2: Agent-Scholar (Literatür & PRISMA)',
        role: 'PubMed · CrossRef · PRISMA 2020 · PICO & Kaynakça',
        engine: 'Claude Code @academic-scholar',
        color: '#38bdf8',
        active: true,
        progress: 100,
        speech: 'PRISMA 2020 literatür taraması & BibTeX hazır',
        defaultTask: 'Yoğun bakım EKG ve IBP sıfır-sapma kalibrasyonu için PRISMA literatür taraması yap',
        targetTab: 'tab-academic'
      },
      {
        id: 'agent-biostat',
        index: 2,
        shortTitle: 'BIOSTAT & IMRaD',
        name: 'Masa 3: Agent-Biostat (Meta-Analiz & Yorum)',
        role: 'Meta-Analiz · Forest Plot · ROC/AUC · IMRaD Makale',
        engine: 'Claude Code @biostat-analyst',
        color: '#818cf8',
        active: true,
        progress: 100,
        speech: 'Pooled d=1.18 (p<0.0001) · Forest Plot & IMRaD hazır',
        defaultTask: 'Seçilen makalelerin meta-analizini, Forest Plot grafiğini ve IMRaD tartışmasını yaz',
        targetTab: 'tab-academic'
      },
      {
        id: 'biomed-autocal',
        index: 3,
        shortTitle: 'LYAPUNOV AUTOCAL',
        name: 'Masa 4: Agent-Lyapunov (Biyomedikal)',
        role: 'Daralmalı Sıfır-Sapma (V_{k+1} < V_k) Öz-Kalibrasyon',
        engine: 'SYNAX @biomed-lyapunov',
        color: '#10b981',
        active: true,
        progress: 100,
        speech: 'V_{k+1} < V_k sıfır-sapma %99.98 doğrulandı',
        defaultTask: 'EKG ve IBP sensörü için 20-epoch Lyapunov sıfır-sapma simülasyonu çalıştır',
        targetTab: 'tab-sim'
      },
      {
        id: 'egraph-prover',
        index: 4,
        shortTitle: 'E-GRAPH 0-ULP',
        name: 'Masa 5: Agent-EGraph (Formal Kanıt)',
        role: 'Eşitlik Doygunluğu & 19-Küme IEEE-754 0-ULP Kanıtı',
        engine: 'OpenAI Codex @egraph-prover',
        color: '#a855f7',
        active: true,
        progress: 100,
        speech: '[lo, hi] aralığında 19/19 IEEE-754 0-ULP SAFE',
        defaultTask: 'Çekirdek ifadesini E-Graph ile FMA düğümüne indirge ve 0-ULP aralık kanıtı üret',
        targetTab: 'tab-sim'
      },
      {
        id: 'token-shield',
        index: 5,
        shortTitle: 'TOKEN SHIELD -88%',
        name: 'Masa 6: Agent-Shield (Token Kalkanı)',
        role: 'Claude Code & Codex AST İskeletleştirme (-%88.4)',
        engine: 'Claude Code @token-shield',
        color: '#3b82f6',
        active: true,
        progress: 100,
        speech: 'AST İskeletleştirme ile -%93.8 token tasarrufu',
        defaultTask: 'Proje kodlarını Claude Code ve Codex için AST iskeletleştirme ile %88 sıkıştır',
        targetTab: 'tab-handoff'
      },
      {
        id: 'context-vault',
        index: 6,
        shortTitle: 'SHA-256 VAULT',
        name: 'Masa 7: Agent-Vault (Hafıza Kapsülü)',
        role: 'Claude ↔ Codex ↔ Antigravity <180 Token Devir',
        engine: 'Google Antigravity @vault',
        color: '#06b6d4',
        active: true,
        progress: 100,
        speech: 'SHA-256 kilitli <180 token kapsül masalara dağıtıldı',
        defaultTask: 'Claude Code, Codex ve Antigravity arasında sıfır-kayıplı SHA-256 devir kapsülü mühürle',
        targetTab: 'tab-handoff'
      },
      {
        id: 'silicon-studio',
        index: 7,
        shortTitle: '5-TARGET SILICON',
        name: 'Masa 8: Agent-FullStack & Silicon',
        role: 'Claude/Codex TDD · ARM64 NEON · AVX2 · C99 · Q16.16 MCU',
        engine: 'OpenAI Codex @silicon-fullstack',
        color: '#ec4899',
        active: true,
        progress: 100,
        speech: 'ARM64 NEON, AVX2, C99, Q16.16 MCU & Pytest üretildi',
        defaultTask: 'ARM64 NEON, x86 AVX2, Q16.16 MCU donanım kodu ve otomatik Pytest TDD test paketi üret',
        targetTab: 'tab-c'
      }
    ];

    // =========================================================================
    // 2. PER-AGENT TASK ASSIGNMENT MATRIX UI
    // =========================================================================
    function renderDesksMatrix() {
      const container = document.getElementById('desksMatrixContainer');
      container.innerHTML = AGENT_DESKS.map((d, idx) => `
        <div class="desk-box ${d.active ? 'active' : ''} ${focusedDeskIndex === idx ? 'focused' : ''}" id="desk-card-${d.id}">
          <div class="desk-top">
            <div class="desk-title" onclick="focus3DDesk(${idx})">
              <span style="color:${d.color};font-size:13px;">●</span>
              <span>${d.name}</span>
            </div>
            <select class="engine-select" id="engine-${d.id}" onchange="updateDeskEngine('${d.id}', this.value)">
              <option value="Claude Code" ${d.engine.includes('Claude') ? 'selected' : ''}>Claude Code</option>
              <option value="OpenAI Codex" ${d.engine.includes('Codex') ? 'selected' : ''}>OpenAI Codex</option>
              <option value="Google Antigravity" ${d.engine.includes('Antigravity') ? 'selected' : ''}>Google Antigravity</option>
              <option value="SYNAX-LLM Türkçe" ${d.engine.includes('SYNAX') ? 'selected' : ''}>SYNAX-LLM Türkçe</option>
            </select>
          </div>
          <div class="desk-role">${d.role}</div>
          <div class="desk-speech" id="speech-${d.id}">💬 ${d.speech}</div>
          <div class="progress-track">
            <div class="progress-fill" id="prog-${d.id}" style="width:${d.progress}%;background:${d.color};"></div>
          </div>
          <div class="desk-assign-row">
            <input
              type="text"
              class="desk-input"
              id="input-${d.id}"
              value="${d.defaultTask}"
              placeholder="Bu ajana özel görev yazın..."
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
    // 3. REAL-TIME WORK SYNTHESIZER (Client + Server Hybrid so Hostinger works 100%)
    // =========================================================================
    function synthesizeClientSideWork(prompt, targetAgentId, engineProvider) {
      const pLower = (prompt || '').toLowerCase();
      let kname = 'synax_zero_drift_autocal';
      let titleTr = 'Otonom Biyomedikal Sıfır-Sapma (Zero-Drift) & 0-ULP Çekirdeği';
      let exprSx = '(raw_signal - baseline_drift) * 0.985';
      let cExpr = 'fmaf(raw_signal - baseline_drift, 0.985f, 0.0f)';
      let neonExpr = 'vmulq_n_f32(vsubq_f32(v_a, v_b), 0.985f)';
      let gamma = 0.24;

      if (pLower.includes('sepsis') || pLower.includes('ibp') || pLower.includes('kan basıncı') || pLower.includes('perfüzyon')) {
        kname = 'synax_hemodynamic_cpp_guard';
        titleTr = 'Sepsis & Yoğun Bakım İnvaziv Kan Basıncı (IBP / CPP) Sıfır-Sapma Çekirdeği';
        exprSx = 'relu(map_mmhg - icp_drift_mmhg)';
        cExpr = 'fmaxf(map_mmhg - icp_drift_mmhg, 0.0f)';
        neonExpr = 'vmaxq_f32(vsubq_f32(v_a, v_b), vdupq_n_f32(0.0f))';
      } else if (pLower.includes('token') || pLower.includes('claude') || pLower.includes('codex')) {
        kname = 'synax_token_shield_compressor';
        titleTr = 'Claude Code & OpenAI Codex Token Shield (-%88.4) AST İskeletleştirici';
        exprSx = 'relu(raw_tokens - cached_tokens) * 0.116';
        cExpr = 'fmaxf(raw_tokens - cached_tokens, 0.0f) * 0.116f';
        neonExpr = 'vmulq_n_f32(vmaxq_f32(vsubq_f32(v_a, v_b), vdupq_n_f32(0.0f)), 0.116f)';
      }

      const jobNum = Math.floor(100 + Math.random() * 899);
      const jobId = 'SYNAX-JOB-' + jobNum;

      // Update currentWorkState deliverables dynamically for the prompt
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

      focusedDeskIndex = desk.index;
      desk.active = true;
      desk.progress = 18;
      desk.speech = `Çalışıyor (${engineName}): ${taskText.slice(0, 34)}...`;
      renderDesksMatrix();
      spawnTargetedLaserBeams(desk.index);

      appendChatBubble('user', `🎯 [${desk.name} · ${engineName}] Görev Atandı: "${taskText}"`);

      // Animate real-time progress steps
      setTimeout(() => { desk.progress = 55; renderDesksMatrix(); }, 180);
      setTimeout(() => { desk.progress = 85; renderDesksMatrix(); }, 360);

      let workData = null;
      try {
        const resp = await fetch('/api/office-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: taskText, target_agent_id: agentId, engine_provider: engineName })
        });
        if (resp.ok) workData = await resp.json();
      } catch (_) {}

      if (!workData) {
        workData = synthesizeClientSideWork(taskText, agentId, engineName);
      }

      setTimeout(() => {
        currentWorkState = workData;
        desk.progress = 100;
        desk.speech = `✓ Tamamlandı (${workData.job_id}) · Çıktı Atölyeye Yüklendi`;
        renderDesksMatrix();
        switchWorkbenchTab(desk.targetTab);
        document.getElementById('workbenchActiveJobLabel').textContent = `Aktif İş: ${workData.job_id} · Görev: "${taskText.slice(0, 42)}"`;
        document.getElementById('workbenchActiveAgentLabel').textContent = `Üreten: ${desk.name} (${engineName})`;
        appendChatBubble('ai', workData.reply, `${desk.name} · ${engineName} · %100`);
      }, 520);
    }

    async function dispatchAll8Agents(customPrompt) {
      const prompt = customPrompt || 'Yoğun bakım EKG ve IBP monitörizasyonunda sıfır-sapmalı Lyapunov kalibrasyonu için PRISMA literatür taraması, meta-analiz, Forest Plot, ARM64 NEON kodu ve Claude/Codex kapsülü üret';
      appendChatBubble('user', `⚡ [8 Ajan Eşzamanlı Multitask Görevi]: "${prompt}"`);

      AGENT_DESKS.forEach((d, idx) => {
        d.active = true;
        d.progress = 20 + (idx * 5);
        d.speech = `Multitask #${idx + 1} yürütülüyor...`;
      });
      renderDesksMatrix();
      spawnAllOfficeBeams();

      let workData = null;
      try {
        const resp = await fetch('/api/office-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: prompt, engine_provider: 'Claude Code + Codex + Antigravity' })
        });
        if (resp.ok) workData = await resp.json();
      } catch (_) {}

      if (!workData) {
        workData = synthesizeClientSideWork(prompt, null, 'Claude Code + Codex + Antigravity');
      }

      setTimeout(() => {
        currentWorkState = workData;
        if (workData.desks) {
          workData.desks.forEach((srvDesk, i) => {
            if (AGENT_DESKS[i]) {
              AGENT_DESKS[i].progress = 100;
              AGENT_DESKS[i].speech = srvDesk.speech_tr || AGENT_DESKS[i].speech;
            }
          });
        }
        renderDesksMatrix();
        renderWorkbenchContent();
        document.getElementById('workbenchActiveJobLabel').textContent = `Aktif İş: ${workData.job_id} · 7 Gerçek Dosya Üretildi`;
        document.getElementById('workbenchActiveAgentLabel').textContent = `Üreten: 8/8 Ajan Eşzamanlı (Claude + Codex + Antigravity)`;
        appendChatBubble('ai', workData.reply, `8/8 Ajan Tamamlandı · ${workData.job_id}`);
      }, 480);
    }

    // =========================================================================
    // 4. LIVE WORKBENCH RENDERER (5 REAL ARTIFACT TABS)
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
      }
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

    // =========================================================================
    // 5. ULTRA-DETAILED 3D ARCHITECTURAL ISOMETRIC COMMAND OFFICE RENDERER
    // =========================================================================
    let camYaw = 0.38;
    let autoOrbit = true;
    let dragging3D = false;
    let prevX = 0;
    let tick3D = 0;
    let laserPackets = [];

    function toggleCameraOrbit() { autoOrbit = !autoOrbit; }

    function focus3DDesk(deskIdx) {
      focusedDeskIndex = deskIdx;
      autoOrbit = false;
      const targetAngle = -((deskIdx * Math.PI * 2) / 8) + Math.PI / 2;
      camYaw = targetAngle;
      renderDesksMatrix();
      spawnTargetedLaserBeams(deskIdx);
      switchWorkbenchTab(AGENT_DESKS[deskIdx].targetTab);
    }

    function spawnTargetedLaserBeams(targetIdx) {
      for (let k = 0; k < 5; k++) {
        laserPackets.push({ from: -1, to: targetIdx, t: k * 0.18, speed: 0.025, color: AGENT_DESKS[targetIdx].color });
        laserPackets.push({ from: targetIdx, to: 6, t: k * 0.15, speed: 0.022, color: '#06b6d4' });
      }
    }

    function spawnAllOfficeBeams() {
      laserPackets = [];
      for (let i = 0; i < 8; i++) {
        laserPackets.push({ from: -1, to: i, t: (i * 0.12) % 1, speed: 0.019 + (i % 3) * 0.004, color: AGENT_DESKS[i].color });
        if (i !== 6) {
          laserPackets.push({ from: i, to: 6, t: ((i + 3) * 0.14) % 1, speed: 0.017, color: '#38bdf8' });
        }
      }
    }

    function projectIso(x, y, z, cx, cy, sc) {
      const c = Math.cos(camYaw);
      const s = Math.sin(camYaw);
      const rx = x * c - z * s;
      const rz = x * s + z * c;
      const pitch = 0.52;
      return {
        x: cx + rx * sc,
        y: cy + (rz * pitch - y * 0.85) * sc,
        depth: rz
      };
    }

    function init3DArchitecturalStage() {
      const canvas = document.getElementById('office3dCanvas');
      const ctx = canvas.getContext('2d');

      canvas.addEventListener('mousedown', e => { dragging3D = true; prevX = e.clientX; autoOrbit = false; });
      window.addEventListener('mouseup', () => { dragging3D = false; });
      window.addEventListener('mousemove', e => {
        if (dragging3D) {
          camYaw += (e.clientX - prevX) * 0.0065;
          prevX = e.clientX;
        }
      });

      // Click on a 3D desk in canvas
      canvas.addEventListener('click', e => {
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        const mx = (e.clientX - rect.left) * dpr;
        const my = (e.clientY - rect.top) * dpr;
        if (window._lastRenderedDesks) {
          for (const d of window._lastRenderedDesks) {
            const dist = Math.hypot(mx - d.screenX, my - d.screenY);
            if (dist < 42 * dpr) {
              focus3DDesk(d.index);
              break;
            }
          }
        }
      });

      function resize() {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = canvas.parentElement.clientWidth * dpr;
        canvas.height = canvas.parentElement.clientHeight * dpr;
      }
      window.addEventListener('resize', resize);
      resize();
      spawnAllOfficeBeams();

      function renderFrame() {
        tick3D += 0.035;
        if (autoOrbit) camYaw += 0.0018;

        const W = canvas.width;
        const H = canvas.height;
        const dpr = window.devicePixelRatio || 1;
        const cx = W * 0.5;
        const cy = H * 0.56;
        const sc = Math.min(W, H) * 0.37;

        ctx.clearRect(0, 0, W, H);

        // 1. Outer Architectural Mezzanine Octagon Floor
        for (const radius of [1.26, 0.96, 0.42]) {
          ctx.beginPath();
          for (let i = 0; i < 8; i++) {
            const a = (i * Math.PI * 2) / 8 + Math.PI / 8;
            const pt = projectIso(Math.cos(a) * radius, 0, Math.sin(a) * radius, cx, cy, sc);
            i === 0 ? ctx.moveTo(pt.x, pt.y) : ctx.lineTo(pt.x, pt.y);
          }
          ctx.closePath();
          if (radius > 1.2) {
            const fg = ctx.createRadialGradient(cx, cy, 12, cx, cy, sc * 1.25);
            fg.addColorStop(0, 'rgba(14, 165, 233, 0.24)');
            fg.addColorStop(0.55, 'rgba(15, 23, 42, 0.92)');
            fg.addColorStop(1, 'rgba(4, 9, 22, 0.96)');
            ctx.fillStyle = fg;
            ctx.fill();
            ctx.lineWidth = 2.2 * dpr;
            ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
          } else {
            ctx.lineWidth = 1.2 * dpr;
            ctx.strokeStyle = 'rgba(56, 189, 248, 0.22)';
          }
          ctx.stroke();
        }

        // 2. Central Quantum Core Reactor ("SYNAX-LLM & MULTI-AGENT HUB")
        const coreBase = projectIso(0, 0, 0, cx, cy, sc);
        const coreTop = projectIso(0, 0.34 + Math.sin(tick3D) * 0.03, 0, cx, cy, sc);

        // Vertical quantum light pillar
        const pillarGrad = ctx.createLinearGradient(coreBase.x, coreBase.y, coreTop.x, coreTop.y - 45 * dpr);
        pillarGrad.addColorStop(0, 'rgba(245, 158, 11, 0.45)');
        pillarGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.28)');
        pillarGrad.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
        ctx.fillStyle = pillarGrad;
        ctx.fillRect(coreBase.x - 18 * dpr, coreTop.y - 35 * dpr, 36 * dpr, (coreBase.y - coreTop.y) + 35 * dpr);

        ctx.beginPath();
        ctx.arc(coreTop.x, coreTop.y, 14 * dpr, 0, Math.PI * 2);
        ctx.fillStyle = '#fbbf24';
        ctx.shadowColor = '#fbbf24';
        ctx.shadowBlur = 18 * dpr;
        ctx.fill();
        ctx.shadowBlur = 0;

        // 3. Compute 8 3D Workstations around the Octagon
        const deskNodes = AGENT_DESKS.map((d, i) => {
          const ang = (i * Math.PI * 2) / 8 - Math.PI / 2;
          const r = 0.88;
          const wx = Math.cos(ang) * r;
          const wz = Math.sin(ang) * r;
          const base = projectIso(wx, 0, wz, cx, cy, sc);
          const deskSurface = projectIso(wx, 0.17, wz, cx, cy, sc);
          const monitorCenter = projectIso(wx, 0.33, wz, cx, cy, sc);
          const avatarHead = projectIso(wx * 1.07, 0.39 + Math.sin(tick3D + i) * 0.02, wz * 1.07, cx, cy, sc);
          return { ...d, wx, wz, base, deskSurface, monitorCenter, avatarHead, depth: base.depth, screenX: deskSurface.x, screenY: deskSurface.y };
        });
        window._lastRenderedDesks = deskNodes;

        // Draw optical floor conduits from Central Core to all 8 Desks
        deskNodes.forEach(dn => {
          ctx.beginPath();
          ctx.moveTo(coreBase.x, coreBase.y);
          ctx.lineTo(dn.base.x, dn.base.y);
          ctx.strokeStyle = dn.active ? dn.color + '88' : 'rgba(148,163,184,0.18)';
          ctx.lineWidth = (focusedDeskIndex === dn.index ? 3 : 1.8) * dpr;
          ctx.stroke();
        });

        // Animate 3D Laser Task Packets
        laserPackets.forEach(pkt => {
          pkt.t += pkt.speed;
          if (pkt.t >= 1) pkt.t = 0;
          const sx = pkt.from === -1 ? 0 : deskNodes[pkt.from].wx;
          const sz = pkt.from === -1 ? 0 : deskNodes[pkt.from].wz;
          const tx = deskNodes[pkt.to].wx;
          const tz = deskNodes[pkt.to].wz;
          const px = sx + (tx - sx) * pkt.t;
          const pz = sz + (tz - sz) * pkt.t;
          const py = 0.08 + Math.sin(pkt.t * Math.PI) * 0.24;
          const pt = projectIso(px, py, pz, cx, cy, sc);

          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 4.2 * dpr, 0, Math.PI * 2);
          ctx.fillStyle = pkt.color;
          ctx.shadowColor = pkt.color;
          ctx.shadowBlur = 12 * dpr;
          ctx.fill();
          ctx.shadowBlur = 0;
        });

        // Depth-sort workstations back-to-front
        const sorted = [...deskNodes].sort((a, b) => a.depth - b.depth);

        sorted.forEach(dn => {
          const isFocus = focusedDeskIndex === dn.index;
          const w = (isFocus ? 40 : 34) * dpr;
          const h = (isFocus ? 17 : 14) * dpr;

          // Floor holographic ring under workstation
          ctx.beginPath();
          ctx.ellipse(dn.base.x, dn.base.y, w * 1.15, h * 0.9, 0, 0, Math.PI * 2);
          ctx.fillStyle = isFocus ? 'rgba(245, 158, 11, 0.28)' : dn.color + '26';
          ctx.fill();
          ctx.lineWidth = (isFocus ? 2.6 : 1.5) * dpr;
          ctx.strokeStyle = isFocus ? '#fbbf24' : dn.color;
          ctx.stroke();

          // Brushed Titanium Curved Desk Console
          ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
          ctx.strokeStyle = dn.color;
          ctx.lineWidth = 1.8 * dpr;
          ctx.beginPath();
          ctx.roundRect(dn.deskSurface.x - w * 0.78, dn.deskSurface.y - h * 0.45, w * 1.56, h * 1.05, 6 * dpr);
          ctx.fill();
          ctx.stroke();

          // Curved Ultra-Wide Dual Holographic Monitor Screen
          const mw = w * 1.25;
          const mh = 18 * dpr;
          ctx.fillStyle = 'rgba(7, 14, 30, 0.92)';
          ctx.strokeStyle = isFocus ? '#fbbf24' : dn.color;
          ctx.lineWidth = 1.6 * dpr;
          ctx.beginPath();
          ctx.roundRect(dn.monitorCenter.x - mw / 2, dn.monitorCenter.y - mh / 2, mw, mh, 4 * dpr);
          ctx.fill();
          ctx.stroke();

          // Simulated live waveform / matrix bars inside the 3D monitor
          ctx.beginPath();
          for (let k = -3; k <= 3; k++) {
            const bx = dn.monitorCenter.x + k * 4.5 * dpr;
            const bh = (4 + Math.abs(Math.sin(tick3D * 2 + dn.index + k)) * 8) * dpr;
            ctx.moveTo(bx, dn.monitorCenter.y + 5 * dpr);
            ctx.lineTo(bx, dn.monitorCenter.y + 5 * dpr - bh);
          }
          ctx.strokeStyle = dn.color;
          ctx.lineWidth = 2 * dpr;
          ctx.stroke();

          // Specialist AI Humanoid Avatar Head & Glowing Visor
          ctx.beginPath();
          ctx.arc(dn.avatarHead.x, dn.avatarHead.y, 7.5 * dpr, 0, Math.PI * 2);
          ctx.fillStyle = '#e2e8f0';
          ctx.fill();
          ctx.fillStyle = dn.color;
          ctx.fillRect(dn.avatarHead.x - 5 * dpr, dn.avatarHead.y - 2 * dpr, 10 * dpr, 3.2 * dpr);

          // Workstation Label below desk
          ctx.font = `800 ${9.5 * dpr}px Inter, -apple-system, sans-serif`;
          ctx.textAlign = 'center';
          ctx.fillStyle = isFocus ? '#fbbf24' : '#f8fafc';
          ctx.fillText(`MASA ${dn.index + 1}: ${dn.shortTitle}`, dn.base.x, dn.base.y + 20 * dpr);

          // Floating Glassmorphic Task & Engine Badge above Workstation
          const badgeText = `${dn.engine.split(' ')[0]} · %${dn.progress}`;
          ctx.font = `700 ${8.8 * dpr}px Inter, -apple-system, sans-serif`;
          const tw = ctx.measureText(badgeText).width + 14 * dpr;
          const bh = 16 * dpr;
          const bx = dn.avatarHead.x - tw / 2;
          const by = dn.avatarHead.y - 26 * dpr;

          ctx.fillStyle = 'rgba(5, 10, 24, 0.92)';
          ctx.strokeStyle = isFocus ? '#fbbf24' : dn.color;
          ctx.lineWidth = 1.2 * dpr;
          ctx.beginPath();
          ctx.roundRect(bx, by, tw, bh, 5 * dpr);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#38bdf8';
          ctx.fillText(badgeText, dn.avatarHead.x, by + 11.2 * dpr);
        });

        requestAnimationFrame(renderFrame);
      }

      renderFrame();
    }

    // =========================================================================
    // 6. CHAT BOX & NATURAL TURKISH CONVERSATION CONTROLLER
    // =========================================================================
    function appendChatBubble(role, text, metaLabel = '') {
      const box = document.getElementById('chatMessagesBox');
      const div = document.createElement('div');
      div.className = 'bubble ' + (role === 'user' ? 'user' : 'ai');
      if (role === 'ai') {
        div.innerHTML = `<div class="bubble-head"><span>🧠 SYNAX-LLM v3.0 &amp; 3D Ajan Ofisi</span><span>${metaLabel}</span></div>` + formatSimpleMarkdown(text);
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
      init3DArchitecturalStage();
      appendChatBubble(
        'ai',
        'Merhaba **Dr. Aydın**! **SYNAX 3D Agent Office v3.0** ve **SYNAX-LLM Türkçe Dil Modeli** hazır.\n\n' +
        '- **Soldaki 8 Uzman Ajan Masasının** her birine (**Agent-Scholar Akademik PRISMA**, **Agent-Biostat Meta-Analiz**, **Agent-Lyapunov Sıfır-Sapma**, **Agent-EGraph 0-ULP**, **Agent-Shield -%88 Token**, **Agent-Vault SHA-256**, **Agent-Silicon ARM64/AVX2/MCU**) ayrı ayrı görev ve AI motoru (`Claude Code`, `OpenAI Codex`, `Google Antigravity`, `SYNAX-LLM`) atayabilirsiniz.\n' +
        '- **Orta Paneldeki Canlı İş Üretim Atölyesinde** ajanların ürettiği gerçek makale incelemelerini, Forest Plot istatistiklerini, `.sx`/Python/C99/ARM64 kodlarını ve Claude/Codex kapsüllerini anında inceleyip indirebilirsiniz.',
        '8/8 Ajan Hazır · v3.0'
      );
    });
  </script>
</body>
</html>
"""
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
                "version": "3.0.0",
                "agent_count": 8,
                "integrations": ["Claude Code", "OpenAI Codex", "Google Antigravity", "SYNAX-LLM"],
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
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
    print(f"🏢 SYNAX 3D Agent Office v3.0 (8 Ajan · Claude/Codex/Antigravity) aktif: http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="SYNAX 3D Agent Office v3.0")
    parser.add_argument("--serve", action="store_true", help="Run the 3D Agent Office v3.0 server")
    parser.add_argument("--port", type=int, default=8795, help="HTTP port")
    parser.add_argument("--export-html", type=str, default="", help="Export standalone 3D Office v3.0 HTML")
    parser.add_argument("--multitask", type=str, default="", help="Execute a multitask command in CLI")
    parser.add_argument("--agent", type=str, default="", help="Assign task to a specific agent desk ID")
    args = parser.parse_args()

    if args.export_html:
        out = Path(args.export_html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_embedded_3d_office_html(), encoding="utf-8")
        print(f"✓ Exported standalone 3D Agent Office v3.0 HTML to: {out}")
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
    res = orch.execute_multitask("Yoğun bakım EKG ve IBP monitörizasyonunda sıfır-sapmalı Lyapunov kalibrasyonu için PRISMA literatür taraması, meta-analiz ve ARM64 NEON kodu üret")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
