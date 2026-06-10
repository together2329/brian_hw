"""Differential equivalence tests for the STA / STA-post / lint .sh→.py ports.

Each owned bash script under workflow/{sta,sta-post,lint}/scripts/ has a same-named
.py beside it. These tests prove the port is behaviourally identical to the bash
original by running BOTH on the same fixtures and comparing stdout, stderr, exit
codes, and generated artifacts.

Technique:
  * PATH-stub fake tools (``sta``, ``verilator``) that record argv and emit canned
    output, so we can diff argv/rc/artifacts deterministically without the real
    EDA tools — and we exercise the tool-missing path too.
  * For the parse_*/write_report scripts we feed canned report files and compare
    the parsed JSON / markdown byte-for-byte.
  * Real ``verilator`` is used when present (it is installed on the dev machine);
    its non-deterministic "Walltime …" telemetry line is the only thing masked.

Documented, intentional divergences (asserted, not failures):
  * Usage strings echo the script's own basename, so ``foo.sh`` vs ``foo.py`` is
    expected; we compare with the basename normalised.
  * ``auto_lint.sh`` and ``write_report.sh`` use GNU-only ``grep -oP``. On a BSD
    grep host (macOS) the .sh silently degrades (empty match / "?" counts); the
    .py implements the *intended* GNU semantics (matching the house-style
    precedent of check_lint_disk.py). A bundled GNU-grep emulation stub proves the
    .sh == .py under GNU semantics.
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

BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(BASH is None, reason="bash not available")

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


def _run_sh(script: Path, args, cwd, env=None):
    return subprocess.run(
        [BASH, str(script), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )


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


def _norm_usage(text: str, sh_name: str) -> str:
    """Collapse the script basename so foo.sh / foo.py usage lines compare equal."""
    return text.replace(sh_name, sh_name.rsplit(".", 1)[0])


def _gnu_grep_stub(bindir: Path) -> None:
    """A `grep` shim that emulates GNU `grep -oP` (incl. \\K + lookbehind) via
    Python, delegating everything else to the real grep. Lets us prove the
    grep -oP scripts match under GNU semantics on a BSD host."""
    real = shutil.which("grep") or "/usr/bin/grep"
    body = (
        "#!/usr/bin/env python3\n"
        "import sys, re, subprocess\n"
        "args = sys.argv[1:]\n"
        "flags = [a for a in args if a.startswith('-') and a != '--']\n"
        "def has(f): return any(f in fl for fl in flags)\n"
        "if has('o') and has('P'):\n"
        "    nonflag = [a for a in args if not a.startswith('-')]\n"
        "    pat = nonflag[0]\n"
        "    data = sys.stdin.read()\n"
        "    out, rc = [], 1\n"
        "    if r'\\K' in pat:\n"
        "        pre, post = pat.split(r'\\K', 1)\n"
        "        rx = re.compile(pre + '(' + post + ')')\n"
        "        for line in data.split('\\n'):\n"
        "            for m in rx.finditer(line):\n"
        "                out.append(m.group(1)); rc = 0\n"
        "    else:\n"
        "        rx = re.compile(pat)\n"
        "        for line in data.split('\\n'):\n"
        "            for m in rx.finditer(line):\n"
        "                out.append(m.group(0)); rc = 0\n"
        "    sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        "    sys.exit(rc)\n"
        f"p = subprocess.run(['{real}'] + args, stdin=sys.stdin)\n"
        "sys.exit(p.returncode)\n"
    )
    _make_exec(bindir / "grep", body)


# Fake OpenSTA that records argv and emits canned reports parsed from run.tcl.
_FAKE_STA = r"""#!/usr/bin/env bash
echo "ARGV: $*" >> "${STA_ARGV_FILE:-/dev/null}"
TCL="${@: -1}"
OUTDIR=$(dirname "$(grep -m1 'setup.rpt' "$TCL" | sed 's/.*> //')")
printf 'Startpoint: ra\nEndpoint: rb\nPath Group: clk\n   %s   slack (MET)\n' "${FAKE_SETUP_SLACK:-0.500}" > "$OUTDIR/setup.rpt"
printf 'Startpoint: rc\nEndpoint: rd\nPath Group: clk\n   0.100   slack (MET)\n' > "$OUTDIR/hold.rpt"
printf 'timing\n' > "$OUTDIR/timing.rpt"
if grep -q skew.rpt "$TCL"; then
  printf 'clock clk\n  max skew = 0.020 ns\n' > "$OUTDIR/skew.rpt"
