import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.scm import SCMCommandResult


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=True,
    )


def _init_repo(path: Path, branch: str = "main") -> None:
    path.mkdir(parents=True, exist_ok=True)
    _ = _run_git(path, "init", "-q", "-b", branch)
    _ = _run_git(path, "config", "user.email", "atlas@local")
    _ = _run_git(path, "config", "user.name", "Atlas Test")


def _create_app(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_COOKIE_SECRET", "test-secret")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    # These exercise SCM ADAPTER routing (git vs perforce), not tenant authz —
    # run single-user so the per-IP authz gate (covered separately in
    # test_atlas_authz_e2e) allows the test IPs the registered user doesn't own.
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    from src import atlas_ui

    atlas_ui.PROJECT_ROOT = tmp_path
    return atlas_ui.create_app()


def _authenticated_client(app) -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"username": "gituser", "password": "pw"},
    )
    assert response.status_code == 200, response.text
    return client


def test_git_api_targets_explicit_ip_repo(tmp_path: Path, monkeypatch):
    root_repo = tmp_path
    _init_repo(root_repo, branch="rootbranch")
    _ = (root_repo / "root.txt").write_text("root\n", encoding="utf-8")
    _ = _run_git(root_repo, "add", "root.txt")
    _ = _run_git(root_repo, "commit", "-q", "-m", "root initial")

    ip_repo = tmp_path / "alpha"
    _init_repo(ip_repo, branch="ipbranch")
    _ = (ip_repo / "foo.txt").write_text("one\n", encoding="utf-8")
    _ = _run_git(ip_repo, "add", "foo.txt")
    _ = _run_git(ip_repo, "commit", "-q", "-m", "ip initial")
    _ = (ip_repo / "foo.txt").write_text("two\n", encoding="utf-8")

    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    status = client.get("/api/git/status?ip=alpha").json()
    assert status["ip"] == "alpha"
    assert status["branch"] == "ipbranch"
    assert status["head"]
    assert status["head_full"]
    assert status["dirty"] is True
    assert status["cwd"] == str(ip_repo)
    assert status["files"] == [
        {"path": "foo.txt", "status": " M", "staged": False, "unstaged": True, "added": 1, "removed": 1}
    ]

    show = client.get(f"/api/git/show?ip=alpha&sha={status['head_full']}").json()
    assert show["ip"] == "alpha"
    assert "ip initial" in show["diff"]
    assert "root initial" not in show["diff"]

    show_alias = client.get(f"/api/scm/show?ip=alpha&revision={status['head_full']}").json()
    assert show_alias["provider"] == "git"
    assert show_alias["revision"] == status["head_full"]

    diff = client.get("/api/git/diff?ip=alpha&path=foo.txt").json()
    assert diff["ip"] == "alpha"
    assert "-one" in diff["diff"]
    assert "+two" in diff["diff"]

    commit = client.post(
        "/api/git/commit",
        json={"ip": "alpha", "message": "ip checkpoint", "add_all": True},
    ).json()
    assert commit["ok"] is True, commit
    assert commit["ip"] == "alpha"

    latest_ip = _run_git(ip_repo, "log", "-1", "--pretty=%s").stdout.strip()
    latest_root = _run_git(root_repo, "log", "-1", "--pretty=%s").stdout.strip()
    assert latest_ip == "ip checkpoint"
    assert latest_root == "root initial"

    graph = client.get("/api/ip/alpha/git/graph?limit=20").json()
    assert graph["provider"] == "git"
    assert graph["commits"][0]["subject"] == "ip checkpoint"

    ip_log = client.get("/api/ip/alpha/git/log?limit=20").json()
    assert ip_log["provider"] == "git"
    assert ip_log["commits"][0]["subject"] == "ip checkpoint"

    revert = client.post(
        "/api/ip/alpha/git/revert",
        json={"hash": status["head_full"]},
    ).json()
    assert revert["ok"] is True, revert
    assert revert["provider"] == "git"
    assert _run_git(ip_repo, "log", "-1", "--pretty=%s").stdout.strip() == "ip initial"

    push = client.post("/api/git/push", json={"ip": "alpha"}).json()
    assert push["branch"] == "ipbranch"
    assert push["ip"] == "alpha"


