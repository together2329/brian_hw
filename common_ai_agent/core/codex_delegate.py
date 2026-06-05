import json
import os
import shlex
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Optional


DEFAULT_CODEX_TIMEOUT_SEC = 900


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class CodexDelegate:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def run(
        self,
        task: str,
        context: str = "",
        workflow_name: str = "",
        model_override: Optional[str] = None,
        system_prompt: Optional[str] = None,
        allowed_tools: Optional[Sequence[str]] = None,
        reasoning_effort: str = "",
        custom_agent_name: str = "",
    ) -> str:
        prompt = self._build_prompt(
            task=task,
            context=context,
            workflow_name=workflow_name,
            system_prompt=system_prompt or "",
            allowed_tools=allowed_tools or (),
            custom_agent_name=custom_agent_name,
        )
        workspace = self._workspace_path()
        cmd = self._build_cmd(
            workspace=workspace,
            model=model_override or os.environ.get("CODEX_CLI_MODEL", "").strip(),
            reasoning_effort=reasoning_effort,
        )
        timeout = _env_int("CODEX_CLI_TIMEOUT_SEC", DEFAULT_CODEX_TIMEOUT_SEC)

        try:
            proc = subprocess.run(
                args=cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=workspace,
            )
        except FileNotFoundError:
            return "[codex error] codex CLI not found. Install with: npm install -g @openai/codex"
        except subprocess.TimeoutExpired:
            return f"[codex error] Command timed out after {timeout}s"

        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
            return f"[codex error] {err}"
        return proc.stdout.strip() or "(no output)"

    def _workspace_path(self) -> Path:
        raw = os.environ.get("CODEX_CLI_WORKSPACE", "").strip()
        if not raw:
            return self.project_root
        path = Path(raw)
        if path.is_absolute():
            return path
        return self.project_root / path

    def _build_cmd(self, workspace: Path, model: str, reasoning_effort: str) -> list[str]:
        sandbox = os.environ.get("CODEX_CLI_SANDBOX", "workspace-write").strip() or "workspace-write"
        approval = os.environ.get("CODEX_CLI_APPROVAL_POLICY", "never").strip() or "never"
        cmd = [
            "codex",
            "exec",
            "--color",
            "never",
            "--sandbox",
            sandbox,
            "--ask-for-approval",
            approval,
        ]
        profile = os.environ.get("CODEX_CLI_PROFILE", "").strip()
        if profile:
            cmd.extend(["-p", profile])
        if model:
            cmd.extend(["-m", model])
        if reasoning_effort:
            cmd.extend(["-c", f"model_reasoning_effort={json.dumps(reasoning_effort)}"])
        extra_args = os.environ.get("CODEX_CLI_EXTRA_ARGS", "").strip()
        if extra_args:
            cmd.extend(shlex.split(extra_args))
        cmd.extend(["-C", str(workspace), "-"])
        return cmd

    def _build_prompt(
        self,
        task: str,
        context: str,
        workflow_name: str,
        system_prompt: str,
        allowed_tools: Sequence[str],
        custom_agent_name: str,
    ) -> str:
        sections: list[tuple[str, str]] = []
        if system_prompt:
            sections.append(("System Instructions", system_prompt))
        if custom_agent_name:
            sections.append(("Custom Agent", custom_agent_name))
        if workflow_name:
            sections.append(("Workflow", workflow_name))
        if allowed_tools:
            sections.append(("Allowed Tools", ", ".join(allowed_tools)))
        if context:
            sections.append(("Context", context))
        sections.append(("Task", task))
        return "\n\n".join(f"[{name}]\n{body}" for name, body in sections)
