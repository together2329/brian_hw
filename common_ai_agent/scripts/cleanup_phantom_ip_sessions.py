#!/usr/bin/env python3
"""Find & clean up *phantom* IP sessions created by stale cross-owner namespaces.

Background
----------
In multi-user ATLAS, a stale ``ip=<other_user_ip>`` carried from a previous login
(URL / localStorage / window globals) could be POSTed to ``/api/session/activate``
under a *different* user. Before the fail-closed guard, the backend trusted that
triple and minted ``<new_user>/<ws>/<other_ip>/<wf>`` — leaving a *ghost* session
row plus a doc-only skeleton directory on disk. That ghost then surfaced the IP in
the new user's dropdown ("why does dma_v1_good show for multiple users?").

The activate / ip-list guards stop NEW ghosts; this script removes the ones that
already exist.

A row is treated as a phantom ONLY when ALL hold (conservative by design):
  1. namespace is 4-seg ``owner/workspace/ip/workflow`` and ip != "default";
  2. the IP is NOT in the owner's ip_blocks catalog at that workspace path;
  3. the on-disk ip_root is a *skeleton* — no ``yaml/*.ssot.yaml``, no ``rtl/``
     content, no ``tb/`` content (a real authored IP always has an SSOT) — OR
     the directory is already gone.

Default is DRY-RUN. ``--apply`` archives the session rows (status='archived',
reversible — list_sessions only returns 'active') and moves any skeleton dir into
a timestamped ``.trash`` folder (reversible). Nothing is hard-deleted.

Usage
-----
  python scripts/cleanup_phantom_ip_sessions.py                 # dry-run, all owners
  python scripts/cleanup_phantom_ip_sessions.py --owner brian_user_3 --ip dma_v1_good
  python scripts/cleanup_phantom_ip_sessions.py --apply         # act (after reviewing dry-run)
"""
from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
import time
from collections import Counter
from contextlib import closing
from pathlib import Path


def _default_db() -> str:
    return os.environ.get("ATLAS_DB_PATH") or str(
        Path.home() / ".common_ai_agent" / "atlas.db"
    )


def _owner_roots(conn: sqlite3.Connection) -> dict[str, Path]:
    """Map owner_user_id -> workspace root, inferred PER OWNER.

    This DB can hold workspaces from many different --root launches, so a single
    global root is unsafe (a wrong root makes every dir look "missing" and would
    mass-flag real sessions as phantoms). Instead derive each owner's root from
    THAT owner's own workspace rows: local_path is ``<ROOT>/<owner>/<ws>``, so
    stripping the two trailing segments yields the root. Pick the most common.
    """
    rows = conn.execute(
        "SELECT owner_user_id, local_path FROM workspaces "
        "WHERE local_path IS NOT NULL AND local_path != '' "
        "AND owner_user_id IS NOT NULL AND owner_user_id != ''"
    ).fetchall()
    per_owner: dict[str, Counter[str]] = {}
    for owner_id, lp in rows:
        p = Path(lp)
        if len(p.parts) >= 3:  # <root>/<owner>/<ws>
            per_owner.setdefault(owner_id, Counter())[str(p.parent.parent)] += 1
    return {oid: Path(c.most_common(1)[0][0]) for oid, c in per_owner.items() if c}


def _is_skeleton(ip_dir: Path) -> tuple[bool, str]:
    """Return (is_skeleton, reason). A real IP always carries an SSOT yaml."""
    if not ip_dir.exists():
        # Caller decides what an absent dir means; never call it a skeleton here
        # (an absent dir under a WRONG root must not look like a phantom).
        return False, "dir-missing"
    try:
        if any(ip_dir.glob("yaml/*.ssot.yaml")):
            return False, "has-ssot"
        for marker in ("rtl", "tb"):
            md = ip_dir / marker
            if md.is_dir() and any(f.is_file() for f in md.rglob("*")):
                return False, f"has-{marker}"
    except OSError as exc:
        return False, f"stat-error:{exc}"  # be safe: do NOT treat as skeleton
    # contents summary (top-level dirs) for the operator to eyeball
    try:
        tops = sorted(c.name for c in ip_dir.iterdir() if c.is_dir())
    except OSError:
        tops = []
    return True, "skeleton(" + ",".join(tops or ["empty"]) + ")"


