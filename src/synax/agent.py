"""
SYNAX Code Agent (`src/synax/agent.py`)
=======================================
Terminal coding agent: the model plans, calls workspace tools (read, search,
edit, shell, .sx check/run), sees results and iterates until the task is done.
Any OpenAI-compatible chat endpoint with tool calling works (Claude, OpenRouter,
Groq, local Ollama). Writes and shell commands require confirmation unless
`--yes` is given. File tools are confined to the workspace root.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# (base_url, default model, api-key env var) tried in order; first key present wins.
PROVIDERS = [
    ("https://api.anthropic.com/v1", "claude-sonnet-4-20250514", "ANTHROPIC_API_KEY"),
    ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-3-flash-preview", "GEMINI_API_KEY"),
    ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-3-flash-preview", "GOOGLE_API_KEY"),
    ("https://openrouter.ai/api/v1", "qwen/qwen3-coder", "OPENROUTER_API_KEY"),
    ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "GROQ_API_KEY"),
    ("https://api.z.ai/api/paas/v4", "glm-4.5-flash", "ZAI_API_KEY"),
]
OLLAMA = ("http://127.0.0.1:11434/v1", "qwen2.5-coder:7b", "")
AUTH_JSON_FALLBACKS = [
    ("google", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-3-flash-preview"),
    ("zai", "https://api.z.ai/api/paas/v4", "glm-4.5-flash"),
]
MAX_OUTPUT = 12000

SYSTEM = """You are SYNAX Code, an autonomous software engineering agent working in the user's workspace.
Work in small verified steps: inspect files before changing them, make the edit, then run the relevant
check or test and read its output. Use sx_check / sx_run for .sx kernels. Never claim something works
without running it. When the task is done, reply with a short summary of what changed and what you verified.
Reply in the user's language (Turkish when addressed in Turkish). Workspace root: {root}
{memory}"""

TOOLS = [
    ("list_files", "List files under a directory (glob pattern, recursive with **).",
     {"path": "string", "pattern": "string"}, []),
    ("read_file", "Read a text file with line numbers.",
     {"path": "string", "offset": "integer", "limit": "integer"}, ["path"]),
    ("grep", "Search files for a regular expression; returns path:line: text.",
     {"pattern": "string", "path": "string"}, ["pattern"]),
    ("write_file", "Create or overwrite a file with full content.",
     {"path": "string", "content": "string"}, ["path", "content"]),
    ("edit_file", "Replace one exact, unique occurrence of old with new in a file.",
     {"path": "string", "old": "string", "new": "string"}, ["path", "old", "new"]),
    ("bash", "Run a shell command in the workspace root (120 s timeout).",
     {"command": "string"}, ["command"]),
    ("sx_check", "Parse and type-check a .sx file.", {"path": "string"}, ["path"]),
    ("sx_run", "Compile, verify and execute a .sx kernel on sample tensors.", {"path": "string"}, ["path"]),
]
NEEDS_APPROVAL = {"write_file", "edit_file", "bash"}


def tool_schemas() -> List[Dict[str, Any]]:
    return [{"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "required": req,
                       "properties": {k: {"type": t} for k, t in props.items()}}}}
        for name, desc, props, req in TOOLS]


def resolve_backend() -> tuple[str, str, str]:
    """Return (base_url, model, api_key); explicit SYNAX_AGENT_* env vars override presets."""
    base, model, key = OLLAMA
    found = False
    for b, m, env in PROVIDERS:
        if os.environ.get(env, "").strip():
            base, model, key = b, m, os.environ[env].strip()
            found = True
            break
    if not found:
        auth_path = Path.home() / ".local" / "share" / "opencode" / "auth.json"
        if auth_path.exists():
            try:
                auth_data = json.loads(auth_path.read_text(encoding="utf-8"))
                for prov_id, b_url, m_id in AUTH_JSON_FALLBACKS:
                    k = auth_data.get(prov_id, {}).get("key", "").strip()
                    if k:
                        base, model, key = b_url, m_id, k
                        break
            except Exception:
                pass
    return (os.environ.get("SYNAX_AGENT_BASE_URL", base).rstrip("/"),
            os.environ.get("SYNAX_AGENT_MODEL", model),
            os.environ.get("SYNAX_AGENT_API_KEY", key))


def http_chat(base: str, model: str, key: str) -> Callable[[List[Dict[str, Any]]], Dict[str, Any]]:
    def chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        body = json.dumps({"model": model, "messages": messages, "tools": tool_schemas(),
                           "max_tokens": 8192}).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "SYNAX-Agent/1.0"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        if "anthropic.com" in base:
            headers["anthropic-version"] = "2023-06-01"
        req = urllib.request.Request(f"{base}/chat/completions", data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.load(resp)["choices"][0]["message"]
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Model hatası {exc.code}: {exc.read().decode(errors='replace')[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Model sunucusuna ulaşılamadı ({base}): {exc.reason}") from exc
    return chat


class Workspace:
    """Tool implementations, confined to `root`."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def path(self, p: str) -> Path:
        full = (self.root / (p or ".")).resolve()
        if full != self.root and self.root not in full.parents:
            raise ValueError(f"Çalışma alanı dışına erişim reddedildi: {p}")
        return full

    def list_files(self, path: str = ".", pattern: str = "**/*") -> str:
        skip = {".git", "node_modules", ".venv", "__pycache__"}
        hits = [str(f.relative_to(self.root)) for f in self.path(path).glob(pattern or "**/*")
                if f.is_file() and not skip & set(f.relative_to(self.root).parts)]
        return "\n".join(sorted(hits)[:500]) or "(boş)"

    def read_file(self, path: str, offset: int = 1, limit: int = 400) -> str:
        lines = self.path(path).read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(int(offset or 1), 1)
        chunk = lines[start - 1:start - 1 + int(limit or 400)]
        return "\n".join(f"{i}\t{line}" for i, line in enumerate(chunk, start)) or "(boş dosya)"

    def grep(self, pattern: str, path: str = ".") -> str:
        rx, out = re.compile(pattern), []
        base = self.path(path)
        files = [base] if base.is_file() else base.rglob("*")
        for f in files:
            if not f.is_file() or {".git", ".venv", "node_modules"} & set(f.parts) or f.stat().st_size > 2_000_000:
                continue
            try:
                for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if rx.search(line):
                        out.append(f"{f.relative_to(self.root)}:{n}: {line.strip()[:200]}")
            except (UnicodeDecodeError, OSError):
                continue
            if len(out) >= 200:
                break
        return "\n".join(out) or "(eşleşme yok)"

    def write_file(self, path: str, content: str) -> str:
        f = self.path(path)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        return f"Yazıldı: {path} ({len(content)} karakter)"

    def edit_file(self, path: str, old: str, new: str) -> str:
        f = self.path(path)
        text = f.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            return f"Düzenleme yapılmadı: eski metin {count} kez bulundu, tam 1 olmalı."
        f.write_text(text.replace(old, new), encoding="utf-8")
        return f"Düzenlendi: {path}"

    def bash(self, command: str) -> str:
        try:
            r = subprocess.run(command, shell=True, cwd=self.root, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return "Zaman aşımı (120 s)."
        return f"exit={r.returncode}\n{r.stdout}{r.stderr}"

    def sx_check(self, path: str) -> str:
        from synax.assistant.tools import check_source
        return check_source(self.path(path).read_text(encoding="utf-8")).text

    def sx_run(self, path: str) -> str:
        import synax
        return json.dumps(synax.run_sx(str(self.path(path))), ensure_ascii=False, default=str, indent=1)


class Agent:
    def __init__(self, workspace: Workspace, chat: Callable[[List[Dict[str, Any]]], Dict[str, Any]],
                 approve: Callable[[str, Dict[str, Any]], bool], log: Callable[[str], None] = print,
                 max_steps: int = 50):
        self.ws, self.chat, self.approve, self.log, self.max_steps = workspace, chat, approve, log, max_steps
        memory_file = workspace.root / "SYNAX.md"
        memory = f"\nProject notes (SYNAX.md):\n{memory_file.read_text(encoding='utf-8')}" if memory_file.exists() else ""
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM.format(root=workspace.root, memory=memory)}]

    def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name not in {t[0] for t in TOOLS}:
            return f"Bilinmeyen araç: {name}"
        if name in NEEDS_APPROVAL and not self.approve(name, args):
            return "Kullanıcı bu işlemi reddetti."
        try:
            result = getattr(self.ws, name)(**args)
        except Exception as exc:  # tool errors go back to the model, not up the stack
            result = f"Hata: {type(exc).__name__}: {exc}"
        return result if len(result) <= MAX_OUTPUT else result[:MAX_OUTPUT] + "\n…(kısaltıldı)"

    def run(self, task: str) -> str:
        self.messages.append({"role": "user", "content": task})
        for _ in range(self.max_steps):
            msg = self.chat(self.messages)
            calls = msg.get("tool_calls") or []
            self.messages.append({"role": "assistant", "content": msg.get("content") or "",
                                  **({"tool_calls": calls} if calls else {})})
            if not calls:
                return msg.get("content") or ""
            if msg.get("content"):
                self.log(msg["content"])
            for call in calls:
                fn = call["function"]
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args, result = {}, "Hata: argümanlar geçerli JSON değil."
                else:
                    self.log(f"  ⚙ {fn['name']}({', '.join(f'{k}={str(v)[:60]!r}' for k, v in args.items())})")
                    result = self.call_tool(fn["name"], args)
                self.messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
        return f"Adım sınırına ulaşıldı ({self.max_steps}); görev yarım kalmış olabilir."


