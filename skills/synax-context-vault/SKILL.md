---
name: synax-context-vault
description: Zero-Token Cross-Agent Handoff & Persistent Semantic Memory Vault for Claude Code, OpenAI Codex, Google Antigravity, Cursor, and Windsurf. Replaces 50,000-token repo re-reads with a <180-token SHA-256 Handoff Capsule (99.7% token reduction) when switching models or sessions.
---

# SYNAX Context Vault (`synax-context-vault`)

Use this skill when switching between **Claude Code, OpenAI Codex, Google Antigravity, Cursor, or free local models** (or before a context compaction / quota limit) so the next agent resumes immediately in **<180 tokens** instead of burning **38,000–50,000 tokens** re-reading the repository.

## Quick CLI Commands

```bash
# Generate and display a cross-agent handoff capsule + token savings report
python3 src/synax/context_vault.py --goal "Continue SIMD kernel optimization" --from-agent claude-code --to-agent openai-codex --save

# Emit only the ultra-dense <180-token prompt header for pasting or piping into another agent
python3 src/synax/context_vault.py --compact
```
