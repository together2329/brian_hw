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
  CODEX_BRIDGE_HOME  CODEX_HOME to use (default: inherit env / ~/.codex)
  CODEX_BRIDGE_MODEL optional model override for the thread
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Callable

CODEX_BIN = os.environ.get("CODEX_BRIDGE_BIN", "codex")
CODEX_HOME = os.environ.get("CODEX_BRIDGE_HOME") or os.environ.get("CODEX_HOME")
CODEX_MODEL = os.environ.get("CODEX_BRIDGE_MODEL")

# A single JSON-RPC notification line can be large (e.g. a command's full
# aggregatedOutput). asyncio's StreamReader defaults to a 64KB line limit and
# RAISES on overflow, which would otherwise crash the read loop and hang the
# turn forever. Give it a generous buffer.
_STREAM_LIMIT = int(os.environ.get("CODEX_BRIDGE_STREAM_LIMIT", str(64 * 1024 * 1024)))
# Control-RPC timeout (initialize / thread.start / turn.start ack).
_CALL_TIMEOUT = float(os.environ.get("CODEX_BRIDGE_CALL_TIMEOUT", "60"))
# Whole-turn timeout: never leave the frontend stuck on "running" forever.
_TURN_TIMEOUT = float(os.environ.get("CODEX_BRIDGE_TURN_TIMEOUT", "180"))

_conns: "dict[str, _CodexConn]" = {}
_conns_lock = asyncio.Lock()

# item.type values that are NOT surfaced as tool activity
_NON_TOOL_ITEMS = {"userMessage", "agentMessage", "reasoning"}


def _item_started_text(item: dict) -> "str | None":
    """Label when a tool-ish ThreadItem starts. None only for message/reasoning
    items (rendered separately via deltas). Known types get a nice label; ANY
    other type still shows generically so no codex activity is silently dropped."""
    itype = item.get("type")
    if itype in _NON_TOOL_ITEMS:
        return None
    if itype == "commandExecution":
        cmd = (item.get("command") or "").strip()
        return f"$ {cmd}" if cmd else "$ (command)"
    if itype == "webSearch":
        action = item.get("action") or {}
        atype = action.get("type")
        if atype == "openPage":
            return f"🌐 open: {action.get('url') or ''}"
        if atype == "findInPage":
            return f"🔎 find '{action.get('pattern') or ''}' in {action.get('url') or ''}"
        return f"🔎 web search: {item.get('query') or action.get('query') or ''}"
    if itype == "fileChange":
        paths = ", ".join((c.get("path") or "") for c in (item.get("changes") or []))
        return f"✎ edit: {paths}" if paths else "✎ edit"
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
        diffs = "\n".join(
            f"{c.get('path') or ''}\n{c.get('diff') or ''}"
            for c in (item.get("changes") or [])
        )
        return ("apply_patch", diffs or f"status: {item.get('status')}")
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


def _thread_store_path() -> str:
    home = CODEX_HOME or os.path.expanduser("~/.codex")
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

    async def start(self) -> None:
        env = dict(os.environ)
        if CODEX_HOME:
            env["CODEX_HOME"] = CODEX_HOME
        self.proc = await asyncio.create_subprocess_exec(
            CODEX_BIN, "app-server", "--listen", "stdio://",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=_STREAM_LIMIT,
            env=env,
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

            def on_note(method: str, params: dict) -> None:
                if method == "item/agentMessage/delta":
                    emit("token", text=params.get("delta", ""))
                elif method in ("item/reasoning/textDelta",
                                "item/reasoning/summaryTextDelta"):
                    emit("reasoning", text=params.get("delta", ""))
                elif method == "item/started":
                    label = _item_started_text(params.get("item") or {})
                    if label is not None:
                        emit("tool", text=label)
                elif method == "item/completed":
                    res = _item_result(params.get("item") or {})
                    if res is not None:
                        tool_label, result_text = res
                        emit("tool_result", text=str(result_text)[:4000], tool=tool_label)
                elif method == "turn/completed":
                    done.set()
                elif method == "error":
                    emit("error", message=json.dumps(params.get("error")))
                    done.set()

            self._on_note = on_note
            try:
                emit("agent_state", running=True)
                await self._call("turn/start", {
                    "threadId": self.thread_id,
                    "input": [{"type": "text", "text": text}],
                })
                try:
                    await asyncio.wait_for(done.wait(), timeout=_TURN_TIMEOUT)
                except asyncio.TimeoutError:
                    emit("error", message=f"codex turn timed out after {_TURN_TIMEOUT:.0f}s")
            finally:
                self._on_note = None
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


async def run_codex_turn(session: Any, text: str, cwd: "str | None" = None) -> None:
    """Run one chat turn through codex app-server for the given atlas session,
    emitting the existing atlas envelope events via session.emit(...). `cwd`
    scopes the session's codex thread to the active IP's workspace directory."""
    def emit(msg_type: str, **payload: Any) -> None:
        try:
            session.emit(msg_type, **payload)
        except Exception:
            pass
    try:
        conn = await _get_conn(session.session_id, cwd)
        await conn.run_turn(text, emit)
    except Exception as exc:  # never strand the frontend
        emit("error", message=f"codex bridge error: {exc}")
        emit("flush")
        emit("agent_state", running=False)
        emit("done")
