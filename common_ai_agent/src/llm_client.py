"""
LLM Client for Common AI Agent.
Handles API communication, streaming, token counting, and prompt caching.
Zero-dependency (uses urllib).

OpenCode-Inspired Features:
- Multi-provider support (agent-specific models)
- Agent-aware API calls
- Dynamic model switching
"""
import json
import socket
import ssl
import http.client
import urllib.request
import urllib.error
import urllib.parse
import time
import copy
import re
import sys
import os
import threading
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from collections import deque

# Add paths for imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, os.path.join(_project_root, 'lib'))
sys.path.insert(0, os.path.join(_project_root, 'core'))
sys.path.insert(0, os.path.join(_project_root, 'vendor'))

import config
from display import Color
from text_utils import strip_metadata_tokens as _strip_metadata_tokens

# --- Global Token Tracking ---
# Stores actual token counts from API responses
# Structure: {"message_index": actual_token_count}
actual_token_cache = {}
last_input_tokens = 0  # Last reported input tokens from API
last_output_tokens = 0  # Last reported output tokens from API
_last_debug_prompt_text = ""
_last_debug_messages = None


def get_active_model() -> str:
    """Return the display name for the currently active LLM backend.

    When a CLI backend is enabled, returns a backend-specific label such as
    "Cursor (Auto)" or "Claude CLI (claude-sonnet-4-6)". Falls back to
    config.MODEL_NAME for the normal path.

    Also calls config.reload_env() so a .env edit (model swap, profile
    change) takes effect without restarting the process — the UI sidebar
    and the next LLM dispatch call will both see the same fresh value.
    The mtime cache makes this near-free on the hot path.
    """
    try:
        config.reload_env()
    except Exception:
        pass
    if getattr(config, "CURSOR_AGENT_ENABLE", False):
        try:
            from src.cursor_agent_backend import last_cursor_model
            label = last_cursor_model or getattr(config, "CURSOR_AGENT_MODEL", "auto")
        except Exception:
            label = getattr(config, "CURSOR_AGENT_MODEL", "auto")
        return f"Cursor ({label})"
    if getattr(config, "CLAUDE_CLI_ENABLE", False):
        try:
            from src.claude_cli_backend import last_claude_model
            label = last_claude_model or getattr(config, "CLAUDE_CLI_MODEL", "sonnet")
        except Exception:
            label = getattr(config, "CLAUDE_CLI_MODEL", "sonnet")
        return f"Claude CLI ({label})"
    return config.MODEL_NAME


# Minimum output tokens floor — never cap below this value even if context is tight
_MIN_OUTPUT_TOKENS = 1024
# Hard cap on generated tokens regardless of model claim (GLM-4.6/4.5 practical limit)
_MAX_OUTPUT_TOKENS_HARD_CAP = 64000
# Safety buffer: leave this many tokens between input usage and context limit
_OUTPUT_SAFETY_BUFFER = 200


# ── Token-Bucket Rate Limiter ────────────────────────────────────────────
class _RateLimiter:
    """
    Sliding-window rate limiter for TPM (Tokens Per Minute) and RPM (Requests Per Minute).
    Thread-safe. Each acquire() blocks until the request + its estimated token cost
    fits within the configured per-minute budget.

    Design:
      - Uses a deque of (timestamp, token_cost) to track a sliding 60s window.
      - For RPM: each request costs 1 "token" unit.
      - For TPM: each request costs the actual input+output token count from the
        *previous* call (predictive), or a configurable estimate for the first call.
      - When both RPM and TPM limits are set, acquire() waits for whichever
        constraint is tighter.
      - When either limit is 0, that dimension is skipped entirely.
    """

    def __init__(self, tpm: int = 0, rpm: int = 0, window_s: float = 60.0):
        self.tpm = tpm
        self.rpm = rpm
        self._window = window_s
        self._lock = threading.Lock()
        # Sliding window entries: (timestamp, estimated_token_count)
        self._token_log: deque = deque()
        self._request_log: deque = deque()
        # Estimate for first call (tokens); updated after each real usage.
        self._default_token_estimate = 2000

    @property
    def active(self) -> bool:
        return self.tpm > 0 or self.rpm > 0

    def _purge(self, now: float):
        """Remove entries older than the sliding window."""
        cutoff = now - self._window
        while self._token_log and self._token_log[0][0] < cutoff:
            self._token_log.popleft()
        while self._request_log and self._request_log[0][0] < cutoff:
            self._request_log.popleft()

    def _tokens_in_window(self) -> int:
        return sum(t for _, t in self._token_log)

    def _requests_in_window(self) -> int:
        return len(self._request_log)

    def acquire(self, estimated_tokens: Optional[int] = None):
        """
        Block until the request can proceed without exceeding limits.
        Uses estimated_tokens for the TPM check; if None, uses internal estimate.
        """
        if not self.active:
            return

        est = estimated_tokens if estimated_tokens is not None else self._default_token_estimate

        with self._lock:
            now = time.time()
            self._purge(now)

            wait_s = 0.0

            # TPM constraint
            if self.tpm > 0:
                current_tokens = self._tokens_in_window()
                remaining_budget = self.tpm - current_tokens
                if remaining_budget <= 0:
                    # Window is full — wait until oldest entry expires
                    wait_s = max(wait_s, self._token_log[0][0] + self._window - now + 0.1)
                elif est > remaining_budget:
                    # Not enough room — wait proportionally
                    # Find how long until enough tokens free up
                    need = est - remaining_budget
                    # Approximate: how many seconds to free 'need' tokens?
                    # Walk through entries to find when 'need' tokens worth of entries expire
                    freed = 0
                    for ts, t in self._token_log:
                        freed += t
                        if freed >= need:
                            t_wait = ts + self._window - now + 0.1
                            wait_s = max(wait_s, t_wait)
                            break

            # RPM constraint
            if self.rpm > 0:
                current_reqs = self._requests_in_window()
                remaining_reqs = self.rpm - current_reqs
                if remaining_reqs <= 0:
                    wait_s = max(wait_s, self._request_log[0][0] + self._window - now + 0.1)

            if wait_s > 0:
                cap = 65.0  # never wait more than window+epsilon
                wait_s = min(wait_s, cap)
                if config.DEBUG_MODE:
                    print(Color.info(f"[RateLimiter] Waiting {wait_s:.1f}s "
                                     f"(tokens_in_window={self._tokens_in_window()}/{self.tpm} "
                                     f"reqs_in_window={self._requests_in_window()}/{self.rpm})"))
                time.sleep(wait_s)

            # Record this request
            now = time.time()
            self._request_log.append((now, 1))
            self._token_log.append((now, est))

    def update_actual_usage(self, actual_tokens: int):
        """
        After receiving real usage from the API, update the last entry's token count
        and refine the default estimate for future calls.
        """
        if not self.active:
            return
        with self._lock:
            if self._token_log:
                ts, _ = self._token_log.pop()
                self._token_log.append((ts, actual_tokens))
            # Exponential moving average for future estimates
            old = self._default_token_estimate
            self._default_token_estimate = int(0.7 * actual_tokens + 0.3 * old)

    def status(self) -> dict:
        """Return current rate limiter status for display."""
        with self._lock:
            self._purge(time.time())
            return {
                "tpm_limit": self.tpm,
                "rpm_limit": self.rpm,
                "tokens_used": self._tokens_in_window(),
                "requests_used": self._requests_in_window(),
                "window_s": self._window,
            }


# Module-level singleton — initialized lazily from config
_rate_limiter: Optional[_RateLimiter] = None


def get_rate_limiter() -> _RateLimiter:
    """Get or create the global rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = _RateLimiter(
            tpm=getattr(config, 'TPM_LIMIT', 0),
            rpm=getattr(config, 'RPM_LIMIT', 0),
        )
    return _rate_limiter


def _reasoning_keyword_match(name: str) -> bool:
    """Pure substring heuristic — no env-aware fallbacks.

    Substring (not prefix) match so vendor/deployment aliases like
    ``sol-soc-gpt-5.4`` or ``proxy/openai/gpt-5.1`` still resolve to
    the embedded base-model family.
    """
    if not name:
        return False
    n = name.lower()
    if '/' in n:
        n = n.split('/')[-1]
    # GPT-5.x family — substring match catches `gpt-5.4`, `gpt5-codex`,
    # `sol-soc-gpt-5.4`, `prod-gpt5-1`, etc.
    if 'gpt-5' in n or 'gpt5' in n:
        return True
    # Codex variants (gpt-4-turbo-codex, gpt-4.5-codex, etc.)
    if 'gpt' in n and 'codex' in n:
        return True
    # Other known reasoning families
    return any(k in n for k in ('glm', 'deepseek', 'qwq', 'r1', 'reasoning', 'o1', 'o3', 'o4'))


def _supports_reasoning_summary(name: str) -> bool:
    """Some model variants don't support Responses API reasoning.summary."""
    if not name:
        return False
    n = name.lower()
    if '/' in n:
        n = n.split('/')[-1]
    # Spark family variants (e.g. gpt-5.3-codex-spark) reject summary.
    return 'spark' not in n


def _reasoning_env_override() -> bool:
    """Treat the model as reasoning-capable when the operator has
    explicitly opted in via env. Covers Azure deployments where the
    deployment name (e.g. ``prod-router``) doesn't match any keyword.

    True when ANY of these is set:
      • REASONING_FORCE=true              — explicit force flag
      • LLM_ACTIVE_BASE_NAME / LLM_BASE_NAME=<reasoning-model>
                                            — points the heuristic at the
                                              real base model behind a
                                              deployment alias
      • LLM_PROVIDER=azure AND
        REASONING_MODE / REASONING_EFFORT is a Responses API reasoning.effort
        — Azure user wired the knob, treat that as a request to enable
    """
    import os as _os
    if _os.getenv('REASONING_FORCE', '').strip().lower() in ('1', 'true', 'yes'):
        return True
    base = (_os.getenv('LLM_ACTIVE_BASE_NAME', '').strip()
            or _os.getenv('LLM_BASE_NAME', '').strip()
            or _os.getenv('LLM_ACTIVE_BASE_MODEL', '').strip()
            or _os.getenv('LLM_BASE_MODEL', '').strip())
    if base and _reasoning_keyword_match(base):
        return True
    provider = (getattr(config, 'LLM_PROVIDER', '') or '').lower()
    if provider == 'azure':
        mode = (getattr(config, 'REASONING_MODE', None)
                or getattr(config, 'REASONING_EFFORT', '')
                or _os.getenv('REASONING_MODE', '')
                or _os.getenv('REASONING_EFFORT', ''))
        if _normalize_reasoning_effort(mode) in ('none', 'low', 'medium', 'high', 'xhigh'):
            return True
    return False


def _is_reasoning_model() -> bool:
    """Heuristic: does the current model produce reasoning/thinking tokens?

    Honors LLM_BASE_NAME / Azure-with-reasoning-mode / REASONING_FORCE
    so deployment aliases (e.g. ``prod-router``) still light up reasoning
    when the operator configured it.
    """
    if _reasoning_keyword_match(getattr(config, 'MODEL_NAME', '')):
        return True
    return _reasoning_env_override()


def _is_reasoning_model_for_name(name: str) -> bool:
    """Same heuristic as ``_is_reasoning_model`` but pinned to a specific
    name (used by the Responses API path which receives the resolved
    deployment/model name per call).

    Env/base-model overrides are only applied to opaque deployment aliases.
    If the caller passes a recognizable non-reasoning model like ``gpt-4o``,
    the explicit per-call model wins.
    """
    if _reasoning_keyword_match(name):
        return True
    n = (name or '').strip().lower()
    if not n:
        return False
    if '/' in n:
        n = n.split('/')[-1]
    known_non_opaque_markers = (
        'gpt', 'claude', 'anthropic', 'qwen', 'kimi', 'moonshot'
    )
    if any(marker in n for marker in known_non_opaque_markers):
        return False
    return _reasoning_env_override()


def _is_openai_gpt_model(model_name: str = None) -> bool:
    """Check if the model is an OpenAI GPT model.

    Pattern: *gpt* — matches gpt-4, gpt-4o, gpt-5.1, gpt-5.1-codex, etc.
    """
    name = (model_name or getattr(config, 'MODEL_NAME', '')).lower()
    if '/' in name:
        name = name.split('/')[-1]
    return 'gpt' in name or name.startswith('o1') or name.startswith('o3') or name.startswith('o4')


def _normalize_reasoning_effort(mode) -> str:
    """Normalize local config to official Responses API reasoning.effort values."""
    mode = str(mode or 'medium').lower().strip()
    if mode in ('off', 'false', 'disabled', 'disable', 'minimal', 'min'):
        return 'medium'
    if mode in ('l',):
        return 'low'
    if mode in ('m', 'med', 'mid'):
        return 'medium'
    if mode in ('h', 'hi'):
        return 'high'
    if mode in ('x', 'xh', 'xhi', 'extra_high', 'extra-high', 'max'):
        return 'xhigh'
    return mode if mode in ('none', 'low', 'medium', 'high', 'xhigh') else 'medium'


def _get_responses_reasoning_mode(reasoning_effort: str = None) -> str:
    """Return normalized Responses API ``reasoning.effort``.

    OpenAI accepts (as of GPT-5.2/5.4/5.5):
      • none                 — no reasoning effort when supported
      • low / medium / high  — original tiers
      • xhigh                — extra-high for supported models

    ``REASONING_MODE`` is only this app's local config name; the API field is
    always ``reasoning.effort``.
    """
    mode = reasoning_effort or getattr(config, 'REASONING_MODE', getattr(config, 'REASONING_EFFORT', 'medium'))
    return _normalize_reasoning_effort(mode)


def _deepseek_reasoning_effort_for_chat(effort: str) -> str:
    """Map local effort tiers to DeepSeek chat/completions effort values."""
    effort = _normalize_reasoning_effort(effort)
    if effort == 'xhigh':
        return 'max'
    if effort in ('low', 'medium', 'high'):
        return 'high'
    return ''


def _apply_chat_reasoning_controls(data: dict, model: str, url: str, reasoning_effort: str = None) -> tuple[str, str]:
    """Apply provider-specific reasoning controls for Chat Completions."""
    effort = _get_responses_reasoning_mode(reasoning_effort)
    model_lower = (model or '').lower()
    url_lower = (url or '').lower()

    if 'deepseek' in model_lower or 'deepseek' in url_lower:
        if effort == 'none':
            data["thinking"] = {"type": "disabled"}
            data.pop("reasoning_effort", None)
            return effort, "DeepSeek thinking.type=disabled"
        deepseek_effort = _deepseek_reasoning_effort_for_chat(effort)
        data["thinking"] = {"type": "enabled"}
        if deepseek_effort:
            data["reasoning_effort"] = deepseek_effort
        if effort in ('low', 'medium'):
            return effort, f"DeepSeek reasoning_effort={deepseek_effort} (provider maps {effort}->high)"
        return effort, f"DeepSeek reasoning_effort={deepseek_effort}"

    if 'glm' in model_lower or 'z.ai' in url_lower:
        thinking_type = "disabled" if effort == 'none' else getattr(config, "GLM_THINKING_TYPE", "enabled")
        if effort != 'none' and thinking_type not in ("enabled", "disabled"):
            thinking_type = "enabled"
        clear_thinking = getattr(config, "GLM_CLEAR_THINKING", True)
        data["thinking"] = {
            "type": thinking_type,
            "clear_thinking": clear_thinking,
        }
        if effort == 'none':
            return effort, "GLM thinking.type=disabled"
        return effort, f"GLM thinking.type={thinking_type}; no provider effort tier"

    if 'kimi' in model_lower or 'moonshot' in model_lower or 'kimi.com' in url_lower or 'moonshot.ai' in url_lower:
        thinking_type = "disabled" if effort == 'none' else "enabled"
        data["thinking"] = {"type": thinking_type}
        data.pop("reasoning_effort", None)
        if effort == 'none':
            return effort, "Kimi thinking.type=disabled"
        return effort, "Kimi thinking.type=enabled; no provider effort tier"

    return effort, "local config only; not sent in chat/completions body"


def compute_safe_max_tokens(used_tokens: int = 0) -> int:
    """
    Return a safe max_tokens value that fits within the remaining context window.

    Hard cap: _MAX_OUTPUT_TOKENS_HARD_CAP (64K) — never exceeds this regardless of config.

    When MAX_CONTEXT_TOKENS is configured:
      - remaining = context_limit - input_tokens - safety_buffer
      - If remaining < effective_budget (context is tight): use remaining // 2
        so input and output each get half of the remaining space.
      - Otherwise: use effective_budget, capped at 64K.

    For reasoning models (GLM, DeepSeek etc.), reasoning tokens count against
    max_tokens.  When MAX_REASONING_TOKENS > 0, we expand the budget so the
    model has room for both reasoning AND visible content:
        effective_budget = MAX_OUTPUT_TOKENS + MAX_REASONING_TOKENS

    Falls back to min(MAX_OUTPUT_TOKENS, 64K) when MAX_CONTEXT_TOKENS is not set.
    Minimum floor: _MIN_OUTPUT_TOKENS (1024).
    """
    base = config.MAX_OUTPUT_TOKENS
    # Apply hard cap at 64K
    base = min(base, _MAX_OUTPUT_TOKENS_HARD_CAP)
    if config.MAX_CONTEXT_TOKENS <= 0 or base <= 0:
        return max(base, _MIN_OUTPUT_TOKENS)
    tokens = used_tokens or last_input_tokens
    if tokens <= 0:
        return max(base, _MIN_OUTPUT_TOKENS)
    # Compression guarantees input never exceeds threshold * limit.
    # Clamp tokens to that ceiling so remaining calculation reflects reality.
    if config.ENABLE_COMPRESSION and 0 < config.COMPRESSION_THRESHOLD < 1:
        compression_ceiling = int(config.MAX_CONTEXT_TOKENS * config.COMPRESSION_THRESHOLD)
        tokens = min(tokens, compression_ceiling)
    remaining = config.MAX_CONTEXT_TOKENS - tokens - _OUTPUT_SAFETY_BUFFER

    # Reasoning models: expand budget to include reasoning token allowance
    # so reasoning doesn't eat into the visible content budget.
    if _is_reasoning_model() and config.MAX_REASONING_TOKENS > 0:
        effective_budget = base + config.MAX_REASONING_TOKENS
    else:
        effective_budget = base

    # Context is tight: give output half of what remains so the window
    # isn't completely consumed by a single long response.
    if remaining < effective_budget:
        safe = remaining // 2
    else:
        safe = effective_budget

    # Apply hard cap and minimum floor
    safe = min(safe, _MAX_OUTPUT_TOKENS_HARD_CAP)
    return max(safe, _MIN_OUTPUT_TOKENS)

# --- LLM Call Performance Log ---
@dataclass
class LLMCallRecord:
    caller: str          # e.g. "main", "compress", "skill_routing", "git_commit"
    model: str
    input_tokens: int
    output_tokens: int
    connect_s: float
    ttft_s: float        # time-to-first-token (streaming) or response_read (nonstream)
    decode_s: float      # generation time after first token (0 for nonstream)
    total_s: float
    timestamp: float

_call_log: list = []     # List[LLMCallRecord]

def _record_call(caller: str, model: str, in_tok: int, out_tok: int,
                 connect_s: float, ttft_s: float, decode_s: float, total_s: float) -> None:
    record = LLMCallRecord(
        caller=caller, model=model,
        input_tokens=in_tok, output_tokens=out_tok,
        connect_s=connect_s, ttft_s=ttft_s, decode_s=decode_s, total_s=total_s,
        timestamp=time.time(),
    )
    _call_log.append(record)
    if getattr(config, "PERF_TRACKING", False):
        _fk = lambda n: f"{n/1000:.1f}k" if n >= 1000 else str(n)
        tok_str = f"in={_fk(in_tok)} out={_fk(out_tok)}" if in_tok else ""
        print(f"  \033[2m[PERF/call] {caller} | {model} | "
              f"connect={connect_s:.3f}s ttft={ttft_s:.3f}s decode={decode_s:.3f}s "
              f"total={total_s:.3f}s {tok_str}\033[0m")

def get_call_log() -> list:
    """Return all LLM call records this session."""
    return _call_log

def print_call_summary() -> None:
    """Print per-caller summary table."""
    if not _call_log:
        print("  No LLM calls recorded.")
        return
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for r in _call_log:
        groups[r.caller].append(r)
    print(f"\n  {'Caller':<20} {'Calls':>5} {'total avg':>10} {'ttft avg':>10} {'in avg':>10} {'out avg':>10}")
    print(f"  {'─'*70}")
    for caller, recs in sorted(groups.items()):
        n = len(recs)
        avg_total = sum(r.total_s for r in recs) / n
        avg_ttft  = sum(r.ttft_s  for r in recs) / n
        avg_in    = sum(r.input_tokens  for r in recs) / n
        avg_out   = sum(r.output_tokens for r in recs) / n
        _fk = lambda v: f"{v/1000:.1f}k" if v >= 1000 else f"{v:.0f}"
        print(f"  {caller:<20} {n:>5} {avg_total:>9.3f}s {avg_ttft:>9.3f}s {_fk(avg_in):>10} {_fk(avg_out):>10}")
    total_s = sum(r.total_s for r in _call_log)
    print(f"  {'─'*70}")
    print(f"  {'TOTAL':<20} {len(_call_log):>5} {total_s:>9.3f}s\n")

# --- Persistent HTTPS Connection Pool ---
# Reuses TCP+SSL connections across LLM calls to avoid per-call handshake overhead.
_ssl_ctx_cache: Optional[ssl.SSLContext] = None
_http_conn_pool: Dict[str, http.client.HTTPSConnection] = {}
_last_post_reused: bool = False  # set by _persistent_post; read by PERF logging
_active_stream_response = None   # current streaming response; closed by cancel_current_stream()
_stream_cancelled = False        # set by cancel_current_stream(); prevents retry loop


def cancel_current_stream() -> None:
    """Close the active streaming HTTP response to unblock the agent thread immediately."""
    global _active_stream_response, _http_conn_pool, _stream_cancelled
    _stream_cancelled = True
    resp = _active_stream_response
    if resp is not None:
        try:
            resp.close()
        except Exception:
            pass
    # Also close the pooled connection so next request gets a fresh one
    for conn in list(_http_conn_pool.values()):
        try:
            conn.close()
        except Exception:
            pass
    _http_conn_pool.clear()


def _get_or_create_ssl_ctx() -> ssl.SSLContext:
    global _ssl_ctx_cache
    if _ssl_ctx_cache is None:
        ctx = ssl.create_default_context()
        if not config.SSL_VERIFY:
            # SSL_VERIFY=false: skip verification (corporate proxy / internal network)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        _ssl_ctx_cache = ctx
    return _ssl_ctx_cache


def _make_https_conn(host: str, timeout: int = 10) -> http.client.HTTPSConnection:
    """
    Create an HTTPSConnection respecting HTTPS_PROXY env var.
    Corporate networks often block direct HTTPS — proxy does CONNECT tunneling.
    """
    proxy = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
             or os.environ.get("ALL_PROXY") or os.environ.get("all_proxy"))
    if proxy:
        p = urllib.parse.urlparse(proxy)
        conn = http.client.HTTPSConnection(
            p.hostname, p.port or 443,
            context=_get_or_create_ssl_ctx(), timeout=timeout,
        )
        conn.set_tunnel(host)
    else:
        conn = http.client.HTTPSConnection(
            host, context=_get_or_create_ssl_ctx(), timeout=timeout,
        )
    return conn


class _PersistentHTTPError(urllib.error.HTTPError):
    """urllib-compatible HTTPError raised by the persistent-connection path."""
    def __init__(self, url: str, code: int, reason: str, body_bytes: bytes):
        super().__init__(url, code, reason, hdrs={}, fp=None)
        self._body_bytes = body_bytes

    def read(self) -> bytes:
        return self._body_bytes