def test_git_api_targets_v2_session_ip_root(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path / "atlas-root"))
    legacy_ip = tmp_path / "NEWIP_MCTP"
    legacy_ip.mkdir()

    ip_repo = tmp_path / "atlas-root" / "alice" / "s1" / "NEWIP_MCTP"
    _init_repo(ip_repo, branch="v2branch")
    _ = (ip_repo / "foo.txt").write_text("one\n", encoding="utf-8")
    _ = _run_git(ip_repo, "add", "foo.txt")
    _ = _run_git(ip_repo, "commit", "-q", "-m", "v2 ip initial")
    _ = (ip_repo / "foo.txt").write_text("two\n", encoding="utf-8")

    client = _authenticated_client(_create_app(tmp_path, monkeypatch))
    session_id = "alice/s1/NEWIP_MCTP/default"

    status = client.get(
        "/api/git/status",
        params={"ip": "NEWIP_MCTP", "session_id": session_id},
    ).json()
    assert status["ip"] == "NEWIP_MCTP"
    assert status["branch"] == "v2branch"
    assert status["cwd"] == str(ip_repo)
    assert status["dirty"] is True

    graph = client.get(
        "/api/ip/NEWIP_MCTP/git/graph",
        params={"limit": "20", "session_id": session_id},
    ).json()
    assert graph["provider"] == "git"
    assert graph["commits"][0]["subject"] == "v2 ip initial"


def test_git_api_does_not_fallback_to_root_for_ip_without_git(tmp_path: Path, monkeypatch):
    _init_repo(tmp_path, branch="rootbranch")
    _ = (tmp_path / "root.txt").write_text("root\n", encoding="utf-8")
    _ = _run_git(tmp_path, "add", "root.txt")
    _ = _run_git(tmp_path, "commit", "-q", "-m", "root initial")
    (tmp_path / "beta").mkdir()

    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    responses = [
        client.get("/api/git/status?ip=beta"),
        client.get("/api/git/diff?ip=beta&path=root.txt"),
        client.post("/api/git/commit", json={"ip": "beta", "message": "wrong repo"}),
        client.post("/api/git/push", json={"ip": "beta"}),
    ]
    for response in responses:
        assert response.status_code == 409
        assert response.json()["error"] == "ip has no .git"

    assert _run_git(tmp_path, "log", "-1", "--pretty=%s").stdout.strip() == "root initial"


def test_scm_api_alias_accepts_perforce_workspace_without_git_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    (tmp_path / "beta").mkdir()

    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    response = client.get("/api/scm/status?ip=beta")
    assert response.status_code == 200
    status = response.json()
    assert status["provider"] == "perforce"
    assert status["ip"] == "beta"
    assert status["cwd"] == str(tmp_path / "beta")
    assert status["files"] == []
    assert "not implemented" in status["error"]


