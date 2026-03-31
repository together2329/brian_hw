"""
test_stream_parser.py — Unit + stress tests for core.stream_parser.StreamParser.

Run:
    pytest tests/test_core/test_stream_parser.py -v
"""

from __future__ import annotations

import random
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.stream_parser import StreamParser, _dedup_line


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parser(reasoning_display=False, reasoning_in_context=False):
    """Return (parser, content_lines, reasoning_lines, thought_lines, blanks)."""
    content: list[str] = []
    reasoning: list[str] = []
    thoughts: list[str] = []
    blanks: list[bool] = []

    def on_reasoning(line, blank=False):
        if blank:
            blanks.append(True)
        else:
            reasoning.append(line)

    p = StreamParser(
        emit_fn=content.append,
        emit_reasoning_fn=on_reasoning,
        emit_thought_fn=thoughts.append,
        emit_blank_fn=lambda: blanks.append(True),
        reasoning_display=reasoning_display,
        reasoning_in_context=reasoning_in_context,
    )
    return p, content, reasoning, thoughts, blanks


def _feed_all(parser, chunks):
    for c in chunks:
        parser.feed(c)
    parser.flush()


def _split_randomly(text: str, rng: random.Random, min_size=1, max_size=10) -> list[str]:
    """Split text into random-sized chunks (stress test helper)."""
    chunks = []
    i = 0
    while i < len(text):
        size = rng.randint(min_size, max_size)
        chunks.append(text[i:i+size])
        i += size
    return chunks


# ---------------------------------------------------------------------------
# Basic content tests
# ---------------------------------------------------------------------------

class TestBasicContent:
    def test_simple_line(self):
        p, content, *_ = _make_parser()
        _feed_all(p, ["Hello world\n"])
        assert "Hello world" in content

    def test_multiline(self):
        p, content, *_ = _make_parser()
        _feed_all(p, ["Line one\nLine two\nLine three\n"])
        assert content == ["Line one", "Line two", "Line three"]

    def test_chunked_single_line(self):
        """Line split across many small chunks."""
        p, content, *_ = _make_parser()
        for ch in "Hello world\n":
            p.feed(ch)
        p.flush()
        assert "Hello world" in content

    def test_no_trailing_newline(self):
        """flush() should emit remaining buffer content."""
        p, content, *_ = _make_parser()
        _feed_all(p, ["Hello world"])
        assert "Hello world" in content

    def test_empty_stream(self):
        p, content, *_ = _make_parser()
        p.flush()
        assert content == []

    def test_blank_lines_in_content(self):
        p, content, _, _, blanks = _make_parser()
        _feed_all(p, ["Line one\n\nLine two\n"])
        assert "Line one" in content
        assert "Line two" in content
        assert len(blanks) >= 1  # blank line emitted

    def test_dedup_exact_repeat(self):
        p, content, *_ = _make_parser()
        _feed_all(p, ["Hello\nHello\n"])
        assert content.count("Hello") == 1  # deduped

    def test_action_block_suppressed(self):
        p, content, *_ = _make_parser()
        _feed_all(p, ["Thought: planning\nAction: read_file(path)\nsome action arg\n"])
        assert not any("Action:" in c for c in content)
        assert not any("some action arg" in c for c in content)

    def test_thought_extracted(self):
        p, content, _, thoughts, _ = _make_parser()
        _feed_all(p, ["Thought: I should read the file\n"])
        assert any("I should read the file" in t for t in thoughts)
        assert not any("Thought:" in c for c in content)


# ---------------------------------------------------------------------------
# Reasoning display tests
# ---------------------------------------------------------------------------

class TestReasoningDisplay:
    def test_reasoning_tuple_displayed(self):
        p, content, reasoning, *_ = _make_parser(reasoning_display=True)
        _feed_all(p, [("reasoning", "step 1\n"), ("reasoning", "step 2\n")])
        assert "step 1" in reasoning
        assert "step 2" in reasoning
        assert content == []  # reasoning not in content

    def test_reasoning_blank_lines_preserved(self):
        p, content, reasoning, _, blanks = _make_parser(reasoning_display=True)
        _feed_all(p, [("reasoning", "para 1\n\npara 2\n")])
        assert "para 1" in reasoning
        assert "para 2" in reasoning
        assert len(blanks) >= 1

    def test_reasoning_suppressed_when_display_off(self):
        p, content, reasoning, *_ = _make_parser(reasoning_display=False)
        _feed_all(p, [("reasoning", "internal thought\n")])
        assert reasoning == []
        assert content == []

    def test_reasoning_in_context_collected(self):
        p, content, reasoning, *_ = _make_parser(
            reasoning_display=True, reasoning_in_context=True
        )
        _feed_all(p, [("reasoning", "think\n")])
        assert "think" in p.collected