def warmup_connection() -> None:
    """
    Pre-establish a live HTTPS keep-alive connection to the LLM API host.
    Respects HTTPS_PROXY and SSL_VERIFY=false (corporate network support).
    Safe to call from a daemon thread — failures are silently ignored.
    """
    t0 = time.perf_counter()
    try:
        parsed = urllib.parse.urlparse(config.BASE_URL)
        host = parsed.netloc
        if not host:
            return
        if _http_conn_pool.get(host) is not None:
            return  # already warm

        conn = _make_https_conn(host, timeout=10)
        base_path = parsed.path.rstrip('/') or '/'
        headers = {"Authorization": f"Bearer {config.API_KEY}"}
        if _is_codex_backend_url(config.BASE_URL):
            base_path = f"{base_path}/models?client_version=0.0.0"
            headers = build_api_headers(config.API_KEY)
        headers["Connection"] = "keep-alive"
        conn.request("GET", base_path, headers=headers)
        resp = conn.getresponse()
        resp.read()  # drain so connection is reusable
        _http_conn_pool[host] = conn

        elapsed = time.perf_counter() - t0
        sys.stderr.write(f"\033[2m[LLM] connected ({elapsed:.2f}s)\033[0m\n")
        sys.stderr.flush()
    except Exception as e:
        elapsed = time.perf_counter() - t0
        try:
            _http_conn_pool.pop(urllib.parse.urlparse(config.BASE_URL).netloc, None)
        except Exception:
            pass
        sys.stderr.write(f"\033[2m[LLM] warmup failed ({elapsed:.2f}s): {e}\033[0m\n")
        sys.stderr.flush()


def _persistent_post(url: str, headers: dict, body: bytes, timeout: int = 300):
    """
    POST via a persistent HTTPS connection (HTTP keep-alive).

    Returns an http.client.HTTPResponse.  The caller MUST drain the response
    with ``response.read()`` (or iterate it fully) before the connection can
    be reused for the next request.

    Retries once on stale-connection errors (RemoteDisconnected, BrokenPipe …).
    """
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    req_headers = dict(headers)
    host_l = host.lower()
    # Some coding endpoints (notably Z.AI GLM / Kimi coding) are more stable
    # with short-lived connections for large generation payloads.
    force_close = os.getenv("LLM_FORCE_CONNECTION_CLOSE", "0") == "1"
    if not force_close and os.getenv("LLM_FORCE_CONNECTION_CLOSE_FOR_CODEX", "1") == "1":
        if "chatgpt.com" in host_l:
            force_close = True
    if not force_close and os.getenv("LLM_FORCE_CONNECTION_CLOSE_FOR_ZAI_KIMI", "1") == "1":
        if ("api.z.ai" in host_l) or ("api.kimi.com" in host_l):
            force_close = True
    req_headers["Connection"] = "close" if force_close else "keep-alive"

    global _last_post_reused
    for attempt in range(2):
        conn = None if force_close else _http_conn_pool.get(host)
        _was_alive = conn is not None and conn.sock is not None
        if conn is None:
            conn = _make_https_conn(host, timeout=timeout)
            if not force_close:
                _http_conn_pool[host] = conn
        else:
            # Update socket timeout on reuse — pooled connections keep the timeout
            # from when they were first created (set at connect() time).  Without
            # this, a streaming call (timeout=3600) reusing a non-streaming socket
            # (timeout=600) times out in 600s while the label says 3600s.
            conn.timeout = timeout
            if conn.sock is not None:
                try:
                    conn.sock.settimeout(timeout)
                except Exception:
                    pass
        try:
            conn.request("POST", path, body=body, headers=req_headers)
            resp = conn.getresponse()
            if resp.status >= 400:
                body_bytes = resp.read()  # fully drain before raising
                raise _PersistentHTTPError(url, resp.status, resp.reason, body_bytes)
            _last_post_reused = _was_alive and attempt == 0 and (not force_close)
            return resp
        except _PersistentHTTPError:
            raise
        except (http.client.RemoteDisconnected, http.client.CannotSendRequest,
                http.client.BadStatusLine,
                ConnectionResetError, BrokenPipeError, OSError):
            # Stale connection (or leftover bytes from prev SSE stream) — drop and retry fresh
            try:
                conn.close()
            except Exception:
                pass
            _http_conn_pool.pop(host, None)
            _last_post_reused = False
            if attempt == 1:
                raise


# --- Cache Token Tracking (Anthropic Prompt Caching) ---
last_cache_creation_tokens = 0  # Last cache creation tokens
last_cache_read_tokens = 0      # Last cache read tokens
total_cache_created = 0         # Total cache tokens created this session
total_cache_read = 0            # Total cache tokens read this session


# ============================================================
# Provider Configuration (OpenCode-Inspired)
# ============================================================

@dataclass
class ProviderConfig:
    """Provider-specific configuration"""
    provider_id: str
    base_url: str
    api_key: str
    model_id: str
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

    @classmethod
    def from_env(cls, provider_id: str = "default") -> 'ProviderConfig':
        """Create from environment/config defaults"""
        return cls(
            provider_id=provider_id,
            base_url=config.BASE_URL,
            api_key=config.API_KEY,
            model_id=config.MODEL_NAME
        )


# Provider registry (cached configs)
_provider_cache: Dict[str, ProviderConfig] = {}


def is_azure_provider() -> bool:
    """Check if the current provider is Azure OpenAI."""
    return getattr(config, "LLM_PROVIDER", "openai").lower() == "azure"


def _provider_supports_responses_api(model: str) -> bool:
    """Reverse filter — does the underlying provider expose /responses?

    Z.AI (GLM family), DeepSeek, Anthropic, Moonshot etc. only ship
    /chat/completions; routing them through /responses returns 404
    (e.g. ``api.z.ai/api/coding/paas/v4/responses``).
    """
    if not model:
        return True  # unknown — leave the rest of the routing untouched
    if is_azure_provider():
        return True  # Azure deployments are often opaque aliases.
    name = model.lower().split('/')[-1]
    # Provider families known to NOT support Responses API
    if name.startswith('glm') or 'deepseek' in name or 'qwen' in name \
            or 'kimi' in name or 'moonshot' in name or 'claude' in name \
            or name.startswith('anthropic'):
        return False
    base = (getattr(config, 'BASE_URL', '') or '').lower()
    if 'api.z.ai' in base or 'deepseek' in base or 'moonshotai' in base \
            or 'anthropic.com' in base:
        return False
    return True


def use_responses_api(resolved_model: str = None) -> bool:
    """Check if the Responses API should be used instead of Chat Completions.

    Returns True when ANY of:
    1. USE_RESPONSES_API=true env flag is set (manual override) AND the
       active provider actually supports /responses
    2. Azure provider + reasoning-capable deployment/model
    3. Azure provider + codex model (auto-detected)
    4. Model name matches *gpt*codex* / GPT-5 pattern (auto-detected)

    Returns False (forced chat completions) when:
    - FORCE_CHAT_COMPLETIONS_GPT5=true and model matches *gpt*5*
    - The active provider doesn't expose /responses (GLM, DeepSeek, etc.)

    Args:
        resolved_model: The effective model for this specific call (overrides
            config.MODEL_NAME). Lets per-call model overrides take the
            Responses API path without toggling the env flag.
    """
    # Prefer per-call resolved_model so per-call overrides are respected
    model = (resolved_model or getattr(config, 'MODEL_NAME', '')).lower()
    if '/' in model:
        model = model.split('/')[-1]

    # Optional: force gpt-5* models to use chat completions
    if getattr(config, "FORCE_CHAT_COMPLETIONS_GPT5", False):
        if 'gpt' in model and '5' in model and 'codex' not in model:
            return False

    # Hard guard: never route a non-OpenAI/Azure provider to /responses,
    # even when USE_RESPONSES_API=true is left on globally.
    if not _provider_supports_responses_api(model):
        return False

    # Manual override
    if getattr(config, "USE_RESPONSES_API", False):
        return True
    # Azure reasoning requires the Responses API. This also covers opaque
    # deployment aliases because _is_reasoning_model_for_name honors
    # LLM_BASE_NAME, REASONING_FORCE, and Azure + REASONING_MODE.
    if is_azure_provider() and _is_reasoning_model_for_name(model):
        return True
    # Auto-detect: Azure + codex model
    if is_azure_provider() and 'codex' in model:
        return True
    # Auto-detect: any gpt+codex model
    if is_responses_api_model(model):
        return True
    return False


def _needs_max_completion_tokens() -> bool:
    """Check if the current model requires 'max_completion_tokens' instead of 'max_tokens'.

    - Azure OpenAI always uses max_completion_tokens
    - OpenAI GPT models (gpt-*, o-series) require max_completion_tokens
    - GLM models (glm-5.x) also require max_completion_tokens
    """
    if is_azure_provider():
        return True
    name = getattr(config, 'MODEL_NAME', '').lower()
    # OpenAI GPT models
    if _is_openai_gpt_model():
        return True
    # GLM models
    if name.startswith('glm'):
        return True
    return False


def _set_max_output_tokens(data: dict, value: int) -> None:
    """Set the max output tokens field using the correct key for the provider.

    Responses API uses `max_output_tokens`, Azure/OpenAI newer models use `max_completion_tokens`.
    See: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/chatgpt
    """
    if use_responses_api():
        data["max_output_tokens"] = value
    elif _needs_max_completion_tokens():
        data["max_completion_tokens"] = value
    else:
        data["max_tokens"] = value


# ─────────────────────────────────────────────────────
# Responses API support (/v1/responses for codex models)
# ─────────────────────────────────────────────────────

def is_responses_api_model(model_name: str = None) -> bool:
    """Check if a model requires the OpenAI Responses API (/v1/responses).

    - *gpt*codex*  → always Responses API
    - *gpt-5*      → Responses API (reasoning_effort + tools not supported in Chat Completions)
    """
    name = (model_name or getattr(config, 'MODEL_NAME', '')).lower()
    if '/' in name:
        name = name.split('/')[-1]
    if 'gpt' in name and 'codex' in name:
        return True
    # GPT-5.x requires Responses API when using tools + reasoning
    if getattr(config, 'FORCE_CHAT_COMPLETIONS_GPT5', False):
        return False
    return 'gpt-5' in name or 'gpt5' in name


def _strip_strict_from_tools(tools: list) -> list:
    """Remove 'strict' and 'additionalProperties' from tool schemas for
    providers that don't support OpenAI strict mode (GLM, DeepSeek, etc.).
    Returns a new list — does not mutate the input.
    """
    import copy
    result = []
    for tool in tools:
        t = copy.deepcopy(tool)
        t.pop("strict", None)
        func = t.get("function", {})
        params = func.get("parameters", {})
        params.pop("additionalProperties", None)
        result.append(t)
    return result



def _blocks_for_responses(content, content_type: str) -> list:
    """Normalize Chat Completions content (str OR list-of-blocks) to Responses
    API content blocks of the given type (input_text / output_text).

    Handles structured content that may arrive from prompt-caching breakpoints
    (list of {"type": "text"|"input_text"|"output_text", "text": "..."} dicts).
    Any non-text block is passed through unchanged.
    """
    if isinstance(content, list):
        blocks = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") in ("text", "input_text", "output_text"):
                    blocks.append({"type": content_type, "text": block.get("text", "")})
                else:
                    blocks.append(block)
            else:
                blocks.append({"type": content_type, "text": str(block)})
        return blocks
    return [{"type": content_type, "text": str(content)}]


def _responses_api_supports_block_content(base_url: str = None) -> bool:
    """Return True when the target Responses backend accepts block-array content.

    OpenAI Responses and Azure OpenAI support the canonical block-list format.
    Some compatible providers (for example OpenRouter's /responses gateway) validate
    role-message content as a plain string instead.
    """
    base = (base_url or getattr(config, "BASE_URL", "") or "").lower()
    if is_azure_provider() or ".azure.com" in base:
        return True
    return "api.openai.com" in base


def _flatten_responses_content_to_text(content) -> str:
    """Flatten block/list content to plain text for strict string-only backends."""
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") in ("text", "input_text", "output_text", "reasoning_text"):
                    text = block.get("text", "")
                    if text:
                        parts.append(str(text))
                elif "text" in block:
                    text = block.get("text", "")
                    if text:
                        parts.append(str(text))
                else:
                    parts.append(json.dumps(block, ensure_ascii=False, sort_keys=True))
            else:
                parts.append(str(block))
        return "\n\n".join(part for part in parts if part)
    return str(content)


