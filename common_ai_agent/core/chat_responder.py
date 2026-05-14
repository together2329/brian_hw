r"""ATLAS Helper — Orchestrator Chat auto-responder.

A standalone agent process, one per room, that watches the chat ledger
for new human posts and replies on the same room with a short natural
language answer grounded in the live IP / workspace context.

Launch
------
Per-IP responder::

    python3 -m core.chat_responder uart_lite

\_global responder::

    python3 -m core.chat_responder _global

Configuration comes from `.env`:

  CHAT_RESPONDER_MODEL           default model alias (default: gpt-5.3-codex)
  CHAT_RESPONDER_EFFORT          reasoning effort (default: low)
  CHAT_RESPONDER_POLL_SECONDS    poll interval (default: 2)
  CHAT_RESPONDER_MIN_INTERVAL_SECONDS  per-room cooldown (default: 3)
  CHAT_RESPONDER_MAX_OUTPUT_TOKENS     reply cap (default: 200)

Each room runs as its own session bridge `atlas-helper/<room>/chat-responder`
so the `chat_consumed` ledger isolates each responder's watermark.

The responder talks to AtlasDB directly + reuses `llm_client.completion`
for the model call — no ReAct loop, no todo tracker, no plan mode. This
keeps the loop cheap and predictable.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from core.atlas_db import AtlasDB


_LOG = logging.getLogger("chat_responder")

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

_DEFAULT_MODEL = "gpt-5.3-codex"
_DEFAULT_EFFORT = "low"
_DEFAULT_POLL_SECONDS = 2.0
_DEFAULT_MIN_INTERVAL_SECONDS = 3.0
_DEFAULT_MAX_OUTPUT_TOKENS = 200

_PROMPT_DIR = _REPO / "workflow" / "chat-responder"
_GLOBAL_ROOM = "_global"
_AGENT_USERNAME = "atlas-helper"
_AGENT_DISPLAY = "🤖 ATLAS Helper"


def _env(name: str, default: str) -> str:
    raw = os.environ.get(name, "").strip()
    return raw if raw else default


def _envf(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except (TypeError, ValueError):
        return default


def _envi(name: str, default: int) -> int:
    try:
        return int(float(_env(name, str(default))))
    except (TypeError, ValueError):
        return default


# ----------------------------------------------------------------------
# Agent service account
# ----------------------------------------------------------------------


def _ensure_agent_user(db: AtlasDB) -> dict:
    """Idempotently seed (or fetch) the `atlas-helper` service account.

    All chat replies are posted as this user. role='agent' lets the
    frontend visually distinguish bot replies from human messages
    while reusing the same permission / actor_user_id machinery."""
    existing = db.get_user_by_username(_AGENT_USERNAME)
    if existing is not None:
        return existing
    return db.create_user(
        username=_AGENT_USERNAME,
        display_name=_AGENT_DISPLAY,
        password_hash="",  # service account — never logs in via UI
        role="agent",
    )


# ----------------------------------------------------------------------
# Context bundle rendering (small, focused — the responder gets a
# stripped-down view; it does not need the full UI payload)
# ----------------------------------------------------------------------


def _render_ip_context(db: AtlasDB, ip_id: str) -> str:
    bundle = db.summarize_ip_room_context(ip_id)
    if not bundle:
        return ""
    ip = bundle.get("ip") or {}
    wf = (bundle.get("workflow") or {}).get("latest_run") or {}
    todos = bundle.get("todos") or {}
    recent = bundle.get("recent_events") or []
    lines = [f"<orchestrator-context room={ip.get('name')!r}>",
             f"ip: {ip.get('name')} ({ip.get('type') or '?'})"]
    if wf:
        lines.append(
            f"workflow: {wf.get('workflow')}/{wf.get('status')}"
            f" stage={wf.get('current_stage') or '?'}"
            f" model={wf.get('model_profile') or '?'}"
        )
    counts = todos.get("counts") or {}
    if counts:
        lines.append("todos: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    for b in (todos.get("top_blockers") or [])[:5]:
        lines.append(f"  blocker[{b.get('status')}] {b.get('title')}")
    for ev in recent[:6]:
        if ev.get("kind") == "llm":
            lines.append(
                f"  llm {ev.get('model')} in={ev.get('tokens_input')}"
                f" out={ev.get('tokens_output')} cost=${ev.get('cost_usd') or 0}"
            )
        else:
            lines.append(f"  trace {ev.get('event_type')}")
    lines.append("</orchestrator-context>")
    return "\n".join(lines)


def _render_global_context(db: AtlasDB) -> str:
    bundle = db.summarize_global_room_context()
    lines = ["<orchestrator-context room='_global'>"]
    for ip in (bundle.get("ips") or [])[:25]:
        lines.append(
            f"  {ip.get('name')}: {ip.get('latest_workflow') or '-'}"
            f"/{ip.get('run_status') or '-'} open={ip.get('open_blockers')}"
            f" done={ip.get('completed')}"
        )
    lines.append("</orchestrator-context>")
    return "\n".join(lines)


def _render_chat_block(messages: list[dict], room: str) -> str:
    lines = [f"<team-chat-feedback room={room!r}>"]
    for m in messages:
        payload = m.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        content = (payload.get("content") or "").strip()
        if not content:
            continue
        name = payload.get("display_name") or m.get("actor_user_id") or "user"
        lines.append(f"[{name}] {content}")
    lines.append("</team-chat-feedback>")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# LLM call (uses ATLAS's existing llm_client.completion / model alias)
# ----------------------------------------------------------------------


def _llm_completion(system_prompt: str,
                    user_block: str,
                    model: str,
                    max_tokens: int) -> str:
    """Single non-streaming completion. Returns the assistant text.

    Uses the same llm_client module the main agent uses so that the
    --model alias, auth, cost recording, and trace_events all share
    one path.

    chat_completion_stream emits a mixed stream — see llm_client docstring:
      - bare str               → assistant content chunk (what we want)
      - ('reasoning', text)    → thinking trace (drop — internal)
      - ('native_tool_calls',) → tool calls (drop — bot doesn't call tools)
      - ('finish_reason', ...) → end marker (drop)
    We collect only the bare strings."""
    # Late import — llm_client transitively imports config and provider modules.
    from llm_client import chat_completion_stream  # type: ignore
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_block},
    ]
    out_chunks: list[str] = []
    char_budget = max_tokens * 6   # tokens ≤ chars/4 worst case; budget for early stop
    for chunk in chat_completion_stream(messages, stop=None,
                                          suppress_spinner=True):
        if isinstance(chunk, str):
            out_chunks.append(chunk)
        # tuples are reasoning / tool_calls / finish_reason — never content
        if sum(len(c) for c in out_chunks) >= char_budget:
            break
    text = "".join(out_chunks).strip()
    return text[: max_tokens * 8]  # safety cap on raw chars


# ----------------------------------------------------------------------
# Responder loop
# ----------------------------------------------------------------------


class Responder:
    def __init__(self, room: str,
                 db: Optional[AtlasDB] = None,
                 bridge: Optional[object] = None,
                 model: Optional[str] = None,
                 poll_seconds: Optional[float] = None,
                 min_interval_seconds: Optional[float] = None,
                 max_output_tokens: Optional[int] = None):
        self.room = room
        self.db = db or AtlasDB()
        # bridge enables real-time WS push of bot replies. When the
        # responder runs in-process with atlas_ui (autostart), pass the
        # live _MultiUserBridge; standalone CLI runs leave it None and
        # WS clients receive the message on next refresh.
        self.bridge = bridge
        self.model = model or _env("CHAT_RESPONDER_MODEL", _DEFAULT_MODEL)
        # Explicit None checks instead of `or` so explicit 0 / 0.0 from
        # tests (and operators who want NO throttle) are honored. Using
        # `or` here treats 0 as falsy and silently falls back to the env
        # default, which masked a throttle in unit tests for hours.
        self.poll_seconds = (poll_seconds if poll_seconds is not None
                             else _envf("CHAT_RESPONDER_POLL_SECONDS",
                                          _DEFAULT_POLL_SECONDS))
        self.min_interval = (min_interval_seconds if min_interval_seconds is not None
                             else _envf("CHAT_RESPONDER_MIN_INTERVAL_SECONDS",
                                          _DEFAULT_MIN_INTERVAL_SECONDS))
        self.max_output_tokens = (max_output_tokens if max_output_tokens is not None
                                   else _envi("CHAT_RESPONDER_MAX_OUTPUT_TOKENS",
                                                _DEFAULT_MAX_OUTPUT_TOKENS))

        # Resolve room → ip_id (None for global) and prompt variant.
        if room == _GLOBAL_ROOM:
            self.ip_id: Optional[str] = None
            self.ip_name: Optional[str] = None
            self.system_prompt = (_PROMPT_DIR / "prompt-global.md").read_text(
                encoding="utf-8"
            )
        else:
            ip = self.db.get_ip_block_by_name(room)
            if ip is None:
                raise SystemExit(f"unknown IP room {room!r}")
            self.ip_id = ip["id"]
            self.ip_name = ip["ip_name"]
            tmpl = (_PROMPT_DIR / "prompt-ip.md").read_text(encoding="utf-8")
            self.system_prompt = tmpl.replace("{ip_name}", self.ip_name)

        # Service account
        self.agent = _ensure_agent_user(self.db)
        self.agent_uid = self.agent["id"]

        # Session id used for chat_consumed isolation.
        self.session_id = f"atlas-helper/{room}/chat-responder"

        # Throttle state
        self._last_reply_at = 0.0
        self._stop = False

    def stop(self, *_a) -> None:
        self._stop = True

    def _build_user_block(self, unread: list[dict]) -> str:
        if self.ip_id:
            ctx = _render_ip_context(self.db, self.ip_id)
        else:
            ctx = _render_global_context(self.db)
        chat = _render_chat_block(unread, self.room)
        return f"{ctx}\n\n{chat}"

    def _post_reply(self, reply: str) -> Optional[dict]:
        if not reply.strip():
            return None
        row = self.db.record_chat_message(
            ip_id=self.ip_id,
            user_id=self.agent_uid,
            content=reply.strip(),
            display_name=_AGENT_DISPLAY,
        )
        # Push to WS clients in real time. Without this, browser tabs
        # only see the bot reply on the next refresh. Best-effort —
        # bridge is None in standalone CLI mode and that path falls
        # back to client-side polling.
        if self.bridge is not None and hasattr(self.bridge, "broadcast_all"):
            try:
                payload = row.get("payload") or {}
                if isinstance(payload, str):
                    import json as _json
                    payload = _json.loads(payload) if payload else {}
                self.bridge.broadcast_all(
                    "chat_message",
                    room=self.room,
                    id=row["id"],
                    ip_id=row.get("ip_id") or None,
                    user_id=row.get("actor_user_id"),
                    display_name=payload.get("display_name") or _AGENT_DISPLAY,
                    content=payload.get("content") or reply.strip(),
                    created_at=row.get("created_at"),
                )
            except Exception:  # pragma: no cover — broadcast is best-effort
                pass
        return row

    def _mark_consumed(self, msgs: list[dict]) -> None:
        for m in msgs:
            try:
                self.db.record_chat_consumed(
                    chat_id=m["id"],
                    session_id=self.session_id,
                    ip_id=self.ip_id,
                )
            except Exception as exc:  # pragma: no cover
                _LOG.warning("chat_consumed failed: %s", exc)

    def tick(self) -> int:
        """One poll cycle. Returns number of chats consumed."""
        unread = self.db.list_chat_unconsumed_for(
            session_id=self.session_id,
            ip_id=self.ip_id,
            after_id=None,
        )
        # Filter out our own posts so the loop never replies to itself.
        unread = [m for m in unread
                  if (m.get("actor_user_id") or "") != self.agent_uid]
        if not unread:
            return 0

        now = time.time()
        if now - self._last_reply_at < self.min_interval:
            # Cooldown — leave the chats unconsumed so the next tick
            # picks them up after the throttle interval. This guarantees
            # we never silently drop human feedback.
            return 0

        user_block = self._build_user_block(unread)
        try:
            reply = _llm_completion(
                system_prompt=self.system_prompt,
                user_block=user_block,
                model=self.model,
                max_tokens=self.max_output_tokens,
            )
        except Exception as exc:
            _LOG.error("LLM call failed: %s", exc, exc_info=True)
            return 0

        posted = self._post_reply(reply) if reply else None
        # ALWAYS consume — even if the LLM returned empty — so the same
        # chat is not retried forever. The ledger records the consume
        # event regardless of whether a reply was emitted.
        self._mark_consumed(unread)
        if posted:
            self._last_reply_at = time.time()
            print(f"[chat-responder/{self.room}] replied to {len(unread)} "
                  f"chat(s): {reply[:80]!r}")
        else:
            print(f"[chat-responder/{self.room}] no reply (consumed "
                  f"{len(unread)} chat(s))")
        return len(unread)

    def run_forever(self) -> None:
        print(f"[chat-responder/{self.room}] starting · model={self.model}"
              f" · poll={self.poll_seconds}s · session={self.session_id}")
        while not self._stop:
            try:
                self.tick()
            except KeyboardInterrupt:
                break
            except Exception as exc:
                _LOG.error("tick failed: %s", exc, exc_info=True)
            time.sleep(self.poll_seconds)
        print(f"[chat-responder/{self.room}] stopped")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def _load_dotenv_if_present() -> None:
    """Tiny .env loader so the module works standalone (without main.py).
    Only reads simple KEY=VALUE lines, no shell substitution."""
    env_path = _REPO / ".env"
    if not env_path.is_file():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:  # pragma: no cover
        pass


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="ATLAS Helper chat responder")
    ap.add_argument("room", help="Room name: an IP name (e.g. uart_lite) or _global")
    ap.add_argument("--model", default=None, help="Override CHAT_RESPONDER_MODEL")
    ap.add_argument("--poll", type=float, default=None, help="Override poll seconds")
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="Override max output tokens")
    ap.add_argument("--once", action="store_true",
                    help="Run a single tick and exit (testing)")
    args = ap.parse_args(argv)

    _load_dotenv_if_present()
    logging.basicConfig(
        level=os.environ.get("CHAT_RESPONDER_LOG_LEVEL", "WARNING"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    r = Responder(
        room=args.room,
        model=args.model,
        poll_seconds=args.poll,
        max_output_tokens=args.max_tokens,
    )

    if args.once:
        n = r.tick()
        return 0 if n >= 0 else 1

    signal.signal(signal.SIGINT, r.stop)
    signal.signal(signal.SIGTERM, r.stop)
    r.run_forever()
    return 0


def autostart_all(
    db: Optional[AtlasDB] = None,
    bridge: Optional[object] = None,
) -> list["Responder"]:
    r"""Start daemon-threaded responders for every IP in the DB plus the
    \_global room. Returns the list of Responder instances so callers can
    inspect health.

    Used by atlas_ui at boot when CHAT_RESPONDER_AUTOSTART=1 so launching
    the UI is enough to bring up all per-room bots — no separate terminals,
    no manual process management. Daemons die with the parent process.

    `bridge` (a _MultiUserBridge) lets each responder fan its reply out
    to every connected WS client in real time. When omitted, the function
    looks it up from `core.orchestrator_inject.get_registered_bridge()`
    which atlas_ui populates at boot.

    Idempotent against repeated calls only in the sense that fresh threads
    are spawned each time; callers should call this exactly once per
    ATLAS UI boot."""
    import threading
    db = db or AtlasDB()
    if bridge is None:
        try:
            from core.orchestrator_inject import get_registered_bridge
            bridge = get_registered_bridge()
        except Exception:  # pragma: no cover
            bridge = None
    rooms: list[str] = ["_global"]
    try:
        for ws in db._fetchall("SELECT id FROM workspaces"):
            for ip in db.list_ip_blocks(ws["id"]):
                rooms.append(ip["ip_name"])
    except Exception:  # pragma: no cover — empty DB at first boot is fine
        pass

    started: list[Responder] = []
    for room in rooms:
        try:
            r = Responder(room=room, db=db, bridge=bridge)
        except SystemExit:
            continue   # unknown room name — skip gracefully
        t = threading.Thread(
            target=r.run_forever,
            name=f"chat-responder-{room}",
            daemon=True,
        )
        t.start()
        started.append(r)
    print(f"[chat-responder] autostart: spawned {len(started)} responder(s) "
          f"({', '.join(r.room for r in started)})")
    return started


if __name__ == "__main__":
    sys.exit(main())
