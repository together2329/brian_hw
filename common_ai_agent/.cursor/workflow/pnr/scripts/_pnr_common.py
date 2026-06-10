#!/usr/bin/env python3
"""_pnr_common.py — Python port of _pnr_common.sh (sourced PnR helper library).

The bash original is ``source``-d by every PnR stage script.  Sourcing does two
things at load time:

1. It re-resolves the bundled PDK paths by sourcing ``workflow/scripts/pdk_env.sh``
   (defaults relative to ``common_ai_agent/``, honouring a ``.env`` override and an
   existing exported value).  ``load_pdk_env()`` reproduces that resolution in
   Python so the ``SKY130_*`` variables the wrapper TCL references resolve
   identically.
2. It defines a set of helper functions.  Those are ported one-for-one below.

Sourcing-semantics mapping (bash -> python):
    * ``source _pnr_common.sh``        -> ``import _pnr_common as common``
    * ``source pdk_env.sh`` (implicit) -> ``common.load_pdk_env(env)`` mutating a
      dict that the caller threads through as ``os.environ`` (the run_* ports call
      ``load_pdk_env(os.environ)`` once at startup, mirroring the source-time side
      effect of exporting ``SKY130_*``).
    * functions returning an rc + echoing to stderr -> functions returning an int
      rc, printing to ``sys.stderr``; functions that ``echo`` a value on stdout for
      command substitution -> functions returning the string (the caller decides
      whether to print).

This module is imported by the sibling ``run_*.py`` ports; it is not a CLI.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, MutableMapping, Optional


# ---------------------------------------------------------------------------
# pdk_env.sh resolution (the implicit `source` at the top of _pnr_common.sh)
# ---------------------------------------------------------------------------

# Keys pdk_env.sh's dotenv loader is willing to import from .env.
_PDK_ENV_DOTENV_KEYS = (
    "PDK_ROOT",
    "SKY130_PDK_ROOT",
    "PDK_LIB_PATH",
    "SKY130_LIB",
    "SKY130_TLEF",
    "SKY130_LEF",
    "SKY130_TRACKS",
    "SKY130_RCX_RULES",
)


def _pdk_env_root() -> Path:
    """Repo root used by pdk_env.sh: two dirs above workflow/scripts/."""
    # pdk_env.sh lives at workflow/scripts/pdk_env.sh and computes
    #   dirname/../.. == common_ai_agent/.  This file lives at
    #   workflow/pnr/scripts/_pnr_common.py, so the same root is parents[3].
    return Path(__file__).resolve().parents[3]


def _pdk_env_abs(root: Path, value: str) -> str:
    """Mirror pdk_env.sh _pdk_env_abs: absolutise a relative value under root."""
    if value.startswith("/"):
        return value
    return f"{root}/{value}"


def _strip_inline_comment(value: str) -> str:
    """Mirror pdk_env.sh value sanitising: drop ' #...' trailing comment + trim + dequote."""
    value = re.sub(r"\s#.*$", "", value)
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    else:
        # pdk_env.sh strips a single leading/trailing quote independently.
        for quote in ('"', "'"):
            if value.endswith(quote):
                value = value[:-1]
            if value.startswith(quote):
                value = value[1:]
    return value


def _load_dotenv(env: MutableMapping[str, str], dotenv: Path) -> None:
    """Mirror _pdk_env_load_dotenv: import a whitelist of keys, never overriding."""
    if not dotenv.is_file():
        return
    for raw in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.lstrip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            # `key%%=*` == whole line; `key` won't be in whitelist -> skip.
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key not in _PDK_ENV_DOTENV_KEYS:
            continue
        if env.get(key):
            continue
        env[key] = _strip_inline_comment(val)


def load_pdk_env(env: MutableMapping[str, str]) -> None:
    """Replicate ``source pdk_env.sh``: fill SKY130_* defaults into ``env``.

    Mirrors the resolution order in workflow/scripts/pdk_env.sh exactly: dotenv
    import (non-overriding), then per-variable default-or-absolutise.  Mutates
    ``env`` in place (callers pass ``os.environ``), matching the bash ``export``.
    """
    root = _pdk_env_root()
    _load_dotenv(env, root / ".env")

    def resolve(key: str, default: str) -> None:
        cur = env.get(key)
        if not cur:
            env[key] = default
        elif not cur.startswith("/"):
            env[key] = _pdk_env_abs(root, cur)
        # else: already absolute -> leave as-is.

    resolve("PDK_ROOT", f"{root}/pdk")
    resolve("SKY130_PDK_ROOT", f"{env['PDK_ROOT']}/sky130")
    resolve("PDK_LIB_PATH", f"{env['SKY130_PDK_ROOT']}/lib")

    # SKY130_LIB has glob-fallback logic instead of a single default.
    cur_lib = env.get("SKY130_LIB")
    if not cur_lib:
        lib_path = env["PDK_LIB_PATH"]
        candidates = [
            f"{lib_path}/sky130_fd_sc_hd__ss_100C_1v40.lib",
            f"{lib_path}/sky130_fd_sc_hd__ss_n40C_1v40.lib",
        ]
        candidates += sorted(glob.glob(f"{lib_path}/*.lib"))
        for cand in candidates:
            if os.access(cand, os.R_OK):
                env["SKY130_LIB"] = cand
                break
    elif not cur_lib.startswith("/"):
        env["SKY130_LIB"] = _pdk_env_abs(root, cur_lib)

    resolve("SKY130_TLEF", f"{env['SKY130_PDK_ROOT']}/lef/sky130_fd_sc_hd.tlef")
    resolve("SKY130_LEF", f"{env['SKY130_PDK_ROOT']}/lef/sky130_fd_sc_hd_merged.lef")
    resolve("SKY130_TRACKS", f"{env['SKY130_PDK_ROOT']}/make_tracks.tcl")
    resolve("SKY130_RCX_RULES", f"{env['SKY130_PDK_ROOT']}/rcx_patterns.rules")


# ---------------------------------------------------------------------------
# Helper functions (1:1 with the sourced bash functions)
# ---------------------------------------------------------------------------


def run_embedded_py(script: str, args: "list[str]",
                    capture: bool = False) -> "subprocess.CompletedProcess":
    """Run an embedded python snippet exactly like the bash `python3 - "$@" <<'PY'`.

    Feeding the body on stdin (``python3 -``) — rather than ``-c`` — makes the
    interpreter report ``File "<stdin>"`` in tracebacks, matching the bash
    heredoc form byte-for-byte.  The leading newline of the triple-quoted source
    is stripped so traceback line numbers line up with the bash heredoc (whose
    first content line is line 1).
    """
    return subprocess.run(
        [sys.executable, "-", *args],
        input=script.lstrip("\n"),
        capture_output=capture,
        text=True,
    )


def argv_from_hook(argv: "list[str]", env: Optional[Mapping[str, str]] = None) -> "list[str]":
    """Reproduce `if [ $# -eq 0 ] && [ -n "$HOOK_CMD_ARGS" ]; then set -- $HOOK_CMD_ARGS; fi`.

    When invoked with no positional args but HOOK_CMD_ARGS is set, the bash
    wrappers re-split HOOK_CMD_ARGS on IFS (unquoted word-splitting) into argv.
    """
    if env is None:
        env = os.environ
    if not argv:
        hook = env.get("HOOK_CMD_ARGS", "")
        if hook:
            return hook.split()
    return argv


def resolve_input_netlist(ip: str) -> str:
    """pnr_resolve_input_netlist: prefer dft/out/scan.v, else syn/out/synth.v."""
    scan = Path(ip) / "dft" / "out" / "scan.v"
    if scan.is_file() and scan.stat().st_size > 0:
        return f"{ip}/dft/out/scan.v"
    synth = Path(ip) / "syn" / "out" / "synth.v"
    if synth.is_file() and synth.stat().st_size > 0:
        return f"{ip}/syn/out/synth.v"
    return ""


def check_tools(env: Optional[MutableMapping[str, str]] = None) -> int:
    """pnr_check_tools: openroad on PATH + readable PDK files. Returns rc (0 ok)."""
    if env is None:
        env = os.environ
    if _which("openroad", env) is None:
        print("[PNR TOOL MISSING] openroad not on PATH", file=sys.stderr)
        return 3
    tlef = env.get("SKY130_TLEF", "")
    lef = env.get("SKY130_LEF", "")
    lib = env.get("SKY130_LIB", "")
    tracks = env.get("SKY130_TRACKS", "")
    rcx = env.get("SKY130_RCX_RULES", "")
    if not _readable(tlef) or not _readable(lef):
        print(f"[PNR MISSING LEF] tlef={tlef} lef={lef}", file=sys.stderr)
        return 4
    if not _readable(lib):
        print(f"[PNR MISSING PDK] $SKY130_LIB unreadable: {lib}", file=sys.stderr)
        return 4
    if not _readable(tracks):
        print(f"[PNR MISSING TRACKS] $SKY130_TRACKS unreadable: {tracks}", file=sys.stderr)
        return 4
    if not _readable(rcx):
        print(f"[PNR MISSING RCX] $SKY130_RCX_RULES unreadable: {rcx}", file=sys.stderr)
        return 4
    env["SKY130_TLEF"] = tlef
    env["SKY130_LEF"] = lef
    env["SKY130_LIB"] = lib
    env["SKY130_TRACKS"] = tracks
    env["SKY130_RCX_RULES"] = rcx
    return 0


def layer_direction(layer: str, env: Optional[Mapping[str, str]] = None) -> str:
    """pnr_layer_direction: scan the TLEF for `LAYER <name> ... DIRECTION <dir>`."""
    if env is None:
        env = os.environ
    tlef = env.get("SKY130_TLEF", "")
    if not tlef or not Path(tlef).is_file():
        return ""
    in_layer = False
    for raw in Path(tlef).read_text(encoding="utf-8", errors="replace").splitlines():
        fields = raw.split()
        if not fields:
            continue
        if fields[0].upper() == "LAYER" and len(fields) >= 2 and fields[1] == layer:
            in_layer = True
            continue
        if in_layer and fields[0].upper() == "DIRECTION" and len(fields) >= 2:
            return fields[1].replace(";", "").lower()
        if in_layer and fields[0].upper() == "END":
            in_layer = False
    return ""


def check_io_layers(hor: str, ver: str, env: Optional[Mapping[str, str]] = None) -> int:
    """pnr_check_io_layers: assert hor is horizontal and ver is vertical."""
    hor_dir = layer_direction(hor, env)
    ver_dir = layer_direction(ver, env)
    if hor_dir != "horizontal":
        print(
            f"[PNR IO LAYER ERROR] horizontal layer {hor} has direction "
            f"{hor_dir or 'unknown'}; use a horizontal routing layer such as met3",
            file=sys.stderr,
        )
        return 8
    if ver_dir != "vertical":
        print(
            f"[PNR IO LAYER ERROR] vertical layer {ver} has direction "
            f"{ver_dir or 'unknown'}; use a vertical routing layer such as met2",
            file=sys.stderr,
        )
        return 8
    return 0


def check_handoff(ip: str) -> "tuple[str, int]":
    """pnr_check_handoff: resolve netlist + assert SDC. Returns (netlist, rc).

    On rc != 0 the netlist string is empty; the bash caller used command
    substitution `NETLIST=$(pnr_check_handoff ...) || exit $?`, so the run_*
    ports check rc and print the netlist on success.
    """
    netlist = resolve_input_netlist(ip)
    if not netlist:
        print(
            "[PNR HANDOFF MISSING] no scan.v or synth.v — run /syn (and optionally /dft) first",
            file=sys.stderr,
        )
        return "", 5
    sdc = Path(ip) / "sta" / "out" / f"{ip}.sdc"
    if not sdc.is_file():
        print(f"[PNR SDC MISSING] {ip}/sta/out/{ip}.sdc — run /sta-sdc first", file=sys.stderr)
        return "", 5
    return netlist, 0


def check_stale(label: str, upstream: str, output: str) -> int:
    """pnr_check_stale: fail if upstream missing; rm output if upstream newer."""
    up = Path(upstream)
    if not (up.is_file() and up.stat().st_size > 0):
        print(f"[PNR STALE {label}] upstream missing: {upstream}", file=sys.stderr)
        return 6
    out = Path(output)
    if out.exists() and up.stat().st_mtime > out.stat().st_mtime:
        print(
            f"[PNR REBUILD {label}] {upstream} newer than {output} — regenerating {output}",
            file=sys.stderr,
        )
        out.unlink(missing_ok=True)
    return 0


# Inline python heredoc from _pnr_common.sh's pnr_top_from_ssot.
_TOP_FROM_SSOT_PY = r"""
import sys, pathlib
ssot, ip = sys.argv[1:3]
try:
    import yaml; d = yaml.safe_load(pathlib.Path(ssot).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
_t = d.get("top_module")
if isinstance(_t, dict): _t = _t.get("name")
print(_t or d.get("top") or ip)
"""


def top_from_ssot(ip: str) -> str:
    """pnr_top_from_ssot: top_module/top from SSOT, else the IP name.

    Runs the identical embedded python via the interpreter so the YAML parse /
    fallback semantics are byte-for-byte the bash original's (which spawned
    `python3 - ...`).
    """
    ssot = f"{ip}/yaml/{ip}.ssot.yaml"
    proc = run_embedded_py(_TOP_FROM_SSOT_PY, [ssot, ip], capture=True)
    return proc.stdout.strip()


# ---------------------------------------------------------------------------
# small shell-builtin equivalents
# ---------------------------------------------------------------------------


def run_openroad_tee(tcl: str, log: str, env: Optional[Mapping[str, str]] = None,
                      append: bool = True) -> int:
    """`openroad -no_init -exit <tcl> 2>&1 | tee[-a] <log>` returning PIPESTATUS[0].

    Streams openroad's merged stdout+stderr to this process's stdout *and* to the
    log file (append when ``append``), then returns openroad's own exit code (not
    tee's), matching ``RC=${PIPESTATUS[0]}`` in the bash wrappers.  Used by the
    four run_* stage ports, so it lives here to keep the invocation identical.
    """
    if env is None:
        env = os.environ
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    # Flush the text-layer stdout buffer so the preceding print() lands before
    # the openroad output we write straight to the binary buffer (otherwise the
    # ordering inverts vs. the bash `echo; openroad | tee` sequence).
    sys.stdout.flush()
    proc = subprocess.run(
        ["openroad", "-no_init", "-exit", tcl],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=dict(env),
    )
    out = proc.stdout or b""
    sys.stdout.buffer.write(out)
    sys.stdout.buffer.flush()
    with open(log, mode + "b") as fh:
        fh.write(out)
    return proc.returncode


def _which(name: str, env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """`command -v <name>` for an executable on PATH (env-aware)."""
    if env is None:
        env = os.environ
    path = env.get("PATH", os.defpath)
    for directory in path.split(os.pathsep):
        if not directory:
            continue
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _readable(path: str) -> bool:
    """`[ -r <path> ]`: non-empty path that exists and is readable."""
    return bool(path) and os.access(path, os.R_OK)
