import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_codex_delegate_runs_codex_exec_with_stdin_prompt(monkeypatch, tmp_path):
    from core.codex_delegate import CodexDelegate

    seen = {}

    def fake_run(*, args, input, capture_output, text, encoding, errors, timeout, cwd):
        seen.update(
            {
                "args": args,
                "input": input,
                "capture_output": capture_output,
                "text": text,
                "encoding": encoding,
                "errors": errors,
                "timeout": timeout,
                "cwd": cwd,
            }
        )
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="done\n", stderr="progress\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("CODEX_CLI_SANDBOX", "workspace-write")
    monkeypatch.setenv("CODEX_CLI_APPROVAL_POLICY", "never")
    monkeypatch.setenv("CODEX_CLI_TIMEOUT_SEC", "123")

    out = CodexDelegate(project_root=tmp_path).run(
        task="fix the failing test",
        context="parent context",
        workflow_name="rtl-gen",
        model_override="gpt-5.4-codex",
        system_prompt="follow repo rules",
        reasoning_effort="high",
    )

    assert out == "done"
    assert seen["args"] == [
        "codex",
        "exec",
        "--color",
        "never",
        "--sandbox",
        "workspace-write",
        "--ask-for-approval",
        "never",
        "-m",
        "gpt-5.4-codex",
        "-c",
        "model_reasoning_effort=\"high\"",
        "-C",
        str(tmp_path),
        "-",
    ]
    assert seen["input"] == (
        "[System Instructions]\nfollow repo rules\n\n"
        "[Workflow]\nrtl-gen\n\n"
        "[Context]\nparent context\n\n"
        "[Task]\nfix the failing test"
    )
    assert seen["timeout"] == 123
    assert seen["cwd"] == tmp_path


def test_codex_delegate_reports_missing_binary(monkeypatch, tmp_path):
    from core.codex_delegate import CodexDelegate

    def fake_run(**_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", fake_run)

    out = CodexDelegate(project_root=tmp_path).run(task="summarize")

    assert "codex CLI not found" in out