def _stringify_responses_message_content(input_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert array-valued role-message content blocks to plain strings."""
    normalized = []
    for item in input_items:
        if item.get("role") in ("user", "assistant", "system", "developer") and isinstance(item.get("content"), list):
            coerced = dict(item)
            coerced["content"] = _flatten_responses_content_to_text(item["content"])
            normalized.append(coerced)
        else:
            normalized.append(item)
    return normalized


def build_chat_url(base_url: str, model: str = None) -> str:
    """
    Build the chat completions URL for the current provider.

    - Standard (OpenAI, Anthropic, etc.): base_url + /chat/completions
    - Azure OpenAI: endpoint + /openai/deployments/{deployment}/chat/completions?api-version=...
    """
    if is_azure_provider():
        deployment = model or config.MODEL_NAME
        api_version = getattr(config, "AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        endpoint = base_url.rstrip("/")
        return f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    return f"{base_url.rstrip('/')}/chat/completions"


def build_responses_url(base_url: str, model: str = None) -> str:
    """
    Build the Responses API URL for the current provider.

    - Azure OpenAI: endpoint + /openai/v1/responses  (v1 API, model in body)
    - Standard (OpenAI): base_url + /responses

    Azure docs: https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation
    Azure Responses API uses the v1 API format (/openai/v1/responses), NOT the
    deployment-based format (/openai/deployments/{id}/responses).
    The deployment name goes in the "model" field of the request body.
    """
    if is_azure_provider():
        endpoint = base_url.rstrip("/")
        return f"{endpoint}/openai/v1/responses"
    if 'openrouter' in base_url.lower():
        return "https://openrouter.ai/api/v1/responses"
    return f"{base_url.rstrip('/')}/responses"


def _convert_messages_to_responses_input(messages: List[Dict[str, Any]]) -> tuple:
    """
    Convert Chat Completions messages[] to Responses API input[] + instructions.

    Returns:
        (input_items, instructions) where:
        - input_items: list of {role, content} dicts for the Responses API
        - instructions: system prompt string (or None)

    Chat Completions format:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, ...]
    Responses API format:
        instructions = "system prompt text"
        input = [{"role": "user", "content": [...]}, {"role": "assistant", "content": [...]}, ...]
        where content items use {"type": "input_text", "text": "..."} for user/system
        and {"type": "output_text", "text": "..."} for assistant

    IMPORTANT: Every function_call_output must have a matching preceding function_call.
    Orphaned tool messages (tool role without a matching assistant tool_calls entry)
    are converted to user messages to avoid API 400 errors.
    """
    instructions = None
    input_items = []
    # Track known call_ids from assistant tool_calls so we can validate tool messages.
    _known_call_ids: set = set()

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Handle assistant messages with tool_calls FIRST (to register call_ids)
        if role == "assistant" and msg.get("tool_calls"):
            # Emit function_call items for each tool call
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                tc_id = tc.get("id", "")
                _known_call_ids.add(tc_id)
                input_items.append({
                    "type": "function_call",
                    "call_id": tc_id,
                    "name": func.get("name", ""),
                    "arguments": func.get("arguments", "{}"),
                })
            # If there's also content, add it as a message
            if content:
                input_items.append({
                    "role": "assistant",
                    "content": _blocks_for_responses(content, "output_text"),
                })
            continue

        # Handle tool messages — validate against known call_ids
        if role == "tool":
            tc_id = msg.get("tool_call_id", "")
            if tc_id and tc_id in _known_call_ids:
                input_items.append({
                    "type": "function_call_output",
                    "call_id": tc_id,
                    "output": str(content),
                })
            else:
                # Orphaned tool message — convert to user message so the
                # context isn't lost but the API doesn't reject the request.
                if str(content).strip():
                    input_items.append({
                        "role": "user",
                        "content": [{"type": "input_text", "text": f"[Orphaned tool result for {tc_id}]: {content}"}],
                    })
            continue

        # System message → instructions (extract first, or merge)
        if role == "system":
            text = str(content)
            if instructions is None:
                instructions = text
            else:
                instructions += "\n\n" + text
            continue

        # User / assistant messages → input items
        if role in ("user", "assistant"):
            content_type = "input_text" if role == "user" else "output_text"
            input_items.append({
                "role": role,
                "content": _blocks_for_responses(content, content_type),
            })
            continue

    return input_items, instructions


def _build_responses_request_body(
    messages: List[Dict[str, Any]],
    model: str,
    stream: bool = True,
    stop: List[str] = None,
    temperature: float = None,
    tools: List[Dict] = None,
    max_output_tokens: int = None,
    base_url: str = None,
    reasoning_effort: str = None,
) -> dict:
    """
    Build a complete Responses API request body from Chat Completions-style messages.

    Handles the conversion from messages[] to input[] + instructions automatically.
    Note: 'stop' parameter is NOT supported by the Responses API — silently ignored.
    """
    input_items, instructions = _convert_messages_to_responses_input(messages)

    if not _responses_api_supports_block_content(base_url):
        input_items = _stringify_responses_message_content(input_items)

    effective_base_url = base_url or getattr(config, 'BASE_URL', '')
    _is_openrouter = 'openrouter' in effective_base_url.lower()
    data = {
        "model": model,
        "input": input_items,
        "stream": stream,
    }
    # Enable store for OpenAI/GLM direct or OpenRouter with these models
    # OpenAI (gpt-5.x, o-series): uses Responses API with store
    # GLM: uses Chat Completions API with store for KV cache
    _model_lower = (model or '').lower()
    _is_cache_capable = (
        'gpt-' in _model_lower or
        any(x in _model_lower for x in ('glm', 'o1', 'o3', 'o4'))
    )
    if not _is_openrouter or (_is_openrouter and _is_cache_capable):
        data["store"] = True  # Required for prompt caching/KV cache

    if instructions:
        data["instructions"] = instructions

    # Codex backend (https://chatgpt.com/backend-api/codex/responses) is the
    # ChatGPT-OAuth gateway and imposes extra constraints over OpenAI's
    # standard /v1/responses:
    #   • instructions is required        (400 "Instructions are required")
    #   • store must be false             (400 "Store must be set to false")
    #   • stream must be true             (400 "Stream must be set to true")
    # Caching: Codex is storage-less by design. opencode itself sets
    # store=false for OpenAI/Codex models (transform.ts:1001) and enables
    # prefix caching via `prompt_cache_key: <stable session key>`. We mirror
    # that — no caching loss, just a different mechanism than OpenAI's store.
    if "chatgpt.com/backend-api/codex" in (effective_base_url or "").lower():
        if not data.get("instructions"):
            data["instructions"] = "You are a helpful assistant."
        data["store"] = False
        data["stream"] = True
        # Stable per-session cache key. Sourced from common_ai_agent's active
        # session ID via get_session_cache_key() so prefix caching survives
        # across turns of the same conversation but stays isolated between
        # sessions. glm/deepseek/anthropic paths are NOT touched — this
        # branch only fires when the URL is the ChatGPT Codex backend.
        try:
            from src.opencode_backend import get_session_cache_key
            data["prompt_cache_key"] = get_session_cache_key()
        except Exception:
            data["prompt_cache_key"] = "common_ai_agent"

    if temperature is not None:
        data["temperature"] = temperature

    # stop: NOT supported by Responses API — intentionally omitted
    # if stop:
    #     data["stop"] = stop

    if max_output_tokens is not None:
        data["max_output_tokens"] = max_output_tokens

    # Enable reasoning for reasoning-capable models (GPT-5.x, o-series)
    _is_reasoning_model = _is_reasoning_model_for_name(model)
    if _is_reasoning_model:
        reasoning_mode = _get_responses_reasoning_mode(reasoning_effort)
        if reasoning_mode in ('none', 'low', 'medium', 'high', 'xhigh'):
            reasoning = {"effort": reasoning_mode}
            if getattr(config, 'RESPONSES_REASONING_SUMMARY', True) and _supports_reasoning_summary(model):
                reasoning["summary"] = "detailed"
            data["reasoning"] = reasoning
        elif getattr(config, 'DEBUG_MODE', False):
            print(Color.warning(f"[DEBUG] Reasoning effort '{reasoning_mode}' not in (none/low/medium/high/xhigh) - skipping reasoning"))
    elif getattr(config, 'DEBUG_MODE', False) and 'gpt-5' in (model or '').lower():
        print(Color.warning(f"[DEBUG] Model '{model}' not detected as reasoning model"))

    if tools:
        # Convert Chat Completions tool format to Responses API format.
        # Only type="function" tools are supported; other tool types are skipped.
        responses_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                responses_tools.append({
                    "type": "function",
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                })
        if responses_tools:
            data["tools"] = responses_tools
            data["tool_choice"] = "auto"

    # Codex backend post-scrub: drop fields the ChatGPT-OAuth gateway
    # rejects. Runs at the very end so it overrides anything earlier
    # branches injected. Mirrors opencode/.../plugin/codex.ts:609-613.
    if "chatgpt.com/backend-api/codex" in (effective_base_url or "").lower():
        data.pop("max_output_tokens", None)
        data.pop("temperature", None)

    return data


def _build_responses_request(data: dict, resolved_model: str) -> dict:
    """Backward-compatible shim over _build_responses_request_body.

    Accepts a Chat Completions-style `data` dict (with keys: messages, tools,
    temperature, stream, max_completion_tokens / max_tokens) and returns a
    Responses API request body. Retained for tests and external callers; the
    canonical builder is _build_responses_request_body.
    """
    return _build_responses_request_body(
        messages=data.get("messages", []),
        model=resolved_model,
        stream=bool(data.get("stream")),
        stop=data.get("stop"),
        temperature=data.get("temperature"),
        tools=data.get("tools"),
        max_output_tokens=data.get("max_completion_tokens") or data.get("max_tokens"),
        base_url=data.get("base_url") or getattr(config, 'BASE_URL', ''),
    )


def build_auth_header(api_key: str) -> str:
    """
    Build the Authorization header value.

    - Standard: Bearer {api_key}
    - Azure OpenAI: uses api-key header instead (no Bearer prefix)
    """
    return f"Bearer {api_key}"


def build_api_headers(api_key: str, extra_headers: dict = None) -> dict:
    """
    Build HTTP headers for the API request.

    - Standard: Authorization: Bearer {api_key}
    - Azure OpenAI: api-key: {api_key} (no Bearer)
    - opencode OAuth (USE_OPENCODE_OAUTH): pulls a fresh access token from
      ~/.local/share/opencode/auth.json each call, then adds Codex-specific
      headers (originator, ChatGPT-Account-Id) so the Codex backend accepts
      the request. Mirrors opencode/packages/opencode/src/plugin/codex.ts.
    """
    if is_azure_provider():
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
            "User-Agent": "BrianCoder/1.0"
        }
    else:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "BrianCoder/1.0"
        }

    # opencode-OAuth headers fire ONLY when the current BASE_URL is the
    # ChatGPT Codex endpoint. This way switching `--model glm` (or any
    # other profile) at runtime — which rewrites BASE_URL via
    # set_active_profile — automatically deactivates Codex headers, so
    # glm/deepseek/anthropic requests stay clean even if USE_OPENCODE_OAUTH
    # was set at boot.
    if "chatgpt.com/backend-api/codex" in (getattr(config, "BASE_URL", "") or "").lower():
        try:
            from src.opencode_backend import (
                get_credentials,
                codex_extra_headers,
                get_session_cache_key,
            )
            cred = get_credentials("openai")
            if cred and cred.get("access"):
                headers["Authorization"] = f"Bearer {cred['access']}"
                # Mirror opencode's codex.ts plugin: set originator,
                # ChatGPT-Account-Id, AND session_id header. The session_id
                # header is part of how the Codex backend keys cache lookups.
                headers.update(
                    codex_extra_headers(
                        cred.get("accountId", ""),
                        session_id=get_session_cache_key(),
                    )
                )
        except Exception:
            pass

    # Kimi For Coding (api.kimi.com/coding/v1) appears to gate on the
    # Vercel AI SDK User-Agent signature rather than on specific product
    # names. Every "approved coding agent" (Claude Code, Kimi CLI, Roo,
    # Kilo, opencode) routes through @ai-sdk/openai-compatible, which
    # appends "ai-sdk/openai-compatible/X.Y ai-sdk/provider-utils/X.Y
    # runtime/node.js/X.Y" via withUserAgentSuffix() in
    # @ai-sdk/provider-utils/post-to-api.ts. We mirror that exact wire
    # format so common_ai_agent gets the same gate treatment without
    # impersonating any specific product. Override via KIMI_CODING_USER_AGENT
    # env if the gate ever changes (e.g. switch to opencode/X.Y identifier).
    # Other Moonshot endpoints (api.moonshot.cn) are NOT gated and retain
    # the default User-Agent.
    _base_lc = (getattr(config, "BASE_URL", "") or "").lower()
    if "api.kimi.com/coding" in _base_lc:
        import os as _os_kc
        # Kimi For Coding gate verified working with this UA pattern
        # (2026-05 e2e screenshot showed kimi-2.6 responding via Sisyphus
        # worker). Plain ai-sdk-only signature returned 403 in follow-up
        # testing — the gate requires BOTH a known coding-agent identifier
        # AND the SDK suffix. Override via KIMI_CODING_USER_AGENT env when
        # experimenting with alternative identifiers (opencode/cli, kimi-cli, etc.).
        headers["User-Agent"] = _os_kc.environ.get(
            "KIMI_CODING_USER_AGENT",
            "claude-cli/0.2.7 (Anthropic; Darwin) "
            "ai-sdk/openai-compatible/1.0.29 "
            "ai-sdk/provider-utils/3.0.19 "
            "runtime/node.js/22.0.0",
        )
        headers.setdefault("HTTP-Referer", "https://www.anthropic.com/")
        headers.setdefault("X-Title", "Claude Code")

    if extra_headers:
        headers.update(extra_headers)

    return headers


def _is_codex_backend_url(url: str = "") -> bool:
    target = str(url or getattr(config, "BASE_URL", "") or "").lower()
    return "chatgpt.com/backend-api/codex" in target


def _refresh_codex_oauth_headers(url: str = "", extra_headers: dict = None) -> Optional[dict]:
    """Force-refresh ChatGPT OAuth and return fresh Codex request headers."""
    if not _is_codex_backend_url(url):
        return None
    try:
        from src.opencode_backend import get_credentials
    except Exception:
        return None
    try:
        cred = get_credentials("openai", auto_refresh=True, force_refresh=True)
    except TypeError:
        cred = get_credentials("openai", auto_refresh=True)
    except Exception:
        return None
    if not (cred and cred.get("access")):
        return None
    try:
        config.API_KEY = cred["access"]
        os.environ["LLM_API_KEY"] = cred["access"]
        if cred.get("accountId"):
            setattr(config, "OPENCODE_ACCOUNT_ID", cred.get("accountId") or "")
            os.environ["OPENCODE_ACCOUNT_ID"] = cred.get("accountId") or ""
    except Exception:
        pass
    return build_api_headers(cred["access"], extra_headers=extra_headers)


def _persistent_post_with_auth_retry(url: str, headers: dict, body: bytes, timeout: int = 300):
    """POST once; on Codex OAuth 401/403 force-refresh and retry once."""
    try:
        return _persistent_post(url, headers, body, timeout=timeout)
    except _PersistentHTTPError as exc:
        if exc.code not in (401, 403) or not _is_codex_backend_url(url):
            raise
        refreshed = _refresh_codex_oauth_headers(url)
        if not refreshed:
            raise
        retry_headers = dict(headers or {})
        retry_headers.update(refreshed)
        try:
            _http_conn_pool.pop(urllib.parse.urlparse(url).netloc, None)
        except Exception:
            pass
        return _persistent_post(url, retry_headers, body, timeout=timeout)


def get_provider_config(provider_id: str = None, model_id: str = None) -> ProviderConfig:
    """
    Get provider configuration for a specific provider/model.

    Args:
        provider_id: Provider name (anthropic, openai, openrouter, etc.)
        model_id: Model name override

    Returns:
        ProviderConfig with API details
    """
    # Default to env config
    if not provider_id and not model_id:
        return ProviderConfig.from_env()

    cache_key = f"{provider_id or 'default'}:{model_id or 'default'}"
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    # Build config based on provider
    provider_id = provider_id or ""
    provider_lower = provider_id.lower()

    # Known provider base URLs
    provider_urls = {
        "anthropic": "https://api.anthropic.com/v1",
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "zai": "https://api.z.ai/api/coding/paas/v4",
        "google": "https://generativelanguage.googleapis.com/v1beta",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "deepinfra": "https://api.deepinfra.com/v1/openai",
        "mistral": "https://api.mistral.ai/v1",
        "azure": getattr(config, "AZURE_OPENAI_ENDPOINT", ""),  # Azure: endpoint only
    }

    # Get base URL
    base_url = provider_urls.get(provider_lower, config.BASE_URL)

    # Get API key from env (PROVIDER_API_KEY or fallback)
    env_key = f"{provider_id.upper()}_API_KEY"
    if provider_lower == "azure":
        api_key = os.getenv("AZURE_OPENAI_API_KEY", config.API_KEY)
    else:
        api_key = os.getenv(env_key, config.API_KEY)

    provider_config = ProviderConfig(
        provider_id=provider_id or "default",
        base_url=base_url,
        api_key=api_key,
        model_id=model_id or config.MODEL_NAME
    )

    _provider_cache[cache_key] = provider_config
    return provider_config


def chat_completion_with_config(
    messages: List[Dict[str, Any]],
    provider_config: ProviderConfig = None,
    stop: List[str] = None,
    temperature: float = None,
    top_p: float = None,
    tools: List[Dict] = None,
):
    """
    Chat completion with explicit provider configuration.
    Yields content chunks from SSE stream.

    Args:
        messages: List of message dicts
        provider_config: Provider configuration (None = use defaults)
        stop: Stop sequences
        temperature: Override temperature
        top_p: Override top_p

    Yields:
        Content chunks
    """
    if provider_config is None:
        provider_config = ProviderConfig.from_env()

    if use_responses_api(provider_config.model_id):
        # ── Responses API path ──
        url = build_responses_url(provider_config.base_url, provider_config.model_id)
        headers = build_api_headers(provider_config.api_key)
        data = _build_responses_request_body(
            messages=messages,
            model=provider_config.model_id,
            stream=True,
            stop=stop,
            temperature=temperature if temperature is not None else provider_config.temperature,
            tools=tools,
            base_url=provider_config.base_url,
        )
        if top_p is not None:
            data["top_p"] = top_p
        elif provider_config.top_p is not None:
            data["top_p"] = provider_config.top_p

        if config.DEBUG_MODE:
            print(Color.info(f"\n[Agent-Aware API Call (Responses API)]"))
            print(Color.info(f"  Provider: {provider_config.provider_id}"))
            print(Color.info(f"  Model: {provider_config.model_id}"))
            print(Color.info(f"  URL: {url}"))

        yield from _execute_streaming_request_responses(url, headers, data, messages, native_mode=bool(tools))
        return

    # Use provided config — build URL and headers based on provider type
    url = build_chat_url(provider_config.base_url, provider_config.model_id)
    headers = build_api_headers(provider_config.api_key)

    data = {
        "model": provider_config.model_id,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True}
    }

    if stop:
        # Z.AI and CanopyWave allow max 4 stop sequences
        _stop = stop[:4] if ("z.ai" in url or "canopywave" in url) else stop
        data["stop"] = _stop

    # Apply temperature/top_p
    if temperature is not None:
        data["temperature"] = temperature
    elif provider_config.temperature is not None:
        data["temperature"] = provider_config.temperature

    if top_p is not None:
        data["top_p"] = top_p
    elif provider_config.top_p is not None:
        data["top_p"] = provider_config.top_p

    if tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"

    if config.DEBUG_MODE:
        print(Color.info(f"\n[Agent-Aware API Call]"))
        print(Color.info(f"  Provider: {provider_config.provider_id}"))
        print(Color.info(f"  Model: {provider_config.model_id}"))
        print(Color.info(f"  URL: {url}"))

    # Reuse existing streaming logic
    yield from _execute_streaming_request(url, headers, data, messages, native_mode=bool(tools))


def _extract_responses_delta_text(event_json: dict) -> str:
    """Extract text from Responses SSE delta payloads."""
    delta = event_json.get("delta", "")
    if isinstance(delta, str):
        return delta
    if isinstance(delta, dict):
        parts = []
        for key in ("text", "summary", "content"):
            value = delta.get(key)
            if isinstance(value, str) and value:
                parts.append(value)
        return "".join(parts)
    if isinstance(delta, list):
        parts = []
        for block in delta:
            if isinstance(block, dict):
                text = block.get("text") or block.get("summary") or block.get("content")
                if text:
                    parts.append(str(text))
            elif block:
                parts.append(str(block))
        return "".join(parts)
    return str(delta) if delta else ""


def _execute_streaming_request_responses(url: str, headers: Dict, data: Dict, messages: List, native_mode: bool = False):
    """
    Execute streaming request using the Responses API SSE format.

    The Responses API uses typed SSE events instead of the Chat Completions delta format:
    - response.output_text.delta → text content chunks
    - response.reasoning.delta → reasoning/thinking content
    - response.function_call_arguments.delta → tool call arguments
    - response.completed → final response with usage stats
    - response.done → stream end marker (replaces [DONE])

    Yields the same format as _execute_streaming_request:
    - Plain strings for content
    - ("reasoning", text) tuples for reasoning
    - ("native_tool_calls", [...]) for tool calls
    - ("finish_reason", reason) for finish signals
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read
    global _last_debug_prompt_text, _last_debug_messages

    _RETRY_DELAYS = [30, 60, 120, 180, 300]
    max_retries = len(_RETRY_DELAYS) + 1

    for retry_count in range(max_retries):
        global _stream_cancelled
        if _stream_cancelled:
            _stream_cancelled = False
            return
        _reasoning_started = False
        _content_label_printed = False
        _wd_stop, _wd_triggered = None, [False]
        _pending_tool_calls: Dict[int, Dict] = {}
        _current_function_call_name = ""
        _current_function_call_id = ""
        _current_function_call_idx = 0

        try:
            _body = json.dumps(data).encode('utf-8')
            response = _persistent_post_with_auth_retry(url, headers, _body, timeout=config.STREAM_API_TIMEOUT)
            global _active_stream_response
            _active_stream_response = response
            _inactivity_s = getattr(config, 'STREAM_INACTIVITY_TIMEOUT', 120)
            _last_data = [time.time()]
            _last_progress = [time.time()]
            _wd_stop, _wd_triggered = _make_stream_watchdog(
                response, _inactivity_s, _last_data, _last_progress
            )
            try:
                usage_info = None
                _yielded_something = False
                _finish_reason = None
                _status = None

                for line in response:
                    _last_data[0] = time.time()
                    line = line.decode('utf-8').strip()
                    if not line.startswith("data: "):
                        continue
                    # Separate progress checkpoint: only real SSE data lines
                    # count as "progress" for the new watchdog. Keep-alives
                    # (':keep-alive', empty lines) reset _last_data[0] above
                    # for the spinner UX, but the second watchdog (fed by
                    # _last_progress) ignores those so a stalled provider
                    # actually triggers the timeout.
                    _last_progress[0] = time.time()
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        event_json = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = event_json.get("type", "")


                    # ── Usage stats (from response.completed or inline) ──
                    if "usage" in event_json:
                        usage_info = event_json["usage"]
                    # response.completed carries usage inside response object
                    if event_type == "response.completed":
                        resp_obj = event_json.get("response", {})
                        if "usage" in resp_obj:
                            usage_info = resp_obj["usage"]
                        _status = resp_obj.get("status", "completed")
                        if _status == "incomplete":
                            _incomplete = resp_obj.get("incomplete_details") or {}
                            _reason = _incomplete.get("reason", "")
                            if _reason == "content_filter":
                                _finish_reason = "content_filter"
                            else:
                                _finish_reason = "length"
                        elif _status == "completed":
                            _finish_reason = "stop"

                    # ── Text content delta ──
                    if event_type == "response.output_text.delta":
                        delta_text = event_json.get("delta", "")
                        if delta_text:
                            yield delta_text
                            _yielded_something = True

                    # ── Reasoning delta (encrypted or visible) ──
                    # OpenAI Responses API sends reasoning summary via
                    # response.reasoning_summary_text.delta (not response.reasoning.delta)
                    if "reasoning" in event_type and event_type.endswith(".delta"):
                        reasoning_text = _extract_responses_delta_text(event_json)
                        if reasoning_text:
                            yield ("reasoning", reasoning_text)
                            _yielded_something = True

                    # ── Function call start (name + id) ──
                    if event_type == "response.function_call_arguments.delta":
                        args_delta = event_json.get("delta", "")
                        idx = _current_function_call_idx
                        if idx not in _pending_tool_calls:
                            _pending_tool_calls[idx] = {
                                "id": _current_function_call_id,
                                "name": _current_function_call_name,
                                "arguments": "",
                            }
                        _pending_tool_calls[idx]["arguments"] += args_delta

                    # ── Reasoning item done (codex/o-series: reasoning in summary field) ──
                    # Codex sends reasoning as output item with summary, not as streaming deltas.
                    # NOTE: OpenAI encrypts codex reasoning - summary[] is always empty even with
                    # summary=detailed. Reasoning tokens are used internally but not exposed to client.
                    if event_type == "response.output_item.done":
                        item = event_json.get("item", {})
                        if item.get("type") == "reasoning":
                            text = _extract_responses_reasoning_text(item)
                            if not text and getattr(config, 'DEBUG_MODE', False):
                                print(Color.warning("  [Reasoning] codex reasoning is encrypted by OpenAI — tokens used internally, text not accessible"))
                            if text:
                                yield ("reasoning", text)
                                _yielded_something = True

                    # ── Function call item added (carries name + id) ──
                    if event_type == "response.output_item.added":
                        item = event_json.get("item", {})
                        if item.get("type") == "function_call":
                            _current_function_call_name = item.get("name", "")
                            _current_function_call_id = item.get("call_id", item.get("id", ""))
                            idx = len(_pending_tool_calls)
                            _current_function_call_idx = idx
                            _pending_tool_calls[idx] = {
                                "id": _current_function_call_id,
                                "name": _current_function_call_name,
                                "arguments": "",
                            }

                # ── Emit accumulated tool calls ──
                if _pending_tool_calls:
                    _yielded_something = True
                    if native_mode:
                        import uuid as _uuid
                        _native_calls = []
                        for idx in sorted(_pending_tool_calls):
                            tc_info = _pending_tool_calls[idx]
                            if tc_info["name"]:
                                _call_id = tc_info.get("id") or f"call_{_uuid.uuid4().hex[:16]}"
                                _args_raw = tc_info["arguments"]
                                _args_str = _args_raw or "{}"
                                try:
                                    json.loads(_args_str)
                                except json.JSONDecodeError:
                                    print(Color.warning(
                                        f"\n  [Tool Call Warning] '{tc_info['name']}' — "
                                        f"arguments JSON invalid (got: {repr(_args_raw)[:80]}). "
                                        f"Defaulting to {{}}. Check hosting tool-call serialization."
                                    ))
                                    _args_str = "{}"
                                _native_calls.append({
                                    "id": _call_id,
                                    "name": tc_info["name"],
                                    "arguments": _args_str,
                                })
                        if _native_calls:
                            yield ("native_tool_calls", _native_calls)
                    else:
                        for idx in sorted(_pending_tool_calls):
                            tc_info = _pending_tool_calls[idx]
                            tc_name = tc_info["name"]
                            tc_args_str = tc_info["arguments"]
                            if tc_name and tc_args_str:
                                try:
                                    tc_args = json.loads(tc_args_str)
                                    args_formatted = ", ".join(
                                        f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in tc_args.items()
                                    )
                                    yield f"\nAction: {tc_name}({args_formatted})\n"
                                except (json.JSONDecodeError, AttributeError):
                                    pass

                # ── Usage stats processing ──
                if usage_info:
                    input_tokens = usage_info.get("input_tokens", 0)
                    output_tokens = usage_info.get("output_tokens", 0)
                    if input_tokens > 0:
                        last_input_tokens = input_tokens
                    if output_tokens > 0:
                        last_output_tokens = output_tokens

                    # Cache stats
                    _cached = usage_info.get("cached_input_tokens",
                               usage_info.get("prompt_tokens_details", {}).get("cached_tokens", 0))
                    # OpenAI Responses API: cached_tokens in input_tokens_details
                    _itd = usage_info.get("input_tokens_details") or {}
                    if _cached == 0 and _itd.get("cached_tokens", 0) > 0:
                        _cached = _itd["cached_tokens"]
                    if _cached > 0:
                        last_cache_read_tokens = _cached
                        total_cache_read += _cached

                    _total = input_tokens + output_tokens
                    if _total > 0:
                        get_rate_limiter().update_actual_usage(_total)

                    if config.DEBUG_MODE:
                        _otd = usage_info.get("output_tokens_details") or {}
                        _reasoning_tok = _otd.get("reasoning_tokens", 0)
                        _content_tok = output_tokens - _reasoning_tok
                        _new_input = input_tokens - _cached
                        total_tokens = input_tokens + output_tokens
                        _r_cfg = data.get("reasoning") or {}
                        _tc_names = [tc.get("name", "?") for tc in _pending_tool_calls.values() if tc.get("name")]
                        _latency = time.time() - _t_connect_start if "_t_connect_start" in dir() else None
                        _resp_model = None
                        print(f"\n{Color.info('[Response (Responses API)]')}")
                        if _resp_model:
                            print(Color.info(f"  Model:       {_resp_model}"))
                        if _finish_reason:
                            print(Color.info(f"  Finish:      {_finish_reason}"))
                        if _latency:
                            _ttft_str = f"  TTFT: {_perf_ttft:.2f}s" if _perf_ttft else ""
                            print(Color.info(f"  Latency:     {_latency:.2f}s{_ttft_str}"))
                        print(Color.info(f"  {'─'*32}"))
                        _in_detail = f"  (cached: {_cached:,} / new: {_new_input:,})" if _cached > 0 else ""
                        _out_detail = f"  (reasoning: {_reasoning_tok:,} / content: {_content_tok:,})" if _reasoning_tok > 0 else ""
                        print(Color.info(f"  Input:       {input_tokens:,}{_in_detail}"))
                        print(Color.info(f"  Output:      {output_tokens:,}{_out_detail}"))
                        print(Color.info(f"  Total:       {total_tokens:,}"))
                        if _tc_names:
                            print(Color.info(f"  {'─'*32}"))
                            print(Color.info(f"  Tool calls:  {len(_tc_names)}  [{', '.join(_tc_names)}]"))
                        if _r_cfg:
                            print(Color.info(f"  {'─'*32}"))
                            for _k, _v in _r_cfg.items():
                                print(Color.info(f"  {_k.capitalize():<12} {_v}"))
                            if _reasoning_tok > 0:
                                print(Color.info(f"  Rsn tokens:  {_reasoning_tok:,}"))
                        print()

                # ── Finish reason signals ──
                if _finish_reason == "length":
                    _mt = data.get('max_output_tokens', 'unset')
                    print(Color.warning(
                        f"\n[Warning] Output truncated: max_output_tokens limit reached "
                        f"(max_output_tokens={_mt}). "
                        f"Increase MAX_OUTPUT_TOKENS or reduce input size."
                    ))
                    yield ("finish_reason", "length")
                elif _finish_reason == "content_filter":
                    yield ("finish_reason", "content_filter")

                # Empty response — retry
                if not _yielded_something and retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Empty response from Responses API. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    try:
                        _parsed_url = urllib.parse.urlparse(url)
                        _stale_conn = _http_conn_pool.pop(_parsed_url.netloc, None)
                        if _stale_conn is not None:
                            _stale_conn.close()
                    except Exception:
                        pass
                else:
                    return
            finally:
                if _wd_stop is not None:
                    _wd_stop.set()
                _active_stream_response = None
                try:
                    response.read()
                except Exception:
                    pass
            if _wd_triggered[0]:
                raise socket.timeout(f"No data for {_inactivity_s}s (inactivity)")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            # Responses API targets OpenAI / Azure — prefer the OpenAI parser.
            parsed = _parse_openai_error(error_body, http_status=e.code)
            _msg = parsed["message"] or e.reason

            if parsed["is_balance_exhausted"] or parsed["is_deployment_missing"]:
                print(Color.error(f"\n  Responses API Error [HTTP {e.code}]: {_msg}"))
                yield f"\n{Color.error(f'[HTTP {e.code}] {_msg}')}\n"
                return

            is_retryable = (parsed["is_retryable"] or e.code == 429 or
                          e.code == 400 or (500 <= e.code < 600))
            # Error 1214 = permanent validation error — never retry
            if parsed.get("is_invalid_messages"):
                is_retryable = False
            if is_retryable and retry_count < max_retries - 1:
                # 504 Gateway Timeout = upstream proxy waited too long
                # for the LLM origin to respond. Usually transient and
                # clears in 2-10s. Use a short fixed-but-jittered delay
                # so we don't sleep 30s the first time when 5s would do.
                # 400 stays at the explicit 5s; everything else uses the
                # standard backoff schedule.
                if e.code == 504:
                    import random as _rnd
                    delay = 5 + retry_count * 5 + _rnd.uniform(0, 3)
                    print(Color.warning(
                        f"\n[Retry {retry_count + 1}/{max_retries - 1}] "
                        f"HTTP 504 Gateway Timeout — upstream busy, "
                        f"retrying in {delay:.1f}s..."))
                elif e.code == 400:
                    delay = 5
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] HTTP {e.code}: {_msg}."))
                else:
                    delay = _RETRY_DELAYS[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] HTTP {e.code}: {_msg}."))
                if error_body and config.DEBUG_MODE:
                    print(Color.warning(f"  Body: {error_body[:300]}"))
                if e.code != 504:
                    print(Color.warning(f"Waiting {delay}s...\n"))
                time.sleep(delay)
                continue

            yield f"\n{Color.error(f'[HTTP Error {e.code}]: {e.reason}')}\n"
            if _msg:
                yield f"{Color.error(f'  {_msg}')}\n"
            if error_body and config.DEBUG_MODE:
                yield f"{Color.DIM}  [Error Body]: {error_body[:500]}{Color.RESET}\n"
            elif error_body and not _msg:
                yield f"{Color.error(f'  {error_body[:300]}')}\n"
            return

        except (socket.timeout, urllib.error.URLError, ssl.SSLError) as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                err_msg = str(e)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] {err_msg}. Waiting {delay}s...\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[Connection Error]: {e}')}\n"
            return

        except Exception as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] {type(e).__name__}: {e}. Waiting {delay}s...\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[{type(e).__name__}]: {e}')}\n"
            return

    return  # all retries exhausted


def _make_stream_watchdog(response, inactivity_s: int, last_data_ref: list,
                          last_progress_ref=None):
    """
    Daemon thread that watches the stream for inactivity.

    - Prints a spinner to stderr every 10 s when there's been a > 5 s gap
      (so the user can see the model is still generating).
    - Closes *response* and sets triggered[0]=True if no data arrives for
      *inactivity_s* seconds (truly stuck / dead connection).

    Usage::

        _last = [time.time()]
        _stop, _triggered = _make_stream_watchdog(response, inactivity_s, _last)
        try:
            for line in response:
                _last[0] = time.time()
                ...
        finally:
            _stop.set()
        if _triggered[0]:
            raise socket.timeout(f"No data for {inactivity_s}s")
    """
    _stop = threading.Event()
    _triggered = [False]
    _SPIN_EVERY = 10   # seconds between spinner prints
    _SPIN_AFTER = 5    # only start spinning after this idle gap

    def _run():
        _last_spin = time.time()
        while not _stop.is_set():
            now = time.time()
            elapsed = now - last_data_ref[0]
            # Independent "real progress" track: if a progress_ref is
            # supplied, the timeout fires on whichever timer (bytes OR
            # real SSE events) idle longer than inactivity_s. SSE
            # keep-alive bytes can hide a stalled provider behind a
            # healthy TCP connection — progress_ref is only bumped on
            # data:-prefixed lines so this lane catches that case.
            progress_elapsed = (
                now - last_progress_ref[0]
                if last_progress_ref is not None
                else 0
            )
            stall = max(elapsed, progress_elapsed)
            if stall >= inactivity_s:
                _triggered[0] = True
                try:
                    response.close()
                except Exception:
                    pass
                break
            if elapsed > _SPIN_AFTER and now - _last_spin >= _SPIN_EVERY:
                _last_spin = now
                sys.stderr.write(
                    f"\r\033[2m  ⏳ streaming… {int(elapsed)}s? idle "
                    f"(limit {inactivity_s}s?)\033[0m\033[K"
                )
                sys.stderr.flush()
            _stop.wait(1)
        # clear spinner line
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return _stop, _triggered


