"""
src/textual_main.py — Textual TUI entry point for common_ai_agent

Usage:
    python src/textual_main.py

Terminal mode (unchanged):
    python src/main.py
"""

from __future__ import annotations

import os
import sys

# ── Path setup ──────────────────────────────────────────────────────────────
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except (OSError, FileNotFoundError):
    # CWD no longer exists (e.g. deleted dir) — fall back to argv[0]
    _script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _project_root)

# Publish the common_ai_agent install root so file-resolution tools (read_file,
# find_files, grep_file) can fall back to it when a relative path doesn't
# exist in the user's cwd. This lets each developer run `python3 textual_main.py`
# from THEIR own project directory (e.g. NEW_ATLAS, NEW_IP, …) and still
# reference shared assets like `workflow/ssot-gen/rules/ssot-template.yaml`
# without symlinks or absolute paths in their prompts. Tools should NEVER
# write to this root — only read.
os.environ.setdefault("COMMON_AI_AGENT_HOME", _project_root)

_vendor_dir = os.path.join(_project_root, "vendor")
if _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)

# ── Python 3.7 compatibility: backport typing helpers via typing_extensions ──
if sys.version_info < (3, 8):
    import typing
    try:
        import typing_extensions as _te
        for _attr in ("get_args", "get_origin", "Literal", "Protocol",
                      "TypedDict", "Final", "Annotated", "get_type_hints"):
            if not hasattr(typing, _attr) and hasattr(_te, _attr):
                setattr(typing, _attr, getattr(_te, _attr))
    except ImportError:
        pass

# Increase escape-sequence timeout to 1000ms (ncurses standard default).
# When moving a cmux tab or terminal window, focus/resize escape sequences
# (\x1b[O, \x1b[8;...t, etc.) can arrive in chunks with >100ms gaps.
# Textual's default 100ms ESCAPE_DELAY fires spurious ESC in those gaps.
# Force-set (not setdefault) so existing env values don't override this.
os.environ["ESCDELAY"] = "300"

try:
    import textual  # noqa: F401
    _TEXTUAL_OK = True
except Exception as e:
    print(f"[warn] Textual unavailable ({e}) - falling back to terminal mode.")
    _TEXTUAL_OK = False

import config
import main as _agent

# Enable Windows Virtual Terminal Processing early for Textual entry point.
# (display.py also auto-enables on import, but this guarantees coverage
# even if import order changes.)
from lib.display import enable_windows_virtual_terminal
enable_windows_virtual_terminal()

if _TEXTUAL_OK:
    from lib.textual_ui import AgentTUI, ContextUpdate


# ── Context info helper ───────────────────────────────────────────────────────

def _emit_context(app: AgentTUI, estimated_tokens: int = 0, max_tok_override: int = 0) -> None:
    """Read current token/skill state from main.py and post ContextUpdate.

    estimated_tokens: pre-computed estimate to use when last_input_tokens == 0
                      (e.g. after /clear or /compact before the next LLM call).
    """
    try:
        _last   = getattr(_agent.llm_client, "last_input_tokens", 0)
        # Use actual API tokens when available; fall back to caller-supplied estimate
        # so /clear and /compact reflect the new token count immediately.
        tokens  = _last if _last > 0 else estimated_tokens
        max_tok = max_tok_override or getattr(config, "MAX_CONTEXT_TOKENS", 128000)
        # Sync active model — use get_active_model() so cursor-agent shows "Cursor (Auto)"
        try:
            from src.llm_client import get_active_model as _get_active_model
            _m = _get_active_model()
        except Exception:
            _m = getattr(config, "MODEL_NAME", "")
        app._active_model = _m or app._active_model
        app._refresh_model_sidebar()
        fn      = getattr(_agent, "load_active_skills", None)
        forced  = getattr(fn, "forced_skills", set()) or set()
        active_list = getattr(fn, "active_skills", []) or []
        auto    = getattr(fn, "_active_skill", None)

        # Priority: active_skills (final merged, set after each LLM call)
        #           > forced_skills (user-explicit)
        #           > _active_skill (auto-routed)
        names: list[str] = []
        if active_list:
            names = list(active_list)
        elif forced:
            names = sorted(forced)
        elif auto:
            names = [auto]

        if len(names) > 2:
            skill = f"{names[0]}, +{len(names)-1}"
        else:
            skill = ", ".join(names)

        mode = "plan" if os.environ.get("PLAN_MODE") == "true" else "normal"

        # Don't overwrite sidebar with 0 — keep _init_sidebar estimate until
        # the first real LLM call provides an actual token count.
        if tokens > 0:
            app.post_message(ContextUpdate(tokens, max_tok, skill, mode))
        elif skill:
            # No token data yet, but skill changed — update skill display only
            app.post_message(ContextUpdate(app._ctx_tokens, max_tok, skill, mode))
        elif mode != getattr(app, "_ctx_mode", "normal"):
            # Mode changed without token/skill update — emit to sync mode display
            app.post_message(ContextUpdate(app._ctx_tokens, max_tok, app._ctx_skill, mode))
    except Exception:
        pass


