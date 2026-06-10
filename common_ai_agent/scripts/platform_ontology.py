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

import ast
import fnmatch
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
ONTOLOGY_YAML = REPO / "ontology" / "platform_ontology.yaml"
REQUIREMENTS_YAML = REPO / "ontology" / "platform_requirements.yaml"
ONTOLOGY_DB = REPO / "ontology" / "platform.db"

GRANULARITIES = {"structural", "behavior", "content", "concurrent"}
STATUSES = {"closed", "open", "refuted"}

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
CREATE TABLE IF NOT EXISTS spine_state (
  snapshot_id INTEGER, requirement_id TEXT, obligation_id TEXT,
  owned_by TEXT, granularity TEXT, status TEXT, effective_status TEXT,
  evidence_json TEXT, refuted_by TEXT,
  PRIMARY KEY (snapshot_id, obligation_id)
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


# ---------- ROCEV 척추 (requirement → obligation → evidence → validation) ----------

def load_spine(path: Path = REQUIREMENTS_YAML) -> dict:
    if not path.is_file():
        return {"requirements": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"requirements": []}


_AST_CACHE: dict = {}


def _test_node_exists(repo: Path, node: str) -> bool:
    """'tests/x.py::test_f' 또는 'tests/x.py::TestC::test_m' 실재 검증 (ast)."""
    parts = node.split("::")
    if len(parts) not in (2, 3):
        return False
    fpath = repo / parts[0]
    if not fpath.is_file():
        return False
    key = fpath.as_posix()
    if key not in _AST_CACHE:
        try:
            _AST_CACHE[key] = ast.parse(fpath.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            return False
    tree = _AST_CACHE[key]
    if len(parts) == 2:
        return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and n.name == parts[1] for n in tree.body)
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == parts[1]:
            return any(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and m.name == parts[2] for m in n.body)
    return False


def _git(repo: Path, *args: str):
    try:
        out = subprocess.run(["git", "-C", str(repo), *args],
                             capture_output=True, text=True, timeout=30)
        return out.returncode, out.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def _commit_exists(repo: Path, sha: str) -> bool:
    rc, _ = _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
    return rc == 0


def _changed_since(repo: Path, sha: str, paths: list):
    """observed_at 이후 해당 파일들 변경 여부. git 불가 시 None (unknown)."""
    if not paths:
        return []
    rc, out = _git(repo, "diff", "--name-only", f"{sha}..HEAD", "--", *paths)
    if rc != 0:
        return None
    return [line for line in out.splitlines() if line.strip()]


def validate_spine(spine: dict, units_doc: dict, repo: Path = REPO):
    """무결성 issue 목록 + obligation별 effective_status 해석을 반환.

    effective_status: closed 인데 observed_at 이후 owner 코드/테스트가 바뀌면 stale.
    """
    unit_ids = {u["id"] for u in units_doc.get("units", [])}
    owned, _, _ = map_ownership(units_doc, expand_scope(units_doc, repo), repo)
    issues = []
    resolved = []
    seen_req, seen_ob = set(), set()
    for req in spine.get("requirements", []):
        rid = req.get("id", "?")
        if rid in seen_req:
            issues.append(f"{rid}: duplicate requirement id")
        seen_req.add(rid)
        if not (req.get("claim") or "").strip():
            issues.append(f"{rid}: empty claim")
        anchor = req.get("design_anchor", "")
        if not anchor or not (repo / anchor).is_file():
            issues.append(f"{rid}: design_anchor missing on disk: {anchor!r}")
        obligations = req.get("obligations") or []
        if not obligations:
            issues.append(f"{rid}: no obligations")
        for ob in obligations:
            oid = ob.get("id", "?")
            if oid in seen_ob:
                issues.append(f"{oid}: duplicate obligation id")
            seen_ob.add(oid)
            owner = ob.get("owned_by", "")
            if owner not in unit_ids:
                issues.append(f"{oid}: owned_by unknown unit {owner!r}")
            if ob.get("granularity") not in GRANULARITIES:
                issues.append(f"{oid}: bad granularity {ob.get('granularity')!r}")
            status = ob.get("status")
            if status not in STATUSES:
                issues.append(f"{oid}: bad status {status!r}")
            repro = ob.get("repro")
            if repro and not (repo / repro).is_file():
                issues.append(f"{oid}: repro missing on disk: {repro}")
            effective = status
            if status == "refuted" and not (ob.get("refuted_by") or "").strip():
                issues.append(f"{oid}: refuted without refuted_by")
            if status == "closed":
                evidence = ob.get("evidence") or []
                if not evidence:
                    issues.append(f"{oid}: closed without evidence")
                stale_files = []
                for ev in evidence:
                    node = ev.get("test", "")
                    if not _test_node_exists(repo, node):
                        issues.append(f"{oid}: evidence node not found: {node}")
                        continue
                    sha = str(ev.get("observed_at", ""))
                    if not sha or not _commit_exists(repo, sha):
                        issues.append(f"{oid}: observed_at not a commit: {sha!r}")
                        continue
                    watch = list(owned.get(owner, [])) + [node.split("::")[0]]
                    changed = _changed_since(repo, sha, watch)
                    if changed:
                        stale_files.extend(changed)
                if stale_files:
                    effective = "stale"
            resolved.append({
                "requirement_id": rid, "obligation_id": oid, "owned_by": owner,
                "granularity": ob.get("granularity"), "status": status,
                "effective_status": effective,
                "evidence": ob.get("evidence") or [],
                "refuted_by": ob.get("refuted_by", ""),
            })
    return issues, resolved


def scan(write_db: bool = True):
    doc = load_ontology()
    scope_files = expand_scope(doc)
    owned, orphans, overlaps = map_ownership(doc, scope_files)
    tests = discover_tests(owned)
    missing = check_declared(doc)
    levels = compute_levels(doc, owned, tests)
    spine = load_spine()
    spine_issues, spine_resolved = validate_spine(spine, doc)

    result = {
        "doc": doc, "owned": owned, "orphans": orphans, "overlaps": overlaps,
        "tests": tests, "missing": missing, "levels": levels,
        "n_scope": len(scope_files),
        "spine": spine, "spine_issues": spine_issues, "spine_resolved": spine_resolved,
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
    con.executemany(
        "INSERT INTO spine_state VALUES (?,?,?,?,?,?,?,?,?)",
        [(sid, r["requirement_id"], r["obligation_id"], r["owned_by"],
          r["granularity"], r["status"], r["effective_status"],
          json.dumps(r["evidence"], ensure_ascii=False), r["refuted_by"])
         for r in spine_resolved])
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
    # --- ROCEV 척추 추적표 ---
    by_req = {}
    for ob in r["spine_resolved"]:
        by_req.setdefault(ob["requirement_id"], []).append(ob)
    if by_req:
        print("--- traceability (requirement → obligations) ---")
        for req in r["spine"].get("requirements", []):
            obs = by_req.get(req["id"], [])
            cnt = {}
            for ob in obs:
                cnt[ob["effective_status"]] = cnt.get(ob["effective_status"], 0) + 1
            summary = " ".join(f"{k}={v}" for k, v in sorted(cnt.items()))
            print(f"{req['id']}: {summary}")
            print(f"    \"{req.get('claim', '')}\"")
            for ob in obs:
                if ob["effective_status"] == "closed":
                    continue
                tag = ob["effective_status"].upper()
                why = ob["refuted_by"].strip() if ob["refuted_by"] else ""
                print(f"    [{tag}] {ob['obligation_id']} ({ob['owned_by']})"
                      + (f" — {why[:80]}" if why else ""))
    if r["spine_issues"]:
        print("--- SPINE INTEGRITY ISSUES ---")
        for issue in r["spine_issues"]:
            print(f"  {issue}")
    print(f"--- orphans (top 15 by size) ---")
    top = sorted(r["orphans"], key=lambda o: -_count_lines(REPO / o))[:15]
    for o in top:
        print(f"  {o} ({_count_lines(REPO / o)}L)")
    return r


def backlog() -> int:
    """작업 큐: open(미착수 약속) + refuted(반증된 약속 = 결함) 목록."""
    r = scan(write_db=False)
    items = [o for o in r["spine_resolved"]
             if o["effective_status"] in ("open", "refuted", "stale")]
    if not items:
        print("[ontology] backlog empty — all obligations closed & fresh")
        return 0
    order = {"refuted": 0, "stale": 1, "open": 2}
    items.sort(key=lambda o: (order[o["effective_status"]], o["owned_by"]))
    print(f"=== backlog ({len(items)}) — refuted(결함) > stale(재검증) > open(미착수) ===")
    for ob in items:
        tag = ob["effective_status"].upper()
        print(f"[{tag:7}] {ob['obligation_id']}  ({ob['owned_by']}, {ob['granularity']})")
        if ob["refuted_by"]:
            print(f"          {ob['refuted_by'].strip()}")
    return 0


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
    for issue in r["spine_issues"]:
        rc = 1
        print(f"[ontology] FAIL: spine: {issue}")
    stale = [o for o in r["spine_resolved"] if o["effective_status"] == "stale"]
    for ob in stale:  # 신선도는 경고 (재실행+observed_at 갱신이 처방)
        print(f"[ontology] WARN: stale evidence: {ob['obligation_id']} "
              f"(owner 코드/테스트가 observed_at 이후 변경됨 — 재검증 필요)")
    if rc == 0:
        n_ob = len(r["spine_resolved"])
        closed = sum(1 for o in r["spine_resolved"] if o["effective_status"] == "closed")
        print(f"[ontology] PASS: declared paths OK, no overlap, "
              f"orphans {len(r['orphans'])} ≤ baseline {baseline}, "
              f"spine {closed}/{n_ob} closed ({len(stale)} stale)")
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
    if cmd == "backlog":
        return backlog()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
