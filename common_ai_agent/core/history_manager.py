"""
Conversation history persistence.

Extracted from src/main.py. Handles saving/loading the message list to JSON.

v2 layout (flat project):
  .session/<project>/conversation.json       ← active conversation (HISTORY_FILE)
  .session/<project>/full_conversation.json  ← append-only, survives compression
"""
import json
import os
from typing import List, Dict, Any, Optional


def _full_history_path(cfg) -> str:
    """Derive full_conversation.json path from HISTORY_FILE location."""
    return os.path.join(os.path.dirname(cfg.HISTORY_FILE), 'full_conversation.json')


def _append_to_full_history(messages: List[Dict[str, Any]], cfg) -> None:
    """Append new messages to the append-only full history file.

    Reads existing full history to find how many messages were already saved,
    then appends only the new ones. Never overwrites — survives compression.
    """
    full_path = _full_history_path(cfg)
    try:
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        else:
            existing = []

        # Only append messages beyond what's already stored
        new_count = len(messages) - len(existing)
        if new_count <= 0:
            return

        new_messages = messages[len(existing):]
        existing.extend(new_messages)

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # Never let full-history errors break the main save


def save_conversation_history(
    messages: List[Dict[str, Any]],
    cfg=None,
    silent: bool = True,
) -> None:
    """Save conversation history to a JSON file if enabled in config.

    Args:
        messages: List of message dicts to persist.
        cfg:      Config namespace. Defaults to importing the config module.
        silent:   If True, suppress the "History saved" print message.
                  Pass silent=False only for the final save on exit.
    """
    if cfg is None:
        import config as cfg  # type: ignore

    if not cfg.SAVE_HISTORY:
        return

    try:
        with open(cfg.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        # Also append new messages to the append-only full history
        _append_to_full_history(messages, cfg)
        if not silent:
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


def load_conversation_history(cfg=None, silent=False) -> Optional[List[Dict[str, Any]]]:
    """Load conversation history from JSON file if it exists.

    Args:
        cfg:    Config namespace. Defaults to importing the config module.
        silent: If True, suppress the "[System] Loaded" print message.

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
            if not silent:
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
