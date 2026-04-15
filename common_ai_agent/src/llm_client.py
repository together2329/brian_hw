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


def get_active_model() -> str:
    """Return the display name for the currently active LLM backend.

    When cursor-agent is enabled, returns "Cursor (<model>)" where <model>
    is the human-readable label from cursor-agent's init event (e.g. "Auto",
    "Sonnet 4.6 1M"). Falls back to config.MODEL_NAME for the normal path.
    """
    if getattr(config, "CURSOR_AGENT_ENABLE", False):
        try:
            from src.cursor_agent_backend import last_cursor_model
            label = last_cursor_model or getattr(config, "CURSOR_AGENT_MODEL", "auto")
        except Exception:
            label = getattr(config, "CURSOR_AGENT_MODEL", "auto")
        return f"Cursor ({label})"
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


def _is_reasoning_model() -> bool:
    """Heuristic: does the current model produce reasoning/thinking tokens?"""
    name = getattr(config, 'MODEL_NAME', '').lower()
    return any(k in name for k in ('glm', 'deepseek', 'qwq', 'r1', 'reasoning', 'o1', 'o3', 'o4')) or \
           (name.startswith('gpt-5') and 'codex' not in name)


def _is_openai_gpt_model(model_name: str = None) -> bool:
    """Check if the model is an OpenAI GPT model.

    Pattern: *gpt* — matches gpt-4, gpt-4o, gpt-5.1, gpt-5.1-codex, etc.
    """
    name = (model_name or getattr(config, 'MODEL_NAME', '')).lower()
    if '/' in name:
        name = name.split('/')[-1]
    return 'gpt' in name or name.startswith('o1') or name.startswith('o3') or name.startswith('o4')


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
        conn.request("GET", base_path, headers={
            "Authorization": f"Bearer {config.API_KEY}",
            "Connection": "keep-alive",
        })
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
    req_headers["Connection"] = "keep-alive"

    global _last_post_reused
    for attempt in range(2):
        conn = _http_conn_pool.get(host)
        _was_alive = conn is not None and conn.sock is not None
        if conn is None:
            conn = _make_https_conn(host, timeout=timeout)
            _http_conn_pool[host] = conn
        try:
            conn.request("POST", path, body=body, headers=req_headers)
            resp = conn.getresponse()
            if resp.status >= 400:
                body_bytes = resp.read()  # fully drain before raising
                raise _PersistentHTTPError(url, resp.status, resp.reason, body_bytes)
            _last_post_reused = _was_alive and attempt == 0
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


