"""Session Snapshot System for Brian Coder"""
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

SNAPSHOT_DIR = Path.home() / ".brian_coder" / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def save_snapshot(messages: List[Dict], name: Optional[str] = None) -> str:
    """
    Save current conversation as snapshot

    Args:
        messages: Message history
        name: Optional snapshot name (default: timestamp)

    Returns:
        Snapshot filename
    """
    if name is None:
        name = f"snapshot_{int(time.time())}"

    # Ensure .json extension
    if not name.endswith(".json"):
        name = f"{name}.json"

    path = SNAPSHOT_DIR / name

    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

    return str(path)


def load_snapshot(name: str) -> List[Dict]:
    """
    Load snapshot by name

    Args:
        name: Snapshot name (with or without .json extension)

    Returns:
        List of message dicts

    Raises:
        FileNotFoundError: If snapshot doesn't exist
    """
    if not name.endswith(".json"):
        name = f"{name}.json"

    path = SNAPSHOT_DIR / name

    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {name}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_snapshots() -> List[str]:
    """
    List all available snapshots

    Returns:
        List of snapshot names (without .json extension)
    """
    return sorted([f.stem for f in SNAPSHOT_DIR.glob("*.json")], reverse=True)


def delete_snapshot(name: str) -> bool:
    """
    Delete a snapshot

    Args:
        name: Snapshot name

    Returns:
        True if deleted, False if not found
    """
    if not name.endswith(".json"):
        name = f"{name}.json"

    path = SNAPSHOT_DIR / name

    if path.exists():
        path.unlink()
        return True
    return False
