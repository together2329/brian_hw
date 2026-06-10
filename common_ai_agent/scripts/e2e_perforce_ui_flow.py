"""E2E: real p4d + real ATLAS app, driving the exact Perforce Sync UI calls.

Mirrors the dev topology (stream depot GOOD_SOC, stream //GOOD_SOC/GOOD_IP,
client atlas_GOOD_IP) on a throwaway local p4d, then walks the UI gestures
through the actual HTTP routes (src/atlas_api_git.py) the way
frontend/atlas/perforce-sync.tsx sends them:

  pane -> +Add -> Submit -> Checkout(edit) -> click pending file (diff)
       -> Submit -> Sync(depot->local) -> Delete CL

Run: python3 scripts/e2e_perforce_ui_flow.py
"""
from __future__ import annotations

import json
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

PASSWORD = "Password123"
IP_NAME = "e2e_ip"
STREAM = "//GOOD_SOC/GOOD_IP"
FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(f"{label}: {detail}")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> None:
    p4 = shutil.which("p4")
    p4d = shutil.which("p4d")
    assert p4 and p4d, "p4/p4d required"

    tmp = Path(tempfile.mkdtemp(prefix="p4e2e_"))
    server_root = tmp / "p4d"
    ws_root = tmp / "perforce_ws"      # Perforce client workspace (scm root)
    project = tmp / "project"          # ATLAS project root (local IP roots)
    ip_root = project / IP_NAME
    for d in (server_root, ws_root, (ip_root / "rtl")):
        d.mkdir(parents=True)

    port = free_port()
    proc = subprocess.Popen(
        [p4d, "-r", server_root.as_posix(), "-p", f"127.0.0.1:{port}",
         "-L", (tmp / "p4d.log").as_posix(), "-J", (tmp / "journal").as_posix()],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )

    base_env = {k: v for k, v in os.environ.items() if not k.startswith("P4")}
    p4env = {
        "P4PORT": f"127.0.0.1:{port}",
        "P4USER": "brian",
        "P4CLIENT": "atlas_GOOD_IP",
        "P4PASSWD": PASSWORD,
        "P4TICKETS": (tmp / "tickets").as_posix(),
    }
    env = {**base_env, **p4env}

    def run(*args: str, input_text: str = "", cwd: Path = ws_root, use_env: dict | None = None):
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

        # --- stream depot + mainline stream + stream client (dev topology) ---
        depot_form = (
            "Depot:\tGOOD_SOC\n"
            "Owner:\tbrian\n"
            "Description:\n\te2e stream depot\n"
            "Type:\tstream\n"
            "StreamDepth:\t//GOOD_SOC/1\n"
            "Map:\tGOOD_SOC/...\n"
        )
        r = run("depot", "-i", input_text=depot_form, cwd=tmp)
        assert r.returncode == 0, r.stderr or r.stdout
        stream_form = (
            f"Stream:\t{STREAM}\n"
            "Owner:\tbrian\n"
            "Name:\tGOOD_IP\n"
            "Parent:\tnone\n"
            "Type:\tmainline\n"
            "ParentView:\tinherit\n"
            "Description:\n\te2e mainline\n"
            "Options:\tallsubmit unlocked notoparent nofromparent mergedown\n"
            "Paths:\n\tshare ...\n"
        )
        r = run("stream", "-i", input_text=stream_form, cwd=tmp)
        assert r.returncode == 0, r.stderr or r.stdout
        client_form = (
            "Client:\tatlas_GOOD_IP\n"
            "Owner:\tbrian\n"
            f"Root:\t{ws_root.as_posix()}\n"
            "Options:\tnoallwrite clobber nocompress unlocked nomodtime normdir\n"
            "LineEnd:\tlocal\n"
            f"Stream:\t{STREAM}\n"
        )
        r = run("client", "-i", input_text=client_form, cwd=tmp)
        assert r.returncode == 0, r.stderr or r.stdout

        # --- ATLAS app over the perforce adapter (same env contract as .env) ---
        os.environ.update(p4env)
        (tmp / "home").mkdir(exist_ok=True)
        os.environ.update({
            "HOME": (tmp / "home").as_posix(),
            # This E2E exercises SCM adapter routing, not tenant authz — run
            # single-user so the per-IP authz gate (covered by
            # tests/test_atlas_authz_e2e.py) allows the throwaway IP.
            "ATLAS_MULTI_USER": "0",
            "ATLAS_COOKIE_SECRET": "e2e-secret",
            "ATLAS_SCM_PROVIDER": "perforce",
            "ATLAS_SCM_ADAPTER_PERFORCE": "core.scm_perforce:PerforceP4Adapter",
            "ATLAS_SCM_ROOT_PERFORCE": ws_root.as_posix(),
            "ATLAS_SCM_CLIENT_PERFORCE": "atlas_GOOD_IP",
        })
        from fastapi.testclient import TestClient
        from src import atlas_ui
        atlas_ui.PROJECT_ROOT = project
        client = TestClient(atlas_ui.create_app())
        reg = client.post("/api/auth/register", json={"username": "e2e", "password": "pw"})
        if reg.status_code != 200:
            reg = client.post("/api/auth/login", json={"username": "e2e", "password": "pw"})
        assert reg.status_code == 200, reg.text

        (ip_root / "rtl" / "main.sv").write_text("module v1; endmodule\n", encoding="utf-8")

        def pane(local_dir: str = "", depot_dir: str = "") -> dict:
            params = f"ip={IP_NAME}&provider=perforce"
            if local_dir:
                params += f"&local_dir={local_dir}"
            if depot_dir:
                params += f"&depot_dir={depot_dir}"
            resp = client.get(f"/api/scm/pane?{params}")
            assert resp.status_code == 200, resp.text
            return resp.json()

        def post(url: str, body: dict) -> dict:
            payload = {"ip": IP_NAME, "provider": "perforce", **body}
            resp = client.post(url, json=payload)
            assert resp.status_code == 200, f"{url}: {resp.text}"
            return resp.json()

        print("\n=== 1. pane (initial) ===")
        state = pane()
        stream = state.get("stream", "")
        depot_dir = state.get("depotDir") or (f"{stream}/" if stream else "")
        check("pane ok", state.get("ok") is True, json.dumps(state)[:300])
        check("stream detected", stream == STREAM, stream)
        local_paths = {row.get("path") for row in state.get("local", [])}
        check("local pane lists IP file/folder", bool(local_paths), str(local_paths))

        print("\n=== 2. + Add (UI gesture: local file, folder target=depotDir) ===")
        add = post("/api/scm/add", {
            "paths": ["rtl/main.sv"], "targetPaths": [depot_dir],
            "stream": stream, "changelist": "default",
        })
        check("add ok", add.get("ok") is True, add.get("error", ""))
        state = pane()
        pend = state.get("pending", [])
        check("pending shows 1 opened file", len(pend) == 1, json.dumps(pend))
        pend_path = pend[0]["path"] if pend else ""
        print(f"  pending[0] = {pend[0] if pend else None}")

        print("\n=== 3. Submit (add) ===")
        sub = post("/api/scm/submit", {
            "message": "e2e add", "add_all": False,
            "stream": stream, "changelist": "default",
        })
        check("submit ok", sub.get("ok") is True, sub.get("error", "") + sub.get("stderr", ""))
        files = run("files", f"{STREAM}/...")
        print(f"  depot files: {files.stdout.strip()}")
        expected_depot = f"{STREAM}/{IP_NAME}/rtl/main.sv"
        check("1:1 depot mapping <stream>/<ip>/rtl/main.sv", expected_depot in files.stdout, files.stdout)
        state = pane()
        check("pending empty after submit", not state.get("pending"), json.dumps(state.get("pending")))
        check("pendingChanges only default", [c["id"] for c in state.get("pendingChanges", [])] == ["default"],
              json.dumps(state.get("pendingChanges")))

        print("\n=== 4. Checkout (UI gesture: local file -> folder target), edit v2 ===")
        (ip_root / "rtl" / "main.sv").write_text("module v2; endmodule\n", encoding="utf-8")
        edit = post("/api/scm/edit", {
            "paths": ["rtl/main.sv"], "targetPaths": [depot_dir],
            "stream": stream, "changelist": "default",
        })
        check("checkout ok", edit.get("ok") is True, edit.get("error", ""))
        opened = run("opened", "-a")
        print(f"  p4 opened: {opened.stdout.strip() or '(nothing)'}")
        check("opened for edit (not add)", " - edit " in opened.stdout, opened.stdout)

        print("\n=== 5. click pending file -> diff ===")
        state = pane()
        pend = state.get("pending", [])
        pend_path = pend[0]["path"] if pend else ""
        check("pending row present for diff click", bool(pend_path), json.dumps(pend))
        resp = client.get(f"/api/scm/diff?ip={IP_NAME}&provider=perforce&stream={stream}&path={pend_path}")
        diff = resp.json()
        diff_text = str(diff.get("diff", ""))
        check("diff ok", resp.status_code == 200 and not diff.get("error"), json.dumps(diff)[:300])
        check("diff shows the v1->v2 change", "v2" in diff_text and "v1" in diff_text, diff_text[:300])
        print("  diff first lines: " + " | ".join(diff_text.splitlines()[:4]))

        print("\n=== 6. Submit (edit) ===")
        sub = post("/api/scm/submit", {
            "message": "e2e edit v2", "add_all": False,
            "stream": stream, "changelist": "default",
        })
        check("submit ok", sub.get("ok") is True, sub.get("error", "") + sub.get("stderr", ""))
        printed = run("print", "-q", expected_depot)
        check("depot head is v2", "module v2" in printed.stdout, printed.stdout)
        state = pane()
        check("pending empty after submit", not state.get("pending"), json.dumps(state.get("pending")))
        check("no junk pending changelists", [c["id"] for c in state.get("pendingChanges", [])] == ["default"],
              json.dumps(state.get("pendingChanges")))

        print("\n=== 7. Sync (depot -> local IP root) ===")
        # depot moves ahead (v3 submitted directly in the workspace)
        ws_file = ws_root / IP_NAME / "rtl" / "main.sv"
        r = run("edit", expected_depot)
        assert r.returncode == 0, r.stderr
        ws_file.write_text("module v3; endmodule\n", encoding="utf-8")
        r = run("submit", "-d", "v3 direct")
        assert r.returncode == 0, r.stderr or r.stdout
        syn = post("/api/scm/sync", {
            "paths": [expected_depot], "targetPaths": [], "stream": stream,
        })
        check("sync ok", syn.get("ok") is True, syn.get("error", ""))
        local_now = (ip_root / "rtl" / "main.sv").read_text(encoding="utf-8")
        check("local IP file updated to v3", "module v3" in local_now, local_now)

        print("\n=== 8. Delete CL (junk numbered changelist) ===")
        change_form = (
            "Change:\tnew\nClient:\tatlas_GOOD_IP\nUser:\tbrian\nStatus:\tnew\n"
            "Description:\n\tjunk e2e CL\n"
        )
        r = run("change", "-i", input_text=change_form)
        assert r.returncode == 0, r.stderr
        change_id = r.stdout.split()[1]
        state = pane()
        check("junk CL visible in pendingChanges", change_id in [c["id"] for c in state.get("pendingChanges", [])],
              json.dumps(state.get("pendingChanges")))
        deleted = post("/api/scm/change/delete", {"changelist": change_id, "stream": stream})
        check("delete CL ok", deleted.get("ok") is True, deleted.get("error", ""))
        state = pane()
        check("junk CL gone", change_id not in [c["id"] for c in state.get("pendingChanges", [])],
              json.dumps(state.get("pendingChanges")))

        print("\n" + ("=" * 60))
        if FAILURES:
            print(f"E2E RESULT: {len(FAILURES)} FAILURE(S)")
            for f in FAILURES:
                print(f"  - {f}")
            sys.exit(1)
        print("E2E RESULT: ALL PASS")
    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(f"(artifacts at {tmp})")


if __name__ == "__main__":
    main()
