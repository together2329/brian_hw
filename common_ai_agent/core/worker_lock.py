"""Worker-grade IP-directory lock.

When multiple HTTP workers run in parallel (`background_task(delegate=
"http-worker")`), two of them can be told to operate on the same IP
directory at the same time — racing on `<ip>/yaml/<ip>.ssot.yaml`,
`<ip>/rtl/*.sv`, etc. This module gives every write-side tool a
cross-process advisory lock at the IP-directory granularity so the
second writer blocks until the first releases.

Design choices:
  • Sentinel file at `<ip>/.ip.lock` — same pattern lib/memory.py uses,
    no new deps (Unix/Windows portable).
  • Lock file content = `{pid, host, started_at, holder_label}` so we
    can detect AND **break stale locks** (worker crashed mid-write).
  • Stale lock TTL defaults to 600 s; configurable via env
    `IP_LOCK_STALE_TTL`.
  • Acquisition timeout defaults to 30 s; configurable via env
    `IP_LOCK_TIMEOUT`.
  • Lock is keyed by absolute IP directory. Files outside any IP
    directory (e.g. project root soc.ssot.yaml) get a global lock
    keyed by the project root.
  • Re-entrant in the same process+thread: if the same thread holds
    the lock for a path and asks again, we just yield without
    re-acquiring. This avoids self-deadlock when a tool calls another
    tool (e.g. write_file → _git_auto_commit → another write).

Usage:
    from core.worker_lock import with_ip_lock
    with with_ip_lock(path):
        # safe to write `path`

Re-entrancy is bounded to the same thread; threads in the same process
serialise like cross-process callers do.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


# ── tunables (env-overridable) ──────────────────────────────────────
def _env_int(name: str, default: int) -> int:
    try: return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError): return default

LOCK_TIMEOUT = _env_int("IP_LOCK_TIMEOUT", 30)        # seconds to wait for lock
STALE_TTL    = _env_int("IP_LOCK_STALE_TTL", 600)     # seconds before lock is considered stale
POLL_INTERVAL = 0.1                                    # seconds between retries

# Re-entrancy guard: thread-local count of locks each thread is holding.
_held_local = threading.local()


def _get_held() -> dict:
    if not hasattr(_held_local, "by_path"):
        _held_local.by_path = {}
    return _held_local.by_path


def _project_root() -> Path:
    """Best-effort project root resolution. Falls back to cwd."""
    # Walk up looking for a marker file (.config, .git, workflow/).
    p = Path(os.getcwd()).resolve()
    for cur in (p, *p.parents):
        if (cur / ".config").exists() or (cur / ".git").exists() or (cur / "workflow").is_dir():
            return cur
    return p


def _is_ip_directory(d: Path) -> bool:
    """An IP dir has a `yaml/<name>.ssot.yaml` leaf inside (project's
    canonical IP layout — set by `scaffold_ip()`)."""
    yaml_dir = d / "yaml"
    if not yaml_dir.is_dir(): return False
    for f in yaml_dir.iterdir():
        if f.is_file() and f.name.endswith(".ssot.yaml"):
            return True
    return False


def _resolve_lock_dir(target: Path) -> Path:
    """Map a target path → directory whose lock should be held.

    Walk upward from `target`; the first ancestor that looks like an IP
    directory wins. If no ancestor is an IP dir, lock at the project
    root (covers things like `<project>/soc.ssot.yaml`).
    """
    p = target.resolve() if target.is_absolute() else (Path(os.getcwd()) / target).resolve()
    if p.is_file() or not p.exists():
        p = p.parent
    proj = _project_root()
    cur = p
    while True:
        if _is_ip_directory(cur):
            return cur
        if cur == proj or cur.parent == cur:
            return proj
        cur = cur.parent


def _lock_file_for(lock_dir: Path) -> Path:
    return lock_dir / ".ip.lock"


def _read_lock_meta(lock_path: Path) -> Optional[dict]:
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            return json.loads(f.read() or "{}")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _is_stale(meta: dict) -> bool:
    if not isinstance(meta, dict): return True
    started = meta.get("started_at")
    if not isinstance(started, (int, float)): return True
    return (time.time() - float(started)) > STALE_TTL


def _try_create_lock(lock_path: Path, label: str) -> bool:
    """Atomic create + write meta. Returns True on success."""
    try:
        # O_EXCL fails if file exists — that's our atomic claim.
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o644)
    except FileExistsError:
        return False
    except OSError:
        return False
    try:
        meta = {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "started_at": time.time(),
            "holder_label": label or "",
        }
        os.write(fd, json.dumps(meta).encode("utf-8"))
    finally:
        try: os.close(fd)
        except OSError: pass
    return True


@contextmanager
def with_ip_lock(target_path, label: str = "", timeout: Optional[float] = None):
    """Hold an advisory lock on the IP directory containing `target_path`.

    `target_path` may be inside or one of: `<ip>/yaml/<ip>.ssot.yaml`,
    `<ip>/rtl/*.sv`, etc. The lock covers ALL writes inside that
    directory until release. Re-entrant in the same thread.

    Args:
        target_path: file or directory path the caller is about to write.
        label:       optional string written into the lock file (used for
                     debug — "write_file:<rel_path>" etc.).
        timeout:     seconds to block (default LOCK_TIMEOUT).
    """
    target = Path(target_path) if not isinstance(target_path, Path) else target_path
    lock_dir = _resolve_lock_dir(target)
    try:
        lock_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Can't create dir — give up on locking, let the caller proceed.
        # (Fallback better than blocking the whole agent.)
        yield None
        return
    lock_path = _lock_file_for(lock_dir)
    held = _get_held()
    key = str(lock_path)
    if held.get(key):
        # Re-entrant in this thread — already own the lock.
        held[key] += 1
        try:
            yield lock_path
        finally:
            held[key] -= 1
            if held[key] <= 0:
                held.pop(key, None)
        return

    deadline = time.time() + (timeout if timeout is not None else LOCK_TIMEOUT)
    while True:
        if _try_create_lock(lock_path, label):
            held[key] = 1
            break
        # Lock exists — check if it's stale (crashed worker).
        meta = _read_lock_meta(lock_path)
        if meta is not None and _is_stale(meta):
            # Best-effort steal: unlink and retry.
            try: lock_path.unlink()
            except FileNotFoundError: pass
            except OSError: pass
            continue
        if time.time() >= deadline:
            holder = ""
            if isinstance(meta, dict):
                holder = (f"pid={meta.get('pid')} host={meta.get('host')} "
                          f"label={meta.get('holder_label','')}")
            raise TimeoutError(
                f"IP lock timeout ({timeout or LOCK_TIMEOUT}s) on {lock_dir} "
                f"— held by {holder or 'unknown'}"
            )
        time.sleep(POLL_INTERVAL)
    try:
        yield lock_path
    finally:
        held[key] = max(0, held.get(key, 1) - 1)
        if held[key] <= 0:
            held.pop(key, None)
            try: lock_path.unlink()
            except FileNotFoundError: pass
            except OSError: pass


def break_lock(target_path) -> bool:
    """Force-release a lock for the IP directory containing target_path.

    For operator use — call when a worker died and left a sentinel.
    Returns True if a lock was actually deleted.
    """
    target = Path(target_path) if not isinstance(target_path, Path) else target_path
    lock_path = _lock_file_for(_resolve_lock_dir(target))
    try:
        lock_path.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False
