# 🔐 SYNAX Context Vault — Claude Code & OpenAI Codex Handoff Capsule
- **Job ID:** `SYNAX-JOB-0001`
- **Vault SHA-256:** `79baf21de2b902639ee3d7e8224e903f8f4a0854d4063d7b8d53b4ed99d7780e`
- **Capsule Size:** `132 tokens` (-93.76% vs raw `2114 tokens`)
- **Synthesized Kernel:** `synax_ecg_zero_drift_autocal` (`biomedical_ecg`)
- **Formal Proof:** `[-7.0, 7.0]` (`19-Suite IEEE-754 0-ULP SAFE` · `#62fecaea679a`)
- **Lyapunov Stability:** $V_1 = 1.976836 \rightarrow V_{20} = 0.00005846$ (`99.587%` zero-drift lock)

## 🤝 1. Claude Code CLI Integration (`claude`)
```bash
# Register SYNAX 3D Agent Office as a live MCP server in Claude Code:
claude mcp add synax-agent-office -- python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax/src/synax/office_mcp_server.py --stdio
```

## 🤝 2. OpenAI Codex CLI Integration (`codex`)
Add to `~/.codex/config.toml` or project `.codex/config.toml`:
```toml
[mcp_servers.synax_agent_office]
command = "python3"
args = ["/Users/o.farukaydin/.gemini/antigravity/scratch/synax/src/synax/office_mcp_server.py", "--stdio"]
```
