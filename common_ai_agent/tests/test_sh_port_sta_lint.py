"""Pinned regression tests for the STA / STA-post / lint python ports.

Each ``*.py`` under ``workflow/{sta,sta-post,lint}/scripts/`` is exercised over a
fixture; we assert the PINNED exit code plus the key output / artifact markers
captured from the (formerly green) sh-vs-py differential parity run. The bash
originals are being removed, so these tests run only the ``.py`` side.

Technique
---------
  * PATH-stub fake tools (``sta``) are tiny *python* executables that record argv
    and emit the canned reports the wrappers parse, so artifacts are
    deterministic without the real OpenSTA — and we exercise the tool-missing
    path too.
  * For the parse_*/write_report scripts we feed canned report files and pin the
    parsed JSON / markdown content the script produces.
  * Real ``verilator`` is used when present (it is installed on the dev machine);
    its non-deterministic banner / "Walltime …" telemetry is masked and only the
    deterministic summary tail is pinned.

The ``grep -oP`` scripts (``auto_lint.py``, ``lint/write_report.py``) implement
GNU semantics natively in python, so the former GNU-grep emulation stub is no
longer needed; their pinned output reflects those GNU semantics directly.

Volatile lines (absolute liberty/temp paths, cwd, embedded timestamps) are
normalised before pinning rather than compared byte-for-byte.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
STA = REPO / "workflow" / "sta" / "scripts"
POST = REPO / "workflow" / "sta-post" / "scripts"
LINT = REPO / "workflow" / "lint" / "scripts"

_WALLTIME = re.compile(r"Walltime.*$", re.M)
_DATE = re.compile(r"^- date    :.*$", re.M)
_RPT_DATE = re.compile(r"^Date  :.*$", re.M)
_TS = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _make_exec(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _run_py(script: Path, args, cwd, env=None):
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )


def _base_env(extra=None):
    env = dict(os.environ)
    env.pop("HOOK_CMD_ARGS", None)
    env.pop("HOOK_TOOL_ARGS", None)
    env.pop("HOOK_TOOL_OUTPUT", None)
    if extra:
        env.update(extra)
    return env


# Fake OpenSTA (python, portable) that records argv and emits canned reports
# parsed from run.tcl. Mirrors the canned content the wrappers expect.
_FAKE_STA = r"""#!/usr/bin/env python3
import os, re, sys

argv = sys.argv[1:]
argv_file = os.environ.get("STA_ARGV_FILE")
if argv_file:
    with open(argv_file, "a", encoding="utf-8") as fh:
        fh.write("ARGV: " + " ".join(argv) + "\n")

tcl = argv[-1]
text = open(tcl, encoding="utf-8").read()
m = re.search(r"^.*setup\.rpt.*$", text, re.M)
target = m.group(0).split("> ", 1)[1].strip()
outdir = os.path.dirname(target)

slack = os.environ.get("FAKE_SETUP_SLACK", "0.500")
with open(os.path.join(outdir, "setup.rpt"), "w", encoding="utf-8") as fh:
    fh.write("Startpoint: ra\nEndpoint: rb\nPath Group: clk\n   %s   slack (MET)\n" % slack)
with open(os.path.join(outdir, "hold.rpt"), "w", encoding="utf-8") as fh:
    fh.write("Startpoint: rc\nEndpoint: rd\nPath Group: clk\n   0.100   slack (MET)\n")
with open(os.path.join(outdir, "timing.rpt"), "w", encoding="utf-8") as fh:
    fh.write("timing\n")
if "skew.rpt" in text:
    with open(os.path.join(outdir, "skew.rpt"), "w", encoding="utf-8") as fh:
        fh.write("clock clk\n  max skew = 0.020 ns\n")

