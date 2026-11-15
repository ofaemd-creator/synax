---
name: synax-token-shield
description: Zero-dependency AI Token Compressor, AST Code Skeletonizer, Terminal Log Deduplicator, SHA-256 Semantic Cache, and Frugal Model Router for Claude Code, OpenAI Codex, Google Antigravity, Cursor, and Windsurf. Cuts token consumption by 75%-92% so agent quotas never run out.
---

# SYNAX Token Shield (`synax-token-shield`)

Use this skill whenever working in **Claude Code, OpenAI Codex, Google Antigravity, Cursor, or Windsurf** to prevent token exhaustion, compress large source files before reading, deduplicate noisy build/test logs, and route deterministic tasks to 0-token local engines.

## 5 Core Token-Saving Engines

1. **AST-Aware Code Skeletonizer (`--file <path> [--focus <symbol>]`)**
   - Preserves 100% of imports, class/function signatures, type annotations, and docstrings while eliding non-target implementation bodies (**75%–92% fewer tokens**).
   - Pass `--focus <function_or_class>` to keep the target symbol's full body while skeletonizing the rest of the file.
2. **Surgical Terminal Log & Stack-Trace Deduplicator (`--compress-log <path_or_text>`)**
   - Strips ANSI escape codes, collapses consecutive duplicate lines (`[×N identical lines collapsed]`), and preserves error/exception frames (**80%–95% fewer tokens**).
3. **SHA-256 Content-Hash Semantic Memoizer (`SemanticTokenCache`)**
   - Prevents agents from re-reading unchanged files across turns by returning a 12-token `[SYNAX-CACHE-HIT sha256=#...]` stub (**100% token reduction on unchanged files**).
4. **Prompt-Cache Prefix Aligner (`build_cache_aligned_payload`)**
   - Structures static system rules and repo maps with Anthropic `cache_control: {"type": "ephemeral"}` and OpenAI prefix-cache alignment (**up to 90% billing reduction**).
5. **Frugal Multi-Model Tier Router (`--route "<task>"`)**
   - **Tier 0 (`0 tokens`):** Routes syntax checks, `.sx` verification, E-Graph algebra, and Interval Prover to local CPU/SIMD (`synaxc`).
   - **Tier 1 (`Free / Flash`):** Routes routine edits/docstrings to free/flash models (`gemma-4-31b:free`, `gemini-3-flash`, `claude-haiku-4.5`).
   - **Tier 2 (`Frontier Shielded`):** Sends pre-skeletonized context (`-82% tokens`) to `claude-sonnet-4` / `openai-codex`.

## Quick CLI Commands

```bash
# 1. Benchmark token savings across a repository directory
python3 src/synax/token_shield.py --dir src/

# 2. Skeletonize a large file before feeding it to Claude/Codex
python3 src/synax/token_shield.py --file src/synax/telegram_bot.py --focus handle_command_text

# 3. Compress noisy pytest/compiler output
python3 src/synax/token_shield.py --compress-log build.log

# 4. Route a task to the most token-frugal engine
python3 src/synax/token_shield.py --route "Prove IEEE-754 interval safety of relu(a - b)"
```
