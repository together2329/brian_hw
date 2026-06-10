#!/usr/bin/env python3
"""platform_ontology.py — common_ai_agent 개발 단위 온톨로지의 스캐너/DB/리포터.

선언부:  ontology/platform_ontology.yaml  (source of truth, git 추적)
측정부:  ontology/platform.db             (derived SQLite, git-ignore)

성숙도 사다리 (기계 판정, 누적):
  L0 존재       owns 파일이 실재 (owns가 비면 선언 증거 실재로 대체)
  L1 단위테스트  tests/ 에서 owned 모듈을 import/참조하는 테스트 발견
  L2 내용검증    content_tests 선언 + 전부 실재
  L3 E2E증명    e2e_evidence 선언 + 전부 실재
  L4 래칫       ratchet_tests 선언 + 전부 실재

silent-PASS 금지 원칙: 선언된 경로가 디스크에 없으면 그 선언은 무효이며
check 모드는 비0으로 종료한다. 자기신고만으로 레벨이 오르는 일은 없다.

Usage:
  python3 scripts/platform_ontology.py scan      # 측정 + DB 스냅샷 적재
  python3 scripts/platform_ontology.py report    # 최신 스냅샷 표/히스토그램
  python3 scripts/platform_ontology.py check     # 무결성 게이트 (rc 0/1)
"""

from __future__ import annotations

import fnmatch
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
ONTOLOGY_YAML = REPO / "ontology" / "platform_ontology.yaml"
ONTOLOGY_DB = REPO / "ontology" / "platform.db"