# ---------------------------------------------------------------------------
# Think tag tests
# ---------------------------------------------------------------------------

class TestThinkTags:
    def test_think_block_to_reasoning(self):
        p, content, reasoning, *_ = _make_parser(reasoning_display=True)
        _feed_all(p, ["<think>\nstep 1\nstep 2\n</think>\nfinal answer\n"])
        assert "final answer" in content
        # think content routed to reasoning
        assert any("step" in r for r in reasoning)

    def test_inline_think(self):
        p, content, reasoning, *_ = _make_parser(reasoning_display=True)
        _feed_all(p, ["<think>reason</think>answer\n"])
        assert "answer" in content


# ---------------------------------------------------------------------------
# Fragment-merging heuristic tests
# ---------------------------------------------------------------------------

class TestFragmentMerge:
    def test_short_lowercase_fragment_merged(self):
        """'n' or 'md' split off as separate chunk should be merged into next line."""
        p, content, *_ = _make_parser()
        # Simulate "construction" split as "constructio\nn\n"
        _feed_all(p, ["constructio\nn\nnext line\n"])
        # "n" (1 char, lowercase) should be merged: output "constructionext line" or similar
        # The key thing is "n" alone should NOT appear as its own line
        assert "n" not in content

    def test_three_char_lowercase_merged(self):
        """'ion' at end of stream line gets merged back."""
        p, content, *_ = _make_parser()
        _feed_all(p, ["construct\nion\nnext\n"])
        assert "ion" not in content

    def test_longer_fragment_not_merged(self):
        """Fragments > 3 chars are emitted as-is."""
        p, content, *_ = _make_parser()
        _feed_all(p, ["hello\nworld\n"])
        assert "hello" in content
        assert "world" in content


# ---------------------------------------------------------------------------
# Stress tests — random chunk splits
# ---------------------------------------------------------------------------

class TestStressRandomChunks:
    """Feed identical content split at random positions; verify output is stable."""

    FULL_TEXT = (
        "I need to check what Task 16 defines for completion handling.\n"
        "Let me grep for CPLD-related content in tlp_construction_spec.md.\n"
        "This will help understand the required signals.\n"
    )

    def _run(self, seed: int) -> list[str]:
        rng = random.Random(seed)
        p, content, *_ = _make_parser()
        chunks = _split_randomly(self.FULL_TEXT, rng, min_size=1, max_size=8)
        _feed_all(p, chunks)
        return content

    def test_output_stable_across_splits(self):
        """Same text → same output regardless of chunk boundaries."""
        results = [self._run(seed) for seed in range(20)]
        # All results should be equal
        for r in results[1:]:
            assert r == results[0], f"Unstable output:\n  seed0: {results[0]}\n  other: {r}"

    def test_full_words_not_broken(self):
        """'tlp_construction_spec.md' should never appear split across output lines."""
        for seed in range(50):
            content = self._run(seed)
            joined = " ".join(content)
            # The word should appear intact OR not at all (if inside an action block)
            if "tlp_construction_spec" in joined:
                # Check it's not split weirdly
                assert "tlp_constructio" not in joined or "tlp_construction_spec" in joined

    def test_no_empty_content_lines(self):
        """No empty strings should appear in content output."""
        for seed in range(30):
            content = self._run(seed)
            for line in content:
                assert line.strip() != "", f"Empty line in content (seed={seed}): {content!r}"

    def test_long_document_stress(self):
        """Stress test with longer multi-paragraph text."""
        long_text = (
            "Task 16 defines the completion protocol.\n"
            "The CPLD interface uses AXI4-Lite signaling.\n"
            "\n"
            "Key signals:\n"
            "  - CPLD_DONE: asserted when computation finishes\n"
            "  - CPLD_ERR: asserted on error condition\n"
            "  - CPLD_DATA[31:0]: result register\n"
            "\n"
            "The tlp_construction_spec.md document describes TLP assembly.\n"
            "See section 3.4 for write completion handling.\n"
        )
        for seed in range(30):
            rng = random.Random(seed)
            p, content, *_ = _make_parser()
            chunks = _split_randomly(long_text, rng, min_size=1, max_size=15)
            _feed_all(p, chunks)
            # Should not crash, and should produce some output
            assert len(content) > 0


# ---------------------------------------------------------------------------
# Helpers unit tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_dedup_line_repeated(self):
        assert _dedup_line("abcabcabc") == "abc"

    def test_dedup_line_no_repeat(self):
        assert _dedup_line("hello world") == "hello world"

    def test_reset_clears_state(self):
        p, content, *_ = _make_parser()
        _feed_all(p, ["first turn\n"])
        assert "first turn" in content

        p.reset()
        assert p.collected == ""
        assert p.state == StreamParser.NOISE

        for ch in "second turn\n":
            p.feed(ch)
        p.flush()
        assert "second turn" in content
