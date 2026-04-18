"""
Delegate Runner — Backend routing for task delegation

Routes a todo task to the appropriate execution backend:
  - SubAgentDelegate: runs run_agent_session() with full workspace config
  - CursorAgentDelegate: wraps cursor-agent CLI
  - CodexDelegate: subprocess call to codex CLI
  - GeminiDelegate: subprocess call to gemini CLI
  - APIDelegate: direct LLM API call

All delegates accept any workflow name dynamically — zero hardcoded names.
"""

import os
import sys
import json
import subprocess
import traceback
from pathlib import Path
from typing import Any, Optional

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)


class DelegateRunner:
    """Routes a todo task to the appropriate execution backend."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._backends = {
            "sub-agent": SubAgentDelegate,
            "cursor-agent": CursorAgentDelegate,
            "codex": CodexDelegate,
            "gemini": GeminiDelegate,
            "api": APIDelegate,
        }

    def run(self, backend: str, task: str, context: str = "",
            workflow_name: str = "", tier: str = "sub") -> str:
        """
        Execute task via the specified backend.

        Args:
            backend: Backend name (sub-agent, cursor-agent, codex, gemini, api)
            task: Task description
            context: Parent agent context
            workflow_name: Workflow to load config from (any name, dynamic)
            tier: "sub" (32K, limited tools) | "main" (200K, all tools)

        Returns:
            Result string from the backend
        """
        cls = self._backends.get(backend)
        if not cls:
            available = ", ".join(sorted(self._backends.keys()))
            raise ValueError(
                f"Unknown delegate backend: '{backend}'. "
                f"Available: {available}"
            )

        delegate = cls(project_root=self.project_root)
        return delegate.run(task, context, workflow_name=workflow_name, tier=tier)

    @staticmethod
    def list_backends() -> list:
        """Return list of available backend names."""
        return ["sub-agent", "cursor-agent", "codex", "gemini", "api"]


# ============================================================
# Backend: Sub-Agent (loads full workspace config)
# ============================================================

class SubAgentDelegate:
    """
    Runs a sub-agent session with the full workspace config loaded.
    
    Loads system_prompt, skills, tools, rules from the specified workflow
    directory. Any workflow name works — zero hardcoded names.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def run(self, task: str, context: str = "", workflow_name: str = "",
            tier: str = "sub") -> str:
        """Execute task via sub-agent with workspace config."""
        from core.agent_runner import run_agent_session

        # Build system prompt from workflow config if specified
        system_prompt = None
        if workflow_name:
            system_prompt = self._build_workflow_prompt(workflow_name)

        # Build full prompt with context
        full_prompt = task
        if context:
            full_prompt = f"[Context from primary agent]\n{context}\n\n[Task]\n{task}"

        result = run_agent_session(
            agent_name="execute",
            prompt=full_prompt,
            system_prompt=system_prompt,
            parent_context=context,
            compress_result=True,
            max_result_chars=8000,
            verbose=False,
            workflow_name=workflow_name,
            tier=tier,
        )

        if result.status == "error":
            return f"[Sub-agent error] {result.error or result.output}"
        return result.output

    def _build_workflow_prompt(self, workflow_name: str) -> Optional[str]:
        """Load system prompt from workflow config."""
        try:
            from workflow.loader import load_workspace
            ws = load_workspace(workflow_name, self.project_root)
            if ws and ws.system_prompt_text:
                # Load base execute prompt and merge
                base = self._load_base_prompt("execute")
                if base:
                    from workflow.loader import merge_prompt
                    return merge_prompt(base, ws.system_prompt_text, ws.system_prompt_mode)
                return ws.system_prompt_text
        except Exception:
            pass
        return None

    def _load_base_prompt(self, agent_name: str) -> Optional[str]:
        """Load base agent prompt from workflow/prompts/."""
        prompt_path = self.project_root / "workflow" / "prompts" / f"{agent_name}.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8").strip()
        return None


# ============================================================
# Backend: Cursor-Agent CLI
# ============================================================

