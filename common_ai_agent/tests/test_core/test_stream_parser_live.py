"""
test_stream_parser_live.py — Real LLM API integration tests for StreamParser.

Strategy
--------
1. Call the real streaming API (chat_completion_stream).
2. Collect ALL raw chunks into a list (raw_chunks).
3. Replay those exact same chunks through StreamParser.
4. Assert that:
   - content_lines contains no reasoning text
   - reasoning_lines contains no content text
   - raw content text == joined(content_lines) (nothing lost)
   - word fragmentation: no line ending mid-word that is continued on the next line
   - blank line count matches original paragraph breaks

Run (needs API key):
    pytest tests/test_core/test_stream_parser_live.py -v -s
Skip without key:
    pytest tests/test_core/test_stream_parser_live.py -v  # auto-skipped
"""

from __future__ import annotations

import os
import sys
import re
import time
import pytest

# ── path setup ───────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_here))
for _p in (os.path.join(_root, "src"), _root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── API key guard ─────────────────────────────────────────────────────────────
try:
    import config as _cfg
    _HAS_API = bool(getattr(_cfg, "OPENROUTER_API_KEY", None) or getattr(_cfg, "API_KEY", None))
except Exception:
    _HAS_API = False

skip_without_api = pytest.mark.skipif(not _HAS_API, reason="No API key — set OPENROUTER_API_KEY")

from core.stream_parser import StreamParser


# ── helpers ───────────────────────────────────────────────────────────────────

def _collect_stream(messages, model=None, max_tokens=512):
    """Call the real API and return raw_chunks list + elapsed seconds."""
    from llm_client import chat_completion_stream
    t0 = time.time()
    chunks = list(chat_completion_stream(
        messages,
        model=model,
        stop=None,
        skip_rate_limit=True,
        suppress_spinner=True,
    ))
    return chunks, time.time() - t0


def _run_parser(chunks, *, reasoning_display=True, reasoning_in_context=True):
    """Feed chunks through StreamParser; return (content_lines, reasoning_lines, blank_count, collected)."""
    content: list[str] = []
    reasoning: list[str] = []
    blanks = 0

    def on_content(line):
        content.append(line)

    def on_reasoning(line, blank=False):
        if blank:
            pass  # blank counted separately via on_blank
        else:
            reasoning.append(line)

    def on_blank():
        nonlocal blanks
        blanks += 1

    p = StreamParser(
        emit_fn=on_content,
        emit_reasoning_fn=on_reasoning,
        emit_thought_fn=lambda _: None,
        emit_blank_fn=on_blank,
        reasoning_display=reasoning_display,
        reasoning_in_context=reasoning_in_context,
    )
    for chunk in chunks:
        p.feed(chunk)
    collected = p.flush()
    return content, reasoning, blanks, collected


def _raw_content_text(chunks: list) -> str:
    """Join all non-reasoning chunks into a single string."""
    parts = []
    for c in chunks:
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, tuple) and c[0] != "reasoning":
            parts.append(c[1])
    return "".join(parts)


def _raw_reasoning_text(chunks: list) -> str:
    """Join all reasoning chunks into a single string."""
    parts = []
    for c in chunks:
        if isinstance(c, tuple) and c[0] == "reasoning":
            parts.append(c[1])
    return "".join(parts)


def _has_reasoning_tuples(chunks: list) -> bool:
    return any(isinstance(c, tuple) and c[0] == "reasoning" for c in chunks)


def _word_fragments(lines: list[str]) -> list[tuple[str, str]]:
    """
    Return (lineA, lineB) pairs where lineA ends mid-word and lineB starts
    with lowercase continuation (heuristic for bad fragmentation).
    e.g. lineA="I need to search the exa", lineB="ct text string"

    Exclusions:
    - Lines starting with backtick are code-fence markers (`python, ```, etc.)
      and are never word-fragment sources.
    """
    frags = []
    for i in range(len(lines) - 1):
        a, b = lines[i], lines[i + 1]
        # Skip code-fence opener/closer lines (start with backtick)
        if a.startswith("`"):
            continue
        # lineA ends with a letter (no space, no punctuation) AND lineB starts lowercase
        if a and b and re.search(r"[a-zA-Z]$", a) and re.match(r"[a-z]", b):
            frags.append((a, b))
    return frags


