"""CLI and editor JSON-RPC transport for the SYNAX chat agent."""

from __future__ import annotations
import json
import sys
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from synax_chat import SynaxChatAgent


def run_chat_cli(args_list: List[str]) -> None:
    from synax_chat import SynaxChatAgent

    agent = SynaxChatAgent()

    # Tek sorguluk komut satırı çağrısı: synax chat --query "..."
    if "--query" in args_list:
        idx = args_list.index("--query")
        if idx + 1 < len(args_list):
            q = args_list[idx + 1]
            res = agent.process_message(q)
            print(res.text)
            if res.code:
                print("\n```synax\n" + res.code + "\n```")
            return

    # JSON-RPC / VS Code Extension IPC modu: synax chat --json-rpc
    if "--json-rpc" in args_list:
        run_json_rpc(agent)
        return

    # İnteraktif Terminal REPL modu
    print("\033[1;36m")
    print(r"""
   ███████╗██╗   ██╗███╗   ██╗ █████╗ ██╗  ██╗     ██████╗ ██████╗ ██████╗ ███████╗
   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗╚██╗██╔╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
   ███████╗ ╚████╔╝ ██╔██╗ ██║███████║ ╚███╔╝     ██║     ██║   ██║██║  ██║█████╗
   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║ ██╔██╗     ██║     ██║   ██║██║  ██║██╔══╝
   ███████║   ██║   ██║ ╚████║██║  ██║██╔╝ ██╗    ╚██████╗╚██████╔╝██████╔╝███████╗
   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
    """)
    print(
        "\033[0m\033[1;32m   🧬 SYNAX CODE — Otonom & Kendi Kendini Geliştiren AI Asistanı (v0.8.0)\033[0m"
    )
    print(
        "\033[90m   SynaxLLM ile sohbet edin veya 'kendine şu beceriyi edin: X = Y' ile eğitin."
    )
    print("   Çıkış için 'exit' veya Ctrl+C.\033[0m\n")

    while True:
        try:
            prompt_input = input("\033[1;33msynax>\033[0m ").strip()
            if not prompt_input:
                continue
            if prompt_input.lower() in ("exit", "quit", "q"):
                print("\n👋 SYNAX Code oturumu sonlandırıldı.")
                break
            res = agent.process_message(prompt_input)
            print(f"\n{res.text}\n")
            if res.code:
                print(f"\033[94m```synax\n{res.code}\n```\033[0m\n")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Görüşmek üzere!")
            break


def run_json_rpc(agent: SynaxChatAgent) -> None:
    """
    Standard stdio JSON-RPC loop for the VS Code extension webview backend.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method", "chat")
            params = req.get("params", {})

            if method == "ping":
                result = {"status": "ok", "version": "0.8.0"}
            elif method == "teach":
                concept = params.get("concept", "")
                formula = params.get("formula", "")
                result = agent.teach_skill(concept, formula)
            elif method in ("chat", "message"):
                msg = params.get("message", "")
                ctx = params.get("context", {})
                res = agent.process_message(msg, ctx)
                result = res.to_dict()
            elif method == "list_skills":
                result = agent.model.brain.get("learned_concepts", {})
            elif method == "evolve":
                code = params.get("code", "")
                target = params.get("target", code)
                from synax.evolution import EvolutionArena

                arena = EvolutionArena()
                report = arena.run_match(target)
                result = {
                    "status": "success",
                    "report": report.to_dict(),
                    "markdown": report.format_markdown(),
                }
            elif method == "synthesize":
                intent = params.get("intent", "")
                from synax.evolution import NeuroSymbolicSynthesizer

                synthesizer = NeuroSymbolicSynthesizer()
                syn_res = synthesizer.synthesize_from_intent(intent)
                result = {
                    "status": "success",
                    "best_code": syn_res.best_code,
                    "winner_id": syn_res.winner_id,
                    "candidates": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "description": c.description,
                            "code": c.code,
                        }
                        for c in syn_res.candidates
                    ],
                }
            elif method == "get_memory":
                from synax.evolution import EpisodicEvolutionMemory

                mem = EpisodicEvolutionMemory()
                result = mem.data
            else:
                result = {"error": f"Unknown method '{method}'"}

            resp = {"id": req_id, "result": result}
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"id": None, "error": str(e)}
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
