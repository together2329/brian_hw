"""
stream_parser.py — Stateful parser for streaming LLM output.

Processes a stream of text chunks (or ("reasoning", text) tuples) and fires
callbacks for each recognized element.  No I/O happens here; callers supply
the callbacks, making the parser fully testable without mocking sys.stdout.

Usage::

    def on_content(line):   print(f"  {line}")
    def on_reasoning(line): print(f"  {DIM}{line}{RESET}")
    def on_thought(line):   print(f"  Thought:{line}")
    def on_blank():         print()

    p = StreamParser(
        emit_fn=on_content,
        emit_reasoning_fn=on_reasoning,
        emit_thought_fn=on_thought,
        emit_blank_fn=on_blank,
    )
    for chunk in llm_stream:
        p.feed(chunk)
    collected_text = p.flush()
"""

from __future__ import annotations

import re
from typing import Callable, Optional, Set, Tuple, Union

Chunk = Union[str, Tuple[str, str]]  # str | ("reasoning", str)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEDUP_RE = re.compile(r"(.+?)\1{2,}")


def _dedup_line(text: str) -> str:
    """Collapse obvious repeated substrings (e.g. LLM output artifacts)."""
    return _DEDUP_RE.sub(r"\1", text)


# ---------------------------------------------------------------------------
# StreamParser
# ---------------------------------------------------------------------------

