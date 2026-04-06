"""
test_streaming_chunk_format.py — Diagnostic: inspect raw streaming chunk format.

각 청크가 어떤 포맷으로 오는지 확인한다:
  - plain str            → content
  - ("reasoning", str)   → reasoning via API field (DeepSeek/GLM reasoning_content)
  - str with <think>     → reasoning via inline tag (DeepSeek open-weights style)

Run:
    cd common_ai_agent
    pytest tests/test_streaming_chunk_format.py -v -s
    python tests/test_streaming_chunk_format.py        # standalone
"""

from __future__ import annotations

import os
import re
import sys
from typing import List, Tuple

# ── path setup ────────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
for _p in (os.path.join(_root, "src"), _root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

# ── env var config (LLM_BASE_URL / LLM_API_KEY / LLM_MODEL_NAME) ─────────────
# config.py already reads these three vars; we just verify LLM_API_KEY is set.
_LLM_API_KEY   = os.environ.get("LLM_API_KEY", "")
_LLM_BASE_URL  = os.environ.get("LLM_BASE_URL", "")
_LLM_MODEL     = os.environ.get("LLM_MODEL_NAME", "")

try:
    import config as _cfg
    _HAS_API = bool(_LLM_API_KEY) or bool(getattr(_cfg, "API_KEY", ""))
except Exception:
    _HAS_API = bool(_LLM_API_KEY)

skip_without_api = pytest.mark.skipif(
    not _HAS_API,
    reason="Set LLM_API_KEY (and optionally LLM_BASE_URL, LLM_MODEL_NAME)"
)


# ── ANSI colours (for standalone mode) ───────────────────────────────────────
_R = "\033[0m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_BOLD = "\033[1m"


# ── chunk analysis ────────────────────────────────────────────────────────────

class ChunkInfo:
    """Parsed representation of a single streaming chunk."""
    __slots__ = ("index", "raw", "token_type", "text", "has_think_open", "has_think_close")

    def __init__(self, index: int, raw):
        self.index = index
        self.raw = raw

        if isinstance(raw, tuple) and len(raw) == 2:
            self.token_type = raw[0]   # "reasoning" | "content"
            self.text = raw[1]
        else:
            self.token_type = "str"
            self.text = raw if isinstance(raw, str) else str(raw)

        self.has_think_open  = "<think>"  in self.text
        self.has_think_close = "</think>" in self.text

    @property
    def is_reasoning_tuple(self) -> bool:
        return self.token_type == "reasoning"

    @property
    def is_content_tuple(self) -> bool:
        return self.token_type == "content"

    @property
    def is_plain_str(self) -> bool:
        return self.token_type == "str"

    @property
    def has_think_tag(self) -> bool:
        return self.has_think_open or self.has_think_close

    def type_label(self) -> str:
        if self.is_reasoning_tuple:
            return f"{_CYAN}tuple('reasoning'){_R}"
        if self.is_content_tuple:
            return f"{_GREEN}tuple('content'){_R}"
        if self.has_think_open:
            return f"{_YELLOW}str <think>{_R}"
        if self.has_think_close:
            return f"{_YELLOW}str </think>{_R}"
        return f"{_DIM}str{_R}"


class StreamReport:
    """Aggregate statistics over all chunks from one streaming call."""

    def __init__(self, chunks: list, model: str = ""):
        self.model = model
        self.infos: List[ChunkInfo] = [ChunkInfo(i, c) for i, c in enumerate(chunks)]

    # ── counts ────────────────────────────────────────────────────────────────
    @property
    def n_total(self): return len(self.infos)

    @property
    def n_reasoning_tuple(self): return sum(1 for c in self.infos if c.is_reasoning_tuple)

    @property
    def n_content_tuple(self): return sum(1 for c in self.infos if c.is_content_tuple)

    @property
    def n_plain_str(self): return sum(1 for c in self.infos if c.is_plain_str)

    @property
    def n_think_tag(self): return sum(1 for c in self.infos if c.has_think_tag)

    # ── derived flags ─────────────────────────────────────────────────────────
    @property
    def separation_mode(self) -> str:
        if self.n_reasoning_tuple > 0:
            return "TUPLE"           # separate reasoning_content API field
        if self.n_think_tag > 0:
            return "THINK_TAG"       # <think>...</think> inside content
        return "NONE"                # no reasoning separation

    @property
    def has_bleed_candidate(self) -> bool:
        """True if any chunk is a tuple with BOTH reasoning and content fields — i.e. bleed."""
        for c in self.infos:
            if c.is_reasoning_tuple:
                next_i = c.index + 1
                if next_i < len(self.infos):
                    nxt = self.infos[next_i]
                    if not nxt.is_reasoning_tuple and nxt.text.lstrip()[:1:].islower():
                        return True
        return False

    # ── text helpers ──────────────────────────────────────────────────────────
    def reasoning_text(self) -> str:
        parts = []
        for c in self.infos:
            if c.is_reasoning_tuple:
                parts.append(c.text)
            elif c.has_think_open or (c.is_plain_str and not c.is_content_tuple):
                # extract text between <think> tags
                m = re.findall(r"<think>(.*?)</think>", c.text, re.DOTALL)
                parts.extend(m)
        return "".join(parts)

    def content_text(self) -> str:
        parts = []
        for c in self.infos:
            if c.is_reasoning_tuple:
                continue
            if c.has_think_tag:
                clean = re.sub(r"<think>.*?</think>", "", c.text, flags=re.DOTALL)
                clean = re.sub(r"</?think>", "", clean)
                parts.append(clean)
            else:
                parts.append(c.text)
        return "".join(parts)

    # ── display ───────────────────────────────────────────────────────────────
    def print_header(self):
        print(f"\n{_BOLD}{'='*64}{_R}")
        print(f"{_BOLD}Model : {self.model or '(default)'}{_R}")
        print(f"Chunks: {self.n_total}  |  "
              f"reasoning_tuple: {_CYAN}{self.n_reasoning_tuple}{_R}  |  "
              f"content_tuple: {_GREEN}{self.n_content_tuple}{_R}  |  "
              f"plain_str: {_DIM}{self.n_plain_str}{_R}  |  "
              f"think_tag: {_YELLOW}{self.n_think_tag}{_R}")
        mode_colour = _CYAN if self.separation_mode == "TUPLE" else (
                      _YELLOW if self.separation_mode == "THINK_TAG" else _DIM)
        print(f"Separation mode: {mode_colour}{_BOLD}{self.separation_mode}{_R}")
        if self.has_bleed_candidate:
            print(f"{_RED}[!] Possible bleed candidate detected{_R}")
        print(f"{'─'*64}")

    def print_chunks(self, max_chunks: int = 80, preview_len: int = 60):
        """Print per-chunk type + preview."""
        shown = self.infos[:max_chunks]
        for c in shown:
            preview = repr(c.text[:preview_len]) + ("…" if len(c.text) > preview_len else "")
            print(f"  [{c.index:03d}] {c.type_label():<30}  {preview}")
        if len(self.infos) > max_chunks:
            print(f"  {_DIM}... {len(self.infos) - max_chunks} more chunks not shown{_R}")

    def print_summary(self):
        r = self.reasoning_text()
        t = self.content_text()
        print(f"{'─'*64}")
        print(f"Reasoning text ({len(r)} chars): {repr(r[:120])}{'…' if len(r)>120 else ''}")
        print(f"Content text   ({len(t)} chars): {repr(t[:120])}{'…' if len(t)>120 else ''}")
        print(f"{'─'*64}")

        # ── assembled view ────────────────────────────────────────────────────
        if r:
            print(f"{_CYAN}{_BOLD}[ASSEMBLED REASONING]{_R}")
            for line in r.splitlines():
                print(f"  {_CYAN}{line}{_R}")
            print()

        print(f"{_GREEN}{_BOLD}[ASSEMBLED CONTENT]{_R}")
        if t.strip():
            for line in t.splitlines():
                print(f"  {_GREEN}{line}{_R}")
        else:
            print(f"  {_DIM}(empty){_R}")

        print(f"{'='*64}\n")


# ── LLM call helper ───────────────────────────────────────────────────────────

def _stream(messages, model=None) -> list:
    from llm_client import chat_completion_stream
    return list(chat_completion_stream(
        messages,
        model=model,
        stop=None,
        skip_rate_limit=True,
        suppress_spinner=True,
    ))


def _make_messages(user_msg: str, think: bool = False) -> list:
    system = "Think step by step before answering." if think else "Be concise."
    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_msg},
    ]