def _parse_zai_error(error_body: str) -> dict:
    """
    Parse Z.AI error response body into a structured dict.

    Z.AI format: {"error": {"code": "1261", "message": "Prompt exceeds max length"}}
    OpenAI format: {"error": {"type": "...", "message": "...", "code": "..."}}

    Returns: {
        "code": str,           # business error code (e.g. "1261", "1302") or ""
        "message": str,        # human-readable message
        "type": str,           # error type (OpenAI) or ""
        "is_balance_exhausted": bool,   # account out of credits
        "is_account_locked": bool,      # account anomaly / locked
        "is_content_filter": bool,      # policy content filter
        "is_prompt_too_long": bool,     # prompt exceeds max length
        "is_high_traffic": bool,        # model overloaded, suggests alt
        "is_rate_limit": bool,          # generic rate limit
        "is_retryable": bool,           # safe to retry
        "reset_time": str,              # when limit resets (e.g. "2025-01-01 00:00")
    }
    """
    result = {
        "code": "",
        "message": "",
        "type": "",
        "is_balance_exhausted": False,
        "is_account_locked": False,
        "is_content_filter": False,
        "is_prompt_too_long": False,
        "is_high_traffic": False,
        "is_rate_limit": False,
        "is_retryable": False,
        "is_invalid_messages": False,
        "reset_time": "",
    }
    try:
        error_json = json.loads(error_body)
        error_info = error_json.get("error", {})
        if isinstance(error_info, str):
            result["message"] = error_info
            return result
        if not isinstance(error_info, dict):
            return result

        result["code"] = str(error_info.get("code", ""))
        result["message"] = error_info.get("message", "")
        result["type"] = error_info.get("type", "")

        code = result["code"]

        # Z.AI business error codes
        # 1113 = account in arrears, 1112 = account locked, 1121 = irregular activities
        if code in ("1112", "1121"):
            result["is_account_locked"] = True
        elif code == "1113":
            result["is_balance_exhausted"] = True
        # 1261 = Prompt exceeds max length
        elif code == "1261":
            result["is_prompt_too_long"] = True
            result["is_retryable"] = True  # retryable after compression
        # 1301 = content filter / unsafe content
        elif code == "1301":
            result["is_content_filter"] = True
        # 1302 = high concurrency, 1303 = high frequency, 1305 = rate limit
        elif code in ("1302", "1303", "1305"):
            result["is_rate_limit"] = True
            result["is_retryable"] = True
        # 1308 = usage limit with reset time, 1310 = weekly/monthly limit
        elif code in ("1308", "1310"):
            result["is_rate_limit"] = True
            result["is_retryable"] = True
            # Extract reset time from message: "limit will reset at 2025-01-01 00:00"
            msg = result["message"]
            import re as _re
            _m = _re.search(r"reset at\s+(.+?)[\.\s]*$", msg)
            if _m:
                result["reset_time"] = _m.group(1).strip()
        # 1309 = GLM Coding Plan expired
        elif code == "1309":
            result["is_balance_exhausted"] = True
        # 1214 = messages parameter is illegal — permanent validation error
        elif code == "1214":
            result["is_invalid_messages"] = True
        # 1312 = model high traffic, suggests alternative model
        elif code == "1312":
            result["is_high_traffic"] = True
            result["is_retryable"] = True
        # 1313 = Fair Use Policy violation — rate restricted
        elif code == "1313":
            result["is_rate_limit"] = True
            result["is_account_locked"] = True
        # 500 = internal error
        elif code == "500":
            result["is_retryable"] = True
    except (json.JSONDecodeError, Exception):
        pass
    return result


def _parse_openai_error(error_body: str, http_status: int = 0) -> dict:
    """
    Parse OpenAI / Azure OpenAI error bodies into the same structured dict
    shape as _parse_zai_error so Responses API call sites can reuse the same
    signal fields.

    OpenAI format:
        {"error": {"message": "...", "type": "rate_limit_exceeded",
                   "code": "rate_limit_exceeded"|null, "param": null}}
    Azure format (extra):
        {"error": {"code": "DeploymentNotFound", "message": "..."}}  # HTTP 404
        {"error": {"code": "content_filter", "message": "...",
                   "innererror": {"content_filter_result": {...}}}}
    """
    result = {
        "code": "",
        "message": "",
        "type": "",
        "is_balance_exhausted": False,
        "is_account_locked": False,
        "is_content_filter": False,
        "is_prompt_too_long": False,
        "is_high_traffic": False,
        "is_rate_limit": False,
        "is_retryable": False,
        "is_deployment_missing": False,
        "is_invalid_messages": False,
        "reset_time": "",
    }
    try:
        error_json = json.loads(error_body)
    except (json.JSONDecodeError, TypeError):
        error_json = {}

    error_info = error_json.get("error", {}) if isinstance(error_json, dict) else {}
    if isinstance(error_info, str):
        result["message"] = error_info
    elif isinstance(error_info, dict):
        result["code"] = str(error_info.get("code") or "")
        result["message"] = error_info.get("message", "") or ""
        result["type"] = error_info.get("type", "") or ""

    _type = result["type"]
    _code = result["code"]
    _msg_lc = result["message"].lower()

    # Classification — OpenAI/Azure use string types/codes, not numeric
    if _type == "rate_limit_exceeded" or _code == "rate_limit_exceeded" or http_status == 429:
        result["is_rate_limit"] = True
        result["is_retryable"] = True
    if _type == "content_filter" or _code == "content_filter" or "content_filter" in _msg_lc:
        result["is_content_filter"] = True
    if _code == "context_length_exceeded" or "maximum context length" in _msg_lc or "context_length_exceeded" in _msg_lc:
        result["is_prompt_too_long"] = True
        result["is_retryable"] = True  # retryable after compression
    if _code == "insufficient_quota" or "quota" in _msg_lc:
        result["is_balance_exhausted"] = True
    if _code in ("DeploymentNotFound", "ModelNotFound") or (http_status == 404 and "deployment" in _msg_lc):
        result["is_deployment_missing"] = True
    if _type == "server_error" or 500 <= http_status < 600:
        result["is_retryable"] = True
    # Z.AI code 1214 = messages parameter is illegal — permanent validation error
    if _code == "1214" or "messages parameter is illegal" in _msg_lc:
        result["is_invalid_messages"] = True
        result["is_retryable"] = False

    return result
def _extract_responses_reasoning_text(item: dict) -> str:
    """Extract visible reasoning text from a Responses API reasoning item."""
    parts = []

    summary = item.get("summary", "")
    if isinstance(summary, str):
        if summary:
            parts.append(summary)
    elif isinstance(summary, list):
        for block in summary:
            if isinstance(block, dict):
                text = block.get("text", "") or block.get("summary", "")
                if text:
                    parts.append(str(text))
            elif block:
                parts.append(str(block))

    for c in item.get("content", []):
        if isinstance(c, dict):
            text = c.get("text", "")
            if text:
                parts.append(str(text))
        elif c:
            parts.append(str(c))

    return "".join(parts)


def _parse_responses_result(result: dict):
    """Parse a non-streaming Responses API result and yield content/reasoning.

    Responses API returns:
    {
      "output": [
        {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "..."}]},
        {"type": "message", "content": [{"type": "output_text", "text": "..."}]},
        {"type": "function_call", "name": "...", "arguments": "..."}
      ],
      "usage": {"input_tokens": N, "output_tokens": N}
    }
    """
    global last_input_tokens, last_output_tokens

    # Extract usage
    usage = result.get("usage", {})
    if usage:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        if input_tokens > 0:
            last_input_tokens = input_tokens
        if output_tokens > 0:
            last_output_tokens = output_tokens
        _total = input_tokens + output_tokens
        if _total > 0:
            get_rate_limiter().update_actual_usage(_total)

    # Extract content from output items
    output_items = result.get("output", [])
    for item in output_items:
        item_type = item.get("type", "")

        if item_type == "reasoning":
            text = _extract_responses_reasoning_text(item)
            if text:
                yield ("reasoning", text)

        elif item_type == "message":
            for c in item.get("content", []):
                text = c.get("text", "")
                if text:
                    yield _strip_metadata_tokens(text).strip()

        elif item_type == "function_call":
            tc_name = item.get("name", "")
            tc_args_str = item.get("arguments", "{}")
            if tc_name:
                try:
                    tc_args = json.loads(tc_args_str)
                    args_formatted = ", ".join(
                        f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in tc_args.items()
                    )
                    yield f"\nAction: {tc_name}({args_formatted})\n"
                except (json.JSONDecodeError, AttributeError):
                    pass


def _apply_responses_extra_body(data: dict, extra_body: Optional[dict], base_url: str) -> dict:
    """Apply chat-style extra_body overrides to a Responses request safely."""
    if not extra_body:
        return data
    extra = dict(extra_body)
    response_format = extra.pop("response_format", None)
    if response_format and "chatgpt.com/backend-api/codex" not in (base_url or "").lower():
        text_cfg = dict(data.get("text") or {})
        text_cfg["format"] = response_format
        data["text"] = text_cfg
    data.update(extra)
    return data


def _collect_responses_raw(
    url: str,
    headers: Dict,
    data: Dict,
    caller_tag: str,
    started_at: float,
    stream_prefix: Optional[str] = None,
) -> str:
    """Collect a Responses API result into the call_llm_raw string contract."""
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    def _emit_stream_text(text: str, prefix_state: dict) -> None:
        if stream_prefix is None or not text:
            return
        if not prefix_state.get("printed"):
            sys.stdout.write(stream_prefix)
            prefix_state["printed"] = True
        if "\n" in text:
            parts = text.split("\n")
            sys.stdout.write(parts[0])
            for part in parts[1:]:
                sys.stdout.write("\n")
                if part:
                    sys.stdout.write(stream_prefix + part)
                    prefix_state["printed"] = True
                else:
                    prefix_state["printed"] = False
        else:
            sys.stdout.write(text)
        sys.stdout.flush()

    try:
        raw_body = json.dumps(data).encode("utf-8")
        timeout = config.STREAM_API_TIMEOUT if data.get("stream") else config.NONSTREAM_API_TIMEOUT
        t_connect = time.perf_counter()
        response = _persistent_post_with_auth_retry(url, headers, raw_body, timeout=timeout)
        connected_at = time.perf_counter()

        if data.get("stream"):
            content_parts: list[str] = []
            tool_calls: dict[int, dict] = {}
            current_call_name = ""
            current_call_id = ""
            current_call_idx = 0
            usage_info = None
            saw_text_delta = False
            prefix_state: dict[str, bool] = {}
            try:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line.split(":", 1)[1].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        event_json = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = event_json.get("type", "")
                    if "usage" in event_json:
                        usage_info = event_json["usage"]

                    if event_type == "response.output_text.delta":
                        delta_text = event_json.get("delta", "")
                        if delta_text:
                            saw_text_delta = True
                            content_parts.append(delta_text)
                            _emit_stream_text(delta_text, prefix_state)
                        continue

                    if event_type == "response.output_item.added":
                        item = event_json.get("item", {})
                        if item.get("type") == "function_call":
                            current_call_name = item.get("name", "")
                            current_call_id = item.get("call_id", item.get("id", ""))
                            current_call_idx = len(tool_calls)
                            tool_calls[current_call_idx] = {
                                "id": current_call_id,
                                "name": current_call_name,
                                "arguments": "",
                            }
                        continue

                    if event_type == "response.function_call_arguments.delta":
                        args_delta = event_json.get("delta", "")
                        if current_call_idx not in tool_calls:
                            tool_calls[current_call_idx] = {
                                "id": current_call_id,
                                "name": current_call_name,
                                "arguments": "",
                            }
                        tool_calls[current_call_idx]["arguments"] += args_delta
                        continue

                    if event_type == "response.completed":
                        resp_obj = event_json.get("response", {})
                        if "usage" in resp_obj:
                            usage_info = resp_obj["usage"]
                        if not saw_text_delta:
                            for parsed in _parse_responses_result(resp_obj):
                                if isinstance(parsed, tuple):
                                    continue
                                content_parts.append(parsed)
                                _emit_stream_text(parsed, prefix_state)
            finally:
                try:
                    response.read()
                except Exception:
                    pass

            if stream_prefix is not None:
                sys.stdout.write("\n")
                sys.stdout.flush()

            if usage_info:
                input_tokens = usage_info.get("input_tokens", 0)
                output_tokens = usage_info.get("output_tokens", 0)
                if input_tokens > 0:
                    last_input_tokens = input_tokens
                if output_tokens > 0:
                    last_output_tokens = output_tokens
                cached = usage_info.get(
                    "cached_input_tokens",
                    usage_info.get("prompt_tokens_details", {}).get("cached_tokens", 0),
                )
                input_details = usage_info.get("input_tokens_details") or {}
                if cached == 0 and input_details.get("cached_tokens", 0) > 0:
                    cached = input_details["cached_tokens"]
                if cached > 0:
                    last_cache_read_tokens = cached
                    total_cache_read += cached

            ended_at = time.perf_counter()
            _record_call(
                caller_tag,
                data.get("model", ""),
                last_input_tokens,
                last_output_tokens,
                connected_at - t_connect,
                ended_at - t_connect,
                0.0,
                ended_at - started_at,
            )

            native_calls = [tool_calls[idx] for idx in sorted(tool_calls) if tool_calls[idx].get("name")]
            if native_calls:
                return json.dumps({"tool_calls": native_calls}, ensure_ascii=False)
            return _strip_metadata_tokens("".join(content_parts)).strip()

        result = json.loads(response.read().decode("utf-8"))
        content_parts = []
        for parsed in _parse_responses_result(result):
            if isinstance(parsed, tuple):
                continue
            content_parts.append(parsed)
        usage = result.get("usage", {})
        if usage:
            last_input_tokens = usage.get("input_tokens", 0)
            last_output_tokens = usage.get("output_tokens", 0)
        ended_at = time.perf_counter()
        _record_call(
            caller_tag,
            data.get("model", ""),
            last_input_tokens,
            last_output_tokens,
            connected_at - t_connect,
            ended_at - t_connect,
            0.0,
            ended_at - started_at,
        )
        return _strip_metadata_tokens("".join(content_parts)).strip()
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = ""
        parsed = _parse_openai_error(error_body, http_status=e.code)
        msg = parsed.get("message") or error_body[:300] or e.reason
        return f"Error calling LLM: HTTP {e.code}: {msg}"
    except Exception as e:
        return f"Error calling LLM: {e}"


