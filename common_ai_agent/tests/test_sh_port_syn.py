"""Pinned regression tests for the syn-stage python ports.

Each ``*.py`` under ``workflow/syn/scripts/`` (plus ``workflow/scripts/pdk_env.py``)
is exercised over a fixture; we assert the PINNED exit code plus the key output /
artifact markers captured from the (formerly green) sh-vs-py differential parity
run. The bash originals are being removed, so these tests run ONLY the ``.py``
side.

Technique
---------
  * PATH-stub fake tools (``yosys`` / ``openroad`` / ``sta``) are tiny *python*
    executables that record their argv to a log and emit the minimal canned
    outputs/files each wrapper parses, so artifacts are deterministic without the
    real EDA tools — and we exercise the tool-missing path too.
  * For the pure writers/parsers (``write_yosys_script`` / ``parse_area`` /
    ``write_report``) we feed a canned fixture and pin the generated file content
    / parsed JSON the script produces.
  * Volatile values (absolute liberty / HOME / temp-root paths, embedded
    timestamps) are masked or asserted as substring markers rather than compared
    byte-for-byte. On macOS the wrappers resolve the temp root through the
    ``/private`` symlink, so we pin structural markers instead of full paths.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SYN = REPO / "workflow" / "syn" / "scripts"
SCRIPTS = REPO / "workflow" / "scripts"

# Bundled liberty the pdk_env default resolves to (asserted present so the
# artifact check is meaningful rather than vacuous-on-missing-PDK).
BUNDLED_LIB = REPO / "pdk" / "sky130" / "lib" / "sky130_fd_sc_hd__ss_100C_1v40.lib"


# --------------------------------------------------------------------------- #
# Fixture helpers
# --------------------------------------------------------------------------- #
def _make_ip(root: Path, ip: str = "demo_ip", top: str = "demo_top") -> Path:
    """Create a minimal IP tree: yaml/ssot, list/filelist, rtl source, sdc."""
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "list").mkdir(parents=True, exist_ok=True)
    (ip_dir / "rtl").mkdir(parents=True, exist_ok=True)
    (ip_dir / "sdc").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"top_module:\n  name: {top}\nsub_modules: []\n", encoding="utf-8"
    )
    (ip_dir / "rtl" / "demo.sv").write_text(
        f"module {top}(input clk);\nendmodule\n", encoding="utf-8"
    )
    (ip_dir / "list" / f"{ip}.f").write_text("rtl/demo.sv\n", encoding="utf-8")
    (ip_dir / "sdc" / f"{ip}.sdc").write_text(
        "create_clock -name clk -period 10 [get_ports clk]\n", encoding="utf-8"
    )
    return ip_dir


def _make_stub(stub_dir: Path, name: str, argv_log: Path, body: str = "") -> None:
    """Write an executable *python* PATH-stub that logs its argv then runs ``body``.

    ``body`` is python source executed after the argv-record preamble; it has
    ``argv`` (the tool's args, ``sys.argv[1:]``) and the stdlib in scope. These
    stubs replace the former bash-shebang stubs so the suite needs no shell.
    """
    stub_dir.mkdir(parents=True, exist_ok=True)
    script = stub_dir / name
    preamble = (
        "#!/usr/bin/env python3\n"
        "import os, sys, re\n"
        "from pathlib import Path\n"
        "argv = sys.argv[1:]\n"
        f"open({json.dumps(str(argv_log))}, 'a', encoding='utf-8')"
        ".write(' '.join(argv) + '\\n')\n"
    )
    script.write_text(preamble + textwrap.dedent(body) + "\nsys.exit(0)\n", encoding="utf-8")
    script.chmod(0o755)


def _run(
    cmd: list[str],
    cwd: Path,
    extra_path: str | None = None,
    override_path: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    if override_path is not None:
        env["PATH"] = override_path
    elif extra_path is not None:
        env["PATH"] = extra_path + os.pathsep + env.get("PATH", "")
    # Strip any pre-set PDK vars so the port exercises pdk_env default resolution.
    for key in (
        "PDK_ROOT",
        "SKY130_PDK_ROOT",
        "PDK_LIB_PATH",
        "SKY130_LIB",
        "SKY130_TLEF",
        "SKY130_LEF",
        "SKY130_TRACKS",
        "SKY130_RCX_RULES",
        "HOOK_CMD_ARGS",
    ):
        env.pop(key, None)
    return subprocess.run(
        cmd, cwd=str(cwd), env=env, capture_output=True, text=True
    )


# --------------------------------------------------------------------------- #
# pdk_env: CLI + importable module
# --------------------------------------------------------------------------- #
_PDK_KEYS = [
    "PDK_ROOT",
    "SKY130_PDK_ROOT",
    "PDK_LIB_PATH",
    "SKY130_LIB",
    "SKY130_TLEF",
    "SKY130_LEF",
    "SKY130_TRACKS",
    "SKY130_RCX_RULES",
]


def test_pdk_env_cli_emits_resolved_keys() -> None:
    """pdk_env.py prints ``KEY=VALUE`` for all 8 PDK keys (default resolution)."""
    env = dict(os.environ)
    for k in _PDK_KEYS:
        env.pop(k, None)
    py = subprocess.run(
        [sys.executable, str(SCRIPTS / "pdk_env.py")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert py.returncode == 0, py.stderr
    out = py.stdout.replace(str(REPO), "<REPO>")
    # Pinned resolved values from the bundled PDK (repo path normalised).
    assert "PDK_ROOT=<REPO>/pdk\n" in out
    assert "SKY130_PDK_ROOT=<REPO>/pdk/sky130\n" in out
    assert "PDK_LIB_PATH=<REPO>/pdk/sky130/lib\n" in out
    assert "SKY130_LIB=<REPO>/pdk/sky130/lib/sky130_fd_sc_hd__ss_100C_1v40.lib\n" in out
    assert "SKY130_TLEF=<REPO>/pdk/sky130/lef/sky130_fd_sc_hd.tlef\n" in out
    assert "SKY130_LEF=<REPO>/pdk/sky130/lef/sky130_fd_sc_hd_merged.lef\n" in out
    assert "SKY130_TRACKS=<REPO>/pdk/sky130/make_tracks.tcl\n" in out
    assert "SKY130_RCX_RULES=<REPO>/pdk/sky130/rcx_patterns.rules\n" in out
    # Every key appears exactly once (line-anchored so PDK_ROOT doesn't also
    # match SKY130_PDK_ROOT).
    for k in _PDK_KEYS:
        assert len(re.findall(rf"(?m)^{re.escape(k)}=", out)) == 1


def test_pdk_env_importable_module() -> None:
    sys.path.insert(0, str(SCRIPTS))
    import pdk_env  # noqa: WPS433

    resolved = pdk_env.resolve_pdk_env()
    assert resolved["PDK_ROOT"].endswith("/pdk")
    assert resolved["SKY130_LIB"].endswith(".lib")
    # apply_pdk_env mutates a dict like ``source`` mutates the env.
    target: dict[str, str] = {}
    pdk_env.apply_pdk_env(target)
    assert target["SKY130_LIB"] == resolved["SKY130_LIB"]


# --------------------------------------------------------------------------- #
# Pure writer: write_yosys_script — generated run.ys content
# --------------------------------------------------------------------------- #
def test_write_yosys_script_artifact_parity(tmp_path: Path) -> None:
    assert BUNDLED_LIB.is_file(), "bundled liberty missing — artifact check is vacuous"

    py_root = tmp_path / "py"
    _make_ip(py_root)

    py = _run([sys.executable, str(SYN / "write_yosys_script.py"), "demo_ip"], py_root)

    assert py.returncode == 0, py.stderr
    py_ys = (py_root / "demo_ip" / "syn" / "run.ys").read_text()
    # Pinned structural content of the generated yosys script.
    assert "hierarchy -check -top demo_top" in py_ys
    assert "synth -top demo_top" in py_ys
    assert f'read_liberty -lib "{BUNDLED_LIB}"' in py_ys
    assert 'write_verilog -noattr "' in py_ys and "/syn/out/synth.v" in py_ys


def test_write_yosys_script_usage_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "write_yosys_script.py")], tmp_path)
    assert py.returncode == 2
    assert "usage:" in py.stderr.lower()


def test_write_yosys_script_hook_cmd_args(tmp_path: Path) -> None:
    """No positional arg → falls back to HOOK_CMD_ARGS."""
    py_root = tmp_path / "py"
    _make_ip(py_root)
    env = dict(os.environ)
    env["HOOK_CMD_ARGS"] = "demo_ip"
    for k in ("SKY130_LIB", "PDK_ROOT"):
        env.pop(k, None)
    py = subprocess.run(
        [sys.executable, str(SYN / "write_yosys_script.py")],
        cwd=str(py_root),
        env=env,
        capture_output=True,
        text=True,
    )
    assert py.returncode == 0, py.stderr
    assert (py_root / "demo_ip" / "syn" / "run.ys").is_file()


# --------------------------------------------------------------------------- #
# Pure parser: parse_area — parsed area.json
# --------------------------------------------------------------------------- #
SAMPLE_SYN_LOG = textwrap.dedent(
    """\
    yosys> stat -liberty foo.lib

    === demo_top ===

       Number of wires:                 12
       Number of cells:                 23
            23  304.042   cells
             1    5.005   sky130_fd_sc_hd__a21oi_1
            10  120.000   sky130_fd_sc_hd__dfrtp_1
             5   60.000   sky130_fd_sc_hd__inv_1

    """
)


def _seed_area_inputs(ip_dir: Path) -> None:
    out = ip_dir / "syn" / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "syn.log").write_text(SAMPLE_SYN_LOG, encoding="utf-8")
    (out / "synth.v").write_text("module demo_top(); endmodule\n", encoding="utf-8")


def test_parse_area_artifact_parity(tmp_path: Path) -> None:
    py_root = tmp_path / "py"
    py_ip = _make_ip(py_root)
    _seed_area_inputs(py_ip)

    py = _run([sys.executable, str(SYN / "parse_area.py"), "demo_ip"], py_root)

    assert py.returncode == 0, py.stderr
    py_json = json.loads((py_ip / "syn" / "out" / "area.json").read_text())
    # The parsed values are the ones we seeded.
    assert py_json["total_cells"] == 23
    assert py_json["by_kind"]["sequential"]["cells"] == 10  # dfrtp


def test_parse_area_missing_log_rc(tmp_path: Path) -> None:
    py_root = tmp_path / "py"
    _make_ip(py_root)
    py = _run([sys.executable, str(SYN / "parse_area.py"), "demo_ip"], py_root)
    assert py.returncode == 2


# --------------------------------------------------------------------------- #
# Pure writer: write_report — markdown (minus the embedded timestamp)
# --------------------------------------------------------------------------- #
def _strip_date(md: str) -> str:
    return re.sub(r"^- date    :.*$", "- date    : <DATE>", md, flags=re.M)


def test_write_report_artifact_parity(tmp_path: Path) -> None:
    py_root = tmp_path / "py"
    py_ip = _make_ip(py_root)
    area = {
        "top": "demo_top",
        "corner": "sky130_fd_sc_hd__ss_100C_1v40.lib",
        "total_cells": 23,
        "total_area_um2": 304.042,
        "by_kind": {
            "sequential": {"cells": 10, "area_um2": None},
            "combinational": {"cells": 13, "area_um2": None},
        },
        "by_cell": {"sky130_fd_sc_hd__inv_1": 5, "sky130_fd_sc_hd__dfrtp_1": 10},
    }
    out = py_ip / "syn" / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "area.json").write_text(json.dumps(area), encoding="utf-8")
    (out / "syn.log").write_text("Warning: something\n", encoding="utf-8")
    (out / "synth.v").write_text("module demo_top(); endmodule\n", encoding="utf-8")

    py = _run([sys.executable, str(SYN / "write_report.py"), "demo_ip"], py_root)

    assert py.returncode == 0, py.stderr
    py_md = _strip_date((py_ip / "syn" / "out" / "syn.report.md").read_text())
    # Pinned report content reflects the seeded area.json (date masked).
    assert "demo_top" in py_md
    assert "23" in py_md  # total cells
    assert "- date    : <DATE>" in py_md


# --------------------------------------------------------------------------- #
# preflight — diagnostics + rc (tools may/may not be present → rc 0/3/4)
# --------------------------------------------------------------------------- #
def test_preflight_no_ip(tmp_path: Path) -> None:
    """No IP arg: env + tool diagnostics; rc depends on yosys presence."""
    py = _run([sys.executable, str(SYN / "preflight.py")], tmp_path, extra_path=None)
    # rc 3 if required yosys missing, 0/4 if present.
    assert py.returncode in (0, 3, 4)
    assert "[SYN PREFLIGHT]" in py.stdout


def test_preflight_with_ip(tmp_path: Path) -> None:
    py_root = tmp_path / "py"
    _make_ip(py_root)
    py = _run([sys.executable, str(SYN / "preflight.py"), "demo_ip"], py_root)
    assert py.returncode in (0, 3, 4)
    assert "[SYN PREFLIGHT]" in py.stdout
    assert "IP dir: OK demo_ip" in py.stdout


def test_preflight_missing_ip_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "preflight.py"), "nope_ip"], tmp_path)
    assert py.returncode == 2  # IP dir missing


# --------------------------------------------------------------------------- #
# run_yosys — PATH-stub (argv log + artifacts + rc) and tool-missing
# --------------------------------------------------------------------------- #
def _run_yosys_stub_body(net_rel: str) -> str:
    """Stub yosys: honour ``-l <log>`` by writing a canned log, plus synth.v."""
    return textwrap.dedent(
        f"""\
        log = ""
        prev = ""
        for a in argv:
            if prev == "-l":
                log = a
            prev = a
        if log:
            Path(log).write_text("canned yosys log\\n", encoding="utf-8")
        net = {net_rel!r}
        Path(net).parent.mkdir(parents=True, exist_ok=True)
        Path(net).write_text("module demo_top(); endmodule\\n", encoding="utf-8")
        print("stub yosys stdout")
        """
    )


def test_run_yosys_stub_argv_and_rc(tmp_path: Path) -> None:
    py_root = tmp_path / "py"
    py_ip = _make_ip(py_root)
    # run.ys must exist for run_yosys
    (py_ip / "syn" / "out").mkdir(parents=True, exist_ok=True)
    (py_ip / "syn" / "run.ys").write_text("stat\n", encoding="utf-8")

    py_argv = tmp_path / "py_argv.log"
    py_stub = tmp_path / "py_bin"
    net_rel = "demo_ip/syn/out/synth.v"
    _make_stub(py_stub, "yosys", py_argv, _run_yosys_stub_body(net_rel))

    py = _run([sys.executable, str(SYN / "run_yosys.py"), "demo_ip"], py_root, extra_path=str(py_stub))

    assert py.returncode == 0, py.stderr
    # argv: the stub records "yosys -l <log> <run.ys>".
    py_args = py_argv.read_text().replace(str(py_root), "<ROOT>")
    assert "-l " in py_args
    assert "/syn/run.ys" in py_args
    # wrote a syn.log
    assert (py_ip / "syn" / "out" / "syn.log").is_file()


def test_run_yosys_tool_missing_rc(tmp_path: Path) -> None:
    """No yosys on PATH → rc 3 (tool-missing path)."""
    py_root = tmp_path / "py"
    py_ip = _make_ip(py_root)
    (py_ip / "syn").mkdir(parents=True, exist_ok=True)
    (py_ip / "syn" / "run.ys").write_text("stat\n", encoding="utf-8")

    # Build a minimal PATH that contains python but deliberately NO yosys, so the
    # tool-missing branch is exercised deterministically even when the host has
    # yosys installed.
    minimal = tmp_path / "minbin"
    minimal.mkdir()
    for tool in (sys.executable, shutil.which("python3"), shutil.which("env")):
        if tool and Path(tool).exists():
            link = minimal / Path(tool).name
            if not link.exists():
                os.symlink(tool, link)
    min_path = str(minimal)

    py = _run(
        [sys.executable, str(SYN / "run_yosys.py"), "demo_ip"],
        py_root,
        override_path=min_path,
    )
    assert py.returncode == 3, py.stderr
    assert "yosys not on PATH" in py.stderr


# --------------------------------------------------------------------------- #
# run_synth — PATH-stub (yosys -p script, argv, artifacts, rc)
# --------------------------------------------------------------------------- #
_RUN_SYNTH_STUB = r'''
script = ""
prev = ""
for a in argv:
    if prev == "-p":
        script = a
    prev = a
print("Printing statistics")
print("   Number of cells: 1")
# Pull write_verilog / write_json targets out of the script & touch them.
m_net = re.search(r'write_verilog -noattr -noexpr "([^"]*)"', script)
m_js = re.search(r'write_json "([^"]*)"', script)
if m_net:
    p = Path(m_net.group(1)); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("module demo_top(); endmodule\n", encoding="utf-8")
if m_js:
    p = Path(m_js.group(1)); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{}\n", encoding="utf-8")
'''


def test_run_synth_stub_parity(tmp_path: Path) -> None:
    py_root = tmp_path / "py"
    _make_ip(py_root)

    py_argv = tmp_path / "py_argv.log"
    py_stub = tmp_path / "py_bin"
    _make_stub(py_stub, "yosys", py_argv, _RUN_SYNTH_STUB)

    py = _run([sys.executable, str(SYN / "run_synth.py"), "demo_ip"], py_root, extra_path=str(py_stub))

    assert py.returncode == 0, py.stderr
    # The yosys -p script text recorded by the stub names the artifact targets.
    py_args = py_argv.read_text().replace(str(py_root), "<ROOT>")
    assert "write_verilog" in py_args and "write_json" in py_args
    # Artifacts created.
    assert (py_root / "demo_ip" / "syn" / "demo_ip.netlist.v").is_file()
    assert (py_root / "demo_ip" / "syn" / "demo_ip.synth.json").is_file()
    assert (py_root / "demo_ip" / "syn" / "synth.log").is_file()


def test_run_synth_unknown_flag_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "run_synth.py"), "demo_ip", "--bogus"], tmp_path)
    assert py.returncode == 2
    assert "unknown flag" in py.stderr


def test_run_synth_no_ip_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "run_synth.py")], tmp_path)
    assert py.returncode == 2


# --------------------------------------------------------------------------- #
# run_openroad — PATH-stub (TCL gen, argv, artifacts, rc) and error paths
# --------------------------------------------------------------------------- #
def test_run_openroad_missing_pdk_rc(tmp_path: Path) -> None:
    """Empty $HOME → ~/src/OpenROAD PDK absent → rc 1.

    We override HOME at an empty temp dir so the missing-PDK branch is
    exercised deterministically regardless of the host's real ~/src/OpenROAD.
    """
    py_root = tmp_path / "py"
    _make_ip(py_root)
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    py = _run(
        [sys.executable, str(SYN / "run_openroad.py"), "demo_ip"],
        py_root,
        env_extra={"HOME": str(empty_home)},
    )
    assert py.returncode == 1, py.stderr
    assert "missing PDK file" in py.stderr


def test_run_openroad_stub_tcl_and_argv_parity(tmp_path: Path) -> None:
    """Stub PDK (fake HOME) + stub openroad → pinned TCL markers, argv, rc.

    HOME points at a temp tree holding the three PDK files plus
    ``sky130hd.tracks``; a PATH-stub ``openroad`` logs its argv and creates the
    DEF its TCL names. We pin the generated openroad_run.tcl structural markers,
    the recorded argv, and the produced artifacts.  The wrappers resolve the
    temp root through ``/private`` on macOS, so absolute paths are asserted as
    substring markers, never byte-for-byte.
    """
    py_root = tmp_path / "py"
    py_ip = _make_ip(py_root)
    # Seed the synth netlist run_openroad requires.
    (py_ip / "syn").mkdir(parents=True, exist_ok=True)
    (py_ip / "syn" / "demo_ip.netlist.v").write_text(
        "module demo_top(); endmodule\n", encoding="utf-8"
    )

    fake_home = tmp_path / "fake_home"
    pdk = fake_home / "src" / "OpenROAD" / "test" / "sky130hd"
    pdk.mkdir(parents=True)
    for name in (
        "sky130_fd_sc_hd__tt_025C_1v80.lib",
        "sky130_fd_sc_hd__nom.tlef",
        "sky130_fd_sc_hd_merged.lef",
        "sky130hd.tracks",
    ):
        (pdk / name).write_text("# stub pdk\n", encoding="utf-8")
    home_env = {"HOME": str(fake_home)}

    py_argv = tmp_path / "py_or.log"
    py_stub = tmp_path / "py_orbin"
    # Stub openroad: log argv, create the DEF named by ``write_def`` in the TCL.
    stub_body = r'''
tcl = argv[-1]
text = Path(tcl).read_text(encoding="utf-8")
m = re.search(r'^write_def (.*)$', text, re.M)
if m:
    p = Path(m.group(1).strip()); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("stub def\n", encoding="utf-8")
print("Design area 1 um^2 1% utilization")
print("stub openroad ok")
'''
    _make_stub(py_stub, "openroad", py_argv, stub_body)

    py = _run(
        [sys.executable, str(SYN / "run_openroad.py"), "demo_ip"],
        py_root,
        extra_path=str(py_stub),
        env_extra=home_env,
    )
    assert py.returncode == 0, (py.stdout, py.stderr)

    # Pinned structural content of the generated TCL (absolute paths → markers).
    tcl = (py_ip / "pnr" / "openroad_run.tcl").read_text()
    assert "read_liberty " in tcl and "sky130_fd_sc_hd__tt_025C_1v80.lib" in tcl
    assert "link_design demo_ip_wrapper" in tcl
    assert "read_verilog " in tcl and "demo_ip/syn/demo_ip.netlist.v" in tcl
    assert "read_sdc " in tcl and "demo_ip/sdc/demo_ip.sdc" in tcl
    assert "initialize_floorplan" in tcl
    assert "global_placement" in tcl and "detailed_placement" in tcl
    assert "write_def " in tcl and "demo_ip/pnr/demo_ip.def" in tcl
    # argv parity (openroad -no_init -exit <tcl>).
    py_args = py_argv.read_text()
    assert py_args.startswith("-no_init -exit ")
    assert "demo_ip/pnr/openroad_run.tcl" in py_args
    # DEF + log + report artifacts.
    assert (py_root / "demo_ip" / "pnr" / "demo_ip.def").is_file()
    assert (py_root / "demo_ip" / "pnr" / "openroad.log").is_file()
    assert (py_root / "demo_ip" / "pnr" / "pnr_report.txt").is_file()


def test_run_openroad_unknown_flag_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "run_openroad.py"), "--bogus"], tmp_path)
    assert py.returncode == 2


def test_run_openroad_no_ip_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "run_openroad.py")], tmp_path)
    assert py.returncode == 2


# --------------------------------------------------------------------------- #
# run_sta — usage/flag/rc + stub-path (TCL + argv)
# --------------------------------------------------------------------------- #
def test_run_sta_no_liberty_rc(tmp_path: Path) -> None:
    """No liberty candidate found → rc 1."""
    py_root = tmp_path / "py"
    _make_ip(py_root)
    # Point at an explicit non-existent liberty so the default search is skipped
    # and the run immediately hits the "no liberty file" branch.
    py = _run(
        [sys.executable, str(SYN / "run_sta.py"), "demo_ip", "--liberty", str(tmp_path / "nope.lib")],
        py_root,
    )
    assert py.returncode == 1
    assert "no liberty file" in py.stderr


def test_run_sta_stub_tcl_and_argv_parity(tmp_path: Path) -> None:
    """Stub yosys (run_synth delegate) + stub sta → sta_run.tcl + argv markers."""
    py_root = tmp_path / "py"
    py_ip = _make_ip(py_root)

    # Explicit liberty so the default candidate search is bypassed.
    liberty = tmp_path / "stub.lib"
    liberty.write_text("/* stub liberty */\n", encoding="utf-8")

    py_argv = tmp_path / "py_sta.log"
    py_stub = tmp_path / "py_stabin"

    # Stub yosys -p (for run_synth delegate): create the netlist its script names.
    _make_stub(py_stub, "yosys", py_argv, _RUN_SYNTH_STUB)
    _make_stub(py_stub, "sta", py_argv, 'print("stub sta report")')

    py = _run(
        [sys.executable, str(SYN / "run_sta.py"), "demo_ip", "--liberty", str(liberty)],
        py_root,
        extra_path=str(py_stub),
    )
    assert py.returncode == 0, (py.stdout, py.stderr)

    # Pinned structural content of the generated OpenSTA TCL (paths → markers).
    tcl = (py_ip / "syn" / "sta_run.tcl").read_text().replace(str(liberty), "<LIB>")
    assert "read_liberty <LIB>" in tcl
    assert "link_design demo_top" in tcl
    assert "read_verilog " in tcl and "demo_ip/syn/demo_ip.netlist.v" in tcl
    assert "report_checks -path_delay max" in tcl
    assert "report_checks -path_delay min" in tcl
    assert "report_tns" in tcl and "report_wns" in tcl
    # The stub log holds both yosys -p ... and sta -no_init -exit ... argv lines.
    py_args = py_argv.read_text()
    assert "write_verilog" in py_args and "write_json" in py_args
    assert "-no_init -exit " in py_args and "demo_ip/syn/sta_run.tcl" in py_args
    assert (py_root / "demo_ip" / "syn" / "sta_report.txt").is_file()


def test_run_sta_unknown_flag_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "run_sta.py"), "demo_ip", "--bogus"], tmp_path)
    assert py.returncode == 2
    assert "unknown flag" in py.stderr


def test_run_sta_no_ip_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "run_sta.py")], tmp_path)
    assert py.returncode == 2


# --------------------------------------------------------------------------- #
# auto_syn — orchestrator: usage + missing-IP rc + full pipeline
# --------------------------------------------------------------------------- #
def test_auto_syn_no_ip_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "auto_syn.py")], tmp_path)
    assert py.returncode == 2


def test_auto_syn_missing_ip_dir_rc(tmp_path: Path) -> None:
    py = _run([sys.executable, str(SYN / "auto_syn.py"), "nope_ip"], tmp_path)
    assert py.returncode == 2


def test_auto_syn_full_pipeline_stub_parity(tmp_path: Path) -> None:
    """End-to-end pipeline with a stub yosys: pinned HANDOFF + artifacts."""
    py_root = tmp_path / "py"
    _make_ip(py_root)

    py_argv = tmp_path / "py_argv.log"
    py_stub = tmp_path / "py_bin"
    # Stub yosys for the auto_syn pipeline: honour -l <log>, write a stat block
    # into the log AND the synth.v the write_yosys_script run.ys names.
    stub_body = r'''
log = ""
prev = ""
for a in argv:
    if prev == "-l":
        log = a
    prev = a
if log:
    Path(log).write_text(
        "=== demo_top ===\n\n"
        "      1    5.005   cells\n"
        "      1    5.005   sky130_fd_sc_hd__inv_1\n",
        encoding="utf-8",
    )
# The run.ys names an absolute write_verilog target; recover & create it.
script = argv[-1]
text = Path(script).read_text(encoding="utf-8")
m = re.search(r'write_verilog -noattr "([^"]*)"', text)
if m:
    p = Path(m.group(1)); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("module demo_top(); endmodule\n", encoding="utf-8")
print("stub yosys ok")
'''
    _make_stub(py_stub, "yosys", py_argv, stub_body)

    # The stub dir is prepended to PATH, so it deterministically shadows any
    # real yosys on the host — the pipeline runs unconditionally.
    py = _run([sys.executable, str(SYN / "auto_syn.py"), "demo_ip"], py_root, extra_path=str(py_stub))

    assert py.returncode == 0, (py.stdout, py.stderr)
    # Final HANDOFF line (root-normalised → pinned marker content).
    py_handoff = [ln for ln in py.stdout.splitlines() if "SYN HANDOFF" in ln]
    assert py_handoff, py.stdout
    assert py_handoff[0].replace(str(py_root), "<ROOT>") == (
        "[SYN HANDOFF] demo_ip/syn/out/synth.v ready "
        "(cells=1, FFs=0, area=5.005 μm²) — run /sta"
    )
    # area.json + report produced.
    assert (py_root / "demo_ip" / "syn" / "out" / "area.json").is_file()
    assert (py_root / "demo_ip" / "syn" / "out" / "syn.report.md").is_file()
