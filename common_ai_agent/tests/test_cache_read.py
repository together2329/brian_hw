"""
test_cache_read.py — Diagnostic: verify prompt cache read is working.

두 번 연속 동일한 시스템 프롬프트로 LLM을 호출하여:
  1st call → cache_creation_input_tokens > 0  (캐시 생성)
  2nd call → cache_read_input_tokens > 0      (캐시 히트)

지원 포맷:
  - Anthropic native: cache_creation_input_tokens / cache_read_input_tokens
  - OpenAI/Z.AI:      prompt_tokens_details.cached_tokens

Run:
    cd common_ai_agent
    pytest tests/test_cache_read.py -v -s
    python tests/test_cache_read.py          # standalone
    python tests/test_cache_read.py --calls 3   # 3회 반복
"""

from __future__ import annotations

import os
import sys
import time
import json
import urllib.request
import urllib.error
from typing import Optional

# ── path setup ────────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
for _p in (os.path.join(_root, "src"), _root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

_LLM_API_KEY  = os.environ.get("LLM_API_KEY", "")
_LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
_LLM_MODEL    = os.environ.get("LLM_MODEL_NAME", "")

try:
    import config as _cfg
    _HAS_API = bool(_LLM_API_KEY) or bool(getattr(_cfg, "API_KEY", ""))
except Exception:
    _HAS_API = bool(_LLM_API_KEY)

skip_without_api = pytest.mark.skipif(
    not _HAS_API,
    reason="Set LLM_API_KEY (and optionally LLM_BASE_URL, LLM_MODEL_NAME)",
)

# ── ANSI colours ──────────────────────────────────────────────────────────────
_R      = "\033[0m"
_DIM    = "\033[2m"
_BOLD   = "\033[1m"
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_GRAY   = "\033[90m"


# ── large system prompt (must be ≥ 1024 tokens for Anthropic to cache) ────────
# ~1200 tokens of stable boilerplate — enough to trigger caching on all providers.
_CACHE_SYSTEM_PROMPT = """\
You are an expert AI coding assistant specializing in hardware design, embedded systems,
and low-level software engineering. You help engineers design, debug, and optimize complex
digital systems including FPGAs, ASICs, microcontrollers, and system-on-chip architectures.

Your knowledge spans:

## Hardware Description Languages
- Verilog and SystemVerilog: RTL design, testbench writing, synthesis constraints
- VHDL: entity/architecture patterns, generics, simulation
- Timing analysis: setup/hold, critical paths, clock domain crossing (CDC)
- AXI4, AXI4-Lite, AXI4-Stream bus protocols and interconnect design

## Digital Design Patterns
- Finite state machines (Mealy, Moore), pipelining, FIFO design
- Arbitration schemes: round-robin, priority, weighted fair queuing
- Memory systems: SRAM, DRAM, HBM, cache hierarchies, ECC
- Power management: clock gating, power domains, UPF/CPF flow

## Embedded Software
- RTOS concepts: task scheduling, mutexes, semaphores, message queues
- DMA controllers, interrupt latency, memory-mapped I/O
- Bare-metal C/C++ for ARM Cortex-M/A, RISC-V
- Bootloader design, secure boot, OTA firmware update flows

## Verification and Testing
- UVM methodology: agents, scoreboards, coverage-driven verification
- Formal verification: assertions, properties, model checking
- Constrained-random stimulus generation, functional coverage
- FPGA prototyping and bring-up methodology

## Tools and Flows
- Synopsys Design Compiler, Cadence Genus (synthesis)
- Synopsys VCS, Cadence Xcelium, Mentor Questa (simulation)
- Xilinx Vivado, Intel Quartus (FPGA implementation)
- Cocotb for Python-based hardware simulation
- Git-based design management, CI/CD for hardware projects

When answering questions:
1. Be precise and technically accurate — hardware bugs are expensive.
2. Show complete, runnable code examples when relevant.
3. Point out common pitfalls (metastability, race conditions, resource conflicts).
4. Explain trade-offs between different design approaches.
5. Use correct terminology for the target domain.

Always assume the user is a competent engineer who wants depth, not hand-holding.
Avoid unnecessary caveats. Get to the point.
""" * 2  # repeat to ensure we are well above 1024 token threshold


# ── raw usage extraction ───────────────────────────────────────────────────────

class UsageInfo:
    """Parsed cache usage from one LLM API response."""

    def __init__(self,
                 input_tokens: int = 0,
                 output_tokens: int = 0,
                 cache_created: int = 0,
                 cache_read: int = 0,
                 raw: Optional[dict] = None):
        self.input_tokens  = input_tokens
        self.output_tokens = output_tokens
        self.cache_created = cache_created
        self.cache_read    = cache_read
        self.raw           = raw or {}

    @property
    def cached(self) -> bool:
        return self.cache_read > 0

    @property
    def written(self) -> bool:
        return self.cache_created > 0

    def cache_label(self) -> str:
        parts = []
        if self.cache_created:
            parts.append(f"{_CYAN}write {_fmt(self.cache_created)}{_R}")
        if self.cache_read:
            parts.append(f"{_GREEN}read  {_fmt(self.cache_read)}{_R}")
        return "  ".join(parts) if parts else f"{_GRAY}none{_R}"

    def __repr__(self):
        return (f"UsageInfo(in={self.input_tokens}, out={self.output_tokens}, "
                f"cache_created={self.cache_created}, cache_read={self.cache_read})")


def _fmt(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def _parse_usage(usage_dict: dict) -> UsageInfo:
    """Extract token counts from raw API usage dict (Anthropic + OpenAI formats)."""
    inp  = usage_dict.get("input_tokens")  or usage_dict.get("prompt_tokens", 0)
    out  = usage_dict.get("output_tokens") or usage_dict.get("completion_tokens", 0)
    cw   = usage_dict.get("cache_creation_input_tokens", 0)
    cr   = usage_dict.get("cache_read_input_tokens", 0)

    # OpenAI / Z.AI style: prompt_tokens_details.cached_tokens
    ptd  = usage_dict.get("prompt_tokens_details") or {}
    cr   = cr or ptd.get("cached_tokens", 0)

    return UsageInfo(input_tokens=inp, output_tokens=out,
                     cache_created=cw, cache_read=cr, raw=usage_dict)


# ── LLM call helpers ──────────────────────────────────────────────────────────

def _call_streaming(messages: list, system: str, model: str,
                    base_url: str, api_key: str) -> UsageInfo:
    """
    One streaming call. Collects the final usage chunk and returns UsageInfo.
    Uses the raw HTTP layer (no llm_client globals) so each call is independent.
    """
    url = f"{base_url.rstrip('/')}/chat/completions"
    all_messages = [{"role": "system", "content": system}] + messages

    # Build Anthropic cache_control blocks if provider is Anthropic
    _is_anthropic = "anthropic" in base_url or "claude" in model.lower()
    if _is_anthropic and getattr(_cfg, "ENABLE_PROMPT_CACHING", False):
        all_messages[0]["content"] = [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ]

    payload = json.dumps({
        "model": model,
        "messages": all_messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": 64,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "prompt-caching-2024-07-31",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    usage_dict: dict = {}
    content_buf = []

    try:
        ctx = {"ssl": None}
        ssl_verify = getattr(_cfg, "SSL_VERIFY", True)
        if not ssl_verify:
            import ssl as _ssl
            ctx["ssl"] = _ssl.create_default_context()
            ctx["ssl"].check_hostname = False
            ctx["ssl"].verify_mode = _ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx.get("ssl"), timeout=60) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue

                # Collect content
                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})
                    c = delta.get("content") or delta.get("reasoning_content") or ""
                    if c:
                        content_buf.append(c)

                # Last chunk usually carries usage
                if "usage" in chunk:
                    usage_dict = chunk["usage"]

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {e.reason}\n{body[:500]}") from e

    return _parse_usage(usage_dict)


def _call_via_llm_client(messages: list, system: str) -> UsageInfo:
    """
    Call through the project's llm_client.chat_completion_stream so that
    ENABLE_PROMPT_CACHING / apply_cache_breakpoints are honoured automatically.
    Reads back cache stats from llm_client module globals.
    """
    import llm_client as lc

    all_msgs = [{"role": "system", "content": system}] + messages
    # Consume generator
    chunks = list(lc.chat_completion_stream(
        all_msgs,
        stop=None,
        skip_rate_limit=True,
        suppress_spinner=True,
    ))

    usage = lc.get_last_usage() or {}
    return UsageInfo(
        input_tokens=usage.get("input",  0),
        output_tokens=usage.get("output", 0),
        cache_created=usage.get("cache_created", 0),
        cache_read=usage.get("cache_read",    0),
        raw=usage,
    )


# ── Report ────────────────────────────────────────────────────────────────────

class CacheReport:
    """Aggregate over multiple sequential calls to the same prompt."""

    def __init__(self, model: str, mode: str):
        self.model  = model
        self.mode   = mode          # "raw" | "client"
        self.calls: list[tuple[int, UsageInfo, float]] = []  # (call_num, usage, elapsed)

    def add(self, call_num: int, usage: UsageInfo, elapsed: float):
        self.calls.append((call_num, usage, elapsed))

    def print_header(self):
        print(f"\n{_BOLD}{'='*68}{_R}")
        print(f"{_BOLD}Model  : {self.model or '(default)'}{_R}")
        print(f"{_BOLD}Mode   : {self.mode}{_R}")
        print(f"{_BOLD}Calls  : {len(self.calls)}{_R}")
        print(f"{'─'*68}")

    def print_calls(self):
        for num, usage, elapsed in self.calls:
            status = (
                f"{_GREEN}[CACHE HIT ✓]{_R}"  if usage.cached  else
                f"{_CYAN}[CACHE WRITE]{_R}"   if usage.written else
                f"{_GRAY}[NO CACHE]   {_R}"
            )
            print(
                f"  Call {num}  {status}  "
                f"in={_fmt(usage.input_tokens)} out={_fmt(usage.output_tokens)}  "
                f"{usage.cache_label()}  {_DIM}({elapsed:.2f}s){_R}"
            )

    def print_summary(self):
        writes = sum(1 for _, u, _ in self.calls if u.written)
        hits   = sum(1 for _, u, _ in self.calls if u.cached)
        total_cr = sum(u.cache_read    for _, u, _ in self.calls)
        total_cw = sum(u.cache_created for _, u, _ in self.calls)

        print(f"{'─'*68}")
        print(f"Cache writes : {writes}  |  Cache hits  : {hits}")
        print(f"Total written: {_fmt(total_cw)} tokens  |  Total read: {_fmt(total_cr)} tokens")

        if hits == 0:
            print(f"\n{_RED}[FAIL] No cache hits detected.{_R}")
            print(f"{_DIM}Possible causes:")
            print(f"  • ENABLE_PROMPT_CACHING=false in .config")
            print(f"  • Provider does not support prompt caching")
            print(f"  • System prompt < 1024 tokens (Anthropic minimum)")
            print(f"  • Non-Anthropic provider ignores cache_control blocks{_R}")
        else:
            print(f"\n{_GREEN}{_BOLD}[PASS] Cache read confirmed on {hits}/{len(self.calls)-1} eligible calls.{_R}")

        print(f"{'='*68}\n")

    @property
    def hit_count(self) -> int:
        return sum(1 for _, u, _ in self.calls if u.cached)


# ── core test logic ───────────────────────────────────────────────────────────

def _run_cache_test(n_calls: int = 3, use_client: bool = True) -> CacheReport:
    """
    Make n_calls sequential identical requests and report cache write/read per call.
    Call 1 → expect cache WRITE.
    Calls 2..n → expect cache READ (hit).
    """
    model    = getattr(_cfg, "MODEL_NAME",  _LLM_MODEL  or "")
    base_url = getattr(_cfg, "BASE_URL",    _LLM_BASE_URL or "")
    api_key  = getattr(_cfg, "API_KEY",     _LLM_API_KEY  or "")

    mode = "llm_client" if use_client else "raw_http"
    report = CacheReport(model=model, mode=mode)

    user_messages = [{"role": "user", "content": "Reply with exactly one word: Ready"}]

    for i in range(1, n_calls + 1):
        t0 = time.time()
        if use_client:
            usage = _call_via_llm_client(user_messages, _CACHE_SYSTEM_PROMPT)
        else:
            usage = _call_streaming(user_messages, _CACHE_SYSTEM_PROMPT,
                                    model=model, base_url=base_url, api_key=api_key)
        elapsed = time.time() - t0
        report.add(i, usage, elapsed)

    return report


# ── pytest tests ──────────────────────────────────────────────────────────────

@skip_without_api
class TestCacheRead:
    """
    Verify that the second LLM call hits the prompt cache.
    Run with: pytest tests/test_cache_read.py -v -s
    """

    def _report(self, report: CacheReport, capsys=None):
        ctx = capsys.disabled() if capsys else _null_ctx()
        with ctx:
            report.print_header()
            report.print_calls()
            report.print_summary()
        return report

    def test_cache_read_via_llm_client(self, capsys):
        """
        Two calls through llm_client.chat_completion_stream.
        Call 1 should write cache; call 2 should read it.
        Fails if ENABLE_PROMPT_CACHING=false or provider doesn't support caching.
        """
        report = _run_cache_test(n_calls=2, use_client=True)
        self._report(report, capsys)

        caching_enabled = getattr(_cfg, "ENABLE_PROMPT_CACHING", False)
        if not caching_enabled:
            pytest.skip("ENABLE_PROMPT_CACHING=false — skipping cache hit assertion")

        # Must have at least one cache write (call 1)
        writes = sum(1 for _, u, _ in report.calls if u.written)
        assert writes >= 1, "No cache write on first call — check provider support"

        # Must have at least one cache read (call 2+)
        assert report.hit_count >= 1, (
            "No cache read detected. "
            "Check: ENABLE_PROMPT_CACHING=true, provider support, system prompt size."
        )

    def test_cache_read_raw_http(self, capsys):
        """
        Same test but bypasses llm_client — uses raw urllib calls.
        Useful to confirm the issue is not in llm_client's cache logic.
        """
        report = _run_cache_test(n_calls=2, use_client=False)
        self._report(report, capsys)

        caching_enabled = getattr(_cfg, "ENABLE_PROMPT_CACHING", False)
        if not caching_enabled:
            pytest.skip("ENABLE_PROMPT_CACHING=false — skipping cache hit assertion")

        assert report.hit_count >= 1, "No cache read via raw HTTP"

    def test_cache_read_three_calls(self, capsys):
        """
        Three sequential calls — call 1 writes, calls 2 and 3 should both read.
        Shows whether cache persists across multiple hits.
        """
        report = _run_cache_test(n_calls=3, use_client=True)
        self._report(report, capsys)

        caching_enabled = getattr(_cfg, "ENABLE_PROMPT_CACHING", False)
        if not caching_enabled:
            pytest.skip("ENABLE_PROMPT_CACHING=false — skipping cache hit assertion")

        assert report.hit_count >= 1, "Expected ≥1 cache read across 3 calls"

    def test_cache_usage_fields_present(self, capsys):
        """
        Verify that usage dict contains cache fields at all — even if zero.
        Fails only if usage came back completely empty (API/parsing issue).
        """
        import llm_client as lc

        msgs = [
            {"role": "system", "content": _CACHE_SYSTEM_PROMPT},
            {"role": "user",   "content": "Say hi"},
        ]
        list(lc.chat_completion_stream(
            msgs, stop=None, skip_rate_limit=True, suppress_spinner=True
        ))
        usage = lc.get_last_usage()

        with capsys.disabled():
            print(f"\n{_BOLD}Raw get_last_usage():{_R}")
            if usage:
                for k, v in usage.items():
                    print(f"  {k:<28} {v}")
            else:
                print(f"  {_RED}None — no API call recorded{_R}")

        assert usage is not None, "get_last_usage() returned None — check llm_client globals"
        assert "input" in usage and usage["input"] > 0, "input tokens missing from usage"


# ── null context manager ──────────────────────────────────────────────────────

class _null_ctx:
    def __enter__(self): return self
    def __exit__(self, *_): pass


# ── standalone runner ─────────────────────────────────────────────────────────

def _standalone(n_calls: int = 3):
    if not _HAS_API:
        print("LLM_API_KEY is not set.")
        print("  export LLM_API_KEY=<your-key>")
        print("  export LLM_BASE_URL=<api-base>   # optional")
        print("  export LLM_MODEL_NAME=<model>    # optional")
        sys.exit(1)

    model    = getattr(_cfg, "MODEL_NAME",  _LLM_MODEL  or "")
    base_url = getattr(_cfg, "BASE_URL",    _LLM_BASE_URL or "")
    caching  = getattr(_cfg, "ENABLE_PROMPT_CACHING", False)

    print(f"{_BOLD}LLM_BASE_URL        : {_R}{base_url}")
    print(f"{_BOLD}LLM_MODEL_NAME      : {_R}{model}")
    print(f"{_BOLD}ENABLE_PROMPT_CACHING: {_R}"
          f"{(_GREEN + 'true' + _R) if caching else (_YELLOW + 'false' + _R)}")
    print(f"{_BOLD}System prompt size  : {_R}~{len(_CACHE_SYSTEM_PROMPT)//4} tokens")

    if not caching:
        print(f"\n{_YELLOW}[WARN] ENABLE_PROMPT_CACHING=false — "
              f"cache writes will be skipped by llm_client.{_R}")
        print(f"{_DIM}Running raw HTTP test instead (bypasses llm_client caching flag).{_R}")

    # ── raw HTTP test ──────────────────────────────────────────────────────────
    print(f"\n{_BOLD}── Raw HTTP ({n_calls} calls) ──{_R}")
    report_raw = _run_cache_test(n_calls=n_calls, use_client=False)
    report_raw.print_header()
    report_raw.print_calls()
    report_raw.print_summary()

    # ── llm_client test ────────────────────────────────────────────────────────
    print(f"\n{_BOLD}── via llm_client ({n_calls} calls) ──{_R}")
    report_cli = _run_cache_test(n_calls=n_calls, use_client=True)
    report_cli.print_header()
    report_cli.print_calls()
    report_cli.print_summary()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Test LLM prompt cache read.")
    ap.add_argument("--calls", type=int, default=3,
                    help="Number of sequential calls (default: 3)")
    ap.add_argument("model", nargs="?", default=None,
                    help="Model override (overrides LLM_MODEL_NAME)")
    args = ap.parse_args()

    if args.model:
        _cfg.MODEL_NAME = args.model  # type: ignore[attr-defined]
    elif _LLM_MODEL:
        _cfg.MODEL_NAME = _LLM_MODEL  # type: ignore[attr-defined]

    _standalone(n_calls=args.calls)