print("wns %s" % slack)
print("tns 0.0")
sys.exit(int(os.environ.get("FAKE_STA_RC", "0")))
"""


# --------------------------------------------------------------------------- #
# sanity: every owned .py exists and compiles
# --------------------------------------------------------------------------- #
OWNED = {
    STA: ["auto_sta", "run_opensta", "parse_wns", "write_report", "write_sdc", "write_sta_tcl"],
    POST: ["auto_sta_post", "parse_wns", "preflight", "run_sta_post", "write_report", "write_sta_post_tcl"],
    LINT: ["auto_lint", "error_log", "lint_all", "lint_file", "run_full_lint", "write_report"],
}


@pytest.mark.parametrize(
    "d,name",
    [(d, n) for d, names in OWNED.items() for n in names],
)
def test_py_port_exists_and_compiles(d, name):
    py = d / f"{name}.py"
    assert py.is_file(), f"missing port {py}"
    r = subprocess.run([sys.executable, "-m", "py_compile", str(py)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# --------------------------------------------------------------------------- #
# STA: write_sta_tcl
# --------------------------------------------------------------------------- #
def _sta_ip(tmp_path: Path, ip="myip") -> Path:
    root = tmp_path
    _write(root / ip / "syn" / "out" / "synth.v", "module my_top; endmodule\n")
    _write(root / ip / "sta" / "out" / f"{ip}.sdc", "# sdc\n")
    _write(root / ip / "yaml" / f"{ip}.ssot.yaml", "top_module:\n  name: my_top\n")
    return root


def test_write_sta_tcl_identical(tmp_path):
    root = _sta_ip(tmp_path)
    lib = _write(tmp_path / "fake.lib", "lib\n")
    env = _base_env({"SKY130_LIB": str(lib)})

    py = _run_py(STA / "write_sta_tcl.py", ["myip"], root, env)
    tcl = (root / "myip" / "sta" / "run.tcl").read_text().replace(str(lib), "<LIB>")

    assert py.returncode == 0
    assert py.stdout == "[STA] wrote myip/sta/run.tcl (top=my_top)\n"
    # Pinned structural content of the generated TCL (liberty path normalised).
    assert "# IP: myip   top: my_top" in tcl
    assert "read_liberty <LIB>" in tcl
    assert "read_verilog myip/syn/out/synth.v" in tcl
    assert "link_design my_top" in tcl
    assert "read_sdc myip/sta/out/myip.sdc" in tcl
    assert "> myip/sta/out/setup.rpt" in tcl
    assert "> myip/sta/out/hold.rpt" in tcl
    assert "report_wns" in tcl and "report_tns" in tcl


def test_write_sta_tcl_usage(tmp_path):
    py = _run_py(STA / "write_sta_tcl.py", [], tmp_path, _base_env())
    assert py.returncode == 2
    assert py.stderr == "[STA] usage: write_sta_tcl.py <ip_name>\n"


def test_write_sta_tcl_missing_netlist(tmp_path):
    _write(tmp_path / "myip" / "sta" / "out" / "myip.sdc", "# sdc\n")
    py = _run_py(STA / "write_sta_tcl.py", ["myip"], tmp_path, _base_env())
    assert py.returncode == 5
    assert py.stderr == "[STA] missing myip/syn/out/synth.v\n"


# --------------------------------------------------------------------------- #
# STA: write_sdc
# --------------------------------------------------------------------------- #
def test_write_sdc_identical(tmp_path):
    ssot = (
        "top_module:\n  name: my_top\n"
        "clocks:\n  - name: clk\n    source_port: clk\n    period_ns: 5.0\n"
        "resets:\n  - name: rst_n\n    source_port: rst_n\n    sync_async: async\n"
        "false_paths:\n  - from: a\n    to: b\n"
        "multicycle_paths:\n  - cycles: 3\n    kind: setup\n    from: x\n    to: y\n"
        "io_delay:\n  input_pct: 0.15\n  output_pct: 0.25\n"
    )
    _write(tmp_path / "myip" / "yaml" / "myip.ssot.yaml", ssot)
    py = _run_py(STA / "write_sdc.py", ["myip"], tmp_path, _base_env())
    sdc = (tmp_path / "myip" / "sta" / "out" / "myip.sdc").read_text()
    assert py.returncode == 0
    assert py.stdout == "[STA] wrote myip/sta/out/myip.sdc (1 clocks)\n"
    # Pinned SDC content reflecting the seeded SSOT.
    assert "create_clock -name clk -period 5.0 [get_ports clk]" in sdc
    assert "set_input_delay  -clock clk 0.750 [all_inputs -no_clocks]" in sdc
    assert "set_output_delay -clock clk 1.250 [all_outputs]" in sdc
    assert "set_false_path -from [get_ports rst_n]" in sdc
    assert "set_false_path -from [get_ports a] -to [get_ports b]" in sdc
    assert "set_multicycle_path 3 -setup -from [get_ports x] -to [get_ports y]" in sdc


def test_write_sdc_empty_clocks_aborts(tmp_path):
    _write(tmp_path / "myip" / "yaml" / "myip.ssot.yaml", "top_module:\n  name: my_top\n")
    py = _run_py(STA / "write_sdc.py", ["myip"], tmp_path, _base_env())
    assert py.returncode == 7
    assert py.stderr == "[STA] SSOT clocks[] is empty — STA will be meaningless. Aborting.\n"


# --------------------------------------------------------------------------- #
# STA: parse_wns + write_report (canned reports)
# --------------------------------------------------------------------------- #
def _seed_sta_reports(tmp_path, ip="myip"):
    out = tmp_path / ip / "sta" / "out"
    _write(out / f"{ip}.sdc", "create_clock -name clk -period 5.0 [get_ports clk]\n")
    _write(out / "setup.rpt", "Startpoint: ra\nEndpoint: rb\nPath Group: clk\n   1.234   slack (MET)\n")
    _write(out / "hold.rpt", "Startpoint: rc\nEndpoint: rd\nPath Group: clk\n  -0.050   slack (VIOLATED)\n")
    _write(out / "sta.log", "wns 1.234\ntns 0.0\nWarning: w\nError: e\n")
    return out


def test_sta_parse_wns_identical(tmp_path):
    out = _seed_sta_reports(tmp_path)
    env = _base_env({"SKY130_LIB": "fake.lib"})
    py = _run_py(STA / "parse_wns.py", ["myip"], tmp_path, env)
    data = json.loads((out / "wns.json").read_text())
    assert py.returncode == 0
    assert py.stdout == (
        "[STA] wrote myip/sta/out/wns.json\n"
        "  clk@5.0ns: setup_wns=1.234 hold_wns=-0.05 setup_viol=0\n"
    )
    # Pinned parsed values from the seeded reports.
    assert data["top"] == "myip"
    assert data["corner"] == "fake.lib"
    clk = data["clocks"][0]
    assert clk["name"] == "clk" and clk["period_ns"] == 5.0
    assert clk["setup_wns_ns"] == 1.234
    assert clk["hold_wns_ns"] == -0.05
    assert clk["hold_violations"] == 1
    assert data["summary"]["all_setup_met"] is True
    assert data["summary"]["all_hold_met"] is False
    assert data["summary"]["worst_setup_path"] == "ra → rb (slack 1.234)"


def test_sta_write_report_identical(tmp_path):
    out = _seed_sta_reports(tmp_path)
    env = _base_env({"SKY130_LIB": "fake.lib"})
    _run_py(STA / "parse_wns.py", ["myip"], tmp_path, env)
    py = _run_py(STA / "write_report.py", ["myip"], tmp_path, env)
    rpt = _DATE.sub("- date    : X", (out / "sta.report.md").read_text())
    assert py.returncode == 0
    assert py.stdout == "[STA] wrote myip/sta/out/sta.report.md\n"
    # Pinned report content reflecting the seeded wns.json.
    assert "# STA Report — myip" in rpt
    assert "- date    : X" in rpt
    assert "- result  : **HOLD FAIL**" in rpt
    assert "| `clk` | 5.0 | 1.234 | 0.000 | 0 | -0.050 | 1 |" in rpt
    assert "- setup: ra → rb (slack 1.234)" in rpt
    assert "- **Error: e**" in rpt


# --------------------------------------------------------------------------- #
# STA: run_opensta (PATH-stub fake sta + tool-missing)
# --------------------------------------------------------------------------- #
def test_run_opensta_fake_tool(tmp_path):
    _write(tmp_path / "myip" / "sta" / "run.tcl", "# tcl\nreport_checks ... > x/setup.rpt\n")
    bindir = tmp_path / "bin"
    _make_exec(
        bindir / "sta",
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        'f = os.environ["STA_ARGV_FILE"]\n'
        'open(f, "a").write("ARGV: " + " ".join(sys.argv[1:]) + "\\n")\n'
        'for i in range(1, 201):\n    print("line %d" % i)\n'
        "sys.exit(7)\n",
    )
    lib = _write(tmp_path / "fake.lib", "lib\n")

    env = _base_env({
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "SKY130_LIB": str(lib),
        "STA_ARGV_FILE": str(tmp_path / "argv_py"),
    })
    py = _run_py(STA / "run_opensta.py", ["myip"], tmp_path, env)
    log = (tmp_path / "myip" / "sta" / "out" / "sta.log").read_text()

    assert py.returncode == 7
    # Argv: the wrapper invokes sta with the OpenSTA flags + the run.tcl.
    assert (tmp_path / "argv_py").read_text() == "ARGV: -no_init -no_splash -exit myip/sta/run.tcl\n"
    # Full log captured (200 lines); stdout tails the log + the rc line.
    assert len(log.splitlines()) == 200
    assert log.splitlines()[-1] == "line 200"
    assert py.stdout.startswith("line 81\n")  # tail -120 of 200
    assert py.stdout.endswith("[STA] sta rc=7 log=myip/sta/out/sta.log\n")
    assert py.stderr == ""


def test_run_opensta_tool_missing(tmp_path):
    _write(tmp_path / "myip" / "sta" / "run.tcl", "# tcl\n")
    lib = _write(tmp_path / "fake.lib", "lib\n")
    env = _base_env({"PATH": "/usr/bin:/bin", "SKY130_LIB": str(lib)})
    py = _run_py(STA / "run_opensta.py", ["myip"], tmp_path, env)
    assert py.returncode == 3
    assert py.stderr == "[STA TOOL MISSING] OpenSTA 'sta' not on PATH\n"


# --------------------------------------------------------------------------- #
# STA: auto_sta full pipeline with fake sta
# --------------------------------------------------------------------------- #
def test_auto_sta_pipeline(tmp_path):
    root = _sta_ip(tmp_path)
    _write(root / "myip" / "yaml" / "myip.ssot.yaml",
           "top_module:\n  name: my_top\nclocks:\n  - name: clk\n    source_port: clk\n    period_ns: 5.0\n")
    rtl = _write(root / "myip" / "rtl" / "x.sv", "module x; endmodule\n")
    os.utime(rtl, (0, 0))  # ancient, so not stale vs netlist
    bindir = root / "bin"
    _make_exec(bindir / "sta", _FAKE_STA)
    lib = _write(root / "fake.lib", "lib\n")
    env = _base_env({"PATH": f"{bindir}:{os.environ['PATH']}", "SKY130_LIB": str(lib)})

    py = _run_py(STA / "auto_sta.py", ["myip"], root, env)
    out = root / "myip" / "sta" / "out"
    arts = {p.name for p in out.iterdir()}

    assert py.returncode == 0
    assert py.stderr == ""
    # Pinned pipeline stdout markers (absolute liberty path is volatile → marker).
    assert "[STA] wrote myip/sta/run.tcl (top=my_top)" in py.stdout
    assert "[STA] sta rc=0 log=myip/sta/out/sta.log" in py.stdout
    assert "[STA] wrote myip/sta/out/wns.json" in py.stdout
    assert "[STA RESULT] PASS — clk@5.0ns: setup_wns=0.500 hold_wns=0.100" in py.stdout
    # Pipeline materialises the full artifact set.
    assert {"setup.rpt", "hold.rpt", "timing.rpt", "sta.log", "wns.json", "sta.report.md"} <= arts
    assert (root / "myip" / "sta" / "run.tcl").is_file()


# --------------------------------------------------------------------------- #
# STA-POST: write_sta_post_tcl, preflight, parse_wns, write_report, auto
# --------------------------------------------------------------------------- #
def _post_ip(tmp_path, ip="myip"):
    _write(tmp_path / ip / "pnr" / "out" / "routed.v", "module my_top; endmodule\n")
    _write(tmp_path / ip / "pnr" / "out" / "routed.spef", "SPEF DATA\n")
    _write(tmp_path / ip / "sta" / "out" / f"{ip}.sdc", "create_clock -name clk -period 5.0 [get_ports clk]\n")
    _write(tmp_path / ip / "yaml" / f"{ip}.ssot.yaml", "top_module:\n  name: my_top\n")
    return tmp_path


def test_write_sta_post_tcl_identical(tmp_path):
    _post_ip(tmp_path)
    lib = _write(tmp_path / "fake.lib", "lib\n")
    env = _base_env({"SKY130_LIB": str(lib)})
    py = _run_py(POST / "write_sta_post_tcl.py", ["myip"], tmp_path, env)
    tcl = (tmp_path / "myip" / "sta-post" / "run.tcl").read_text().replace(str(lib), "<LIB>")
    assert py.returncode == 0
    assert py.stdout == "[STA-POST] wrote myip/sta-post/run.tcl (top=my_top)\n"
    # Pinned post-route TCL content (liberty path normalised).
    assert "mode: post_route (parasitic-aware)" in tcl
    assert "read_liberty <LIB>" in tcl
    assert "read_verilog myip/pnr/out/routed.v" in tcl
    assert "read_spef myip/pnr/out/routed.spef" in tcl
    assert "$scan_en_ports" in tcl  # literal Tcl var preserved
    assert "set_case_analysis 0 $scan_en_ports" in tcl
    assert "> myip/sta-post/out/skew.rpt" in tcl


def test_preflight_ok_and_errors(tmp_path):
    _post_ip(tmp_path)
    bindir = tmp_path / "bin"
    _make_exec(bindir / "sta", "#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
    lib = _write(tmp_path / "fake.lib", "lib\n")
    good_path = f"{bindir}:{os.environ['PATH']}"

    env = _base_env({"PATH": good_path, "SKY130_LIB": str(lib)})
    py = _run_py(POST / "preflight.py", ["myip"], tmp_path, env)
    assert py.returncode == 0
    # Pinned preflight markers (cwd / absolute paths are volatile → markers).
    assert "[STA-POST PREFLIGHT] routed_v=myip/pnr/out/routed.v" in py.stdout
    assert "[STA-POST PREFLIGHT] routed_spef=myip/pnr/out/routed.spef size=" in py.stdout
    assert "[STA-POST PREFLIGHT] sdc=myip/sta/out/myip.sdc" in py.stdout
    assert py.stdout.rstrip().endswith("[STA-POST PREFLIGHT] OK")
    assert py.stderr == ""

    # error-path exit codes + pinned stderr markers
    cases = {
        2: (_base_env({"PATH": good_path, "SKY130_LIB": str(lib)}),
            "[STA-POST PREFLIGHT] IP dir missing: ghost\n"),
        3: (_base_env({"PATH": "/usr/bin:/bin", "SKY130_LIB": str(lib)}),
            "[STA-POST TOOL MISSING] OpenSTA 'sta' not on PATH\n"),
        4: (_base_env({"PATH": good_path, "SKY130_LIB": "/nope.lib"}),
            "[STA-POST MISSING PDK] $SKY130_LIB unreadable: /nope.lib\n"),
    }
    for rc, (e, expect_err) in cases.items():
        arg = "ghost" if rc == 2 else "myip"
        p = _run_py(POST / "preflight.py", [arg], tmp_path, e)
        assert p.returncode == rc
        assert p.stderr == expect_err


def _seed_post_reports(tmp_path, ip="myip", with_pre=True):
    out = tmp_path / ip / "sta-post" / "out"
    _write(tmp_path / ip / "sta" / "out" / f"{ip}.sdc", "create_clock -name clk -period 5.0 [get_ports clk]\n")
    _write(out / "setup.rpt", "Startpoint: ra\nEndpoint: rb\nPath Group: clk\n  -0.250   slack (VIOLATED)\n")
    _write(out / "hold.rpt", "Startpoint: rc\nEndpoint: rd\nPath Group: clk\n   0.100   slack (MET)\n")
    _write(out / "skew.rpt", "clock clk\n  max skew = 0.030 ns\n  max latency = 0.500 ns\n")
    _write(out / "sta.log", "wns -0.250\ntns -0.250\n")
    if with_pre:
        pre = {
            "top": ip, "corner": "fake.lib",
            "clocks": [{"name": "clk", "period_ns": 5.0, "setup_wns_ns": -0.100,
                        "setup_tns_ns": -0.100, "setup_violations": 1,
                        "hold_wns_ns": 0.100, "hold_tns_ns": 0.0, "hold_violations": 0}],
            "summary": {"all_setup_met": False, "all_hold_met": True,
                        "worst_setup_path": "", "worst_hold_path": ""},
        }
        _write(tmp_path / ip / "sta" / "out" / "wns.json", json.dumps(pre, indent=2))
    return out


def test_post_parse_wns_identical(tmp_path):
    out = _seed_post_reports(tmp_path)
    env = _base_env({"SKY130_LIB": "fake.lib"})
    py = _run_py(POST / "parse_wns.py", ["myip"], tmp_path, env)
    data = json.loads((out / "wns.json").read_text())
    assert py.returncode == 0
    assert py.stdout == (
        "[STA-POST] wrote myip/sta-post/out/wns.json\n"
        "  clk@5.0ns: setup_wns=-0.25 hold_wns=0.1 skew=30.0ps\n"
    )
    assert data["mode"] == "post_route"
    clk = data["clocks"][0]
    assert clk["setup_wns_ns"] == -0.25
    assert clk["hold_wns_ns"] == 0.1


def test_post_write_report_with_delta(tmp_path):
    out = _seed_post_reports(tmp_path)
    env = _base_env({"SKY130_LIB": "fake.lib"})
    _run_py(POST / "parse_wns.py", ["myip"], tmp_path, env)
    py = _run_py(POST / "write_report.py", ["myip"], tmp_path, env)
    rpt = _DATE.sub("- date    : X", (out / "sta.report.md").read_text())
    assert py.returncode == 0
    assert py.stdout == "[STA-POST] wrote myip/sta-post/out/sta.report.md\n"
    # Pinned post-route report content incl. the pre-vs-post delta table.
    assert "# Post-Route STA Report — myip" in rpt
    assert "- mode    : **post_route** (parasitic-aware sign-off)" in rpt
    assert "- result  : **SETUP FAIL**" in rpt
    assert "| `clk` | 5.0 | -0.250 | -0.250 | 1 | 0.100 | 0 | 30.0 |" in rpt
    assert "## Pre-route /sta vs sign-off /sta-post" in rpt
    assert "| `clk` | -0.100 | -0.250 | -0.150 | 0.100 | 0.100 | 0.000 |" in rpt


def test_auto_sta_post_pipeline(tmp_path):
    _post_ip(tmp_path)
    bindir = tmp_path / "bin"
    _make_exec(bindir / "sta", _FAKE_STA)
    lib = _write(tmp_path / "fake.lib", "lib\n")
    env = _base_env({"PATH": f"{bindir}:{os.environ['PATH']}", "SKY130_LIB": str(lib)})

    py = _run_py(POST / "auto_sta_post.py", ["myip"], tmp_path, env)
    out = tmp_path / "myip" / "sta-post" / "out"
    arts = {p.name for p in out.iterdir()}

    assert py.returncode == 0
    assert py.stderr == ""
    # Pinned pipeline markers: preflight → tcl → sta → parse → report → result.
    assert "[STA-POST PREFLIGHT] OK" in py.stdout
    assert "[STA-POST] wrote myip/sta-post/run.tcl (top=my_top)" in py.stdout
    assert "[STA-POST] sta rc=0 log=myip/sta-post/out/sta.log" in py.stdout
    assert "[STA-POST] wrote myip/sta-post/out/wns.json" in py.stdout
    assert "[STA-POST RESULT] PASS (sign-off, parasitic-aware)" in py.stdout
    assert {"setup.rpt", "hold.rpt", "skew.rpt", "sta.log", "wns.json", "sta.report.md"} <= arts
    assert (tmp_path / "myip" / "sta-post" / "run.tcl").is_file()


# --------------------------------------------------------------------------- #
# LINT (real verilator where present)
# --------------------------------------------------------------------------- #
HAVE_VERILATOR = shutil.which("verilator") is not None


def _mask_walltime(text: str) -> str:
    return _WALLTIME.sub("Walltime X", text)


@pytest.mark.skipif(not HAVE_VERILATOR, reason="verilator not installed")
def test_lint_file_clean_and_warn(tmp_path):
    clean = _write(tmp_path / "clean.sv", "module clean (input logic a, output logic b);\n  assign b = a;\nendmodule\n")
    warn = _write(tmp_path / "warn.sv", "module warn (input logic [3:0] a, output logic b);\n  assign b = a;\nendmodule\n")
    # (file, expected rc, expected benchmark tail, expected stdout summary tail).
    cases = [
        (clean, 0, "lint_file=clean.sv errors=0 warnings=0\n", "clean.sv: 0 errors, 0 warnings\n"),
        (warn, 1, "lint_file=warn.sv errors=1 warnings=5\n", "warn.sv: 1 errors, 5 warnings\n"),
    ]
    for f, expect_rc, bench_tail, out_tail in cases:
        env = _base_env({"BENCHMARK_LOG": str(tmp_path / ("bm_" + f.stem))})
        py = _run_py(LINT / "lint_file.py", [f.name], tmp_path, env)
        assert py.returncode == expect_rc
        # Deterministic summary tail (verilator banner/Walltime telemetry masked).
        assert py.stdout.endswith(out_tail)
        bench = _TS.sub("TS", (tmp_path / ("bm_" + f.stem)).read_text())
        assert bench == "TS " + bench_tail


def test_lint_file_missing_and_usage(tmp_path):
    py = _run_py(LINT / "lint_file.py", ["nope.sv"], tmp_path, _base_env())
    assert py.returncode == 1
    assert py.stdout == "File not found: nope.sv\n"
    py = _run_py(LINT / "lint_file.py", [], tmp_path, _base_env())
    assert py.returncode == 1
    assert py.stdout == "Usage: /lint-file <file.sv>\n"


@pytest.mark.skipif(not HAVE_VERILATOR, reason="verilator not installed")
def test_lint_all(tmp_path):
    _write(tmp_path / "clean.sv", "module clean (input logic a, output logic b);\n  assign b = a;\nendmodule\n")
    _write(tmp_path / "warn.v", "module warn2 (input logic [3:0] a, output logic b);\n  assign b = a;\nendmodule\n")
    _write(tmp_path / "tb_foo.sv", "module tb_foo; endmodule\n")  # excluded
    env = _base_env({"BENCHMARK_LOG": str(tmp_path / "bm_py")})
    py = _run_py(LINT / "lint_all.py", [], tmp_path, env)
    # warn.v lints non-clean → non-zero rc; tb_foo.sv is excluded.
    assert py.returncode == 1
    bench = _TS.sub("TS", (tmp_path / "bm_py").read_text())
    assert bench == "TS lint_all errors=1 warnings=7\n"


def test_error_log(tmp_path):
    out = "line ok\n%Warning-FOO: bar\nsome Error here\nplain line"
    env = _base_env({"BENCHMARK_LOG": str(tmp_path / "eb_py"), "HOOK_TOOL_OUTPUT": out})
    py = _run_py(LINT / "error_log.py", [], tmp_path, env)
    assert py.returncode == 0
    bench = _TS.sub("TS", (tmp_path / "eb_py").read_text())
    # Only the Warning/Error lines are extracted into the issues log.
    assert bench == "TS lint_issues:\n  %Warning-FOO: bar\n  some Error here\n"

    # no issues in output → no file written
    env = _base_env({"BENCHMARK_LOG": str(tmp_path / "n_py"), "HOOK_TOOL_OUTPUT": "nothing"})
    _run_py(LINT / "error_log.py", [], tmp_path, env)
    assert not (tmp_path / "n_py").exists()


@pytest.mark.skipif(not HAVE_VERILATOR, reason="verilator not installed")
def test_auto_lint_gnu_grep_parity(tmp_path):
    """auto_lint.py implements the grep -oP (GNU) extraction natively. Pin the
    benchmark line it emits for a clean file from a HOOK_TOOL_ARGS path."""
    _write(tmp_path / "clean.sv", "module clean (input logic a, output logic b);\n  assign b = a;\nendmodule\n")
    env = _base_env({
        "BENCHMARK_LOG": str(tmp_path / "abm_py"),
        "HOOK_TOOL_ARGS": 'path="clean.sv"',
    })
    py = _run_py(LINT / "auto_lint.py", [], tmp_path, env)
    assert py.returncode == 0
    bench = _TS.sub("TS", (tmp_path / "abm_py").read_text())
    assert bench == "TS auto_lint file=clean.sv errors=0 warnings=0\n"


def test_auto_lint_no_file_no_log(tmp_path):
    env = _base_env({"BENCHMARK_LOG": str(tmp_path / "n_py"), "HOOK_TOOL_ARGS": "nothing"})
    py = _run_py(LINT / "auto_lint.py", [], tmp_path, env)
    assert py.returncode == 0
    assert not (tmp_path / "n_py").exists()


def test_write_report_gnu_grep_parity(tmp_path):
    """write_report.py extracts errors=/warnings= via grep -oP (GNU) semantics,
    implemented natively. Pin the generated report content + stdout echo."""
    log = _write(
        tmp_path / ".benchmark",
        "2026-01-01T00:00:00 lint_all errors=3 warnings=7\n"
        "2026-01-01T00:00:01 lint_issues:\n"
        "  %Warning-WIDTHTRUNC: foo\n"
        "2026-01-01T00:00:02 lint_file=x.sv errors=3 warnings=7\n",
    )
    _write(tmp_path / "clean.sv", "module clean(input a, output b); assign b=a; endmodule\n")
    env = _base_env({"BENCHMARK_LOG": str(log)})
    py = _run_py(LINT / "write_report.py", [], tmp_path, env)
    rpt = _RPT_DATE.sub("Date  : X", (tmp_path / "lint_report.txt").read_text())
    assert py.returncode == 0
    # Pinned report content (date masked).
    assert "=== Lint Report ===" in rpt
    assert "Result: 3 errors, 7 warnings" in rpt
    assert "2026-01-01T00:00:00 lint_all errors=3 warnings=7" in rpt
    assert "2026-01-01T00:00:02 lint_file=x.sv errors=3 warnings=7" in rpt
    assert "[Issues Log]" in rpt
    # stdout echoes the written report.
    out = _RPT_DATE.sub("Date  : X", py.stdout)
    assert out.startswith("Written: lint_report.txt\n")
    assert "Result: 3 errors, 7 warnings" in out


def test_run_full_lint_errors(tmp_path):
    # usage (no ip)
    py = _run_py(LINT / "run_full_lint.py", [], tmp_path, _base_env())
    assert py.returncode == 2
    assert py.stderr == "usage: run_full_lint.py <ip> [--root .]\n"

    # unknown flag
    py = _run_py(LINT / "run_full_lint.py", ["--bogus"], tmp_path, _base_env())
    assert py.returncode == 2
    assert py.stderr == "[run_full_lint] unknown flag: --bogus\n"

    # missing waiver (absolute path is volatile → marker)
    (tmp_path / "spi" / "rtl").mkdir(parents=True)
    py = _run_py(LINT / "run_full_lint.py", ["spi"], tmp_path, _base_env())
    assert py.returncode == 1
    assert py.stderr.startswith("[run_full_lint] missing waiver: ")
    assert py.stderr.rstrip().endswith("spi/rtl/spi_lint.vlt for template.")
    assert "spi/rtl/spi_lint.vlt" in py.stderr


@pytest.mark.skipif(not HAVE_VERILATOR, reason="verilator not installed")
def test_run_full_lint_real(tmp_path):
    _write(tmp_path / "spi" / "rtl" / "spi.sv",
           "module spi_top (input logic clk, input logic a, output logic b);\n  always_comb b = a;\nendmodule\n")
    _write(tmp_path / "spi" / "rtl" / "spi_lint.vlt", "`verilator_config\n")
    _write(tmp_path / "spi" / "yaml" / "spi.ssot.yaml", "top_module:\n  name: spi_top\n")
    py = _run_py(LINT / "run_full_lint.py", ["spi"], tmp_path, _base_env())
    log = _mask_walltime((tmp_path / "spi" / "lint" / "verilator_lint.log").read_text())
    out = _mask_walltime(py.stdout)
    # spi.sv has an unused signal → lint is not clean.
    assert py.returncode == 1
    # Deterministic verilator verdict markers (banner/Walltime masked).
    assert "%Error: Exiting due to 2 warning(s)" in log
    assert "[run_full_lint] G_LINT_CLEAN: FAIL — 3 warning(s)/error(s)" in out
