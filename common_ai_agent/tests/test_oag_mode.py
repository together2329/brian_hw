"""OAG_MODE: tightly fuse a project's .codex OAG (Ontology IP Agent) pack into
the default agent.

When OAG_MODE=1 the agent must (1) inject the project's AGENTS.md + .codex/rules
into its prompt context (independent of prompt-injection) and (2) expose the
native `oag` tool that drives the project's own .codex/scripts/oag_cli.py gateway
directly — no MCP, because this is our own custom ReAct agent. Default OFF.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(PROJECT_ROOT), str(PROJECT_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core import prompt_builder as pb
from core import tools as T


def _make_oag_project(tmp_path):
    """Minimal .codex project: AGENTS.md + a rule + a fake oag_cli.py gateway
    that echoes its argv so the test is deterministic without the real OAG
    backend."""
    (tmp_path / "AGENTS.md").write_text(
        "# Project Agent Rules\nAlways run oag.inspect first.\n", encoding="utf-8")
    codex = tmp_path / ".codex"
    (codex / "rules").mkdir(parents=True)
    (codex / "rules" / "oag-rocev.rules.md").write_text(
        "# ROCEV\nDeclare before code.\n", encoding="utf-8")
    scripts = codex / "scripts"
    scripts.mkdir()
    (scripts / "oag_cli.py").write_text(
        "import sys, json\nprint(json.dumps({'echo': sys.argv[1:]}))\n", encoding="utf-8")
    return tmp_path


# ── flag (platform.config / prompt_builder resolver) ──

def test_oag_mode_default_off(monkeypatch):
    monkeypatch.delenv("OAG_MODE", raising=False)
    assert pb.oag_mode_enabled() is False


def test_oag_mode_env_on(monkeypatch):
    monkeypatch.setenv("OAG_MODE", "1")
    assert pb.oag_mode_enabled() is True


# ── AGENTS.md / rules injection (agent.prompt-builder) ──

def test_oag_root_and_agents_context(monkeypatch, tmp_path):
    _make_oag_project(tmp_path)
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    assert pb.oag_root() == tmp_path
    ctx = pb._build_oag_agents_context()
    assert pb.OAG_CONTEXT_START in ctx and pb.OAG_CONTEXT_END in ctx
    assert "Project Agent Rules" in ctx   # AGENTS.md injected
    assert "ROCEV" in ctx                 # .codex/rules/*.md injected
    assert "oag(" in ctx                  # tells the agent to drive via the oag tool


def test_oag_root_none_when_no_codex(monkeypatch, tmp_path):
    monkeypatch.delenv("OAG_ROOT", raising=False)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)           # empty cwd: no .codex / AGENTS.md
    assert pb.oag_root() is None
    assert pb._build_oag_agents_context() == ""


# ── native oag tool drives .codex (agent.tools) ──

def test_oag_tool_off_when_mode_off(monkeypatch):
    monkeypatch.delenv("OAG_MODE", raising=False)
    assert "OAG_MODE is off" in T.oag(tool="oag.inspect", ip="timer")


def test_oag_tool_calls_gateway(monkeypatch, tmp_path):
    _make_oag_project(tmp_path)
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    out = T.oag(tool="oag.inspect", ip="timer", stage="rtl-gen", intent="check")
    # fake gateway echoes argv: ["call","--json","{...payload...}"]
    assert "call" in out and "oag.inspect" in out and "timer" in out


def test_oag_tool_script_mode(monkeypatch, tmp_path):
    _make_oag_project(tmp_path)
    (tmp_path / ".codex" / "scripts" / "smoke.py").write_text(
        "print('SMOKE_OK')\n", encoding="utf-8")
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    assert "SMOKE_OK" in T.oag(script="smoke.py")


def test_filtered_tools_gates_oag(monkeypatch):
    monkeypatch.delenv("OAG_MODE", raising=False)
    assert "oag" not in T.filtered_available_tools()
    monkeypatch.setenv("OAG_MODE", "1")
    assert "oag" in T.filtered_available_tools()