LEVEL_NAMES = {0: "L0 존재", 1: "L1 단위테스트", 2: "L2 내용검증", 3: "L3 E2E", 4: "L4 래칫"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  n_scope_files INTEGER, n_owned_files INTEGER, n_orphans INTEGER
);
CREATE TABLE IF NOT EXISTS unit_state (
  snapshot_id INTEGER, unit_id TEXT, kind TEXT, summary TEXT,
  level INTEGER, n_files INTEGER, n_lines INTEGER, n_tests INTEGER,
  known_gaps_json TEXT, evidence_json TEXT,
  PRIMARY KEY (snapshot_id, unit_id)
);
CREATE TABLE IF NOT EXISTS unit_files (
  snapshot_id INTEGER, unit_id TEXT, path TEXT, lines INTEGER
);
CREATE TABLE IF NOT EXISTS unit_tests (
  snapshot_id INTEGER, unit_id TEXT, path TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS orphans (
  snapshot_id INTEGER, path TEXT, lines INTEGER
);
"""


def load_ontology(path: Path = ONTOLOGY_YAML) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _count_lines(p: Path) -> int:
    try:
        return sum(1 for _ in p.open("rb"))
    except OSError:
        return 0


def expand_scope(doc: dict, repo: Path = REPO) -> list:
    files = []
    for pattern in doc.get("scope", []):
        files.extend(sorted(repo.glob(pattern)))
    return [f for f in files if f.is_file()]


def map_ownership(doc: dict, scope_files: list, repo: Path = REPO):
    """returns (owned: {unit_id: [relpath]}, orphans: [relpath], overlaps: [(path, [unit,...])])"""
    rels = [f.relative_to(repo).as_posix() for f in scope_files]
    owned = {}
    claims = {}
    for unit in doc.get("units", []):
        uid = unit["id"]
        owned[uid] = []
        for rel in rels:
            for pat in unit.get("owns") or []:
                if rel == pat or fnmatch.fnmatch(rel, pat):
                    owned[uid].append(rel)
                    claims.setdefault(rel, []).append(uid)
                    break
        # scope 밖이라도 글롭 아닌 literal 경로가 실재하면 명시 소유로 인정
        for pat in unit.get("owns") or []:
            if "*" not in pat and pat not in rels and (repo / pat).is_file():
                owned[uid].append(pat)
                claims.setdefault(pat, []).append(uid)
    orphans = [r for r in rels if r not in claims]
    overlaps = [(p, us) for p, us in claims.items() if len(us) > 1]
    return owned, orphans, overlaps


def _module_patterns(rel: str):
    """core/react_loop.py → import 매칭용 regex들."""
    if not rel.endswith(".py"):
        return []
    dotted = rel[:-3].replace("/", ".")
    pats = [
        re.compile(r"(?m)^\s*(?:from|import)\s+" + re.escape(dotted) + r"\b"),
        re.compile(r"(?m)^\s*from\s+" + re.escape(dotted.rsplit(".", 1)[0])
                   + r"\s+import\s+[\w, (]*\b" + re.escape(dotted.rsplit(".", 1)[1]) + r"\b")
        if "." in dotted else None,
        re.compile(re.escape(rel)),  # 경로 문자열 직접 참조 (subprocess 등)
    ]
    return [p for p in pats if p is not None]


def discover_tests(owned: dict, repo: Path = REPO) -> dict:
    """tests/test_*.py 본문에서 owned 모듈 import/참조 → {unit_id: [test relpath]}"""
    unit_pats = {uid: [(rel, _module_patterns(rel)) for rel in rels]
                 for uid, rels in owned.items()}
    found = {uid: set() for uid in owned}
    for tf in sorted((repo / "tests").glob("test_*.py")):
        try:
            text = tf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        trel = tf.relative_to(repo).as_posix()
        for uid, entries in unit_pats.items():
            for _rel, pats in entries:
                if any(p.search(text) for p in pats):
                    found[uid].add(trel)
                    break
    return {uid: sorted(v) for uid, v in found.items()}


def check_declared(doc: dict, repo: Path = REPO) -> list:
    """선언 경로 실재 검증. 누락 목록 반환 (비면 OK)."""
    missing = []
    for unit in doc.get("units", []):
        for field in ("content_tests", "e2e_evidence", "ratchet_tests"):
            for rel in unit.get(field) or []:
                if not (repo / rel).is_file():
                    missing.append((unit["id"], field, rel))
    return missing


def compute_levels(doc: dict, owned: dict, tests: dict, repo: Path = REPO) -> dict:
    levels = {}
    for unit in doc.get("units", []):
        uid = unit["id"]
        has_owned = bool(owned.get(uid))
        declared_ok = lambda field: bool(unit.get(field)) and all(
            (repo / rel).is_file() for rel in unit[field])
        any_declared = any(declared_ok(f) for f in ("content_tests", "e2e_evidence", "ratchet_tests"))
        l0 = has_owned or (not (unit.get("owns") or []) and any_declared)
        l1 = l0 and (bool(tests.get(uid)) or declared_ok("content_tests"))
        l2 = l1 and declared_ok("content_tests")
        l3 = l2 and declared_ok("e2e_evidence")
        l4 = l3 and declared_ok("ratchet_tests")
        levels[uid] = 4 if l4 else 3 if l3 else 2 if l2 else 1 if l1 else 0
    return levels


def scan(write_db: bool = True):
    doc = load_ontology()
    scope_files = expand_scope(doc)
    owned, orphans, overlaps = map_ownership(doc, scope_files)
    tests = discover_tests(owned)
    missing = check_declared(doc)
    levels = compute_levels(doc, owned, tests)

    result = {
        "doc": doc, "owned": owned, "orphans": orphans, "overlaps": overlaps,
        "tests": tests, "missing": missing, "levels": levels,
        "n_scope": len(scope_files),
    }
    if not write_db:
        return result

    ONTOLOGY_DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(ONTOLOGY_DB)
    con.executescript(SCHEMA)
    ts = datetime.now(timezone.utc).isoformat()
    n_owned = sum(len(v) for v in owned.values())
    cur = con.execute(
        "INSERT INTO snapshots (ts, n_scope_files, n_owned_files, n_orphans) VALUES (?,?,?,?)",
        (ts, len(scope_files), n_owned, len(orphans)))
    sid = cur.lastrowid
    for unit in doc.get("units", []):
        uid = unit["id"]
        files = owned.get(uid, [])
        lines = sum(_count_lines(REPO / f) for f in files)
        evidence = {f: unit.get(f) or [] for f in ("content_tests", "e2e_evidence", "ratchet_tests")}
        con.execute(
            "INSERT INTO unit_state VALUES (?,?,?,?,?,?,?,?,?,?)",
            (sid, uid, unit.get("kind", ""), unit.get("summary", ""), levels[uid],
             len(files), lines, len(tests.get(uid, [])),
             json.dumps(unit.get("known_gaps") or [], ensure_ascii=False),
             json.dumps(evidence, ensure_ascii=False)))
        con.executemany("INSERT INTO unit_files VALUES (?,?,?,?)",
                        [(sid, uid, f, _count_lines(REPO / f)) for f in files])
        con.executemany("INSERT INTO unit_tests VALUES (?,?,?,?)",
                        [(sid, uid, t, "discovered") for t in tests.get(uid, [])])
    con.executemany("INSERT INTO orphans VALUES (?,?,?)",
                    [(sid, o, _count_lines(REPO / o)) for o in orphans])
    con.commit()
    con.close()
    result["snapshot_id"] = sid
    return result


def report():
    r = scan(write_db=False)
    doc, levels, tests, owned = r["doc"], r["levels"], r["tests"], r["owned"]
    print(f"=== platform ontology — scope {r['n_scope']} files, "
          f"orphans {len(r['orphans'])}, overlaps {len(r['overlaps'])} ===")
    rows = []
    for unit in doc["units"]:
        uid = unit["id"]
        lines = sum(_count_lines(REPO / f) for f in owned.get(uid, []))
        rows.append((levels[uid], uid, unit.get("kind", ""), len(owned.get(uid, [])),
                     lines, len(tests.get(uid, [])), len(unit.get("known_gaps") or [])))
    rows.sort(key=lambda x: (-x[0], x[1]))
    print(f"{'level':<14}{'unit':<26}{'kind':<10}{'files':>5}{'lines':>8}{'tests':>6}{'gaps':>5}")
    for lv, uid, kind, nf, nl, nt, ng in rows:
        print(f"{LEVEL_NAMES[lv]:<14}{uid:<26}{kind:<10}{nf:>5}{nl:>8}{nt:>6}{ng:>5}")
    hist = {}
    for lv in levels.values():
        hist[lv] = hist.get(lv, 0) + 1
    print("--- histogram ---")
    for lv in range(5):
        print(f"{LEVEL_NAMES[lv]:<14}{'#' * hist.get(lv, 0)} {hist.get(lv, 0)}")
    if r["missing"]:
        print("--- MISSING declared paths ---")
        for uid, field, rel in r["missing"]:
            print(f"  {uid}.{field}: {rel}")
    print(f"--- orphans (top 15 by size) ---")
    top = sorted(r["orphans"], key=lambda o: -_count_lines(REPO / o))[:15]
    for o in top:
        print(f"  {o} ({_count_lines(REPO / o)}L)")
    return r


def check() -> int:
    r = scan(write_db=False)
    rc = 0
    if r["missing"]:
        rc = 1
        for uid, field, rel in r["missing"]:
            print(f"[ontology] FAIL: {uid}.{field} declares missing path {rel}")
    if r["overlaps"]:
        rc = 1
        for path, units in r["overlaps"]:
            print(f"[ontology] FAIL: {path} owned by multiple units: {units}")
    baseline = r["doc"].get("orphan_baseline")
    if baseline is not None and len(r["orphans"]) > baseline:
        rc = 1
        print(f"[ontology] FAIL: orphans {len(r['orphans'])} > baseline {baseline} "
              f"(새 파일은 단위에 등록하세요)")
    if rc == 0:
        print(f"[ontology] PASS: declared paths OK, no overlap, "
              f"orphans {len(r['orphans'])} ≤ baseline {baseline}")
    return rc


def main(argv: list) -> int:
    cmd = argv[0] if argv else "report"
    if cmd == "scan":
        r = scan()
        print(f"[ontology] snapshot #{r['snapshot_id']} written to {ONTOLOGY_DB} "
              f"(scope={r['n_scope']}, orphans={len(r['orphans'])})")
        return 0
    if cmd == "report":
        report()
        return 0
    if cmd == "check":
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