# ── test data ─────────────────────────────────────────────────────────────────

# Prompts designed to elicit different output patterns:
#   (label, system_prompt, user_message, notes)
TEST_CASES = [
    (
        "plain_answer",
        "You are a helpful assistant. Be concise.",
        "List 3 fruits. One per line.",
        "No reasoning, just clean content with newlines.",
    ),
    (
        "step_by_step",
        "You are a helpful assistant.",
        "Count from 1 to 5 and briefly explain what counting is.",
        "Multi-paragraph content — checks blank line handling.",
    ),
    (
        "reasoning_heavy",
        "You are a careful analyst. Think step by step before answering.",
        "What is 17 * 13? Show your work.",
        "Likely to produce reasoning (either <think> or reasoning tuples).",
    ),
    (
        "code_output",
        "You are a coding assistant.",
        "Write a Python one-liner that reverses a string. Explain it briefly.",
        "Code + explanation — checks mixed content.",
    ),
    (
        "multilingual",
        "You are a helpful assistant.",
        "Translate 'Hello, how are you?' into Korean and Japanese.",
        "Unicode content — checks no character corruption.",
    ),
]


# ── main tests ─────────────────────────────────────────────────────────────────

@skip_without_api
class TestStreamParserLive:
    """End-to-end tests: real API stream → StreamParser → assertions."""

    @pytest.mark.parametrize("label,system,user,_note", TEST_CASES)
    def test_content_not_empty(self, label, system, user, _note):
        """Parser must emit at least one content line for any real response."""
        messages = [{"role": "system", "content": system},
                    {"role": "user",   "content": user}]
        chunks, elapsed = _collect_stream(messages)
        assert chunks, f"[{label}] API returned no chunks (elapsed={elapsed:.1f}s)"

        content, _, _, _ = _run_parser(chunks)
        assert len(content) > 0, (
            f"[{label}] StreamParser emitted no content lines.\n"
            f"  raw_chunks={chunks[:10]}"
        )

    @pytest.mark.parametrize("label,system,user,_note", TEST_CASES)
    def test_no_word_fragmentation(self, label, system, user, _note):
        """No content line should end mid-word with the next line being a lowercase continuation."""
        messages = [{"role": "system", "content": system},
                    {"role": "user",   "content": user}]
        chunks, _ = _collect_stream(messages)
        content, _, _, _ = _run_parser(chunks)

        frags = _word_fragments(content)
        assert not frags, (
            f"[{label}] Word fragments detected in content output:\n"
            + "\n".join(f"  '{a}' → '{b}'" for a, b in frags[:5])
            + f"\n  Full content: {content}"
        )

    @pytest.mark.parametrize("label,system,user,_note", TEST_CASES)
    def test_no_empty_content_lines(self, label, system, user, _note):
        """Content lines must never be empty strings."""
        messages = [{"role": "system", "content": system},
                    {"role": "user",   "content": user}]
        chunks, _ = _collect_stream(messages)
        content, _, _, _ = _run_parser(chunks)

        empties = [i for i, line in enumerate(content) if not line.strip()]
        assert not empties, (
            f"[{label}] Empty content lines at indices {empties}: {content}"
        )

    @pytest.mark.parametrize("label,system,user,_note", TEST_CASES)
    def test_collected_equals_raw_content(self, label, system, user, _note):
        """
        collected (what StreamParser accumulates) must equal the raw content text.
        This catches any text that was silently dropped.
        """
        messages = [{"role": "system", "content": system},
                    {"role": "user",   "content": user}]
        chunks, _ = _collect_stream(messages)
        _, _, _, collected = _run_parser(chunks, reasoning_in_context=False)

        raw = _raw_content_text(chunks).strip()
        assert collected.strip() == raw, (
            f"[{label}] collected != raw_content\n"
            f"  raw   ({len(raw)} chars): {raw[:200]!r}\n"
            f"  coll  ({len(collected)} chars): {collected[:200]!r}"
        )

    def test_reasoning_separation_when_tuples_present(self):
        """
        If the API sends ("reasoning", ...) tuples, they must:
          - appear in reasoning_lines (not content_lines)
          - NOT be present in content_lines
        """
        messages = [
            {"role": "system", "content": "Think carefully before answering."},
            {"role": "user",   "content": "What is the square root of 144? Explain why."},
        ]
        chunks, _ = _collect_stream(messages)

        if not _has_reasoning_tuples(chunks):
            pytest.skip("Model did not emit reasoning tuples — skip separation test")

        content, reasoning, _, _ = _run_parser(chunks, reasoning_display=True)
        raw_reasoning = _raw_reasoning_text(chunks)

        # Reasoning text should end up in reasoning_lines
        assert len(reasoning) > 0, (
            "API sent reasoning tuples but StreamParser emitted nothing to reasoning_lines.\n"
            f"  raw_reasoning: {raw_reasoning[:300]!r}"
        )

        # No reasoning text should bleed into content_lines
        content_joined = " ".join(content)
        reasoning_joined = " ".join(reasoning)

        # Take a sample of reasoning words and ensure they don't appear verbatim in content
        # (use first sentence as a fingerprint)
        first_sentence = raw_reasoning.split(".")[0].strip()
        if len(first_sentence) > 20:
            assert first_sentence not in content_joined, (
                f"Reasoning bleed detected: first reasoning sentence found in content!\n"
                f"  sentence: {first_sentence!r}\n"
                f"  content:  {content_joined[:400]!r}"
            )

    def test_think_tag_separation(self):
        """
        If the model wraps reasoning in <think>...</think> tags, those lines
        must appear in reasoning_lines, not content_lines.
        """
        # Use a prompt that's known to trigger <think> on some models
        messages = [
            {"role": "user", "content": "<think>test</think>\nJust say 'done'."},
        ]
        # Inject a synthetic think-tag stream to test the parser in isolation
        synthetic_chunks = [
            "<think>\n",
            "internal step 1\n",
            "internal step 2\n",
            "</think>\n",
            "done\n",
        ]
        content, reasoning, _, _ = _run_parser(
            synthetic_chunks, reasoning_display=True
        )

        assert "done" in content, f"'done' not in content: {content}"
        assert not any("<think>" in c or "</think>" in c for c in content), (
            f"<think> tags leaked into content: {content}"
        )
        assert any("step" in r for r in reasoning), (
            f"Think-block content not routed to reasoning: {reasoning}"
        )

    def test_reasoning_suppressed_when_display_off(self):
        """With reasoning_display=False, reasoning tuples must produce no output at all."""
        messages = [
            {"role": "system", "content": "Think step by step."},
            {"role": "user",   "content": "Is 97 prime?"},
        ]
        chunks, _ = _collect_stream(messages)

        if not _has_reasoning_tuples(chunks):
            # Still test with synthetic reasoning tuples
            chunks = [("reasoning", "secret thought\n"), "Yes, 97 is prime.\n"]

        content, reasoning, _, _ = _run_parser(chunks, reasoning_display=False)

        assert reasoning == [], (
            f"reasoning_display=False but got reasoning output: {reasoning}"
        )

    def test_blank_lines_preserved_in_content(self):
        """
        Multi-paragraph responses must preserve blank lines between paragraphs.
        """
        messages = [
            {"role": "system", "content": "Use paragraph breaks in your answer."},
            {"role": "user",   "content": "Describe a cat in two short paragraphs."},
        ]
        chunks, _ = _collect_stream(messages)
        raw = _raw_content_text(chunks)
        raw_blank_count = raw.count("\n\n")

        _, _, blank_count, _ = _run_parser(chunks)

        if raw_blank_count > 0:
            assert blank_count > 0, (
                f"Raw response had {raw_blank_count} blank lines but parser emitted 0.\n"
                f"  raw (first 300): {raw[:300]!r}"
            )

    @pytest.mark.parametrize("label,system,user,_note", TEST_CASES)
    def test_replay_stability(self, label, system, user, _note):
        """
        Replaying the exact same chunk list twice must produce identical output.
        (Parser is stateless between runs — uses a fresh instance each call.)
        """
        messages = [{"role": "system", "content": system},
                    {"role": "user",   "content": user}]
        chunks, _ = _collect_stream(messages)

        content1, reasoning1, blanks1, _ = _run_parser(chunks)
        content2, reasoning2, blanks2, _ = _run_parser(chunks)

        assert content1 == content2, (
            f"[{label}] Non-deterministic content between two replays:\n"
            f"  run1: {content1}\n  run2: {content2}"
        )
        assert reasoning1 == reasoning2, (
            f"[{label}] Non-deterministic reasoning between two replays"
        )
        assert blanks1 == blanks2


