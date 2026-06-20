"""OAG_MODE: tightly fuse a project's .codex OAG (Ontology IP Agent) pack into
the default agent.

When OAG_MODE=1 the agent must (1) inject the project's AGENTS.md + .codex/rules
into its prompt context (independent of prompt-injection) and (2) expose the
native `oag` tool that drives the project's own .codex/scripts/oag_cli.py gateway
directly — no MCP, because this is our own custom ReAct agent. Code fallback is
OFF when OAG_MODE is unset; the checked-in repo .config now keeps native OAG off
because local codex mode routes through the Codex app-server bridge by default.
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
    codex.mkdir(parents=True, exist_ok=True)
    # OAG is core: AGENTS.md / rules live INSIDE .codex (the vendored pack)
    (codex / "AGENTS.md").write_text(
        "# Project Agent Rules\nAlways run oag.inspect first.\n", encoding="utf-8")
    (codex / "rules").mkdir(parents=True)
    (codex / "rules" / "oag-rocev.rules.md").write_text(
        "# ROCEV\nDeclare before code.\n", encoding="utf-8")
    scripts = codex / "scripts"
    scripts.mkdir()
    (scripts / "oag_cli.py").write_text(
        "import sys, json\nprint(json.dumps({'echo': sys.argv[1:]}))\n", encoding="utf-8")
    return tmp_path


# ── flag (platform.config / prompt_builder resolver) ──

def _repo_config_values() -> dict[str, str]:
    values: dict[str, str] = {}
    config = PROJECT_ROOT / ".config"
    for raw in config.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def test_oag_mode_default_off(monkeypatch):
    monkeypatch.delenv("OAG_MODE", raising=False)
    assert pb.oag_mode_enabled() is False


def test_repo_config_defaults_codex_appserver_with_oag_mode_off():
    values = _repo_config_values()
    assert values["CODEX_BRIDGE"] == "1"
    assert values["CODEX_BRIDGE_OAG_MODE"] == "0"
    assert values["OAG_MODE"] == "0"


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


def test_oag_injected_into_static_system_prompt(monkeypatch, tmp_path):
    """AGENTS.md rules belong in the STATIC (cached) system prompt as a one-time
    rule block — NOT the per-turn dynamic context (they are static project rules,
    sent/cached once, not re-sent every turn)."""
    _make_oag_project(tmp_path)
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    monkeypatch.delenv("ATLAS_PROMPT_INJECTION", raising=False)
    monkeypatch.delenv("ENABLE_PROMPT_INJECTION", raising=False)

    class _Cfg:
        CACHE_OPTIMIZATION_MODE = "optimized"

    out = pb.build_system_prompt(
        messages=[{"role": "user", "content": "hi"}],
        cfg=_Cfg(),
        build_base_fn=lambda **kw: "BASE SYSTEM PROMPT",
    )
    assert isinstance(out, dict)
    assert pb.OAG_CONTEXT_START in out["static"]        # cached, static
    assert pb.OAG_CONTEXT_START not in out["dynamic"]   # not the per-turn dynamic
    assert "Project Agent Rules" in out["static"]


# ── native oag tool drives .codex (agent.tools) ──

def test_oag_tool_off_when_mode_off(monkeypatch):
    monkeypatch.delenv("OAG_MODE", raising=False)
    assert "OAG_MODE is off" in T.oag(tool="oag.inspect", ip="timer")


def test_oag_tool_calls_gateway(monkeypatch, tmp_path):
    _make_oag_project(tmp_path)
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)
    monkeypatch.delenv("ATLAS_IP_ROOT", raising=False)
    out = T.oag(tool="oag.inspect", ip="timer", stage="rtl-gen", intent="check")
    # fake gateway echoes argv: ["call","--json","{...payload...}"]
    assert "call" in out and "oag.inspect" in out and "timer" in out


def test_oag_tool_defaults_to_active_ip(monkeypatch, tmp_path):
    import json

    _make_oag_project(tmp_path)
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "apb_gpio")
    out = T.oag(tool="oag.inspect", stage="rtl-gen")
    echoed = json.loads(out)
    payload = json.loads(echoed["echo"][2])
    assert payload["tool"] == "oag.inspect"
    assert payload["arguments"]["ip_dir"] == "apb_gpio"


def test_oag_tool_rejects_mismatched_active_ip(monkeypatch, tmp_path):
    _make_oag_project(tmp_path)
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "apb_gpio")
    out = T.oag(tool="oag.scaffold", ip="timer")
    assert "refusing oag.scaffold" in out
    assert "active IP is 'apb_gpio'" in out


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


def test_oag_skill_activates_on_demand(monkeypatch):
    """L2: the vendored oag-ip-workflow skill auto-activates for IP work in OAG
    mode by keyword relevance — without the literal word 'skill' — and stays off
    for unrelated messages (progressive disclosure, not always-dumped)."""
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(PROJECT_ROOT))   # vendored .codex lives here
    monkeypatch.setenv("ENABLE_SKILL_SYSTEM", "true")

    from core.skill_system import get_skill_registry
    reg = get_skill_registry()
    sk_dir = str(PROJECT_ROOT / ".codex" / "skills")
    if sk_dir not in reg._loader.extra_dirs:
        reg._loader.extra_dirs.append(sk_dir)
    reg.reload_all_skills()

    skill = reg.get_skill("oag-ip-workflow")
    assert skill is not None                                   # discovered from .codex/skills
    assert skill.activation.auto_detect is True
    assert "rtl" in [k.lower() for k in skill.activation.keywords]

    import config as cfg
    monkeypatch.setattr(cfg, "ENABLE_SKILL_SYSTEM", True, raising=False)
    import src.main as M
    M.load_active_skills._active_skill = None

    # IP-relevant message → oag skill activates (no "skill" word in it)
    on = M.load_active_skills([{"role": "user", "content": "write the apb timer rtl and cocotb testbench"}])
    assert any("OAG IP Workflow" in p for p in on)

    # unrelated message → oag skill not activated
    M.load_active_skills._active_skill = None
    off = M.load_active_skills([{"role": "user", "content": "hello, tell me a joke"}])
    assert not any("OAG IP Workflow" in p for p in off)


def test_oag_platform_backend_runs_local_no_recursion(tmp_path):
    """L4: scripts/oag.py is a platform-canonical OAG backend that runs the engine
    LOCALLY and never re-delegates — even when OAG_COMMON_AI_AGENT points back at
    the platform (which would otherwise loop). Returns oag_tool_response.v1."""
    import json
    import os
    import subprocess
    backend = PROJECT_ROOT / "scripts" / "oag.py"
    assert backend.is_file()
    env = dict(os.environ)
    env["OAG_COMMON_AI_AGENT"] = str(PROJECT_ROOT)   # would infinite-loop if unguarded
    env["COMMON_AI_AGENT_HOME"] = str(PROJECT_ROOT)
    r = subprocess.run(
        [sys.executable, str(backend), "call", "--json",
         json.dumps({"tool": "oag.inspect", "arguments": {"ip_dir": "nope_ip"}})],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60, env=env)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d.get("schema_version") == "oag_tool_response.v1"
    assert d.get("tool") == "oag.inspect"


def _seed_active_run(tmp_path, status="in_progress", prompt_block="=== OAG NEXT ACTION ===\nnext=write the rtl\n=== END ==="):
    import json
    (tmp_path / ".codex").mkdir(exist_ok=True)
    runs = tmp_path / "myip" / "ontology" / "runs"
    (runs / "RUN_X").mkdir(parents=True, exist_ok=True)
    (runs / "active_run.json").write_text(json.dumps({"ip": "myip", "run_id": "RUN_X"}), encoding="utf-8")
    (runs / "RUN_X" / "run_state.json").write_text(
        json.dumps({"status": status, "next_action": {"prompt_block": prompt_block}}), encoding="utf-8")


def test_oag_active_run_injected_and_gated(monkeypatch, tmp_path):
    """L3: an incomplete OAG run's next-action block is surfaced every turn
    (context-inject + soft stop-gate); a closed run injects nothing."""
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))   # IPs/runs live in the workspace
    _seed_active_run(tmp_path, status="in_progress")
    ctx = pb._build_oag_run_context()
    assert pb.OAG_RUN_CONTEXT_START in ctx
    assert "write the rtl" in ctx and "ip=myip" in ctx

    _seed_active_run(tmp_path, status="closed")
    assert pb._build_oag_run_context() == ""


def test_oag_active_run_scoped_to_active_ip(monkeypatch, tmp_path):
    """L3 scope: only the ACTIVE IP's run is injected — other IPs' open runs are
    not dumped into every prompt (prevents multi-IP prompt bloat)."""
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("ATLAS_IP_ROOT", raising=False)
    _seed_active_run(tmp_path, status="in_progress")   # seeds 'myip'

    # active IP is a different IP with no run -> nothing injected
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "other_ip_no_run")
    assert pb._build_oag_run_context() == ""

    # active IP == myip -> its run is injected
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "myip")
    assert pb.OAG_RUN_CONTEXT_START in pb._build_oag_run_context()


def test_oag_active_run_goes_to_dynamic_not_static(monkeypatch, tmp_path):
    """L3: the active-run block is DYNAMIC (changes each step) → per-turn dynamic
    context, not the cached static system prompt."""
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("ATLAS_PROMPT_INJECTION", raising=False)
    _seed_active_run(tmp_path, status="in_progress")

    class _Cfg:
        CACHE_OPTIMIZATION_MODE = "optimized"

    out = pb.build_system_prompt(
        messages=[{"role": "user", "content": "hi"}],
        cfg=_Cfg(),
        build_base_fn=lambda **kw: "BASE SYSTEM PROMPT",
    )
    assert pb.OAG_RUN_CONTEXT_START in out["dynamic"]
    assert pb.OAG_RUN_CONTEXT_START not in out["static"]


def test_oag_skill_injected_when_injection_off(monkeypatch):
    """L2 integration: in OAG mode the workflow skill body is injected into the
    prompt for IP work EVEN WHEN prompt-injection is OFF (the normal skill block
    is injection-gated; OAG mode adds it independently). This is the headless gap
    the E2E exposed."""
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("OAG_ROOT", str(PROJECT_ROOT))   # vendored .codex skill (has keywords)
    monkeypatch.delenv("ATLAS_PROMPT_INJECTION", raising=False)
    monkeypatch.delenv("ENABLE_PROMPT_INJECTION", raising=False)

    from core.skill_system import get_skill_registry
    reg = get_skill_registry()
    sk_dir = str(PROJECT_ROOT / ".codex" / "skills")
    if sk_dir not in reg._loader.extra_dirs:
        reg._loader.extra_dirs.append(sk_dir)
    reg.reload_all_skills()

    import config as cfg_mod
    monkeypatch.setattr(cfg_mod, "ENABLE_SKILL_SYSTEM", True, raising=False)
    import src.main as M
    M.load_active_skills._active_skill = None
    M.load_active_skills._oag_last = None

    class _Cfg:
        CACHE_OPTIMIZATION_MODE = "optimized"
        ENABLE_SKILL_SYSTEM = True

    out = pb.build_system_prompt(
        messages=[{"role": "user", "content": "write the apb timer rtl and cocotb testbench"}],
        cfg=_Cfg(),
        build_base_fn=lambda **kw: "BASE",
        load_skills_fn=M.load_active_skills,
    )
    assert isinstance(out, dict)
    assert "OAG IP Workflow" in out["dynamic"]   # skill body injected despite injection OFF


def test_oag_pack_vendored_and_self_contained(monkeypatch, tmp_path):
    """The .codex OAG pack ships INSIDE common_ai_agent (vendored), so OAG mode is
    self-contained: oag_root falls back to the platform root even when the
    cwd/workspace has no .codex (no external ontology_ip_agent needed)."""
    repo = PROJECT_ROOT  # common_ai_agent
    assert (repo / ".codex" / "scripts" / "oag_cli.py").is_file()   # vendored gateway
    assert (repo / ".codex" / "AGENTS.md").is_file()                # vendored agent rules
    monkeypatch.delenv("OAG_ROOT", raising=False)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)            # a workspace with no .codex
    assert pb.oag_root() == repo           # resolves to the platform's vendored pack
