#!/usr/bin/env python3
"""sync_cursor_pack.py — .cursor 를 단독 전달 가능한 자가포함 팩으로 vendoring.

정본(workflow/, src 엔진 2종, scripts 헬퍼)을 .cursor 안으로 복사하고
해시 manifest 를 남긴다. 정본이 바뀌면 `check` 가 drift 를 잡는다 (ratchet).

  python3 scripts/sync_cursor_pack.py sync    # 정본 → .cursor 복사 + manifest
  python3 scripts/sync_cursor_pack.py check   # drift 검사 (rc 0/1)

vendor 대상:
  workflow/**        → .cursor/workflow/   (py/json/md/yaml; __pycache__·mas-gen 제외)
  src/workflow_stage_engine.py, src/workflow_stage_surface.py → .cursor/src/
  scripts/ip_wiki.py, scripts/atlas_mcp_server.py             → .cursor/scripts/
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACK = REPO / ".cursor"
MANIFEST = PACK / "VENDOR_MANIFEST.json"

VENDOR_EXTS = {".py", ".json", ".md", ".yaml", ".yml", ".txt", ".j2", ".sv", ".v"}
EXCLUDE_DIRS = {"__pycache__", "mas-gen"}
# README.md는 사람용 문서일 뿐 엔진/게이트가 소비하지 않는다. vendoring에서 제외해
# 세션 간 README 추가/삭제가 드리프트 래칫을 흔드는 noise를 차단한다.
EXCLUDE_NAMES = {"README.md"}

SINGLE_FILES = [
    ("src/workflow_stage_engine.py", "src/workflow_stage_engine.py"),
    ("src/workflow_stage_surface.py", "src/workflow_stage_surface.py"),
    ("src/workflow_lint_kpi.py", "src/workflow_lint_kpi.py"),
    ("scripts/ip_wiki.py", "scripts/ip_wiki.py"),
    ("scripts/atlas_mcp_server.py", "scripts/atlas_mcp_server.py"),
]


def _iter_workflow():
    for p in sorted((REPO / "workflow").rglob("*")):
        if not p.is_file() or p.suffix not in VENDOR_EXTS:
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.name in EXCLUDE_NAMES:
            continue
        yield p


def _pairs():
    """(정본 절대경로, 팩 내 상대경로) 목록."""
    out = [(p, Path("workflow") / p.relative_to(REPO / "workflow")) for p in _iter_workflow()]
    out += [(REPO / src, Path(dst)) for src, dst in SINGLE_FILES if (REPO / src).is_file()]
    return out


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sync() -> int:
    manifest = {}
    n = 0
    for src, rel in _pairs():
        dst = PACK / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.is_file() or dst.read_bytes() != src.read_bytes():
            shutil.copy2(src, dst)
            n += 1
        manifest[rel.as_posix()] = _sha(src)
    # 패키지 임포트용 (from src.workflow_stage_engine import ...)
    init = PACK / "src" / "__init__.py"
    if not init.is_file():
        init.write_text("", encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(f"[sync_cursor_pack] synced {n} changed / {len(manifest)} vendored files")
    return 0


def check() -> int:
    if not MANIFEST.is_file():
        print("[sync_cursor_pack] FAIL: VENDOR_MANIFEST.json missing — run sync")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    issues = []
    current = {rel.as_posix(): src for src, rel in _pairs()}
    for rel, sha in manifest.items():
        vend = PACK / rel
        if not vend.is_file():
            issues.append(f"vendored file missing: {rel}")
            continue
        if _sha(vend) != sha:
            issues.append(f"vendored copy diverged from manifest: {rel}")
        src = current.get(rel)
        if src is None:
            issues.append(f"canonical source gone (stale vendor): {rel}")
        elif _sha(src) != sha:
            issues.append(f"canonical changed since sync (drift): {rel}")
    for rel in current:
        if rel not in manifest:
            issues.append(f"new canonical file not vendored: {rel}")
    if issues:
        for i in issues[:20]:
            print(f"[sync_cursor_pack] FAIL: {i}")
        if len(issues) > 20:
            print(f"[sync_cursor_pack] ... and {len(issues) - 20} more")
        print("[sync_cursor_pack] fix: python3 scripts/sync_cursor_pack.py sync")
        return 1
    print(f"[sync_cursor_pack] PASS: {len(manifest)} vendored files in sync")
    return 0


def main(argv) -> int:
    cmd = argv[0] if argv else "check"
    if cmd == "sync":
        return sync()
    if cmd == "check":
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