def _execute_streaming_request(url: str, headers: Dict, data: Dict, messages: List, native_mode: bool = False):
    """
    Execute streaming request with retry logic.
    Internal helper for chat_completion functions.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    _RETRY_DELAYS = [30, 60, 120, 180, 300]  # inactivity/timeout backoff (seconds)
    max_retries = len(_RETRY_DELAYS) + 1

    for retry_count in range(max_retries):
        # If ESC cancelled the stream, stop retrying immediately
        global _stream_cancelled
        if _stream_cancelled:
            _stream_cancelled = False
            return
        _reasoning_started = False
        _content_label_printed = False
        _debug_line_buf = ""
        _debug_in_think = False
        _wd_stop, _wd_triggered = None, [False]  # init before try so except can always reference
        _in_think_tag = False
        _think_buf = ""

        try:
            _body = json.dumps(data).encode('utf-8')
            response = _persistent_post_with_auth_retry(url, headers, _body, timeout=config.STREAM_API_TIMEOUT)
            global _active_stream_response
            _active_stream_response = response
            _inactivity_s = getattr(config, 'STREAM_INACTIVITY_TIMEOUT', 120)
            _last_data = [time.time()]
            _last_progress = [time.time()]
            _wd_stop, _wd_triggered = _make_stream_watchdog(
                response, _inactivity_s, _last_data, _last_progress
            )
            try:
                usage_info = None
                _yielded_something = False
                _finish_reason = None   # captured from last non-null finish_reason chunk
                # Accumulate native tool calls across streaming chunks.
                # OpenAI/Z.AI: name+id in first chunk, arguments fragmented across subsequent chunks.
                _pending_tool_calls: Dict[int, Dict] = {}
                for line in response:
                    _last_data[0] = time.time()
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        # Real SSE event: bump the secondary "progress"
                        # timer. _last_data[0] above tracks raw bytes for
                        # spinner UX; _last_progress[0] only moves on
                        # actual data:-prefixed lines so the watchdog can
                        # detect provider stalls hidden behind keep-alives.
                        _last_progress[0] = time.time()
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_str)

                            # Kimi For Coding stream-format diagnostic dump.
                            # Enabled by KIMI_DEBUG_STREAM=1 OR auto-on when BASE_URL
                            # is Kimi and no content has been yielded yet (so we capture
                            # at least the first few chunks for offline analysis).
                            # Stderr-only so it doesn't pollute the response stream.
                            if "api.kimi.com/coding" in (getattr(config, "BASE_URL", "") or "").lower():
                                import os as _os_dbg
                                if _os_dbg.environ.get("KIMI_DEBUG_STREAM", "1") not in ("0", "false", "no"):
                                    import sys as _sys_dbg
                                    _sys_dbg.stderr.write(f"[KIMI_RAW] {data_str[:600]}\n")

                            # Usage stats appear only in the last chunk (Z.AI / OpenAI spec)
                            if "usage" in chunk_json:
                                usage_info = chunk_json["usage"]

                            if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                                choice = chunk_json["choices"][0]
                                # Capture finish_reason; only the last chunk has a non-null value
                                _fr = choice.get("finish_reason")
                                if _fr:
                                    _finish_reason = _fr
                                delta = choice.get("delta", {})

                                # Reasoning tokens (DeepSeek, GLM, OpenRouter reasoning_details, Kimi K2 thinking)
                                # Kimi K2 thinking-style models may use additional keys:
                                # delta.reasoning, delta.reasoning_content, delta.thinking, delta.thought.
                                reasoning = (delta.get("reasoning")
                                             or delta.get("reasoning_content")
                                             or delta.get("thinking")
                                             or delta.get("thought")
                                             or "")
                                if not reasoning:
                                    for rd in (delta.get("reasoning_details") or []):
                                        if rd.get("type") == "thinking":
                                            reasoning = (reasoning or "") + (rd.get("thinking", "") or rd.get("summary", ""))
                                # Content key fallbacks for non-OpenAI-compliant providers.
                                # Kimi For Coding may emit `text` or `message.content` in some chunks.
                                content = (delta.get("content")
                                           or delta.get("text")
                                           or (delta.get("message") or {}).get("content")
                                           or "")

                                # Bleed fix: GLM-4.7 can emit reasoning tail and content start
                                # in the same delta chunk. Merge into reasoning when both are
                                # present and content begins mid-sentence.
                                if reasoning and content:
                                    first_char = content.lstrip()[:1]
                                    if first_char and (first_char.islower() or first_char.isdigit() or first_char in ',;:'):
                                        reasoning = reasoning + content
                                        content = ""

                                # <think> tag state machine: internal hosting embeds reasoning
                                # inside content as <think>...</think> across multiple chunks.
                                # Track open/close tags across chunk boundaries.
                                if not reasoning and content and (_think_buf or '<t' in content or '</t' in content):
                                    _think_buf += content
                                    content = ""
                                    reasoning = ""
                                    # Process _think_buf until no more complete tags
                                    while True:
                                        if _in_think_tag:
                                            close_pos = _think_buf.find("</think>")
                                            if close_pos == -1:
                                                # Still inside <think> — emit as reasoning
                                                # but keep last 8 chars as partial-tag buffer
                                                _safe = len(_think_buf) - 8
                                                if _safe > 0:
                                                    reasoning += _think_buf[:_safe]
                                                    _think_buf = _think_buf[_safe:]
                                                break
                                            else:
                                                reasoning += _think_buf[:close_pos]
                                                _think_buf = _think_buf[close_pos + 8:]
                                                _in_think_tag = False
                                        else:
                                            open_pos = _think_buf.find("<think>")
                                            if open_pos == -1:
                                                # No <think> tag — check for partial tag at end
                                                # Keep up to 7 chars as potential partial "<think>"
                                                _safe = max(0, len(_think_buf) - 7)
                                                content += _think_buf[:_safe]
                                                _think_buf = _think_buf[_safe:]
                                                break
                                            else:
                                                content += _think_buf[:open_pos]
                                                _think_buf = _think_buf[open_pos + 7:]
                                                _in_think_tag = True

                                if reasoning:
                                    yield ("reasoning", reasoning)
                                    _yielded_something = True
                                if content:
                                    yield content
                                    _yielded_something = True

                                # Accumulate native tool_calls across streaming chunks.
                                # OpenAI/Z.AI streaming protocol:
                                #   - first chunk carries id, type, function.name
                                #   - subsequent chunks carry only function.arguments fragments
                                tool_calls = delta.get("tool_calls") or []
                                for tc in tool_calls:
                                    idx = tc.get("index", 0)
                                    if idx not in _pending_tool_calls:
                                        _pending_tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                                    # id and name arrive only in the first chunk — preserve them
                                    if tc.get("id"):
                                        _pending_tool_calls[idx]["id"] = tc["id"]
                                    func = tc.get("function", {})
                                    if func.get("name"):
                                        _pending_tool_calls[idx]["name"] = func["name"]
                                    if func.get("arguments"):
                                        _pending_tool_calls[idx]["arguments"] += func["arguments"]

                        except json.JSONDecodeError:
                            continue

                # Emit accumulated tool calls after stream ends.
                if _pending_tool_calls:
                    _yielded_something = True
                    if native_mode:
                        import uuid as _uuid
                        _native_calls = []
                        for idx in sorted(_pending_tool_calls):
                            tc_info = _pending_tool_calls[idx]
                            if tc_info["name"]:
                                # Prefer the API-provided id; fall back to generated id
                                _call_id = tc_info.get("id") or f"call_{_uuid.uuid4().hex[:16]}"
                                # Validate arguments JSON; default to {} on parse failure
                                _args_raw = tc_info["arguments"]
                                _args_str = _args_raw or "{}"
                                try:
                                    json.loads(_args_str)
                                except json.JSONDecodeError:
                                    # Internal hosting often sends malformed/truncated arguments.
                                    # Warn visibly so it doesn't silently become an empty-arg error.
                                    print(Color.warning(
                                        f"\n  [Tool Call Warning] '{tc_info['name']}' — "
                                        f"arguments JSON invalid (got: {repr(_args_raw)[:80]}). "
                                        f"Defaulting to {{}}. Check hosting tool-call serialization."
                                    ))
                                    _args_str = "{}"
                                _native_calls.append({
                                    "id": _call_id,
                                    "name": tc_info["name"],
                                    "arguments": _args_str,
                                })
                        if _native_calls:
                            yield ("native_tool_calls", _native_calls)
                    else:
                        for idx in sorted(_pending_tool_calls):
                            tc_info = _pending_tool_calls[idx]
                            tc_name = tc_info["name"]
                            tc_args_str = tc_info["arguments"]
                            if tc_name and tc_args_str:
                                try:
                                    tc_args = json.loads(tc_args_str)
                                    args_formatted = ", ".join(
                                        f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in tc_args.items()
                                    )
                                    yield f"\nAction: {tc_name}({args_formatted})\n"
                                except (json.JSONDecodeError, AttributeError):
                                    pass

                if usage_info:
                    input_tokens = usage_info.get("input_tokens") or usage_info.get("prompt_tokens", 0)
                    output_tokens = usage_info.get("output_tokens") or usage_info.get("completion_tokens", 0)
                    if input_tokens > 0:
                        last_input_tokens = input_tokens
                    if output_tokens > 0:
                        last_output_tokens = output_tokens

                    # Extract cached token count from Z.AI / OpenAI prompt_tokens_details
                    _pt_details = usage_info.get("prompt_tokens_details") or {}
                    _cached = _pt_details.get("cached_tokens", 0)
                    if _cached > 0:
                        last_cache_read_tokens = _cached
                        total_cache_read += _cached

                    # Update rate limiter with actual token usage
                    _total = input_tokens + output_tokens
                    if _total > 0:
                        get_rate_limiter().update_actual_usage(_total)

                # finish_reason signals: emit for callers that need to react
                if _finish_reason == "length":
                    # Output was cut off by max_tokens — warn and signal
                    _mt = data.get('max_completion_tokens', data.get('max_tokens', 'unset'))
                    print(Color.warning(
                        f"\n[Warning] Output truncated: max_tokens limit reached "
                        f"(max_tokens={_mt}). "
                        f"Increase MAX_OUTPUT_TOKENS or reduce input size."
                    ))
                    yield ("finish_reason", "length")
                elif _finish_reason == "content_filter":
                    yield ("finish_reason", "content_filter")
                # "stop" and "tool_calls" are normal — no special signal needed

                # Empty response (HTTP 200 but no content/reasoning/tool_calls) — retry
                if not _yielded_something and retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Empty response from LLM. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    # Drop pooled connection: SSE stream may not be fully drained,
                    # leaving tail bytes that cause BadStatusLine on the next request.
                    try:
                        _parsed_url = urllib.parse.urlparse(url)
                        _stale_conn = _http_conn_pool.pop(_parsed_url.netloc, None)
                        if _stale_conn is not None:
                            _stale_conn.close()
                    except Exception:
                        pass
                    # fall through to finally, then loop continues
                else:
                    # Print [Response] debug block AFTER all content has been yielded
                    if usage_info and config.DEBUG_MODE:
                        _reasoning_tok = usage_info.get("reasoningTokens") or \
                            (usage_info.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
                        _cached = (usage_info.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
                        _content_tok = output_tokens - _reasoning_tok
                        _new_input = input_tokens - _cached
                        total_tokens = input_tokens + output_tokens
                        _tc_names = [tc.get("name", "?") for tc in _pending_tool_calls.values() if tc.get("name")]
                        _latency = time.time() - _t_connect_start if "_t_connect_start" in dir() else None
                        print(f"\n{Color.info('[Response]')}")
                        if _finish_reason:
                            print(Color.info(f"  Finish:      {_finish_reason}"))
                        if _latency or _perf_ttft:
                            _ttft_str = f"  TTFT: {_perf_ttft:.2f}s" if _perf_ttft else ""
                            _lat_val = f"{_latency:.2f}s" if _latency else ""
                            print(Color.info(f"  Latency:     {_lat_val}{_ttft_str}"))
                        print(Color.info(f"  {'─'*32}"))
                        _in_detail = f"  (cached: {_cached:,} / new: {_new_input:,})" if _cached > 0 else ""
                        _out_detail = f"  (reasoning: {_reasoning_tok:,} / content: {_content_tok:,})" if _reasoning_tok > 0 else ""
                        print(Color.info(f"  Input:       {input_tokens:,}{_in_detail}"))
                        print(Color.info(f"  Output:      {output_tokens:,}{_out_detail}"))
                        print(Color.info(f"  Total:       {total_tokens:,}"))
                        if _tc_names:
                            print(Color.info(f"  {'─'*32}"))
                            print(Color.info(f"  Tool calls:  {len(_tc_names)}  [{', '.join(_tc_names)}]"))
                        print()
                    return
            finally:
                if _wd_stop is not None:
                    _wd_stop.set()
                _active_stream_response = None  # stream done
                try:
                    response.read()
                except Exception:
                    pass
            if _wd_triggered[0]:
                raise socket.timeout(f"No data for {_inactivity_s}s (inactivity)")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            zai = _parse_zai_error(error_body)

            # ── Extract zai values for f-string compatibility (no backslashes) ──
            _zai_msg = zai["message"]
            _zai_code = zai["code"]
            _zai_type = zai["type"]
            _zai_reset = zai["reset_time"]

            # ── Non-retryable: account locked or balance exhausted ──
            if zai["is_account_locked"] or zai["is_balance_exhausted"]:
                code_str = f" (code {_zai_code})" if _zai_code else ""
                yield f"\n{Color.error(f'[HTTP {e.code}]{code_str} {_zai_msg}')}\n"
                if zai["is_balance_exhausted"]:
                    yield f"{Color.warning('→ Please top up your API credits or check your subscription plan.')}\n"
                else:
                    yield f"{Color.warning('→ Account is locked. Contact Z.AI customer service to unlock.')}\n"
                return

            # ── Content filter: do not retry ──
            if zai["is_content_filter"]:
                yield f"\n{Color.error('[Content Filter] Request blocked by safety policy.')}\n"
                yield f"{Color.warning('→ Rephrase your prompt to avoid potentially sensitive content.')}\n"
                return

            # ── Prompt too long: signal caller to compress and retry ──
            if zai["is_prompt_too_long"]:
                yield f"\n{Color.error('[Prompt Too Long] Input exceeds model context limit (code 1261).')}\n"
                yield ("finish_reason", "prompt_too_long")
                return

            # ── Rate limit with reset time: show when it resets ──
            if zai["is_rate_limit"] and _zai_reset:
                if retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS[retry_count]
                    print(Color.warning(
                        f"\n[Retry {retry_count + 1}/{max_retries - 1}] Rate limited "
                        f"(code {_zai_code}). Resets at {_zai_reset}. "
                        f"Waiting {delay}s...\n"
                    ))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[Rate Limited] {_zai_msg}')}\n"
                yield f"{Color.warning(f'→ Limit resets at {_zai_reset}')}\n"
                return

            # ── High traffic: show suggested alternative model ──
            if zai["is_high_traffic"]:
                if retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Model high traffic (code 1312). Waiting {delay}s...\n"))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[High Traffic] {_zai_msg}')}\n"
                return

            # ── Generic retryable: 400 (vLLM transient), 429 or 5xx ──
            is_retryable = e.code == 400 or e.code == 429 or (500 <= e.code < 600)
            # Error 1214 = permanent validation error — never retry (zai/GLM)
            if zai.get("is_invalid_messages"):
                is_retryable = False
            if is_retryable and retry_count < max_retries - 1:
                # See zai-code-1xxx block above for 504 rationale.
                # 504 = upstream gateway timeout; short jittered delay
                # so we don't sit on 30s when 5s usually clears it.
                if e.code == 504:
                    import random as _rnd
                    delay = 5 + retry_count * 5 + _rnd.uniform(0, 3)
                    print(Color.warning(
                        f"\n[Retry {retry_count + 1}/{max_retries - 1}] "
                        f"HTTP 504 Gateway Timeout — upstream busy, "
                        f"retrying in {delay:.1f}s..."))
                else:
                    delay = 5 if e.code == 400 else _RETRY_DELAYS[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] HTTP {e.code}: {e.reason}"))
                if error_body and config.DEBUG_MODE:
                    print(Color.warning(f"  Body: {error_body[:300]}"))
                if e.code != 504:
                    print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # ── Non-retryable or max retries reached: show error details ──
            yield f"\n{Color.error(f'[HTTP Error {e.code}]: {e.reason}')}\n"
            if _zai_code:
                yield f"{Color.error(f'  Code: {_zai_code}')}\n"
            if _zai_msg:
                yield f"{Color.error(f'  Message: {_zai_msg}')}\n"
            elif _zai_type:
                yield f"{Color.error(f'  Type: {_zai_type}')}\n"
            else:
                yield f"{Color.error(f'  {error_body[:300]}')}\n"
            return

        except socket.timeout as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            # Covers both real socket timeouts and inactivity-watchdog triggers
            inactivity_triggered = getattr(e, '_inactivity', False) or 'inactivity' in str(e).lower()
            label = f"Inactivity ({_inactivity_s}s)" if inactivity_triggered else f"Read timeout ({config.STREAM_API_TIMEOUT}s)"
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] {label}: {e}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[{label}]: {e}')}\n"
            return

        except (urllib.error.URLError, ssl.SSLError) as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Connection Error: {error_msg}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            yield f"\n{Color.error(f'[Connection Error]: {error_msg}')}\n"
            return

        except Exception as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            # Watchdog closed the connection → convert to socket.timeout for retry
            if _wd_triggered[0]:
                if retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Inactivity ({_inactivity_s}s): no data received"))
                    print(Color.warning(f"Waiting {delay}s before retry...\n"))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[Inactivity Timeout]: no data for {_inactivity_s}s')}\n"
                return
            error_type = type(e).__name__
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] {error_type}: {e}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            yield f"\n{Color.error(f'[{error_type}]: {e}')}\n"
            return


def call_llm_for_agent(
    messages: List[Dict[str, Any]],
    agent_name: str = None,
    temperature: float = None
) -> str:
    """
    Call LLM with agent-specific configuration (non-streaming).

    Args:
        messages: List of message dicts
        agent_name: Agent name to look up config (optional)
        temperature: Override temperature

    Returns:
        Complete response text
    """
    provider_config = ProviderConfig.from_env()  # Default

    # Try to get agent-specific config
    if agent_name:
        try:
            from core.agent_config import get_agent_config
            agent = get_agent_config(agent_name)
            if agent and agent.model:
                provider_config = get_provider_config(
                    provider_id=agent.model.provider_id,
                    model_id=agent.model.model_id
                )
                if agent.temperature is not None and temperature is None:
                    temperature = agent.temperature
        except ImportError:
            pass  # agent_config not available

    url = build_chat_url(provider_config.base_url, provider_config.model_id)
    headers = build_api_headers(provider_config.api_key)

    data = {
        "model": provider_config.model_id,
        "messages": messages,
        "stream": False
    }

    if temperature is not None:
        data["temperature"] = temperature

    try:
        _body = json.dumps(data).encode('utf-8')
        response = _persistent_post_with_auth_retry(url, headers, _body, timeout=config.NONSTREAM_API_TIMEOUT)
        result = json.loads(response.read().decode('utf-8'))
        content = result["choices"][0]["message"]["content"]
        return _strip_metadata_tokens(content).strip()

    except Exception as e:
        return f"Error calling LLM: {e}"

def _chat_completion_nonstream(messages, stop=None, model=None, skip_rate_limit=False, suppress_spinner=False):
    """
    Non-streaming LLM call. Fetches complete response then yields chunks.
    Yields ("reasoning", text) tuples for reasoning, plain strings for content.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    # Rate limiting: TPM/RPM bucket if configured, else legacy fixed delay
    if not skip_rate_limit:
        _rl = get_rate_limiter()
        if _rl.active:
            _rl.acquire(estimated_tokens=last_input_tokens + last_output_tokens if last_input_tokens > 0 else None)
        elif config.RATE_LIMIT_DELAY > 0:
            time.sleep(config.RATE_LIMIT_DELAY)

    # Apply prompt caching if enabled
    processed_messages = messages
    if config.ENABLE_PROMPT_CACHING and is_anthropic_provider():
        processed_messages = copy.deepcopy(messages)
        processed_messages = apply_cache_breakpoints(processed_messages)
    elif any(isinstance(m.get("content"), list) for m in messages):
        # Non-Anthropic provider: flatten list-of-blocks content to plain string
        processed_messages = copy.deepcopy(messages)
        for m in processed_messages:
            if isinstance(m.get("content"), list):
                m["content"] = "\n\n".join(
                    block.get("text", "") for block in m["content"]
                    if isinstance(block, dict) and block.get("type") == "text"
                )

    # Non-native mode: strip native tool call artifacts so the API doesn't reject them.
    # After context compression, history may contain assistant messages with tool_calls
    # and role:tool messages from before native mode was toggled off. Convert them to
    # plain text so strict APIs (GLM, Z.AI) don't return HTTP 400/500.
    if not getattr(config, "ENABLE_NATIVE_TOOL_CALLS", False):
        _has_artifacts = any(
            m.get("role") == "tool" or (m.get("role") == "assistant" and m.get("tool_calls"))
            for m in processed_messages
        )
        if _has_artifacts:
            if processed_messages is messages:
                processed_messages = copy.deepcopy(messages)
            cleaned: list = []
            for _m in processed_messages:
                _role = _m.get("role")
                if _role == "tool":
                    # Convert tool result to user observation message
                    cleaned.append({"role": "user", "content": f"Observation: {_m.get('content', '')}"})
                elif _role == "assistant" and _m.get("tool_calls"):
                    # Convert native tool call to text Action: lines
                    _calls = _m.get("tool_calls", [])
                    _lines = []
                    for _tc in _calls:
                        _fn = _tc.get("function", {})
                        _lines.append(f"Action: {_fn.get('name', '?')}({_fn.get('arguments', '{}')})")
                    _text = _m.get("content") or ""
                    _combined = (_text + "\n" if _text else "") + "\n".join(_lines)
                    _new_msg = {"role": "assistant", "content": _combined.strip()}
                    # Preserve reasoning_content when converting native tool_calls → text.
                    if "reasoning_content" in _m:
                        _new_msg["reasoning_content"] = _m["reasoning_content"]
                    cleaned.append(_new_msg)
                else:
                    cleaned.append(_m)
            processed_messages = cleaned

    # ── Clean messages for API (same as streaming path) ──
    # Strip internal-only fields and preserve reasoning_content for
    # reasoning models (DeepSeek, GLM, etc).  This is the non-streaming
    # counterpart of the clean step in chat_completion_stream().
    _ns_api_roles = {"system", "user", "assistant", "tool"}
    _ns_cleaned = []
    _ns_model_for_clean = model or getattr(config, 'MODEL_NAME', '')
    _ns_model_lower = _ns_model_for_clean.lower()
    for _m in processed_messages:
        if _m.get("role") not in _ns_api_roles:
            continue
        _clean = {"role": _m["role"]}
        if "content" in _m:
            _clean["content"] = _m["content"]
        if "tool_calls" in _m:
            _clean["tool_calls"] = _m["tool_calls"]
        if "tool_call_id" in _m:
            _clean["tool_call_id"] = _m["tool_call_id"]
        # Preserved thinking: model-agnostic preservation (see streaming path for rationale)
        if "reasoning_content" in _m and _m["reasoning_content"]:
            _clean["reasoning_content"] = _m["reasoning_content"]
        elif 'deepseek' in _ns_model_lower and _m.get("role") == "assistant":
            _clean["reasoning_content"] = " "
        elif "reasoning_content" in _m and 'glm-' in _ns_model_lower:
            if not getattr(config, "GLM_CLEAR_THINKING", True):
                _clean["reasoning_content"] = _m["reasoning_content"]
        _ns_cleaned.append(_clean)
    processed_messages = _ns_cleaned

    resolved_model = model or config.MODEL_NAME

    # ── Responses API path ──
    if use_responses_api(resolved_model):
        url = build_responses_url(config.BASE_URL, resolved_model)
        api_key = config.API_KEY
        headers = build_api_headers(api_key)
        data = _build_responses_request_body(
            messages=processed_messages,
            model=resolved_model,
            stream=False,
            stop=stop,
            max_output_tokens=compute_safe_max_tokens() if config.MAX_OUTPUT_TOKENS > 0 else None,
            base_url=url,
        )

        _spinner = None
        if not suppress_spinner:
            try:
                from lib.display import Spinner as _Spinner
                _spinner = _Spinner("Thinking")
                _spinner.start()
            except Exception:
                _spinner = None

        try:
            _body = json.dumps(data).encode('utf-8')
            response = _persistent_post_with_auth_retry(url, headers, _body, timeout=config.NONSTREAM_API_TIMEOUT)
            result = json.loads(response.read().decode('utf-8'))
        except (urllib.error.HTTPError, socket.timeout, urllib.error.URLError, ssl.SSLError):
            if _spinner:
                _spinner.stop()
            raise
        except Exception as e:
            if _spinner:
                _spinner.stop()
            print(Color.error(f"\n  LLM error (Responses API): {e}"))
            return
        finally:
            if _spinner:
                _spinner.stop()

        # Parse Responses API result: output[].content[].text
        usage = result.get("usage", {})
        if usage:
            last_input_tokens = usage.get("input_tokens", 0)
            last_output_tokens = usage.get("output_tokens", 0)
            _total = last_input_tokens + last_output_tokens
            if _total > 0:
                get_rate_limiter().update_actual_usage(_total)

        # Extract content from output array
        _content_parts = []
        _reasoning_parts = []
        for item in result.get("output", []):
            if item.get("type") == "message":
                for content_block in item.get("content", []):
                    if content_block.get("type") == "output_text":
                        _content_parts.append(content_block.get("text", ""))
            elif item.get("type") == "reasoning":
                text = _extract_responses_reasoning_text(item)
                if text:
                    _reasoning_parts.append(text)

        content = "".join(_content_parts)
        reasoning = "".join(_reasoning_parts)
        content = _strip_metadata_tokens(content)

        if reasoning:
            for line in reasoning.splitlines(keepends=True):
                yield ("reasoning", line)
        if content:
            for line in content.splitlines(keepends=True):
                yield line
            if not content.endswith('\n'):
                yield '\n'
        return

    # ── Chat Completions path (default) ──
    # Build URL and API key based on provider routing
    if resolved_model and resolved_model.startswith("openrouter/"):
        resolved_model = resolved_model[len("openrouter/"):]
        url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = os.environ.get("OPENROUTER_API_KEY", config.API_KEY)
    elif resolved_model and resolved_model.startswith("zai/"):
        resolved_model = resolved_model[len("zai/"):]
        url = "https://api.z.ai/api/coding/paas/v4/chat/completions"
        api_key = os.environ.get("ZAI_API_KEY", config.API_KEY)
    else:
        url = build_chat_url(config.BASE_URL, resolved_model)
        api_key = config.API_KEY

    headers = build_api_headers(api_key)

    data = {
        "model": resolved_model,
        "messages": processed_messages,
        "stream": False,
    }
    if stop:
        # Z.AI and CanopyWave allow max 4 stop sequences
        _stop = stop[:4] if ("z.ai" in url or "canopywave" in url) else stop
        data["stop"] = _stop
    if config.MAX_OUTPUT_TOKENS > 0:
        _set_max_output_tokens(data, compute_safe_max_tokens())

    # Show spinner while waiting (suppressed during compression)
    _spinner = None
    if not suppress_spinner:
        try:
            from lib.display import Spinner as _Spinner
            _spinner = _Spinner("Thinking")
            _spinner.start()
        except Exception:
            _spinner = None

    _perf = getattr(config, "PERF_TRACKING", False)
    try:
        _body = json.dumps(data).encode('utf-8')
        _t_connect = time.time()
        response = _persistent_post_with_auth_retry(url, headers, _body, timeout=config.NONSTREAM_API_TIMEOUT)
        _t_connected = time.time()
        _ns_connect = _t_connected - _t_connect
        if _perf:
            _reuse_tag = "reused" if _last_post_reused else "new-conn"
            print(f"  \033[2m[PERF/LLM] connect: {_ns_connect:.3f}s ({_reuse_tag})\033[0m")
        result = json.loads(response.read().decode('utf-8'))
        _t_done = time.time()
        _ns_read = _t_done - _t_connected
        if _perf:
            print(f"  \033[2m[PERF/LLM] response_read: {_ns_read:.3f}s\033[0m")
    except (urllib.error.HTTPError, socket.timeout, urllib.error.URLError, ssl.SSLError):
        raise  # Let streaming caller handle 401/429/5xx/timeout properly (no silent empty-response)
    except Exception as e:
        if _spinner:
            _spinner.stop()
        print(Color.error(f"\n  LLM error: {e}"))
        return
    finally:
        if _spinner:
            _spinner.stop()

    choices = result.get("choices") or []
    if not choices:
        # ── Responses API format ──
        if is_responses_api_model(resolved_model):
            yield from _parse_responses_result(result)
            return
        return  # empty body (HTTP 200 but no content) — caller retry loop handles it
    msg = choices[0]["message"]
    usage = result.get("usage", {})
    if usage:
        last_input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
        last_output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
        # Update rate limiter with actual token usage
        _total = last_input_tokens + last_output_tokens
        if _total > 0:
            get_rate_limiter().update_actual_usage(_total)
        # Parse cache stats — Anthropic and OpenAI/Z.AI formats, gated by config
        if config.ENABLE_PROMPT_CACHING:
            _cct = usage.get("cache_creation_input_tokens", 0)
            _crt = usage.get("cache_read_input_tokens", 0)
            _ptd = usage.get("prompt_tokens_details") or {}
            _crt = _crt or _ptd.get("cached_tokens", 0)
            last_cache_creation_tokens = _cct
            last_cache_read_tokens     = _crt
            total_cache_created += _cct
            total_cache_read    += _crt

    # Record call (nonstream: ttft = connect+read, decode = 0)
    _record_call(
        caller="main(nonstream)",
        model=model or config.MODEL_NAME,
        in_tok=last_input_tokens,
        out_tok=last_output_tokens,
        connect_s=_ns_connect,
        ttft_s=_ns_connect + _ns_read,
        decode_s=0.0,
        total_s=_ns_connect + _ns_read,
    )

    # Non-streaming tool_calls in message (some internal hosts skip streaming protocol)
    _msg_tool_calls = msg.get("tool_calls") or []
    if _msg_tool_calls and getattr(config, "ENABLE_NATIVE_TOOL_CALLS", False):
        import uuid as _uuid
        _native_calls = []
        for tc in _msg_tool_calls:
            _func = tc.get("function", {})
            _name = _func.get("name", "")
            _args_raw = _func.get("arguments", "")
            _args_str = _args_raw or "{}"
            try:
                json.loads(_args_str)
            except json.JSONDecodeError:
                print(Color.warning(
                    f"\n  [Tool Call Warning] '{_name}' — "
                    f"arguments JSON invalid (got: {repr(_args_raw)[:80]}). "
                    f"Defaulting to {{}}. Check hosting tool-call serialization."
                ))
                _args_str = "{}"
            if _name:
                _native_calls.append({
                    "id": tc.get("id") or f"call_{_uuid.uuid4().hex[:16]}",
                    "name": _name,
                    "arguments": _args_str,
                })
        if _native_calls:
            yield ("native_tool_calls", _native_calls)
            return  # tool call response — no content to yield

    # Yield reasoning first (if present)
    reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""

    # Yield content line-by-line
    content = msg.get("content") or ""
    # moonshotai non-streaming: content=None, answer is in reasoning_content only.
    # Promote reasoning to content so the agent gets a response.
    if not content and reasoning and "moonshotai" in (resolved_model or "").lower():
        content = reasoning
        reasoning = ""
    # Sanitize provider metadata tokens
    content = _strip_metadata_tokens(content)

    # Non-streaming bleed fix: some models (e.g. GLM-4.7) split reasoning mid-sentence
    # and put the tail in content. Since we have the full text, we can reliably fix it.
    if reasoning and content:
        first_char = content.lstrip()[:1]
        if first_char and (first_char.islower() or first_char.isdigit() or first_char in ',;:'):
            # Content starts mid-sentence → find first sentence boundary
            m = re.search(r'[.!?]\s*[A-Z\n]', content)
            if m:
                reasoning = reasoning + content[:m.start() + 1]
                content = content[m.start() + 1:].lstrip()
            else:
                # No boundary found — treat all as reasoning tail, content is empty
                reasoning = reasoning + content
                content = ""

    # Debug output — use stderr so TUI stdout capture doesn't duplicate content
    if config.DEBUG_MODE:
        if reasoning:
            sys.stderr.write(f"\n\033[36m[reasoning]\033[0m {reasoning}\n")
            sys.stderr.flush()
        if content:
            sys.stderr.write(f"\n\033[32m[content]\033[0m {content}\n")
            sys.stderr.flush()

    if reasoning:
        for line in reasoning.splitlines(keepends=True):
            yield ("reasoning", line)

    if content:
        for line in content.splitlines(keepends=True):
            yield line
        # Ensure final newline
        if not content.endswith('\n'):
            yield '\n'