# ── Agent runner ──────────────────────────────────────────────────────────────

def _run_agent(app: AgentTUI) -> None:
    """Called inside the AgentTUI worker thread."""
    config.ENABLE_MULTILINE_INPUT = False

    from lib.textual_ui import StreamChunk, ReasoningChunk, TodoUpdate, FlushResponse, TokenUsage, AskUserRequest

    def _todo_and_context(text: str) -> None:
        app.post_message(TodoUpdate(text))
        _emit_context(app)

    _agent._textual_input_fn          = app._input_bridge.get_input
    _agent._textual_emit_content_fn   = lambda line: app.post_message(StreamChunk(line))
    _agent._textual_emit_reasoning_fn = lambda line, blank=False: app.post_message(ReasoningChunk(line, blank))
    _agent._textual_emit_todo_fn      = _todo_and_context
    _agent._textual_emit_flush_fn     = lambda: app.post_message(FlushResponse())
    _agent._textual_emit_context_fn   = lambda tok, max_tok: _emit_context(app, tok, max_tok)
    _agent._textual_emit_token_fn     = lambda in_tok, cache_tok, out_tok: app.post_message(TokenUsage(in_tok, cache_tok, out_tok))
    _agent._textual_esc_check_fn          = app.check_and_reset_interrupt
    _agent._textual_poll_human_input_fn   = app._input_bridge.poll_interrupt

    # Set agent_running flag so input routing knows to use interrupt queue
    def _set_agent_running(val: bool):
        app._input_bridge.agent_running = val

    _agent._textual_set_agent_running_fn = _set_agent_running

    # ── ask_user → Textual modal ────────────────────────────────────
    # Each ask_user call pushes an AskUserModal screen; the agent thread
    # blocks on a per-flow queue until the user submits or cancels.
    # Multiple ask_user calls within one agent turn stack naturally —
    # Textual processes push_screen sequentially.
    import queue as _queue
    import uuid as _uuid

    def _format_answer(ans: dict, options: list) -> str:
        selected_ids = ans.get("selected") or []
        custom = (ans.get("custom") or "").strip()
        label_by_id = {o.get("id"): o.get("label", o.get("id")) for o in options or []}
        labels = [label_by_id.get(sid, sid) for sid in selected_ids]
        parts = []
        if labels: parts.append("selected: " + ", ".join(labels))
        if custom: parts.append("note: " + custom)
        return " · ".join(parts) if parts else "(user submitted with no selection)"

    def _ask_user_textual(question, options, kind, subtitle, questions=None):
        flow_id = "qa_" + _uuid.uuid4().hex[:10]
        answer_q: _queue.Queue = _queue.Queue()
        app.post_message(AskUserRequest(
            flow_id=flow_id, question=question, kind=kind,
            subtitle=subtitle or "", options=options or [],
            answer_q=answer_q, questions=questions,
        ))
        try:
            ans = answer_q.get(timeout=900)  # 15 min ceiling
        except _queue.Empty:
            return "[ask_user: no answer received within 15 min]"
        # Cancel-all from the user — match Claude Code's wording so the
        # agent recognizes this consistent signal.
        if ans.get("type") == "cancel":
            return "User declined to answer questions"
        # Batched response: list of per-question answers.
        if questions and "answers" in ans:
            blocks = []
            for q, qa in zip(questions, ans.get("answers") or []):
                label = (q.get("subtitle") or q.get("question", ""))[:40]
                blocks.append(f"  • {label}\n    {_format_answer(qa, q.get('options'))}")
            return "Batched answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
        return _format_answer(ans, options or [])

    try:
        from core import tools as _tools
        if hasattr(_tools, "set_ask_user_callback"):
            _tools.set_ask_user_callback(_ask_user_textual)
    except Exception as _e:
        print(f"[warn] ask_user callback registration failed: {_e}")

    _agent.chat_loop()
    # After chat_loop finishes, the conversation history has been saved.
    # Now signal the app to close cleanly.
    app.exit()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse as _argparse

    _effort_aliases = {
        'l': 'low',
        'm': 'medium',
        'med': 'medium',
        'mid': 'medium',
        'h': 'high',
        'hi': 'high',
        'x': 'xhigh',
        'xh': 'xhigh',
        'xhi': 'xhigh',
        'max': 'xhigh',
    }

    _parser = _argparse.ArgumentParser(
        prog="textual_main",
        description="common_ai_agent launcher — picks textual / atlas / web UI",
        add_help=True,
    )
    _parser.add_argument('-s', '--session', default=None)
    _parser.add_argument('-w', '--workspace', '-wf', '--workflow', default=None,
                         help='Workflow name (e.g. ssot-gen, rtl-gen, sim, lint)')
    _parser.add_argument('-u', '--ui', default=None,
                         choices=['textual', 'atlas', 'web'],
                         help='UI mode (overrides UI_MODE in .config). '
                              'textual = terminal TUI, atlas = React/WebSocket browser UI, '
                              'web = legacy SSE browser UI')
    _parser.add_argument('--port', type=int, default=None,
                         help='Override port for atlas/web UI '
                              '(defaults to ATLAS_UI_PORT=8765 / WEB_UI_PORT=8080)')
    _parser.add_argument('--host', default=None,
                         help='Override bind host for atlas/web UI '
                              '(defaults to 127.0.0.1; use 0.0.0.0 for LAN exposure)')
    _parser.add_argument('--model', type=str, default='',
                         help='Active LLM profile or bare model name. Profiles '
                              '(PROFILE_<name>_BASE_URL/API_KEY/MODEL in .env) switch '
                              'all three at once; cursor-cli/claude-cli use local CLI backends; '
                              'bare names only override LLM_MODEL_NAME. '
                              'gpt-5* names trigger ChatGPT OAuth (opencode_backend).')
    _parser.add_argument('--effort', default='',
                        help='Responses API reasoning effort: none|low|medium|high|xhigh')
    _parser.add_argument('--admin', nargs='?', const='3002', default=None,
                         help='Also launch the standalone admin server '
                              '(src/atlas_admin.py). Pass a port to override '
                              '(default 3002). Bind host comes from --admin-host '
                              '(default 127.0.0.1, keep admin off the LAN).')
    _parser.add_argument('--admin-host', default='127.0.0.1',
                         help='Bind host for the --admin server (default '
                              '127.0.0.1). Set to 0.0.0.0 only when you '
                              'understand the admin surface is now LAN-reachable.')
    _args, _ = _parser.parse_known_args()

    # --model: mirror src/main.py:2510 handler so textual_main behaves the same.
    # Without this, `--model gpt-5.5` was silently ignored — the boot-time
    # USE_OPENCODE_OAUTH default still ran but the user's intended override
    # never reached set_active_profile / activate_opencode_oauth.
    if getattr(_args, 'model', ''):
        _m = _args.model.strip()
        if config.set_active_profile(_m):
            print(f"[--model] profile '{_m}' active "
                  f"→ {config.MODEL_NAME} @ {config.BASE_URL}")
        elif config.activate_cli_backend(_m):
            from src.llm_client import get_active_model as _get_active_model
            print(f"[--model] CLI backend active → {_get_active_model()}")
        elif config.is_opencode_model(_m) and config.auto_opencode_oauth_allowed():
            _bare = _m.split("/", 1)[-1]
            if config.activate_opencode_oauth(_bare):
                print(f"[--model] opencode-OAuth active → "
                      f"{config.MODEL_NAME} @ {config.BASE_URL}")
            else:
                print(f"[--model] '{_m}' looks like an OpenAI model but "
                      f"no opencode credential is available. "
                      f"Run: python -m src.opencode_backend login")
        else:
            _deact_cli = getattr(config, "deactivate_cli_backends", None)
            if callable(_deact_cli):
                _deact_cli()
            _mark_override = getattr(config, "mark_runtime_model_override", None)
            if callable(_mark_override):
                _mark_override()
            config.MODEL_NAME = _m
            os.environ['LLM_MODEL_NAME'] = _m
            os.environ['MODEL_NAME'] = _m
            print(f"[--model] '{_m}' is not a defined profile; "
                  f"applied as bare LLM_MODEL_NAME override "
                  f"(BASE_URL/API_KEY unchanged).")

    # --effort: set runtime reasoning effort for Responses API.
    # Mirrors `/effort` command behavior (same aliases + env updates),
    # but applies only for this process before UI bootstraps.
    if getattr(_args, 'effort', ''):
        _raw_effort = _args.effort.strip().lower()
        _effort = _effort_aliases.get(_raw_effort, _raw_effort)
        if _effort in ('none', 'low', 'medium', 'high', 'xhigh'):
            config.REASONING_MODE = _effort
            config.REASONING_EFFORT = _effort
            config.GLM_THINKING_TYPE = 'disabled' if _effort == 'none' else 'enabled'
            os.environ['REASONING_MODE'] = _effort
            os.environ['REASONING_EFFORT'] = _effort
            os.environ['GLM_THINKING_TYPE'] = config.GLM_THINKING_TYPE
            print(f"[--effort] reasoning effort set to {_effort} (provider-specific mapping applies at request time)")
        else:
            print(f"[--effort] unknown effort: {_raw_effort}. Allowed: none, low, medium, high, xhigh")

    _session_name = _args.session or _args.workspace or 'default'
    _agent._setup_session(_session_name)

    # Apply workflow if specified (same as main.py -w/--workflow)
    if _args.workspace:
        try:
            _agent._setup_workspace(_args.workspace)
        except SystemExit:
            raise  # _setup_workspace calls sys.exit(1) on unknown workspace
        except Exception as _e:
            print(f"[warn] Workflow '{_args.workspace}' failed to load: {_e}")

    # ── UI Mode routing ────────────────────────────────────────────────────
    # Priority: --ui CLI flag > UI_MODE env/config > "textual" default.
    _ui_mode = (_args.ui or getattr(config, "UI_MODE", "textual")).lower()
    _web_port   = _args.port or getattr(config, "WEB_UI_PORT", 8080)
    _atlas_port = _args.port or getattr(config, "ATLAS_UI_PORT", 8765)
    _atlas_host = _args.host or getattr(config, "ATLAS_UI_HOST", "127.0.0.1")
    _web_host   = _args.host or getattr(config, "WEB_UI_HOST",   "127.0.0.1")

    # --admin: launch the standalone admin server as a subprocess
    # alongside the main UI. Always bound to 127.0.0.1 so the admin
    # surface doesn't leak onto the LAN even when --host=0.0.0.0.
    # Child is left to die with the parent — atexit cleanup keeps the
    # spawn lifecycle simple. Failures are non-fatal.
    if _args.admin:
        try:
            import atexit as _atexit
            import os as _os_admin
            import subprocess as _sp_admin
            import sys as _sys_admin
            _admin_port = str(_args.admin).strip() or "3002"
            # Invoke atlas_admin.py by absolute path — it self-bootstraps
            # its PYTHONPATH from __file__, so `python <path>/atlas_admin.py`
            # works regardless of caller cwd. `python -m src.atlas_admin`
            # broke whenever the spawning shell's cwd didn't expose a
            # `src/` package on sys.path.
            _admin_script = _os_admin.path.join(
                _os_admin.path.dirname(_os_admin.path.abspath(__file__)),
                "atlas_admin.py",
            )
            # If --admin-host wasn't explicitly provided, follow --host.
            # This is the natural default — operators who exposed the
            # main UI on a LAN IP usually want admin on the same IP.
            # 127.0.0.1 stays the implicit default when neither was set.
            _admin_host = getattr(_args, 'admin_host', None)
            if not _admin_host or _admin_host == '127.0.0.1':
                _admin_host = (_args.host or _admin_host or '127.0.0.1')
            _admin_proc = _sp_admin.Popen(
                [_sys_admin.executable, _admin_script,
                 "--port", _admin_port, "--host", _admin_host],
                stdout=None, stderr=None,
                cwd=_os_admin.path.dirname(_os_admin.path.dirname(_admin_script)),
            )
            _atexit.register(lambda p=_admin_proc: (p.terminate() if p.poll() is None else None))
            print(f"\n  [admin] launched standalone admin server → http://{_admin_host}:{_admin_port}/admin", flush=True)
        except Exception as _exc_admin:
            print(f"[warn] --admin: failed to spawn admin server: {_exc_admin}", flush=True)

    if _ui_mode == "atlas":
        from src.atlas_ui import run_atlas_ui
        run_atlas_ui(port=_atlas_port, host=_atlas_host)
    elif _ui_mode == "web":
        from src.web_ui import run_web_ui
        run_web_ui(port=_web_port, host=_web_host)
    elif _TEXTUAL_OK:
        from lib.textual_ui import AgentTUI, ContextUpdate
        AgentTUI(_run_agent).run()
    else:
        print("[fallback] Running in terminal mode (src/main.py).")
        _agent.chat_loop()