# ── detailed diagnostic test (run with -s to see output) ──────────────────────

@skip_without_api
class TestStreamParserLiveDiagnostic:
    """
    Diagnostic test — not a pass/fail test, but prints a detailed side-by-side
    comparison of raw stream vs parsed output.  Run with `pytest -s` to see.
    """

    def test_show_raw_vs_parsed(self, capsys):
        """Print raw stream chunks alongside parsed output for manual review."""
        messages = [
            {"role": "system", "content": "Think step by step. Be thorough."},
            {"role": "user",   "content": "Explain how a binary search works in 3 steps."},
        ]
        chunks, elapsed = _collect_stream(messages)

        content, reasoning, blanks, collected = _run_parser(
            chunks, reasoning_display=True, reasoning_in_context=True
        )

        has_reasoning = _has_reasoning_tuples(chunks)
        raw_content = _raw_content_text(chunks)
        raw_reasoning = _raw_reasoning_text(chunks)

        with capsys.disabled():
            print(f"\n{'='*60}")
            print(f"API elapsed: {elapsed:.1f}s  |  total chunks: {len(chunks)}")
            print(f"Has reasoning tuples: {has_reasoning}")
            print(f"{'─'*60}")
            print(f"RAW CONTENT ({len(raw_content)} chars):")
            for i, line in enumerate(raw_content.splitlines()):
                print(f"  [{i:02d}] {line!r}")
            print(f"{'─'*60}")
            print(f"RAW REASONING ({len(raw_reasoning)} chars):")
            for i, line in enumerate(raw_reasoning.splitlines()[:20]):
                print(f"  [{i:02d}] {line!r}")
            print(f"{'─'*60}")
            print(f"PARSED CONTENT ({len(content)} lines):")
            for i, line in enumerate(content):
                print(f"  [{i:02d}] {line!r}")
            print(f"PARSED REASONING ({len(reasoning)} lines, {blanks} blanks):")
            for i, line in enumerate(reasoning[:20]):
                print(f"  [{i:02d}] {line!r}")
            print(f"{'─'*60}")
            frags = _word_fragments(content)
            print(f"Word fragments: {len(frags)}")
            for a, b in frags:
                print(f"  '{a}' → '{b}'")
            print(f"{'='*60}\n")


