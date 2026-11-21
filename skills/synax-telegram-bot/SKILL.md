---
name: synax-telegram-bot
description: Zero-dependency Telegram Bot & MCP remote agent skill bridging SYNAX, Claude Code, OpenAI Codex, and Google Antigravity to mobile Telegram commands (/status, /check, /run, /egraph, /prove, /code).
---

# SYNAX Telegram Bot Skill (`synax-telegram-bot`)

This skill equips **Claude Code**, **OpenAI Codex**, **Google Antigravity**, **Cursor**, and **SYNAX Code** with a zero-dependency Telegram Bot API client and remote compiler/agent bridge (`src/synax/telegram_bot.py`).

## Capabilities

1. **Remote Compiler & 19-Suite IEEE-754 Verification (`/check`, `/run`)**:
   - Validate `.sx` kernels or inline tensor expressions from Telegram and run them with automatic `IMMUNE` (`NaN`/`Inf` -> `0.0`) recovery.
2. **E-Graph Equality Saturation (`/egraph`)**:
   - Optimize algebraic expressions into hardware intrinsics (`fma`, `pow2`, `pow3`, `relu`) and inspect hardware cycle savings from your phone.
3. **Static IEEE-754 Interval Prover (`/prove`)**:
   - Generate formal interval bounds `[lo, hi]` and verify division-by-zero and overflow freedom with a SHA-256 certificate.
4. **Autonomous Workspace Agent Dispatch (`/code`)**:
   - Trigger `src/synax/agent.py` (backed by Claude, Gemini, OpenRouter, Groq, or Ollama) with `TELEGRAM_ALLOWED_CHAT_IDS` access control.

## CLI Usage

```bash
./synax telegram --status
./synax telegram --cmd "/egraph (a * b + c) + (x - x)"
./synax telegram --cmd "/prove relu(a - b)"
./synax telegram --poll
```