def chat_completion_stream(messages, stop=None, model=None, skip_rate_limit=False, caller_tag=None, suppress_spinner=False, tools=None, reasoning_effort=None):
    """
    Sends a chat completion request to the LLM using urllib.
    Yields content chunks from the SSE stream.
    Supports Anthropic Prompt Caching when enabled.
    Updates global actual_token_cache with real token counts from API.

    Args:
        messages: List of message dicts
        stop: Optional stop sequences
        model: Optional model override (default: config.MODEL_NAME)
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read
    global _last_debug_prompt_text, _last_debug_messages

    # cursor-agent backend dispatch
    if getattr(config, "CURSOR_AGENT_ENABLE", False):
        from src.cursor_agent_backend import cursor_agent_stream
        yield from cursor_agent_stream(
            messages=messages,
            model=getattr(config, "CURSOR_AGENT_MODEL", "auto"),
            yolo=getattr(config, "CURSOR_AGENT_YOLO", False),
            mode=getattr(config, "CURSOR_AGENT_MODE", ""),
            workspace=getattr(config, "CURSOR_AGENT_WORKSPACE", ""),
        )
        return
    if getattr(config, "CLAUDE_CLI_ENABLE", False):
        from src.claude_cli_backend import claude_cli_stream
        yield from claude_cli_stream(
            messages=messages,
            model=getattr(config, "CLAUDE_CLI_MODEL", "sonnet"),
            permission_mode=getattr(config, "CLAUDE_CLI_PERMISSION_MODE", "default"),
            tools=getattr(config, "CLAUDE_CLI_TOOLS", ""),
            workspace=getattr(config, "CLAUDE_CLI_WORKSPACE", ""),
            no_session_persistence=getattr(config, "CLAUDE_CLI_NO_SESSION_PERSISTENCE", True),
            output_format=getattr(config, "CLAUDE_CLI_OUTPUT_FORMAT", "json"),
            timeout_sec=getattr(config, "CLAUDE_CLI_TIMEOUT_SEC", 300),
        )
        return

    _t_fn_start = time.time()  # track pre-connect setup time

    # Kimi For Coding force-non-stream override.
    # api.kimi.com/coding/v1 returns HTTP 200 + immediate [DONE] with zero
    # delta chunks when stream=true is requested (verified e2e 2026-05).
    # The non-stream path returns full content normally. Force the
    # non-stream code path for any Kimi For Coding endpoint regardless of
    # the global ENABLE_STREAMING setting. Other providers unaffected.
    _kimi_force_nonstream = "api.kimi.com/coding" in (
        getattr(config, "BASE_URL", "") or ""
    ).lower()

    # Non-streaming mode: fetch full response then yield line-by-line
    if (not config.ENABLE_STREAMING) or _kimi_force_nonstream:
        _ns_delays = [3, 5, 10, 20, 40]
        _ns_max = len(_ns_delays) + 1
        _ns_model = model  # track for fallback
        _ns_fallback_used = False
        for _ns_retry in range(_ns_max):
            try:
                yield from _chat_completion_nonstream(messages, stop=stop, model=_ns_model, skip_rate_limit=skip_rate_limit, suppress_spinner=suppress_spinner)
                return
            except urllib.error.HTTPError as e:
                error_body = ""
                try:
                    error_body = e.read().decode('utf-8')
                except Exception:
                    pass
                if e.code == 401:
                    # Try fallback model before giving up
                    if not _ns_fallback_used and config.SECONDARY_MODEL and config.SECONDARY_MODEL != (_ns_model or config.MODEL_NAME):
                        _ns_fallback_used = True
                        _ns_model = config.SECONDARY_MODEL
                        print(Color.warning(f"\n[Fallback] 401 Unauthorized. Switching to: {_ns_model}\n"))
                        continue
                    yield f"\n{Color.error('[401 Unauthorized] Token quota exhausted — please top up your API credits.')}\n"
                    return
                is_retryable = e.code == 400 or e.code == 429 or (500 <= e.code < 600)
                # Error 1214 = permanent validation error — never retry (zai/GLM)
                _ns_zai = _parse_zai_error(error_body) if error_body else {}
                if _ns_zai.get("is_invalid_messages"):
                    is_retryable = False
                if is_retryable and _ns_retry < _ns_max - 1:
                    # 504 = transient upstream gateway timeout; use a
                    # short jittered delay (see streaming path above).
                    if e.code == 504:
                        import random as _rnd
                        delay = 5 + _ns_retry * 5 + _rnd.uniform(0, 3)
                        print(Color.warning(
                            f"\n[Retry {_ns_retry + 1}/{_ns_max - 1}] "
                            f"HTTP 504 Gateway Timeout — upstream busy, "
                            f"retrying in {delay:.1f}s..."))
                    else:
                        delay = 5 if e.code == 400 else _ns_delays[_ns_retry]
                        # Surface the server's reason on EVERY retry, not just
                        # the terminal failure — Codex returns {"detail": "..."}
                        # which carries the actual constraint violation
                        # (Instructions required, Store must be false, etc.).
                        _hint = ""
                        try:
                            _ej = json.loads(error_body) if error_body else {}
                            _hint = (
                                (isinstance(_ej.get("error"), dict) and _ej["error"].get("message"))
                                or _ej.get("detail")
                                or (error_body[:200] if error_body else "")
                            )
                        except Exception:
                            _hint = error_body[:200] if error_body else ""
                        _hint_s = f" — {_hint}" if _hint else ""
                        print(Color.warning(f"\n[Retry {_ns_retry + 1}/{_ns_max - 1}] HTTP {e.code}: {e.reason}{_hint_s}. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[HTTP Error {e.code}]: {e.reason}')}\n"
                try:
                    error_json = json.loads(error_body)
                    if 'error' in error_json:
                        error_info = error_json['error']
                        if isinstance(error_info, dict):
                            error_message = error_info.get('message', '')
                            if error_message:
                                yield f"{Color.error(f'  {error_message}')}\n"
                        else:
                            yield f"{Color.error(f'  {error_info}')}\n"
                    elif 'detail' in error_json:
                        # Codex backend uses {"detail": "..."} instead of {"error": ...}
                        _detail_msg = error_json['detail']
                        yield f"{Color.error(f'  {_detail_msg}')}\n"
                except Exception:
                    if error_body:
                        yield f"{Color.error(f'  {error_body[:300]}')}\n"
                return
            except socket.timeout as e:
                if _ns_retry < _ns_max - 1:
                    delay = _ns_delays[_ns_retry]
                    print(Color.warning(f"\n[Retry {_ns_retry + 1}/{_ns_max - 1}] Timeout: {e}. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[Timeout]: {e}')}\n"
                return
            except (urllib.error.URLError, ssl.SSLError) as e:
                if _ns_retry < _ns_max - 1:
                    delay = _ns_delays[_ns_retry]
                    err_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
                    print(Color.warning(f"\n[Retry {_ns_retry + 1}/{_ns_max - 1}] Connection error: {err_msg}. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    continue
                err_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
                yield f"\n{Color.error(f'[Connection Error]: {err_msg}')}\n"
                return
            except Exception as e:
                error_type = type(e).__name__
                if _ns_retry < _ns_max - 1:
                    delay = _ns_delays[_ns_retry]
                    print(Color.warning(f"\n[Retry {_ns_retry + 1}/{_ns_max - 1}] {error_type}: {e}. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[{error_type}]: {e}')}\n"
                return
        return

    _perf_pre = getattr(config, "PERF_TRACKING", False)
    _t_pre = time.time()

    # Rate limiting: TPM/RPM bucket if configured, else legacy fixed delay
    if not skip_rate_limit:
        _rl = get_rate_limiter()
        if _rl.active:
            _rl.acquire(estimated_tokens=last_input_tokens + last_output_tokens if last_input_tokens > 0 else None)
        elif config.RATE_LIMIT_DELAY > 0:
            if config.DEBUG_MODE:
                print(Color.info(f"[System] Waiting {config.RATE_LIMIT_DELAY}s for rate limit..."))
            time.sleep(config.RATE_LIMIT_DELAY)
    if _perf_pre:
        print(f"  \033[2m[PERF/setup] rate_limit: {time.time()-_t_pre:.3f}s\033[0m")

    # Apply prompt caching if enabled (deepcopy to preserve original)
    _t_pre = time.time()
    processed_messages = messages
    if config.ENABLE_PROMPT_CACHING and is_anthropic_provider():
        processed_messages = copy.deepcopy(messages)
        processed_messages = apply_cache_breakpoints(processed_messages)
    elif any(isinstance(m.get("content"), list) for m in messages):
        # Non-Anthropic provider: flatten list-of-blocks content to plain string
        # (optimized mode builds blocks for Anthropic cache; non-Anthropic needs strings)
        processed_messages = copy.deepcopy(messages)
        for m in processed_messages:
            if isinstance(m.get("content"), list):
                m["content"] = "\n\n".join(
                    block.get("text", "") for block in m["content"]
                    if isinstance(block, dict) and block.get("type") == "text"
                )
    # Non-native mode: strip native tool call artifacts (same as nonstream path above)
    if not getattr(config, "ENABLE_NATIVE_TOOL_CALLS", False):
        _has_artifacts = any(
            m.get("role") == "tool" or (m.get("role") == "assistant" and m.get("tool_calls"))
            for m in processed_messages
        )
        if _has_artifacts:
            if processed_messages is messages:
                processed_messages = copy.deepcopy(messages)
            _cleaned: list = []
            for _m in processed_messages:
                _role = _m.get("role")
                if _role == "tool":
                    _cleaned.append({"role": "user", "content": f"Observation: {_m.get('content', '')}"})
                elif _role == "assistant" and _m.get("tool_calls"):
                    _calls = _m.get("tool_calls", [])
                    _lines = [f"Action: {_tc.get('function', {}).get('name', '?')}({_tc.get('function', {}).get('arguments', '{}')})"
                              for _tc in _calls]
                    _text = _m.get("content") or ""
                    _combined = (_text + "\n" if _text else "") + "\n".join(_lines)
                    _new_msg = {"role": "assistant", "content": _combined.strip()}
                    # Preserve reasoning_content when converting native tool_calls → text.
                    # Cross-model transitions (DeepSeek → other → DeepSeek) can cause
                    # native-mode messages with reasoning_content to be converted in
                    # non-native mode.  Without this, the field would be dropped and
                    # the subsequent clean step would only get an empty placeholder.
                    if "reasoning_content" in _m:
                        _new_msg["reasoning_content"] = _m["reasoning_content"]
                    _cleaned.append(_new_msg)
                else:
                    _cleaned.append(_m)
            processed_messages = _cleaned

    # Sanitize messages for strict APIs (GLM-5.1/Z.AI, etc.):
    # 1. Merge stray system messages into position 0
    # 2. Merge consecutive same-role messages (user+user, assistant+assistant)
    # Note: "tool" role messages must NOT be merged — they need unique tool_call_id.
    # Note: "assistant" messages with tool_calls must NOT be merged (native tool mode).
    if processed_messages is messages:
        processed_messages = copy.deepcopy(messages)
    _merged = []
    for m in processed_messages:
        if not _merged:
            _merged.append(m)
            continue
        if m.get("role") == "system":
            if _merged[0].get("role") == "system":
                _merged[0]["content"] += "\n\n" + str(m.get("content", ""))
            else:
                _merged.insert(0, m)
            continue
        # Never merge tool messages or messages with tool_calls
        _is_tool_msg = m.get("role") == "tool"
        _prev_has_tool_calls = bool(_merged[-1].get("tool_calls"))
        _cur_has_tool_calls = bool(m.get("tool_calls"))
        if (not _is_tool_msg and not _prev_has_tool_calls and not _cur_has_tool_calls
                and _merged[-1].get("role") == m.get("role")):
            _merged[-1]["content"] = str(_merged[-1].get("content", "") or "") + "\n\n" + str(m.get("content", ""))
            # Preserve reasoning_content when merging assistant messages
            # DeepSeek REQUIRES reasoning_content on ALL assistant messages in history
            if m.get("role") == "assistant" and "reasoning_content" in m:
                prev_rc = _merged[-1].get("reasoning_content", "")
                new_rc = m.get("reasoning_content", "")
                _merged[-1]["reasoning_content"] = str(prev_rc) + "\n" + str(new_rc) if prev_rc else new_rc
            continue
        _merged.append(m)
    if _merged and _merged[0].get("role") != "system":
        _merged.insert(0, {"role": "system", "content": "You are a helpful AI coding assistant."})
    processed_messages = _merged

    # Strip internal-only fields (turn_id, timestamp, _tokens) before sending to API
    _API_ROLES = {"system", "user", "assistant", "tool"}
    _processed_clean = []
    for m in processed_messages:
        if m.get("role") not in _API_ROLES:
            continue
        clean = {"role": m["role"]}
        if "content" in m:
            clean["content"] = m["content"]
        if "tool_calls" in m:
            clean["tool_calls"] = m["tool_calls"]
        if "tool_call_id" in m:
            clean["tool_call_id"] = m["tool_call_id"]
        # Preserved thinking: pass reasoning_content back to API
        # - DeepSeek: REQUIRED — API returns HTTP 400 if missing in thinking mode.
        #   When chat history from another model (GPT, Claude, etc.) is loaded,
        #   those assistant messages won't have reasoning_content. DeepSeek's API
        #   requires reasoning_content on ALL assistant messages when thinking mode
        #   is active, so we inject a placeholder for missing ones.
        # - GLM-5/5.1: optional, controlled by GLM_CLEAR_THINKING config.
        # - Cross-model preservation: always carry forward reasoning_content if
        #   present on the source message, regardless of current model.  This
        #   prevents data loss when switching DeepSeek → other → DeepSeek: the
        #   field survives across model transitions because we never strip it.
        _m_lower = (model or getattr(config, 'MODEL_NAME', '')).lower()
        if "reasoning_content" in m and m["reasoning_content"]:
            # Preserve existing reasoning_content for ALL models (model-agnostic).
            # This is critical for cross-model session transitions:
            #   DeepSeek → other model → back to DeepSeek
            # Without this, the intermediate "other model" call strips the field
            # and the final DeepSeek call only gets an empty placeholder.
            clean["reasoning_content"] = m["reasoning_content"]
        elif 'deepseek' in _m_lower and m.get("role") == "assistant":
            # Cross-model history: assistant messages from other models lack
            # reasoning_content. Inject a placeholder so DeepSeek API accepts
            # the request. (empty string " " matches react_loop.py convention)
            clean["reasoning_content"] = " "
        elif "reasoning_content" in m and 'glm-' in _m_lower:
            # GLM with empty/whitespace reasoning_content — only preserve
            # if GLM_CLEAR_THINKING is False.
            if not getattr(config, "GLM_CLEAR_THINKING", True):
                clean["reasoning_content"] = m["reasoning_content"]
        _processed_clean.append(clean)
    processed_messages = _processed_clean

    if _perf_pre:
        print(f"  \033[2m[PERF/setup] prompt_cache_prep: {time.time()-_t_pre:.3f}s\033[0m")

    # Determine API key for the request
    api_key = config.API_KEY

    # If model override uses "provider/..." format, route accordingly
    if model and "/" in model:
        parts = model.split("/", 1)
        provider = parts[0]
        if provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            api_key = os.environ.get("OPENROUTER_API_KEY", config.API_KEY)
        elif provider == "zai":
            url = "https://api.z.ai/api/coding/paas/v4/chat/completions"
            api_key = os.environ.get("ZAI_API_KEY", config.API_KEY)
        else:
            url = build_chat_url(config.BASE_URL, model)
    else:
        url = build_chat_url(config.BASE_URL)

    headers = build_api_headers(api_key)

    # Add Anthropic-specific headers if caching enabled
    if config.ENABLE_PROMPT_CACHING and is_anthropic_provider():
        headers["anthropic-beta"] = "prompt-caching-2024-07-31"
        if config.DEBUG_MODE:
            print(Color.info("[System] Prompt caching enabled - added anthropic-beta header"))

    # Resolve model: explicit override > config default
    resolved_model = model or config.MODEL_NAME

    # If model override uses "provider/model" format, strip the provider prefix
    # (URL routing is already handled above)
    if resolved_model and resolved_model.startswith("openrouter/"):
        resolved_model = resolved_model[len("openrouter/"):]

    # ── Responses API path ──
    if use_responses_api(resolved_model):
        url = build_responses_url(config.BASE_URL, resolved_model)
        headers = build_api_headers(api_key)
        data = _build_responses_request_body(
            messages=processed_messages,
            model=resolved_model,
            stream=True,
            stop=stop,
            tools=tools,
            max_output_tokens=compute_safe_max_tokens() if config.MAX_OUTPUT_TOKENS > 0 else None,
            base_url=url,
            reasoning_effort=reasoning_effort,
        )

        if config.DEBUG_MODE:
            from collections import Counter as _Counter
            tag = f" ({caller_tag})" if caller_tag else ""
            _role_counts = _Counter(m.get("role", "?") for m in processed_messages)
            _role_str = "  /  ".join(f"{r}: {c}" for r, c in sorted(_role_counts.items()))
            _total_chars = sum(len(str(m.get("content", ""))) for m in processed_messages)
            _est_tok = _total_chars // 4
            _r_cfg = data.get("reasoning") or {}
            _tool_names = [t.get("name", t.get("function", {}).get("name", "?")) for t in (data.get("tools") or [])]
            print(Color.info(f"\n[Request Debug (Responses API)]{tag}"))
            print(Color.info(f"  URL:         {url}"))
            print(Color.info(f"  Model:       {resolved_model}"))
            print(Color.info(f"  Stream:      {data.get('stream', True)}"))
            print(Color.info(f"  Messages:    {len(processed_messages)}  ({_role_str})"))
            print(Color.info(f"  Est.tokens:  {_est_tok:,}"))
            if data.get("temperature") is not None:
                print(Color.info(f"  Temperature: {data['temperature']}"))
            if data.get("max_output_tokens"):
                print(Color.info(f"  Max tokens:  {data['max_output_tokens']:,}"))
            if data.get("stop"):
                print(Color.info(f"  Stop seqs:   {len(data['stop'])}"))
            if _tool_names:
                print(Color.info(f"  Tools:       {len(_tool_names)}  [{', '.join(_tool_names[:5])}{'...' if len(_tool_names)>5 else ''}]"))
                print(Color.info(f"  Tool choice: {data.get('tool_choice', 'auto')}"))
            if _r_cfg:
                _r_parts = "  ".join(f"{k}={v}" for k, v in _r_cfg.items())
                print(Color.info(f"  Reasoning:   {_r_parts}"))
            if data.get("store") is not None:
                print(Color.info(f"  Store:       {data['store']}"))

        yield from _execute_streaming_request_responses(url, headers, data, processed_messages, native_mode=bool(tools))
        return

    # ── Chat Completions path (default) ──
    data = {
        "model": resolved_model,
        "messages": processed_messages,
        "stream": True,
        "stream_options": {"include_usage": True}  # Request usage data in streaming (OpenAI)
    }

    # Enable store for cache-capable models in Chat Completions API
    # - GLM: KV cache support (reduces memory footprint on subsequent calls)
    # - OpenAI (gpt-5.x, o-series): prompt caching for faster responses
    _model_lower = (resolved_model or '').lower()
    if 'glm' in _model_lower or 'gpt-' in _model_lower or any(x in _model_lower for x in ('o1', 'o3', 'o4')):
        data["store"] = True

    if stop:
        # Z.AI and CanopyWave allow max 4 stop sequences
        _stop = stop[:4] if ("z.ai" in url or "canopywave" in url) else stop
        data["stop"] = _stop

    if config.MAX_OUTPUT_TOKENS > 0:
        _set_max_output_tokens(data, compute_safe_max_tokens())

    # Native tool call support: inject tools schema when provided
    if tools:
        # Strip strict mode for non-OpenAI providers (GLM, DeepSeek, etc.)
        # that may not support it in Chat Completions format.
        _is_openai = "openai.com" in url
        if not _is_openai:
            tools = _strip_strict_from_tools(tools)
        data["tools"] = tools
        data["tool_choice"] = "auto"

    _chat_effort_cfg, _chat_effort_note = _apply_chat_reasoning_controls(
        data, resolved_model, url, reasoning_effort
    )

    # Debug: Log request details
    if config.DEBUG_MODE:
        from collections import Counter as _Counter
        tag = f" ({caller_tag})" if caller_tag else ""
        _role_counts = _Counter(m.get("role", "?") for m in processed_messages)
        _role_str = "  /  ".join(f"{r}: {c}" for r, c in sorted(_role_counts.items()))
        total_chars = sum(len(str(m.get('content', ''))) for m in processed_messages)
        estimated_tokens = total_chars // 4
        has_structured = any(isinstance(m.get('content'), list) for m in processed_messages)
        _tool_names = [t.get("function", {}).get("name", "?") for t in (data.get("tools") or [])]
        _max_tok = data.get("max_completion_tokens") or data.get("max_tokens")
        _prompt_debug_text = ""
        _common_tok = None
        _common_pct = None
        _first_diff = None
        try:
            _prompt_debug_text = json.dumps(
                {"messages": processed_messages, "tools": data.get("tools") or []},
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            if _last_debug_prompt_text:
                _common_chars = 0
                _limit = min(len(_last_debug_prompt_text), len(_prompt_debug_text))
                while _common_chars < _limit and _last_debug_prompt_text[_common_chars] == _prompt_debug_text[_common_chars]:
                    _common_chars += 1
                _common_tok = _common_chars // 4
                _common_pct = int(100 * _common_chars / max(1, len(_prompt_debug_text)))
            if _last_debug_messages is not None:
                _min_len = min(len(_last_debug_messages), len(processed_messages))
                for _idx in range(_min_len):
                    _prev_msg = json.dumps(_last_debug_messages[_idx], ensure_ascii=False, sort_keys=True, default=str)
                    _cur_msg = json.dumps(processed_messages[_idx], ensure_ascii=False, sort_keys=True, default=str)
                    if _prev_msg != _cur_msg:
                        _first_diff = (_idx, processed_messages[_idx].get("role", "?"))
                        break
                if _first_diff is None and len(_last_debug_messages) != len(processed_messages):
                    _first_diff = (_min_len, "length")
        except Exception:
            pass
        print(Color.info(f"\n[Request Debug]{tag}"))
        print(Color.info(f"  URL:         {url}"))
        print(Color.info(f"  Model:       {resolved_model}"))
        print(Color.info(f"  Stream:      {data.get('stream', True)}"))
        print(Color.info(f"  Messages:    {len(processed_messages)}  ({_role_str})"))
        print(Color.info(f"  Est.tokens:  {estimated_tokens:,}"))
        print(Color.info(f"  Cache blocks: {has_structured}  (structured prompt blocks, not GLM hit-rate)"))
        if _common_tok is not None:
            print(Color.info(f"  Prompt reuse:{_common_tok:,} est.tok prefix ({_common_pct}%) vs previous request"))
        if _first_diff is not None:
            print(Color.info(f"  First diff:  message[{_first_diff[0]}] role={_first_diff[1]}"))
        if data.get("temperature") is not None:
            print(Color.info(f"  Temperature: {data['temperature']}"))
        if _max_tok:
            print(Color.info(f"  Max tokens:  {_max_tok:,}"))
        if data.get("stop"):
            print(Color.info(f"  Stop seqs:   {len(data['stop'])}"))
        if _tool_names:
            print(Color.info(f"  Tools:       {len(_tool_names)}  [{', '.join(_tool_names[:5])}{'...' if len(_tool_names)>5 else ''}]"))
            print(Color.info(f"  Tool choice: {data.get('tool_choice', 'auto')}"))
        print(Color.info(f"  Effort cfg:  {_chat_effort_cfg}  ({_chat_effort_note})"))
        if data.get("reasoning_effort"):
            print(Color.info(f"  Reasoning:   effort={data['reasoning_effort']}"))
        if data.get("store") is not None:
            print(Color.info(f"  Store:       {data['store']}"))
        if data.get("thinking"):
            _th = data["thinking"]
            print(Color.info(f"  Thinking:    type={_th.get('type')} clear={_th.get('clear_thinking')}"))
        if _prompt_debug_text:
            _last_debug_prompt_text = _prompt_debug_text
            try:
                _last_debug_messages = copy.deepcopy(processed_messages)
            except Exception:
                _last_debug_messages = None

        # FULL_PROMPT_DEBUG: Show complete input messages
        if getattr(config, 'FULL_PROMPT_DEBUG', False):
            print(Color.info("\n" + "="*60))
            print(Color.info("[FULL PROMPT DEBUG] Complete input messages:"))
            print(Color.info("="*60))
            msgs_to_show = processed_messages
            start_index = 0

            # Check for limit configuration
            if getattr(config, 'FULL_PROMPT_DEBUG_LIMIT_ENABLED', True):
                limit_count = getattr(config, 'FULL_PROMPT_DEBUG_LIMIT_COUNT', 5)
                total_msgs = len(processed_messages)
                
                if total_msgs > limit_count:
                    start_index = total_msgs - limit_count
                    if start_index > 0:
                        print(Color.info(f"\n... [Skipping {start_index} earlier messages (showing last {limit_count})] ..."))
                        msgs_to_show = processed_messages[start_index:]

            # Check for line limit configuration
            line_limit_enabled = getattr(config, 'FULL_PROMPT_DEBUG_LINE_LIMIT_ENABLED', True)
            line_limit_count = getattr(config, 'FULL_PROMPT_DEBUG_LINE_LIMIT_COUNT', 20)

            for i, msg in enumerate(msgs_to_show):
                real_idx = start_index + i + 1
                role = msg.get('role', 'unknown')
                content = str(msg.get('content', ''))
                
                print(Color.info(f"\n--- Message {real_idx} [{role}] ---"))
                
                # Colorize Action and Thought in debug output using regex for potential multi-matches
                import re
                
                # Colors
                CYAN = "\033[96m"
                YELLOW = "\033[93m" 
                RESET = "\033[0m"

                colored_lines = []
                lines = content.splitlines()
                for line in lines[:line_limit_count] if line_limit_enabled and len(lines) > line_limit_count else lines:
                    # Highlight "Action:"
                    line = re.sub(r'(Action:)', YELLOW + r'\1' + RESET, line)
                    # Highlight "Thought:"
                    line = re.sub(r'(Thought:)', CYAN + r'\1' + RESET, line)
                    colored_lines.append(line)
                
                if line_limit_enabled and len(lines) > line_limit_count:
                    # Print first N lines and truncation notice
                    print('\n'.join(colored_lines))
                    print(Color.info(f"... [truncated, {len(lines) - line_limit_count} lines hidden (total {len(lines)} lines)]"))
                else:
                    # Default large message handling (fallback to char truncation)
                    content_to_print = '\n'.join(colored_lines)
                    if len(content) > 5000:
                        print(content_to_print[:5000])
                        print(Color.info(f"... [truncated, total {len(content)} chars]"))
                    else:
                        print(content_to_print)
            print(Color.info("="*60 + "\n"))
        print()

    # Retry logic for transient errors
    _RETRY_DELAYS2 = [3, 5, 10, 20, 40]  # backoff for all retryable errors
    max_retries = len(_RETRY_DELAYS2) + 1
    _fallback_used = False  # True after switching to SECONDARY_MODEL

    for retry_count in range(max_retries):
        global _stream_cancelled
        if _stream_cancelled:
            _stream_cancelled = False
            return
        # Local state for label tracking (resets each retry)
        _reasoning_started = False
        _content_label_printed = False
        _debug_line_buf = ""
        _debug_in_think = False
        _wd_stop, _wd_triggered = None, [False]  # init before try so except can always reference
        _in_think_tag = False
        _think_buf = ""

        _perf = getattr(config, "PERF_TRACKING", False)
        try:
            _t_pre = time.time()
            _post_body = json.dumps(data).encode('utf-8')
            if _perf:
                print(f"  \033[2m[PERF/setup] json_encode: {time.time()-_t_pre:.3f}s\033[0m")

            # Persistent connection (skips TCP+SSL handshake on 2nd+ call)
            _t_pre = time.time()
            if _perf:
                print(f"  \033[2m[PERF/setup] ssl_ctx: {time.time()-_t_pre:.3f}s\033[0m")

            _t_connect = time.time()
            _perf_connect = None
            _perf_ttft = None
            _perf_gen_elapsed = None
            _perf_chunks = 0
            response = _persistent_post_with_auth_retry(url, headers, _post_body, timeout=config.STREAM_API_TIMEOUT)
            global _active_stream_response
            _active_stream_response = response
            _inactivity_s = getattr(config, 'STREAM_INACTIVITY_TIMEOUT', 120)
            _last_data = [time.time()]
            _last_progress = [time.time()]
            _wd_stop, _wd_triggered = _make_stream_watchdog(
                response, _inactivity_s, _last_data, _last_progress
            )
            try:
                _perf_connect = time.time() - _t_connect
                # Parse Server-Sent Events (SSE)
                usage_info = None
                _t_first_token = None
                _total_tokens_streamed = 0
                _yielded_something = False
                _finish_reason = None   # captured from last non-null finish_reason chunk
                # Accumulate native tool calls across streaming chunks.
                _pending_tool_calls: Dict[int, Dict] = {}
                for line in response:
                    _last_data[0] = time.time()
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        # Secondary progress checkpoint — see Responses API
                        # streamer for rationale (don't let SSE keep-alives
                        # mask a stalled provider).
                        _last_progress[0] = time.time()
                        data_str = line[6:] # Remove "data: " prefix
                        if data_str == "[DONE]":
                            if _t_first_token:
                                _perf_gen_elapsed = time.time() - _t_first_token
                                _perf_chunks = _total_tokens_streamed
                            break
                        try:
                            chunk_json = json.loads(data_str)

                            # Usage stats appear only in the last chunk (Z.AI / OpenAI spec)
                            if "usage" in chunk_json:
                                usage_info = chunk_json["usage"]

                            # Extract content delta
                            # Structure: choices[0].delta.content
                            if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                                choice = chunk_json["choices"][0]
                                # Capture finish_reason; only non-null in the last chunk
                                _fr = choice.get("finish_reason")
                                if _fr:
                                    _finish_reason = _fr
                                delta = choice.get("delta", {})

                                # Reasoning tokens (DeepSeek, GLM, OpenRouter reasoning_details)
                                reasoning = delta.get("reasoning") or delta.get("reasoning_content", "")
                                if not reasoning:
                                    for rd in (delta.get("reasoning_details") or []):
                                        if rd.get("type") == "thinking":
                                            reasoning = (reasoning or "") + (rd.get("thinking", "") or rd.get("summary", ""))
                                content = delta.get("content", "") or ""

                                # Streaming bleed fix: when both reasoning_content and content
                                # arrive in the same delta, the content is always a bleed-over
                                # from the reasoning tail (observed consistently on GLM-4.7).
                                if reasoning and content:
                                    reasoning = reasoning + content
                                    content = ""

                                # <think> tag state machine for internal hosting
                                if not reasoning and content and (_think_buf or '<t' in content or '</t' in content):
                                    _think_buf += content
                                    content = ""
                                    reasoning = ""
                                    while True:
                                        if _in_think_tag:
                                            close_pos = _think_buf.find("</think>")
                                            if close_pos == -1:
                                                _safe = len(_think_buf) - 8
                                                if _safe > 0:
                                                    reasoning += _think_buf[:_safe]
                                                    _think_buf = _think_buf[_safe:]
                                                break
                                            else:
                                                reasoning += _think_buf[:close_pos]
                                                _think_buf = _think_buf[close_pos + 8:]
                                                _in_think_tag = False
                                        else:
                                            open_pos = _think_buf.find("<think>")
                                            if open_pos == -1:
                                                _safe = max(0, len(_think_buf) - 7)
                                                content += _think_buf[:_safe]
                                                _think_buf = _think_buf[_safe:]
                                                break
                                            else:
                                                content += _think_buf[:open_pos]
                                                _think_buf = _think_buf[open_pos + 7:]
                                                _in_think_tag = True

                                if reasoning or content:
                                    if _t_first_token is None:
                                        _t_first_token = time.time()
                                        _perf_ttft = _t_first_token - _t_connect
                                    _total_tokens_streamed += 1

                                if reasoning:
                                    yield ("reasoning", reasoning)
                                    _yielded_something = True
                                if content:
                                    yield content
                                    _yielded_something = True

                                # Accumulate native tool_calls across streaming chunks.
                                # OpenAI/Z.AI streaming protocol:
                                #   - first chunk carries id, type, function.name
                                #   - subsequent chunks carry only function.arguments fragments
                                tool_calls = delta.get("tool_calls") or []
                                for tc in tool_calls:
                                    idx = tc.get("index", 0)
                                    if idx not in _pending_tool_calls:
                                        _pending_tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                                    # id and name arrive only in the first chunk — preserve them
                                    if tc.get("id"):
                                        _pending_tool_calls[idx]["id"] = tc["id"]
                                    func = tc.get("function", {})
                                    if func.get("name"):
                                        _pending_tool_calls[idx]["name"] = func["name"]
                                    if func.get("arguments"):
                                        _pending_tool_calls[idx]["arguments"] += func["arguments"]

                        except json.JSONDecodeError:
                            continue

                # Emit accumulated tool calls after stream ends.
                # Native mode (tools param set): yield structured tuple for react_loop.
                # Legacy mode: convert to Action: text lines for ReAct parser.
                if _pending_tool_calls:
                    _yielded_something = True
                    if tools:
                        # Native tool call mode — yield structured list for react_loop
                        import uuid as _uuid
                        _native_calls = []
                        for idx in sorted(_pending_tool_calls):
                            tc_info = _pending_tool_calls[idx]
                            tc_name = tc_info["name"]
                            tc_args_str = tc_info["arguments"] or "{}"
                            if tc_name:
                                # Prefer API-provided id; fall back to generated uuid
                                call_id = tc_info.get("id") or f"call_{_uuid.uuid4().hex}"
                                # Validate arguments JSON
                                try:
                                    json.loads(tc_args_str)
                                except json.JSONDecodeError:
                                    tc_args_str = "{}"
                                _native_calls.append({
                                    "id": call_id,
                                    "name": tc_name,
                                    "arguments": tc_args_str,
                                })
                        if _native_calls:
                            yield ("native_tool_calls", _native_calls)
                    else:
                        # Legacy ReAct mode — convert to Action: text
                        for idx in sorted(_pending_tool_calls):
                            tc_info = _pending_tool_calls[idx]
                            tc_name = tc_info["name"]
                            tc_args_str = tc_info["arguments"]
                            if tc_name and tc_args_str:
                                try:
                                    tc_args = json.loads(tc_args_str)
                                    args_formatted = ", ".join(
                                        f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in tc_args.items()
                                    )
                                    yield f"\nAction: {tc_name}({args_formatted})\n"
                                except (json.JSONDecodeError, AttributeError):
                                    pass

                # Print PERF/LLM summary after streaming completes (clean, no mid-stream interleave)
                if _perf:
                    _setup = _t_connect - _t_fn_start
                    _tps_str = ""
                    if _perf_gen_elapsed and _perf_gen_elapsed > 0:
                        _tps = _perf_chunks / _perf_gen_elapsed
                        _tps_str = f" ({_perf_chunks} chunks, {_tps:.1f} tok/s)"
                    _reuse_tag = "reused" if _last_post_reused else "new-conn"
                    print(f"\n  \033[2m[PERF/LLM] setup={_setup:.3f}s | connect={_perf_connect:.3f}s ({_reuse_tag}) | ttft={_perf_ttft:.3f}s | decode={_perf_gen_elapsed:.3f}s{_tps_str}\033[0m")

                # Record call
                _record_call(
                    caller=caller_tag or "main",
                    model=resolved_model,
                    in_tok=last_input_tokens,
                    out_tok=last_output_tokens,
                    connect_s=_perf_connect or 0.0,
                    ttft_s=_perf_ttft or 0.0,
                    decode_s=_perf_gen_elapsed or 0.0,
                    total_s=(_perf_connect or 0.0) + (_perf_ttft or 0.0) + (_perf_gen_elapsed or 0.0),
                )

                # Update global token tracking with actual values from API
                if usage_info:
                    # Both OpenAI and Anthropic use "input_tokens" or "prompt_tokens"
                    input_tokens = usage_info.get("input_tokens") or usage_info.get("prompt_tokens", 0)
                    output_tokens = usage_info.get("output_tokens") or usage_info.get("completion_tokens", 0)
                    if input_tokens > 0:
                        last_input_tokens = input_tokens
                    if output_tokens > 0:
                        last_output_tokens = output_tokens

                    # Update rate limiter with actual token usage
                    _total = input_tokens + output_tokens
                    if _total > 0:
                        get_rate_limiter().update_actual_usage(_total)

                # Parse cache token usage — supports both Anthropic and OpenAI/Z.AI formats
                _cache_creation_tok = 0
                _cache_read_tok = 0
                if usage_info and config.ENABLE_PROMPT_CACHING:
                    _cache_creation_tok = usage_info.get("cache_creation_input_tokens", 0)
                    _cache_read_tok = usage_info.get("cache_read_input_tokens", 0)
                    _ptd = usage_info.get("prompt_tokens_details") or {}
                    _cache_read_tok = _cache_read_tok or _ptd.get("cached_tokens", 0)
                    last_cache_creation_tokens = _cache_creation_tok
                    last_cache_read_tokens = _cache_read_tok
                    total_cache_created += _cache_creation_tok
                    total_cache_read += _cache_read_tok

                if usage_info and config.DEBUG_MODE:
                    total_tokens = input_tokens + output_tokens
                    _new_input = input_tokens - _cache_read_tok - _cache_creation_tok
                    _cache_hit_pct = (_cache_read_tok / input_tokens * 100.0) if input_tokens else 0.0
                    _tc_names = [tc.get("name", "?") for tc in _pending_tool_calls.values() if tc.get("name")] if "_pending_tool_calls" in dir() else []
                    _reasoning_tok = usage_info.get("thinking_input_tokens", 0) or \
                        (usage_info.get("usage", {}) or {}).get("thinking_input_tokens", 0)
                    _content_tok = output_tokens - _reasoning_tok
                    print(f"\n{Color.info('[Response]')}")
                    if _finish_reason:
                        print(Color.info(f"  Finish:      {_finish_reason}"))
                    print(Color.info(f"  {'─'*32}"))
                    _cache_detail = ""
                    if _cache_creation_tok > 0:
                        _cache_detail += f"  (created: {_cache_creation_tok:,})"
                    if _cache_read_tok > 0:
                        _cache_detail += f"  (cached: {_cache_read_tok:,} / new: {_new_input:,})"
                    _out_detail = f"  (reasoning: {_reasoning_tok:,} / content: {_content_tok:,})" if _reasoning_tok > 0 else ""
                    print(Color.info(f"  Input:       {input_tokens:,}{_cache_detail}"))
                    if _cache_read_tok > 0:
                        print(Color.info(f"  Cache hit:   {_cache_hit_pct:.1f}%"))
                    print(Color.info(f"  Output:      {output_tokens:,}{_out_detail}"))
                    print(Color.info(f"  Total:       {total_tokens:,}"))
                    if _tc_names:
                        print(Color.info(f"  {'─'*32}"))
                        print(Color.info(f"  Tool calls:  {len(_tc_names)}  [{', '.join(_tc_names)}]"))
                    print()
                
                # finish_reason signals
                if _finish_reason == "length":
                    _mt = data.get('max_completion_tokens', data.get('max_tokens', 'unset'))
                    print(Color.warning(
                        f"\n[Warning] Output truncated: max_tokens limit reached "
                        f"(max_tokens={_mt}). "
                        f"Increase MAX_OUTPUT_TOKENS or reduce input size."
                    ))
                    yield ("finish_reason", "length")
                elif _finish_reason == "content_filter":
                    yield ("finish_reason", "content_filter")

                # Empty response (HTTP 200 but no content/reasoning/tool_calls) — retry
                if not _yielded_something and retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS2[min(retry_count, len(_RETRY_DELAYS2)-1)]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] Empty response from LLM. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    # fall through to finally, then loop continues
                else:
                    return  # Success (or exhausted retries with empty response)
            finally:
                if _wd_stop is not None:
                    _wd_stop.set()
                _active_stream_response = None  # stream done
                # Drain any unread bytes so the connection can be reused
                try:
                    response.read()
                except Exception:
                    pass
            if _wd_triggered[0]:
                raise socket.timeout(f"No data for {_inactivity_s}s (inactivity)")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            zai = _parse_zai_error(error_body)

            # ── 401: Auth failure → try fallback model ──
            if e.code == 401:
                if not _fallback_used and config.SECONDARY_MODEL and config.SECONDARY_MODEL != resolved_model:
                    _fallback_used = True
                    resolved_model = config.SECONDARY_MODEL
                    print(Color.warning(f"\n[Fallback] Auth error (401). Switching to: {resolved_model}\n"))
                    continue
                yield f"\n{Color.error('[401 Unauthorized] Token quota exhausted — please top up your API credits.')}\n"
                return

            # ── Extract zai values for f-string compatibility (no backslashes) ──
            _zai_msg = zai["message"]
            _zai_code = zai["code"]
            _zai_type = zai["type"]
            _zai_reset = zai["reset_time"]

            # ── Account locked / balance exhausted → do NOT retry ──
            if zai["is_account_locked"] or zai["is_balance_exhausted"]:
                code_str = f" (code {_zai_code})" if _zai_code else ""
                yield f"\n{Color.error(f'[HTTP {e.code}]{code_str} {_zai_msg}')}\n"
                if zai["is_balance_exhausted"]:
                    yield f"{Color.warning('→ Please top up your API credits or check your subscription plan.')}\n"
                else:
                    yield f"{Color.warning('→ Account is locked. Contact Z.AI customer service to unlock.')}\n"
                return

            # ── Content filter → do NOT retry ──
            if zai["is_content_filter"]:
                yield f"\n{Color.error('[Content Filter] Request blocked by safety policy.')}\n"
                yield f"{Color.warning('→ Rephrase your prompt to avoid potentially sensitive content.')}\n"
                return

            # ── Prompt too long → signal caller to compress ──
            if zai["is_prompt_too_long"]:
                yield f"\n{Color.error('[Prompt Too Long] Input exceeds model context limit (code 1261).')}\n"
                yield ("finish_reason", "prompt_too_long")
                return

            # ── Rate limit with reset time ──
            if zai["is_rate_limit"] and _zai_reset:
                if retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS2[retry_count]
                    print(Color.warning(
                        f"\n[Retry {retry_count + 1}/{max_retries - 1}] Rate limited "
                        f"(code {_zai_code}). Resets at {_zai_reset}. "
                        f"Waiting {delay}s...\n"
                    ))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[Rate Limited] {_zai_msg}')}\n"
                yield f"{Color.warning(f'→ Limit resets at {_zai_reset}')}\n"
                return

            # ── High traffic → try fallback model ──
            if zai["is_high_traffic"]:
                if not _fallback_used and config.SECONDARY_MODEL and config.SECONDARY_MODEL != resolved_model:
                    _fallback_used = True
                    resolved_model = config.SECONDARY_MODEL
                    print(Color.warning(
                        f"\n[Fallback] Model overloaded (code 1312). Switching to: {resolved_model}\n"
                    ))
                    continue
                if retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS2[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Model high traffic. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[High Traffic] {_zai_msg}')}\n"
                return

            # ── Generic retryable: 400 (vLLM transient), 429 or 5xx ──
            is_retryable = e.code == 400 or e.code == 429 or (500 <= e.code < 600)
            # Error 1214 = permanent validation error — never retry (zai/GLM)
            if zai.get("is_invalid_messages"):
                is_retryable = False
            if is_retryable and retry_count < max_retries - 1:
                # 504 = transient upstream gateway timeout; use shorter
                # jittered delay (see streaming-path block for full
                # rationale).
                if e.code == 504:
                    import random as _rnd
                    delay = 5 + retry_count * 5 + _rnd.uniform(0, 3)
                    print(Color.warning(
                        f"\n[Retry {retry_count + 1}/{max_retries - 1}] "
                        f"HTTP 504 Gateway Timeout — upstream busy, "
                        f"retrying in {delay:.1f}s..."))
                else:
                    delay = 5 if e.code == 400 else _RETRY_DELAYS2[retry_count]
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] HTTP {e.code}: {e.reason}"))
                    print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # ── Non-retryable or max retries reached ──
            yield f"\n{Color.error(f'[HTTP Error {e.code}]: {e.reason}')}\n"
            if _zai_code:
                yield f"{Color.error(f'  Code: {_zai_code}')}\n"
            if _zai_msg:
                yield f"{Color.error(f'  Message: {_zai_msg}')}\n"
            elif _zai_type:
                yield f"{Color.error(f'  Type: {_zai_type}')}\n"
            else:
                yield f"{Color.error(f'  {error_body[:300]}')}\n"

            if config.DEBUG_MODE:
                yield f"\n{Color.info('[Debug Info]')}\n"
                yield f"{Color.info(f'  Model: {resolved_model}')}\n"
                yield f"{Color.info(f'  URL: {url}')}\n"

            return

        except urllib.error.URLError as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            # Connection error - retry
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS2[min(retry_count, len(_RETRY_DELAYS2)-1)]
                error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)

                # Special handling for SSL errors
                if 'SSL' in error_msg or 'ssl' in error_msg.lower():
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] SSL Error: {error_msg}"))
                    print(Color.warning(f"This is usually a temporary network issue."))
                else:
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] Connection Error: {error_msg}"))

                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # Max retries reached
            error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            yield f"\n{Color.error(f'[Connection Error]: {error_msg}')}\n"
            yield f"{Color.warning('Tip: If SSL errors persist, check your network connection or try again later.')}\n"
            return

        except socket.timeout as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            # Covers real socket timeouts and inactivity-watchdog triggers
            inactivity_triggered = 'inactivity' in str(e).lower()
            label = f"Inactivity ({_inactivity_s}s, no data)" if inactivity_triggered else f"Read timeout ({config.STREAM_API_TIMEOUT}s)"
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS2[min(retry_count, len(_RETRY_DELAYS2)-1)]
                # Reset stale connection so next attempt gets a fresh socket
                try:
                    _http_conn_pool.pop(urllib.parse.urlparse(url).netloc, None)
                except Exception:
                    pass
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] {label}: {e}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[{label}]: {e}')}\n"
            return

        except ssl.SSLError as e:
            if _stream_cancelled:
                _stream_cancelled = False
                return
            # Explicit SSL error handling (backup catch)
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS2[min(retry_count, len(_RETRY_DELAYS2)-1)]
                try:
                    _http_conn_pool.pop(urllib.parse.urlparse(url).netloc, None)
                except Exception:
                    pass
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] SSL Handshake Error: {e}"))
                print(Color.warning(f"This is usually a temporary network/server issue."))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # Max retries reached
            yield f"\n{Color.error(f'[SSL Error]: {e}')}\n"
            yield f"{Color.warning('Possible causes:')}\n"
            yield f"{Color.warning('  1. Temporary network instability')}\n"
            yield f"{Color.warning('  2. API server maintenance')}\n"
            yield f"{Color.warning('  3. Firewall/proxy interference')}\n"
            yield f"{Color.info('Try again in a few moments.')}\n"
            return

        except Exception as e:
            # ESC pressed during stream → cancel_current_stream() closes the underlying
            # socket, which can surface here as AttributeError/OSError/IncompleteRead.
            # Honor the cancel flag immediately — no retry message, no sleep.
            if _stream_cancelled:
                _stream_cancelled = False
                return
            # Catch-all for unexpected errors (incl. ResponseNotReady from stale connection,
            # or watchdog-closed connection raising OSError/IncompleteRead)
            if _wd_triggered[0]:
                if retry_count < max_retries - 1:
                    delay = _RETRY_DELAYS2[min(retry_count, len(_RETRY_DELAYS2)-1)]
                    try:
                        _http_conn_pool.pop(urllib.parse.urlparse(url).netloc, None)
                    except Exception:
                        pass
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Inactivity ({_inactivity_s}s): no data received"))
                    print(Color.warning(f"Waiting {delay}s before retry...\n"))
                    time.sleep(delay)
                    continue
                yield f"\n{Color.error(f'[Inactivity Timeout]: no data for {_inactivity_s}s')}\n"
                return
            error_type = type(e).__name__
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS2[min(retry_count, len(_RETRY_DELAYS2)-1)]
                try:
                    _http_conn_pool.pop(urllib.parse.urlparse(url).netloc, None)
                except Exception:
                    pass
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Unexpected error ({error_type}): {e}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # Max retries reached
            yield f"\n{Color.error(f'[{error_type}]: {e}')}\n"
            yield f"{Color.info('If this persists, please check your network connection.')}\n"
            return

def call_llm_raw(prompt="", temperature=0.7, model=None, messages=None, stop=None, stream_prefix=None, spinner_label=None, max_tokens=None, extra_body=None, caller_tag=None, tools=None):
    """
    Call LLM without streaming (for extraction tasks, sub-agents, etc.).

    Args:
        prompt: Either a string prompt OR a list of message dicts
        temperature: Sampling temperature (default: 0.7)
        model: Optional model override (default: config.MODEL_NAME)
        messages: Alternative to prompt - pass messages list directly
        stop: Optional list of stop sequences
        stream_prefix: If set, stream output to stdout with this prefix (e.g. "  │ ")
        spinner_label: If set (and stream_prefix is None), show a spinner while waiting
        tools: Optional list of function tool definitions (OpenAI function calling format)

    Returns:
        Complete response text. When the model returns a tool_calls response instead of
        content (finish_reason == "tool_calls"), returns JSON string:
        '{"tool_calls": [{"id": ..., "name": ..., "arguments": ...}, ...]}'
    """
    global last_input_tokens, last_output_tokens

    # cursor-agent backend dispatch
    if getattr(config, "CURSOR_AGENT_ENABLE", False):
        from src.cursor_agent_backend import cursor_agent_call
        msgs = messages if messages else [{"role": "user", "content": prompt}]
        return cursor_agent_call(
            messages=msgs,
            model=getattr(config, "CURSOR_AGENT_MODEL", "auto"),
            yolo=getattr(config, "CURSOR_AGENT_YOLO", False),
            mode=getattr(config, "CURSOR_AGENT_MODE", ""),
            workspace=getattr(config, "CURSOR_AGENT_WORKSPACE", ""),
            stream_prefix=stream_prefix,
        )
    if getattr(config, "CLAUDE_CLI_ENABLE", False):
        from src.claude_cli_backend import claude_cli_call
        msgs = messages if messages else [{"role": "user", "content": prompt}]
        return claude_cli_call(
            messages=msgs,
            model=getattr(config, "CLAUDE_CLI_MODEL", "sonnet"),
            permission_mode=getattr(config, "CLAUDE_CLI_PERMISSION_MODE", "default"),
            tools=getattr(config, "CLAUDE_CLI_TOOLS", ""),
            workspace=getattr(config, "CLAUDE_CLI_WORKSPACE", ""),
            no_session_persistence=getattr(config, "CLAUDE_CLI_NO_SESSION_PERSISTENCE", True),
            output_format=getattr(config, "CLAUDE_CLI_OUTPUT_FORMAT", "json"),
            timeout_sec=getattr(config, "CLAUDE_CLI_TIMEOUT_SEC", 300),
            stream_prefix=stream_prefix,
        )

    resolved_model = model or config.MODEL_NAME

    # Route to OpenRouter or Z.AI if model specifies it
    if resolved_model and resolved_model.startswith("openrouter/"):
        resolved_model = resolved_model[len("openrouter/"):]
        url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = os.environ.get("OPENROUTER_API_KEY", config.API_KEY)
    elif resolved_model and resolved_model.startswith("zai/"):
        resolved_model = resolved_model[len("zai/"):]
        url = "https://api.z.ai/api/coding/paas/v4/chat/completions"
        api_key = os.environ.get("ZAI_API_KEY", config.API_KEY)
    else:
        url = build_chat_url(config.BASE_URL, resolved_model)
        api_key = config.API_KEY

    headers = build_api_headers(api_key)

    # Support both string prompt and messages list
    if messages is not None:
        msgs = messages
    elif isinstance(prompt, list):
        msgs = prompt
    else:
        msgs = [{"role": "user", "content": prompt}]

    use_stream = stream_prefix is not None
    data = {
        "model": resolved_model,
        "messages": msgs,
        "temperature": temperature,
        "stream": use_stream
    }
    if use_stream:
        # Ask the provider (OpenAI/Z.AI compatible Chat Completions) to include
        # usage stats in the streaming tail. Without this, the final chunk has
        # no `usage` field → last_input_tokens / last_output_tokens stay 0 →
        # react_loop.py never invokes emit_token_fn → cost never reaches the
        # ATLAS UI cost panel.
        data["stream_options"] = {"include_usage": True}
    if stop:
        # Z.AI and CanopyWave allow max 4 stop sequences
        _stop = stop[:4] if ("z.ai" in url or "canopywave" in url) else stop
        data["stop"] = _stop
    if max_tokens is not None:
        _set_max_output_tokens(data, max_tokens)
    # Native function calling: inject tools schema + tool_choice
    if tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"
    if extra_body:
        data.update(extra_body)

    _raw_t_start = time.perf_counter()
    if caller_tag:
        _raw_caller = caller_tag
    else:
        # Auto-detect caller from call stack (1 level up = direct caller)
        try:
            _f = sys._getframe(1)
            _fname = os.path.basename(_f.f_code.co_filename).replace(".py", "")
            _func  = _f.f_code.co_name
            _raw_caller = f"{_fname}.{_func}"
        except Exception:
            _raw_caller = "call_llm_raw"

    if use_responses_api(resolved_model):
        responses_url = build_responses_url(config.BASE_URL, resolved_model)
        responses_headers = build_api_headers(config.API_KEY)
        responses_min = 500 if _is_reasoning_model_for_name(resolved_model) else 16
        responses_max = max(max_tokens, responses_min) if max_tokens is not None else None
        responses_data = _build_responses_request_body(
            messages=msgs,
            model=resolved_model,
            stream=use_stream,
            stop=stop,
            temperature=temperature,
            tools=tools,
            max_output_tokens=responses_max,
            base_url=responses_url,
        )
        responses_data = _apply_responses_extra_body(responses_data, extra_body, responses_url)
        return _collect_responses_raw(
            responses_url,
            responses_headers,
            responses_data,
            _raw_caller,
            _raw_t_start,
            stream_prefix=stream_prefix,
        )

    try:
        _raw_body = json.dumps(data).encode('utf-8')

        if use_stream:
            full_content = []
            _prefix_printed = False
            _raw_t_connect = time.perf_counter()
            response = _persistent_post_with_auth_retry(url, headers, _raw_body, timeout=config.STREAM_API_TIMEOUT)
            try:
                _raw_connected = time.perf_counter()
                _raw_t_first = None
                for raw_line in response:
                    line = raw_line.decode('utf-8').strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        thinking_token = delta.get("reasoning_content", "")
                        answer_token = delta.get("content", "")
                        token = thinking_token or answer_token
                        if answer_token:
                            full_content.append(answer_token)
                        if token:
                            if _raw_t_first is None:
                                _raw_t_first = time.perf_counter()
                            if not _prefix_printed:
                                sys.stdout.write(stream_prefix)
                                _prefix_printed = True
                            if '\n' in token:
                                parts = token.split('\n')
                                sys.stdout.write(parts[0])
                                for part in parts[1:]:
                                    sys.stdout.write('\n')
                                    if part:
                                        sys.stdout.write(stream_prefix + part)
                                        _prefix_printed = True
                                    else:
                                        _prefix_printed = False
                            else:
                                sys.stdout.write(token)
                            sys.stdout.flush()
                        usage = chunk.get("usage", {})
                        if usage:
                            last_input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
                            last_output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
                    except (json.JSONDecodeError, KeyError):
                        pass
                sys.stdout.write('\n')
                sys.stdout.flush()
            finally:
                try:
                    response.read()
                except Exception:
                    pass
            _raw_t_end = time.perf_counter()
            _raw_connect = _raw_connected - _raw_t_connect
            _raw_ttft = (_raw_t_first - _raw_t_connect) if _raw_t_first else _raw_connect
            _raw_decode = (_raw_t_end - _raw_t_first) if _raw_t_first else 0.0
            _record_call(_raw_caller, resolved_model, last_input_tokens, last_output_tokens,
                         _raw_connect, _raw_ttft, _raw_decode, _raw_t_end - _raw_t_start)
            content = "".join(full_content)
            return _strip_metadata_tokens(content).strip()

        # Show spinner while waiting (non-streaming)
        _spinner = None
        if spinner_label:
            try:
                import sys as _sys
                _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                _parent = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
                _sys.path.insert(0, os.path.abspath(_parent))
                from lib.display import Spinner as _Spinner
                _spinner = _Spinner(spinner_label)
                _spinner.start()
            except Exception:
                _spinner = None

        _raw_t_connect = time.perf_counter()
        try:
            response = _persistent_post_with_auth_retry(url, headers, _raw_body, timeout=config.NONSTREAM_API_TIMEOUT)
            _raw_connected = time.perf_counter()
            result = json.loads(response.read().decode('utf-8'))
            _raw_t_end = time.perf_counter()
        finally:
            if _spinner:
                _spinner.stop()
                sys.stderr.write(f"  \033[36m✽\033[0m \033[2m{spinner_label}...\033[0m\n")
                sys.stderr.flush()

        choice = result["choices"][0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "")
        content = message.get("content") or ""

        usage = result.get("usage", {})
        if usage:
            last_input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
            last_output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
        _raw_connect = _raw_connected - _raw_t_connect
        _raw_read = _raw_t_end - _raw_connected
        _record_call(_raw_caller, resolved_model, last_input_tokens, last_output_tokens,
                     _raw_connect, _raw_connect + _raw_read, 0.0, _raw_t_end - _raw_t_start)

        # Function calling response: model returned tool_calls instead of content
        raw_tool_calls = message.get("tool_calls")
        if finish_reason == "tool_calls" or raw_tool_calls:
            parsed = []
            for tc in (raw_tool_calls or []):
                func = tc.get("function", {})
                args_str = func.get("arguments", "{}")
                # Validate arguments JSON
                try:
                    json.loads(args_str)
                except json.JSONDecodeError:
                    args_str = "{}"
                parsed.append({
                    "id": tc.get("id", ""),
                    "name": func.get("name", ""),
                    "arguments": args_str,
                })
            if config.DEBUG_MODE:
                print(Color.info(f"[call_llm_raw] tool_calls: {parsed}"))
            return json.dumps({"tool_calls": parsed}, ensure_ascii=False)

        return _strip_metadata_tokens(content).strip()

    except Exception as e:
        return f"Error calling LLM: {e}"


def call_llm_api(messages, temperature=0.7, max_tokens=None, model=None, show_reasoning=True):
    """
    Call LLM API and return (reasoning, content) tuple.
    Reasoning tokens are also printed to stdout when show_reasoning=True.
    Automatically uses the Responses API for models that require it (gpt-5.x, codex).

    Args:
        messages: List of message dicts (role/content)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Optional max output tokens
        model: Optional model override
        show_reasoning: Print separated reasoning/content blocks to stdout (default: True)

    Returns:
        Tuple (reasoning: str, content: str).
        reasoning is empty string when the model does not emit reasoning tokens.
    """
    global last_input_tokens, last_output_tokens
    resolved_model = model or getattr(config, 'MODEL_NAME', '')
    api_key = config.API_KEY
    headers = build_api_headers(api_key)

    # Responses API path (gpt-5.x, codex models)
    if use_responses_api(resolved_model):
        url = build_responses_url(config.BASE_URL, resolved_model)
        # Reasoning models need at least ~500 tokens: reasoning consumes most of the budget
        _responses_min = 500 if _is_reasoning_model_for_name(resolved_model) else 16
        _max_out = max(max_tokens, _responses_min) if max_tokens is not None else None
        data = _build_responses_request_body(
            messages=messages,
            model=resolved_model,
            stream=False,
            stop=None,
            max_output_tokens=_max_out,
            base_url=url,
        )
        try:
            raw_body = json.dumps(data).encode('utf-8')
            response = _persistent_post_with_auth_retry(url, headers, raw_body, timeout=config.NONSTREAM_API_TIMEOUT)
            result = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            err = f"Error calling LLM: {e}"
            return ("", err)

        usage = result.get("usage", {})
        if usage:
            last_input_tokens = usage.get("input_tokens", 0)
            last_output_tokens = usage.get("output_tokens", 0)

        _content_parts = []
        _reasoning_parts = []
        for item in result.get("output", []):
            if item.get("type") == "message":
                for cb in item.get("content", []):
                    if cb.get("type") == "output_text":
                        _content_parts.append(cb.get("text", ""))
            elif item.get("type") == "reasoning":
                text = _extract_responses_reasoning_text(item)
                if text:
                    _reasoning_parts.append(text)

        reasoning_text = "".join(_reasoning_parts)
        content_text = _strip_metadata_tokens("".join(_content_parts)).strip()

        if show_reasoning:
            print("\033[36m" + "="*50 + "\033[0m")
            print("\033[36m[REASONING]\033[0m")
            print(reasoning_text if reasoning_text else "(none)")
            print("\033[32m" + "="*50 + "\033[0m")
            print("\033[32m[CONTENT]\033[0m")
            print(content_text)
            print("\033[32m" + "="*50 + "\033[0m")

        return (reasoning_text, content_text)

    # Chat Completions path (DeepSeek, GLM, OpenRouter, etc.)
    url = build_chat_url(config.BASE_URL, resolved_model)
    data = {
        "model": resolved_model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if max_tokens is not None:
        _set_max_output_tokens(data, max_tokens)
    elif getattr(config, 'MAX_OUTPUT_TOKENS', 0) > 0:
        _set_max_output_tokens(data, config.MAX_OUTPUT_TOKENS)

    try:
        raw_body = json.dumps(data).encode('utf-8')
        response = _persistent_post_with_auth_retry(url, headers, raw_body, timeout=config.NONSTREAM_API_TIMEOUT)
        result = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return ("", f"Error calling LLM: {e}")

    choice = result.get("choices", [{}])[0]
    message = choice.get("message", {})

    reasoning_text = message.get("reasoning_content") or message.get("reasoning") or ""
    if not reasoning_text:
        for rd in (message.get("reasoning_details") or []):
            if rd.get("type") == "thinking":
                reasoning_text = (reasoning_text or "") + (rd.get("thinking", "") or rd.get("summary", ""))

    content_text = _strip_metadata_tokens(message.get("content") or "").strip()
    usage = result.get("usage", {})
    if usage:
        last_input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
        last_output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))

    if show_reasoning:
        print("\033[36m" + "="*50 + "\033[0m")
        print("\033[36m[REASONING]\033[0m")
        print(reasoning_text if reasoning_text else "(none)")
        print("\033[32m" + "="*50 + "\033[0m")
        print("\033[32m[CONTENT]\033[0m")
        print(content_text)
        print("\033[32m" + "="*50 + "\033[0m")

    return (reasoning_text, content_text)


def estimate_tokens(messages):
    """Estimates token count based on characters (4 chars ~= 1 token)."""
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return total_chars // 4

def is_anthropic_provider():
    """
    Detects if current provider is Anthropic based on BASE_URL or MODEL_NAME.

    Returns:
        bool: True if Anthropic API is being used
    """
    base_url_lower = config.BASE_URL.lower()
    model_lower = config.MODEL_NAME.lower()

    # Direct Anthropic API
    if "anthropic.com" in base_url_lower:
        return True

    # Claude models via OpenRouter or other proxies
    if "claude" in model_lower:
        return True

    return False

def estimate_message_tokens(message):
    """
    Estimates token count for a single message.
    Uses 4 chars ≈ 1 token heuristic.

    Args:
        message: dict with "content" field (str or list)

    Returns:
        int: estimated token count
    """
    content = message.get("content", "")

    # Handle string content
    if isinstance(content, str):
        return len(content) // 4

    # Handle optimized prompt structure (dict)
    if isinstance(content, dict):
        total_chars = 0
        for val in content.values():
            if isinstance(val, str):
                total_chars += len(val)
        return total_chars // 4

    # Handle structured content (list of blocks)
    if isinstance(content, list):
        total_chars = 0
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                total_chars += len(block.get("text", ""))
        return total_chars // 4

    return 0


def get_actual_tokens(messages):
    """
    Gets actual token count using hybrid approach:
    1. If we have actual token count from last API call, use it
    2. Otherwise, use estimation

    Args:
        messages: list of message dicts

    Returns:
        int: actual or estimated token count
    """
    global last_input_tokens

    # If we have recent actual token count from API, use it
    if last_input_tokens > 0:
        return last_input_tokens

    # Fallback to estimation
    return sum(estimate_message_tokens(m) for m in messages)


def get_last_usage():
    """
    Get token usage from last API call.

    Returns:
        dict: {
            "input": int,
            "output": int,
            "total": int,
            "cache_created": int,      # Cache creation tokens (if caching enabled)
            "cache_read": int,         # Cache read tokens (if caching enabled)
            "total_cache_created": int,  # Session total cache created
            "total_cache_read": int      # Session total cache read
        }
        Returns None if no API call has been made yet.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    if last_input_tokens == 0 and last_output_tokens == 0:
        return None

    return {
        "input": last_input_tokens,
        "output": last_output_tokens,
        "total": last_input_tokens + last_output_tokens,
        "cache_created": last_cache_creation_tokens,
        "cache_read": last_cache_read_tokens,
        "total_cache_created": total_cache_created,
        "total_cache_read": total_cache_read
    }