class StreamParser:
    """
    State machine that processes streaming LLM output.

    States
    ------
    NOISE   — before any content has started (preamble, system tokens)
    CONTENT — regular assistant content
    ACTION  — inside an Action: block (suppressed from display)

    Callbacks
    ---------
    emit_fn(line)          called for each displayable content line
    emit_reasoning_fn(line, blank=False)  called for each reasoning line;
                           blank=True means it's an empty paragraph separator
    emit_thought_fn(line)  called when a "Thought: ..." line is found
    emit_blank_fn()        called for blank lines inside content sections
    """

    NOISE, CONTENT, ACTION = 0, 1, 2

    def __init__(
        self,
        *,
        emit_fn: Callable[[str], None],
        emit_reasoning_fn: Callable[..., None],
        emit_thought_fn: Callable[[str], None],
        emit_blank_fn: Optional[Callable[[], None]] = None,
        reasoning_display: bool = True,
        reasoning_in_context: bool = False,
    ) -> None:
        self._emit = emit_fn
        self._emit_reasoning = emit_reasoning_fn
        self._emit_thought = emit_thought_fn
        self._emit_blank = emit_blank_fn or (lambda: None)

        self.reasoning_display = reasoning_display
        self.reasoning_in_context = reasoning_in_context

        # internal state
        self.state: int = self.NOISE
        self._buf: str = ""          # content buffer
        self._rbuf: str = ""         # reasoning buffer
        self._in_think: bool = False
        self._content_started: bool = False
        self._seen: Set[str] = set()
        self._content_emitted: bool = False
        self._reasoning_emitted: bool = False  # track if any reasoning was displayed

        # collected raw text (for callers that need to parse actions from it)
        self.collected: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def feed(self, chunk: Chunk) -> None:
        """Feed one streaming chunk to the parser."""
        token_type = "content"
        if isinstance(chunk, tuple) and len(chunk) == 2:
            token_type, chunk = chunk  # type: ignore[assignment]

        # Accumulate full content
        if token_type == "reasoning":
            if self.reasoning_in_context:
                self.collected += chunk
        else:
            self.collected += chunk  # type: ignore[operator]

        # ----- reasoning token -----
        if token_type == "reasoning":
            if not chunk:
                return
            if self.reasoning_display:
                self._rbuf += chunk
                self._flush_reasoning_lines()
            return  # never fall through to content processing

        # ----- flush pending reasoning before content -----
        if self._rbuf:
            if self.reasoning_display:
                self._emit_reasoning(self._rbuf)
                self._reasoning_emitted = True
            self._rbuf = ""
            if self._reasoning_emitted:
                self._emit_blank()  # blank line separating reasoning from content
                self._reasoning_emitted = False  # reset — flush() must not fire again

        # ----- content token -----
        self._buf += chunk  # type: ignore[operator]
        self._process_content_lines()

    def flush(self) -> str:
        """
        Flush remaining buffers after the stream ends.
        Returns the full collected text.
        """
        # Flush remaining reasoning
        if self._rbuf:
            if self.reasoning_display:
                self._emit_reasoning(self._rbuf)
                self._reasoning_emitted = True
            self._rbuf = ""

        # Blank line after reasoning block ends (only if content follows or stream ended)
        if self._reasoning_emitted:
            self._emit_blank()
            self._reasoning_emitted = False  # only emit once

        # Flush remaining content
        remaining = self._buf.strip()
        self._buf = ""
        if remaining and self.state != self.ACTION:
            text, _e, _x, _r = self._strip_think(remaining)
            ai = text.lower().find("action:")
            if ai == 0:
                text = ""
            elif ai > 0:
                text = text[:ai].rstrip()
            if text:
                self._emit_dedup(text)

        return self.collected

    def reset(self) -> None:
        """Reset parser to initial state (reuse across turns)."""
        self.state = self.NOISE
        self._buf = ""
        self._rbuf = ""
        self._in_think = False
        self._content_started = False
        self._seen = set()
        self._content_emitted = False
        self._reasoning_emitted = False
        self.collected = ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flush_reasoning_lines(self) -> None:
        while "\n" in self._rbuf:
            rline, self._rbuf = self._rbuf.split("\n", 1)
            if rline.strip():
                self._emit_reasoning(rline)
                self._reasoning_emitted = True
            else:
                self._emit_reasoning("", blank=True)

    def _process_content_lines(self) -> None:
        while "\n" in self._buf:
            raw_line, self._buf = self._buf.split("\n", 1)
            prev_emitted = self._content_emitted
            self._content_emitted = False

            stripped = raw_line.strip()

            # Fragment-merging heuristic: very short all-lowercase fragments
            # that look like continuation of a word split across streaming
            # chunks are pushed back into the buffer.
            if stripped and len(stripped) <= 3 and stripped.islower() and "\n" in self._buf:
                self._buf = stripped + self._buf
                continue

            text, entered, exited, reasoning = self._strip_think(raw_line)

            if reasoning:
                self._emit_reasoning(reasoning)

            if self._in_think and not exited:
                continue

            if not text:
                if self.state == self.CONTENT:
                    self._emit_blank()
                continue

            text_lower = text.lower()
            ai = text_lower.find("action:")
            if ai < 0 and text_lower.strip() == "action":
                ai = 0
            ti = text_lower.find("thought:")

            if ai >= 0 and (ti < 0 or ai < ti):
                self.state = self.ACTION
            elif ti >= 0:
                thought = text[ti + 8:]
                if thought and thought not in self._seen:
                    self._emit_thought(thought)
                    self._seen.add(thought)
                self.state = self.CONTENT
            elif self.state == self.ACTION:
                pass  # inside action block, suppress
            else:
                if self.state == self.NOISE:
                    self.state = self.CONTENT
                    self._content_started = True
                self._emit_dedup(text)

    def _emit_dedup(self, text: str) -> None:
        text = _dedup_line(text)
        # Backtick fences (```) must always be emitted — closing fence is
        # identical to opening and would otherwise be swallowed by dedup.
        is_fence = text.startswith("```")
        if is_fence or text not in self._seen:
            self._emit(text)
            if not is_fence:
                self._seen.add(text)
            self._content_emitted = True

    def _strip_think(self, text: str) -> Tuple[str, bool, bool, str]:
        """Strip <think>...</think> blocks, returning (clean, entered, exited, reasoning)."""
        parts = re.split(r"(</?think>)", text)
        clean, reasoning = [], []
        entered = exited = False
        for p in parts:
            if p == "<think>":
                self._in_think = True
                entered = True
            elif p == "</think>":
                self._in_think = False
                exited = True
            elif p:
                (reasoning if self._in_think else clean).append(p)
        return "".join(clean), entered, exited, "".join(reasoning)
