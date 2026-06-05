import builtins
import importlib
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


def test_atlas_admin_module_import_does_not_import_fastapi(monkeypatch):
    sys.modules.pop("src.atlas_admin", None)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "fastapi":
            raise RuntimeError("fastapi import should be deferred")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = importlib.import_module("src.atlas_admin")

    assert module.__name__ == "src.atlas_admin"


def test_atlas_admin_dependency_bootstrap_checks_windows_user_site(monkeypatch, tmp_path):
    import src.atlas_admin as atlas_admin

    windows_version = f"Python{sys.version_info.major}{sys.version_info.minor}"
    appdata = tmp_path / "AppData" / "Roaming"
    user_site = appdata / "Python" / windows_version / "site-packages"
    user_site.mkdir(parents=True)
    monkeypatch.setenv("APPDATA", str(appdata))

    paths = atlas_admin._account_user_site_paths(tmp_path)

    assert user_site in paths


def test_create_admin_app_does_not_require_fastapi_request_reexport(monkeypatch):
    import fastapi
    import src.atlas_admin as atlas_admin

    monkeypatch.delattr(fastapi, "Request", raising=False)

    app = atlas_admin.create_admin_app(PROJECT_ROOT)

    assert app.title == "ATLAS Admin"


def test_runtime_admin_subprocess_uses_new_windows_process_group(monkeypatch):
    import src.atlas_runtime_run as atlas_runtime_run

    monkeypatch.setattr(atlas_runtime_run.os, "name", "nt")
    monkeypatch.setattr(
        atlas_runtime_run.subprocess,
        "CREATE_NEW_PROCESS_GROUP",
        512,
        raising=False,
    )

    kwargs = atlas_runtime_run._admin_subprocess_kwargs()

    assert kwargs["creationflags"] == 512
    assert "env" in kwargs


def test_atlas_admin_script_boots_when_home_changes():
    port = _free_port()
    env = os.environ.copy()

    with tempfile.TemporaryDirectory() as home:
        env["HOME"] = home
        env["ATLAS_DB_PATH"] = str(Path(home) / "atlas.db")
        proc = subprocess.Popen(
            [
                sys.executable,
                "src/atlas_admin.py",
                "--port",
                str(port),
                "--host",
                "127.0.0.1",
                "--root",
                str(PROJECT_ROOT),
            ],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.time() + 10
            body = ""
            last_error = ""
            while time.time() < deadline:
                if proc.poll() is not None:
                    stdout, stderr = proc.communicate(timeout=1)
                    raise AssertionError(
                        f"admin exited early rc={proc.returncode}\nstdout={stdout}\nstderr={stderr}"
                    )
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/healthz",
                        timeout=0.5,
                    ) as resp:
                        body = resp.read().decode("utf-8")
                        break
                except OSError as exc:
                    last_error = repr(exc)
                    time.sleep(0.2)
            assert '"ok":true' in body, last_error
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