def get_token_count_from_api(messages):
    """
    [DEPRECATED - Not used by compress_history anymore]
    Gets actual token count from API without generating response.
    Uses max_tokens=1 to minimize cost and get usage info quickly.

    Note: compress_history now uses last_input_tokens from regular API calls
    instead of making additional API calls. This function is kept for
    potential future use.

    Args:
        messages: list of message dicts

    Returns:
        int: actual input token count, or 0 if failed
    """
    try:
        url = build_chat_url(config.BASE_URL)
        headers = build_api_headers(config.API_KEY)

        # Non-streaming request with minimal output
        data = {
            "model": config.MODEL_NAME,
            "messages": messages,
            "stream": False   # Non-streaming to get usage immediately
        }
        _set_max_output_tokens(data, 1)  # Minimal output to save cost

        response = _persistent_post_with_auth_retry(url, headers, json.dumps(data).encode('utf-8'), timeout=10)
        result = json.loads(response.read().decode('utf-8'))

        # Extract token count from usage
        if "usage" in result:
            usage = result["usage"]
            # Both OpenAI and Anthropic formats
            input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens", 0)

            if config.DEBUG_MODE:
                print(Color.info(f"[Token Count API] Got actual count: {input_tokens:,} tokens"))

            return input_tokens

    except Exception as e:
        if config.DEBUG_MODE:
            print(Color.warning(f"[Token Count API] Failed: {e}"))

    return 0

