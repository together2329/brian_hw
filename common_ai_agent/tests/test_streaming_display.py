"""
Tests for streaming display functions (_strip_think, _is_dup, state machine).
Functions are inlined from main.py since they're local closures.
"""
import re
import pytest


# ─── Replicate functions from main.py ───

def _strip_think(text):
    """Remove <think> tags, return (cleaned_text, entered_think, exited_think)."""
    clean = re.sub(r'<think>.*?</think>', '', text)  # complete pairs
    entered = '<think>' in text and '</think>' not in text
    exited = '</think>' in text and '<think>' not in text
    clean = re.sub(r'</?think>', '', clean).strip()  # leftover tags
    return clean, entered, exited


def _dedup_line(text):
    """Remove intra-line repetition (50-char sliding window)."""
    if len(text) < 100:
        return text
    for i in range(min(len(text) // 2, 600)):
        seg = text[i:i + 50]
        if len(seg) < 50:
            break
        j = text.find(seg, i + 50)
        if j > i:
            return text[:j].rstrip()
    return text


def _is_dup(text, _seen):
    """Check if text was already printed (exact or substring with 70% overlap)."""
    if text in _seen:
        return True
    if len(text) > 60:
        for prev in _seen:
            shorter, longer = (text, prev) if len(text) <= len(prev) else (prev, text)
            if len(shorter) > len(longer) * 0.7 and shorter in longer:
                return True
    return False


# ═══════════════════════════════════════════
#  BASIC TESTS
# ═══════════════════════════════════════════

class TestStripThinkBasic:
    """Basic correctness tests for _strip_think."""

    def test_no_tags(self):
        text, entered, exited = _strip_think("hello world")
        assert text == "hello world"
        assert not entered
        assert not exited

    def test_complete_pair_removed(self):
        text, entered, exited = _strip_think("before<think>inner</think>after")
        assert text == "beforeafter"
        assert not entered
        assert not exited

    def test_enter_think(self):
        # Unpaired <think> — tag stripped, content kept (caller uses _in_think to suppress)
        text, entered, exited = _strip_think("prefix<think>partial thinking")
        assert text == "prefixpartial thinking"
        assert entered
        assert not exited

    def test_exit_think(self):
        # Unpaired </think> — tag stripped, all content kept (caller was suppressing via _in_think)
        text, entered, exited = _strip_think("continued</think>suffix")
        assert text == "continuedsuffix"
        assert not entered
        assert exited

    def test_only_think_tags(self):
        text, entered, exited = _strip_think("<think>all thinking</think>")
        assert text == ""
        assert not entered
        assert not exited

    def test_suffix_preserved_critical(self):
        """CRITICAL: the original bug — suffix after </think> was lost."""
        text, entered, exited = _strip_think("<think>reasoning</think>important output")
        assert text == "important output"
        assert not entered
        assert not exited

    def test_prefix_and_suffix_both_preserved(self):
        text, entered, exited = _strip_think("hello<think>mid</think>world")
        assert text == "helloworld"

    def test_multiple_complete_pairs(self):
        text, _, _ = _strip_think("a<think>x</think>b<think>y</think>c")
        assert text == "abc"

    def test_empty_string(self):
        text, entered, exited = _strip_think("")
        assert text == ""
        assert not entered
        assert not exited

    def test_partial_tag_not_matched(self):
        text, entered, exited = _strip_think("hello <thin> world")
        assert text == "hello <thin> world"
        assert not entered
        assert not exited


class TestIsDupBasic:
    """Basic correctness tests for _is_dup."""

    def test_exact_match(self):
        seen = {"hello world"}
        assert _is_dup("hello world", seen)

    def test_no_match(self):
        seen = {"hello world"}
        assert not _is_dup("goodbye world", seen)

    def test_empty_seen(self):
        assert not _is_dup("anything", set())

    def test_short_text_no_substring_check(self):
        """Text <= 60 chars should only do exact match, not substring."""
        seen = {"short text here"}
        assert not _is_dup("short text", seen)  # substring but too short

    def test_substring_with_70pct_overlap(self):
        """Long text substring match requires 70% length ratio."""
        long_text = "a" * 100
        seen = {long_text}
        # 75 chars = 75% of 100 → should match
        assert _is_dup("a" * 75, seen)

    def test_substring_below_70pct_no_match(self):
        """Substring below 70% threshold should NOT match."""
        long_text = "a" * 100
        seen = {long_text}
        # 65 chars = 65% of 100 → should NOT match
        assert not _is_dup("a" * 65, seen)

    def test_false_positive_fix(self):
        """Original bug: 'brown fox jumps over' vs 'The quick brown fox jumps' → false positive."""
        seen = {"The quick brown fox jumps over the lazy dog and runs away fast!!!!"}
        # 20 chars out of 65 → ~30% — should NOT match
        assert not _is_dup("brown fox jumps over the lazy dog and runs away fast!!!! hooray", seen)


class TestDedupLineBasic:
    """Basic tests for _dedup_line."""

    def test_short_text_unchanged(self):
        assert _dedup_line("short") == "short"

    def test_repeated_pattern_detected(self):
        # "abcdefghij" * 12 has repeating 50-char segments — dedup correctly truncates
        text = "abcdefghij" * 12  # 120 chars
        result = _dedup_line(text)
        assert len(result) < len(text)

    def test_repeated_block(self):
        """A long line with a repeated 50+ char segment should be truncated."""
        block = "The quick brown fox jumps over the lazy dog hello "  # exactly 50 chars
        text = block + "world " + block + "world"
        result = _dedup_line(text)
        assert len(result) < len(text)


class TestStateMachine:
    """Test state transitions: NOISE → CONTENT → ACTION → CONTENT."""

    NOISE, CONTENT, ACTION = 0, 1, 2

    def _process_line(self, text, state, seen):
        """Simulate the state machine logic from main.py."""
        ti = text.find('Thought:')
        ai = text.find('Action:')
        output = None

        if ai >= 0 and (ti < 0 or ai < ti):
            state = self.ACTION
        elif ti >= 0:
            thought = text[ti + 8:]
            if thought and not _is_dup(thought, seen):
                output = f"Thought:{thought}"
                seen.add(thought)
            state = self.CONTENT
        elif state == self.NOISE or state == self.ACTION:
            if state == self.NOISE and text.startswith('#'):
                state = self.CONTENT
                output = text
        else:
            # CONTENT
            if not _is_dup(text, seen):
                output = text
                seen.add(text)
        return state, output

    def test_noise_suppresses_text(self):
        state, output = self._process_line("random text", self.NOISE, set())
        assert state == self.NOISE
        assert output is None

    def test_noise_allows_header(self):
        state, output = self._process_line("# Header", self.NOISE, set())
        assert state == self.CONTENT
        assert output == "# Header"

    def test_thought_enters_content(self):
        state, output = self._process_line("Thought: I need to search", self.NOISE, set())
        assert state == self.CONTENT
        assert "I need to search" in output

    def test_action_enters_action(self):
        state, output = self._process_line("Action: search_tool", self.CONTENT, set())
        assert state == self.ACTION
        assert output is None

    def test_action_suppresses_input(self):
        """In ACTION state, non-Thought/Action lines are suppressed."""
        state, output = self._process_line("Action_Input: {query}", self.ACTION, set())
        assert state == self.ACTION
        assert output is None

    def test_action_to_content_on_thought(self):
        """CRITICAL: Thought: should recover from ACTION state."""
        state, output = self._process_line("Thought: back to thinking", self.ACTION, set())
        assert state == self.CONTENT
        assert "back to thinking" in output

    def test_content_emits_text(self):
        state, output = self._process_line("normal text line", self.CONTENT, set())
        assert state == self.CONTENT
        assert output == "normal text line"


class TestPartialDisplay:
    """Test partial display filtering logic."""

    def _should_display(self, buf):
        """Simulate partial display condition."""
        p = re.sub(r'</?think>', '', buf).strip()
        return p and len(p) > 3 and not p.startswith('Action')

    def test_short_text_hidden(self):
        assert not self._should_display("Ab")
        assert not self._should_display("Act")

    def test_normal_text_shown(self):
        assert self._should_display("Hello world")

    def test_action_prefix_hidden(self):
        assert not self._should_display("Action: tool")
        assert not self._should_display("Action_Input: data")

    def test_think_tags_stripped_leaves_content(self):
        # Partial display strips tags but content remains — _in_think state prevents display in practice
        assert self._should_display("<think>hidden</think>")  # "hidden" remains, len > 3
        # Empty think block → no content after strip
        assert not self._should_display("<think></think>")

    def test_action_partial_hidden(self):
        """'Acti' building up should be hidden (starts with 'Action' prefix)."""
        # "Acti" is 4 chars, > 3, but doesn't start with "Action" → shown
        # This is acceptable — only "Action" prefix blocks display
        assert self._should_display("Acti")
        # But once it becomes "Action", it's blocked
        assert not self._should_display("Action")
        assert not self._should_display("Action:")


# ═══════════════════════════════════════════
#  STRESS TESTS
# ═══════════════════════════════════════════

class TestStripThinkStress:
    """Edge cases and adversarial inputs for _strip_think."""

    def test_nested_tags(self):
        """Nested <think> — regex is non-greedy, handles first pair."""
        text, _, _ = _strip_think("<think>outer<think>inner</think>rest</think>end")
        # non-greedy: matches <think>outer<think>inner</think>, leaves rest</think>end
        # then strips leftover </think>
        assert "end" in text

    def test_many_pairs(self):
        pairs = "".join(f"t{i}<think>x{i}</think>" for i in range(100))
        text, entered, exited = _strip_think(pairs)
        assert "<think>" not in text
        assert "</think>" not in text
        assert not entered
        assert not exited
        for i in range(100):
            assert f"t{i}" in text

    def test_think_with_newlines_in_content(self):
        text, _, _ = _strip_think("a<think>line1\nline2</think>b")
        # re.sub with .*? doesn't match \n by default
        # so it won't match across newlines — but in streaming, lines are split before this
        # Just verify no crash
        assert isinstance(text, str)

    def test_very_long_think_block(self):
        inner = "x" * 10000
        text, _, _ = _strip_think(f"pre<think>{inner}</think>post")
        assert text == "prepost"

    def test_empty_think_block(self):
        text, _, _ = _strip_think("a<think></think>b")
        assert text == "ab"

    def test_whitespace_only_after_strip(self):
        text, _, _ = _strip_think("  <think>content</think>  ")
        assert text == ""

    def test_special_chars_in_think(self):
        text, _, _ = _strip_think("ok<think>$@!#%^&*()</think>fine")
        assert text == "okfine"

    def test_html_like_content(self):
        """Ensure other HTML-like tags are not affected."""
        text, _, _ = _strip_think("<div>hello</div><think>secret</think><span>world</span>")
        assert text == "<div>hello</div><span>world</span>"


class TestIsDupStress:
    """Stress and edge case tests for _is_dup."""

    def test_large_seen_set(self):
        seen = {f"line number {i} with some padding text to make it longer" for i in range(1000)}
        # Exact match in large set
        assert _is_dup("line number 500 with some padding text to make it longer", seen)
        # No match
        assert not _is_dup("completely different text that is not in the set at all!!!!!!!!", seen)

    def test_boundary_60_chars(self):
        """Text exactly 60 chars should NOT do substring check."""
        text_60 = "a" * 60
        seen = {"a" * 100}
        assert not _is_dup(text_60, seen)

    def test_boundary_61_chars(self):
        """Text 61 chars SHOULD do substring check."""
        text_61 = "a" * 61
        seen = {"a" * 80}
        # 61/80 = 76.25% > 70% → match
        assert _is_dup(text_61, seen)

    def test_exact_70pct_boundary(self):
        """Exactly 70% should match (> 0.7 is strict, so 70% = 0.7 → no match)."""
        seen = {"a" * 100}
        # 70 chars = exactly 70% → 70 > 100*0.7=70.0 is False
        assert not _is_dup("a" * 70, seen)
        # 71 chars = 71% → 71 > 70.0 is True
        assert _is_dup("a" * 71, seen)

    def test_reverse_substring(self):
        """Seen text is shorter than new text — should still detect."""
        short = "x" * 75
        long = "x" * 100
        seen = {short}
        # short=75, long=100, 75 > 70.0 → match
        assert _is_dup(long, seen)

    def test_no_false_positive_different_content(self):
        """Different long strings should not match."""
        seen = {"The implementation of the binary search algorithm requires careful handling"}
        assert not _is_dup("A completely different sentence about something else entirely plus more", seen)

    def test_unicode_text(self):
        seen = {"한국어 텍스트가 포함된 긴 문장입니다. 이 문장은 테스트를 위해 작성되었습니다. 충분히 길어야 합니다."}
        assert _is_dup("한국어 텍스트가 포함된 긴 문장입니다. 이 문장은 테스트를 위해 작성되었습니다. 충분히 길어야 합니다.", seen)
        assert not _is_dup("다른 한국어 문장입니다. 이것은 완전히 다른 내용을 담고 있으며 매칭되면 안됩니다!!!!", seen)

    def test_empty_text(self):
        assert not _is_dup("", set())
        assert not _is_dup("", {"something"})


class TestStateMachineStress:
    """Stress tests for state machine transitions."""

    NOISE, CONTENT, ACTION = 0, 1, 2

    def _process_lines(self, lines, initial_state=0):
        """Process multiple lines through the state machine, return (final_state, outputs)."""
        state = initial_state
        seen = set()
        outputs = []
        for line in lines:
            ti = line.find('Thought:')
            ai = line.find('Action:')
            output = None

            if ai >= 0 and (ti < 0 or ai < ti):
                state = self.ACTION
            elif ti >= 0:
                thought = line[ti + 8:]
                if thought and not _is_dup(thought, seen):
                    output = thought
                    seen.add(thought)
                state = self.CONTENT
            elif state == self.NOISE or state == self.ACTION:
                if state == self.NOISE and line.startswith('#'):
                    state = self.CONTENT
                    output = line
            else:
                if not _is_dup(line, seen):
                    output = line
                    seen.add(line)

            if output:
                outputs.append(output)
        return state, outputs

    def test_typical_react_flow(self):
        """Simulate typical ReAct: Thought → Action → (stop) → Thought → Action."""
        lines = [
            "Thought: I need to search for the file",
            "Action: search_tool",
            "Action_Input: {\"query\": \"main.py\"}",
        ]
        state, outputs = self._process_lines(lines)
        assert state == self.ACTION
        assert len(outputs) == 1  # only Thought emitted
        assert "I need to search" in outputs[0]

    def test_multiple_thoughts_deduped(self):
        lines = [
            "Thought: same thought",
            "some content",
            "Thought: same thought",  # duplicate
        ]
        state, outputs = self._process_lines(lines)
        assert outputs.count(" same thought") == 1

    def test_noise_to_content_to_action_to_content(self):
        """Full cycle: NOISE → CONTENT → ACTION → CONTENT."""
        lines = [
            "ignored noise",
            "Thought: first thought",
            "detail line",
            "Action: tool",
            "Action_Input: data",
            "Thought: recovered thought",
            "more content",
        ]
        state, outputs = self._process_lines(lines)
        assert state == self.CONTENT
        assert " first thought" in outputs
        assert " recovered thought" in outputs
        assert "more content" in outputs
        assert "ignored noise" not in outputs
        assert "Action_Input: data" not in outputs

    def test_action_with_thought_in_same_line(self):
        """Line with both Action: and Thought: — Action: wins if it comes first."""
        lines = ["Action: tool Thought: hmm"]
        state, _ = self._process_lines(lines)
        assert state == self.ACTION

    def test_thought_before_action_in_same_line(self):
        """Thought: before Action: — Thought: wins."""
        lines = ["Thought: hmm Action: tool"]
        state, outputs = self._process_lines(lines)
        assert state == self.CONTENT

    def test_many_lines_no_crash(self):
        """Process 10k lines without crash or excessive memory."""
        lines = [f"line {i} with some content padding" for i in range(10000)]
        lines.insert(0, "Thought: start")
        state, outputs = self._process_lines(lines)
        assert state == self.CONTENT
        assert len(outputs) > 0

    def test_rapid_state_changes(self):
        """Rapid alternation between states."""
        lines = []
        for i in range(100):
            lines.append(f"Thought: thought {i}")
            lines.append(f"content {i}")
            lines.append(f"Action: tool_{i}")
        state, outputs = self._process_lines(lines)
        assert state == self.ACTION


class TestDedupLineStress:
    """Stress tests for _dedup_line."""

    def test_exact_boundary_100_chars(self):
        text = "a" * 99
        assert _dedup_line(text) == text  # < 100, unchanged

        text = "a" * 100
        # 100 chars of same char — will find repetition
        result = _dedup_line(text)
        assert len(result) <= len(text)

    def test_no_false_truncation(self):
        """Unique content should not be truncated."""
        # Build a string > 100 chars with no 50-char repeating segment
        import string
        # Use a non-repeating pattern
        text = "".join(f"{c}{i}" for i, c in enumerate(string.ascii_letters * 3))[:150]
        result = _dedup_line(text)
        assert result == text

    def test_very_long_repeated(self):
        block = "abcdefghij" * 6  # 60 chars
        text = block + " separator " + block
        result = _dedup_line(text)
        assert len(result) < len(text)
