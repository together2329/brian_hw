import sys
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import tools


@pytest.mark.parametrize("subdir", sorted(tools._IP_SUBDIRS))
def test_write_file_all_ip_subdirs_use_atlas_project_root(tmp_path, monkeypatch, subdir):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    cwd_file = server_cwd / ip / subdir / "artifact.txt"
    target = project_root / ip / subdir / "artifact.txt"
    cwd_file.parent.mkdir(parents=True)
    cwd_file.write_text("stale cwd artifact\n", encoding="utf-8")

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    result = tools.write_file(path=f"{ip}/{subdir}/artifact.txt", content=f"{subdir} root scoped\n")

    assert str(target) in result
    assert target.read_text(encoding="utf-8") == f"{subdir} root scoped\n"
    assert cwd_file.read_text(encoding="utf-8") == "stale cwd artifact\n"


def test_write_file_ip_prefixed_path_uses_atlas_project_root(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    project_file = project_root / ip / "yaml" / f"{ip}.ssot.yaml"
    cwd_file = server_cwd / ip / "yaml" / f"{ip}.ssot.yaml"
    project_file.parent.mkdir(parents=True)
    cwd_file.parent.mkdir(parents=True)
    project_file.write_text("project draft\n", encoding="utf-8")
    cwd_file.write_text("stale cwd draft\n", encoding="utf-8")

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    result = tools.write_file(path=f"{ip}/yaml/{ip}.ssot.yaml", content="project updated\n")

    assert str(project_file) in result
    assert project_file.read_text(encoding="utf-8") == "project updated\n"
    assert cwd_file.read_text(encoding="utf-8") == "stale cwd draft\n"


def test_write_file_ip_subdir_path_uses_active_ip_under_atlas_project_root(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    cwd_file = server_cwd / "yaml" / f"{ip}.ssot.yaml"
    target = project_root / ip / "yaml" / f"{ip}.ssot.yaml"
    cwd_file.parent.mkdir(parents=True)
    cwd_file.write_text("wrong cwd file\n", encoding="utf-8")

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    result = tools.write_file(path=f"yaml/{ip}.ssot.yaml", content="root scoped\n")

    assert str(target) in result
    assert target.read_text(encoding="utf-8") == "root scoped\n"
    assert cwd_file.read_text(encoding="utf-8") == "wrong cwd file\n"


def test_write_file_unprefixed_ssot_yaml_infers_ip_under_project_root(tmp_path, monkeypatch):
    ip = "new_axi"
    project_root = tmp_path / "ROOT_IP"
    server_cwd = tmp_path / "common_ai_agent"
    cwd_file = server_cwd / "yaml" / f"{ip}.ssot.yaml"
    target = project_root / ip / "yaml" / f"{ip}.ssot.yaml"
    cwd_file.parent.mkdir(parents=True)
    cwd_file.write_text("wrong source-root yaml\n", encoding="utf-8")

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "default")
    monkeypatch.delenv("ATLAS_IP_ROOT", raising=False)
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    result = tools.write_file(path=f"yaml/{ip}.ssot.yaml", content="project root yaml\n")

    assert str(target) in result
    assert target.read_text(encoding="utf-8") == "project root yaml\n"
    assert cwd_file.read_text(encoding="utf-8") == "wrong source-root yaml\n"


def test_write_file_unprefixed_ssot_yaml_uses_ip_root_collection(tmp_path, monkeypatch):
    ip = "new_axi"
    project_root = tmp_path / "Project"
    ip_collection = project_root / "ROOT_IP"
    server_cwd = tmp_path / "common_ai_agent"
    cwd_file = server_cwd / "yaml" / f"{ip}.ssot.yaml"
    target = ip_collection / ip / "yaml" / f"{ip}.ssot.yaml"
    ip_collection.mkdir(parents=True)
    cwd_file.parent.mkdir(parents=True)
    cwd_file.write_text("wrong source-root yaml\n", encoding="utf-8")

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_IP_ROOT", str(ip_collection))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "default")
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    result = tools.write_file(path=f"yaml/{ip}.ssot.yaml", content="ip collection yaml\n")

    assert str(target) in result
    assert target.read_text(encoding="utf-8") == "ip collection yaml\n"
    assert cwd_file.read_text(encoding="utf-8") == "wrong source-root yaml\n"


def test_replace_tools_prefer_atlas_project_root_for_ip_paths(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    project_wiki = project_root / ip / "wiki" / "index.md"
    cwd_wiki = server_cwd / ip / "wiki" / "index.md"
    project_yaml = project_root / ip / "yaml" / f"{ip}.ssot.yaml"
    cwd_yaml = server_cwd / ip / "yaml" / f"{ip}.ssot.yaml"
    for path, text in (
        (project_wiki, "root wiki old\n"),
        (cwd_wiki, "cwd wiki old\n"),
        (project_yaml, "line 1\nline 2\nline 3\n"),
        (cwd_yaml, "cwd line 1\ncwd line 2\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    result = tools.replace_in_file(
        path=f"{ip}/wiki/index.md",
        old_text="root wiki old",
        new_text="root wiki new",
    )
    assert str(project_wiki) in result
    assert project_wiki.read_text(encoding="utf-8") == "root wiki new\n"
    assert cwd_wiki.read_text(encoding="utf-8") == "cwd wiki old\n"

    result = tools.replace_lines(
        path=f"{ip}/yaml/{ip}.ssot.yaml",
        start_line=2,
        end_line=2,
        new_content="line two replaced",
    )
    assert str(project_yaml) in result
    assert project_yaml.read_text(encoding="utf-8") == "line 1\nline two replaced\nline 3\n"
    assert cwd_yaml.read_text(encoding="utf-8") == "cwd line 1\ncwd line 2\n"


def test_file_tools_accept_backslash_ip_paths(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    target = project_root / ip / "rtl" / "block.sv"
    (server_cwd / ip).mkdir(parents=True)

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    tool_path = rf"{ip}\rtl\block.sv"
    result = tools.write_file(path=tool_path, content="alpha\nbeta\n")
    assert str(target) in result
    assert target.read_text(encoding="utf-8") == "alpha\nbeta\n"

    assert "alpha" in tools.read_file(path=tool_path)
    assert "block.sv" in tools.list_dir(path=rf"{ip}\rtl")
    assert "alpha" in tools.grep_file(pattern="alpha", path=tool_path, context_lines=0)
    assert "beta" in tools.read_lines(path=tool_path, start_line=2, end_line=2)
    assert "block.sv" in tools.find_files(pattern="*.sv", directory=rf"{ip}\rtl")

    result = tools.replace_in_file(path=tool_path, old_text="beta", new_text="gamma")
    assert str(target) in result
    assert target.read_text(encoding="utf-8") == "alpha\ngamma\n"

    result = tools.replace_lines(path=tool_path, start_line=1, end_line=1, new_content="delta")
    assert str(target) in result
    assert target.read_text(encoding="utf-8") == "delta\ngamma\n"


def test_non_ip_file_tools_normalize_backslash_relative_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("PROJECT_ROOT", raising=False)
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)
    monkeypatch.setattr(tools, "_git_auto_commit", lambda *args, **kwargs: None)

    result = tools.write_file(path=r"notes\artifact.txt", content="local text\n")

    target = tmp_path / "notes" / "artifact.txt"
    assert "notes/artifact.txt" in result
    assert target.read_text(encoding="utf-8") == "local text\n"
    assert not (tmp_path / r"notes\artifact.txt").exists()
    assert "local text" in tools.read_file(path=r"notes\artifact.txt")
    assert "artifact.txt" in tools.list_dir(path=r"notes")


def test_run_command_runs_inside_active_ip_under_atlas_project_root(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    (project_root / ip).mkdir(parents=True)
    (server_cwd / ip).mkdir(parents=True)

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)

    result = tools.run_command("pwd", timeout=5)

    assert result == str(project_root / ip)


def test_run_command_cd_active_ip_runs_from_atlas_project_root(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    (project_root / ip).mkdir(parents=True)
    (server_cwd / ip).mkdir(parents=True)

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)

    result = tools.run_command(f"cd {ip} && pwd", timeout=5)

    assert result == str(project_root / ip)


def test_run_command_detects_backslash_ip_path_prefix(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    (project_root / ip / "rtl").mkdir(parents=True)
    (server_cwd / ip).mkdir(parents=True)

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)

    result = tools.run_command(
        f'"{sys.executable}" -c "import os; print(os.getcwd())" # {ip}\\rtl\\top.sv',
        timeout=5,
    )

    assert Path(result).resolve() == project_root.resolve()


def test_run_command_falls_back_to_atlas_project_root_without_active_ip_dir(tmp_path, monkeypatch):
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    project_root.mkdir(parents=True)
    server_cwd.mkdir(parents=True)

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "missing_ip")

    result = tools.run_command("pwd", timeout=5)

    assert result == str(project_root)


def _setup_active_ip_git_repo(tmp_path, monkeypatch):
    ip = "uart_core"
    project_root = tmp_path / "served_root"
    server_cwd = tmp_path / "common_ai_agent"
    ip_root = project_root / ip
    source_file = ip_root / "rtl" / "top.sv"
    source_file.parent.mkdir(parents=True)
    server_cwd.mkdir(parents=True)

    subprocess.run(["git", "init", "-q"], cwd=ip_root, check=True)
    subprocess.run(["git", "config", "user.email", "atlas@example.local"], cwd=ip_root, check=True)
    subprocess.run(["git", "config", "user.name", "Atlas Test"], cwd=ip_root, check=True)
    source_file.write_text("module old_top;\nendmodule\n", encoding="utf-8")
    subprocess.run(["git", "add", "rtl/top.sv"], cwd=ip_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=ip_root, check=True)
    source_file.write_text("module new_top;\nendmodule\n", encoding="utf-8")

    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
    return ip


def test_git_status_runs_inside_active_ip_repo(tmp_path, monkeypatch):
    _setup_active_ip_git_repo(tmp_path, monkeypatch)

    result = tools.git_status()

    assert "Git status:" in result
    assert "rtl/top.sv" in result
    assert "not a git repository" not in result.lower()


def test_git_diff_runs_inside_active_ip_repo(tmp_path, monkeypatch):
    _setup_active_ip_git_repo(tmp_path, monkeypatch)

    result = tools.git_diff()

    assert "-module old_top;" in result
    assert "+module new_top;" in result
    assert "not a git repository" not in result.lower()


def test_git_diff_accepts_active_ip_backslash_path(tmp_path, monkeypatch):
    ip = _setup_active_ip_git_repo(tmp_path, monkeypatch)

    result = tools.git_diff(rf"{ip}\rtl\top.sv")

    assert "-module old_top;" in result
    assert "+module new_top;" in result
    assert "not a git repository" not in result.lower()