def _catalog_for_owner(conn: sqlite3.Connection, owner_user_id: str, ws_dir: Path) -> set[str]:
    """IP names registered to this owner whose workspace resolves to ws_dir.

    Match on realpath rather than a raw string equality so a trailing slash,
    symlink, or case difference between the stored ``local_path`` and the
    script's ``ws_dir`` can't yield an empty catalog (which would wrongly mark a
    REAL registered IP as a phantom candidate).
    """
    try:
        target = os.path.realpath(str(ws_dir))
    except OSError:
        target = str(ws_dir)
    rows = conn.execute(
        """
        SELECT i.ip_name, w.local_path FROM workspaces w
          JOIN ip_blocks i ON i.workspace_id = w.id
         WHERE w.owner_user_id = ?
           AND lower(COALESCE(i.status,'active')) = 'active'
        """,
        (owner_user_id,),
    ).fetchall()
    names: set[str] = set()
    for name, local_path in rows:
        nm = str(name or "").strip()
        if not nm:
            continue
        try:
            same = os.path.realpath(str(local_path)) == target
        except OSError:
            same = str(local_path) == str(ws_dir)
        if same:
            names.add(nm)
    return names


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=_default_db(), help="control DB path")
    ap.add_argument("--root", default=os.environ.get("ATLAS_ROOT", ""), help="workspace root (auto-inferred if omitted)")
    ap.add_argument("--owner", default="", help="restrict to this owner segment")
    ap.add_argument("--ip", default="", help="restrict to this IP name")
    ap.add_argument("--apply", action="store_true", help="actually archive rows + move skeleton dirs (default: dry-run)")
    ap.add_argument("--trash", default="", help="trash dir for moved skeletons (default: <root>/.trash/phantom-<ts>)")
    args = ap.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.is_file():
        print(f"ERROR: control DB not found: {db_path}", file=sys.stderr)
        return 2
    with closing(sqlite3.connect(str(db_path))) as conn:
        conn.row_factory = sqlite3.Row
        return _run(conn, args)