def test_git_provider_override_stays_git_when_default_scm_is_perforce(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    ip_repo = tmp_path / "alpha"
    _init_repo(ip_repo, branch="ipbranch")
    _ = (ip_repo / "foo.txt").write_text("one\n", encoding="utf-8")
    _ = _run_git(ip_repo, "add", "foo.txt")
    _ = _run_git(ip_repo, "commit", "-q", "-m", "ip initial")
    (tmp_path / "beta").mkdir()

    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    scm_status = client.get("/api/scm/status?ip=alpha").json()
    assert scm_status["provider"] == "perforce"
    assert "not implemented" in scm_status["error"]

    git_status = client.get("/api/git/status?ip=alpha&provider=git").json()
    assert git_status["provider"] == "git"
    assert git_status["ip"] == "alpha"
    assert git_status["branch"] == "ipbranch"
    assert git_status["cwd"] == str(ip_repo)

    graph = client.get("/api/ip/alpha/git/graph?limit=20&provider=git").json()
    assert graph["provider"] == "git"
    assert graph["commits"][0]["subject"] == "ip initial"

    missing_git = client.get("/api/ip/beta/git/graph?limit=20&provider=git")
    assert missing_git.status_code == 409
    assert missing_git.json()["error"] == "ip has no .git — create via /new-ip first"


def test_scm_status_allows_perforce_root_inside_configured_external_workspace(tmp_path: Path, monkeypatch):
    project_root = tmp_path / "project"
    p4_workspace = tmp_path / "p4_workspace"
    project_root.mkdir(parents=True)
    p4_workspace.mkdir(parents=True)
    monkeypatch.setenv("P4_WORKSPACE_ROOT", str(p4_workspace))
    seen: dict[str, object] = {}

    class FakePerforceAdapter:
        provider = "perforce"

        def __init__(self, root: str) -> None:
            self.root = root

        def status(self, *, local_root=None):
            seen["local_root"] = local_root
            return {
                "ok": True,
                "provider": self.provider,
                "branch": "",
                "head": "",
                "head_full": "",
                "files": [],
            }

    def fake_resolve_scm_adapter(root: str, provider=None):
        seen["root"] = root
        seen["provider"] = provider
        return FakePerforceAdapter(root)

    monkeypatch.setattr("atlas_api_git.resolve_scm_adapter", fake_resolve_scm_adapter)
    client = _authenticated_client(_create_app(project_root, monkeypatch))

    response = client.get(
        "/api/scm/status",
        params={"provider": "perforce", "scm_root": str(p4_workspace)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "perforce"
    assert payload["scmRoot"] == str(p4_workspace)
    assert seen == {
        "root": str(p4_workspace),
        "provider": "perforce",
        "local_root": str(project_root),
    }


def test_scm_status_rejects_external_perforce_root_without_configured_workspace(tmp_path: Path, monkeypatch):
    project_root = tmp_path / "project"
    p4_workspace = tmp_path / "p4_workspace"
    project_root.mkdir(parents=True)
    p4_workspace.mkdir(parents=True)

    client = _authenticated_client(_create_app(project_root, monkeypatch))

    response = client.get(
        "/api/scm/status",
        params={"provider": "perforce", "scm_root": str(p4_workspace)},
    )

    assert response.status_code == 400
    assert response.json()["error"] == (
        "scmRoot escapes project root or configured Perforce workspace root"
    )


def test_scm_status_rejects_external_git_root_even_with_configured_perforce_workspace(tmp_path: Path, monkeypatch):
    project_root = tmp_path / "project"
    p4_workspace = tmp_path / "p4_workspace"
    project_root.mkdir(parents=True)
    p4_workspace.mkdir(parents=True)
    monkeypatch.setenv("P4_WORKSPACE_ROOT", str(p4_workspace))

    client = _authenticated_client(_create_app(project_root, monkeypatch))

    response = client.get(
        "/api/scm/status",
        params={"provider": "git", "scm_root": str(p4_workspace)},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "scmRoot escapes project root"


def test_scm_edit_route_uses_perforce_adapter(tmp_path: Path, monkeypatch):
    (tmp_path / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "p4_workspace").mkdir(parents=True, exist_ok=True)
    seen: dict[str, object] = {}

    class FakePerforceAdapter:
        provider = "perforce"

        def __init__(self, root: str) -> None:
            self.root = root

        def edit_paths(self, paths, *, local_root=None, target_paths=None, stream="", changelist=""):
            seen["paths"] = list(paths)
            seen["local_root"] = local_root
            seen["target_paths"] = list(target_paths or [])
            seen["stream"] = stream
            seen["changelist"] = changelist
            return SCMCommandResult(
                ok=True,
                provider=self.provider,
                root=self.root,
                stdout="edit ok",
                returncode=0,
                command=("p4", "edit"),
            )

    def fake_resolve_scm_adapter(root: str, provider=None):
        seen["root"] = root
        seen["provider"] = provider
        return FakePerforceAdapter(root)

    monkeypatch.setattr("atlas_api_git.resolve_scm_adapter", fake_resolve_scm_adapter)
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))
    response = client.post(
        "/api/scm/edit",
        json={
            "ip": "alpha",
            "provider": "perforce",
            "scmRoot": str(tmp_path / "p4_workspace"),
            "stream": "//GOOD_SOC/GOOD_IP",
            "paths": ["foo.v"],
            "targetPaths": ["//GOOD_SOC/GOOD_IP/rtl/foo.v"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["provider"] == "perforce"
    assert payload["ip"] == "alpha"
    assert payload["cwd"] == str(tmp_path / "alpha")
    assert payload["localRoot"] == str(tmp_path / "alpha")
    assert payload["scmRoot"] == str(tmp_path / "p4_workspace")
    assert payload["stdout"] == "edit ok"
    assert seen == {
        "root": str(tmp_path / "p4_workspace"),
        "provider": "perforce",
        "paths": ["foo.v"],
        "local_root": str(tmp_path / "alpha"),
        "target_paths": ["//GOOD_SOC/GOOD_IP/rtl/foo.v"],
        "stream": "//GOOD_SOC/GOOD_IP",
        "changelist": "",
    }


def test_scm_edit_route_can_checkout_perforce_target_without_local_root(tmp_path: Path, monkeypatch):
    (tmp_path / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "p4_workspace").mkdir(parents=True, exist_ok=True)
    seen: dict[str, object] = {}

    class FakePerforceAdapter:
        provider = "perforce"

        def __init__(self, root: str) -> None:
            self.root = root

        def edit_paths(self, paths, *, local_root=None, target_paths=None, stream="", changelist=""):
            seen["paths"] = list(paths)
            seen["local_root"] = local_root
            seen["target_paths"] = list(target_paths or [])
            seen["stream"] = stream
            seen["changelist"] = changelist
            return SCMCommandResult(
                ok=True,
                provider=self.provider,
                root=self.root,
                stdout="checkout ok",
                returncode=0,
                command=("p4", "edit"),
            )

    def fake_resolve_scm_adapter(root: str, provider=None):
        seen["root"] = root
        seen["provider"] = provider
        return FakePerforceAdapter(root)

    monkeypatch.setattr("atlas_api_git.resolve_scm_adapter", fake_resolve_scm_adapter)
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))
    response = client.post(
        "/api/scm/edit",
        json={
            "ip": "alpha",
            "provider": "perforce",
            "scmRoot": str(tmp_path / "p4_workspace"),
            "stream": "//GOOD_SOC/GOOD_IP",
            "sourceRoot": "scm",
            "changelist": "12",
            "paths": ["//GOOD_SOC/GOOD_IP/rtl/foo.v"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["stdout"] == "checkout ok"
    assert seen == {
        "root": str(tmp_path / "p4_workspace"),
        "provider": "perforce",
        "paths": ["//GOOD_SOC/GOOD_IP/rtl/foo.v"],
        "local_root": None,
        "target_paths": [],
        "stream": "//GOOD_SOC/GOOD_IP",
        "changelist": "12",
    }


def test_scm_pane_route_passes_directory_scope_to_perforce_adapter(tmp_path: Path, monkeypatch):
    (tmp_path / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "p4_workspace").mkdir(parents=True, exist_ok=True)
    seen: dict[str, object] = {}

    class FakePerforceAdapter:
        provider = "perforce"

        def __init__(self, root: str) -> None:
            self.root = root

        def sync_state(
            self,
            *,
            local_root=None,
            stream="",
            local_dir="",
            depot_dir="",
        ):
            seen["local_root"] = local_root
            seen["stream"] = stream
            seen["local_dir"] = local_dir
            seen["depot_dir"] = depot_dir
            return {
                "ok": True,
                "provider": self.provider,
                "local": [],
                "depot": [],
                "pending": [],
            }

    def fake_resolve_scm_adapter(root: str, provider=None):
        seen["root"] = root
        seen["provider"] = provider
        return FakePerforceAdapter(root)

    monkeypatch.setattr("atlas_api_git.resolve_scm_adapter", fake_resolve_scm_adapter)
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    response = client.get(
        "/api/scm/pane",
        params={
            "ip": "alpha",
            "provider": "perforce",
            "scm_root": str(tmp_path / "p4_workspace"),
            "stream": "//GOOD_SOC/GOOD_IP",
            "local_dir": "rtl",
            "depot_dir": "//GOOD_SOC/GOOD_IP/rtl/",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert seen == {
        "root": str(tmp_path / "p4_workspace"),
        "provider": "perforce",
        "local_root": str(tmp_path / "alpha"),
        "stream": "//GOOD_SOC/GOOD_IP",
        "local_dir": "rtl",
        "depot_dir": "//GOOD_SOC/GOOD_IP/rtl/",
    }


def test_scm_sync_route_rejects_empty_perforce_selection_with_target_folder(tmp_path: Path, monkeypatch):
    (tmp_path / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "p4_workspace").mkdir(parents=True, exist_ok=True)
    seen: dict[str, object] = {}

    class FakePerforceAdapter:
        provider = "perforce"

        def __init__(self, root: str) -> None:
            self.root = root

        def sync(self, revision: str = "", stream: str = ""):
            seen["sync_called"] = True
            return SCMCommandResult(ok=True, provider=self.provider, root=self.root)

    def fake_resolve_scm_adapter(root: str, provider=None):
        seen["root"] = root
        seen["provider"] = provider
        return FakePerforceAdapter(root)

    monkeypatch.setattr("atlas_api_git.resolve_scm_adapter", fake_resolve_scm_adapter)
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    response = client.post(
        "/api/scm/sync",
        json={
            "ip": "alpha",
            "provider": "perforce",
            "scmRoot": str(tmp_path / "p4_workspace"),
            "paths": [],
            "targetPaths": ["rtl/"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"] == "no Perforce files selected to sync"
    assert "sync_called" not in seen


def test_scm_change_delete_route_uses_perforce_adapter(tmp_path: Path, monkeypatch):
    (tmp_path / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "p4_workspace").mkdir(parents=True, exist_ok=True)
    seen: dict[str, object] = {}

    class FakePerforceAdapter:
        provider = "perforce"

        def __init__(self, root: str) -> None:
            self.root = root

        def delete_pending_changelist(self, changelist: str, stream: str = ""):
            seen["changelist"] = changelist
            seen["stream"] = stream
            return SCMCommandResult(
                ok=True,
                provider=self.provider,
                root=self.root,
                stdout=f"Change {changelist} deleted.",
                returncode=0,
                command=("p4", "change", "-d", changelist),
            )

    def fake_resolve_scm_adapter(root: str, provider=None):
        seen["root"] = root
        seen["provider"] = provider
        return FakePerforceAdapter(root)

    monkeypatch.setattr("atlas_api_git.resolve_scm_adapter", fake_resolve_scm_adapter)
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))
    response = client.post(
        "/api/scm/change/delete",
        json={
            "ip": "alpha",
            "provider": "perforce",
            "scmRoot": str(tmp_path / "p4_workspace"),
            "stream": "//GOOD_SOC/GOOD_IP",
            "changelist": "12",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["stdout"] == "Change 12 deleted."
    assert seen == {
        "root": str(tmp_path / "p4_workspace"),
        "provider": "perforce",
        "changelist": "12",
        "stream": "//GOOD_SOC/GOOD_IP",
    }


def test_scm_change_delete_route_reports_unsupported_provider(tmp_path: Path, monkeypatch):
    (tmp_path / "alpha").mkdir(parents=True, exist_ok=True)
    _init_repo(tmp_path / "alpha")
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))
    response = client.post(
        "/api/scm/change/delete",
        json={"ip": "alpha", "changelist": "12"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert "not supported" in payload["error"]


def test_scm_uiprefs_roundtrip_persists_pane_locations(tmp_path: Path, monkeypatch):
    prefs_path = tmp_path / "home" / ".common_ai_agent" / "perforce_ui_state.json"
    monkeypatch.setenv("ATLAS_SCM_UI_PREFS_PATH", str(prefs_path))
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    empty = client.get("/api/scm/uiprefs?ip=alpha").json()
    assert empty == {"ok": True, "prefs": {}}

    saved = client.post(
        "/api/scm/uiprefs",
        json={
            "ip": "alpha",
            "localDir": "rtl",
            "depotDir": "//GOOD_SOC/GOOD_IP/alpha/rtl/",
            "stream": "//GOOD_SOC/GOOD_IP",
        },
    ).json()
    assert saved["ok"] is True

    restored = client.get("/api/scm/uiprefs?ip=alpha").json()
    assert restored["prefs"] == {
        "localDir": "rtl",
        "depotDir": "//GOOD_SOC/GOOD_IP/alpha/rtl/",
        "stream": "//GOOD_SOC/GOOD_IP",
    }
    assert prefs_path.exists()
    # other ips / owners do not see it
    assert client.get("/api/scm/uiprefs?ip=beta").json()["prefs"] == {}
    assert client.get("/api/scm/uiprefs?ip=alpha&session_id=other/sess/alpha/wf").json()["prefs"] == {}


def test_scm_uiprefs_sanitizes_keys_and_bounds_growth(tmp_path: Path, monkeypatch):
    import json as _json

    prefs_path = tmp_path / "home" / ".common_ai_agent" / "perforce_ui_state.json"
    monkeypatch.setenv("ATLAS_SCM_UI_PREFS_PATH", str(prefs_path))
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    # invalid ip names collapse into the shared default bucket (no key injection)
    weird = client.post(
        "/api/scm/uiprefs",
        json={"ip": "../../etc::evil\n", "localDir": "rtl"},
    ).json()
    assert weird["ok"] is True
    data = _json.loads(prefs_path.read_text(encoding="utf-8"))
    assert list(data.keys()) == ["default::default"]

    # oversized values are truncated
    client.post("/api/scm/uiprefs", json={"ip": "alpha", "localDir": "x" * 5000})
    got = client.get("/api/scm/uiprefs?ip=alpha").json()["prefs"]
    assert len(got["localDir"]) == 512

    # key growth is bounded at 200 (oldest evicted)
    for idx in range(205):
        client.post("/api/scm/uiprefs", json={"ip": f"bulk_{idx}", "localDir": "d"})
    data = _json.loads(prefs_path.read_text(encoding="utf-8"))
    assert len(data) == 200
    assert "default::bulk_204" in data
    assert "default::default" not in data  # oldest got evicted


def test_scm_submit_route_passes_selected_perforce_changelist(tmp_path: Path, monkeypatch):
    (tmp_path / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "p4_workspace").mkdir(parents=True, exist_ok=True)
    seen: dict[str, object] = {}

    class FakePerforceAdapter:
        provider = "perforce"

        def __init__(self, root: str) -> None:
            self.root = root

        def submit(self, message: str, *, add_all=True, stream="", changelist="", local_root=None, paths=None):
            seen["message"] = message
            seen["add_all"] = add_all
            seen["stream"] = stream
            seen["changelist"] = changelist
            seen["local_root"] = local_root
            seen["paths"] = list(paths or [])
            return SCMCommandResult(
                ok=True,
                provider=self.provider,
                root=self.root,
                stdout="submit ok",
                returncode=0,
                command=("p4", "submit"),
            )

    def fake_resolve_scm_adapter(root: str, provider=None):
        seen["root"] = root
        seen["provider"] = provider
        return FakePerforceAdapter(root)

    monkeypatch.setattr("atlas_api_git.resolve_scm_adapter", fake_resolve_scm_adapter)
    client = _authenticated_client(_create_app(tmp_path, monkeypatch))
    response = client.post(
        "/api/scm/submit",
        json={
            "ip": "alpha",
            "provider": "perforce",
            "scmRoot": str(tmp_path / "p4_workspace"),
            "stream": "//GOOD_SOC/GOOD_IP",
            "message": "submit selected pending",
            "add_all": False,
            "changelist": "12",
            "paths": ["//GOOD_SOC/GOOD_IP/rtl/opened.sv"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert seen == {
        "root": str(tmp_path / "p4_workspace"),
        "provider": "perforce",
        "message": "submit selected pending",
        "add_all": False,
        "stream": "//GOOD_SOC/GOOD_IP",
        "changelist": "12",
        "local_root": str(tmp_path / "alpha"),
        "paths": ["//GOOD_SOC/GOOD_IP/rtl/opened.sv"],
    }
