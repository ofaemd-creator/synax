"""SYNAX Code agent loop: tool dispatch, workspace confinement and approval gate."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from synax.agent import Agent, Workspace


def scripted(*replies):
    """Fake model that returns the given assistant messages in order."""
    it = iter(replies)
    return lambda messages: next(it)


def call(name, **args):
    return {"content": "", "tool_calls": [{"id": name, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}]}


def test_agent_edits_file_then_finishes(tmp_path):
    (tmp_path / "a.txt").write_text("merhaba dünya\n")
    agent = Agent(Workspace(tmp_path), scripted(call("edit_file", path="a.txt", old="dünya", new="SYNAX"),
                                                {"content": "Bitti."}), approve=lambda *_: True, log=lambda _: None)
    assert agent.run("değiştir") == "Bitti."
    assert (tmp_path / "a.txt").read_text() == "merhaba SYNAX\n"
    assert agent.messages[-2]["content"] == "Düzenlendi: a.txt"


def test_denied_write_is_not_applied(tmp_path):
    agent = Agent(Workspace(tmp_path), scripted(call("write_file", path="x.txt", content="x"), {"content": "ok"}),
                  approve=lambda *_: False, log=lambda _: None)
    agent.run("yaz")
    assert not (tmp_path / "x.txt").exists()
    assert "reddetti" in agent.messages[-2]["content"]


def test_paths_outside_workspace_are_rejected(tmp_path):
    agent = Agent(Workspace(tmp_path), scripted(call("read_file", path="../../etc/passwd"), {"content": "ok"}),
                  approve=lambda *_: True, log=lambda _: None)
    agent.run("oku")
    assert "dışına erişim reddedildi" in agent.messages[-2]["content"]


def test_ambiguous_edit_is_refused(tmp_path):
    (tmp_path / "b.txt").write_text("x x")
    assert "2 kez" in Workspace(tmp_path).edit_file("b.txt", "x", "y")
    assert (tmp_path / "b.txt").read_text() == "x x"


def test_project_memory_enters_system_prompt(tmp_path):
    (tmp_path / "SYNAX.md").write_text("Testler: pytest -q")
    agent = Agent(Workspace(tmp_path), scripted(), approve=lambda *_: True)
    assert "pytest -q" in agent.messages[0]["content"]


if __name__ == "__main__":
    import tempfile
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(Path(tempfile.mkdtemp()))
            print(f"✓ {name}")
