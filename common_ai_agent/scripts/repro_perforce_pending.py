"""Repro: Perforce Sync UI symptoms — pending-list pileup + checkout not updating depot.

Spins up a throwaway local p4d, seeds //depot/rtl/main.sv, then replays the
exact adapter calls the Perforce Sync tab makes (src/atlas_api_git.py →
core/scm_perforce.py) under realistic client states.

Run: python3 scripts/repro_perforce_pending.py
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from core.scm_perforce import PerforceP4Adapter  # noqa: E402

PASSWORD = "Password123"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> None:
    p4 = shutil.which("p4")
    p4d = shutil.which("p4d")
    assert p4 and p4d, "p4/p4d required"

    tmp = Path(tempfile.mkdtemp(prefix="p4repro_"))
    server_root = tmp / "p4d"
    client_root = tmp / "client"
    ip_root = tmp / "worktree_ip"
    for d in (server_root, client_root, ip_root):
        d.mkdir()

    port = free_port()
    proc = subprocess.Popen(
        [p4d, "-r", server_root.as_posix(), "-p", f"127.0.0.1:{port}",
         "-L", (tmp / "p4d.log").as_posix(), "-J", (tmp / "journal").as_posix()],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )

    env = {k: v for k, v in os.environ.items() if not k.startswith("P4")}
    env.update({
        "P4PORT": f"127.0.0.1:{port}",
        "P4USER": "atlas_pytest",
        "P4CLIENT": "atlas_ws",
        "P4PASSWD": PASSWORD,
        "P4TICKETS": (tmp / "tickets").as_posix(),
        "ATLAS_SCM_CLIENT_PERFORCE": "atlas_ws",
    })

    def run(*args: str, input_text: str = "", cwd: Path = client_root, use_env: dict | None = None):
        run_env = dict(use_env or env)
        run_env["PWD"] = cwd.as_posix()
        return subprocess.run([p4, *args], cwd=cwd, env=run_env,
                              input=input_text, capture_output=True, text=True, check=False)

    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.05)

        passwd_env = dict(env)
        passwd_env.pop("P4PASSWD")
        r = run("passwd", input_text=f"{PASSWORD}\n{PASSWORD}\n", cwd=tmp, use_env=passwd_env)
        assert r.returncode == 0, r.stderr
        r = run("login", input_text=f"{PASSWORD}\n", cwd=tmp)
        assert r.returncode == 0, r.stderr

        client_spec = (
            "Client:\tatlas_ws\nOwner:\tatlas_pytest\n"
            f"Root:\t{client_root.as_posix()}\n"
            "Options:\tnoallwrite clobber nocompress unlocked nomodtime normdir\n"
            "LineEnd:\tlocal\nView:\n\t//depot/... //atlas_ws/...\n"
        )
        r = run("client", "-i", input_text=client_spec, cwd=tmp)
        assert r.returncode == 0, r.stderr

        seed = client_root / "rtl" / "main.sv"
        seed.parent.mkdir(parents=True)
        seed.write_text("module seed; endmodule\n", encoding="utf-8")
        r = run("add", "rtl/main.sv")
        assert r.returncode == 0, f"add failed: {r.stdout} {r.stderr}"
        r = run("submit", "-d", "seed main")
        assert r.returncode == 0, f"submit failed: {r.stdout} {r.stderr}"

        # mirror fixture: adapter subprocesses inherit os.environ
        for key, value in env.items():
            if key.startswith("P4") or key.startswith("ATLAS_"):
                os.environ[key] = value

        adapter = PerforceP4Adapter(client_root, executable=p4)

        def show(label: str) -> None:
            opened = run("opened", "-a").stdout.strip() or "(nothing opened)"
            pend = run("changes", "-s", "pending", "-c", "atlas_ws").stdout.strip() or "(no pending CLs)"
            print(f"  {label} opened : {opened}")
            print(f"  {label} pendCL : {pend}")

        def unsync() -> None:
            r = run("sync", "//depot/rtl/main.sv#0")
            print(f"  [unsync have=0] rc={r.returncode} {r.stdout.strip()}{r.stderr.strip()}")

        banner = lambda s: print(f"\n=== {s} ===")

        # ---------------------------------------------------------------- R1
        banner("R1: UI 'Checkout' with depot files selected (sourceRoot=scm), client has NOT synced the file")
        unsync()
        res = adapter.edit_paths(["//depot/rtl/main.sv"])
        print(f"  edit_paths ok={res.ok} rc={res.returncode} stdout={res.stdout.strip()!r} err={res.error!r}")
        show("after")

        # ---------------------------------------------------------------- R2
        banner("R2: UI 'Checkout' local worktree file -> folder targetPaths=[//depot/rtl/] (depotDir), client not synced")
        src = ip_root / "rtl" / "main.sv"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("module edited_v2; endmodule\n", encoding="utf-8")
        res = adapter.edit_paths(["rtl/main.sv"], local_root=ip_root,
                                 target_paths=["//depot/rtl/"], changelist="default")
        print(f"  edit_paths ok={res.ok} rc={res.returncode} stdout={res.stdout.strip()!r} err={res.error!r}")
        show("after checkout")
        sub = adapter.submit("update main via checkout", add_all=False, changelist="default")
        print(f"  submit ok={sub.ok} rc={sub.returncode}\n    stdout={sub.stdout.strip()!r}\n    err={sub.error!r}")
        show("after submit")
        head = run("print", "-q", "//depot/rtl/main.sv").stdout.strip()
        print(f"  depot head content: {head!r}  (expected edited_v2)")

        # ---------------------------------------------------------------- R3
        banner("R3: user retries the same checkout+submit (does the pending list grow?)")
        res = adapter.edit_paths(["rtl/main.sv"], local_root=ip_root,
                                 target_paths=["//depot/rtl/"], changelist="default")
        print(f"  edit_paths ok={res.ok} err={res.error!r}")
        sub = adapter.submit("update main retry", add_all=False, changelist="default")
        print(f"  submit ok={sub.ok} err={sub.error!r} stdout={sub.stdout.strip()!r}")
        show("after retry")

        # ---------------------------------------------------------------- R4
        banner("R4: revert pending files — are emptied numbered CLs deleted?")
        pend_files = run("opened", "-a").stdout
        res = adapter.revert_paths(["//depot/rtl/main.sv"])
        print(f"  revert ok={res.ok} stdout={res.stdout.strip()!r}")
        show("after revert")

        # ---------------------------------------------------------------- R5
        banner("R5: control — file-style depot target (//depot/rtl/main.sv), client not synced (the tested path)")
        unsync()
        src.write_text("module edited_v3; endmodule\n", encoding="utf-8")
        res = adapter.edit_paths(["rtl/main.sv"], local_root=ip_root,
                                 target_paths=["//depot/rtl/main.sv"], changelist="default")
        print(f"  edit_paths ok={res.ok} err={res.error!r}")
        sub = adapter.submit("update main v3", add_all=False, changelist="default")
        print(f"  submit ok={sub.ok} err={sub.error!r}")
        head = run("print", "-q", "//depot/rtl/main.sv").stdout.strip()
        print(f"  depot head content: {head!r}  (expected edited_v3)")
        show("after R5")

    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(f"\n(server root kept at {tmp})")


if __name__ == "__main__":
    main()