def _run(conn: sqlite3.Connection, args) -> int:
    override_root = Path(args.root).expanduser() if args.root else None
    owner_roots = _owner_roots(conn)
    print(f"DB:   {Path(args.db)}")
    print(f"root: {override_root if override_root else 'per-owner (auto)'}")
    print(f"mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print("-" * 78)

    # uid -> username (for readable output)
    users = {r["id"]: r["username"] for r in conn.execute("SELECT id, username FROM users")}

    rows = conn.execute(
        "SELECT id, user_id, namespace, status FROM sessions "
        "WHERE status = 'active' AND namespace LIKE '%/%/%/%'"
    ).fetchall()

    # cache catalogs by (owner_user_id, resolved workspace path)
    catalog_cache: dict[tuple[str, str], set[str]] = {}
    candidates: list[dict] = []
    unverifiable: list[tuple[str, str]] = []
    multi_root_owners: set[str] = set()
    for r in rows:
        ns = str(r["namespace"] or "")
        parts = [p for p in ns.split("/") if p]
        if len(parts) != 4:
            continue
        owner, ws, ip, wf = parts
        if ip == "default":
            continue
        if args.owner and owner != args.owner:
            continue
        if args.ip and ip != args.ip:
            continue
        root = override_root or owner_roots.get(r["user_id"])
        if root is None:
            unverifiable.append((ns, "no workspace row to locate this owner on disk"))
            continue
        ws_dir = root / owner / ws
        if not ws_dir.exists():
            # Can't see the workspace on disk → don't trust this root. A wrong
            # root would make every dir look missing and mass-flag real
            # sessions, so report for manual review instead of auto-acting. This
            # also covers an owner whose REAL workspace lives under a second
            # root that _owner_roots did not pick (signalled below).
            multi_root_owners.add(owner)
            unverifiable.append((ns, f"workspace dir absent under inferred root: {ws_dir}"))
            continue
        key = (r["user_id"], str(ws_dir.resolve()))
        if key not in catalog_cache:
            catalog_cache[key] = _catalog_for_owner(conn, r["user_id"], ws_dir)
        if ip in catalog_cache[key]:
            continue  # legitimately registered → never touch
        ip_dir = ws_dir / ip
        if ip_dir.exists():
            skeleton, reason = _is_skeleton(ip_dir)
            if not skeleton:
                continue  # real artifacts on disk → never touch
        else:
            reason = "ghost-row (session row, no ip dir)"  # archive row only
        candidates.append({
            "id": r["id"],
            "user": users.get(r["user_id"], r["user_id"]),
            "namespace": ns,
            "ip_dir": ip_dir,
            "root": root,
            "reason": reason,
        })

    if unverifiable:
        print(f"NOTE: {len(unverifiable)} session(s) could not be verified on disk "
              f"(left untouched — pass --root to check explicitly):")
        for ns, why in unverifiable[:20]:
            print(f"    ? {ns}  —  {why}")
        if len(unverifiable) > 20:
            print(f"    … and {len(unverifiable) - 20} more")
        if multi_root_owners and not override_root:
            print(f"    (owners possibly spanning multiple roots: "
                  f"{', '.join(sorted(multi_root_owners)[:8])} — verify with explicit --root)")
        print("-" * 78)

    if not candidates:
        print("No phantom IP sessions found. Nothing to do.")
        return 0

    print(f"Found {len(candidates)} phantom session row(s):\n")
    for c in candidates:
        print(f"  • {c['namespace']}")
        print(f"      user={c['user']}  reason={c['reason']}")
        print(f"      session_id={c['id']}")
        print(f"      ip_dir={c['ip_dir']}")

    if not args.apply:
        print("\nDRY-RUN: re-run with --apply to archive these rows and move skeleton dirs.")
        return 0

    # APPLY -------------------------------------------------------------------
    # Per-candidate so each uses ITS OWN root (owners can live under different
    # deployment roots — a single shared `root` here would move one owner's dir
    # into another owner's .trash) and so a row is archived only alongside its
    # own (successful or cleanly-skipped) move.
    ts = time.strftime("%Y%m%d-%H%M%S")
    now = time.time()
    archived = 0
    moved = 0
    moved_dirs: set[str] = set()
    trash_bases: set[str] = set()
    for c in candidates:
        d: Path = c["ip_dir"]
        droot: Path = c["root"]
        # If a real SSOT landed since detection, leave BOTH the row and the dir
        # untouched (don't archive a now-legit IP).
        if d.exists():
            skeleton, _ = _is_skeleton(d)
            if not skeleton:
                print(f"  ! SKIP (no longer skeleton): {c['namespace']} — {d}")
                continue
        conn.execute(
            "UPDATE sessions SET status='archived', archived_at=?, updated_at=? WHERE id=?",
            (now, now, c["id"]),
        )
        conn.commit()
        archived += 1
        if d.exists() and str(d) not in moved_dirs:
            trash_base = Path(args.trash) if args.trash else (droot / ".trash" / f"phantom-{ts}")
            rel = d.relative_to(droot) if str(d).startswith(str(droot)) else Path(d.name)
            dest = trash_base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(d), str(dest))
            moved += 1
            moved_dirs.add(str(d))
            trash_bases.add(str(trash_base))
            print(f"  moved skeleton → {dest}")
    print(f"\nArchived {archived} session row(s) (status='archived', reversible); "
          f"moved {moved} skeleton dir(s).")
    for tb in sorted(trash_bases):
        print(f"  trash: {tb}")
    print("Undo: restore dirs from .trash and set the rows' status back to 'active'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
