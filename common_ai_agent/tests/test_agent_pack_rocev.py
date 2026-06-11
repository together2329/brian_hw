from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


def parse_simple_toml(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    lines = iter(text.splitlines())
    for line in lines:
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value == '"""':
            chunk = []
            for inner in lines:
                if inner == '"""':
                    break
                chunk.append(inner)
            result[key] = "\n".join(chunk)
        elif value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1]
        else:
            result[key] = value
    return result


def run_python(script: Path, payload: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


def test_codex_pack_shapes_are_parseable():
    hooks = json.loads((REPO / ".codex_ref/hooks.json").read_text(encoding="utf-8"))
    assert "SessionStart" in hooks["hooks"]
    assert "UserPromptSubmit" in hooks["hooks"]
    assert "PreToolUse" in hooks["hooks"]
    assert "PostToolUse" in hooks["hooks"]
    assert "Stop" in hooks["hooks"]

    for agent_path in sorted((REPO / ".codex_ref/agents").glob("*.toml")):
        agent = parse_simple_toml(agent_path.read_text(encoding="utf-8"))
        assert {"name", "description", "developer_instructions"} <= set(agent)

    for skill_path in sorted((REPO / ".agents/skills").glob("*/SKILL.md")):
        text = skill_path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "\nname:" in text
        assert "\ndescription:" in text


def test_cursor_new_pack_shapes_are_parseable():
    hooks = json.loads((REPO / ".cursor_new/hooks.json").read_text(encoding="utf-8"))
    assert "sessionStart" in hooks["hooks"]
    assert "beforeSubmitPrompt" in hooks["hooks"]
    assert "beforeShellExecution" in hooks["hooks"]
    assert "afterFileEdit" in hooks["hooks"]
    assert "stop" in hooks["hooks"]

    for rule_path in sorted((REPO / ".cursor_new/rules").glob("*.mdc")):
        text = rule_path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "description:" in text

    for skill_path in sorted((REPO / ".cursor_new/skills").glob("*/SKILL.md")):
        text = skill_path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "\nname:" in text
        assert "\ndescription:" in text

    for agent_path in sorted((REPO / ".cursor_new/agents").glob("*.md")):
        text = agent_path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "\nname:" in text
        assert "\ndescription:" in text


def test_codex_hooks_block_shallow_evidence_shortcuts():
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "grep PASS pwm_gen_cx1/sim/results.xml",
        },
    }
    result = run_python(REPO / ".codex_ref/hooks/rocev_pre_tool_use.py", payload)
    assert result["decision"] == "block"
    assert "Requirement" in result["reason"]

    stop_payload = {
        "hook_event_name": "Stop",
        "last_assistant_message": "RTL sim passed and tests passed.",
    }
    result = run_python(REPO / ".codex_ref/hooks/rocev_stop_reminder.py", stop_payload)
    assert result["decision"] == "block"
    assert "Requirement" in result["reason"]

    destructive_payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "git -C pwm_gen_cx1 reset --hard HEAD",
        },
    }
    result = run_python(REPO / ".codex_ref/hooks/rocev_pre_tool_use.py", destructive_payload)
    assert result["decision"] == "block"
    assert "IP-local git/wiki memory" in result["reason"]

    cursor_payload = {"command": "grep PASS pwm_gen_cx1/sim/results.xml"}
    result = run_python(REPO / ".cursor_new/hooks/guard-rocev-evidence.py", cursor_payload)
    assert result["permission"] == "ask"
    assert "PASS string" in result["user_message"]

    cursor_destructive_payload = {"command": "rm -rf pwm_gen_cx1/.git"}
    result = run_python(REPO / ".cursor_new/hooks/guard-rocev-evidence.py", cursor_destructive_payload)
    assert result["permission"] == "ask"
    assert "IP-local git/wiki memory" in result["user_message"]


def test_ip_dev_memory_hooks_are_declared():
    codex_hooks = json.loads((REPO / ".codex_ref/hooks.json").read_text(encoding="utf-8"))
    codex_commands = [
        hook["command"]
        for groups in codex_hooks["hooks"].values()
        for group in groups
        for hook in group.get("hooks", [])
    ]
    assert any("ip_dev_memory.py" in command and "hook-session" in command for command in codex_commands)
    assert any("ip_dev_memory.py" in command and "hook-file-edit" in command for command in codex_commands)
    assert any("ip_dev_memory.py" in command and "hook-stop" in command for command in codex_commands)

    cursor_hooks = json.loads((REPO / ".cursor_new/hooks.json").read_text(encoding="utf-8"))
    cursor_commands = [hook["command"] for hooks in cursor_hooks["hooks"].values() for hook in hooks]
    assert ".cursor/hooks/ip-dev-memory-session.py" in cursor_commands
    assert ".cursor/hooks/ip-dev-memory-stop.py" in cursor_commands


def test_rocev_ip_audit_finds_ten_real_ip_examples():
    ips = [
        "pwm_gen_cx1",
        "fifo_sync_cx1",
        "counter8_cx1",
        "debounce_cx1",
        "edge_det_cx1",
        "gray_code_cx1",
        "parity_gen_cx1",
        "shift_reg_cx1",
        "uart_tx_lite_cx1",
        "watchdog_cx1",
        "mctp_assembler_v3",
    ]
    proc = subprocess.run(
        [sys.executable, ".codex_ref/scripts/rocev_ip_audit.py", *ips],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert data["count"] >= 10
    names = {item["ip"] for item in data["results"]}
    assert "pwm_gen_cx1" in names
    assert "mctp_assembler_v3" in names
    assert all(item["validation"] in {"closed", "partial", "open"} for item in data["results"])
