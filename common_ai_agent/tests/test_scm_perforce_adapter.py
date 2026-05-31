"""Tests for the deployment Perforce adapter (core/scm_perforce.py).

The override-loading tests run anywhere. The live tests talk to a local Helix
Core server and are skipped unless `p4 info` succeeds against a configured
workspace (see scripts/perforce_setup.sh).
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Union

import pytest

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.scm import resolve_scm_adapter  # noqa: E402
from core.scm_perforce import PerforceP4Adapter  # noqa: E402

ADAPTER_REF = "core.scm_perforce:PerforceP4Adapter"


def _p4_ready() -> bool:
    try:
        a = PerforceP4Adapter(PROJECT_ROOT)
        return a.detect().ok and a._client_root() is not None
    except Exception:
        return False


p4_required = pytest.mark.skipif(not _p4_ready(), reason="no reachable/configured p4 workspace")


# ----------------------------------------------------------------- no server
def test_override_loads_real_adapter(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    monkeypatch.setenv("ATLAS_SCM_ADAPTER_PERFORCE", ADAPTER_REF)
    adapter = resolve_scm_adapter(tmp_path)
    assert adapter.__class__.__name__ == "PerforceP4Adapter"
    assert adapter.provider == "perforce"
    caps = adapter.capabilities()
    assert caps["submit"] is True
    assert caps["sync"] is True
    assert caps["status"] is True


def test_safe_filespecs_rejects_escapes(tmp_path):
    a = PerforceP4Adapter(tmp_path)
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    specs = a._safe_filespecs(["a.txt", "../../etc/passwd", "/abs/escape"])
    # only the in-root relative path survives
    assert specs == [(tmp_path / "a.txt").resolve().as_posix()]


def test_submit_refused_at_client_root(monkeypatch):
    # When the adapter root equals the client root, submit must refuse so a
    # blanket reconcile can never sweep the whole workspace (.env, etc.).
    a = PerforceP4Adapter(PROJECT_ROOT)
    if a._client_root() is None or a._client_root() != a.root:
        pytest.skip("client root not equal to project root in this environment")
    res = a.submit("should refuse")
    assert res.ok is False
    assert "client root" in res.error


def test_edit_paths_runs_p4_edit_and_rejects_escapes(tmp_path):
    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="opened")

    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    adapter = RecordingAdapter(tmp_path)
    ok = adapter.edit_paths(["a.txt", "../../etc/passwd"])
    assert ok.ok is True
    assert ok.returncode == 0
    assert adapter.calls == [("edit", (tmp_path / "a.txt").resolve().as_posix())]

    invalid = RecordingAdapter(tmp_path)
    bad = invalid.edit_paths(["../../etc/passwd", "/abs/escape"])
    assert bad.ok is False
    assert bad.returncode == 2
    assert "no valid paths" in bad.error
    assert invalid.calls == []


# --------------------------------------------------------------- live server
@p4_required
def test_live_status_and_pane_shapes():
    a = PerforceP4Adapter(PROJECT_ROOT)
    st = a.status()
    assert st["provider"] == "perforce"
    assert set(["ok", "branch", "head", "dirty", "files"]).issubset(st.keys())
    ss = a.sync_state()
    assert ss["ok"] is True
    for key in ("local", "depot", "pending", "client", "stream"):
        assert key in ss


@p4_required
def test_live_submit_sync_roundtrip():
    proj = Path(PROJECT_ROOT)
    smoke = proj / f"_p4_pytest_{os.getpid()}"
    depot_path = f"//GOOD_SOC/GOOD_IP/{smoke.name}/..."
    smoke.mkdir(exist_ok=True)
    fpath = smoke / "hello.txt"
    fpath.write_text("v1\n", encoding="utf-8")
    a = PerforceP4Adapter(smoke)
    try:
        # new file shows as add
        st = a.status()
        assert st["dirty"] is True
        assert any(f["action"] == "add" for f in st["files"])

        sub = a.submit("pytest roundtrip v1")
        assert sub.ok, sub.error or sub.stderr

        # overwrite local, then force-sync should restore depot content
        os.chmod(fpath, 0o644)
        fpath.write_text("LOCAL EDIT\n", encoding="utf-8")
        syn = a.sync()
        assert syn.ok, syn.error or syn.stderr
        assert fpath.read_text(encoding="utf-8").strip() == "v1"

        assert a.status()["dirty"] is False
    finally:
        a._run_p4("revert", a._scope)
        subprocess.run(["p4", "obliterate", "-y", depot_path], capture_output=True, text=True)
        for p in sorted(smoke.rglob("*"), reverse=True):
            try:
                os.chmod(p, 0o644)
            except OSError:
                pass
        try:
            os.chmod(fpath, 0o644)
        except OSError:
            pass
        import shutil
        shutil.rmtree(smoke, ignore_errors=True)
