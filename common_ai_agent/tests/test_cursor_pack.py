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
        text=True, env={"PATH": "/usr/bin:/bin"}, timeout=15)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_subagent_hook_blocks_claim_without_evidence():
    out = _run_subagent_hook({
        "subagent_type": "atlas-sim", "status": "completed",
        "summary": "시뮬레이션을 잘 마쳤고 모든 것이 정상으로 보입니다.", "loop_count": 0})
    assert "증거" in out.get("followup_message", "")


def test_subagent_hook_passes_with_evidence():
    for summary in ("sim gate PASS: 28/28 scoreboard, results.xml fresh",
                    "pytest: 11 passed; check_sim_disk rc=0"):
        out = _run_subagent_hook({
            "subagent_type": "atlas-sim", "status": "completed",
            "summary": summary, "loop_count": 0})
        assert out == {}, summary


def test_subagent_hook_ignores_non_owner_and_aborts():
    assert _run_subagent_hook({
        "subagent_type": "explorer", "status": "completed", "summary": "둘러봄"}) == {}
    assert _run_subagent_hook({
        "subagent_type": "atlas-sim", "status": "aborted", "summary": ""}) == {}


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


# ---------- rocev-chain skill: 실재 스크립트만 참조 ----------

def test_rocev_chain_references_existing_scripts():
    referenced = set()
    for doc in (CURSOR / "skills" / "rocev-chain" / "SKILL.md",
                CURSOR / "agents" / "atlas-req-gen.md",
                CURSOR / "agents" / "atlas-rocev-chain.md"):
        text = doc.read_text(encoding="utf-8")
        referenced |= set(re.findall(r"python3 (\S+\.py)", text))
    assert referenced, "rocev-chain references no scripts"
    for rel in sorted(referenced):
        assert (REPO / rel).is_file(), f"rocev-chain references missing script: {rel}"


def test_rocev_chain_subagent_owners_exist():
    text = (CURSOR / "agents" / "atlas-rocev-chain.md").read_text(encoding="utf-8")
    for owner in re.findall(r"`/(atlas-[a-z0-9-]+)`", text):
        assert (CURSOR / "agents" / f"{owner}.md").is_file(), f"owner subagent missing: {owner}"
