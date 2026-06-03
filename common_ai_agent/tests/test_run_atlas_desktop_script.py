from __future__ import annotations

import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_atlas_desktop.sh"
HARDCODED_ROOT = "/".join(("", "Users", "brian", "Desktop", "Project", "ROOT" + "_IP"))


def _run_dry(*args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "ATLAS_DESKTOP_DRY_RUN": "1",
    }
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def test_desktop_launcher_accepts_root_without_hardcoded_ip_parent(tmp_path: Path) -> None:
    project_root = tmp_path / "ip_parent"
    project_root.mkdir()

    result = _run_dry(
        "--root",
        str(project_root),
        "--ip",
        "NEWIP_MCTP",
        "--workflow",
        "default",
        "--session-id",
        "2076604",
        "--workspace-session",
        "default",
        "--scm-provider",
        "perforce",
    )

    assert result.returncode == 0, result.stdout
    assert HARDCODED_ROOT not in result.stdout
    assert f"--root {project_root}" in result.stdout
    assert "-ip NEWIP_MCTP" in result.stdout
    assert "--workflow default" in result.stdout
    assert "ATLAS_SCM_PROVIDER=perforce" in result.stdout
    assert "ip=NEWIP_MCTP" in result.stdout
    assert "workflow=default" in result.stdout
    assert "session_id=2076604" in result.stdout
    assert "workspace_session=default" in result.stdout
    assert "session=2076604%2Fdefault%2FNEWIP_MCTP%2Fdefault" in result.stdout
    assert "ATLAS_CONTEXT_KEY=2076604/default/NEWIP_MCTP/default" in result.stdout


def test_desktop_launcher_appends_ip_to_backend_url_query() -> None:
    result = _run_dry(
        "--backend-url",
        "http://127.0.0.1:4321/?existing=1",
        "--ip",
        "demo_ip",
    )

    assert result.returncode == 0, result.stdout
    assert "http://127.0.0.1:4321/?existing=1&ip=demo_ip" in result.stdout
    assert "workspace_session=default" in result.stdout


def test_desktop_launcher_defaults_root_to_home_atlas(tmp_path: Path) -> None:
    env_home = tmp_path / "home"
    env_home.mkdir()
    env = {
        **os.environ,
        "ATLAS_DESKTOP_DRY_RUN": "1",
        "HOME": str(env_home),
    }
    result = subprocess.run(
        ["bash", str(SCRIPT), "--ip", "NEWIP_MCTP", "--workflow", "default"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    default_root = env_home / "ATLAS"
    assert result.returncode == 0, result.stdout
    assert default_root.is_dir()
    assert f"--root {default_root}" in result.stdout
    assert f"ATLAS_ROOT={default_root}" in result.stdout
    assert "workspace_session=default" in result.stdout


def test_desktop_launcher_accepts_workspace_session_segment(tmp_path: Path) -> None:
    project_root = tmp_path / "atlas_root"
    project_root.mkdir()

    result = _run_dry(
        "--root",
        str(project_root),
        "--session-id",
        "alice",
        "--workspace-session",
        "s2",
        "--ip",
        "NEWIP_MCTP",
        "--workflow",
        "ssot-gen",
    )

    assert result.returncode == 0, result.stdout
    assert "session_id=alice" in result.stdout
    assert "workspace_session=s2" in result.stdout
    assert "session=alice%2Fs2%2FNEWIP_MCTP%2Fssot-gen" in result.stdout
    assert "ATLAS_CONTEXT_KEY=alice/s2/NEWIP_MCTP/ssot-gen" in result.stdout
