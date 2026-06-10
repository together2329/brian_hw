"""Cursor 팩 검증 — todo-loop hook 행동 계약 + 팩 참조 무결성.

evidence for (ontology/platform_requirements.yaml REQ_PLAT_CURSOR_PARITY_001):
  OBL_CURSOR_TODO_LOOP_HOOK            — stop hook의 stdin/stdout 계약
  OBL_CURSOR_PACK_REFERENTIAL_INTEGRITY — hooks.json/agents/skills 유령 참조 차단
  OBL_CURSOR_ROCEV_CHAIN_SKILL          — rocev-chain이 실재 스크립트만 참조
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CURSOR = REPO / ".cursor"
HOOK = CURSOR / "hooks" / "stop-todo-loop.py"


# ---------- todo-loop hook 행동 계약 ----------

def _run_hook(stdin_obj, todo_file=None, project_dir=None):
    env = {"PATH": "/usr/bin:/bin"}
    if todo_file is not None:
        env["TODO_FILE"] = str(todo_file)
    if project_dir is not None:
        env["CURSOR_PROJECT_DIR"] = str(project_dir)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(stdin_obj), capture_output=True, text=True,
        env=env, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _todo_file(tmp_path, todos):
    p = tmp_path / "current_todos.json"
    p.write_text(json.dumps({"todos": todos}, ensure_ascii=False), encoding="utf-8")
    return p


def test_hook_loops_while_todos_open(tmp_path):
    p = _todo_file(tmp_path, [
        {"content": "RTL 컴파일 고치기", "status": "in_progress", "criteria": "lint gate PASS"},
        {"content": "sim 돌리기", "status": "pending"},
        {"content": "이미 끝남", "status": "completed"},
    ])
    out = _run_hook({"status": "completed", "loop_count": 0}, todo_file=p)
    assert "followup_message" in out
    assert "2개" in out["followup_message"]
    assert "RTL 컴파일 고치기" in out["followup_message"]
    assert "이미 끝남" not in out["followup_message"]


def test_hook_silent_when_all_done(tmp_path):
    p = _todo_file(tmp_path, [
        {"content": "a", "status": "completed"},
        {"content": "b", "status": "approved"},
        {"content": "c", "status": "cancelled"},
    ])
    assert _run_hook({"status": "completed", "loop_count": 1}, todo_file=p) == {}


def test_hook_silent_on_abort_and_error(tmp_path):
    """사용자 중단/에러에 루프를 걸면 안 된다."""
    p = _todo_file(tmp_path, [{"content": "x", "status": "pending"}])
    for status in ("aborted", "error"):
        assert _run_hook({"status": status, "loop_count": 0}, todo_file=p) == {}


def test_hook_silent_when_file_missing_or_corrupt(tmp_path):
    assert _run_hook({"status": "completed"}, todo_file=tmp_path / "nope.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert _run_hook({"status": "completed"}, todo_file=bad) == {}


def test_hook_default_path_uses_project_dir(tmp_path):
    (tmp_path / "current_todos.json").write_text(
        json.dumps({"todos": [{"content": "프로젝트 기본 경로", "status": "pending"}]}),
        encoding="utf-8")
    out = _run_hook({"status": "completed"}, project_dir=tmp_path)
    assert "프로젝트 기본 경로" in out.get("followup_message", "")


# ---------- subagentStop 증거 hook ----------

SUBAGENT_HOOK = CURSOR / "hooks" / "subagent-evidence-check.py"


def _run_subagent_hook(stdin_obj):
    proc = subprocess.run(
        [sys.executable, str(SUBAGENT_HOOK)],
        input=json.dumps(stdin_obj, ensure_ascii=False), capture_output=True,
        text=True, env={"PATH": "/usr/bin:/bin", "CURSOR_PROJECT_DIR": str(REPO)},
        timeout=15)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_subagent_hook_blocks_claim_without_evidence():
    out = _run_subagent_hook({
        "subagent_type": "sim", "status": "completed",
        "summary": "시뮬레이션을 잘 마쳤고 모든 것이 정상으로 보입니다.", "loop_count": 0})
    assert "증거" in out.get("followup_message", "")


def test_subagent_hook_passes_with_evidence():
    for summary in ("sim gate PASS: 28/28 scoreboard, results.xml fresh",
                    "pytest: 11 passed; check_sim_disk rc=0"):
        out = _run_subagent_hook({
            "subagent_type": "sim", "status": "completed",
            "summary": summary, "loop_count": 0})
        assert out == {}, summary


def test_subagent_hook_ignores_readonly_unknown_and_aborts():
    # readonly 관찰자(explorer)와 미정의 subagent 는 면제, abort 에도 침묵
    assert _run_subagent_hook({
        "subagent_type": "explorer", "status": "completed", "summary": "둘러봄"}) == {}
    assert _run_subagent_hook({
        "subagent_type": "ghost-agent", "status": "completed", "summary": "?"}) == {}
    assert _run_subagent_hook({
        "subagent_type": "sim", "status": "aborted", "summary": ""}) == {}


# ---------- 루프 시뮬레이션: hook이 todo를 닫아가며 종료까지 가는가 ----------

def test_stop_loop_simulation_terminates(tmp_path):
    """todo를 하나씩 닫는 에이전트를 흉내내 루프가 정확히 N회로 끝나는지."""
    todos = [{"content": f"task-{i}", "status": "pending"} for i in range(3)]
    p = _todo_file(tmp_path, todos)
    loops = 0
    while loops < 10:
        out = _run_hook({"status": "completed", "loop_count": loops}, todo_file=p)
        if out == {}:
            break
        loops += 1
        for t in todos:  # 에이전트가 todo 하나를 완료
            if t["status"] != "completed":
                t["status"] = "completed"
                break
        p.write_text(json.dumps({"todos": todos}), encoding="utf-8")
    assert loops == 3  # 3개 todo → 정확히 3번 followup 후 종료


# ---------- 팩 참조 무결성 (유령 참조 차단) ----------

def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path}: missing frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def test_hooks_json_commands_exist_and_are_python():
    doc = json.loads((CURSOR / "hooks.json").read_text(encoding="utf-8"))
    assert doc.get("version") == 1
    commands = [h["command"] for hooks in doc["hooks"].values() for h in hooks]
    assert commands, "hooks.json declares no hooks"
    for cmd in commands:
        script = REPO / cmd
        assert script.is_file(), f"hooks.json references missing script: {cmd}"
        head = script.read_text(encoding="utf-8").splitlines()[0]
        assert head.startswith("#!"), f"{cmd}: missing shebang"


def test_stop_todo_loop_registered_with_real_loop_limit():
    doc = json.loads((CURSOR / "hooks.json").read_text(encoding="utf-8"))
    stops = {h["command"]: h for h in doc["hooks"].get("stop", [])}
    entry = stops.get(".cursor/hooks/stop-todo-loop.py")
    assert entry, "stop-todo-loop.py not registered as a stop hook"
    assert entry.get("loop_limit", 0) >= 2, "todo loop needs loop_limit ≥ 2 to actually loop"


def test_agents_frontmatter_valid():
    agents = sorted((CURSOR / "agents").glob("*.md"))
    assert agents
    for path in agents:
        fm = _frontmatter(path)
        assert fm.get("name"), f"{path.name}: name missing"
        assert fm.get("description"), f"{path.name}: description missing"
        assert re.fullmatch(r"[a-z0-9-]+", fm["name"]), f"{path.name}: name not kebab-case"


def test_rules_frontmatter_valid():
    rules = sorted((CURSOR / "rules").glob("*.mdc"))
    assert rules
    for path in rules:
        fm = _frontmatter(path)
        assert fm.get("description"), f"{path.name}: description missing"


def test_mcp_json_valid_and_server_exists():
    doc = json.loads((CURSOR / "mcp.json").read_text(encoding="utf-8"))
    for name, server in doc["mcpServers"].items():
        for arg in server.get("args", []):
            if arg.endswith(".py"):
                assert (REPO / arg).is_file(), f"mcp server {name}: missing {arg}"


def test_skills_name_matches_folder():
    skills = sorted((CURSOR / "skills").glob("*/SKILL.md"))
    assert skills
    for path in skills:
        fm = _frontmatter(path)
        assert fm.get("name") == path.parent.name, (
            f"{path}: frontmatter name {fm.get('name')!r} != folder {path.parent.name!r}")
        assert fm.get("description"), f"{path}: description missing"


# ---------- 자가포함(단독 전달) 증명 ----------

def test_vendor_manifest_in_sync():
    """ratchet: 정본(workflow/엔진/헬퍼)이 바뀌면 sync 전까지 빨간불."""
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "sync_cursor_pack.py"), "check"],
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_pack_is_self_contained(tmp_path):
    """.cursor만 복사한 '전달본'에서 엔진/게이트/ip_wiki/MCP가 repo 없이 돈다."""
    import shutil
    fake = tmp_path / "delivered_project"
    fake.mkdir()
    shutil.copytree(CURSOR, fake / ".cursor",
                    ignore=shutil.ignore_patterns("__pycache__"))
    env = {"PATH": "/usr/bin:/bin"}

    def run(args, **kw):
        return subprocess.run([sys.executable, *args], cwd=fake, env=env,
                              capture_output=True, text=True, timeout=90, **kw)

    # 1. 러너가 vendored 엔진(.cursor/src)으로 import 성공
    r = run([".cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py", "--help"])
    assert r.returncode == 0 and "usage" in (r.stdout + r.stderr).lower(), r.stderr[-400:]

    # 2. vendored 게이트가 단독 실행 (정상적 FAIL verdict — crash 아님)
    r = run([".cursor/workflow/sim/scripts/check_sim_disk.py", "ghost_ip"])
    assert r.returncode == 1 and "check_sim_disk" in r.stdout, r.stderr[-400:]

    # 3. vendored ip_wiki 라운드트립
    (fake / "demo_ip").mkdir()
    assert run([".cursor/scripts/ip_wiki.py", "init", "demo_ip"]).returncode == 0
    assert run([".cursor/scripts/ip_wiki.py", "log", "demo_ip",
                "--title", "standalone OK"]).returncode == 0
    assert run([".cursor/scripts/ip_wiki.py", "check", "demo_ip"]).returncode == 0

    # 4. vendored MCP 서버 handshake
    msgs = (json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18"}}) + "\n"
            + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + "\n")
    r = run([".cursor/scripts/atlas_mcp_server.py"], input=msgs)
    assert r.returncode == 0
    names = set()
    for line in r.stdout.splitlines():
        msg = json.loads(line)
        if msg.get("id") == 2:
            names = {t["name"] for t in msg["result"]["tools"]}
    assert "rtl_db_query" in names


# ---------- rocev-chain skill: 실재 스크립트만 참조 ----------

def test_rocev_chain_references_existing_scripts():
    referenced = set()
    for doc in (CURSOR / "skills" / "rocev-chain" / "SKILL.md",
                CURSOR / "agents" / "req-gen.md",
                CURSOR / "agents" / "rocev-chain.md"):
        text = doc.read_text(encoding="utf-8")
        refs = re.findall(r"python3 (\S+\.py)", text)
        referenced |= {r for r in refs if "<" not in r}  # <ip> 플레이스홀더 제외
    assert referenced, "rocev-chain references no scripts"
    for rel in sorted(referenced):
        assert (REPO / rel).is_file(), f"rocev-chain references missing script: {rel}"


def test_workflow_families_have_agents():
    """모든 활성 workflow family에 owner agent 존재 (system prompt 기반)."""
    SKIP = {"mas-gen", "default", "worker", "cmux", "chat-responder", "eda",
            "prompts", "scripts", "wiki", "ip-contract", "orchestrator"}
    fam_alias = {"sim_debug": "sim-debug", "signoff": "signoff-runner"}
    missing = []
    for d in sorted((REPO / "workflow").iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name in SKIP:
            continue
        if not (d / "system_prompt.md").is_file() and not (d / "scripts").is_dir():
            continue
        name = fam_alias.get(d.name, d.name)
        if not ((CURSOR / "agents" / f"{name}.md").is_file()
                or (CURSOR / "agents" / f"{name.replace('-gen', '')}.md").is_file()):
            missing.append(d.name)
    assert missing == [], f"workflow families without owner agent: {missing}"


def test_orchestrator_routes_every_stage_owner():
    """orchestrator 라우팅 표의 owner들이 전부 실재 + 핵심 스테이지 망라."""
    text = (CURSOR / "agents" / "orchestrator.md").read_text(encoding="utf-8")
    owners = set(re.findall(r"`/([a-z0-9-]+)`", text))
    for required in ("ssot-gen", "req-gen", "rtl-gen", "tb-gen", "sim", "lint",
                     "coverage", "mutation", "syn", "pnr", "sta", "signoff-runner",
                     "verifier", "hephaestus"):
        assert required in owners, f"orchestrator routing missing: {required}"
    for owner in owners:
        assert (CURSOR / "agents" / f"{owner}.md").is_file(), f"routed owner missing: {owner}"


def test_rocev_chain_subagent_owners_exist():
    text = (CURSOR / "agents" / "rocev-chain.md").read_text(encoding="utf-8")
    owners = re.findall(r"`/([a-z0-9-]+)`", text)
    assert owners, "rocev-chain declares no stage owners"
    for owner in owners:
        assert (CURSOR / "agents" / f"{owner}.md").is_file(), f"owner subagent missing: {owner}"


def test_no_atlas_prefixed_names_under_cursor():
    """ratchet: 팩 식별자(파일/폴더명)에 atlas- 접두어 금지 (2026-06-10 지시).

    .cursor/workflow 는 정본 미러(vendor)라서 면제 — 정본 파일명을 바꾸면
    엔진/manifest 가 깨진다."""
    offenders = [p for p in CURSOR.rglob("atlas-*")
                 if "atlas-" in p.name
                 and ".cursor/workflow/" not in p.as_posix()]
    assert offenders == [], f"atlas-prefixed names remain: {offenders}"
