"""
Context Management Unit Tests

Tests for:
- /window N rolling window (strict N*2 slice + user-first guarantee)
- /compression N auto-compression trigger
- slash command signals
- ReAct-style histories (many assistant msgs per user turn)
- edge cases
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.slash_commands import get_registry


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def make_history(pairs, include_system=True):
    """
    Build a message list from (user, assistant) pairs.
    assistant=None → user message with no reply yet.
    assistant=LIST → multiple assistant messages (simulates ReAct iterations).
    """
    msgs = []
    if include_system:
        msgs.append({"role": "system", "content": "sys"})
    for q, a in pairs:
        msgs.append({"role": "user", "content": q})
        if a is None:
            pass
        elif isinstance(a, list):
            for item in a:
                msgs.append({"role": "assistant", "content": item})
        else:
            msgs.append({"role": "assistant", "content": a})
    return msgs


def make_react_history(n_turns, iters_per_turn=5, include_system=True):
    """
    Build a realistic ReAct history: each user turn has multiple assistant iterations.
    Simulates: user → [assistant tool_call × iters_per_turn] per turn.
    """
    msgs = []
    if include_system:
        msgs.append({"role": "system", "content": "sys"})
    for t in range(n_turns):
        msgs.append({"role": "user", "content": f"Q{t+1}"})
        for i in range(iters_per_turn):
            msgs.append({"role": "assistant", "content": f"A{t+1}_iter{i+1}"})
    return msgs


def apply_window(messages, rolling_window_size):
    """Mirror the strict window logic from main.py."""
    sys_msgs = [m for m in messages if m.get("role") == "system"]
    non_sys  = [m for m in messages if m.get("role") != "system"]

    sliced = non_sys[-(rolling_window_size * 2):]
    while sliced and sliced[0].get("role") != "user":
        sliced = sliced[1:]
    return sys_msgs + (sliced if sliced else non_sys[-2:])


def count_roles(msgs):
    from collections import Counter
    c = Counter(m["role"] for m in msgs)
    return dict(c)


def compression_should_trigger(messages, threshold):
    non_sys_count = sum(1 for m in messages if m.get("role") != "system")
    return non_sys_count > threshold


# ──────────────────────────────────────────────
# Slash command signal tests
# ──────────────────────────────────────────────

class TestSlashCommandSignals:
    def setup_method(self):
        self.registry = get_registry()

    def test_window_valid(self):
        assert self.registry.execute("/window 5")  == "WINDOW_MODE:5"
        assert self.registry.execute("/window 10") == "WINDOW_MODE:10"
        assert self.registry.execute("/window 1")  == "WINDOW_MODE:1"

    def test_window_disable(self):
        assert self.registry.execute("/window 0") == "WINDOW_MODE:0"

    def test_window_invalid_args(self):
        assert self.registry.execute("/window")     == "WINDOW_MODE:0"
        assert self.registry.execute("/window abc") == "WINDOW_MODE:0"
        assert self.registry.execute("/window -1")  == "WINDOW_MODE:0"

    def test_compression_valid(self):
        assert self.registry.execute("/compression 10") == "COMPRESSION_MODE:10"
        assert self.registry.execute("/compression 30") == "COMPRESSION_MODE:30"

    def test_compression_disable(self):
        assert self.registry.execute("/compression 0") == "COMPRESSION_MODE:0"

    def test_compression_invalid_args(self):
        assert self.registry.execute("/compression")     == "COMPRESSION_MODE:0"
        assert self.registry.execute("/compression abc") == "COMPRESSION_MODE:0"

    def test_model_switch(self):
        res = self.registry.execute("/model gpt-4o")
        assert res == "MODEL_SWITCH:gpt-4o"

    def test_model_with_slash(self):
        res = self.registry.execute("/model openrouter/qwen/qwen-2.5-72b")
        assert res == "MODEL_SWITCH:openrouter/qwen/qwen-2.5-72b"


# ──────────────────────────────────────────────
# Core invariants (must hold for any history/window)
# ──────────────────────────────────────────────

class TestWindowInvariants:
    """These must ALWAYS hold regardless of history shape."""

    @pytest.mark.parametrize("window", [1, 2, 3, 5, 10])
    @pytest.mark.parametrize("n_turns,iters", [(3,1),(5,3),(10,5),(3,10),(1,20)])
    def test_strictly_bounded(self, window, n_turns, iters):
        """Non-system count must be ≤ window*2."""
        msgs = make_react_history(n_turns, iters)
        result = apply_window(msgs, window)
        non_sys = [m for m in result if m["role"] != "system"]
        assert len(non_sys) <= window * 2, (
            f"window={window}, turns={n_turns}, iters={iters}: "
            f"got {len(non_sys)} non-sys (max {window*2})"
        )

    @pytest.mark.parametrize("window", [1, 2, 3, 5])
    @pytest.mark.parametrize("n_turns,iters", [(3,1),(5,5),(2,10),(1,3)])
    def test_always_starts_with_user(self, window, n_turns, iters):
        """First non-system message must always be user."""
        msgs = make_react_history(n_turns, iters)
        result = apply_window(msgs, window)
        non_sys = [m for m in result if m["role"] != "system"]
        assert non_sys, "window produced empty non-sys"
        assert non_sys[0]["role"] == "user", (
            f"window={window}, turns={n_turns}, iters={iters}: "
            f"starts with {non_sys[0]['role']!r}"
        )

    @pytest.mark.parametrize("window", [1, 2, 3])
    def test_system_always_preserved(self, window):
        """System message must always appear exactly once."""
        msgs = make_react_history(5, 5)
        result = apply_window(msgs, window)
        sys_count = sum(1 for m in result if m["role"] == "system")
        assert sys_count == 1


# ──────────────────────────────────────────────
# ReAct scenario: many assistant iters per turn
# ──────────────────────────────────────────────

class TestReActWindow:
    def test_react_window3_is_bounded(self):
        """
        10 turns × 5 assistant iters = 50 non-sys.
        window=3 should give ≤ 6 non-sys, not 50.
        """
        msgs = make_react_history(10, iters_per_turn=5)
        result = apply_window(msgs, 3)
        non_sys = [m for m in result if m["role"] != "system"]
        assert len(non_sys) <= 6, f"Expected ≤6 non-sys, got {len(non_sys)}"

    def test_react_window3_vs_large_history(self):
        """Verify window actually shrinks a large ReAct history."""
        msgs = make_react_history(20, iters_per_turn=8)  # 160 non-sys
        total_before = sum(1 for m in msgs if m["role"] != "system")
        result = apply_window(msgs, 3)
        total_after = sum(1 for m in result if m["role"] != "system")
        assert total_after <= 6
        assert total_after < total_before  # must shrink

    def test_react_window_like_real_log(self):
        """
        Simulate the real log: user:11 assistant:28 total:41.
        window=3 should bring this down to ≤6 non-sys.
        """
        # 11 user turns, uneven assistant counts
        msgs = [{"role": "system", "content": "sys"}]
        assistant_counts = [2, 3, 2, 3, 2, 4, 2, 3, 2, 2, 3]  # 28 total
        for i, ac in enumerate(assistant_counts):
            msgs.append({"role": "user", "content": f"Q{i+1}"})
            for j in range(ac):
                msgs.append({"role": "assistant", "content": f"A{i+1}_{j+1}"})

        roles = count_roles(msgs)
        assert roles["user"] == 11
        assert roles["assistant"] == 28

        result = apply_window(msgs, 3)
        non_sys = [m for m in result if m["role"] != "system"]
        user_count = sum(1 for m in non_sys if m["role"] == "user")

        assert len(non_sys) <= 6, f"Expected ≤6 non-sys, got {len(non_sys)}"
        assert non_sys[0]["role"] == "user"
        assert user_count <= 3

    def test_full_history_preserved(self):
        """full_messages must keep everything; window_msgs is the trimmed view."""
        msgs = make_react_history(5, iters_per_turn=4)
        full_before = len(msgs)

        # Simulate one more user turn
        window = 2
        msgs.append({"role": "user", "content": "new question"})
        full_messages = list(msgs)  # copy = full history

        window_msgs = apply_window(full_messages, window)

        # full_messages unchanged
        assert len(full_messages) == full_before + 1

        # window_msgs is smaller
        assert len(window_msgs) < len(full_messages)
        non_sys = [m for m in window_msgs if m["role"] != "system"]
        assert len(non_sys) <= window * 2


# ──────────────────────────────────────────────
# Edge cases
# ──────────────────────────────────────────────

class TestWindowEdgeCases:
    def test_window_larger_than_history(self):
        """window > available pairs → return all messages."""
        msgs = make_history([("Q1","A1"), ("Q2", None)])
        result = apply_window(msgs, 10)
        assert len(result) == len(msgs)

    def test_single_message(self):
        """Single user message — always returns it."""
        msgs = make_history([("Q1", None)])
        result = apply_window(msgs, 1)
        non_sys = [m for m in result if m["role"] != "system"]
        assert non_sys[0]["content"] == "Q1"

    def test_no_system_message(self):
        """Works without system message."""
        msgs = make_react_history(5, 3, include_system=False)
        result = apply_window(msgs, 2)
        non_sys = [m for m in result if m["role"] != "system"]
        assert non_sys[0]["role"] == "user"
        assert len(non_sys) <= 4

    def test_window_1(self):
        """window=1 → only the last user message (+ system)."""
        msgs = make_react_history(5, iters_per_turn=4)
        result = apply_window(msgs, 1)
        non_sys = [m for m in result if m["role"] != "system"]
        assert len(non_sys) <= 2
        assert non_sys[0]["role"] == "user"
        assert non_sys[0]["content"] == "Q5"

    def test_window_bounded_across_turns(self):
        """window_msgs stays bounded across many turns."""
        window = 2
        full_messages = make_history([("Q1","A1"), ("Q2","A2")])

        for turn in range(3, 15):
            full_messages.append({"role": "user", "content": f"Q{turn}"})
            window_msgs = apply_window(full_messages, window)
            non_sys = [m for m in window_msgs if m["role"] != "system"]
            assert len(non_sys) <= window * 2, f"turn={turn}: {len(non_sys)} > {window*2}"
            assert non_sys[0]["role"] == "user"
            # Simulate assistant reply
            full_messages.append({"role": "assistant", "content": f"A{turn}"})


# ──────────────────────────────────────────────
# Auto-compression trigger tests
# ──────────────────────────────────────────────

class TestAutoCompression:
    def test_trigger_above_threshold(self):
        msgs = make_history([("Q1","A1"), ("Q2","A2"), ("Q3", None)])
        assert compression_should_trigger(msgs, 4) is True
        assert compression_should_trigger(msgs, 5) is False

    def test_no_trigger_below_threshold(self):
        msgs = make_history([("Q1","A1")])
        assert compression_should_trigger(msgs, 10) is False

    def test_system_not_counted(self):
        msgs = make_history([("Q1","A1"), ("Q2", None)])  # 3 non-sys
        assert compression_should_trigger(msgs, 3) is False
        assert compression_should_trigger(msgs, 2) is True

    def test_threshold_1(self):
        msgs = make_history([("Q1", None)])
        assert compression_should_trigger(msgs, 1) is False
        msgs.append({"role": "assistant", "content": "A1"})
        assert compression_should_trigger(msgs, 1) is True

    def test_react_history_compression(self):
        """ReAct history with many messages triggers at right threshold."""
        msgs = make_react_history(3, iters_per_turn=5)  # 18 non-sys
        assert compression_should_trigger(msgs, 18) is False
        assert compression_should_trigger(msgs, 17) is True


# ──────────────────────────────────────────────
# Combined: window + compression
# ──────────────────────────────────────────────

class TestWindowAndCompression:
    def test_compression_then_window(self):
        """After compression reduces history, window still works."""
        msgs = make_react_history(10, iters_per_turn=5)  # 50 non-sys

        # Mock compression: keep last 10
        sys_msgs = [m for m in msgs if m["role"] == "system"]
        non_sys = [m for m in msgs if m["role"] != "system"]
        compressed = sys_msgs + non_sys[-10:]

        result = apply_window(compressed, 2)
        non_sys_result = [m for m in result if m["role"] != "system"]
        assert non_sys_result[0]["role"] == "user"
        assert len(non_sys_result) <= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