def use_responses_api() -> bool:
    """Check if the Responses API should be used instead of Chat Completions.

    Enabled via USE_RESPONSES_API=true in .config.
    Used for Azure gpt-5-codex models and OpenAI codex models that require the
    /responses endpoint instead of /chat/completions.
    """
    return getattr(config, "USE_RESPONSES_API", False)


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

    Pattern: *gpt*codex* — e.g. gpt-5.1-codex → /v1/responses
    """
    name = (model_name or getattr(config, 'MODEL_NAME', '')).lower()
    if '/' in name:
        name = name.split('/')[-1]
    return 'gpt' in name and 'codex' in name


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


def _to_fc_id(call_id: str) -> str:
    """Convert chat completions call ID (e.g. 'call_abc123') to Responses API format ('fc_abc123')."""
    if not call_id:
        return "fc_" + _generate_id()
    if call_id.startswith("call_"):
        return "fc_" + call_id[5:]
    if call_id.startswith("fc_"):
        return call_id
    return "fc_" + call_id


def _generate_id() -> str:
    """Generate a short random ID for function calls."""
    import random, string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))


def _messages_to_responses_input(messages: list) -> list:
    """Convert chat completions messages to Responses API input format.

    Chat Completions:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

    Responses API:
        [{"role": "system", "content": [{"type": "input_text", "text": "..."}]},
         {"role": "user",   "content": [{"type": "input_text", "text": "..."}]}]
    """
    result = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Skip tool messages — Responses API handles function_call_output differently
        if role == "tool":
            # Convert tool result to function_call_output
            fc_id = _to_fc_id(msg.get("tool_call_id", ""))
            result.append({
                "type": "function_call_output",
                "call_id": fc_id,
                "output": str(content),
            })
            continue

        # Handle assistant messages with tool_calls
        if role == "assistant" and msg.get("tool_calls"):
            # Add the assistant text content first
            if content:
                result.append({
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": str(content)}],
                })
            # Add function calls with fc_ prefixed IDs
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                fc_id = _to_fc_id(tc.get("id", ""))
                result.append({
                    "type": "function_call",
                    "id": fc_id,
                    "call_id": fc_id,
                    "name": func.get("name", ""),
                    "arguments": func.get("arguments", "{}"),
                })
            continue

        # Handle reasoning items (required for reasoning models like GPT-5)
        # These may appear as assistant messages with reasoning content
        if role == "assistant" and isinstance(content, str) and content.startswith("__reasoning__:"):
            # Pass through as reasoning item
            result.append({
                "type": "reasoning",
                "summary": [],
                "content": [{"type": "reasoning_text", "text": content[len("__reasoning__:"):]},
            ]})
            continue

        # Regular messages (system, user, assistant)
        content_type = "input_text" if role in ("system", "user") else "output_text"
        entry = {
            "role": role,
            "content": [{"type": content_type, "text": str(content)}],
        }
        result.append(entry)

    return result


def _build_responses_request(data: dict, resolved_model: str) -> dict:
    """Build a Responses API request body from a chat completions data dict.

    Converts:
        messages → input
        max_completion_tokens → max_output_tokens
        tools (function calling) → tools (Responses API format)
    """
    messages = data.get("messages", [])
    resp_data = {
        "model": resolved_model,
        "input": _messages_to_responses_input(messages),
    }

    # Transfer max tokens
    max_val = data.get("max_completion_tokens") or data.get("max_tokens")
    if max_val:
        resp_data["max_output_tokens"] = max_val

    # Transfer temperature
    if "temperature" in data:
        resp_data["temperature"] = data["temperature"]

    # Transfer stream
    if data.get("stream"):
        resp_data["stream"] = True

    # Convert tools from chat completions format to Responses API format
    if "tools" in data:
        resp_tools = []
        for tool in data["tools"]:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                resp_tool = {
                    "type": "function",
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                }
                resp_tools.append(resp_tool)
        if resp_tools:
            resp_data["tools"] = resp_tools

    return resp_data


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

    - Azure OpenAI: endpoint + /openai/deployments/{deployment}/responses?api-version=...
    - Standard (OpenAI): base_url + /responses
    """
    if is_azure_provider():
        deployment = model or config.MODEL_NAME
        api_version = getattr(config, "AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        endpoint = base_url.rstrip("/")
        return f"{endpoint}/openai/deployments/{deployment}/responses?api-version={api_version}"
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
    """
    instructions = None
    input_items = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Handle tool messages — pass through as-is
        if role == "tool":
            input_items.append({
                "type": "function_call_output",
                "call_id": msg.get("tool_call_id", ""),
                "output": str(content),
            })
            continue

        # Handle assistant messages with tool_calls
        if role == "assistant" and msg.get("tool_calls"):
            # Emit function_call items for each tool call
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                input_items.append({
                    "type": "function_call",
                    "call_id": tc.get("id", ""),
                    "name": func.get("name", ""),
                    "arguments": func.get("arguments", "{}"),
                })
            # If there's also content, add it as a message
            if content:
                input_items.append({
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": str(content)}],
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

            # Handle content as list of blocks (structured content from caching)
            if isinstance(content, list):
                converted_blocks = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") in ("text", "input_text", "output_text"):
                            converted_blocks.append({
                                "type": content_type,
                                "text": block.get("text", ""),
                            })
                        else:
                            converted_blocks.append(block)
                    else:
                        converted_blocks.append({"type": content_type, "text": str(block)})
                input_items.append({"role": role, "content": converted_blocks})
            else:
                input_items.append({
                    "role": role,
                    "content": [{"type": content_type, "text": str(content)}],
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
) -> dict:
    """
    Build a complete Responses API request body from Chat Completions-style messages.

    Handles the conversion from messages[] to input[] + instructions automatically.
    """
    input_items, instructions = _convert_messages_to_responses_input(messages)

    data = {
        "model": model,
        "input": input_items,
        "store": False,
        "stream": stream,
    }

    if instructions:
        data["instructions"] = instructions

    if temperature is not None:
        data["temperature"] = temperature

    if stop:
        data["stop"] = stop

    if max_output_tokens is not None:
        data["max_output_tokens"] = max_output_tokens

    if tools:
        # Convert Chat Completions tool format to Responses API format
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
            else:
                responses_tools.append(tool)
        data["tools"] = responses_tools
        data["tool_choice"] = "auto"

    return data


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

    if extra_headers:
        headers.update(extra_headers)

    return headers


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

    if use_responses_api():
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
        # Z.AI allows max 4 stop sequences
        _stop = stop[:4] if "z.ai" in url else stop
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

    _RETRY_DELAYS = [5, 10, 20, 40, 80]
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
            response = _persistent_post(url, headers, _body, timeout=config.STREAM_API_TIMEOUT)
            global _active_stream_response
            _active_stream_response = response
            _inactivity_s = getattr(config, 'STREAM_INACTIVITY_TIMEOUT', 120)
            _last_data = [time.time()]
            _wd_stop, _wd_triggered = _make_stream_watchdog(response, _inactivity_s, _last_data)
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
                    if event_type == "response.reasoning.delta":
                        reasoning_text = event_json.get("delta", "")
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
                                _args_str = tc_info["arguments"] or "{}"
                                try:
                                    json.loads(_args_str)
                                except json.JSONDecodeError:
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
                                        f'{k}={json.dumps(v)}' for k, v in tc_args.items()
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
                    if _cached > 0:
                        last_cache_read_tokens = _cached
                        total_cache_read += _cached

                    _total = input_tokens + output_tokens
                    if _total > 0:
                        get_rate_limiter().update_actual_usage(_total)

                    if config.DEBUG_MODE:
                        total_tokens = input_tokens + output_tokens
                        print(f"\n{Color.info('[Token Usage (Responses API)]')}")
                        print(f"{Color.info(f'  Input: {input_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Output: {output_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Total: {total_tokens:,} tokens')}")
                        if _cached > 0:
                            print(f"{Color.info(f'  Cached: {_cached:,} tokens')}")
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
            zai = _parse_zai_error(error_body)
            _zai_msg = zai["message"]
            _zai_code = zai["code"]
            _zai_type = zai["type"]
            _zai_reset = zai["reset_time"]

            if zai["is_account_locked"] or zai["is_balance_exhausted"]:
                print(Color.error(f"\n  LLM API Error [HTTP {e.code}]: {_zai_msg}"))
                yield f"\n{Color.error(f'[HTTP {e.code}] {_zai_msg}')}\n"
                return

            is_retryable = (zai["is_retryable"] or e.code == 429 or
                          (500 <= e.code < 600))
            if is_retryable and retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] HTTP {e.code}. Waiting {delay}s...\n"))
                time.sleep(delay)
                continue

            yield f"\n{Color.error(f'[HTTP Error {e.code}]: {e.reason}')}\n"
            try:
                error_json = json.loads(error_body)
                if 'error' in error_json:
                    err_info = error_json['error']
                    if isinstance(err_info, dict):
                        err_msg = err_info.get('message', '')
                    else:
                        err_msg = str(err_info)
                    if err_msg:
                        yield f"{Color.error(f'  {err_msg}')}\n"
            except Exception:
                if error_body:
                    yield f"{Color.error(f'  {error_body[:300]}')}\n"
            return

        except (socket.timeout, urllib.error.URLError, ssl.SSLError) as e:
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                err_msg = str(e)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] {err_msg}. Waiting {delay}s...\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[Connection Error]: {e}')}\n"
            return

        except Exception as e:
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] {type(e).__name__}: {e}. Waiting {delay}s...\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[{type(e).__name__}]: {e}')}\n"
            return

    return  # all retries exhausted


def _make_stream_watchdog(response, inactivity_s: int, last_data_ref: list):
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
            if elapsed >= inactivity_s:
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
            for c in item.get("content", []):
                text = c.get("text", "")
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
                        f'{k}={json.dumps(v)}' for k, v in tc_args.items()
                    )
                    yield f"\nAction: {tc_name}({args_formatted})\n"
                except (json.JSONDecodeError, AttributeError):
                    pass


def _execute_responses_stream(url: str, headers: Dict, data: Dict, messages: List, native_mode: bool = False):
    """
    Execute streaming request for the OpenAI Responses API (/v1/responses).

    The Responses API uses a different SSE event format:
      - event: response.output_text.delta  → content text
      - event: response.reasoning.delta    → reasoning text
      - event: response.function_call_arguments.delta → tool call args
      - event: response.completed          → final response with usage
      - event: response.done               → stream end

    Yields the same tuple format as _execute_streaming_request so the
    rest of the pipeline doesn't need to change.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    _RETRY_DELAYS = [5, 10, 20, 40, 80]
    max_retries = len(_RETRY_DELAYS) + 1

    for retry_count in range(max_retries):
        global _stream_cancelled
        if _stream_cancelled:
            _stream_cancelled = False
            return

        _yielded_something = False
        _pending_tool_calls: Dict[int, Dict] = {}
        _wd_stop, _wd_triggered = None, [False]

        try:
            _body = json.dumps(data).encode('utf-8')
            if getattr(config, 'DEBUG_MODE', False):
                _body_preview = _body.decode('utf-8')[:1500]
                print(Color.info(f"\n[Responses API Stream] URL: {url}"))
                print(Color.info(f"[Responses API Stream] Body (first 1500 chars):\n{_body_preview}\n"))
            response = _persistent_post(url, headers, _body, timeout=config.STREAM_API_TIMEOUT)
            global _active_stream_response
            _active_stream_response = response
            _inactivity_s = getattr(config, 'STREAM_INACTIVITY_TIMEOUT', 120)
            _last_data = [time.time()]
            _wd_stop, _wd_triggered = _make_stream_watchdog(response, _inactivity_s, _last_data)

            try:
                _current_event = ""
                for line in response:
                    _last_data[0] = time.time()
                    line = line.decode('utf-8').strip()

                    # Track SSE event type
                    if line.startswith("event: "):
                        _current_event = line[7:].strip()
                        continue
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # ── Content text delta ──
                    if _current_event in ("response.output_text.delta",):
                        text = chunk.get("delta", "")
                        if text:
                            yield text
                            _yielded_something = True

                    # ── Reasoning delta ──
                    elif _current_event in ("response.reasoning.delta",):
                        text = chunk.get("delta", "")
                        if text:
                            yield ("reasoning", text)
                            _yielded_something = True

                    # ── Function call name ──
                    elif _current_event == "response.function_call_arguments.delta":
                        # Arguments come as fragments — accumulate
                        pass

                    # ── Completed: extract usage and function calls ──
                    elif _current_event in ("response.completed", "response.done"):
                        resp_obj = chunk.get("response", chunk)

                        # Extract usage
                        usage = resp_obj.get("usage", {})
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

                        # Extract cache token usage for Responses API
                        if usage and config.ENABLE_PROMPT_CACHING:
                            cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
                            cache_read_tokens = usage.get("cache_read_input_tokens", 0)
                            _ptd = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
                            cache_read_tokens = cache_read_tokens or _ptd.get("cached_tokens", 0)
                            if cache_creation_tokens > 0 or cache_read_tokens > 0:
                                last_cache_creation_tokens = cache_creation_tokens
                                last_cache_read_tokens = cache_read_tokens
                                total_cache_created += cache_creation_tokens
                                total_cache_read += cache_read_tokens

                        # Extract function calls from output
                        output_items = resp_obj.get("output", [])
                        _func_calls = []
                        for item in output_items:
                            if item.get("type") == "function_call":
                                _func_calls.append({
                                    "id": item.get("call_id", item.get("id", "")),
                                    "name": item.get("name", ""),
                                    "arguments": item.get("arguments", "{}"),
                                })

                        if _func_calls:
                            if native_mode:
                                yield ("native_tool_calls", _func_calls)
                            else:
                                for fc in _func_calls:
                                    tc_name = fc["name"]
                                    tc_args_str = fc["arguments"]
                                    if tc_name and tc_args_str:
                                        try:
                                            tc_args = json.loads(tc_args_str)
                                            args_formatted = ", ".join(
                                                f'{k}={json.dumps(v)}' for k, v in tc_args.items()
                                            )
                                            yield f"\nAction: {tc_name}({args_formatted})\n"
                                        except (json.JSONDecodeError, AttributeError):
                                            pass
                            _yielded_something = True

                # Empty response retry
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

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode('utf-8')
            except Exception:
                pass
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Responses API error: HTTP {e.code}: {e.reason}. Waiting {delay}s...\n"))
                if error_body:
                    print(Color.warning(f"  Error body: {error_body[:500]}\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[Responses API Error] HTTP {e.code}: {e.reason}')}\n"
            if error_body:
                yield f"{Color.error(f'  {error_body[:500]}')}\n"
            return
        except Exception as e:
            if retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] Responses API error: {e}. Waiting {delay}s...\n"))
                time.sleep(delay)
                continue
            yield f"\n{Color.error(f'[Responses API Error]: {e}')}\n"
            return


def _execute_streaming_request(url: str, headers: Dict, data: Dict, messages: List, native_mode: bool = False):
    """
    Execute streaming request with retry logic.
    Internal helper for chat_completion functions.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    _RETRY_DELAYS = [5, 10, 20, 40, 80]  # inactivity/timeout backoff (seconds)
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

        try:
            _body = json.dumps(data).encode('utf-8')
            response = _persistent_post(url, headers, _body, timeout=config.STREAM_API_TIMEOUT)
            global _active_stream_response
            _active_stream_response = response
            _inactivity_s = getattr(config, 'STREAM_INACTIVITY_TIMEOUT', 120)
            _last_data = [time.time()]
            _wd_stop, _wd_triggered = _make_stream_watchdog(response, _inactivity_s, _last_data)
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
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_str)

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

                                # Reasoning tokens (DeepSeek, GLM etc.)
                                reasoning = delta.get("reasoning") or delta.get("reasoning_content", "")
                                content = delta.get("content", "")

                                # Bleed fix: GLM-4.7 can emit reasoning tail and content start
                                # in the same delta chunk. Merge into reasoning when both are
                                # present and content begins mid-sentence.
                                if reasoning and content:
                                    first_char = content.lstrip()[:1]
                                    if first_char and (first_char.islower() or first_char.isdigit() or first_char in ',;:'):
                                        reasoning = reasoning + content
                                        content = ""

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
                                tool_calls = delta.get("tool_calls", [])
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
                                _args_str = tc_info["arguments"] or "{}"
                                try:
                                    json.loads(_args_str)
                                except json.JSONDecodeError:
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
                                        f'{k}={json.dumps(v)}' for k, v in tc_args.items()
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

                    if config.DEBUG_MODE:
                        total_tokens = input_tokens + output_tokens
                        print(f"\n{Color.info('[Token Usage]')}")
                        print(f"{Color.info(f'  Input: {input_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Output: {output_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Total: {total_tokens:,} tokens')}")
                        if _cached > 0:
                            print(f"{Color.info(f'  Cached: {_cached:,} tokens (prompt cache hit)')}")
                        print()

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

            # ── Generic retryable: 429 or 5xx ──
            is_retryable = e.code == 429 or (500 <= e.code < 600)
            if is_retryable and retry_count < max_retries - 1:
                delay = _RETRY_DELAYS[retry_count]
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries - 1}] HTTP {e.code}: {e.reason}"))
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
        response = _persistent_post(url, headers, _body, timeout=config.NONSTREAM_API_TIMEOUT)
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

    resolved_model = model or config.MODEL_NAME

    # ── Responses API path ──
    if use_responses_api():
        url = build_responses_url(config.BASE_URL, resolved_model)
        api_key = config.API_KEY
        headers = build_api_headers(api_key)
        data = _build_responses_request_body(
            messages=processed_messages,
            model=resolved_model,
            stream=False,
            stop=stop,
            max_output_tokens=compute_safe_max_tokens() if config.MAX_OUTPUT_TOKENS > 0 else None,
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
            response = _persistent_post(url, headers, _body, timeout=config.NONSTREAM_API_TIMEOUT)
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
                _reasoning_parts.append(item.get("summary", ""))

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
        # Z.AI allows max 4 stop sequences
        _stop = stop[:4] if "z.ai" in url else stop
        data["stop"] = _stop
    if config.MAX_OUTPUT_TOKENS > 0:
        _set_max_output_tokens(data, compute_safe_max_tokens())

    # ── Responses API routing (gpt-5.1-codex etc.) ──
    if is_responses_api_model(resolved_model):
        url = build_responses_url(config.BASE_URL, resolved_model)
        data = _build_responses_request(data, resolved_model)

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
        response = _persistent_post(url, headers, _body, timeout=config.NONSTREAM_API_TIMEOUT)
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

    # Yield reasoning first (if present)
    reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""

    # Yield content line-by-line
    content = msg.get("content") or ""
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

    # Debug output (mirrors streaming debug labels so DEBUG_MODE: continue works correctly)
    if config.DEBUG_MODE:
        if reasoning:
            sys.stdout.write(f"\n\033[36m[reasoning]\033[0m {reasoning}\n")
            sys.stdout.flush()
        if content:
            sys.stdout.write(f"\n\033[32m[content]\033[0m {content}\n")
            sys.stdout.flush()

    if reasoning:
        for line in reasoning.splitlines(keepends=True):
            yield ("reasoning", line)

    if content:
        for line in content.splitlines(keepends=True):
            yield line
        # Ensure final newline
        if not content.endswith('\n'):
            yield '\n'


def chat_completion_stream(messages, stop=None, model=None, skip_rate_limit=False, caller_tag=None, suppress_spinner=False, tools=None):
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

    _t_fn_start = time.time()  # track pre-connect setup time

    # Non-streaming mode: fetch full response then yield line-by-line
    if not config.ENABLE_STREAMING:
        _ns_delays = [5, 10, 20, 40, 80]
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
                is_retryable = e.code == 429 or (500 <= e.code < 600)
                if is_retryable and _ns_retry < _ns_max - 1:
                    delay = _ns_delays[_ns_retry]
                    print(Color.warning(f"\n[Retry {_ns_retry + 1}/{_ns_max - 1}] HTTP {e.code}: {e.reason}. Waiting {delay}s...\n"))
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
    if use_responses_api():
        url = build_responses_url(config.BASE_URL, resolved_model)
        headers = build_api_headers(api_key)
        data = _build_responses_request_body(
            messages=processed_messages,
            model=resolved_model,
            stream=True,
            stop=stop,
            tools=tools,
            max_output_tokens=compute_safe_max_tokens() if config.MAX_OUTPUT_TOKENS > 0 else None,
        )

        if config.DEBUG_MODE:
            tag = f" ({caller_tag})" if caller_tag else ""
            print(Color.info(f"\n[Request Debug (Responses API)]{tag}"))
            print(Color.info(f"  URL: {url}"))
            print(Color.info(f"  Model: {resolved_model}"))
            print(Color.info(f"  Messages count: {len(processed_messages)}"))
            print(Color.info(f"  API: Responses (/responses)"))

        yield from _execute_streaming_request_responses(url, headers, data, processed_messages, native_mode=bool(tools))
        return

    # ── Chat Completions path (default) ──
    data = {
        "model": resolved_model,
        "messages": processed_messages,
        "stream": True,
        "stream_options": {"include_usage": True}  # Request usage data in streaming (OpenAI)
    }

    if stop:
        # Z.AI allows max 4 stop sequences
        _stop = stop[:4] if "z.ai" in url else stop
        data["stop"] = _stop

    if config.MAX_OUTPUT_TOKENS > 0:
        _set_max_output_tokens(data, compute_safe_max_tokens())

    # Native tool call support: inject tools schema when provided
    if tools:
        # Strip strict mode for non-OpenAI providers (GLM, DeepSeek, etc.)
        # that may not support it in Chat Completions format.
        # Responses API (_build_responses_request) handles strict separately.
        if not is_responses_api_model(resolved_model):
            _is_openai = "openai.com" in url
            if not _is_openai:
                tools = _strip_strict_from_tools(tools)
        data["tools"] = tools
        data["tool_choice"] = "auto"

    # ── Responses API routing (gpt-5.1-codex etc.) ──
    if is_responses_api_model(resolved_model):
        url = build_responses_url(config.BASE_URL, resolved_model)
        data = _build_responses_request(data, resolved_model)
        if config.DEBUG_MODE:
            tag = f" ({caller_tag})" if caller_tag else ""
            print(Color.info(f"\n[Request Debug - Responses API]{tag}"))
            print(Color.info(f"  URL: {url}"))
            print(Color.info(f"  Model: {resolved_model}"))
        yield from _execute_responses_stream(url, headers, data, messages, native_mode=bool(tools))
        return

    # Debug: Log request details
    if config.DEBUG_MODE:
        tag = f" ({caller_tag})" if caller_tag else ""
        print(Color.info(f"\n[Request Debug]{tag}"))
        print(Color.info(f"  URL: {url}"))
        print(Color.info(f"  Model: {resolved_model}"))
        print(Color.info(f"  Messages count: {len(processed_messages)}"))

        # Estimate total tokens
        total_chars = sum(len(str(m.get('content', ''))) for m in processed_messages)
        estimated_tokens = total_chars // 4
        print(Color.info(f"  Estimated input tokens: {estimated_tokens:,}"))

        # Check if structured content (caching applied)
        has_structured = any(isinstance(m.get('content'), list) for m in processed_messages)
        print(Color.info(f"  Structured content (caching): {has_structured}"))

        # Show first message structure
        if processed_messages:
            first_content = processed_messages[0].get('content', '')
            if isinstance(first_content, list):
                print(Color.info(f"  First message: [list with {len(first_content)} blocks]"))
            else:
                print(Color.info(f"  First message: [string, {len(str(first_content))} chars]"))
        
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
    _RETRY_DELAYS2 = [5, 10, 20, 40, 80]  # backoff for all retryable errors
    max_retries = len(_RETRY_DELAYS2) + 1
    _fallback_used = False  # True after switching to SECONDARY_MODEL

    for retry_count in range(max_retries):
        # Local state for label tracking (resets each retry)
        _reasoning_started = False
        _content_label_printed = False
        _debug_line_buf = ""
        _debug_in_think = False
        _wd_stop, _wd_triggered = None, [False]  # init before try so except can always reference

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
            response = _persistent_post(url, headers, _post_body, timeout=config.STREAM_API_TIMEOUT)
            _inactivity_s = getattr(config, 'STREAM_INACTIVITY_TIMEOUT', 120)
            _last_data = [time.time()]
            _wd_stop, _wd_triggered = _make_stream_watchdog(response, _inactivity_s, _last_data)
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

                                # Reasoning tokens (DeepSeek, GLM etc.)
                                reasoning = delta.get("reasoning") or delta.get("reasoning_content", "")
                                content = delta.get("content", "")

                                # Streaming bleed fix: when both reasoning_content and content
                                # arrive in the same delta, the content is always a bleed-over
                                # from the reasoning tail (observed consistently on GLM-4.7).
                                # Real content starts in its own delta (reasoning field absent).
                                if reasoning and content:
                                    reasoning = reasoning + content
                                    content = ""

                                # Handle reasoning and content for debug display
                                if config.DEBUG_MODE:
                                    if reasoning:
                                        if not _reasoning_started:
                                            sys.stdout.write(f"\n\033[36m[reasoning]\033[0m ")
                                            _reasoning_started = True
                                        sys.stdout.write(reasoning)
                                        sys.stdout.flush()
                                    if content:
                                        if not _content_label_printed:
                                            sys.stdout.write(f"\n\033[32m[content]\033[0m ")
                                            _content_label_printed = True
                                        sys.stdout.write(content)
                                        sys.stdout.flush()

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
                                tool_calls = delta.get("tool_calls", [])
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
                                        f'{k}={json.dumps(v)}' for k, v in tc_args.items()
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

                    # Display actual token usage (always show for visibility)
                    if config.DEBUG_MODE:
                        total_tokens = input_tokens + output_tokens
                        print(f"\n{Color.info('[Token Usage]')}")
                        print(f"{Color.info(f'  Input: {input_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Output: {output_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Total: {total_tokens:,} tokens')}\n")

                # Parse cache token usage — supports both Anthropic and OpenAI/Z.AI formats
                if usage_info and config.ENABLE_PROMPT_CACHING:
                    # Anthropic: cache_creation_input_tokens / cache_read_input_tokens
                    # OpenAI / Z.AI: prompt_tokens_details.cached_tokens (read-only, implicit)
                    cache_creation_tokens = usage_info.get("cache_creation_input_tokens", 0)
                    cache_read_tokens = usage_info.get("cache_read_input_tokens", 0)
                    _ptd = usage_info.get("prompt_tokens_details") or {}
                    cache_read_tokens = cache_read_tokens or _ptd.get("cached_tokens", 0)

                    # Debug: log raw usage info for cache diagnosis
                    if config.DEBUG_MODE:
                        print(f"{Color.DIM}[Cache Debug] usage_info keys: {list(usage_info.keys())} | ptd: {_ptd} | cached: {cache_read_tokens}{Color.RESET}")

                    # Update cache token tracking
                    last_cache_creation_tokens = cache_creation_tokens
                    last_cache_read_tokens = cache_read_tokens
                    total_cache_created += cache_creation_tokens
                    total_cache_read += cache_read_tokens
                
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
                    delay = initial_delay * (2 ** retry_count)
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] Empty response from LLM. Waiting {delay}s...\n"))
                    time.sleep(delay)
                    # fall through to finally, then loop continues
                else:
                    return  # Success (or exhausted retries with empty response)
            finally:
                if _wd_stop is not None:
                    _wd_stop.set()
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

            # ── Generic retryable: 429 or 5xx ──
            is_retryable = e.code == 429 or (500 <= e.code < 600)
            if is_retryable and retry_count < max_retries - 1:
                delay = _RETRY_DELAYS2[retry_count]
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
            # Connection error - retry
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
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
            # Covers real socket timeouts and inactivity-watchdog triggers
            inactivity_triggered = 'inactivity' in str(e).lower()
            label = f"Inactivity ({_inactivity_s}s, no data)" if inactivity_triggered else f"Read timeout ({config.STREAM_API_TIMEOUT}s)"
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
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
            # Explicit SSL error handling (backup catch)
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
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
            # Catch-all for unexpected errors (incl. ResponseNotReady from stale connection,
            # or watchdog-closed connection raising OSError/IncompleteRead)
            if _wd_triggered[0]:
                if retry_count < max_retries - 1:
                    delay = initial_delay * (2 ** retry_count)
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
                delay = initial_delay * (2 ** retry_count)
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
    if stop:
        # Z.AI allows max 4 stop sequences
        _stop = stop[:4] if "z.ai" in url else stop
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

    try:
        _raw_body = json.dumps(data).encode('utf-8')

        if use_stream:
            full_content = []
            _prefix_printed = False
            _raw_t_connect = time.perf_counter()
            response = _persistent_post(url, headers, _raw_body, timeout=config.STREAM_API_TIMEOUT)
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
            response = _persistent_post(url, headers, _raw_body, timeout=config.NONSTREAM_API_TIMEOUT)
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

        response = _persistent_post(url, headers, json.dumps(data).encode('utf-8'), timeout=10)
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
            response = _persistent_post(url, headers, json.dumps(data).encode('utf-8'), timeout=30)
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