class CursorAgentDelegate:
    """Delegates to cursor-agent CLI for execution."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def run(self, task: str, context: str = "", workflow_name: str = "") -> str:
        """Execute task via cursor-agent CLI."""
        try:
            import config as _cfg
        except ImportError:
            import src.config as _cfg

        model = getattr(_cfg, "CURSOR_AGENT_MODEL", "auto")
        workspace = getattr(_cfg, "CURSOR_AGENT_WORKSPACE", "")
        yolo = getattr(_cfg, "CURSOR_AGENT_YOLO", False)
        mode = getattr(_cfg, "CURSOR_AGENT_MODE", "")

        cmd = ["cursor-agent", "--print", "--model", model or "auto",
               "--output-format", "stream-json", "--stream-partial-output"]
        if yolo:
            cmd.append("--yolo")
        if mode:
            cmd += ["--mode", mode]
        if workspace:
            cmd += ["--workspace", workspace]

        # Combine context and task
        full_prompt = task
        if context:
            full_prompt = f"[Context]\n{context}\n\n[Task]\n{task}"
        cmd += ["-p", full_prompt]

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1,
            )
            collected = []
            for raw_line in proc.stdout:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    chunk = json.loads(raw_line)
                    if chunk.get("type") == "assistant" and "timestamp_ms" in chunk:
                        for block in chunk.get("message", {}).get("content", []):
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block.get("text", "")
                                if text:
                                    collected.append(text)
                except json.JSONDecodeError:
                    continue

            proc.stdout.close()
            proc.wait()

            result = "".join(collected).strip()
            if not result and proc.returncode != 0:
                stderr = proc.stderr.read() if proc.stderr else ""
                return f"[cursor-agent error] {stderr.strip() or f'exit code {proc.returncode}'}"
            return result or "(no output)"
        except FileNotFoundError:
            return "[cursor-agent error] cursor-agent not found. Install it or check PATH."


# ============================================================
# Backend: Codex CLI
# ============================================================

class CodexDelegate:
    """Delegates to OpenAI Codex CLI."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def run(self, task: str, context: str = "", workflow_name: str = "") -> str:
        """Execute task via codex CLI."""
        full_prompt = task
        if context:
            full_prompt = f"[Context]\n{context}\n\n[Task]\n{task}"

        try:
            proc = subprocess.run(
                ["codex", "--quiet", full_prompt],
                capture_output=True, text=True, timeout=300,
            )
            if proc.returncode != 0:
                return f"[codex error] {proc.stderr.strip() or f'exit code {proc.returncode}'}"
            return proc.stdout.strip() or "(no output)"
        except FileNotFoundError:
            return "[codex error] codex CLI not found. Install with: npm install -g @openai/codex"
        except subprocess.TimeoutExpired:
            return "[codex error] Command timed out after 300s"


# ============================================================
# Backend: Gemini CLI
# ============================================================

class GeminiDelegate:
    """Delegates to Google Gemini CLI."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def run(self, task: str, context: str = "", workflow_name: str = "") -> str:
        """Execute task via gemini CLI."""
        full_prompt = task
        if context:
            full_prompt = f"[Context]\n{context}\n\n[Task]\n{task}"

        try:
            proc = subprocess.run(
                ["gemini", "-p", full_prompt],
                capture_output=True, text=True, timeout=300,
            )
            if proc.returncode != 0:
                return f"[gemini error] {proc.stderr.strip() or f'exit code {proc.returncode}'}"
            return proc.stdout.strip() or "(no output)"
        except FileNotFoundError:
            return "[gemini error] gemini CLI not found. Install Google Gemini CLI."
        except subprocess.TimeoutExpired:
            return "[gemini error] Command timed out after 300s"


# ============================================================
# Backend: Direct LLM API Call
# ============================================================

class APIDelegate:
    """Delegates via direct LLM API call (same endpoint/key as primary)."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def run(self, task: str, context: str = "", workflow_name: str = "") -> str:
        """Execute task via direct LLM API call."""
        try:
            if _project_root not in sys.path:
                sys.path.insert(0, _project_root)
            if os.path.join(_project_root, 'src') not in sys.path:
                sys.path.insert(0, os.path.join(_project_root, 'src'))

            from llm_client import call_llm_raw

            full_prompt = task
            if context:
                full_prompt = f"[Context]\n{context}\n\n[Task]\n{task}"

            result = call_llm_raw(prompt=full_prompt)
            if not result or result.startswith("Error"):
                return f"[api error] {result}"
            return result
        except Exception as e:
            return f"[api error] {e}\n{traceback.format_exc()}"
