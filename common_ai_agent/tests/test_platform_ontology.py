"""platform ontology 래칫 + 스캐너 자체검증 (kill-proof 포함).

원칙: 검사관(스캐너)은 가짜를 잡는 시험을 통과해야 일한다.
- 선언 경로가 디스크에 없으면 레벨이 오르면 안 된다 (silent-PASS 금지)
- 실제 repo에 대해: 선언 경로 전부 실재, 소유권 중복 0, orphan ≤ baseline
"""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "platform_ontology", REPO / "scripts" / "platform_ontology.py")
po = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(po)


# ---------- 실제 repo에 대한 래칫 ----------

def test_yaml_loads_and_unit_ids_unique():
    doc = po.load_ontology()
    ids = [u["id"] for u in doc["units"]]
    assert ids, "units must not be empty"
    assert len(ids) == len(set(ids)), f"duplicate unit ids: {ids}"


def test_declared_paths_all_exist():
    """선언된 content_tests/e2e_evidence/ratchet_tests 는 전부 실재해야 한다."""
    missing = po.check_declared(po.load_ontology())
    assert missing == [], f"declared-but-missing paths: {missing}"


def test_no_ownership_overlap_and_orphan_ratchet():
    doc = po.load_ontology()
    scope = po.expand_scope(doc)
    _owned, orphans, overlaps = po.map_ownership(doc, scope)
    assert overlaps == [], f"files owned by multiple units: {overlaps}"
    baseline = doc.get("orphan_baseline")
    assert baseline is not None, "orphan_baseline must be set after first scan"
    assert len(orphans) <= baseline, (
        f"orphans {len(orphans)} > baseline {baseline} — 새 모듈을 만들었으면 "
        f"ontology/platform_ontology.yaml 의 단위에 등록하세요 (목록: {orphans[:5]} ...)")


def test_check_passes_on_real_repo():
    assert po.check() == 0


# ---------- 스캐너 로직 kill-proof (조작된 입력으로 검증) ----------

def _doc(units, scope=("pkg/*.py",), baseline=None):
    return {"scope": list(scope), "orphan_baseline": baseline, "units": units}


def _mkrepo(tmp_path, files):
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def test_ownership_glob_orphan_overlap(tmp_path):
    repo = _mkrepo(tmp_path, {"pkg/a.py": "", "pkg/b.py": "", "pkg/c.py": ""})
    doc = _doc([
        {"id": "u1", "owns": ["pkg/a.py"]},
        {"id": "u2", "owns": ["pkg/a.py", "pkg/b.py"]},  # a.py 중복 소유
    ])
    scope = po.expand_scope(doc, repo)
    owned, orphans, overlaps = po.map_ownership(doc, scope, repo)
    assert owned["u1"] == ["pkg/a.py"]
    assert orphans == ["pkg/c.py"]
    assert overlaps == [("pkg/a.py", ["u1", "u2"])]


def test_missing_declared_path_blocks_level(tmp_path):
    """KILL-PROOF: 존재하지 않는 content_tests 선언은 L2를 주면 안 된다."""
    repo = _mkrepo(tmp_path, {
        "pkg/a.py": "",
        "tests/test_a.py": "import pkg.a\n",
    })
    real = {"id": "u", "owns": ["pkg/a.py"], "content_tests": ["tests/test_a.py"]}
    fake = {"id": "u", "owns": ["pkg/a.py"], "content_tests": ["tests/test_ghost.py"]}

    for unit, expected in ((real, 2), (fake, 1)):
        doc = _doc([unit])
        owned, _, _ = po.map_ownership(doc, po.expand_scope(doc, repo), repo)
        tests = po.discover_tests(owned, repo)
        levels = po.compute_levels(doc, owned, tests, repo)
        assert levels["u"] == expected, f"unit={unit} expected L{expected}, got L{levels['u']}"
    assert po.check_declared(_doc([fake]), repo) == [("u", "content_tests", "tests/test_ghost.py")]


def test_level_ladder_is_cumulative(tmp_path):
    """e2e 선언만 있고 content_tests 가 없으면 L3로 건너뛸 수 없다."""
    repo = _mkrepo(tmp_path, {
        "pkg/a.py": "",
        "tests/test_a.py": "import pkg.a\n",
        "e2e/run.py": "",
    })
    unit = {"id": "u", "owns": ["pkg/a.py"], "e2e_evidence": ["e2e/run.py"]}
    doc = _doc([unit])
    owned, _, _ = po.map_ownership(doc, po.expand_scope(doc, repo), repo)
    tests = po.discover_tests(owned, repo)
    assert po.compute_levels(doc, owned, tests, repo)["u"] == 1  # not 3


def test_out_of_scope_literal_owns_counts(tmp_path):
    """scope 밖 literal owns(예: scripts/...)도 실재하면 소유로 인정, 유령 경로는 무시."""
    repo = _mkrepo(tmp_path, {"pkg/a.py": "", "scripts/tool.py": ""})
    doc = _doc([{"id": "u", "owns": ["scripts/tool.py", "scripts/ghost.py"]}])
    owned, orphans, _ = po.map_ownership(doc, po.expand_scope(doc, repo), repo)
    assert owned["u"] == ["scripts/tool.py"]
    assert orphans == ["pkg/a.py"]


def test_discover_tests_matches_import_and_path(tmp_path):
    repo = _mkrepo(tmp_path, {
        "pkg/mod.py": "",
        "tests/test_import.py": "from pkg.mod import thing\n",
        "tests/test_path.py": 'run(["python3", "pkg/mod.py"])\n',
        "tests/test_unrelated.py": "import os\n",
    })
    owned = {"u": ["pkg/mod.py"]}
    tests = po.discover_tests(owned, repo)
    assert tests["u"] == ["tests/test_import.py", "tests/test_path.py"]


def test_scan_writes_snapshot(tmp_path, monkeypatch):
    db = tmp_path / "platform.db"
    monkeypatch.setattr(po, "ONTOLOGY_DB", db)
    r = po.scan(write_db=True)
    assert r["snapshot_id"] >= 1
    con = sqlite3.connect(db)
    n_units = con.execute("SELECT COUNT(*) FROM unit_state").fetchone()[0]
    n_snap = con.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    con.close()
    assert n_snap == 1
    assert n_units == len(po.load_ontology()["units"])