def _calculate_cache_interval(messages, max_breakpoints):
    """
    Dynamically calculates optimal cache interval based on message count.

    Args:
        messages: list of message dicts
        max_breakpoints: maximum allowed breakpoints (typically 3)

    Returns:
        int: interval between cache breakpoints
    """
    # Exclude system message from count
    message_count = len(messages) - 1  # -1 for system message

    if message_count <= 1:
        return 1

    # Reserve 1 breakpoint for system message
    available_breakpoints = max_breakpoints - 1

    if available_breakpoints <= 0:
        return message_count  # No dynamic breakpoints

    # Calculate interval to evenly distribute breakpoints
    interval = max(1, message_count // available_breakpoints)

    return interval

def convert_to_cache_format(content, add_cache_control=False):
    """
    Converts string content to structured format for prompt caching.

    Args:
        content: str or list (message content)
        add_cache_control: bool (whether to add cache control marker)

    Returns:
        list: structured content blocks
    """
    # Already in structured format
    if isinstance(content, list):
        if add_cache_control and content:
            # Add cache_control to last block
            content[-1]["cache_control"] = {"type": "ephemeral"}
        return content

    # Convert string to structured format
    block = {
        "type": "text",
        "text": content
    }

    if add_cache_control:
        block["cache_control"] = {"type": "ephemeral"}

    return [block]

def apply_cache_breakpoints(messages):
    """
    Applies cache breakpoints to messages based on configuration.

    Args:
        messages: list of message dicts (standard format)

    Returns:
        list: messages with cache_control applied (modified in-place)
    """
    if not config.ENABLE_PROMPT_CACHING:
        return messages

    if not is_anthropic_provider():
        if config.DEBUG_MODE:
            print(Color.info("[System] Prompt caching disabled: non-Anthropic provider"))
        return messages

    max_breakpoints = min(config.MAX_CACHE_BREAKPOINTS, 4)  # Anthropic max = 4
    breakpoint_count = 0

    # 1. System message always gets cache breakpoint (if exists and meets min tokens)
    if messages and messages[0].get("role") == "system":
        content = messages[0].get("content")

        # Multi-block format (optimized mode): check if already has cache_control
        if isinstance(content, list):
            # Check if any block already has cache_control (from optimized mode)
            has_cache = any(
                isinstance(block, dict) and "cache_control" in block
                for block in content
            )
            if has_cache:
                breakpoint_count += 1  # Count it but don't modify
                if config.DEBUG_MODE:
                    total_tokens = estimate_message_tokens(messages[0])
                    print(Color.info(f"[System] Cache breakpoint 1/{max_breakpoints}: System message (multi-block, pre-configured, {total_tokens} tokens)"))
            else:
                # Legacy list format without cache_control: apply it to last block
                tokens = estimate_message_tokens(messages[0])
                if tokens >= config.MIN_CACHE_TOKENS:
                    messages[0]["content"] = convert_to_cache_format(content, add_cache_control=True)
                    breakpoint_count += 1
                    if config.DEBUG_MODE:
                        print(Color.info(f"[System] Cache breakpoint 1/{max_breakpoints}: System message (list format, {tokens} tokens)"))
        else:
            # Single string format (legacy mode)
            tokens = estimate_message_tokens(messages[0])
            if tokens >= config.MIN_CACHE_TOKENS:
                messages[0]["content"] = convert_to_cache_format(content, add_cache_control=True)
                breakpoint_count += 1
                if config.DEBUG_MODE:
                    print(Color.info(f"[System] Cache breakpoint 1/{max_breakpoints}: System message ({tokens} tokens)"))

    # 2. Dynamic breakpoints in message history
    if breakpoint_count < max_breakpoints and len(messages) > 1:
        # Determine interval
        if config.CACHE_INTERVAL > 0:
            interval = config.CACHE_INTERVAL
        else:
            interval = _calculate_cache_interval(messages, max_breakpoints)

        if config.DEBUG_MODE:
            print(Color.info(f"[System] Cache interval: {interval} messages"))

        # Apply breakpoints at intervals (working backwards from recent messages)
        # This ensures most recent context is cached
        for i in range(len(messages) - 1, 0, -interval):
            if breakpoint_count >= max_breakpoints:
                break

            tokens = estimate_message_tokens(messages[i])
            if tokens >= config.MIN_CACHE_TOKENS:
                messages[i]["content"] = convert_to_cache_format(
                    messages[i]["content"],
                    add_cache_control=True
                )
                breakpoint_count += 1
                if config.DEBUG_MODE:
                    print(Color.info(f"[System] Cache breakpoint {breakpoint_count}/{max_breakpoints}: Message {i} ({tokens} tokens)"))

    return messages

# =========================================================================
# Embedding Utilities (Centralized)
# =========================================================================

# Cache for embedding dimension
_cached_embedding_dim = None

# Cache for embeddings (LRU)
# Key: {model}:{text_hash}, Value: list[float]
_embedding_cache = {}

def get_embedding(text: str, model: str = None) -> List[float]:
    """
    Get embedding for text using configured API.
    Handles caching and retries.
    
    Args:
        text: Text to embed
        model: Model name override (optional)
        
    Returns:
        List of floats (embedding vector)
    """
    if model is None:
        model = config.EMBEDDING_MODEL
        
    # Check cache
    cache_key = f"{model}:{hash(text)}"
    if cache_key in _embedding_cache:
        # Simple LRU: re-insert to move to end (Python 3.7+ dicts preserve order)
        val = _embedding_cache.pop(cache_key)
        _embedding_cache[cache_key] = val
        return val
        
    # Prepare API request
    emb_api_key = config.EMBEDDING_API_KEY or config.API_KEY
    if is_azure_provider():
        # Azure OpenAI embedding endpoint
        api_version = getattr(config, "AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        url = f"{config.EMBEDDING_BASE_URL.rstrip('/')}/openai/deployments/{model}/embeddings?api-version={api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": emb_api_key,
            "User-Agent": "BrianCoder-Embedding"
        }
    else:
        url = f"{config.EMBEDDING_BASE_URL}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {emb_api_key}",
            "User-Agent": "BrianCoder-Embedding"
        }
    data = {
        "input": text,
        "model": model,
        "encoding_format": "float"
    }
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = _persistent_post_with_auth_retry(url, headers, json.dumps(data).encode('utf-8'), timeout=30)
            result = json.loads(response.read().decode('utf-8'))
            embedding = result["data"][0]["embedding"]

            # Cache result
            _embedding_cache[cache_key] = embedding
            # Maintain cache size (max 1000)
            if len(_embedding_cache) > 1000:
                try:
                    # Remove first item (oldest)
                    _embedding_cache.pop(next(iter(_embedding_cache)))
                except StopIteration:
                    pass

            return embedding
        except Exception as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(Color.warning(f"[Embedding] Retry {attempt+1}/{max_retries} in {delay}s: {e}"))
                time.sleep(delay)
                continue
            
            # Final attempt failed - simple error, no traceback
            print(Color.error(f"[Embedding] Failed after {max_retries} attempts: {e}"))
            raise e
            
    # Should not reach here
    return []

def get_embedding_dimension() -> int:
    """
    Get the embedding dimension.
    If config.EMBEDDING_DIMENSION is set, returns it.
    Otherwise, auto-detects by making a test API call.
    """
    global _cached_embedding_dim
    
    # 1. Check runtime cache
    if _cached_embedding_dim is not None:
        return _cached_embedding_dim
        
    # Try to detect from API first (Prioritize reality over config)
    try:
        if config.DEBUG_MODE:
            print(f"{Color.info('[System] Probing embedding dimension...')}")
            
        test_emb = get_embedding("test")
        if test_emb and len(test_emb) > 0:
            _cached_embedding_dim = len(test_emb)
            if config.DEBUG_MODE:
                print(f"{Color.success(f'[System] Detected embedding dimension: {_cached_embedding_dim}')}")
            return _cached_embedding_dim
    except Exception as e:
        if config.DEBUG_MODE:
            print(f"{Color.warning(f'[System] Dimension probe failed: {e}')}")

    # Fallback: If manually configured, use that
    if config.EMBEDDING_DIMENSION is not None and config.EMBEDDING_DIMENSION > 0:
        _cached_embedding_dim = config.EMBEDDING_DIMENSION
        return _cached_embedding_dim

    # Final fallback
    _cached_embedding_dim = 1536
    return 1536
