"""Differential equivalence tests for the PnR + DFT bash->python ports.

For each ``*.sh`` under ``workflow/pnr/scripts/`` and ``workflow/dft/scripts/``
there is a same-named ``*.py`` that must be a drop-in replacement: identical CLI,
exit code, stdout/stderr, recorded tool-invocation argv, and produced artifacts.

Technique
---------
The real EDA tools (OpenROAD ``openroad``, AUCOHL ``fault``) are replaced by
PATH-stub fakes that:
  * append their argv to ``$ARGV_LOG`` (so we can diff the invocation sequence),
  * emit the minimal canned outputs/files the wrappers expect.

For each script we run the ``.sh`` and the ``.py`` in the *same* workspace + cwd
(sh first, snapshot, clean the output subtree, then py, snapshot) so even
cwd-echoing stages (preflight) compare equal, then assert rc + stdout + stderr +
recorded tool argv + artifact tree all match.  A second set of cases drives the
tool-missing path (PATH scrubbed to system bins, no ``openroad``/``fault``) to
check the "not on PATH" parity.

No real tools are required; the stubs supply invocation parity only.  The
tool-missing cases scrub PATH to ``/usr/bin:/bin`` because a developer machine
may have a real ``openroad`` on PATH that would otherwise mask rc 3.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PNR_SCRIPTS = PROJECT_ROOT / "workflow" / "pnr" / "scripts"
DFT_SCRIPTS = PROJECT_ROOT / "workflow" / "dft" / "scripts"

# Minimal PATH that excludes a developer's ~/.local/bin/openroad for the
# tool-missing cases (python3 + bash live in /usr/bin and /bin).
_SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"


# ---------------------------------------------------------------------------
# Stub tools
# ---------------------------------------------------------------------------

_OPENROAD_PNR_STUB = r"""#!/usr/bin/env bash
# Fake OpenROAD for PnR: record argv, then materialise any write_def /
# write_verilog / write_spef target referenced by the TCL (last arg).
[ -n "${ARGV_LOG:-}" ] && echo "openroad $*" >> "$ARGV_LOG"
tcl="${@: -1}"
if [ -f "$tcl" ]; then
  while read -r a b _rest; do
    case "$a" in
      write_def)     [ -n "$b" ] && { mkdir -p "$(dirname "$b")"; echo "DEF" > "$b"; } ;;
      write_verilog) [ -n "$b" ] && { mkdir -p "$(dirname "$b")"; echo "module top; endmodule" > "$b"; } ;;
      write_spef)    [ -n "$b" ] && { mkdir -p "$(dirname "$b")"; echo "*SPEF" > "$b"; } ;;
    esac
  done < "$tcl"
fi
echo "[fake-openroad] design area 1234.5 u^2 60 % utilization"
exit 0
"""

_OPENROAD_DFT_STUB = r"""#!/usr/bin/env bash
# Fake OpenROAD for DFT: record argv, materialise scan.v with scan FFs from
# write_verilog, then print a report_dft chain line on stdout.
[ -n "${ARGV_LOG:-}" ] && echo "openroad $*" >> "$ARGV_LOG"
tcl="${@: -1}"
if [ -f "$tcl" ]; then
  while read -r a b _rest; do
    if [ "$a" = "write_verilog" ] && [ -n "$b" ]; then
      mkdir -p "$(dirname "$b")"
      printf 'module top;\n sky130_fd_sc_hd__sdfrtp_1 ff0();\n sky130_fd_sc_hd__sdfrtp_1 ff1();\n sky130_fd_sc_hd__dfrtp_1 ff2();\nendmodule\n' > "$b"
    fi
  done < "$tcl"
fi
echo "Scan chain 0: length=2, scan_in=scan_in[0], scan_out=scan_out[0], clock=clk"
exit 0
"""

_FAULT_STUB = r"""#!/usr/bin/env bash
# Fake Fault ATPG: record argv, write the -o test output, print a coverage line.
[ -n "${ARGV_LOG:-}" ] && echo "fault $*" >> "$ARGV_LOG"
prev=""
for arg in "$@"; do
  if [ "$prev" = "-o" ]; then mkdir -p "$(dirname "$arg")"; echo "test-patterns" > "$arg"; fi
  prev="$arg"
