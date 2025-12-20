"""
Context Usage Tracker

Tracks token usage across different components:
- System prompt
- Tool definitions
- Memory files
- Messages (conversation history)

Provides Claude Code style visualization.
"""

from typing import Dict, Optional
import os


class ContextTracker:
    """
    Tracks token usage for all context components.

    Uses 4 chars ≈ 1 token heuristic for estimation.
    """

    def __init__(self, max_tokens: int = 200000):
        """
        Initialize context tracker.

        Args:
            max_tokens: Maximum context window size
        """
        self.max_tokens = max_tokens
        self.system_prompt_tokens = 0
        self.tools_tokens = 0
        self.memory_tokens = 0
        self.messages_tokens = 0
        self.message_count = 0
        self.actual_percentage = 0

    def update_system_prompt(self, prompt: str):
        """Update system prompt token count"""
        self.system_prompt_tokens = len(prompt) // 4

    def update_tools(self, tools_json: str):
        """Update tools definition token count"""
        self.tools_tokens = len(tools_json) // 4

    def update_memory(self, memory_content: Dict[str, str]):
        """
        Update memory files token count.

        Args:
            memory_content: Dict of {filename: content}
        """
        total_chars = sum(len(content) for content in memory_content.values())
        self.memory_tokens = total_chars // 4

    def update_messages(self, messages: list, exclude_system: bool = True):
        """
        Update messages token count.

        Uses actual token counts from message metadata if available,
        otherwise falls back to estimation.

        Args:
            messages: List of message dicts with "content" and optional "_tokens"
            exclude_system: If True, exclude system message (already counted in system_prompt)
        """
        from llm_client import estimate_message_tokens

        if exclude_system:
            # Skip first message if it's system role
            msg_list = [m for m in messages if m.get("role") != "system"]
        else:
            msg_list = messages

        total_tokens = 0
        actual_count = 0
        estimated_count = 0
        assistant_count = 0
        assistant_with_actual = 0

        for msg in msg_list:
            # Track assistant messages separately
            is_assistant = msg.get("role") == "assistant"
            if is_assistant:
                assistant_count += 1

            # Use actual token count from metadata if available (for assistant messages)
            if "_tokens" in msg and is_assistant:
                # Message has actual token metadata from API
                # CRITICAL FIX: Only use valid output tokens, not the total request tokens!
                tokens_meta = msg["_tokens"]
                
                # Try to get output/completion tokens specifically
                output_tokens = tokens_meta.get("completion_tokens", 
                               tokens_meta.get("output_tokens", 
                               tokens_meta.get("output", 0)))
                
                if output_tokens > 0:
                    msg_tokens = output_tokens
                    total_tokens += msg_tokens
                    actual_count += 1
                    assistant_with_actual += 1
                else:
                    # Fallback if metadata doesn't have clear output count
                    # Estimate based on content
                    content = str(msg.get("content", ""))
                    msg_tokens = len(content) // 4
                    total_tokens += msg_tokens
                    estimated_count += 1
            else:
                 # Fallback for user/system messages or assistant without metadata
                 # Estimate based on content
                content = str(msg.get("content", ""))
                msg_tokens = len(content) // 4
                total_tokens += msg_tokens
                estimated_count += 1


        self.messages_tokens = total_tokens
        self.message_count = len(msg_list)  # Store count for display

        # Calculate percentage based on ASSISTANT messages only
        # (user messages never have _tokens, so they skew the percentage)
        if assistant_count > 0:
            self.actual_percentage = (assistant_with_actual / assistant_count) * 100
        elif actual_count > 0:
            # No assistant messages but have some actual tokens (edge case)
            self.actual_percentage = (actual_count / len(msg_list)) * 100
        else:
            self.actual_percentage = 0

        # Store stats for debugging
        self._message_stats = {
            "total_messages": len(msg_list),
            "with_actual_tokens": actual_count,
            "with_estimated_tokens": estimated_count,
            "assistant_messages": assistant_count,
            "assistant_with_actual": assistant_with_actual
        }

    def get_total_tokens(self) -> int:
        """Get total tokens used"""
        return (self.system_prompt_tokens +
                self.tools_tokens +
                self.memory_tokens +
                self.messages_tokens)

    def get_free_tokens(self) -> int:
        """Get remaining free tokens"""
        return max(0, self.max_tokens - self.get_total_tokens())

    def get_usage_percentage(self) -> float:
        """Get usage as percentage (0-100)"""
        total = self.get_total_tokens()
        return (total / self.max_tokens) * 100 if self.max_tokens > 0 else 0

    def format_tokens(self, tokens: int) -> str:
        """
        Format token count for display.

        Examples:
            1234 -> "1.2k"
            12345 -> "12.3k"
            123456 -> "123k"
        """
        if tokens >= 1000:
            return f"{tokens / 1000:.1f}k"
        return str(tokens)

    def get_bar_char(self, percentage: float) -> str:
        """
        Get bar character based on usage percentage.

        Args:
            percentage: Usage percentage (0-100)

        Returns:
            Character: ⛁ (used), ⛀ (partial), ⛶ (free)
        """
        if percentage >= 100:
            return "⛁"  # Full block
        elif percentage >= 50:
            return "⛀"  # Half block
        else:
            return "⛶"  # Empty block

    def create_usage_bar(self, component_tokens: int, bar_width: int = 10) -> str:
        """
        Create visual usage bar for a component.

        Args:
            component_tokens: Tokens used by component
            bar_width: Number of characters in bar

        Returns:
            String like "⛁ ⛁ ⛀ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶"
        """
        tokens_per_block = self.max_tokens / bar_width
        filled_blocks = component_tokens / tokens_per_block

        chars = []
        for i in range(bar_width):
            remaining = filled_blocks - i
            if remaining >= 1.0:
                chars.append("⛁")
            elif remaining >= 0.5:
                chars.append("⛀")
            else:
                chars.append("⛶")

        return " ".join(chars)

    def create_overall_bar(self, bar_width: int = 10) -> str:
        """
        Create overall usage bar showing all components.

        Returns colored segments for each component.
        """
        tokens_per_block = self.max_tokens / bar_width

        # Calculate blocks for each component
        components = [
            self.system_prompt_tokens,
            self.tools_tokens,
            self.memory_tokens,
            self.messages_tokens,
        ]

        # Build bar from left to right
        chars = []
        current_total = 0

        for comp_tokens in components:
            current_total += comp_tokens
            blocks_needed = int((current_total / tokens_per_block))

            while len(chars) < blocks_needed and len(chars) < bar_width:
                chars.append("⛁")

        # Add half block if needed
        if len(chars) < bar_width:
            remaining_tokens = current_total - (len(chars) * tokens_per_block)
            if remaining_tokens >= tokens_per_block * 0.5:
                chars.append("⛀")

        # Fill rest with empty blocks
        while len(chars) < bar_width:
            chars.append("⛶")

        return " ".join(chars)

    def visualize(self, model_name: str = "deepseek-chat", actual_total: int = None) -> str:
        """
        Create Claude Code style visualization.

        Args:
            model_name: Name of the model being used
            actual_total: Actual total tokens from API (if available)

        Returns:
            Formatted string with usage visualization
        """
        # Use actual total from API if available
        # OR if messages have mostly actual tokens (>50%), use calculated total
        actual_pct = getattr(self, 'actual_percentage', 0)
        has_mostly_actual = actual_pct >= 50.0

        if actual_total is not None and actual_total > 0:
            total_tokens = actual_total
            usage_pct = (total_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0
            free_tokens = max(0, self.max_tokens - total_tokens)
            is_actual = True
        elif has_mostly_actual and self.message_count > 0:
            # Messages have mostly actual tokens, use calculated total
            total_tokens = self.get_total_tokens()
            free_tokens = self.get_free_tokens()
            usage_pct = self.get_usage_percentage()
            is_actual = True
        else:
            # Fall back to estimation
            total_tokens = self.get_total_tokens()
            free_tokens = self.get_free_tokens()
            usage_pct = self.get_usage_percentage()
            is_actual = False

        # Format numbers
        total_str = self.format_tokens(total_tokens)
        max_str = self.format_tokens(self.max_tokens)
        free_str = self.format_tokens(free_tokens)

        lines = []
        lines.append("")
        lines.append(" Context Usage")

        # Overall bar with model info
        overall_bar = self.create_overall_bar(10)

        # Show actual vs estimated
        if is_actual:
            if actual_total is not None and actual_total > 0:
                lines.append(f" {overall_bar}   {model_name} · {total_str}/{max_str} tokens ({usage_pct:.1f}%) [API actual]")
            else:
                # Mostly actual from saved metadata
                lines.append(f" {overall_bar}   {model_name} · {total_str}/{max_str} tokens ({usage_pct:.1f}%) [saved tokens]")
        else:
            lines.append(f" {overall_bar}   {model_name} · {total_str}/{max_str} tokens ({usage_pct:.1f}%) [estimated]")

        # Individual component bars
        # When using actual total, estimate breakdown
        msg_count = getattr(self, 'message_count', 0)

        if actual_total is not None and actual_total > 0:
            # Estimate system prompt tokens
            system_est = self.system_prompt_tokens if self.system_prompt_tokens > 0 else 0
            messages_est = max(0, actual_total - system_est)

            components = [
                ("System (includes tools, memory, graph)", system_est, "⛁"),
                (f"Messages ({msg_count} msgs)", messages_est, "⛁"),
            ]
        else:
            components = [
                ("System (includes tools, memory, graph)", self.system_prompt_tokens, "⛁"),
                ("System tools", self.tools_tokens, "⛁"),
                ("Memory files", self.memory_tokens, "⛁"),
                (f"Messages ({msg_count} msgs)", self.messages_tokens, "⛁"),
            ]

        for name, tokens, icon in components:
            if tokens > 0:
                bar = self.create_usage_bar(tokens, 10)
                tokens_str = self.format_tokens(tokens)
                pct = (tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0
                lines.append(f" {bar}   {icon} {name}: {tokens_str} tokens ({pct:.1f}%)")

        # Free space bar
        free_bar = self.create_usage_bar(0, 10)  # All empty
        free_pct = 100 - usage_pct
        if free_tokens < 0:
            lines.append(f" {free_bar}   ⛶ Free space: {free_str} ({free_pct:.1f}%) ⚠️  OVER LIMIT!")
        else:
            lines.append(f" {free_bar}   ⛶ Free space: {free_str} ({free_pct:.1f}%)")

        lines.append("")

        return "\n".join(lines)


# Global instance
_tracker: Optional[ContextTracker] = None


def get_tracker(max_tokens: int = 200000) -> ContextTracker:
    """
    Get global context tracker instance.

    Args:
        max_tokens: Maximum context window size

    Returns:
        ContextTracker instance
    """
    global _tracker
    if _tracker is None:
        _tracker = ContextTracker(max_tokens)
    return _tracker


def reset_tracker(max_tokens: int = 200000):
    """Reset global tracker"""
    global _tracker
    _tracker = ContextTracker(max_tokens)


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":
    # Test visualization
    tracker = ContextTracker(max_tokens=200000)

    # Simulate usage
    tracker.system_prompt_tokens = 3700
    tracker.tools_tokens = 15400
    tracker.memory_tokens = 6700
    tracker.messages_tokens = 8

    print(tracker.visualize("claude-sonnet-4-5-20250929"))

    # Test with more usage
    print("\n" + "=" * 60)
    print("High Usage Example")
    print("=" * 60)

    tracker2 = ContextTracker(max_tokens=200000)
    tracker2.system_prompt_tokens = 10000
    tracker2.tools_tokens = 30000
    tracker2.memory_tokens = 50000
    tracker2.messages_tokens = 80000

    print(tracker2.visualize("deepseek-chat"))
