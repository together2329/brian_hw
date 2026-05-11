import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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
    assert status["files"] == [
        {"path": "foo.txt", "status": " M", "staged": False, "unstaged": True, "added": 1, "removed": 1}
    ]

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

    push = client.post("/api/git/push", json={"ip": "alpha"}).json()
    assert push["branch"] == "ipbranch"
    assert push["ip"] == "alpha"


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
