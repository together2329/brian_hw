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
    """Human-readable label when a tool-ish ThreadItem starts; None to skip.
    Reads the real per-type fields — codex command/exec items carry the command
    in `command` (NOT `text`), so a plain item.text read renders empty."""
    itype = item.get("type")
    if itype == "commandExecution":
        cmd = (item.get("command") or "").strip()
        return f"$ {cmd}" if cmd else "$ (command)"
    if itype == "mcpToolCall":
        server = item.get("server") or ""
        tool = item.get("tool") or "tool"
        return f"{server}.{tool}" if server else str(tool)
    if itype == "fileChange":
        n = len(item.get("changes") or [])
        return f"apply_patch — {n} file(s)"
    if itype == "dynamicToolCall":
        return str(item.get("tool") or "tool")
    if itype == "webSearch":
        action = item.get("action") or {}
        atype = action.get("type")
        if atype == "openPage":
            return f"🌐 open: {action.get('url') or ''}"
        if atype == "findInPage":
            return f"🔎 find '{action.get('pattern') or ''}' in {action.get('url') or ''}"
        q = item.get("query") or action.get("query") or ""
        return f"🔎 web search: {q}"
    if itype == "imageView":
        return f"🖼 {item.get('path') or ''}"
    return None


def _item_result(item: dict) -> "tuple[str, str] | None":
    """(tool_label, result_text) for a completed tool-ish ThreadItem; None to
    skip. Command output lives in `aggregatedOutput`, not `text`."""
    itype = item.get("type")
    if itype == "commandExecution":
        out = item.get("aggregatedOutput")
        if not out:
            ec = item.get("exitCode")
            out = f"(exit {ec})" if ec is not None else f"({item.get('status') or 'no output'})"
        return ("command", str(out))
    if itype == "mcpToolCall":
        tool = str(item.get("tool") or "mcp")
        if item.get("error"):
            return (tool, "error: " + json.dumps(item.get("error")))
        res = item.get("result")
        return (tool, json.dumps(res) if res is not None else "(ok)")
    if itype == "fileChange":
        return ("apply_patch", f"status: {item.get('status')}")
    if itype == "dynamicToolCall":
        ci = item.get("contentItems")
        return (
            str(item.get("tool") or "tool"),
            json.dumps(ci) if ci is not None else f"success={item.get('success')}",
        )
    return None


class _CodexConn:
    """A persistent `codex app-server` stdio connection + one thread."""

    def __init__(self, cwd: "str | None" = None) -> None:
        self.proc: "asyncio.subprocess.Process | None" = None
        self.thread_id: "str | None" = None
        self.cwd = cwd
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
        conn = _CodexConn(cwd)
        _conns[session_id] = conn  # reserve; start() (handshake) runs OUTSIDE
        # the global lock so a slow/stuck session can't block every other one.
    try:
        await conn.start()
    except Exception:
        async with _conns_lock:
            if _conns.get(session_id) is conn:
                del _conns[session_id]
        raise
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
