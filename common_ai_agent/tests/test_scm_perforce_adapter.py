"""Tests for the deployment Perforce adapter (core/scm_perforce.py).

The override-loading tests run anywhere. The live tests talk to a local Helix
Core server and are skipped unless `p4 info` succeeds against a configured
workspace (see scripts/perforce_setup.sh).
"""
import os
import re
import shutil
import socket
import subprocess
import sys
import time
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
        if not a.detect().ok or a._client_root() is None:
            return False
        return a._soften(a._run_p4("opened", a._workspace_scope(), timeout=5)).ok
    except Exception:
        return False


p4_required = pytest.mark.skipif(not _p4_ready(), reason="no reachable/configured p4 workspace")

P4_TEST_PASSWORD = "Password123"
ATLAS_TEST_CLIENT_ENV_VARS = (
    "ATLAS_SCM_CLIENT_PERFORCE",
    "ATLAS_PERFORCE_CLIENT",
    "ATLAS_P4CLIENT",
)


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_p4d(port: int, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=1)
            pytest.fail(f"p4d exited early\nstdout={stdout}\nstderr={stderr}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    pytest.fail("p4d did not accept TCP connections in time")


def _run_live_p4(
    p4: str,
    env: dict[str, str],
    cwd: Path,
    *args: str,
    input_text: str = "",
) -> subprocess.CompletedProcess[str]:
    run_env = dict(env)
    run_env["PWD"] = cwd.as_posix()
    return subprocess.run(
        [p4, *args],
        cwd=cwd,
        env=run_env,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def local_p4d(monkeypatch, tmp_path):
    p4 = shutil.which("p4")
    p4d = shutil.which("p4d")
    if p4 is None or p4d is None:
        pytest.skip("p4 and p4d are required for the local Helix Core integration test")

    server_root = tmp_path / "p4d"
    client_root = tmp_path / "client"
    ip_root = tmp_path / "worktree_ip"
    server_root.mkdir()
    client_root.mkdir()
    ip_root.mkdir()

    port = _free_tcp_port()
    process = subprocess.Popen(
        [
            p4d,
            "-r", server_root.as_posix(),
            "-p", f"127.0.0.1:{port}",
            "-L", (tmp_path / "p4d.log").as_posix(),
            "-J", (tmp_path / "journal").as_posix(),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    env = {key: value for key, value in os.environ.items() if not key.startswith("P4")}
    env.update({
        "P4PORT": f"127.0.0.1:{port}",
        "P4USER": "atlas_pytest",
        "P4CLIENT": "atlas_ws",
        "P4PASSWD": P4_TEST_PASSWORD,
        "P4TICKETS": (tmp_path / "tickets").as_posix(),
        "ATLAS_SCM_CLIENT_PERFORCE": "atlas_ws",
        "ATLAS_PERFORCE_CLIENT": "atlas_ws",
        "ATLAS_P4CLIENT": "atlas_ws",
    })

    try:
        _wait_for_p4d(port, process)
        passwd_env = dict(env)
        passwd_env.pop("P4PASSWD", None)
        password = _run_live_p4(
            p4,
            passwd_env,
            tmp_path,
            "passwd",
            input_text=f"{P4_TEST_PASSWORD}\n{P4_TEST_PASSWORD}\n",
        )
        assert password.returncode == 0, password.stderr or password.stdout
        login = _run_live_p4(p4, env, tmp_path, "login", input_text=f"{P4_TEST_PASSWORD}\n")
        assert login.returncode == 0, login.stderr or login.stdout

        client_spec = (
            "Client:\tatlas_ws\n"
            "Owner:\tatlas_pytest\n"
            f"Root:\t{client_root.as_posix()}\n"
            "Options:\tnoallwrite noclobber nocompress unlocked nomodtime normdir\n"
            "LineEnd:\tlocal\n"
            "View:\n"
            "\t//depot/... //atlas_ws/...\n"
        )
        client = _run_live_p4(p4, env, tmp_path, "client", "-i", input_text=client_spec)
        assert client.returncode == 0, client.stderr or client.stdout

        seed = client_root / "rtl" / "main.sv"
        seed.parent.mkdir(parents=True)
        seed.write_text("module seed; endmodule\n", encoding="utf-8")
        add = _run_live_p4(p4, env, client_root, "add", "rtl/main.sv")
        assert add.returncode == 0, add.stderr or add.stdout
        submit = _run_live_p4(p4, env, client_root, "submit", "-d", "seed main")
        assert submit.returncode == 0, submit.stderr or submit.stdout

        for key in list(os.environ):
            if key.startswith("P4") or key in ATLAS_TEST_CLIENT_ENV_VARS:
                monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            if key.startswith("P4") or key in ATLAS_TEST_CLIENT_ENV_VARS:
                monkeypatch.setenv(key, value)

        yield {
            "p4": p4,
            "env": env,
            "client_root": client_root,
            "ip_root": ip_root,
        }
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)


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


def test_env_client_override_adds_p4_client_arg(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_SCM_CLIENT_PERFORCE", "atlas_env_client")

    result = PerforceP4Adapter(tmp_path, executable="__missing_p4__")._run_p4("info")

    assert result.command == (
        "__missing_p4__",
        "-c",
        "atlas_env_client",
        "-d",
        str(tmp_path.resolve()),
        "info",
    )


def test_p4client_env_override_beats_selected_stream_client(monkeypatch, tmp_path):
    monkeypatch.delenv("ATLAS_SCM_CLIENT_PERFORCE", raising=False)
    monkeypatch.delenv("ATLAS_PERFORCE_CLIENT", raising=False)
    monkeypatch.delenv("ATLAS_P4CLIENT", raising=False)
    monkeypatch.setenv("P4CLIENT", "atlas_env_client")
    adapter = PerforceP4Adapter(tmp_path, executable="__missing_p4__")
    adapter._select_stream("//GOOD_SOC/GOOD_IP_DEV")

    result = adapter._run_p4("info")

    assert result.command == (
        "__missing_p4__",
        "-c",
        "atlas_env_client",
        "-d",
        str(tmp_path.resolve()),
        "info",
    )


def test_configured_client_reads_override_from_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("ATLAS_SCM_CLIENT_PERFORCE", raising=False)
    monkeypatch.delenv("ATLAS_PERFORCE_CLIENT", raising=False)
    monkeypatch.delenv("ATLAS_P4CLIENT", raising=False)
    monkeypatch.delenv("P4CLIENT", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ATLAS_P4CLIENT=atlas_dotenv_client\n", encoding="utf-8")
    adapter = PerforceP4Adapter(tmp_path, executable="__missing_p4__")
    adapter._select_stream("//GOOD_SOC/GOOD_IP_DEV")

    result = adapter._run_p4("info")

    assert result.command == (
        "__missing_p4__",
        "-c",
        "atlas_dotenv_client",
        "-d",
        str(tmp_path.resolve()),
        "info",
    )


def test_process_env_client_override_beats_dotenv_client(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_SCM_CLIENT_PERFORCE", "atlas_env_client")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ATLAS_P4CLIENT=atlas_dotenv_client\n", encoding="utf-8")

    result = PerforceP4Adapter(tmp_path, executable="__missing_p4__")._run_p4("info")

    assert result.command == (
        "__missing_p4__",
        "-c",
        "atlas_env_client",
        "-d",
        str(tmp_path.resolve()),
        "info",
    )


def test_perforce_sync_ui_reselects_opened_changelist_after_mutation():
    source = (Path(PROJECT_ROOT) / "frontend" / "atlas" / "perforce-sync.tsx").read_text(
        encoding="utf-8",
    )

    assert "selectOpenedChange?: boolean" in source
    assert "preferPendingPaths?: string[]" in source
    assert "nextPendingChangeSelection(current, nextPane, options.preferPendingPaths)" in source
    assert "{ selectOpenedChange: true }" in source
    assert "paneWithPendingChangeOptions(d)" in source


def test_perforce_sync_ui_submit_debug_context_contract():
    source = (Path(PROJECT_ROOT) / "frontend" / "atlas" / "perforce-sync.tsx").read_text(
        encoding="utf-8",
    )

    assert "Submit blocked before request" in source
    assert "Submit failed." in source
    assert "selected CL:" in source
    assert "files in selected CL:" in source
    assert "returncode:" in source
    assert "stderr:" in source


def test_safe_filespecs_rejects_escapes(tmp_path):
    a = PerforceP4Adapter(tmp_path)
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    specs = a._safe_filespecs(["a.txt", "../../etc/passwd", "/abs/escape"])
    # only the in-root relative path survives
    assert specs == [(tmp_path / "a.txt").resolve().as_posix()]


def test_safe_filespecs_preserves_literal_client_root(tmp_path):
    actual_root = tmp_path / "actual_workspace"
    client_root = tmp_path / "client_workspace"
    actual_root.mkdir()
    os.symlink(actual_root, client_root)
    (client_root / "a.txt").write_text("x", encoding="utf-8")

    class ClientRootAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientRoot": client_root.as_posix()}

    adapter = ClientRootAdapter(client_root)

    assert adapter.root == actual_root.resolve()
    assert adapter._safe_filespecs(["a.txt"]) == [(client_root / "a.txt").as_posix()]


def test_safe_filespecs_accepts_client_and_depot_specs_for_same_ip(tmp_path):
    ip_root = tmp_path / "dma_prompt_ip"
    (ip_root / "req").mkdir(parents=True)
    (ip_root / "req" / "a.txt").write_text("x", encoding="utf-8")

    adapter = PerforceP4Adapter(ip_root)
    specs = adapter._safe_filespecs([
        "//atlas_GOOD_IP/dma_prompt_ip/req/a.txt",
        "//GOOD_SOC/GOOD_IP/dma_prompt_ip/req/a.txt",
    ])

    expected = (ip_root / "req" / "a.txt").resolve().as_posix()
    assert specs == [expected, expected]


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

        def _info(self) -> dict[str, str]:
            return {}

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


def test_sync_state_lists_local_disk_files_when_p4_has_no_records(tmp_path):
    (tmp_path / "rtl").mkdir()
    (tmp_path / "rtl" / "brian_dma.sv").write_text("module brian_dma; endmodule\n", encoding="utf-8")

    class EmptyPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return ""

        def _run_p4(self, *args: str, timeout: int = 60):
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            return [], self._result(ok=True)

    state = EmptyPaneAdapter(tmp_path).sync_state(local_dir="rtl")

    assert state["ok"] is True
    assert state["local"] == [{"path": "rtl/brian_dma.sv", "state": "new", "kind": "file"}]


def test_sync_state_reports_p4_lookup_errors_instead_of_silent_empty_panes(tmp_path):
    (tmp_path / "rtl").mkdir()
    (tmp_path / "rtl" / "brian_dma.sv").write_text("module brian_dma; endmodule\n", encoding="utf-8")

    class ExpiredSessionAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return ""

        def _run_p4(self, *args: str, timeout: int = 60):
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            return [], self._result(
                ok=False,
                stderr="Your session has expired, please login again.",
                error="Your session has expired, please login again.",
                returncode=1,
            )

    state = ExpiredSessionAdapter(tmp_path).sync_state(local_dir="rtl")

    assert state["ok"] is False
    assert "session has expired" in state["error"]
    assert state["local"] == [{"path": "rtl/brian_dma.sv", "state": "new", "kind": "file"}]


def test_sync_state_accepts_selected_stream_and_lists_available_streams(tmp_path):
    class StreamPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {
                "clientName": self._client_for_stream(self._selected_stream),
                "clientStream": self._selected_stream,
            }

        def _latest_change(self) -> str:
            return ""

        def _run_p4(self, *args: str, timeout: int = 60):
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "streams":
                return [
                    {"Stream": "//GOOD_SOC/GOOD_IP"},
                    {"Stream": "//GOOD_SOC/GOOD_IP_DEV"},
                ], self._result(ok=True)
            return [], self._result(ok=True)

    state = StreamPaneAdapter(tmp_path).sync_state(stream="//GOOD_SOC/GOOD_IP_DEV")

    assert state["stream"] == "//GOOD_SOC/GOOD_IP_DEV"
    assert state["client"] == "atlas_GOOD_IP_DEV"
    assert state["streams"] == ["//GOOD_SOC/GOOD_IP", "//GOOD_SOC/GOOD_IP_DEV"]


def test_sync_state_keeps_local_root_and_depot_scope_independent(tmp_path):
    local_root = tmp_path / "dma_prompt_ip"
    (local_root / "req").mkdir(parents=True)
    (local_root / "req" / "local_only.txt").write_text("x", encoding="utf-8")
    depot_client_file = tmp_path / "perforce_checkout" / "shared" / "remote_only.txt"

    class SplitPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return "7"

        def _run_p4(self, *args: str, timeout: int = 60):
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [
                    {
                        "depotFile": "//GOOD_SOC/GOOD_IP/shared/remote_only.txt",
                        "clientFile": depot_client_file.as_posix(),
                        "headRev": "3",
                        "headAction": "edit",
                    },
                ], self._result(ok=True)
            return [], self._result(ok=True)

    state = SplitPaneAdapter(local_root).sync_state()

    assert state["ok"] is True
    assert state["local"] == [{"path": "req", "state": "", "kind": "folder"}]
    assert state["depot"] == [{"path": "//GOOD_SOC/GOOD_IP/shared/remote_only.txt", "rev": "3", "kind": "file"}]


def test_sync_state_browses_only_current_directories(tmp_path):
    local_root = tmp_path / "local_ip"
    (local_root / "rtl").mkdir(parents=True)
    (local_root / "rtl" / "nested.sv").write_text("module nested; endmodule\n", encoding="utf-8")
    (local_root / "top.sv").write_text("module top; endmodule\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    class ScopedPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return "7"

        def _run_p4(self, *args: str, timeout: int = 60):
            calls.append(args)
            if args and args[0] == "dirs":
                return self._result(ok=True, stdout="//GOOD_SOC/GOOD_IP/rtl\n")
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            calls.append(args)
            if args and args[0] == "fstat":
                return [
                    {
                        "depotFile": "//GOOD_SOC/GOOD_IP/top.sv",
                        "headRev": "3",
                        "headAction": "edit",
                    },
                ], self._result(ok=True)
            return [], self._result(ok=True)

    state = ScopedPaneAdapter(tmp_path / "p4_workspace").sync_state(
        stream="//GOOD_SOC/GOOD_IP",
        local_root=local_root,
    )

    assert state["ok"] is True
    assert state["local"] == [
        {"path": "rtl", "state": "", "kind": "folder"},
        {"path": "top.sv", "state": "new", "kind": "file"},
    ]
    assert state["depot"] == [
        {"path": "//GOOD_SOC/GOOD_IP/rtl/", "rev": "", "kind": "folder"},
        {"path": "//GOOD_SOC/GOOD_IP/top.sv", "rev": "3", "kind": "file"},
    ]
    assert ("dirs", "//GOOD_SOC/GOOD_IP/*") in calls
    assert any(call[-1] == "//GOOD_SOC/GOOD_IP/*" for call in calls if call and call[0] == "fstat")
    assert not any(call[-1] == "//GOOD_SOC/GOOD_IP/..." for call in calls if call and call[0] == "fstat")
    assert not any(row["path"] == "rtl/nested.sv" for row in state["local"])


def test_sync_state_clamps_depot_dir_to_selected_stream(tmp_path):
    calls: list[tuple[str, ...]] = []

    class ScopedPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return "7"

        def _run_p4(self, *args: str, timeout: int = 60):
            calls.append(args)
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            calls.append(args)
            return [], self._result(ok=True)

    state = ScopedPaneAdapter(tmp_path).sync_state(
        stream="//GOOD_SOC/GOOD_IP",
        depot_dir="//OTHER_DEPOT/OTHER_IP/rtl/...",
    )

    assert state["ok"] is True
    assert state["depotDir"] == "//GOOD_SOC/GOOD_IP/"
    assert ("dirs", "//GOOD_SOC/GOOD_IP/*") in calls
    assert not any("//OTHER_DEPOT" in part for call in calls for part in call)


def test_sync_state_lists_split_root_visible_local_path_without_missing_projection(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "shared").mkdir(parents=True)
    (p4_root / "shared").mkdir(parents=True)
    (local_root / "shared" / "remote_only.txt").write_text("x", encoding="utf-8")
    depot_client_file = p4_root / "shared" / "remote_only.txt"
    depot_client_file.write_text("x", encoding="utf-8")

    class SplitPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return "7"

        def _run_p4(self, *args: str, timeout: int = 60):
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [
                    {
                        "depotFile": "//GOOD_SOC/GOOD_IP/shared/remote_only.txt",
                        "clientFile": depot_client_file.as_posix(),
                        "headRev": "3",
                        "headAction": "edit",
                        "haveRev": "3",
                    },
                ], self._result(ok=True)
            return [], self._result(ok=True)

    state = SplitPaneAdapter(p4_root).sync_state(
        local_root=local_root,
        local_dir="shared",
        depot_dir="//GOOD_SOC/GOOD_IP/shared/",
    )

    assert state["ok"] is True
    assert state["local"] == [{"path": "shared/remote_only.txt", "state": "new", "kind": "file"}]
    assert state["depot"] == [
        {"path": "//GOOD_SOC/GOOD_IP/shared/remote_only.txt", "rev": "3", "kind": "file"},
    ]


def test_sync_state_does_not_mark_split_root_absent_depot_files_missing(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "rtl").mkdir(parents=True)
    (p4_root / "rtl").mkdir(parents=True)
    (local_root / "rtl" / "edited.sv").write_text("module edited_local; endmodule\n", encoding="utf-8")
    (p4_root / "rtl" / "edited.sv").write_text("module edited_depot; endmodule\n", encoding="utf-8")
    (p4_root / "rtl" / "deleted.sv").write_text("module deleted; endmodule\n", encoding="utf-8")

    class SplitPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return "7"

        def _run_p4(self, *args: str, timeout: int = 60):
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [
                    {
                        "depotFile": "//GOOD_SOC/GOOD_IP/rtl/deleted.sv",
                        "clientFile": (p4_root / "rtl" / "deleted.sv").as_posix(),
                        "headRev": "3",
                        "headAction": "edit",
                        "haveRev": "3",
                    },
                    {
                        "depotFile": "//GOOD_SOC/GOOD_IP/rtl/edited.sv",
                        "clientFile": (p4_root / "rtl" / "edited.sv").as_posix(),
                        "headRev": "3",
                        "headAction": "edit",
                        "haveRev": "3",
                    },
                ], self._result(ok=True)
            return [], self._result(ok=True)

    state = SplitPaneAdapter(p4_root).sync_state(
        local_root=local_root,
        local_dir="rtl",
        depot_dir="//GOOD_SOC/GOOD_IP/rtl/",
    )

    assert state["ok"] is True
    assert state["local"] == [{"path": "rtl/edited.sv", "state": "new", "kind": "file"}]
    assert all(row.get("state") != "missing" for row in state["local"])


def test_sync_state_does_not_project_split_root_depot_files_as_missing(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    local_root.mkdir()
    p4_root.mkdir()

    class SplitPaneAdapter(PerforceP4Adapter):
        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _latest_change(self) -> str:
            return "7"

        def _run_p4(self, *args: str, timeout: int = 60):
            if args and args[0] == "dirs":
                return self._result(ok=True)
            return self._result(ok=True)

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [
                    {
                        "depotFile": f"//GOOD_SOC/GOOD_IP/rtl/missing_{idx}.sv",
                        "clientFile": (p4_root / "rtl" / f"missing_{idx}.sv").as_posix(),
                        "headRev": "3",
                        "headAction": "edit",
                        "haveRev": "3",
                    }
                    for idx in range(50)
                ], self._result(ok=True)
            return [], self._result(ok=True)

    state = SplitPaneAdapter(p4_root).sync_state(
        stream="//GOOD_SOC/GOOD_IP",
        local_root=local_root,
        depot_dir="//GOOD_SOC/GOOD_IP/rtl/",
    )

    assert state["ok"] is True
    assert state["local"] == []
    assert all(row.get("state") != "missing" for row in state["local"])
    assert len(state["depot"]) == 50


def test_sync_paths_copies_depot_filespecs_into_local_root(tmp_path):
    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="synced")

    ip_root = tmp_path / "dma_prompt_ip"
    p4_root = tmp_path / "perforce_workspace"
    p4_root.mkdir()
    adapter = RecordingAdapter(p4_root)

    result = adapter.sync_paths([
        "//GOOD_SOC/GOOD_IP/shared/remote_only.txt",
        "//GOOD_SOC/GOOD_IP/dma_prompt_ip/req/main_note.txt",
    ], local_root=ip_root)

    assert result.ok is True
    assert adapter.calls == [
        (
            "print", "-q", "-o",
            (ip_root / "shared" / "remote_only.txt").as_posix(),
            "//GOOD_SOC/GOOD_IP/shared/remote_only.txt",
        ),
        (
            "print", "-q", "-o",
            (ip_root / "req" / "main_note.txt").as_posix(),
            "//GOOD_SOC/GOOD_IP/dma_prompt_ip/req/main_note.txt",
        ),
    ]


def test_sync_paths_does_not_reuse_single_target_for_multiple_depot_files(tmp_path):
    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="synced")

    ip_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    p4_root.mkdir()
    adapter = RecordingAdapter(p4_root)

    result = adapter.sync_paths(
        [
            "//GOOD_SOC/GOOD_IP/rtl/a.sv",
            "//GOOD_SOC/GOOD_IP/rtl/b.sv",
        ],
        local_root=ip_root,
        target_paths=["rtl/selected_target.sv"],
    )

    assert result.ok is True
    assert adapter.calls == [
        (
            "print", "-q", "-o",
            (ip_root / "rtl" / "selected_target.sv").as_posix(),
            "//GOOD_SOC/GOOD_IP/rtl/a.sv",
        ),
        (
            "print", "-q", "-o",
            (ip_root / "rtl" / "b.sv").as_posix(),
            "//GOOD_SOC/GOOD_IP/rtl/b.sv",
        ),
    ]


def test_sync_paths_reuses_single_folder_target_for_multiple_depot_files(tmp_path):
    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="synced")

    ip_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    p4_root.mkdir()
    adapter = RecordingAdapter(p4_root)

    result = adapter.sync_paths(
        [
            "//GOOD_SOC/GOOD_IP/rtl/a.sv",
            "//GOOD_SOC/GOOD_IP/rtl/b.sv",
        ],
        local_root=ip_root,
        target_paths=["synced/"],
    )

    assert result.ok is True
    assert adapter.calls == [
        (
            "print", "-q", "-o",
            (ip_root / "synced" / "a.sv").as_posix(),
            "//GOOD_SOC/GOOD_IP/rtl/a.sv",
        ),
        (
            "print", "-q", "-o",
            (ip_root / "synced" / "b.sv").as_posix(),
            "//GOOD_SOC/GOOD_IP/rtl/b.sv",
        ),
    ]


def test_open_paths_copies_local_file_to_perforce_target(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "rtl").mkdir(parents=True)
    p4_root.mkdir()
    (local_root / "rtl" / "mapped.sv").write_text("module mapped; endmodule\n", encoding="utf-8")

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [{"clientFile": (p4_root / "rtl" / "target.sv").as_posix()}], self._result(ok=True)
            return [], self._result(ok=True)

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.open_paths(
        ["rtl/mapped.sv"],
        local_root=local_root,
        target_paths=["//GOOD_SOC/GOOD_IP/rtl/target.sv"],
    )

    assert result.ok is True
    assert (p4_root / "rtl" / "target.sv").read_text(encoding="utf-8") == "module mapped; endmodule\n"
    assert adapter.calls == [("reconcile", (p4_root / "rtl" / "target.sv").as_posix())]


def test_open_paths_maps_selected_depot_folder_target(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "src").mkdir(parents=True)
    p4_root.mkdir()
    (local_root / "src" / "mapped.sv").write_text("module mapped; endmodule\n", encoding="utf-8")

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _info(self) -> dict[str, str]:
            return {"clientRoot": p4_root.as_posix()}

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.open_paths(
        ["src/mapped.sv"],
        local_root=local_root,
        target_paths=["//GOOD_SOC/GOOD_IP/rtl/"],
    )

    assert result.ok is True
    assert (p4_root / "rtl" / "mapped.sv").read_text(encoding="utf-8") == "module mapped; endmodule\n"
    assert adapter.calls == [("reconcile", (p4_root / "rtl" / "mapped.sv").as_posix())]


def test_open_paths_stream_root_folder_target_mirrors_ip_subpath(tmp_path):
    # REQ_PLAT_SCM_PERFORCE_SYNC_001 / OBL_P4_STREAM_ROOT_TARGET_MAPS_IP.
    # The UI's default Add/Checkout target is the depot pane's current folder,
    # which starts at the STREAM ROOT. That used to resolve to rel="" -> None
    # -> "cannot map local paths to Perforce target paths", so nothing was ever
    # opened and submit reported "no changes to submit".
    local_root = tmp_path / "my_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "rtl").mkdir(parents=True)
    p4_root.mkdir()
    (local_root / "rtl" / "main.sv").write_text("module mapped; endmodule\n", encoding="utf-8")

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _info(self) -> dict[str, str]:
            return {"clientRoot": p4_root.as_posix()}

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.open_paths(
        ["rtl/main.sv"],
        stream="//GOOD_SOC/GOOD_IP",
        local_root=local_root,
        target_paths=["//GOOD_SOC/GOOD_IP/"],
    )

    target = p4_root / "my_ip" / "rtl" / "main.sv"
    assert result.ok is True, result.error
    assert target.read_text(encoding="utf-8") == "module mapped; endmodule\n"
    assert adapter.calls == [("reconcile", target.as_posix())]


def test_open_paths_does_not_reuse_single_file_target_for_multiple_sources(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "src").mkdir(parents=True)
    p4_root.mkdir()
    (local_root / "src" / "first.sv").write_text("module first; endmodule\n", encoding="utf-8")
    (local_root / "src" / "second.sv").write_text("module second; endmodule\n", encoding="utf-8")

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _info(self) -> dict[str, str]:
            return {"clientRoot": p4_root.as_posix()}

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [{"clientFile": (p4_root / "rtl" / "target.sv").as_posix()}], self._result(ok=True)
            return [], self._result(ok=True)

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.open_paths(
        ["src/first.sv", "src/second.sv"],
        local_root=local_root,
        target_paths=["//GOOD_SOC/GOOD_IP/rtl/target.sv"],
    )

    assert result.ok is True
    assert (p4_root / "rtl" / "target.sv").read_text(encoding="utf-8") == "module first; endmodule\n"
    assert (p4_root / "src" / "second.sv").read_text(encoding="utf-8") == "module second; endmodule\n"
    assert adapter.calls == [
        ("reconcile", (p4_root / "rtl" / "target.sv").as_posix(), (p4_root / "src" / "second.sv").as_posix()),
    ]


def test_open_paths_moves_opened_files_to_selected_pending_changelist(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "rtl").mkdir(parents=True)
    p4_root.mkdir()
    (local_root / "rtl" / "mapped.sv").write_text("module mapped; endmodule\n", encoding="utf-8")

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _info(self) -> dict[str, str]:
            return {"clientRoot": p4_root.as_posix()}

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.open_paths(
        ["rtl/mapped.sv"],
        local_root=local_root,
        changelist="12",
    )

    target = p4_root / "rtl" / "mapped.sv"
    assert result.ok is True
    assert adapter.calls == [
        ("reconcile", target.as_posix()),
        ("reopen", "-c", "12", target.as_posix()),
    ]


def test_pending_changes_list_is_client_wide_so_empty_changelists_are_selectable(tmp_path):
    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _info(self) -> dict[str, str]:
            return {"clientName": "atlas_GOOD_IP", "clientStream": "//GOOD_SOC/GOOD_IP"}

        def _records(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return [
                {"change": "12", "desc": "CU selected pending changelist"},
            ], self._result(ok=True)

    adapter = RecordingAdapter(tmp_path)

    changes, result = adapter._pending_changes()

    assert result.ok is True
    assert changes == [
        {"id": "default", "label": "default", "description": ""},
        {
            "id": "12",
            "label": "12 CU selected pending changelist",
            "description": "CU selected pending changelist",
        },
    ]
    assert adapter.calls == [("changes", "-s", "pending", "-c", "atlas_GOOD_IP")]


def test_edit_paths_checks_out_depot_file_to_selected_pending_changelist(tmp_path):
    p4_root = tmp_path / "perforce_workspace"
    p4_root.mkdir()

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.edit_paths(["//GOOD_SOC/GOOD_IP/rtl/main.sv"], changelist="12")

    assert result.ok is True
    assert adapter.calls == [
        ("edit", "//GOOD_SOC/GOOD_IP/rtl/main.sv"),
        ("reopen", "-c", "12", "//GOOD_SOC/GOOD_IP/rtl/main.sv"),
    ]


def test_submit_numbered_changelist_updates_description_before_submit(tmp_path):
    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []
            self.input_texts: list[str] = []

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "opened":
                return [
                    {"depotFile": "//GOOD_SOC/GOOD_IP/rtl/opened.sv", "action": "edit", "change": "12"},
                ], self._result(ok=True)
            return [], self._result(ok=True)

        def _run_p4(self, *args: str, timeout: int = 60, input_text: str = ""):
            self.calls.append(args)
            self.input_texts.append(input_text)
            if args == ("change", "-o", "12"):
                return self._result(
                    ok=True,
                    stdout=(
                        "Change:\t12\n"
                        "Client:\tatlas_GOOD_IP\n\n"
                        "Description:\n"
                        "\told description\n\n"
                        "Files:\n"
                        "\t//GOOD_SOC/GOOD_IP/rtl/opened.sv\n"
                    ),
                )
            if args == ("change", "-i"):
                return self._result(ok=True, stdout="Change 12 updated.")
            if args == ("submit", "-c", "12"):
                return self._result(ok=True, stdout="Change 12 submitted.")
            return self._result(ok=True)

    adapter = RecordingAdapter(tmp_path)

    result = adapter.submit("ship checkout fix", add_all=False, changelist="12")

    assert result.ok is True
    assert adapter.calls == [
        ("change", "-o", "12"),
        ("change", "-i"),
        ("submit", "-c", "12"),
    ]
    assert "Description:\n\tship checkout fix\n" in adapter.input_texts[1]
    assert "\told description" not in adapter.input_texts[1]


def test_live_local_p4d_checkout_copy_submit_roundtrip(local_p4d):
    # Given: a real local p4d server has //depot/rtl/main.sv submitted.
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    ip_root = local_p4d["ip_root"]
    source = ip_root / "rtl" / "main.sv"
    source.parent.mkdir(parents=True)
    source.write_text("module edited; endmodule\n", encoding="utf-8")
    adapter = PerforceP4Adapter(client_root, executable=p4)
    assert adapter._configured_client() == "atlas_ws"

    # When: the UI-style checkout maps the local worktree file to a Perforce target and submits it.
    opened = adapter.edit_paths(
        ["rtl/main.sv"],
        local_root=ip_root,
        target_paths=["//depot/rtl/main.sv"],
        changelist="default",
    )
    assert opened.ok, opened.error or opened.stderr
    pending = _run_live_p4(p4, env, client_root, "opened", "-a")
    assert "//depot/rtl/main.sv" in pending.stdout

    submitted = adapter.submit("checkout edit submit", add_all=False, changelist="default")

    # Then: the pending file is cleared and the submitted depot content matches the local edit.
    assert submitted.ok, submitted.error or submitted.stderr
    after = _run_live_p4(p4, env, client_root, "opened", "-a")
    assert "//depot/rtl/main.sv" not in after.stdout
    printed = _run_live_p4(p4, env, client_root, "print", "-q", "//depot/rtl/main.sv")
    assert printed.returncode == 0, printed.stderr or printed.stdout
    assert "module edited; endmodule" in printed.stdout


def test_live_local_p4d_submit_restages_split_local_workspace_edit(local_p4d):
    # Given: local IP files live outside the Perforce client root. Checkout
    # opens/copies the current local file, then the user edits the local file
    # again before pressing Submit.
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    ip_root = local_p4d["ip_root"]
    source = ip_root / "rtl" / "main.sv"
    source.parent.mkdir(parents=True)
    source.write_text("module first_checkout_copy; endmodule\n", encoding="utf-8")
    adapter = PerforceP4Adapter(client_root, executable=p4)
    assert adapter._configured_client() == "atlas_ws"

    opened = adapter.edit_paths(
        ["rtl/main.sv"],
        local_root=ip_root,
        target_paths=["//depot/rtl/main.sv"],
        changelist="default",
    )
    assert opened.ok, opened.error or opened.stderr
    assert (client_root / "rtl" / "main.sv").read_text(encoding="utf-8") == "module first_checkout_copy; endmodule\n"
    source.write_text("module edited_after_checkout; endmodule\n", encoding="utf-8")
    assert (client_root / "rtl" / "main.sv").read_text(encoding="utf-8") == "module first_checkout_copy; endmodule\n"

    submitted = adapter.submit(
        "split local workspace submit",
        add_all=False,
        changelist="default",
        local_root=ip_root,
        paths=["//depot/rtl/main.sv"],
    )

    assert submitted.ok, submitted.error or submitted.stderr
    assert "restaged local edit: //depot/rtl/main.sv" in submitted.stdout
    printed = _run_live_p4(p4, env, client_root, "print", "-q", "//depot/rtl/main.sv")
    assert printed.returncode == 0, printed.stderr or printed.stdout
    assert "module edited_after_checkout; endmodule" in printed.stdout


def test_live_local_p4d_numbered_checkout_submit_clears_pending(local_p4d):
    # Given: a numbered pending changelist on a real local p4d server.
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    ip_root = local_p4d["ip_root"]
    change_form = (
        "Change:\tnew\n"
        "Client:\tatlas_ws\n"
        "User:\tatlas_pytest\n"
        "Status:\tnew\n"
        "Description:\n"
        "\tnumbered checkout submit\n"
    )
    change = _run_live_p4(p4, env, client_root, "change", "-i", input_text=change_form)
    assert change.returncode == 0, change.stderr or change.stdout
    match = re.search(r"Change (\d+) created", change.stdout)
    assert match is not None, change.stdout
    change_id = match.group(1)
    source = ip_root / "rtl" / "main.sv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("module numbered_checkout_copy; endmodule\n", encoding="utf-8")
    adapter = PerforceP4Adapter(client_root, executable=p4)
    assert adapter._configured_client() == "atlas_ws"

    # When: the local edit is checked out into the selected changelist and submitted.
    opened = adapter.edit_paths(
        ["rtl/main.sv"],
        local_root=ip_root,
        target_paths=["//depot/rtl/main.sv"],
        changelist=change_id,
    )
    assert opened.ok, opened.error or opened.stderr
    assert (client_root / "rtl" / "main.sv").read_text(encoding="utf-8") == "module numbered_checkout_copy; endmodule\n"
    source.write_text("module numbered_after_checkout; endmodule\n", encoding="utf-8")
    assert (client_root / "rtl" / "main.sv").read_text(encoding="utf-8") == "module numbered_checkout_copy; endmodule\n"
    submitted = adapter.submit(
        "numbered checkout submit",
        add_all=False,
        changelist=change_id,
        local_root=ip_root,
        paths=["//depot/rtl/main.sv"],
    )

    # Then: the selected changelist leaves the pending list and depot receives the edit.
    assert submitted.ok, submitted.error or submitted.stderr
    assert "restaged local edit: //depot/rtl/main.sv" in submitted.stdout
    pending_changes = _run_live_p4(p4, env, client_root, "changes", "-s", "pending", "-c", "atlas_ws")
    assert f"Change {change_id} " not in pending_changes.stdout
    printed = _run_live_p4(p4, env, client_root, "print", "-q", "//depot/rtl/main.sv")
    assert "module numbered_after_checkout; endmodule" in printed.stdout


def test_live_checkout_folder_target_unsynced_opens_edit_and_submits(local_p4d):
    # REQ_PLAT_SCM_PERFORCE_SYNC_001 / OBL_P4_CHECKOUT_OPENS_EXISTING_AS_EDIT.
    # UI default gesture: local files + folder targetPaths=[depotDir/]. With the
    # client at have=0 this used to open the existing depot file for ADD and the
    # submit died with "add of added file; must revert".
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    ip_root = local_p4d["ip_root"]
    unsync = _run_live_p4(p4, env, client_root, "sync", "//depot/rtl/main.sv#0")
    assert unsync.returncode == 0, unsync.stderr
    source = ip_root / "rtl" / "main.sv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("module folder_target_edit; endmodule\n", encoding="utf-8")
    adapter = PerforceP4Adapter(client_root, executable=p4)

    opened = adapter.edit_paths(
        ["rtl/main.sv"],
        local_root=ip_root,
        target_paths=["//depot/rtl/"],
        changelist="default",
    )
    assert opened.ok, opened.error or opened.stderr
    pending = _run_live_p4(p4, env, client_root, "opened", "-a")
    assert "//depot/rtl/main.sv#1 - edit" in pending.stdout, pending.stdout

    submitted = adapter.submit("folder target checkout", add_all=False, changelist="default")
    assert submitted.ok, submitted.error or submitted.stderr
    printed = _run_live_p4(p4, env, client_root, "print", "-q", "//depot/rtl/main.sv")
    assert "module folder_target_edit; endmodule" in printed.stdout
    leftovers = _run_live_p4(p4, env, client_root, "changes", "-s", "pending", "-c", "atlas_ws")
    assert leftovers.stdout.strip() == "", leftovers.stdout


def test_live_depot_selection_checkout_unsynced_opens_for_edit(local_p4d):
    # REQ_PLAT_SCM_PERFORCE_SYNC_001 / OBL_P4_EDIT_FAILURE_NOT_SOFTENED.
    # `p4 edit` of an unsynced depot file only warns "file(s) not on client."
    # (sometimes with rc=0); the softened result used to fake a successful
    # checkout that opened nothing.
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    unsync = _run_live_p4(p4, env, client_root, "sync", "//depot/rtl/main.sv#0")
    assert unsync.returncode == 0, unsync.stderr
    adapter = PerforceP4Adapter(client_root, executable=p4)

    opened = adapter.edit_paths(["//depot/rtl/main.sv"])

    assert opened.ok, opened.error or opened.stderr
    pending = _run_live_p4(p4, env, client_root, "opened", "-a")
    assert "//depot/rtl/main.sv#1 - edit" in pending.stdout, pending.stdout
    assert (client_root / "rtl" / "main.sv").exists()


def test_live_failed_default_submit_strands_no_numbered_changelist(local_p4d):
    # REQ_PLAT_SCM_PERFORCE_SYNC_001 / OBL_P4_SUBMIT_FAIL_NO_STRANDED_CL.
    # A failed filespec submit moves default-changelist files into a fresh
    # numbered changelist; the adapter must move them back and delete the shell.
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    unsync = _run_live_p4(p4, env, client_root, "sync", "//depot/rtl/main.sv#0")
    assert unsync.returncode == 0, unsync.stderr
    stale = client_root / "rtl" / "main.sv"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("module conflicting_add; endmodule\n", encoding="utf-8")
    recon = _run_live_p4(p4, env, client_root, "reconcile", "rtl/main.sv")
    assert "opened for add" in (recon.stdout + recon.stderr), recon.stdout + recon.stderr
    adapter = PerforceP4Adapter(client_root, executable=p4)

    submitted = adapter.submit("conflicting add", add_all=False, changelist="default")

    assert not submitted.ok
    leftovers = _run_live_p4(p4, env, client_root, "changes", "-s", "pending", "-c", "atlas_ws")
    assert leftovers.stdout.strip() == "", leftovers.stdout
    reopened = _run_live_p4(p4, env, client_root, "opened", "-a")
    assert "default change" in reopened.stdout, reopened.stdout


def test_live_delete_pending_changelist_keeps_workspace_content(local_p4d):
    # REQ_PLAT_SCM_PERFORCE_SYNC_001 / OBL_P4_PENDING_CL_DELETABLE (explicit delete).
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    ip_root = local_p4d["ip_root"]
    change_form = (
        "Change:\tnew\n"
        "Client:\tatlas_ws\n"
        "User:\tatlas_pytest\n"
        "Status:\tnew\n"
        "Description:\n"
        "\tjunk changelist\n"
    )
    change = _run_live_p4(p4, env, client_root, "change", "-i", input_text=change_form)
    assert change.returncode == 0, change.stderr
    match = re.search(r"Change (\d+) created", change.stdout)
    assert match is not None, change.stdout
    change_id = match.group(1)
    source = ip_root / "rtl" / "main.sv"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("module keep_me; endmodule\n", encoding="utf-8")
    adapter = PerforceP4Adapter(client_root, executable=p4)
    opened = adapter.edit_paths(
        ["rtl/main.sv"],
        local_root=ip_root,
        target_paths=["//depot/rtl/main.sv"],
        changelist=change_id,
    )
    assert opened.ok, opened.error or opened.stderr

    deleted = adapter.delete_pending_changelist(change_id)

    assert deleted.ok, deleted.error or deleted.stderr
    leftovers = _run_live_p4(p4, env, client_root, "changes", "-s", "pending", "-c", "atlas_ws")
    assert f"Change {change_id} " not in leftovers.stdout
    still_open = _run_live_p4(p4, env, client_root, "opened", "-a")
    assert "//depot/rtl/main.sv" not in still_open.stdout
    # revert -k: deleting the junk changelist must not clobber workspace content
    assert (client_root / "rtl" / "main.sv").read_text(encoding="utf-8") == "module keep_me; endmodule\n"


def test_live_revert_paths_deletes_emptied_numbered_changelist(local_p4d):
    # REQ_PLAT_SCM_PERFORCE_SYNC_001 / OBL_P4_PENDING_CL_DELETABLE (revert path).
    p4 = local_p4d["p4"]
    env = local_p4d["env"]
    client_root = local_p4d["client_root"]
    change_form = (
        "Change:\tnew\n"
        "Client:\tatlas_ws\n"
        "User:\tatlas_pytest\n"
        "Status:\tnew\n"
        "Description:\n"
        "\trevert sweep\n"
    )
    change = _run_live_p4(p4, env, client_root, "change", "-i", input_text=change_form)
    match = re.search(r"Change (\d+) created", change.stdout)
    assert match is not None, change.stdout
    change_id = match.group(1)
    edit = _run_live_p4(p4, env, client_root, "edit", "-c", change_id, "//depot/rtl/main.sv")
    assert edit.returncode == 0, edit.stderr
    adapter = PerforceP4Adapter(client_root, executable=p4)

    reverted = adapter.revert_paths(["//depot/rtl/main.sv"])

    assert reverted.ok, reverted.error or reverted.stderr
    leftovers = _run_live_p4(p4, env, client_root, "changes", "-s", "pending", "-c", "atlas_ws")
    assert f"Change {change_id} " not in leftovers.stdout, leftovers.stdout


def test_delete_pending_changelist_requires_numbered_id(tmp_path):
    adapter = PerforceP4Adapter(tmp_path)
    for bogus in ("", "default", "abc"):
        result = adapter.delete_pending_changelist(bogus)
        assert result.ok is False
        assert "numbered" in result.error


def test_diff_accepts_pending_depot_file_path(tmp_path):
    p4_root = tmp_path / "perforce_workspace"
    p4_root.mkdir()

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            return self._result(ok=True, stdout="--- depot\n+++ client\n")

    adapter = RecordingAdapter(p4_root)

    result = adapter.diff("//GOOD_SOC/GOOD_IP/rtl/main.sv")

    assert result.ok is True
    assert result.stdout == "--- depot\n+++ client\n"
    assert adapter.calls == [("diff", "-du", "//GOOD_SOC/GOOD_IP/rtl/main.sv")]


def test_edit_paths_opens_existing_target_before_copy(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "rtl").mkdir(parents=True)
    (p4_root / "rtl").mkdir(parents=True)
    source = local_root / "rtl" / "mapped.sv"
    target = p4_root / "rtl" / "target.sv"
    source.write_text("module mapped; endmodule\n", encoding="utf-8")
    target.write_text("module old; endmodule\n", encoding="utf-8")
    os.chmod(target, 0o444)

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _info(self) -> dict[str, str]:
            return {"clientRoot": p4_root.as_posix()}

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [{
                    "clientFile": target.as_posix(),
                    "depotFile": "//GOOD_SOC/GOOD_IP/rtl/target.sv",
                    "headAction": "edit",
                    "haveRev": "1",
                }], self._result(ok=True)
            return [], self._result(ok=True)

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            if args and args[0] == "edit":
                os.chmod(args[1], 0o644)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.edit_paths(
        ["rtl/mapped.sv"],
        local_root=local_root,
        target_paths=["//GOOD_SOC/GOOD_IP/rtl/target.sv"],
    )

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "module mapped; endmodule\n"
    assert adapter.calls == [
        ("edit", target.as_posix()),
    ]


def test_edit_paths_syncs_missing_depot_target_before_copy(tmp_path):
    local_root = tmp_path / "local_ip"
    p4_root = tmp_path / "perforce_workspace"
    (local_root / "rtl").mkdir(parents=True)
    (p4_root / "rtl").mkdir(parents=True)
    source = local_root / "rtl" / "mapped.sv"
    target = p4_root / "rtl" / "target.sv"
    source.write_text("module mapped; endmodule\n", encoding="utf-8")

    class RecordingAdapter(PerforceP4Adapter):
        def __init__(self, root: Union[str, Path], executable: str = "p4") -> None:
            super().__init__(root, executable=executable)
            self.calls: list[tuple[str, ...]] = []

        def _info(self) -> dict[str, str]:
            return {"clientRoot": p4_root.as_posix()}

        def _records(self, *args: str, timeout: int = 60):
            if args and args[0] == "fstat":
                return [{
                    "clientFile": target.as_posix(),
                    "depotFile": "//GOOD_SOC/GOOD_IP/rtl/target.sv",
                    "headAction": "edit",
                    "haveRev": "0",
                }], self._result(ok=True)
            return [], self._result(ok=True)

        def _run_p4(self, *args: str, timeout: int = 60):
            self.calls.append(args)
            if args[:2] == ("sync", "-f"):
                target.write_text("module old; endmodule\n", encoding="utf-8")
                os.chmod(target, 0o444)
            if args and args[0] == "edit":
                os.chmod(args[1], 0o644)
            return self._result(ok=True, stdout="opened")

    adapter = RecordingAdapter(p4_root)

    result = adapter.edit_paths(
        ["rtl/mapped.sv"],
        local_root=local_root,
        target_paths=["//GOOD_SOC/GOOD_IP/rtl/target.sv"],
        changelist="12",
    )

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "module mapped; endmodule\n"
    assert adapter.calls == [
        ("sync", "-f", "//GOOD_SOC/GOOD_IP/rtl/target.sv"),
        ("edit", target.as_posix()),
        ("reopen", "-c", "12", target.as_posix()),
    ]


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
        a._run_p4("revert", a._workspace_scope())
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