done
echo "Coverage: 92.4%"
exit 0
"""


def _write_exec(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _make_pdk(tmp: Path) -> "dict[str, str]":
    """Create PDK stub files and return the SKY130_* env mapping."""
    pdk = tmp / "pdk"
    pdk.mkdir(parents=True, exist_ok=True)
    tlef = pdk / "fake.tlef"
    # met3 horizontal, met2 vertical so pnr_check_io_layers passes for met3/met2.
    tlef.write_text(
        "LAYER met2\n  DIRECTION VERTICAL ;\nEND met2\n"
        "LAYER met3\n  DIRECTION HORIZONTAL ;\nEND met3\n",
        encoding="utf-8",
    )
    (pdk / "fake.lib").write_text("lib\n", encoding="utf-8")
    (pdk / "tracks.tcl").write_text("tracks\n", encoding="utf-8")
    (pdk / "rcx.rules").write_text("rcx\n", encoding="utf-8")
    # Pin PDK roots too so pdk_env.sh never points at the real bundled PDK
    # (keeps the preflight cwd/PDK_ROOT echo deterministic and self-contained).
    return {
        "PDK_ROOT": str(pdk),
        "SKY130_PDK_ROOT": str(pdk),
        "PDK_LIB_PATH": str(pdk),
        "SKY130_TLEF": str(tlef),
        "SKY130_LEF": str(tlef),
        "SKY130_LIB": str(pdk / "fake.lib"),
        "SKY130_TRACKS": str(pdk / "tracks.tcl"),
        "SKY130_RCX_RULES": str(pdk / "rcx.rules"),
    }


def _env_with_path(extra: "dict[str, str]", path_value: str) -> "dict[str, str]":
    env = dict(os.environ)
    env.update(extra)
    env["PATH"] = path_value
    return env


def _run(cmd: "list[str]", cwd: Path, env: "dict[str, str]", argv_log: Path):
    e = dict(env)
    e["ARGV_LOG"] = str(argv_log)
    return subprocess.run(cmd, cwd=str(cwd), env=e, capture_output=True, text=True)


def _tree_signature(root: Path) -> "list[tuple[str, str]]":
    """(relpath, content) for every file under root, sorted."""
    sig = []
    if not root.exists():
        return sig
    for p in sorted(root.rglob("*")):
        if p.is_file():
            sig.append((str(p.relative_to(root)), p.read_text(encoding="utf-8", errors="replace")))
    return sig


def _run_pair(name: str, script_dir: Path, script: str, ip: str, work: Path,
              env: "dict[str, str]", out_subtree: str,
              prime=None) -> None:
    """Run ``<script>.sh`` then ``<script>.py`` in the same work dir; assert parity.

    ``out_subtree`` is the per-IP output dir (e.g. ``myip/pnr``) snapshotted and
    cleaned between the two runs.  ``prime`` is an optional callable(work, env)
    that recreates the stage's required inputs before each run.
    """
    out_dir = work / out_subtree
    argv_log = work / "_argv.log"

    def reset():
        if out_dir.exists():
            shutil.rmtree(out_dir)
        if argv_log.exists():
            argv_log.unlink()
        if prime:
            prime(work, env)

    reset()
    sh = _run(["bash", str(script_dir / f"{script}.sh"), ip], work, env, argv_log)
    sh_tree = _tree_signature(out_dir)
    sh_argv = argv_log.read_text() if argv_log.exists() else ""

    reset()
    py = _run([sys.executable, str(script_dir / f"{script}.py"), ip], work, env, argv_log)
    py_tree = _tree_signature(out_dir)
    py_argv = argv_log.read_text() if argv_log.exists() else ""

    assert sh.returncode == py.returncode, (
        f"{name}: rc {sh.returncode} (sh) != {py.returncode} (py)\n"
        f"sh.err={sh.stderr!r}\npy.err={py.stderr!r}"
    )
    assert sh.stdout == py.stdout, f"{name}: stdout differs\n--- sh\n{sh.stdout}\n--- py\n{py.stdout}"
    assert sh.stderr == py.stderr, f"{name}: stderr differs\n--- sh\n{sh.stderr}\n--- py\n{py.stderr}"
    assert sh_argv == py_argv, f"{name}: tool argv differs\n--- sh\n{sh_argv}\n--- py\n{py_argv}"
    assert sh_tree == py_tree, f"{name}: artifact tree differs"


# ---------------------------------------------------------------------------
# Fixtures: workspaces
# ---------------------------------------------------------------------------


def _make_pnr_ip(work: Path, ip: str = "myip") -> None:
    d = work / ip
    (d / "yaml").mkdir(parents=True, exist_ok=True)
    (d / "syn" / "out").mkdir(parents=True, exist_ok=True)
    (d / "sta" / "out").mkdir(parents=True, exist_ok=True)
    (d / "yaml" / f"{ip}.ssot.yaml").write_text(
        "top_module: { name: myip_top }\n"
        "pnr:\n"
        "  utilization_pct: 65\n"
        "  aspect_ratio: 1.2\n"
        "  core_space_um: 3.0\n"
        "  global_density: 0.7\n"
        "  io_layers: { horizontal: met3, vertical: met2 }\n"
        "  cts_buf_list: [sky130_fd_sc_hd__clkbuf_4, sky130_fd_sc_hd__clkbuf_8]\n",
        encoding="utf-8",
    )
    (d / "syn" / "out" / "synth.v").write_text(
        "module myip_top(input scan_en); endmodule\n", encoding="utf-8"
    )
    (d / "sta" / "out" / f"{ip}.sdc").write_text("set_sdc_dummy\n", encoding="utf-8")


def _make_dft_ip(work: Path, ip: str, enabled: bool, atpg: bool = False) -> None:
    d = work / ip
    (d / "yaml").mkdir(parents=True, exist_ok=True)
    (d / "syn" / "out").mkdir(parents=True, exist_ok=True)
    ssot = "top_module: { name: %s_top }\n" % ip
    if enabled:
        ssot += (
            "dft:\n"
            "  enabled: true\n"
            "  scan_enable_port: scan_en\n"
            "  max_chains: 4\n"
            "  max_chain_length: 100\n"
        )
        if atpg:
            ssot += (
                "  atpg:\n"
                "    enabled: true\n"
                "    fault_model: stuck_at\n"
                "    target_coverage: 0.95\n"
            )
    (d / "yaml" / f"{ip}.ssot.yaml").write_text(ssot, encoding="utf-8")
    port = "(input scan_en)" if enabled else ""
    (d / "syn" / "out" / "synth.v").write_text(
        f"module {ip}_top{port}; endmodule\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# PnR tests
# ---------------------------------------------------------------------------

# Stages that consume an upstream artifact; prime the run_* chain up to each.
_PNR_CHAIN = ["run_fp", "run_place", "run_cts", "run_route"]


def _prime_pnr(upto: str):
    def _prime(work: Path, env: "dict[str, str]") -> None:
        idx = _PNR_CHAIN.index(upto) if upto in _PNR_CHAIN else len(_PNR_CHAIN)
        for stage in _PNR_CHAIN[:idx]:
            _run([sys.executable, str(PNR_SCRIPTS / f"{stage}.py"), "myip"],
                 work, env, work / "_prime.log")
    return _prime


@pytest.mark.parametrize("stage", ["preflight", "run_fp", "run_place", "run_cts", "run_route", "write_report"])
def test_pnr_stage_parity(tmp_path, stage):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exec(bindir / "openroad", _OPENROAD_PNR_STUB)
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_pnr_ip(work)
    env = _env_with_path(pdk, f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    _run_pair(stage, PNR_SCRIPTS, stage, "myip", work, env, "myip/pnr", prime=_prime_pnr(stage))


def test_pnr_auto_full_pipeline(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exec(bindir / "openroad", _OPENROAD_PNR_STUB)
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_pnr_ip(work)
    env = _env_with_path(pdk, f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    _run_pair("auto_pnr", PNR_SCRIPTS, "auto_pnr", "myip", work, env, "myip/pnr")


def test_pnr_usage_no_args(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exec(bindir / "openroad", _OPENROAD_PNR_STUB)
    env = _env_with_path(_make_pdk(tmp_path), f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    for stage in ["run_fp", "run_place", "run_cts", "run_route", "preflight", "auto_pnr", "write_report"]:
        sh = _run(["bash", str(PNR_SCRIPTS / f"{stage}.sh")], tmp_path, env, tmp_path / "s.log")
        py = _run([sys.executable, str(PNR_SCRIPTS / f"{stage}.py")], tmp_path, env, tmp_path / "p.log")
        assert sh.returncode == py.returncode == 2, f"{stage}: rc {sh.returncode}/{py.returncode}"
        assert sh.stdout == py.stdout, f"{stage}: stdout {sh.stdout!r} != {py.stdout!r}"
        assert sh.stderr == py.stderr, f"{stage}: stderr {sh.stderr!r} != {py.stderr!r}"


def test_pnr_tool_missing(tmp_path):
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_pnr_ip(work)
    env = _env_with_path(pdk, _SYSTEM_PATH)  # no openroad on this PATH
    for stage in ["run_fp", "run_place", "run_cts", "run_route", "preflight"]:
        sh = _run(["bash", str(PNR_SCRIPTS / f"{stage}.sh"), "myip"], work, env, tmp_path / "s.log")
        py = _run([sys.executable, str(PNR_SCRIPTS / f"{stage}.py"), "myip"], work, env, tmp_path / "p.log")
        assert sh.returncode == py.returncode == 3, (
            f"{stage}: expected openroad-missing rc 3, got {sh.returncode}/{py.returncode}\n"
            f"sh.err={sh.stderr!r} py.err={py.stderr!r}"
        )
        assert sh.stdout == py.stdout
        assert sh.stderr == py.stderr


# ---------------------------------------------------------------------------
# DFT tests
# ---------------------------------------------------------------------------


def _prime_dft_scan(work: Path, env: "dict[str, str]") -> None:
    """Run write_dft_tcl + run_openroad_dft (.py) so parse/report have inputs."""
    log = work / "_p.log"
    _run([sys.executable, str(DFT_SCRIPTS / "write_dft_tcl.py"), "scan"], work, env, log)
    _run([sys.executable, str(DFT_SCRIPTS / "run_openroad_dft.py"), "scan"], work, env, log)


def test_dft_auto_passthrough(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exec(bindir / "openroad", _OPENROAD_DFT_STUB)
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_dft_ip(work, "pass", enabled=False)
    env = _env_with_path(pdk, f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    _run_pair("auto_dft/pass", DFT_SCRIPTS, "auto_dft", "pass", work, env, "pass/dft")


def test_dft_auto_scan_insert_with_atpg(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exec(bindir / "openroad", _OPENROAD_DFT_STUB)
    _write_exec(bindir / "fault", _FAULT_STUB)
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_dft_ip(work, "scan", enabled=True, atpg=True)
    env = _env_with_path(pdk, f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    _run_pair("auto_dft/scan", DFT_SCRIPTS, "auto_dft", "scan", work, env, "scan/dft")


@pytest.mark.parametrize("stage", ["write_dft_tcl", "run_openroad_dft", "parse_chains", "write_report"])
def test_dft_stage_parity(tmp_path, stage):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exec(bindir / "openroad", _OPENROAD_DFT_STUB)
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_dft_ip(work, "scan", enabled=True)
    env = _env_with_path(pdk, f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    prime = _prime_dft_scan if stage in ("parse_chains", "write_report") else None
    _run_pair(stage, DFT_SCRIPTS, stage, "scan", work, env, "scan/dft", prime=prime)


def test_dft_fault_atpg_standalone(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exec(bindir / "openroad", _OPENROAD_DFT_STUB)
    _write_exec(bindir / "fault", _FAULT_STUB)
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_dft_ip(work, "scan", enabled=True, atpg=True)
    env = _env_with_path(pdk, f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    _run_pair("run_fault_atpg", DFT_SCRIPTS, "run_fault_atpg", "scan", work, env, "scan/dft",
              prime=_prime_dft_scan)


def test_dft_usage_no_args(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    env = _env_with_path(_make_pdk(tmp_path), f"{bindir}{os.pathsep}{_SYSTEM_PATH}")
    for stage in ["write_dft_tcl", "run_openroad_dft", "run_fault_atpg", "parse_chains", "write_report", "auto_dft"]:
        sh = _run(["bash", str(DFT_SCRIPTS / f"{stage}.sh")], tmp_path, env, tmp_path / "s.log")
        py = _run([sys.executable, str(DFT_SCRIPTS / f"{stage}.py")], tmp_path, env, tmp_path / "p.log")
        assert sh.returncode == py.returncode == 2, f"{stage}: rc {sh.returncode}/{py.returncode}"
        assert sh.stdout == py.stdout, f"{stage}: stdout {sh.stdout!r} != {py.stdout!r}"
        assert sh.stderr == py.stderr, f"{stage}: stderr {sh.stderr!r} != {py.stderr!r}"


def test_dft_tool_missing(tmp_path):
    pdk = _make_pdk(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _make_dft_ip(work, "scan", enabled=True)
    env = _env_with_path(pdk, _SYSTEM_PATH)  # no openroad on this PATH
    sh = _run(["bash", str(DFT_SCRIPTS / "auto_dft.sh"), "scan"], work, env, tmp_path / "s.log")
    py = _run([sys.executable, str(DFT_SCRIPTS / "auto_dft.py"), "scan"], work, env, tmp_path / "p.log")
    assert sh.returncode == py.returncode == 3, (
        f"auto_dft tool-missing: rc {sh.returncode}/{py.returncode}\n"
        f"sh.err={sh.stderr!r} py.err={py.stderr!r}"
    )
    assert sh.stdout == py.stdout
    assert sh.stderr == py.stderr
