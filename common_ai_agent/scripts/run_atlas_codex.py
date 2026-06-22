#!/usr/bin/env python3
"""Launch the ATLAS web UI with the codex app-server bridge pointed at an
external .codex OAG pack (default ~/Desktop/Project/ip_dev/.codex), with codex
hooks + skill-load surfaced in the chat (🪝 / 📦).

Why it edits .config: the bridge reads CODEX_BRIDGE_* at turn time, and ATLAS
reloads .config on every request (force_reload when the file changes), which
would overwrite plain shell env vars. So this script temporarily writes the pack
config into .config and RESTORES it on exit (try/finally — survives Ctrl-C).
Auth stays on ~/.codex (the pack has no auth.json; do NOT set CODEX_HOME to it).

Usage:
    python3 scripts/run_atlas_codex.py [--pack DIR] [--port N] [--no-build]
      --pack    project that holds .codex   (default ~/Desktop/Project/ip_dev)
      --port    server port                 (default 3041)
      --no-build  skip the vite dist rebuild

Then open http://localhost:<port> (admin/1151) and send any prompt — the OAG
hooks (🪝) and skill load (📦) show up as activity lines in the chat.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # common_ai_agent
CONFIG = ROOT / ".config"

# CODEX_BRIDGE_* values forced for the run (CODEX_BRIDGE_HOME / _OAG_ROOT added
# from --pack at runtime). Auth stays on ~/.codex by NOT setting a runtime home.
OVERRIDES = {
    "CODEX_BRIDGE": "1",
    "CODEX_BRIDGE_ENABLE_HOOKS": "1",
    "CODEX_BRIDGE_RUN_OAG_HOOKS": "1",
    "CODEX_BRIDGE_STAGE_DOT_CODEX": "1",
    "CODEX_BRIDGE_TRUST_THREAD_CWD": "1",
    "CODEX_BRIDGE_BYPASS_HOOK_TRUST": "1",
    "CODEX_BRIDGE_SHOW_HOOKS": "1",
}


def write_config(pack: Path, pack_root: Path) -> None:
    ov = dict(OVERRIDES, CODEX_BRIDGE_HOME=str(pack), CODEX_BRIDGE_OAG_ROOT=str(pack_root))
    seen: set = set()
    out = []
    for ln in CONFIG.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", ln)
        if m and m.group(1) in ov:
            out.append(f"{m.group(1)}={ov[m.group(1)]}")
            seen.add(m.group(1))
        else:
            out.append(ln)
    out += [f"{k}={v}" for k, v in ov.items() if k not in seen]
    CONFIG.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    # Default to the vendored OAG pack checked in at common_ai_agent/ontology_ip_agent/.codex
    # (self-contained). Pass --pack ~/Desktop/Project/ip_dev to run against that
    # project's real IPs instead.
    ap.add_argument("--pack", default=str(ROOT / "ontology_ip_agent"))
    ap.add_argument("--port", type=int, default=3041)
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    pack_root = Path(args.pack).expanduser().resolve()
    pack = pack_root / ".codex"
    if not pack.is_dir():
        print(f"ERROR: no .codex pack at {pack}", file=sys.stderr)
        return 1

    fd, bak_path = tempfile.mkstemp(prefix="atlas_config_bak_")
    os.close(fd)
    shutil.copy2(CONFIG, bak_path)
    try:
        write_config(pack, pack_root)
        print(f"[run-atlas-codex] .config -> CODEX_BRIDGE=1, pack={pack}")

        if not args.no_build:
            print("[run-atlas-codex] building frontend dist (npm run build)...")
            subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend" / "atlas",
                           check=True, stdout=subprocess.DEVNULL)
            print("[run-atlas-codex] dist built")

        subprocess.run(f"lsof -ti:{args.port} | xargs kill", shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        env = dict(os.environ, ATLAS_FRONTEND_MODE="vite")
        env.setdefault("CODEX_BRIDGE_MULTI_AGENT_MODE", "explicitRequestOnly")
        print(f"[run-atlas-codex] starting ATLAS → http://localhost:{args.port}  (admin/1151)")
        print("[run-atlas-codex] send any prompt → 🪝 hook / 📦 skill lines appear in chat. "
              "Ctrl-C to stop.")
        subprocess.run([sys.executable, "src/atlas_ui.py", "--port", str(args.port)],
                       cwd=ROOT, env=env)
    except KeyboardInterrupt:
        pass
    finally:
        shutil.copy2(bak_path, CONFIG)
        os.unlink(bak_path)
        print("\n[run-atlas-codex] .config restored (CODEX_BRIDGE back to its committed default)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
