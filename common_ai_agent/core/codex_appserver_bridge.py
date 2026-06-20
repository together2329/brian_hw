"""Codex app-server bridge for the atlas `/ws/agent` chat.

Flag-gated via the `CODEX_BRIDGE` env var. When enabled, a conversational
prompt from the atlas chat is run through `codex app-server` (stdio JSON-RPC)
instead of the built-in Python ReAct engine, and the streamed result is emitted
back through the SAME `session.emit(...)` envelope the frontend already
consumes:

    agent_state(running=True) -> token(text=...) / reasoning(text=...)
                              -> tool / tool_result -> flush -> agent_state(running=False) -> done

Talking to codex over stdio needs no extra deps (asyncio subprocess + json).
One persistent app-server process + thread is kept per atlas session_id, so the
conversation has multi-turn memory. Turns on a session are serialized.

Env:
  CODEX_BRIDGE       "1" to enable (checked by the caller in atlas_ui.py)
  CODEX_BRIDGE_BIN   codex binary (default "codex" on PATH)
  CODEX_BRIDGE_HOME  source .codex pack to stage (repo-relative paths supported)
  CODEX_BRIDGE_RUNTIME_HOME optional CODEX_HOME override; default keeps ~/.codex
  CODEX_BRIDGE_MODEL optional model override for the thread
  CODEX_BRIDGE_OAG_ROOT OAG pack/project root visible to the app-server process
  CODEX_BRIDGE_ENABLE_HOOKS "1" to enable Codex hook/plugin features
  CODEX_BRIDGE_RUN_OAG_HOOKS "1" to run staged OAG prompt hooks before each turn
  CODEX_BRIDGE_STAGE_DOT_CODEX "1" to stage OAG pack runtime files in thread cwd
  CODEX_BRIDGE_TRUST_THREAD_CWD "1" to trust the thread cwd in CODEX_HOME config
  CODEX_BRIDGE_BYPASS_HOOK_TRUST "1" to run staged hooks in app-server automation
  CODEX_BRIDGE_OAG_MODE OAG_MODE visible to the codex app-server process
                        (default "0" so native ATLAS OAG injection stays off)
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable

CODEX_BIN = os.environ.get("CODEX_BRIDGE_BIN", "codex")
CODEX_MODEL = os.environ.get("CODEX_BRIDGE_MODEL")
_REPO_ROOT = Path(__file__).resolve().parents[1]

# A single JSON-RPC notification line can be large (e.g. a command's full
# aggregatedOutput). asyncio's StreamReader defaults to a 64KB line limit and
# RAISES on overflow, which would otherwise crash the read loop and hang the
# turn forever. Give it a generous buffer.
_STREAM_LIMIT = int(os.environ.get("CODEX_BRIDGE_STREAM_LIMIT", str(64 * 1024 * 1024)))
# Control-RPC timeout (initialize / thread.start / turn.start ack).
_CALL_TIMEOUT = float(os.environ.get("CODEX_BRIDGE_CALL_TIMEOUT", "60"))
# Whole-turn timeout: never leave the frontend stuck on "running" forever.
_TURN_TIMEOUT = float(os.environ.get("CODEX_BRIDGE_TURN_TIMEOUT", "180"))
_TOOL_ONLY_FALLBACK_LIMIT = int(os.environ.get("CODEX_BRIDGE_TOOL_FALLBACK_LIMIT", "4000"))
_HOOK_TIMEOUT = float(os.environ.get("CODEX_BRIDGE_HOOK_TIMEOUT", "10"))
_STAGED_DOT_CODEX_MARKER = ".atlas_codex_bridge_source"
_RUNTIME_DOT_CODEX_ENTRIES = (
    "AGENTS.md",
    "config.toml",
    "hooks",
    "hooks.json",
    "mcp.json",
    "rules",
    "scripts",
    "skills",
)

_conns: "dict[str, _CodexConn]" = {}
_conns_lock = asyncio.Lock()

# item.type values that are NOT surfaced as tool activity
_NON_TOOL_ITEMS = {"userMessage", "agentMessage", "reasoning"}

# codex multi-agent (subagent) ThreadItem types. These are surfaced through a
# dedicated `subagent` envelope (the atlas left-rail lanes) instead of generic
# main-feed tool activity, so the user can watch each `/subagent` separately.
_COLLAB_ITEM = "collabAgentToolCall"
_SUBAGENT_ACTIVITY_ITEM = "subAgentActivity"
_SUBAGENT_ITEMS = {_COLLAB_ITEM, _SUBAGENT_ACTIVITY_ITEM}

# codex CollabAgentStatus / SubAgentActivityKind -> atlas lane status token.
_COLLAB_STATUS = {
    "pendinginit": "spawning", "running": "running", "interrupted": "closed",
    "completed": "completed", "errored": "failed", "shutdown": "closed",
    "notfound": "failed",
}
_SUBACTIVITY_STATUS = {
    "started": "running", "interacted": "running", "interrupted": "closed",
}

# Optionally force codex into multi-agent mode so an explicit `/subagent`
# spawns a sub-thread. DEFAULT OFF: the bridge only SURFACES whatever subagent
# activity codex already emits (codex's own config/skills drive spawning), so
# enabling here is unnecessary and would change the app-server process command
# for every codex-mode user. Set CODEX_BRIDGE_MULTI_AGENT_MODE=explicitRequestOnly
# (or proactive) to have the bridge force-enable it on builds that support it.
_MULTI_AGENT_MODE = os.environ.get("CODEX_BRIDGE_MULTI_AGENT_MODE", "").strip()
# Cap any single lane transcript chunk so a runaway child cannot flood the WS.
_SUBAGENT_TEXT_LIMIT = int(os.environ.get("CODEX_BRIDGE_SUBAGENT_TEXT_LIMIT", "8000"))


def _norm(value: "Any") -> str:
    return str(value or "").strip().lower()


def _short_tid(tid: "Any") -> str:
    """A distinct short label for a codex thread id. codex thread ids are
    time-ordered, so the first 8 chars collide across a spawn batch (a whole
    team reads the same); include the 2nd uuid group to keep lanes distinct."""
    parts = str(tid or "").split("-")
    if len(parts) >= 2 and parts[1]:
        return f"{parts[0][:8]}-{parts[1]}"
    return str(tid or "")[:8]


def _multi_agent_enabled() -> bool:
    return _norm(_MULTI_AGENT_MODE) not in {"", "off", "none", "0", "false", "disabled"}


def _collab_agent_ids(item: dict) -> "list[str]":
    """Lane keys for a collabAgentToolCall item: the receiver thread(s) (the
    spawned/targeted agent), falling back to the sender thread."""
    rids = item.get("receiverThreadIds") or []
    if isinstance(rids, str):
        rids = [rids]
    ids = [str(r) for r in rids if r]
    if ids:
        return ids
    sender = item.get("senderThreadId")
    return [str(sender)] if sender else []


def _subagent_lane_events(item: dict, started: bool, main_thread_id: str) -> "list[dict]":
    """Map a codex subagent ThreadItem (collabAgentToolCall / subAgentActivity)
    to zero or more `subagent` envelope payloads. Pure (no I/O) so it is unit
    testable; on_note adds sticky labels."""
    itype = item.get("type")
    out: "list[dict]" = []
    if itype == _SUBAGENT_ACTIVITY_ITEM:
        tid = str(item.get("agentThreadId") or "")
        if not tid or tid == main_thread_id:
            return out
        path = str(item.get("agentPath") or "")
        kind = _norm(item.get("kind"))
        out.append({
            "agent_id": tid, "parent_id": main_thread_id,
            "label": path or _short_tid(tid),
            "status": _SUBACTIVITY_STATUS.get(kind, "running"),
            "kind": "status",
            "text": (f"{kind} · {path}".strip(" ·") or "activity"),
        })
        return out
    if itype == _COLLAB_ITEM:
        tool = _norm(item.get("tool"))
        prompt = str(item.get("prompt") or "")
        states = item.get("agentsStates") or {}
        for tid in _collab_agent_ids(item):
            # The parent thread itself is not a subagent lane. During a spawn's
            # `item/started` phase the child thread id is not assigned yet, so
            # _collab_agent_ids falls back to the sender (= parent); skip it so
            # we never create a lane keyed to main (which would pollute the
            # synthesized Main row in the UI).
            if not tid or tid == main_thread_id:
                continue
            st = _COLLAB_STATUS.get(_norm((states.get(tid) or {}).get("status")), "")
            status = st or ("running" if started else "completed")
            if "spawn" in tool:
                kind, text = "spawn", (prompt or "(spawned agent)")
            elif "send" in tool or "input" in tool:
                kind, text = "message", prompt
            elif "wait" in tool:
                kind, text = "status", "waiting"
            elif "close" in tool:
                kind, text = "status", "closed"
            elif "resume" in tool:
                kind, text = "status", "resumed"
            else:
                kind, text = "status", (tool or "collab")
            out.append({
                "agent_id": tid, "parent_id": main_thread_id,
                "label": "", "status": status, "kind": kind,
                "text": text[:_SUBAGENT_TEXT_LIMIT],
            })
    return out


def _toml_quoted_key(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _app_server_cmd(cwd: "str | None" = None) -> list[str]:
    cmd = [CODEX_BIN]
    if _truthy_env(os.environ.get("CODEX_BRIDGE_BYPASS_HOOK_TRUST")):
        cmd.append("--dangerously-bypass-hook-trust")
    cmd.append("app-server")
    if cwd:
        trusted_cwd = str(Path(cwd).resolve(strict=False))
        cmd.extend(["-c", f"projects.{_toml_quoted_key(trusted_cwd)}.trust_level=\"trusted\""])
    if _truthy_env(os.environ.get("CODEX_BRIDGE_ENABLE_HOOKS")):
        cmd.extend(["--enable", "hooks", "--enable", "plugin_hooks", "--enable", "plugins"])
    if _multi_agent_enabled():
        # process-level feature gate so the per-turn multiAgentMode selection is
        # honored (subagent spawning + the items the bridge surfaces as lanes).
        cmd.extend(["-c", "features.multi_agent_mode=true"])
    cmd.extend(["--listen", "stdio://"])
    return cmd


def _truthy_env(value: "str | None") -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "enable", "enabled"}


def _resolve_repo_relative_path(raw: "str | None") -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    path = Path(os.path.expandvars(value)).expanduser()
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return str(path.resolve(strict=False))


def _configured_codex_pack_home() -> str:
    return _resolve_repo_relative_path(
        os.environ.get("CODEX_BRIDGE_HOME") or os.environ.get("CODEX_BRIDGE_PACK_HOME")
    )


def _configured_runtime_codex_home() -> str:
    return _resolve_repo_relative_path(
        os.environ.get("CODEX_BRIDGE_RUNTIME_HOME") or os.environ.get("CODEX_HOME")
    )


def _runtime_codex_home_for_files() -> str:
    return _configured_runtime_codex_home() or os.path.expanduser("~/.codex")


def _configured_oag_root() -> str:
    return _resolve_repo_relative_path(
        os.environ.get("CODEX_BRIDGE_OAG_ROOT") or os.environ.get("OAG_ROOT")
    )


def _app_server_env(cwd: "str | None" = None) -> dict[str, str]:
    env = dict(os.environ)
    runtime_home = _configured_runtime_codex_home()
    if runtime_home:
        env["CODEX_HOME"] = runtime_home
    pack_home = _configured_codex_pack_home()
    if pack_home:
        mcp_config = os.path.join(pack_home, "mcp.json")
        if os.path.isfile(mcp_config):
            env["MCP_CONFIG_PATH"] = mcp_config
    oag_root = _configured_oag_root()
    if oag_root:
        env["OAG_ROOT"] = oag_root
    if cwd:
        env.setdefault("OAG_IP_DIR", cwd)
    # Codex app-server is the engine here. Keep ATLAS's native OAG path out of
    # the subprocess by default, even if a parent shell still has OAG_MODE=1.
    env["OAG_MODE"] = (os.environ.get("CODEX_BRIDGE_OAG_MODE", "0").strip() or "0")
    env.setdefault("OAG_ACTOR_SURFACE", "codex-appserver")
    return env


def _stage_dot_codex(cwd: "str | None") -> None:
    """Expose the configured Codex pack at `<thread cwd>/.codex`.

    The ontology-ip-agent hook commands are intentionally project-relative
    (`python3 .codex/hooks/...`). A plain CODEX_HOME override is not enough when
    the thread runs inside an IP workspace, so stage the runtime subset without
    replacing an existing user/project `.codex`.
    """
    if not _truthy_env(os.environ.get("CODEX_BRIDGE_STAGE_DOT_CODEX")):
        return
    if not cwd:
        return
    codex_home = _configured_codex_pack_home()
    if not codex_home:
        return
    source = Path(codex_home)
    if not ((source / "hooks.json").is_file() or (source / "skills").is_dir()):
        return
    target_dir = Path(cwd)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / ".codex"
        marker = target / _STAGED_DOT_CODEX_MARKER
        if target.exists() and not (
            target.is_dir() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == str(source)
        ):
            return
        target.mkdir(parents=True, exist_ok=True)
        for entry in _RUNTIME_DOT_CODEX_ENTRIES:
            src = source / entry
            dst = target / entry
            if src.is_dir():
                shutil.copytree(
                    src,
                    dst,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
            elif src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        script_alias = target_dir / "scripts"
        if not script_alias.exists() and not script_alias.is_symlink() and (target / "scripts").is_dir():
            script_alias.symlink_to(Path(".codex") / "scripts", target_is_directory=True)
        marker.write_text(str(source), encoding="utf-8")
    except (OSError, RuntimeError):
        return


def _ensure_thread_cwd_trusted(cwd: "str | None") -> None:
    if not _truthy_env(os.environ.get("CODEX_BRIDGE_TRUST_THREAD_CWD", "1")):
        return
    if not cwd:
        return
    config_path = Path(_runtime_codex_home_for_files()) / "config.toml"
    trusted_cwd = str(Path(cwd).resolve(strict=False))
    header = f"[projects.{_toml_quoted_key(trusted_cwd)}]"
    try:
        text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
        if header in text:
            return
        config_path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if not text or text.endswith("\n") else "\n"
        with config_path.open("a", encoding="utf-8") as f:
            f.write(f"{prefix}\n{header}\ntrust_level = \"trusted\"\n")
    except OSError:
        return


def _extract_hook_additional_context(raw: str) -> str:
    blocks: "list[str]" = []
    for line in str(raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        hook_out = payload.get("hookSpecificOutput")
        if not isinstance(hook_out, dict):
            continue
        text = hook_out.get("additionalContext")
        if isinstance(text, str) and text.strip():
            blocks.append(text.strip())
    return "\n\n".join(blocks)


async def _run_oag_prompt_hook(cwd: str, hook_script: str, payload: dict[str, Any]) -> str:
    script = Path(cwd) / ".codex" / "hooks" / hook_script
    if not script.is_file():
        return ""
    env = _app_server_env(cwd)
    env.setdefault("OAG_IP_DIR", cwd)
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3",
            str(script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        out, _err = await asyncio.wait_for(
            proc.communicate(json.dumps(payload, ensure_ascii=False).encode()),
            timeout=_HOOK_TIMEOUT,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return _extract_hook_additional_context(out.decode("utf-8", errors="replace"))


async def _oag_user_prompt_context(cwd: "str | None", text: str) -> str:
    if not _truthy_env(os.environ.get("CODEX_BRIDGE_RUN_OAG_HOOKS")):
        return ""
    if not cwd:
        return ""
    payload = {
        "hook_event_name": "UserPromptSubmit",
        "hookEventName": "UserPromptSubmit",
        "prompt": text,
        "ip_dir": cwd,
        "stage": os.environ.get("OAG_STAGE") or "",
        "intent": str(text or "")[:240] or "atlas codex bridge prompt",
    }
    blocks = []
    for script in ("codex_context_inject.py", "codex_draft_pressure.py"):
        block = await _run_oag_prompt_hook(cwd, script, payload)
        if block:
            blocks.append(block)
    return "\n\n".join(blocks)


def _item_started_text(item: dict) -> "str | None":
    """Label when a tool-ish ThreadItem starts. None only for message/reasoning
    items (rendered separately via deltas). Known types get a nice label; ANY
    other type still shows generically so no codex activity is silently dropped."""
    itype = item.get("type")
    if itype in _NON_TOOL_ITEMS:
        return None
    if itype == "commandExecution":
        cmd = (item.get("command") or "").strip()
        cwd = item.get("cwd") or ""
        base = f"$ {cmd}" if cmd else "$ (command)"
        return f"{base}   ·cwd {cwd}" if cwd else base  # surface where codex runs it
    if itype == "webSearch":
        action = item.get("action") or {}
        atype = action.get("type")
        if atype == "openPage":
            return f"🌐 open: {action.get('url') or ''}"
        if atype == "findInPage":
            return f"🔎 find '{action.get('pattern') or ''}' in {action.get('url') or ''}"
        return f"🔎 web search: {item.get('query') or action.get('query') or ''}"
    if itype == "fileChange":
        parts = []
        for c in (item.get("changes") or []):
            kind = c.get("kind")
            kname = kind.get("type") if isinstance(kind, dict) else (str(kind) if kind else "")
            mark = {"add": "＋add", "delete": "－del", "update": "~mod"}.get(
                (kname or "").lower(), "✎"
            )
            parts.append(f"{mark} {c.get('path') or ''}".strip())
        return "✎ apply_patch: " + ", ".join(parts) if parts else "✎ edit"
    if itype == "mcpToolCall":
        server = item.get("server") or ""
        tool = item.get("tool") or "tool"
        return f"{server}.{tool}" if server else str(tool)
    if itype == "dynamicToolCall":
        return str(item.get("tool") or "tool")
    if itype == "imageView":
        return f"🖼 {item.get('path') or ''}"
    # generic: any other codex activity item still shows up
    return f"⚙ {itype or 'activity'}"


def _item_result(item: dict) -> "tuple[str, str] | None":
    """(tool_label, result_text) for a completed tool-ish ThreadItem. Known
    types are formatted (command output, file diffs, ...); unknown types dump
    their fields so nothing is invisible."""
    itype = item.get("type")
    if itype in _NON_TOOL_ITEMS:
        return None
    if itype == "commandExecution":
        out = item.get("aggregatedOutput")
        if not out:
            ec = item.get("exitCode")
            out = f"(exit {ec})" if ec is not None else f"({item.get('status') or 'no output'})"
        return ("command", str(out))
    if itype == "fileChange":
        blocks = []
        for c in (item.get("changes") or []):
            kind = c.get("kind")
            kname = kind.get("type") if isinstance(kind, dict) else (str(kind) if kind else "")
            path = c.get("path") or ""
            diff = c.get("diff") or ""
            # ADD shows new content; UPDATE shows codex's unified +/- diff.
            header = f"{(kname or 'edit').upper()}: {path}".rstrip()
            blocks.append(f"{header}\n{diff}".rstrip())
        return ("apply_patch", "\n\n".join(blocks) or f"status: {item.get('status')}")
    if itype == "mcpToolCall":
        tool = str(item.get("tool") or "mcp")
        if item.get("error"):
            return (tool, "error: " + json.dumps(item.get("error")))
        res = item.get("result")
        return (tool, json.dumps(res) if res is not None else "(ok)")
    if itype == "dynamicToolCall":
        ci = item.get("contentItems")
        return (
            str(item.get("tool") or "tool"),
            json.dumps(ci) if ci is not None else f"success={item.get('success')}",
        )
    if itype in ("webSearch", "imageView"):
        return None  # the started label already showed it
    # generic: dump remaining fields so any new/unknown item type stays visible
    extra = {k: v for k, v in item.items() if k not in ("id", "type")}
    try:
        body = json.dumps(extra, ensure_ascii=False)
    except Exception:
        body = str(extra)
    return (str(itype or "activity"), body if extra else "(done)")


def _tool_only_fallback_text(tool_results: "list[tuple[str, str]]") -> str:
    """Make a visible assistant message when a turn produced only tool output.

    Codex can legally finish a turn after a native tool call without emitting an
    `agentMessage` delta. ATLAS chat only persists/renders assistant text, so a
    tool-only turn would otherwise look blank even though useful evidence
    arrived. Keep the fallback small and literal: this is a visibility bridge,
    not a second summarizer.
    """
    cleaned: "list[tuple[str, str]]" = []
    for label, body in tool_results:
        text = str(body or "").strip()
        if not text:
            continue
        cleaned.append((str(label or "tool"), text[:_TOOL_ONLY_FALLBACK_LIMIT]))
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        label, body = cleaned[0]
        return f"Tool result ({label}):\n\n{body}"
    parts = ["Tool results:"]
    for label, body in cleaned:
        parts.append(f"\n[{label}]\n{body}")
    return "\n".join(parts)


def _thread_store_path() -> str:
    home = _runtime_codex_home_for_files()
    return os.path.join(home, "atlas_bridge_threads.json")


def _load_threads() -> dict:
    try:
        with open(_thread_store_path()) as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _save_thread(session_id: str, thread_id: str) -> None:
    """Persist atlas session_id -> codex thread_id so a respawned codex (or a
    restarted backend) resumes the SAME conversation instead of forgetting."""
    if not session_id or not thread_id:
        return
    try:
        data = _load_threads()
        if data.get(session_id) == thread_id:
            return
        data[session_id] = thread_id
        path = _thread_store_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except Exception:
        pass


class _CodexConn:
    """A persistent `codex app-server` stdio connection + one thread."""

    def __init__(self, cwd: "str | None" = None,
                 resume_thread_id: "str | None" = None) -> None:
        self.proc: "asyncio.subprocess.Process | None" = None
        self.thread_id: "str | None" = None
        self.cwd = cwd
        self._resume_thread_id = resume_thread_id
        self._next_id = 0
        self._pending: "dict[str, asyncio.Future]" = {}
        self._turn_lock = asyncio.Lock()
        self._on_note: "Callable[[str, dict], None] | None" = None
        self._broken = False
        # subagent (multi-agent) turn state: the main turn id (to avoid a nested
        # subagent turn ending the parent turn early) and sticky lane labels.
        self._main_turn_id: "str | None" = None
        self._sub_labels: "dict[str, str]" = {}

    async def start(self) -> None:
        _stage_dot_codex(self.cwd)
        _ensure_thread_cwd_trusted(self.cwd)
        proc_cwd = self.cwd if self.cwd else None
        self.proc = await asyncio.create_subprocess_exec(
            *_app_server_cmd(self.cwd),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=_STREAM_LIMIT,
            env=_app_server_env(self.cwd),
            cwd=proc_cwd,
        )
        asyncio.create_task(self._read_loop())
        asyncio.create_task(self._drain_stderr())

        await self._call("initialize", {
            "clientInfo": {"name": "atlas-codex-bridge", "version": "0.1.0"},
            "capabilities": {"experimentalApi": True},
        })
        self._notify("initialized")

        # Resume the prior conversation for this session if we have its thread
        # id (codex loads the rollout from disk); fall back to a fresh thread.
        if self._resume_thread_id:
            try:
                res = await self._call("thread/resume",
                                       {"threadId": self._resume_thread_id})
                self.thread_id = (
                    (res.get("thread") or {}).get("id") or self._resume_thread_id
                )
                return
            except Exception:
                pass  # rollout missing/stale -> start fresh below

        params: "dict[str, Any]" = {}
        if CODEX_MODEL:
            params["model"] = CODEX_MODEL
        if self.cwd:
            params["cwd"] = self.cwd  # scope codex to the active IP's workspace dir
        res = await self._call("thread/start", params)
        self.thread_id = (
            (res.get("thread") or {}).get("id") or res.get("threadId") or res.get("id")
        )

    def alive(self) -> bool:
        return (
            self.proc is not None
            and self.proc.returncode is None
            and not self._broken
        )

    def _fail_pending(self, exc: BaseException) -> None:
        """Mark the connection broken and unblock every in-flight `_call`."""
        self._broken = True
        for fut in list(self._pending.values()):
            if not fut.done():
                fut.set_exception(exc)
        self._pending.clear()

    # ---- transport ----
    def _send(self, obj: dict) -> None:
        assert self.proc and self.proc.stdin
        self.proc.stdin.write((json.dumps(obj) + "\n").encode())

    def _notify(self, method: str, params: "dict | None" = None) -> None:
        self._send({"method": method, **({"params": params} if params else {})})

    async def _call(self, method: str, params: "dict | None" = None,
                    timeout: float = _CALL_TIMEOUT) -> dict:
        self._next_id += 1
        rid = str(self._next_id)
        fut = asyncio.get_running_loop().create_future()
        self._pending[rid] = fut
        self._send({"id": rid, "method": method,
                    **({"params": params} if params is not None else {})})
        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            self._pending.pop(rid, None)
            raise RuntimeError(f"codex app-server '{method}' timed out after {timeout}s")

    async def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        try:
            while True:
                try:
                    line = await self.proc.stdout.readline()
                except (ValueError, asyncio.LimitOverrunError,
                        asyncio.IncompleteReadError) as exc:
                    # An oversized line blew the stream buffer; the reader is
                    # now desynced. Mark broken so the next turn respawns
                    # instead of hanging on never-resolved futures.
                    self._fail_pending(RuntimeError(f"codex stream overflow: {exc}"))
                    return
                if not line:
                    break
                try:
                    msg = json.loads(line)
                except Exception:
                    continue
                if "id" in msg and ("result" in msg or "error" in msg):
                    fut = self._pending.pop(str(msg["id"]), None)
                    if fut and not fut.done():
                        if "error" in msg:
                            fut.set_exception(RuntimeError(json.dumps(msg["error"])))
                        else:
                            fut.set_result(msg.get("result") or {})
                    continue
                method = msg.get("method")
                if method and self._on_note:
                    try:
                        self._on_note(method, msg.get("params") or {})
                    except Exception:
                        pass
        finally:
            # EOF or error: unblock any in-flight calls so the turn errors out
            # cleanly rather than hanging.
            self._fail_pending(RuntimeError("codex app-server connection closed"))

    async def _drain_stderr(self) -> None:
        assert self.proc and self.proc.stderr
        while True:
            line = await self.proc.stderr.readline()
            if not line:
                break  # keep the pipe from filling; logs are dropped quietly

    # ---- one chat turn ----
    async def run_turn(self, text: str, emit: "Callable[..., None]") -> None:
        async with self._turn_lock:
            done = asyncio.Event()
            saw_agent_text = False
            saw_error = False
            tool_results: "list[tuple[str, str]]" = []

            def _sub_label(tid: str) -> str:
                return self._sub_labels.get(tid) or (_short_tid(tid) if tid else "subagent")

            def _emit_sub(ev: dict) -> None:
                # learn + stick the human label for a lane; back-fill it when a
                # later event (e.g. a delta) arrives carrying no label of its own.
                _tid = str(ev.get("agent_id") or "")
                _lbl = str(ev.get("label") or "")
                if _tid and _lbl:
                    self._sub_labels[_tid] = _lbl
                elif _tid and not _lbl:
                    ev["label"] = _sub_label(_tid)
                ev.setdefault("parent_id", self.thread_id or "")
                emit("subagent", **ev)

            def on_note(method: str, params: dict) -> None:
                nonlocal saw_agent_text, saw_error
                tid = str(params.get("threadId") or "")
                is_sub = bool(tid) and bool(self.thread_id) and tid != self.thread_id

                if method == "thread/started":
                    # A subagent thread announces itself with a parentThreadId +
                    # human nickname/role; capture the nice label (e.g.
                    # "RTL Implementation [oag-rtl-implementation-agent]") so the
                    # lane shows it instead of a raw thread id.
                    th = params.get("thread") or {}
                    th_id = str(th.get("id") or "")
                    if th_id and th.get("parentThreadId"):
                        nick = str(th.get("agentNickname") or "")
                        role = str(th.get("agentRole") or "")
                        label = (f"{nick} [{role}]" if nick and role
                                 else (nick or role or _short_tid(th_id)))
                        _emit_sub({"agent_id": th_id, "label": label,
                                   "status": "spawning", "kind": "status",
                                   "text": "spawned"})
                    return

                if method in ("item/started", "item/completed"):
                    item = params.get("item") or {}
                    if item.get("type") in _SUBAGENT_ITEMS:
                        for ev in _subagent_lane_events(
                                item, method == "item/started", self.thread_id or ""):
                            _emit_sub(ev)
                        return
                    if is_sub:
                        # the subagent's OWN tool activity -> its lane transcript
                        if method == "item/started":
                            lbl = _item_started_text(item)
                            if lbl is not None:
                                _emit_sub({"agent_id": tid, "status": "running",
                                           "kind": "tool", "text": lbl})
                        else:
                            res = _item_result(item)
                            if res is not None:
                                _tl, _body = res
                                _emit_sub({"agent_id": tid, "status": "running",
                                           "kind": "tool_result",
                                           "text": str(_body)[:_SUBAGENT_TEXT_LIMIT]})
                        return
                    # main-thread tool activity -> existing main chat feed
                    if method == "item/started":
                        label = _item_started_text(item)
                        if label is not None:
                            emit("tool", text=label)
                    else:
                        res = _item_result(item)
                        if res is not None:
                            tool_label, result_text = res
                            result_body = str(result_text)[:_TOOL_ONLY_FALLBACK_LIMIT]
                            if result_body.strip():
                                tool_results.append((str(tool_label), result_body))
                            emit("tool_result", text=result_body, tool=tool_label)
                    return

                if method == "item/agentMessage/delta":
                    delta = str(params.get("delta", ""))
                    if is_sub:
                        _emit_sub({"agent_id": tid, "status": "running",
                                   "kind": "message",
                                   "text": delta[:_SUBAGENT_TEXT_LIMIT]})
                        return
                    if delta.strip():
                        saw_agent_text = True
                    emit("token", text=delta)
                    return

                if method in ("item/reasoning/textDelta",
                              "item/reasoning/summaryTextDelta"):
                    delta = str(params.get("delta", ""))
                    if is_sub:
                        _emit_sub({"agent_id": tid, "status": "running",
                                   "kind": "reasoning",
                                   "text": delta[:_SUBAGENT_TEXT_LIMIT]})
                        return
                    emit("reasoning", text=delta)
                    return

                if method == "turn/completed":
                    # Only the MAIN turn ends the bridge turn. A subagent runs
                    # nested inside the main turn, so its turn/completed must not
                    # flush the parent early -- just close that lane.
                    turn_id = str(params.get("turnId")
                                  or (params.get("turn") or {}).get("id") or "")
                    is_main = (
                        (self._main_turn_id and turn_id == self._main_turn_id)
                        or (not self._main_turn_id and not is_sub)
                    )
                    if is_main:
                        done.set()
                    elif tid:
                        _emit_sub({"agent_id": tid, "status": "completed",
                                   "kind": "status", "text": "turn completed"})
                    return

                if method == "error":
                    if is_sub and tid:
                        _emit_sub({"agent_id": tid, "status": "failed",
                                   "kind": "status",
                                   "text": json.dumps(params.get("error"))})
                        return
                    saw_error = True
                    emit("error", message=json.dumps(params.get("error")))
                    done.set()

            self._on_note = on_note
            try:
                emit("agent_state", running=True)
                params: "dict[str, Any]" = {
                    "threadId": self.thread_id,
                    "input": [{"type": "text", "text": text}],
                }
                if _multi_agent_enabled():
                    # opt codex into multi-agent mode so an explicit `/subagent`
                    # spawns a sub-thread we surface as a left-rail lane.
                    params["multiAgentMode"] = _MULTI_AGENT_MODE
                hook_context = await _oag_user_prompt_context(self.cwd, text)
                if hook_context:
                    params["additionalContext"] = {
                        "oag": {"kind": "application", "value": hook_context}
                    }
                self._main_turn_id = None
                try:
                    res = await self._call("turn/start", params)
                except RuntimeError:
                    # Older codex builds may reject the experimental
                    # multiAgentMode param; retry once without it so the turn
                    # still runs (lanes just won't populate).
                    if "multiAgentMode" in params:
                        params.pop("multiAgentMode", None)
                        res = await self._call("turn/start", params)
                    else:
                        raise
                self._main_turn_id = str(
                    (res.get("turn") or {}).get("id")
                    or res.get("turnId") or res.get("id") or "")
                try:
                    await asyncio.wait_for(done.wait(), timeout=_TURN_TIMEOUT)
                except asyncio.TimeoutError:
                    saw_error = True
                    emit("error", message=f"codex turn timed out after {_TURN_TIMEOUT:.0f}s")
            finally:
                self._on_note = None
                if not saw_agent_text and not saw_error:
                    fallback = _tool_only_fallback_text(tool_results)
                    if fallback:
                        emit("token", text=fallback)
                emit("flush")
                emit("agent_state", running=False)
                emit("done")


async def _get_conn(session_id: str, cwd: "str | None" = None) -> _CodexConn:
    async with _conns_lock:
        conn = _conns.get(session_id)
        if conn is not None and conn.alive():
            return conn
        resume_id = _load_threads().get(session_id)  # prior thread for this session
        conn = _CodexConn(cwd, resume_thread_id=resume_id)
        _conns[session_id] = conn  # reserve; start() (handshake) runs OUTSIDE
        # the global lock so a slow/stuck session can't block every other one.
    try:
        await conn.start()
    except Exception:
        async with _conns_lock:
            if _conns.get(session_id) is conn:
                del _conns[session_id]
        raise
    if conn.thread_id:
        _save_thread(session_id, conn.thread_id)  # remember for resume after a respawn
    return conn


def _append_conversation(path: str, user_text: str, assistant_text: str) -> None:
    """Append one (user, assistant) turn to a session conversation.json — the same
    ``[{role, content}, ...]`` file the atlas frontend hydrates via
    /api/conversation. The codex bridge bypasses atlas's own history writer, so
    without this the codex replies vanish on the next turn / re-render. Best-effort
    and atomic; never raises into the turn."""
    try:
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        rows: list = []
        if p.is_file():
            try:
                loaded = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    rows = loaded
            except Exception:
                rows = []
        if user_text and str(user_text).strip():
            rows.append({"role": "user", "content": str(user_text)})
        if assistant_text and str(assistant_text).strip():
            rows.append({"role": "assistant", "content": str(assistant_text)})
        if len(rows) > 500:  # keep the file bounded
            rows = rows[-500:]
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)
    except Exception:
        pass


async def run_codex_turn(
    session: Any, text: str, cwd: "str | None" = None, conn_key: "str | None" = None,
    transcript_path: "str | None" = None,
) -> None:
    """Run one chat turn through codex app-server for the given atlas session,
    emitting the existing atlas envelope events via session.emit(...). `cwd`
    scopes the session's codex thread to the active IP's workspace directory.

    `conn_key` selects the persistent codex connection. It must be the RESOLVED
    per-IP namespace (e.g. ``user/session/ip/workflow``): the websocket
    ``session.session_id`` can be a coarse connection-level ``'default'``, so
    keying on it would force every IP under one shared codex process + cwd
    (the first IP's cwd would stick for all later IPs). Falls back to the
    session id when no key is supplied.

    `transcript_path` is the session conversation.json: the user prompt and the
    accumulated agent reply are appended there so the chat feed persists."""
    _agent_buf: "list[str]" = []
    def emit(msg_type: str, **payload: Any) -> None:
        if msg_type == "token":
            _agent_buf.append(str(payload.get("text") or ""))
        try:
            session.emit(msg_type, **payload)
        except Exception:
            pass
    try:
        _key = conn_key or getattr(session, "session_id", "") or "default"
        conn = await _get_conn(_key, cwd)
        await conn.run_turn(text, emit)
    except Exception as exc:  # never strand the frontend
        emit("error", message=f"codex bridge error: {exc}")
        emit("flush")
        emit("agent_state", running=False)
        emit("done")
    finally:
        if transcript_path:
            _append_conversation(transcript_path, text, "".join(_agent_buf))
