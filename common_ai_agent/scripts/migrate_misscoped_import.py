#!/usr/bin/env python3
"""Relocate import evidence written to the wrong (non-session) IP root.

Background
----------
Before the session-aware import fix, ``POST /api/ssot/import/upload`` and the
``/import`` command resolved the IP directory via the non-session
``_ip_root(ip)`` (== ``PROJECT_ROOT/<ip>``). In a multi-user deployment the file
tree, chat worker, and ``/to-ssot`` all read the *per-session* workspace
(``<root>/<owner>/<workspace_session>/<ip>``), so imported docs landed in a
directory the UI never displays — "import이 안 되는 느낌".

This tool moves the import artifacts (``req/imports``, ``req/*.json``,
``wiki/import-evidence.md``, and the import-enriched ``yaml/<ip>.ssot.yaml``)
from the stray non-session root into the per-session root, WITHOUT clobbering
the session's own richer wiki, and rewrites the PROJECT_ROOT-relative path
prefix embedded in the manifests/evidence so downstream resolution still finds
the files. The drained non-session directory is moved to ``<root>/.trash`` so
the operation is reversible.

Everything is backup-first and supports ``--dry-run``. Run --dry-run first.

Usage
-----
    python scripts/migrate_misscoped_import.py \
        --src  /abs/NEW_WORKSPACE/mctp_assembler \
        --dst  /abs/NEW_WORKSPACE/brian_user_3/default/mctp_assembler \
        --root /abs/NEW_WORKSPACE \
        [--dry-run]

``--rel-old`` / ``--rel-new`` default to ``<src rel to root>`` and
``<dst rel to root>`` and drive the path-prefix rewrite.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _rewrite_prefixes(text: str, rel_old: str, rel_new: str) -> tuple[str, int]:
    """Rewrite anchored ``<rel_old>/{req,wiki,yaml}/`` occurrences to rel_new.

    Anchored to the artifact sub-roots so unrelated tokens (e.g.
    ``rtl/<ip>.sv``) are never touched.
    """
    n = 0
    for sub in ("req/", "wiki/", "yaml/"):
        needle = f"{rel_old}/{sub}"
        repl = f"{rel_new}/{sub}"
        if needle in text:
            n += text.count(needle)
            text = text.replace(needle, repl)
    return text, n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, type=Path, help="stray non-session IP dir")
    ap.add_argument("--dst", required=True, type=Path, help="per-session IP dir")
    ap.add_argument("--root", required=True, type=Path, help="ATLAS workspace root (PROJECT_ROOT)")
    ap.add_argument("--rel-old", default="", help="override old PROJECT_ROOT-relative IP prefix")
    ap.add_argument("--rel-new", default="", help="override new PROJECT_ROOT-relative IP prefix")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src: Path = args.src.resolve()
    dst: Path = args.dst.resolve()
    root: Path = args.root.resolve()
    dry = args.dry_run

    if not src.is_dir():
        print(f"ERROR: src not a dir: {src}", file=sys.stderr)
        return 2
    if src == dst:
        print("ERROR: src == dst", file=sys.stderr)
        return 2
    for p, name in ((src, "src"), (dst, "dst")):
        try:
            p.relative_to(root)
        except ValueError:
            print(f"ERROR: {name} {p} is not under root {root}", file=sys.stderr)
            return 2

    rel_old = args.rel_old or _rel(src, root)
    rel_new = args.rel_new or _rel(dst, root)
    stamp = int(time.time())
    tag = "DRY-RUN" if dry else "APPLY"
    print(f"[{tag}] migrate import artifacts")
    print(f"  src     : {src}")
    print(f"  dst     : {dst}")
    print(f"  root    : {root}")
    print(f"  rewrite : {rel_old}/{{req,wiki,yaml}}/  ->  {rel_new}/{{req,wiki,yaml}}/")
    print()

    dst.mkdir(parents=True, exist_ok=True)
    actions: list[str] = []

    def do_move(s: Path, d: Path) -> None:
        actions.append(f"MOVE  {s}  ->  {d}")
        if not dry:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(s), str(d))

    def do_copy(s: Path, d: Path) -> None:
        actions.append(f"COPY  {s}  ->  {d}")
        if not dry:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(s), str(d))

    def do_backup(p: Path) -> None:
        bak = p.with_suffix(p.suffix + f".pre_migrate_{stamp}.bak")
        actions.append(f"BACKUP {p}  ->  {bak}")
        if not dry:
            shutil.copy2(str(p), str(bak))

    # 1) req/imports + req/*.json  (session req/ is expected empty)
    src_req = src / "req"
    dst_req = dst / "req"
    if src_req.is_dir():
        dst_req.mkdir(parents=True, exist_ok=True)
        for child in sorted(src_req.iterdir()):
            target = dst_req / child.name
            if target.exists():
                if target.is_dir() and not any(target.iterdir()):
                    if not dry:
                        target.rmdir()
                else:
                    do_backup(target) if target.is_file() else actions.append(f"SKIP (exists dir) {target}")
                    if target.is_file() and not dry:
                        target.unlink()
                    elif target.is_dir():
                        continue
            do_move(child, target)

    # 2) wiki/import-evidence.md only (preserve session's live wiki)
    src_ev = src / "wiki" / "import-evidence.md"
    if src_ev.is_file():
        do_copy(src_ev, dst / "wiki" / "import-evidence.md")

    # 3) yaml: bring the import-enriched draft over, backing up the session stub
    src_yaml_dir = src / "yaml"
    dst_yaml_dir = dst / "yaml"
    if src_yaml_dir.is_dir():
        for sy in sorted(src_yaml_dir.glob("*.ssot.y*ml")):
            dy = dst_yaml_dir / sy.name
            if dy.is_file():
                do_backup(dy)
                if not dry:
                    dy.unlink()
            do_copy(sy, dy)

    # 4) rewrite embedded PROJECT_ROOT-relative path prefixes in moved/copied files
    rewrite_targets = [
        dst / "req" / "import_manifest.json",
        dst / "req" / "extracted_decisions.json",
        dst / "wiki" / "import-evidence.md",
    ]
    rewrite_targets += sorted((dst / "yaml").glob("*.ssot.y*ml")) if (dst / "yaml").is_dir() else []
    for tgt in rewrite_targets:
        if not tgt.is_file():
            continue
        text = tgt.read_text(encoding="utf-8", errors="replace")
        new_text, n = _rewrite_prefixes(text, rel_old, rel_new)
        if n:
            actions.append(f"REWRITE {tgt}  ({n} path prefixes)")
            if not dry:
                tgt.write_text(new_text, encoding="utf-8")

    # 5) quarantine the drained non-session dir (reversible)
    trash = root / ".trash" / f"{src.name}_nonsession_{stamp}"
    actions.append(f"TRASH {src}  ->  {trash}")
    if not dry:
        trash.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(trash))

    print("\n".join(actions) if actions else "(nothing to do)")
    print()
    print(f"[{tag}] done — {len(actions)} actions"
          + ("  (no changes written; re-run without --dry-run to apply)" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
