"""tests/test_compressor_llm_failure.py

Red-first tests for the silent-swallow defect in core/compressor.py.

Defect: when the LLM summarizer raises during compress_history, the
compressor silently returns a char-truncation fallback without any
machine-readable marker, so callers cannot distinguish a real summary
from a degraded fallback.

Fix contract verified here:
  1. LLM failure -> result contains a failure marker in the content AND
     llm_failed=True is surfaced via the emit_fn warning banner.
  2. LLM success -> no marker, real summary text appears.
  3. raise_on_llm_failure=True -> CompressionLLMError raised instead.
  4. _summary_is_llm_fallback() correctly detects markers from both
     _compress_single and _compress_chunked.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import types
import pytest
from core.compressor import (
    compress_history,
    CompressionLLMError,
    _summary_is_llm_fallback,
    _LLM_FAILURE_MARKERS,
)


# ---------------------------------------------------------------------------
# Minimal config stub — matches the fields compress_history reads
# ---------------------------------------------------------------------------

def _make_cfg(**overrides):
    cfg = types.SimpleNamespace(
        ENABLE_COMPRESSION=True,
        MAX_CONTEXT_TOKENS=128_000,
        COMPRESSION_THRESHOLD=0.9,
        PREEMPTIVE_COMPRESSION_THRESHOLD=0.85,
        COMPRESSION_KEEP_RECENT=4,
        COMPRESSION_MODE="single",
        COMPRESSION_CHUNK_SIZE=10,
        ENABLE_TURN_PROTECTION=False,
        TURN_PROTECTION_COUNT=3,
        COMPRESSION_INPUT_MAX_CHARS=0,
        COMPRESSION_INPUT_BUDGET_RATIO=0.5,
        COMPRESSION_PRE_ANALYSIS=False,
        SMART_TRUNCATE_TEXT_MAX=2000,
        SMART_TRUNCATE_TOOL_MAX=2000,
        SMART_TRUNCATE_HIGHVALUE_MULT=2.0,
        COMPRESSION_TOOL_CALL_PATHS=0,
        MODEL_NAME="test-model",
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


# ---------------------------------------------------------------------------
# History fixture big enough to trigger compression
# ---------------------------------------------------------------------------

def _make_history(n_pairs: int = 40) -> list[dict]:
    msgs: list[dict] = [{"role": "system", "content": "You are a coding agent."}]
    for i in range(n_pairs):
        msgs.append({"role": "user", "content": f"Task {i}: edit file_{i}.py. " * 8})
        msgs.append({
            "role": "assistant", "content": "",
            "tool_calls": [{"id": f"c{i}", "type": "function",
                            "function": {"name": "write_file",
                                         "arguments": f'{{"path": "file_{i}.py"}}'}}],
        })
        msgs.append({
            "role": "tool", "tool_call_id": f"c{i}", "name": "write_file",
            "content": f"wrote file_{i}.py ok; 3 passed " * 6,
        })
    return msgs


# ---------------------------------------------------------------------------
# LLM stubs
# ---------------------------------------------------------------------------

def _working_llm(messages, **kw):
    """Simulates a healthy summarizer — yields a real summary."""
    yield "## Working Context\n- CWD: /repo\n## Completed Work\n- edited file_0..file_39\n"


def _failing_llm(messages, **kw):
    """Simulates a broken LLM (bad key, wrong model, network error)."""
    raise RuntimeError("HTTP 401 invalid api key (simulated)")
    yield ""  # pragma: no cover


# ---------------------------------------------------------------------------
# Helper: find any message whose content contains a substring
# ---------------------------------------------------------------------------

def _find_content(result: list[dict], substring: str) -> str | None:
    for m in result:
        c = str(m.get("content", ""))
        if substring in c:
            return c
    return None


# ===========================================================================
# Tests
# ===========================================================================

class TestLLMFailureSurfacedInContent:
    """Failing LLM must embed a machine-readable marker in the fallback content."""

    def test_failure_marker_present_in_result(self):
        """When the LLM raises, compress_history must embed a failure marker."""
        hist = _make_history()
        cfg = _make_cfg()
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
        )
        # At least one message must carry one of the known failure markers
        assert _summary_is_llm_fallback(result), (
            "Expected at least one failure marker in compressed result, "
            "but _summary_is_llm_fallback() returned False — "
            "the silent-swallow defect is present."
        )

    def test_failure_marker_is_specific_string(self):
        """The marker must contain one of the canonical _LLM_FAILURE_MARKERS strings."""
        hist = _make_history()
        cfg = _make_cfg()
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
        )
        all_content = " ".join(str(m.get("content", "")) for m in result)
        found = any(marker in all_content for marker in _LLM_FAILURE_MARKERS)
        assert found, (
            f"None of {_LLM_FAILURE_MARKERS!r} found in compressed content — "
            "callers cannot distinguish a degraded result from a real summary."
        )

    def test_fallback_content_still_present(self):
        """Fallback must include some original message content, not be empty."""
        hist = _make_history()
        cfg = _make_cfg()
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
        )
        # Result must be non-empty and system summary must have some content
        assert result, "compress_history returned an empty list"
        sys_msgs = [m for m in result if m.get("role") == "system"]
        assert sys_msgs, "No system message in compressed result"
        # The truncation fallback concatenates original message content
        combined = " ".join(str(m.get("content", "")) for m in sys_msgs)
        assert len(combined) > 50, "Fallback content is suspiciously empty"


class TestLLMFailureWarnsBannerViaEmitFn:
    """Failing LLM must emit a visible warning banner via emit_fn."""

    def test_warning_banner_emitted_on_failure(self):
        """emit_fn receives an 'AI Summary Unavailable' banner when LLM fails."""
        hist = _make_history()
        cfg = _make_cfg()
        emitted: list[str] = []
        compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
            emit_fn=lambda t: emitted.append(str(t or "")),
        )
        banner_text = "".join(emitted)
        assert "AI Summary Unavailable" in banner_text, (
            "Expected 'AI Summary Unavailable' in emit_fn output, "
            f"but got: {banner_text[:300]!r}"
        )

    def test_no_banner_on_success(self):
        """emit_fn must NOT contain the failure banner when LLM succeeds."""
        hist = _make_history()
        cfg = _make_cfg()
        emitted: list[str] = []
        compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_working_llm, quiet=True,
            emit_fn=lambda t: emitted.append(str(t or "")),
        )
        banner_text = "".join(emitted)
        assert "AI Summary Unavailable" not in banner_text, (
            "Unexpected failure banner in successful compression output."
        )


class TestSuccessfulPathUnchanged:
    """When the LLM succeeds, the summary must contain the LLM output, not a fallback."""

    def test_real_summary_in_result(self):
        """LLM output must appear in the compressed result content."""
        hist = _make_history()
        cfg = _make_cfg()
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_working_llm, quiet=True,
        )
        assert not _summary_is_llm_fallback(result), (
            "compress_history flagged a successful LLM result as a fallback — "
            "false positive in _summary_is_llm_fallback()."
        )
        # Working LLM yields "Completed Work" — must appear
        found = _find_content(result, "Completed Work")
        assert found is not None, (
            "'Completed Work' from the stub LLM not found in compressed result — "
            "the successful summary was not used."
        )

    def test_no_failure_marker_on_success(self):
        """No failure marker must appear when the LLM succeeds."""
        hist = _make_history()
        cfg = _make_cfg()
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_working_llm, quiet=True,
        )
        all_content = " ".join(str(m.get("content", "")) for m in result)
        for marker in _LLM_FAILURE_MARKERS:
            assert marker not in all_content, (
                f"Failure marker {marker!r} present in successful compression output."
            )


class TestRaiseOnLLMFailureFlag:
    """raise_on_llm_failure=True must raise CompressionLLMError instead of degrading."""

    def test_raises_compression_llm_error(self):
        """compress_history must raise CompressionLLMError when opted in."""
        hist = _make_history()
        cfg = _make_cfg()
        with pytest.raises(CompressionLLMError):
            compress_history(
                hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
                raise_on_llm_failure=True,
            )

    def test_no_raise_by_default(self):
        """Default (raise_on_llm_failure=False) must NOT raise on LLM failure."""
        hist = _make_history()
        cfg = _make_cfg()
        # Should return a list, not raise
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
        )
        assert isinstance(result, list), (
            "compress_history should return a list by default, not raise."
        )

    def test_success_does_not_raise_even_when_opted_in(self):
        """raise_on_llm_failure=True must not affect the successful path."""
        hist = _make_history()
        cfg = _make_cfg()
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_working_llm, quiet=True,
            raise_on_llm_failure=True,
        )
        assert isinstance(result, list)
        assert not _summary_is_llm_fallback(result)


class TestSummaryIsLLMFallbackHelper:
    """Unit tests for the _summary_is_llm_fallback() detection helper."""

    def test_detects_single_pass_marker(self):
        marker_content = "[Previous Conversation Summary (5 messages, compression failed)]: some text"
        msgs = [{"role": "system", "content": marker_content}]
        assert _summary_is_llm_fallback(msgs)

    def test_detects_chunked_marker(self):
        marker_content = "[Chunk compression failed (10 messages)]: some text"
        msgs = [{"role": "system", "content": marker_content}]
        assert _summary_is_llm_fallback(msgs)

    def test_detects_compression_failed_marker(self):
        marker_content = "[Compression failed]"
        msgs = [{"role": "system", "content": marker_content}]
        assert _summary_is_llm_fallback(msgs)

    def test_clean_summary_not_detected(self):
        clean_content = "[Previous Conversation Summary (5 messages)]: ## Working Context\n- CWD: /repo"
        msgs = [{"role": "system", "content": clean_content}]
        assert not _summary_is_llm_fallback(msgs)

    def test_empty_list_returns_false(self):
        assert not _summary_is_llm_fallback([])

    def test_none_returns_false(self):
        assert not _summary_is_llm_fallback(None)

    def test_partial_marker_text_without_bracket_anchor_is_not_flagged(self):
        # "compression failed" in plain prose should NOT trigger — markers are bracket-anchored
        prose_content = "The previous compression failed to capture the full context."
        msgs = [{"role": "system", "content": prose_content}]
        assert not _summary_is_llm_fallback(msgs)


class TestChunkedModeFailureSurfaced:
    """Same guarantees apply when COMPRESSION_MODE=chunked."""

    def test_chunked_failure_marker_present(self):
        hist = _make_history(n_pairs=20)
        cfg = _make_cfg(COMPRESSION_MODE="chunked", COMPRESSION_CHUNK_SIZE=5)
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
        )
        assert _summary_is_llm_fallback(result), (
            "Chunked compression failure not surfaced with a marker."
        )

    def test_chunked_failure_banner_emitted(self):
        hist = _make_history(n_pairs=20)
        cfg = _make_cfg(COMPRESSION_MODE="chunked", COMPRESSION_CHUNK_SIZE=5)
        emitted: list[str] = []
        compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_failing_llm, quiet=True,
            emit_fn=lambda t: emitted.append(str(t or "")),
        )
        assert "AI Summary Unavailable" in "".join(emitted)

    def test_chunked_success_no_marker(self):
        hist = _make_history(n_pairs=20)
        cfg = _make_cfg(COMPRESSION_MODE="chunked", COMPRESSION_CHUNK_SIZE=5)
        result = compress_history(
            hist, force=True, cfg=cfg, llm_call_fn=_working_llm, quiet=True,
        )
        assert not _summary_is_llm_fallback(result)
