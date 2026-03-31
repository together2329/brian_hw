"""
Conversation history persistence.

Extracted from src/main.py. Handles saving/loading the message list to JSON.
"""
import json
import os
from typing import List, Dict, Any, Optional


def save_conversation_history(
    messages: List[Dict[str, Any]],
    cfg=None,
) -> None:
    """Save conversation history to a JSON file if enabled in config.

    Args:
        messages: List of message dicts to persist.
        cfg:      Config namespace. Defaults to importing the config module.
    """
    if cfg is None:
        import config as cfg  # type: ignore

    if not cfg.SAVE_HISTORY:
        return

    try:
        with open(cfg.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        try:
            from lib.display import Color  # type: ignore
            print(Color.success(f"[System] History saved to {cfg.HISTORY_FILE}"))
        except ImportError:
            print(f"[System] History saved to {cfg.HISTORY_FILE}")
    except Exception as e:
        try:
            from lib.display import Color  # type: ignore
            print(Color.error(f"[System] Failed to save history: {e}"))
        except ImportError:
            print(f"[System] Failed to save history: {e}")


def load_conversation_history(cfg=None) -> Optional[List[Dict[str, Any]]]:
    """Load conversation history from JSON file if it exists.

    Args:
        cfg: Config namespace. Defaults to importing the config module.

    Returns:
        List of message dicts, or None if not available.
    """
    if cfg is None:
        import config as cfg  # type: ignore

    if not cfg.SAVE_HISTORY:
        return None

    try:
        if os.path.exists(cfg.HISTORY_FILE):
            with open(cfg.HISTORY_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            try:
                from lib.display import Color  # type: ignore
                print(Color.success(f"[System] Loaded {len(messages)} messages from {cfg.HISTORY_FILE}"))
            except ImportError:
                print(f"[System] Loaded {len(messages)} messages from {cfg.HISTORY_FILE}")
            return messages
    except Exception as e:
        try:
            from lib.display import Color  # type: ignore
            print(Color.error(f"[System] Failed to load history: {e}"))
        except ImportError:
            print(f"[System] Failed to load history: {e}")

    return None