fi
echo "wns ${FAKE_SETUP_SLACK:-0.500}"
echo "tns 0.0"
exit "${FAKE_STA_RC:-0}"
"""


# --------------------------------------------------------------------------- #
# sanity: every owned .sh has a same-named .py
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
    sh = d / f"{name}.sh"
    py = d / f"{name}.py"
    assert sh.is_file(), f"missing source {sh}"
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
    env = _base_env({"SKY130_LIB": str(tmp_path / "fake.lib")})
    _write(tmp_path / "fake.lib", "lib\n")

    sh = _run_sh(STA / "write_sta_tcl.sh", ["myip"], root, env)
    sh_tcl = (root / "myip" / "sta" / "run.tcl").read_text()
    (root / "myip" / "sta" / "run.tcl").unlink()
    py = _run_py(STA / "write_sta_tcl.py", ["myip"], root, env)
    py_tcl = (root / "myip" / "sta" / "run.tcl").read_text()

    assert sh.returncode == py.returncode == 0
    assert sh_tcl == py_tcl
    assert sh.stdout == py.stdout
    assert sh.stderr == py.stderr


def test_write_sta_tcl_usage(tmp_path):
    sh = _run_sh(STA / "write_sta_tcl.sh", [], tmp_path, _base_env())
    py = _run_py(STA / "write_sta_tcl.py", [], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 2
    assert _norm_usage(sh.stderr, "write_sta_tcl.sh") == _norm_usage(py.stderr, "write_sta_tcl.py")


def test_write_sta_tcl_missing_netlist(tmp_path):
    _write(tmp_path / "myip" / "sta" / "out" / "myip.sdc", "# sdc\n")
    sh = _run_sh(STA / "write_sta_tcl.sh", ["myip"], tmp_path, _base_env())
    sh2 = tmp_path / "myip" / "sta" / "run.tcl"
    if sh2.exists():
        sh2.unlink()
    py = _run_py(STA / "write_sta_tcl.py", ["myip"], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 5
    assert sh.stderr == py.stderr


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
    sh = _run_sh(STA / "write_sdc.sh", ["myip"], tmp_path, _base_env())
    sdc_sh = (tmp_path / "myip" / "sta" / "out" / "myip.sdc").read_text()
    (tmp_path / "myip" / "sta" / "out" / "myip.sdc").unlink()
    py = _run_py(STA / "write_sdc.py", ["myip"], tmp_path, _base_env())
    sdc_py = (tmp_path / "myip" / "sta" / "out" / "myip.sdc").read_text()
    assert sh.returncode == py.returncode == 0
    assert sdc_sh == sdc_py
    assert sh.stdout == py.stdout


def test_write_sdc_empty_clocks_aborts(tmp_path):
    _write(tmp_path / "myip" / "yaml" / "myip.ssot.yaml", "top_module:\n  name: my_top\n")
    sh = _run_sh(STA / "write_sdc.sh", ["myip"], tmp_path, _base_env())
    py = _run_py(STA / "write_sdc.py", ["myip"], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 7
    assert sh.stderr == py.stderr


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
    sh = _run_sh(STA / "parse_wns.sh", ["myip"], tmp_path, env)
    js_sh = (out / "wns.json").read_text()
    (out / "wns.json").unlink()
    py = _run_py(STA / "parse_wns.py", ["myip"], tmp_path, env)
    js_py = (out / "wns.json").read_text()
    assert sh.returncode == py.returncode == 0
    assert json.loads(js_sh) == json.loads(js_py)
    assert js_sh == js_py
    assert sh.stdout == py.stdout


def test_sta_write_report_identical(tmp_path):
    out = _seed_sta_reports(tmp_path)
    env = _base_env({"SKY130_LIB": "fake.lib"})
    _run_sh(STA / "parse_wns.sh", ["myip"], tmp_path, env)
    sh = _run_sh(STA / "write_report.sh", ["myip"], tmp_path, env)
    rpt_sh = _DATE.sub("- date    : X", (out / "sta.report.md").read_text())
    (out / "sta.report.md").unlink()
    py = _run_py(STA / "write_report.py", ["myip"], tmp_path, env)
    rpt_py = _DATE.sub("- date    : X", (out / "sta.report.md").read_text())
    assert sh.returncode == py.returncode == 0
    assert rpt_sh == rpt_py
    assert sh.stdout == py.stdout


# --------------------------------------------------------------------------- #
# STA: run_opensta (PATH-stub fake sta + tool-missing)
# --------------------------------------------------------------------------- #
def test_run_opensta_fake_tool(tmp_path):
    _write(tmp_path / "myip" / "sta" / "run.tcl", "# tcl\nreport_checks ... > x/setup.rpt\n")
    bindir = tmp_path / "bin"
    _make_exec(
        bindir / "sta",
        '#!/usr/bin/env bash\necho "ARGV: $*" >> "$STA_ARGV_FILE"\n'
        'for i in $(seq 1 200); do echo "line $i"; done\nexit 7\n',
    )
    lib = _write(tmp_path / "fake.lib", "lib\n")

    env_sh = _base_env({"PATH": f"{bindir}:{os.environ['PATH']}", "SKY130_LIB": str(lib), "STA_ARGV_FILE": str(tmp_path / "argv_sh")})
    sh = _run_sh(STA / "run_opensta.sh", ["myip"], tmp_path, env_sh)
    log_sh = (tmp_path / "myip" / "sta" / "out" / "sta.log").read_text()

    env_py = dict(env_sh, STA_ARGV_FILE=str(tmp_path / "argv_py"))
    py = _run_py(STA / "run_opensta.py", ["myip"], tmp_path, env_py)
    log_py = (tmp_path / "myip" / "sta" / "out" / "sta.log").read_text()

    assert sh.returncode == py.returncode == 7
    assert (tmp_path / "argv_sh").read_text() == (tmp_path / "argv_py").read_text()
    assert log_sh == log_py
    assert sh.stdout == py.stdout  # tail -120 + rc line
    assert sh.stderr == py.stderr


def test_run_opensta_tool_missing(tmp_path):
    _write(tmp_path / "myip" / "sta" / "run.tcl", "# tcl\n")
    lib = _write(tmp_path / "fake.lib", "lib\n")
    env = _base_env({"PATH": "/usr/bin:/bin", "SKY130_LIB": str(lib)})
    sh = _run_sh(STA / "run_opensta.sh", ["myip"], tmp_path, env)
    py = _run_py(STA / "run_opensta.py", ["myip"], tmp_path, env)
    assert sh.returncode == py.returncode == 3
    assert sh.stderr == py.stderr


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

    sh = _run_sh(STA / "auto_sta.sh", ["myip"], root, env)
    arts_sh = {p.name: p.read_text() for p in (root / "myip" / "sta" / "out").iterdir()}
    arts_sh["run.tcl"] = (root / "myip" / "sta" / "run.tcl").read_text()
    shutil.rmtree(root / "myip" / "sta")

    py = _run_py(STA / "auto_sta.py", ["myip"], root, env)
    arts_py = {p.name: p.read_text() for p in (root / "myip" / "sta" / "out").iterdir()}
    arts_py["run.tcl"] = (root / "myip" / "sta" / "run.tcl").read_text()

    assert sh.returncode == py.returncode == 0
    assert sh.stdout == py.stdout
    assert sh.stderr == py.stderr
    for name in arts_sh:
        a = _DATE.sub("- date    : X", arts_sh[name])
        b = _DATE.sub("- date    : X", arts_py[name])
        assert a == b, f"artifact {name} differs"


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
    sh = _run_sh(POST / "write_sta_post_tcl.sh", ["myip"], tmp_path, env)
    tcl_sh = (tmp_path / "myip" / "sta-post" / "run.tcl").read_text()
    (tmp_path / "myip" / "sta-post" / "run.tcl").unlink()
    py = _run_py(POST / "write_sta_post_tcl.py", ["myip"], tmp_path, env)
    tcl_py = (tmp_path / "myip" / "sta-post" / "run.tcl").read_text()
    assert sh.returncode == py.returncode == 0
    assert tcl_sh == tcl_py
    assert "$scan_en_ports" in tcl_py  # literal Tcl var preserved
    assert sh.stdout == py.stdout


def test_preflight_ok_and_errors(tmp_path):
    _post_ip(tmp_path)
    bindir = tmp_path / "bin"
    _make_exec(bindir / "sta", "#!/usr/bin/env bash\nexit 0\n")
    lib = _write(tmp_path / "fake.lib", "lib\n")
    good_path = f"{bindir}:{os.environ['PATH']}"

    env = _base_env({"PATH": good_path, "SKY130_LIB": str(lib)})
    sh = _run_sh(POST / "preflight.sh", ["myip"], tmp_path, env)
    py = _run_py(POST / "preflight.py", ["myip"], tmp_path, env)
    assert sh.returncode == py.returncode == 0
    assert sh.stdout == py.stdout  # incl. wc -c padded size + cwd
    assert sh.stderr == py.stderr

    # error-path exit codes
    cases = {
        2: _base_env({"PATH": good_path, "SKY130_LIB": str(lib)}),  # bad ip arg
        3: _base_env({"PATH": "/usr/bin:/bin", "SKY130_LIB": str(lib)}),  # tool missing
        4: _base_env({"PATH": good_path, "SKY130_LIB": "/nope.lib"}),  # pdk missing
    }
    for rc, e in cases.items():
        arg = "ghost" if rc == 2 else "myip"
        s = _run_sh(POST / "preflight.sh", [arg], tmp_path, e)
        p = _run_py(POST / "preflight.py", [arg], tmp_path, e)
        assert s.returncode == p.returncode == rc
        assert s.stderr == p.stderr


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
    sh = _run_sh(POST / "parse_wns.sh", ["myip"], tmp_path, env)
    js_sh = (out / "wns.json").read_text()
    (out / "wns.json").unlink()
    py = _run_py(POST / "parse_wns.py", ["myip"], tmp_path, env)
    js_py = (out / "wns.json").read_text()
    assert sh.returncode == py.returncode == 0
    assert js_sh == js_py
    assert json.loads(js_sh)["mode"] == "post_route"
    assert sh.stdout == py.stdout


def test_post_write_report_with_delta(tmp_path):
    out = _seed_post_reports(tmp_path)
    env = _base_env({"SKY130_LIB": "fake.lib"})
    _run_sh(POST / "parse_wns.sh", ["myip"], tmp_path, env)
    sh = _run_sh(POST / "write_report.sh", ["myip"], tmp_path, env)
    rpt_sh = _DATE.sub("- date    : X", (out / "sta.report.md").read_text())
    (out / "sta.report.md").unlink()
    py = _run_py(POST / "write_report.py", ["myip"], tmp_path, env)
    rpt_py = _DATE.sub("- date    : X", (out / "sta.report.md").read_text())
    assert sh.returncode == py.returncode == 0
    assert rpt_sh == rpt_py
    assert "Pre-route /sta vs sign-off" in rpt_py
    assert sh.stdout == py.stdout


def test_auto_sta_post_pipeline(tmp_path):
    _post_ip(tmp_path)
    bindir = tmp_path / "bin"
    _make_exec(bindir / "sta", _FAKE_STA)
    lib = _write(tmp_path / "fake.lib", "lib\n")
    env = _base_env({"PATH": f"{bindir}:{os.environ['PATH']}", "SKY130_LIB": str(lib)})

    sh = _run_sh(POST / "auto_sta_post.sh", ["myip"], tmp_path, env)
    arts_sh = {p.name: p.read_text() for p in (tmp_path / "myip" / "sta-post" / "out").iterdir()}
    arts_sh["run.tcl"] = (tmp_path / "myip" / "sta-post" / "run.tcl").read_text()
    shutil.rmtree(tmp_path / "myip" / "sta-post")

    py = _run_py(POST / "auto_sta_post.py", ["myip"], tmp_path, env)
    arts_py = {p.name: p.read_text() for p in (tmp_path / "myip" / "sta-post" / "out").iterdir()}
    arts_py["run.tcl"] = (tmp_path / "myip" / "sta-post" / "run.tcl").read_text()

    assert sh.returncode == py.returncode == 0
    # preflight cwd line + wc size + parse + report all in order
    assert sh.stdout == py.stdout
    assert sh.stderr == py.stderr
    for name in arts_sh:
        a = _DATE.sub("- date    : X", arts_sh[name])
        b = _DATE.sub("- date    : X", arts_py[name])
        assert a == b, f"artifact {name} differs"


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
    for f, expect_rc in [(clean, 0), (warn, 1)]:
        env_sh = _base_env({"BENCHMARK_LOG": str(tmp_path / "bm_sh")})
        env_py = _base_env({"BENCHMARK_LOG": str(tmp_path / "bm_py")})
        sh = _run_sh(LINT / "lint_file.sh", [f.name], tmp_path, env_sh)
        py = _run_py(LINT / "lint_file.py", [f.name], tmp_path, env_py)
        assert sh.returncode == py.returncode == expect_rc
        assert _mask_walltime(sh.stdout) == _mask_walltime(py.stdout)
        b_sh = _TS.sub("TS", (tmp_path / "bm_sh").read_text())
        b_py = _TS.sub("TS", (tmp_path / "bm_py").read_text())
        assert b_sh == b_py
        (tmp_path / "bm_sh").unlink()
        (tmp_path / "bm_py").unlink()


def test_lint_file_missing_and_usage(tmp_path):
    sh = _run_sh(LINT / "lint_file.sh", ["nope.sv"], tmp_path, _base_env())
    py = _run_py(LINT / "lint_file.py", ["nope.sv"], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 1
    assert sh.stdout == py.stdout
    sh = _run_sh(LINT / "lint_file.sh", [], tmp_path, _base_env())
    py = _run_py(LINT / "lint_file.py", [], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 1
    assert sh.stdout == py.stdout


@pytest.mark.skipif(not HAVE_VERILATOR, reason="verilator not installed")
def test_lint_all(tmp_path):
    _write(tmp_path / "clean.sv", "module clean (input logic a, output logic b);\n  assign b = a;\nendmodule\n")
    _write(tmp_path / "warn.v", "module warn2 (input logic [3:0] a, output logic b);\n  assign b = a;\nendmodule\n")
    _write(tmp_path / "tb_foo.sv", "module tb_foo; endmodule\n")  # excluded
    env_sh = _base_env({"BENCHMARK_LOG": str(tmp_path / "bm_sh")})
    env_py = _base_env({"BENCHMARK_LOG": str(tmp_path / "bm_py")})
    sh = _run_sh(LINT / "lint_all.sh", [], tmp_path, env_sh)
    py = _run_py(LINT / "lint_all.py", [], tmp_path, env_py)
    assert sh.returncode == py.returncode
    assert _mask_walltime(sh.stdout) == _mask_walltime(py.stdout)
    b_sh = _TS.sub("TS", (tmp_path / "bm_sh").read_text())
    b_py = _TS.sub("TS", (tmp_path / "bm_py").read_text())
    assert b_sh == b_py


def test_error_log(tmp_path):
    out = "line ok\n%Warning-FOO: bar\nsome Error here\nplain line"
    env_sh = _base_env({"BENCHMARK_LOG": str(tmp_path / "eb_sh"), "HOOK_TOOL_OUTPUT": out})
    env_py = _base_env({"BENCHMARK_LOG": str(tmp_path / "eb_py"), "HOOK_TOOL_OUTPUT": out})
    sh = _run_sh(LINT / "error_log.sh", [], tmp_path, env_sh)
    py = _run_py(LINT / "error_log.py", [], tmp_path, env_py)
    assert sh.returncode == py.returncode == 0
    b_sh = _TS.sub("TS", (tmp_path / "eb_sh").read_text())
    b_py = _TS.sub("TS", (tmp_path / "eb_py").read_text())
    assert b_sh == b_py

    # empty output → neither writes a file
    env_sh = _base_env({"BENCHMARK_LOG": str(tmp_path / "n_sh"), "HOOK_TOOL_OUTPUT": "nothing"})
    env_py = _base_env({"BENCHMARK_LOG": str(tmp_path / "n_py"), "HOOK_TOOL_OUTPUT": "nothing"})
    _run_sh(LINT / "error_log.sh", [], tmp_path, env_sh)
    _run_py(LINT / "error_log.py", [], tmp_path, env_py)
    assert not (tmp_path / "n_sh").exists()
    assert not (tmp_path / "n_py").exists()


def test_auto_lint_gnu_grep_parity(tmp_path):
    """auto_lint.sh uses grep -oP (GNU-only). Under a GNU-grep stub the .sh and
    .py produce identical benchmark lines; the .py matches the intended semantics."""
    _write(tmp_path / "clean.sv", "module clean (input logic a, output logic b);\n  assign b = a;\nendmodule\n")
    if not HAVE_VERILATOR:
        pytest.skip("verilator not installed")
    bindir = tmp_path / "gnu"
    _gnu_grep_stub(bindir)
    env_sh = _base_env({
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "BENCHMARK_LOG": str(tmp_path / "abm_sh"),
        "HOOK_TOOL_ARGS": 'path="clean.sv"',
    })
    env_py = _base_env({
        "BENCHMARK_LOG": str(tmp_path / "abm_py"),
        "HOOK_TOOL_ARGS": 'path="clean.sv"',
    })
    sh = _run_sh(LINT / "auto_lint.sh", [], tmp_path, env_sh)
    py = _run_py(LINT / "auto_lint.py", [], tmp_path, env_py)
    assert sh.returncode == py.returncode == 0
    b_sh = _TS.sub("TS", (tmp_path / "abm_sh").read_text())
    b_py = _TS.sub("TS", (tmp_path / "abm_py").read_text())
    assert b_sh == b_py
    assert "file=clean.sv" in b_py


def test_auto_lint_no_file_no_log(tmp_path):
    env_sh = _base_env({"BENCHMARK_LOG": str(tmp_path / "n_sh"), "HOOK_TOOL_ARGS": "nothing"})
    env_py = _base_env({"BENCHMARK_LOG": str(tmp_path / "n_py"), "HOOK_TOOL_ARGS": "nothing"})
    sh = _run_sh(LINT / "auto_lint.sh", [], tmp_path, env_sh)
    py = _run_py(LINT / "auto_lint.py", [], tmp_path, env_py)
    assert sh.returncode == py.returncode == 0
    assert not (tmp_path / "n_sh").exists()
    assert not (tmp_path / "n_py").exists()


def test_write_report_gnu_grep_parity(tmp_path):
    """write_report.sh uses grep -oP for errors=/warnings= extraction (GNU-only).
    Prove .sh == .py under GNU semantics."""
    log = _write(
        tmp_path / ".benchmark",
        "2026-01-01T00:00:00 lint_all errors=3 warnings=7\n"
        "2026-01-01T00:00:01 lint_issues:\n"
        "  %Warning-WIDTHTRUNC: foo\n"
        "2026-01-01T00:00:02 lint_file=x.sv errors=3 warnings=7\n",
    )
    _write(tmp_path / "clean.sv", "module clean(input a, output b); assign b=a; endmodule\n")
    bindir = tmp_path / "gnu"
    _gnu_grep_stub(bindir)
    env_sh = _base_env({"PATH": f"{bindir}:{os.environ['PATH']}", "BENCHMARK_LOG": str(log)})
    env_py = _base_env({"BENCHMARK_LOG": str(log)})
    sh = _run_sh(LINT / "write_report.sh", [], tmp_path, env_sh)
    rpt_sh = _RPT_DATE.sub("Date  : X", (tmp_path / "lint_report.txt").read_text())
    (tmp_path / "lint_report.txt").unlink()
    py = _run_py(LINT / "write_report.py", [], tmp_path, env_py)
    rpt_py = _RPT_DATE.sub("Date  : X", (tmp_path / "lint_report.txt").read_text())
    assert sh.returncode == py.returncode == 0
    assert rpt_sh == rpt_py
    assert "3 errors, 7 warnings" in rpt_py
    so = _RPT_DATE.sub("Date  : X", sh.stdout)
    po = _RPT_DATE.sub("Date  : X", py.stdout)
    assert so == po


def test_run_full_lint_errors(tmp_path):
    # usage (no ip)
    sh = _run_sh(LINT / "run_full_lint.sh", [], tmp_path, _base_env())
    py = _run_py(LINT / "run_full_lint.py", [], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 2
    assert _norm_usage(sh.stderr, "run_full_lint.sh") == _norm_usage(py.stderr, "run_full_lint.py")

    # unknown flag
    sh = _run_sh(LINT / "run_full_lint.sh", ["--bogus"], tmp_path, _base_env())
    py = _run_py(LINT / "run_full_lint.py", ["--bogus"], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 2
    assert sh.stderr == py.stderr

    # missing waiver
    (tmp_path / "spi" / "rtl").mkdir(parents=True)
    sh = _run_sh(LINT / "run_full_lint.sh", ["spi"], tmp_path, _base_env())
    py = _run_py(LINT / "run_full_lint.py", ["spi"], tmp_path, _base_env())
    assert sh.returncode == py.returncode == 1
    assert sh.stderr == py.stderr  # logical-pwd path must match (not /private/tmp)


@pytest.mark.skipif(not HAVE_VERILATOR, reason="verilator not installed")
def test_run_full_lint_real(tmp_path):
    _write(tmp_path / "spi" / "rtl" / "spi.sv",
           "module spi_top (input logic clk, input logic a, output logic b);\n  always_comb b = a;\nendmodule\n")
    _write(tmp_path / "spi" / "rtl" / "spi_lint.vlt", "`verilator_config\n")
    _write(tmp_path / "spi" / "yaml" / "spi.ssot.yaml", "top_module:\n  name: spi_top\n")
    sh = _run_sh(LINT / "run_full_lint.sh", ["spi"], tmp_path, _base_env())
    log_sh = (tmp_path / "spi" / "lint" / "verilator_lint.log").read_text()
    (tmp_path / "spi" / "lint" / "verilator_lint.log").unlink()
    py = _run_py(LINT / "run_full_lint.py", ["spi"], tmp_path, _base_env())
    log_py = (tmp_path / "spi" / "lint" / "verilator_lint.log").read_text()
    assert sh.returncode == py.returncode
    assert _mask_walltime(sh.stdout) == _mask_walltime(py.stdout)
    assert _mask_walltime(log_sh) == _mask_walltime(log_py)
