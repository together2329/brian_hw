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


# ---------- ROCEV 척추 (requirement→obligation→evidence) ----------

def test_spine_integrity_on_real_repo():
    """실제 척추 선언: 무결성 issue 0 (유령 노드/anchor/owner 없음)."""
    issues, resolved = po.validate_spine(po.load_spine(), po.load_ontology())
    assert issues == [], f"spine integrity issues: {issues}"
    assert resolved, "spine must declare obligations"


def test_spine_every_refuted_has_reason_and_closed_has_evidence():
    _, resolved = po.validate_spine(po.load_spine(), po.load_ontology())
    for ob in resolved:
        if ob["status"] == "refuted":
            assert ob["refuted_by"].strip(), f"{ob['obligation_id']}: refuted without reason"
        if ob["status"] == "closed":
            assert ob["evidence"], f"{ob['obligation_id']}: closed without evidence"


def _spine(obligation):
    return {"requirements": [{
        "id": "REQ_X", "claim": "c", "design_anchor": "anchor.md",
        "obligations": [obligation],
    }]}


def _units_doc():
    return {"scope": [], "orphan_baseline": 0,
            "units": [{"id": "u", "owns": []}]}


def test_spine_killproof_ghost_evidence_node(tmp_path):
    """KILL-PROOF: 존재하지 않는 테스트 노드를 evidence로 선언하면 잡혀야 한다."""
    (tmp_path / "anchor.md").write_text("a", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_real.py").write_text(
        "class TestC:\n    def test_m(self):\n        pass\n\ndef test_f():\n    pass\n",
        encoding="utf-8")
    ok_func = {"id": "O1", "owned_by": "u", "granularity": "behavior", "status": "closed",
               "evidence": [{"test": "tests/test_real.py::test_f", "observed_at": "x"}]}
    ok_method = {"id": "O1", "owned_by": "u", "granularity": "behavior", "status": "closed",
                 "evidence": [{"test": "tests/test_real.py::TestC::test_m", "observed_at": "x"}]}
    ghost = {"id": "O1", "owned_by": "u", "granularity": "behavior", "status": "closed",
             "evidence": [{"test": "tests/test_real.py::test_ghost", "observed_at": "x"}]}
    for ob, node_ok in ((ok_func, True), (ok_method, True), (ghost, False)):
        issues, _ = po.validate_spine(_spine(ob), _units_doc(), tmp_path)
        node_issues = [i for i in issues if "evidence node not found" in i]
        assert bool(node_issues) == (not node_ok), f"{ob['evidence']}: {issues}"


def test_spine_killproof_contract_violations(tmp_path):
    """closed-without-evidence / refuted-without-reason / unknown owner / ghost anchor."""
    (tmp_path / "anchor.md").write_text("a", encoding="utf-8")
    cases = [
        ({"id": "O", "owned_by": "u", "granularity": "behavior", "status": "closed"},
         "closed without evidence"),
        ({"id": "O", "owned_by": "u", "granularity": "behavior", "status": "refuted"},
         "refuted without refuted_by"),
        ({"id": "O", "owned_by": "nobody", "granularity": "behavior", "status": "open"},
         "owned_by unknown unit"),
        ({"id": "O", "owned_by": "u", "granularity": "vibes", "status": "open"},
         "bad granularity"),
    ]
    for ob, expected in cases:
        issues, _ = po.validate_spine(_spine(ob), _units_doc(), tmp_path)
        assert any(expected in i for i in issues), f"{expected!r} not caught: {issues}"
    ghost_anchor = _spine({"id": "O", "owned_by": "u", "granularity": "behavior",
                           "status": "open"})
    ghost_anchor["requirements"][0]["design_anchor"] = "ghost.md"
    issues, _ = po.validate_spine(ghost_anchor, _units_doc(), tmp_path)
    assert any("design_anchor missing" in i for i in issues)


def test_spine_freshness_marks_stale(tmp_path):
    """observed_at 이후 owner 코드가 바뀌면 effective_status=stale (git 픽스처)."""
    import subprocess
    def git(*a):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True,
                       capture_output=True, text=True)
    git("init", "-q")
    git("config", "user.email", "t@t"); git("config", "user.name", "t")
    (tmp_path / "anchor.md").write_text("a", encoding="utf-8")
    (tmp_path / "pkg").mkdir(); (tmp_path / "tests").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests" / "test_a.py").write_text("def test_f():\n    pass\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-qm", "base")
    out = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True)
    sha = out.stdout.strip()
    units = {"scope": ["pkg/*.py"], "orphan_baseline": 0,
             "units": [{"id": "u", "owns": ["pkg/a.py"]}]}
    ob = {"id": "O", "owned_by": "u", "granularity": "behavior", "status": "closed",
          "evidence": [{"test": "tests/test_a.py::test_f", "observed_at": sha}]}
    issues, resolved = po.validate_spine(_spine(ob), units, tmp_path)
    assert issues == [] and resolved[0]["effective_status"] == "closed"  # 변경 전: fresh
    (tmp_path / "pkg" / "a.py").write_text("x = 2\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-qm", "change owner code")
    issues, resolved = po.validate_spine(_spine(ob), units, tmp_path)
    assert issues == [] and resolved[0]["effective_status"] == "stale"  # 변경 후: stale


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
