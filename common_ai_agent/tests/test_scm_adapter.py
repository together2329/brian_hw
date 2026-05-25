import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.scm import (  # noqa: E402
    GitSCMAdapter,
    PerforceSCMAdapter,
    configured_scm_provider,
    resolve_scm_adapter,
)


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=True,
    )


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "atlas@local")
    _run_git(path, "config", "user.name", "Atlas Test")


def test_git_scm_adapter_status_diff_log_submit_and_reset(tmp_path: Path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "design.txt").write_text("one\n", encoding="utf-8")
    _run_git(repo, "add", "design.txt")
    _run_git(repo, "commit", "-q", "-m", "initial")
    first_head = _run_git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "design.txt").write_text("two\n", encoding="utf-8")

    adapter = GitSCMAdapter(repo)

    status = adapter.status()
    assert status["ok"] is True
    assert status["provider"] == "git"
    assert status["branch"] == "main"
    assert status["dirty"] is True
    assert status["files"] == [
        {
            "path": "design.txt",
            "status": " M",
            "staged": False,
            "unstaged": True,
            "added": 1,
            "removed": 1,
        }
    ]

    diff = adapter.diff("design.txt")
    assert diff.ok is True
    assert "-one" in diff.stdout
    assert "+two" in diff.stdout

    commit = adapter.submit("change design", add_all=True)
    assert commit.ok is True, commit.to_dict()
    assert adapter.status()["dirty"] is False

    log = adapter.log(limit=5)
    assert log["ok"] is True
    assert log["commits"][0]["subject"] == "change design"
    assert log["commits"][0]["time"] > 0

    graph = adapter.graph(limit=5)
    assert graph["ok"] is True
    assert graph["commits"][0]["subject"] == "change design"

    reset = adapter.hard_reset(first_head)
    assert reset.ok is True, reset.to_dict()
    assert (repo / "design.txt").read_text(encoding="utf-8") == "one\n"


def test_resolve_scm_adapter_defaults_to_git_for_git_repo(tmp_path: Path):
    _init_repo(tmp_path)

    adapter = resolve_scm_adapter(tmp_path, provider="auto")

    assert adapter.provider == "git"
    assert adapter.detect().ok is True


def test_perforce_adapter_is_explicit_interface_until_implemented(tmp_path: Path):
    adapter = PerforceSCMAdapter(tmp_path)

    assert adapter.provider == "perforce"
    assert adapter.capabilities()["status"] is False
    status = adapter.status()
    assert status["ok"] is False
    assert "not implemented" in status["error"]


def test_forced_provider_and_env_normalization(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "p4")

    assert configured_scm_provider() == "perforce"
    assert resolve_scm_adapter(tmp_path).provider == "perforce"


def test_perforce_adapter_can_be_overridden_from_external_file(tmp_path: Path, monkeypatch):
    plugin = tmp_path / "custom_p4_adapter.py"
    plugin.write_text(
        """
from core.scm import SCMAdapter


class CustomPerforceAdapter(SCMAdapter):
    provider = "perforce"

    def capabilities(self):
        caps = super().capabilities()
        caps["status"] = True
        return caps

    def detect(self):
        return self._result(ok=True, stdout="custom p4")

    def status(self):
        return {
            "ok": True,
            "provider": self.provider,
            "root": str(self.root),
            "branch": "p4-client",
            "head": "12345",
            "head_full": "12345",
            "ahead": 0,
            "behind": 0,
            "dirty": True,
            "files": [{"path": "//depot/ip/foo.sv", "status": "edit"}],
        }
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    monkeypatch.setenv("ATLAS_SCM_ADAPTER_PERFORCE", f"{plugin}:CustomPerforceAdapter")

    adapter = resolve_scm_adapter(tmp_path)

    assert adapter.__class__.__name__ == "CustomPerforceAdapter"
    assert adapter.status()["files"][0]["path"] == "//depot/ip/foo.sv"


def test_auto_provider_uses_custom_perforce_adapter_when_git_is_absent(tmp_path: Path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin = plugin_dir / "custom_auto_p4.py"
    plugin.write_text(
        """
from core.scm import SCMAdapter


class AutoPerforceAdapter(SCMAdapter):
    provider = "perforce"

    def detect(self):
        return self._result(ok=True, stdout="detected")
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "auto")
    monkeypatch.setenv("ATLAS_SCM_PLUGIN_PATH", str(plugin_dir))
    monkeypatch.setenv("ATLAS_SCM_ADAPTER_PERFORCE", "custom_auto_p4:AutoPerforceAdapter")

    adapter = resolve_scm_adapter(tmp_path)

    assert adapter.__class__.__name__ == "AutoPerforceAdapter"
    assert adapter.provider == "perforce"


def test_bad_adapter_override_reports_configuration_error(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    monkeypatch.setenv("ATLAS_SCM_ADAPTER_PERFORCE", f"{tmp_path / 'missing.py'}:Nope")

    adapter = resolve_scm_adapter(tmp_path)
    status = adapter.status()

    assert adapter.provider == "perforce"
    assert status["ok"] is False
    assert "failed to load" in status["error"]
