"""IP development memory helper checks.

evidence for: OBL_IP_DEV_MEMORY_INIT_GIT_WIKI
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("ip_dev_memory", REPO / "scripts" / "ip_dev_memory.py")
ipdm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ipdm)


def make_ip(tmp_path: Path, name: str = "pwm_demo_cx1") -> Path:
    ip = tmp_path / name
    (ip / "req").mkdir(parents=True)
    (ip / "rtl").mkdir()
    (ip / "req" / "locked_truth.md").write_text("# truth\n", encoding="utf-8")
    return ip


def test_init_creates_wiki_and_ip_local_git(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("COMMON_AI_AGENT_ROOT", str(REPO))
    ip = make_ip(tmp_path)

    result = ipdm.init_ip(ip)

    assert result["ip"] == "pwm_demo_cx1"
    assert (ip / "wiki" / "index.md").is_file()
    assert (ip / "wiki" / "log.md").is_file()
    assert (ip / "wiki" / "llm_memory.md").is_file()
    assert (ip / "wiki" / "git.md").is_file()
    assert (ip / ".git").is_dir()
    assert subprocess.run(["git", "-C", str(ip), "status", "--short"], capture_output=True).returncode == 0


def test_log_and_snapshot_create_resumable_history(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("COMMON_AI_AGENT_ROOT", str(REPO))
    ip = make_ip(tmp_path)

    assert ipdm.main(["init", str(ip)]) == 0
    assert ipdm.main(
        [
            "log",
            str(ip),
            "--stage",
            "sim",
            "--title",
            "scoreboard reviewed",
            "--body",
            "Observed expected pwm_out rows.",
            "--evidence",
            "sim/scoreboard_events.jsonl",
        ]
    ) == 0
    assert ipdm.main(["snapshot", str(ip), "--message", "sim: record scoreboard review"]) == 0

    memory = (ip / "wiki" / "llm_memory.md").read_text(encoding="utf-8")
    assert "scoreboard reviewed" in memory
    assert "sim/scoreboard_events.jsonl" in memory
    log = subprocess.run(
        ["git", "-C", str(ip), "log", "--oneline"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    assert "sim: record scoreboard review" in log
    assert ipdm.main(["check", str(ip), "--require-git"]) == 0


def test_hook_session_detects_ip_from_prompt(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("COMMON_AI_AGENT_ROOT", str(REPO))
    monkeypatch.setenv("IP_DEV_MEMORY_WORKSPACE_ROOT", str(tmp_path))
    ip = make_ip(tmp_path, "timer_irq_cx1")

    payload = {"prompt": "timer_irq_cx1 RTL을 이어서 개발해줘"}
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "ip_dev_memory.py"), "hook-session", "--surface", "codex"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "COMMON_AI_AGENT_ROOT": str(REPO),
            "IP_DEV_MEMORY_WORKSPACE_ROOT": str(tmp_path),
        },
        check=True,
    )

    data = json.loads(proc.stdout)
    assert "hookSpecificOutput" in data
    assert "timer_irq_cx1" in data["hookSpecificOutput"]["additionalContext"]
    assert (ip / "wiki" / "llm_memory.md").is_file()
    assert (ip / ".git").is_dir()


def test_hook_session_does_not_treat_workspace_root_as_ip(tmp_path: Path):
    (tmp_path / "rtl").mkdir()

    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "ip_dev_memory.py"), "hook-session", "--surface", "codex"],
        input=json.dumps({}),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env={
            **os.environ,
            "COMMON_AI_AGENT_ROOT": str(REPO),
            "IP_DEV_MEMORY_WORKSPACE_ROOT": str(tmp_path),
        },
        check=True,
    )

    assert json.loads(proc.stdout) == {}
    assert not (tmp_path / ".git").exists()
    assert not (tmp_path / "wiki").exists()


def test_hook_stop_blocks_missing_git_for_detected_ip(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("COMMON_AI_AGENT_ROOT", str(REPO))
    monkeypatch.setenv("IP_DEV_MEMORY_WORKSPACE_ROOT", str(tmp_path))
    ip = make_ip(tmp_path, "edge_irq_cx1")
    ipdm.load_ip_wiki(REPO).cmd_init(str(ip))

    payload = {"last_assistant_message": "edge_irq_cx1 RTL work is complete."}
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "ip_dev_memory.py"), "hook-stop", "--surface", "codex"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "COMMON_AI_AGENT_ROOT": str(REPO),
            "IP_DEV_MEMORY_WORKSPACE_ROOT": str(tmp_path),
        },
        check=True,
    )

    data = json.loads(proc.stdout)
    assert data["decision"] == "block"
    assert "missing IP-local .git" in data["reason"]