# ── GLM-4.7 specific bleed regression test ───────────────────────────────────

GLM_MODEL = "z-ai/glm-4.7"


@skip_without_api
class TestGLMStreamingBleed:
    """
    GLM-4.7 is known to split a reasoning token mid-word and put the tail in the
    content delta of the SAME chunk. Without the streaming bleed fix in llm_client,
    the tail token appears as content, causing visible artefacts like:

        ...approach to           ← last reasoning line
                                 ← blank line (transition marker)
        e key sections...        ← content that should have been reasoning

    These tests confirm the fix prevents that.
    """

    def test_no_reasoning_bleed_into_content(self, capsys):
        """Reasoning text must not appear verbatim in content output."""
        messages = [
            {"role": "system", "content": "Think step by step. Be very thorough."},
            {"role": "user",   "content": "How does a PCIe TLP completion work? Explain briefly."},
        ]
        chunks, elapsed = _collect_stream(messages, model=GLM_MODEL)

        if not _has_reasoning_tuples(chunks):
            pytest.skip("GLM model did not emit reasoning_content tuples this run")

        content, reasoning, _, _ = _run_parser(chunks, reasoning_display=True)
        raw_reasoning = _raw_reasoning_text(chunks)

        # Verify reasoning text stayed in reasoning, not content
        content_joined = " ".join(content)
        first_sentence = raw_reasoning.split(".")[0].strip()
        if len(first_sentence) > 20:
            assert first_sentence not in content_joined, (
                f"GLM reasoning bleed detected!\n"
                f"  first_reasoning_sentence: {first_sentence!r}\n"
                f"  content: {content_joined[:400]!r}"
            )

    def test_content_does_not_start_lowercase_after_reasoning(self, capsys):
        """
        After the reasoning block, the first content word must start with uppercase
        (or be code/punctuation). A lowercase start indicates a bleed tail.
        """
        messages = [
            {"role": "system", "content": "Think step by step. Be thorough."},
            {"role": "user",   "content": "What is AXI back-pressure and why does it matter?"},
        ]
        chunks, _ = _collect_stream(messages, model=GLM_MODEL)

        if not _has_reasoning_tuples(chunks):
            pytest.skip("GLM model did not emit reasoning_content tuples this run")

        content, _, _, _ = _run_parser(chunks, reasoning_display=True)
        if not content:
            pytest.skip("No content lines to check")

        first_line = content[0].lstrip()
        first_char = first_line[:1]
        assert not (first_char and first_char.islower()), (
            f"Content starts with lowercase '{first_char}' — likely reasoning bleed tail.\n"
            f"  first content line: {content[0]!r}\n"
            f"  all content: {content}"
        )

    def test_show_glm_raw_vs_parsed(self, capsys):
        """Diagnostic: print raw GLM stream vs parsed output side by side."""
        messages = [
            {"role": "system", "content": "Think step by step. Be thorough."},
            {"role": "user",   "content": "Explain AXI handshake in 3 steps."},
        ]
        chunks, elapsed = _collect_stream(messages, model=GLM_MODEL)
        content, reasoning, blanks, _ = _run_parser(
            chunks, reasoning_display=True, reasoning_in_context=True
        )
        raw_content  = _raw_content_text(chunks)
        raw_reasoning = _raw_reasoning_text(chunks)

        with capsys.disabled():
            print(f"\n{'='*60}")
            print(f"[GLM-4.7] elapsed: {elapsed:.1f}s | chunks: {len(chunks)}")
            print(f"Has reasoning tuples: {_has_reasoning_tuples(chunks)}")
            print(f"{'─'*60}")
            print(f"RAW CONTENT ({len(raw_content)} chars):")
            for i, line in enumerate(raw_content.splitlines()[:15]):
                print(f"  [{i:02d}] {line!r}")
            print(f"RAW REASONING first 10 lines:")
            for i, line in enumerate(raw_reasoning.splitlines()[:10]):
                print(f"  [{i:02d}] {line!r}")
            print(f"{'─'*60}")
            print(f"PARSED CONTENT ({len(content)} lines):")
            for i, line in enumerate(content[:10]):
                print(f"  [{i:02d}] {line!r}")
            print(f"PARSED REASONING ({len(reasoning)} lines, {blanks} blanks):")
            for i, line in enumerate(reasoning[:10]):
                print(f"  [{i:02d}] {line!r}")
            first_content = content[0] if content else ""
            print(f"{'─'*60}")
            print(f"First content char: {first_content[:1]!r} (should be uppercase or code)")
            frags = _word_fragments(content)
            print(f"Word fragments: {len(frags)}")
            print(f"{'='*60}\n")
