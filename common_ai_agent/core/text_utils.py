"""
Shared text processing utilities.

Consolidates duplicated regex patterns from:
  - main.py (thinking tag removal, 2 places)
  - core/agent_runner.py (thinking tag removal)
  - src/llm_client.py (metadata token sanitization, 4 places)
  - src/llm_client.py (token estimation, 2 places)
  - src/main.py (token estimation, 2+ places)
"""
import re
from typing import Union, List, Dict, Any


def strip_thinking_tags(text: str) -> str:
    """Remove <think>...</think> blocks and bare <think>/</ think> tags.

    DeepSeek/GLM models sometimes emit reasoning as content instead of
    a separate reasoning field. This removes those tokens before storing
    or processing the response.
    """
    # Full blocks (possibly multiline)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Partial tags (stream cut mid-tag or bare tags)
    text = re.sub(r'</?think>', '', text)
    return text


def strip_metadata_tokens(text: str) -> str:
    """Remove provider metadata tokens from LLM output.

    Handles tokens from OpenRouter, DeepSeek, Qwen, Mistral, GLM, etc.:
      <|final<|something|>   — malformed combined token
      <|end_of_text|>        — EOS token
      <|im_start|>           — ChatML tokens
      <|end_of               — stream-truncated partial token
    """
    text = re.sub(r'<\|final<\|[^>]*\|>', '', text)
    text = re.sub(r'<\|[^|<>]+\|>', '', text)
    text = re.sub(r'<\|[a-z_]+$', '', text)
    return text


def estimate_tokens(text_or_messages: Union[str, List[Dict[str, Any]]]) -> int:
    """Estimate token count using the 4-chars-per-token heuristic.

    Accepts either a plain string or a list of message dicts
    (OpenAI chat format). Structured content (list-type content field)
    is handled by extracting the 'text' key from each block.
    """
    if isinstance(text_or_messages, str):
        return len(text_or_messages) // 4

    total_chars = 0
    for msg in text_or_messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total_chars += len(block.get("text", ""))
    return total_chars // 4
