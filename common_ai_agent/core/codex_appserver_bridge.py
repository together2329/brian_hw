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

_conns: "dict[str, _CodexConn]" = {}
_conns_lock = asyncio.Lock()

# item.type values that are NOT surfaced as tool activity
_NON_TOOL_ITEMS = {"userMessage", "agentMessage", "reasoning"}


class _CodexConn:
    """A persistent `codex app-server` stdio connection + one thread."""

    def __init__(self) -> None:
        self.proc: "asyncio.subprocess.Process | None" = None
        self.thread_id: "str | None" = None
        self._next_id = 0
        self._pending: "dict[str, asyncio.Future]" = {}
        self._turn_lock = asyncio.Lock()
        self._on_note: "Callable[[str, dict], None] | None" = None

    async def start(self) -> None:
        env = dict(os.environ)
        if CODEX_HOME:
            env["CODEX_HOME"] = CODEX_HOME
        self.proc = await asyncio.create_subprocess_exec(
            CODEX_BIN, "app-server", "--listen", "stdio://",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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
        res = await self._call("thread/start", params)
        self.thread_id = (
            (res.get("thread") or {}).get("id") or res.get("threadId") or res.get("id")
        )

    def alive(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    # ---- transport ----
    def _send(self, obj: dict) -> None:
        assert self.proc and self.proc.stdin
        self.proc.stdin.write((json.dumps(obj) + "\n").encode())

    def _notify(self, method: str, params: "dict | None" = None) -> None:
        self._send({"method": method, **({"params": params} if params else {})})

    async def _call(self, method: str, params: "dict | None" = None) -> dict:
        self._next_id += 1
        rid = str(self._next_id)
        fut = asyncio.get_running_loop().create_future()
        self._pending[rid] = fut
        self._send({"id": rid, "method": method,
                    **({"params": params} if params is not None else {})})
        return await fut

    async def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        while True:
            line = await self.proc.stdout.readline()
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
                    item = params.get("item") or {}
                    if item.get("type") not in _NON_TOOL_ITEMS:
                        emit("tool", text=str(item.get("type") or "tool"))
                elif method == "item/completed":
                    item = params.get("item") or {}
                    itype = item.get("type")
                    if itype not in _NON_TOOL_ITEMS:
                        summary = item.get("text") or itype or ""
                        emit("tool_result", text=str(summary)[:1200],
                             tool=str(itype or "tool"))
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
                await done.wait()
            finally:
                self._on_note = None
                emit("flush")
                emit("agent_state", running=False)
                emit("done")


async def _get_conn(session_id: str) -> _CodexConn:
    async with _conns_lock:
        conn = _conns.get(session_id)
        if conn is None or not conn.alive():
            conn = _CodexConn()
            await conn.start()
            _conns[session_id] = conn
        return conn


async def run_codex_turn(session: Any, text: str) -> None:
    """Run one chat turn through codex app-server for the given atlas session,
    emitting the existing atlas envelope events via session.emit(...)."""
    def emit(msg_type: str, **payload: Any) -> None:
        try:
            session.emit(msg_type, **payload)
        except Exception:
            pass
    try:
        conn = await _get_conn(session.session_id)
        await conn.run_turn(text, emit)
    except Exception as exc:  # never strand the frontend
        emit("error", message=f"codex bridge error: {exc}")
        emit("flush")
        emit("agent_state", running=False)
        emit("done")