def ask_user(name: str, args: Dict[str, Any]) -> bool:
    preview = args.get("command") or args.get("path", "")
    if name == "edit_file":
        preview += f"\n--- eski\n{args.get('old', '')[:800]}\n+++ yeni\n{args.get('new', '')[:800]}"
    return input(f"\n? {name}: {preview}\n  İzin ver? [e/H] ").strip().lower() in ("e", "y", "evet", "yes")


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="synax code", description="SYNAX Code otonom kodlama ajanı")
    ap.add_argument("task", nargs="*", help="Görev (boşsa etkileşimli oturum)")
    ap.add_argument("--yes", action="store_true", help="Yazma ve kabuk komutlarını onaysız çalıştır")
    ap.add_argument("--root", default=".", help="Çalışma alanı kökü")
    args = ap.parse_args(argv)

    base, model, key = resolve_backend()
    agent = Agent(Workspace(Path(args.root)), http_chat(base, model, key),
                  (lambda *_: True) if args.yes else ask_user)
    print(f"SYNAX Code · {model} @ {base} · kök: {agent.ws.root}")
    task = " ".join(args.task)
    while True:
        if not task:
            try:
                task = input("\nsynax› ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if task in ("/çık", "/exit", "exit"):
                return
            if not task:
                continue
        try:
            print("\n" + agent.run(task))
        except RuntimeError as exc:
            print(f"\n✗ {exc}")
        if args.task:
            return
        task = ""


if __name__ == "__main__":
    main()