# ── pytest tests ──────────────────────────────────────────────────────────────

@skip_without_api
class TestStreamingChunkFormat:
    """
    Each test calls the real LLM and prints a full chunk-format report.
    Pass/fail only checks that SOMETHING was returned — the real value is
    the printed output (run with pytest -s).
    """

    def _run_and_report(self, messages, model=None, capsys=None):
        chunks = _stream(messages, model=model)
        report = StreamReport(chunks, model=model or getattr(_cfg, "MODEL_NAME", ""))

        ctx = capsys.disabled() if capsys else _null_ctx()
        with ctx:
            report.print_header()
            report.print_chunks()
            report.print_summary()

        return report

    # ── default model, no reasoning prompt ────────────────────────────────────
    def test_plain_content_format(self, capsys):
        """Simple answer — expect plain str chunks, no reasoning."""
        msg = _make_messages("List 3 colours. One per line.")
        r = self._run_and_report(msg, capsys=capsys)
        assert r.n_total > 0, "No chunks returned"

    # ── default model, reasoning-eliciting prompt ──────────────────────────────
    def test_reasoning_prompt_format(self, capsys):
        """Maths question — model may emit reasoning via tuple or <think> tag."""
        msg = _make_messages("What is 17 × 13? Show your work.", think=True)
        r = self._run_and_report(msg, capsys=capsys)
        assert r.n_total > 0, "No chunks returned"

    # ── explicitly check separation mode ──────────────────────────────────────
    def test_report_separation_mode(self, capsys):
        """
        Prints which separation mode the current model uses.
        Fails only if zero chunks come back.
        """
        msg = _make_messages("Explain binary search in 2 steps.", think=True)
        r = self._run_and_report(msg, capsys=capsys)

        with capsys.disabled():
            mode = r.separation_mode
            if mode == "TUPLE":
                print(f"{_CYAN}→ Model uses API-level reasoning_content tuples.{_R}")
            elif mode == "THINK_TAG":
                print(f"{_YELLOW}→ Model uses <think> inline tags in content.{_R}")
            else:
                print(f"{_DIM}→ Model produces no reasoning separation.{_R}")

        assert r.n_total > 0

    # ── GLM-specific bleed test ────────────────────────────────────────────────
    def test_glm_chunk_format(self, capsys):
        """GLM-4.7 via z.ai — known to use reasoning_content tuples with possible bleed."""
        glm_model = "z-ai/glm-4.7"
        msg = _make_messages("What is AXI back-pressure? Explain briefly.", think=True)
        try:
            r = self._run_and_report(msg, model=glm_model, capsys=capsys)
        except Exception as e:
            pytest.skip(f"GLM model not reachable: {e}")

        with capsys.disabled():
            if r.has_bleed_candidate:
                print(f"{_RED}[BLEED] GLM bleed candidate still detected after fix!{_R}")
            else:
                print(f"{_GREEN}[OK] No bleed candidates detected.{_R}")

        assert r.n_total > 0

    # ── compare both streaming functions ──────────────────────────────────────
    def test_both_streaming_paths_same_format(self, capsys):
        """
        _execute_streaming_request and chat_completion_stream must produce
        consistent chunk types for the same prompt.
        Both should yield plain str for content (not tuple).
        """
        from llm_client import _execute_streaming_request, chat_completion_stream

        import config
        url = f"{config.BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.API_KEY}",
        }
        messages = _make_messages("Say 'hello'.")
        data = {
            "model": config.MODEL_NAME,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        chunks_helper = list(_execute_streaming_request(url, headers, data, messages))
        chunks_main   = list(chat_completion_stream(
            messages, stop=None, skip_rate_limit=True, suppress_spinner=True
        ))

        rh = StreamReport(chunks_helper, model="helper(_execute_streaming_request)")
        rm = StreamReport(chunks_main,   model="main(chat_completion_stream)")

        with capsys.disabled():
            print(f"\n{_BOLD}── Helper function ──{_R}")
            rh.print_header()
            rh.print_chunks(max_chunks=20)
            print(f"\n{_BOLD}── Main function ──{_R}")
            rm.print_header()
            rm.print_chunks(max_chunks=20)

            # Content chunks must be plain str in both paths (not ("content", ...) tuple)
            helper_content_tuples = rh.n_content_tuple
            main_content_tuples   = rm.n_content_tuple
            print(f"\nHelper content tuples: {helper_content_tuples} (should be 0)")
            print(f"Main   content tuples: {main_content_tuples}   (should be 0)")

        assert rh.n_content_tuple == 0, (
            f"_execute_streaming_request still yields ('content', ...) tuples: "
            f"{rh.n_content_tuple} found"
        )
        assert rm.n_content_tuple == 0, (
            f"chat_completion_stream yields ('content', ...) tuples: "
            f"{rm.n_content_tuple} found"
        )


# ── null context manager for standalone mode ──────────────────────────────────

class _null_ctx:
    def __enter__(self): return self
    def __exit__(self, *_): pass


# ── standalone runner ─────────────────────────────────────────────────────────

def _standalone(max_chunks: int = 80):
    if not _HAS_API:
        print("LLM_API_KEY is not set.")
        print("  export LLM_API_KEY=<your-key>")
        print("  export LLM_BASE_URL=<api-base>   # optional")
        print("  export LLM_MODEL_NAME=<model>    # optional")
        sys.exit(1)

    model = getattr(_cfg, "MODEL_NAME", _LLM_MODEL or "")
    print(f"{_BOLD}LLM_BASE_URL  : {_R}{getattr(_cfg, 'BASE_URL', _LLM_BASE_URL)}")
    print(f"{_BOLD}LLM_MODEL_NAME: {_R}{model}")

    prompts = [
        ("plain",     "List 3 colours. One per line.",                 False),
        ("reasoning", "What is 17 × 13? Show your work.",             True),
        ("code",      "Write a one-liner Python to reverse a string.", False),
    ]

    for label, user_msg, think in prompts:
        print(f"\n{_BOLD}[{label}]{_R}")
        messages = _make_messages(user_msg, think=think)
        chunks = _stream(messages)
        r = StreamReport(chunks, model=model)
        r.print_header()
        r.print_chunks(max_chunks=max_chunks)
        r.print_summary()


if __name__ == "__main__":
    # Usage:
    #   export LLM_API_KEY=...
    #   export LLM_BASE_URL=...      # optional
    #   export LLM_MODEL_NAME=...    # optional
    #
    #   python3 tests/test_streaming_chunk_format.py           # 80 chunks
    #   python3 tests/test_streaming_chunk_format.py --all     # all chunks
    #   python3 tests/test_streaming_chunk_format.py z-ai/glm-4.7 --all
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("model", nargs="?", default=None,
                    help="model override (overrides LLM_MODEL_NAME)")
    ap.add_argument("--all", action="store_true", help="show all chunks (no limit)")
    args = ap.parse_args()
    if args.model:
        _cfg.MODEL_NAME = args.model  # type: ignore[attr-defined]
    elif _LLM_MODEL:
        _cfg.MODEL_NAME = _LLM_MODEL  # type: ignore[attr-defined]
    _standalone(max_chunks=10**9 if args.all else 80)
