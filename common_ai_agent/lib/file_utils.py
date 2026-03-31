"""
Shared file I/O utilities.

Consolidates duplicated implementations from:
  - lib/memory.py  (_read_json_file, _atomic_write_json)
  - lib/procedural_memory.py  (identical implementations)
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


def read_json_file(path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Read a JSON dict from disk, returning `default` on any error.

    Args:
        path: File path (str or Path).
        default: Value to return on missing file or parse error. Defaults to {}.

    Returns:
        Parsed dict, or `default` if the file is missing, unreadable,
        not valid JSON, or the root value is not a dict.
    """
    if default is None:
        default = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else default
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def atomic_write_json(path, data: Dict[str, Any]) -> None:
    """Atomically write a JSON dict to disk.

    Writes to a temp file in the same directory, then os.replace() for
    an atomic swap. Creates parent directories if they do not exist.

    Args:
        path: Destination file path (str or Path).
        data: Dict to serialize as JSON.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=str(path.parent),
            delete=False,
            encoding='utf-8',
        ) as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(str(tmp_path), str(path))
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
