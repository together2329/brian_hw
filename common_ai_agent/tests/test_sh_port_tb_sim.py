"""Differential equivalence tests: tb/sim .sh checkers vs their .py ports.

For each ported script we build a good fixture plus >=2 degraded fixtures, run
the OLD .sh (via bash) and the NEW .py (via sys.executable), and assert exit-code
parity.  Where the verdict output is deterministic we also assert stdout parity.

The .sh side is skipped when bash is unavailable.  Cases that depend on external
EDA tools (verilator/iverilog) are gated on tool presence; the verilator build
success path asserts exit-code parity only because verilator emits
non-deterministic timing/memory lines that differ between any two runs.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
WF = REPO / "workflow"

HAVE_BASH = shutil.which("bash") is not None
HAVE_VERILATOR = shutil.which("verilator") is not None

skip_no_bash = pytest.mark.skipif(not HAVE_BASH, reason="bash not available for .sh side")


def _run_sh(script: Path, args: list[str], *, cwd: Path, env: dict[str, str] | None = None):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=full_env,
    )


def _run_py(script: Path, args: list[str], *, cwd: Path, env: dict[str, str] | None = None):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=full_env,
    )


def _assert_parity(sh, py, *, check_stdout: bool = True) -> None:
    assert sh.returncode == py.returncode, (
        f"rc mismatch: sh={sh.returncode} py={py.returncode}\n"
        f"--- sh ---\n{sh.stdout}\n--- py ---\n{py.stdout}"
    )
    if check_stdout:
        assert sh.stdout == py.stdout, (
            f"stdout mismatch:\n--- sh ---\n{sh.stdout!r}\n--- py ---\n{py.stdout!r}"
        )


# --------------------------------------------------------------------------- #
# check_sim_pass (canonical sim/ variant + tb-gen delegator)
# --------------------------------------------------------------------------- #
SIM_PASS_SH = WF / "sim" / "scripts" / "check_sim_pass.sh"
SIM_PASS_PY = WF / "sim" / "scripts" / "check_sim_pass.py"
TBGEN_SIM_PASS_SH = WF / "tb-gen" / "scripts" / "check_sim_pass.sh"
TBGEN_SIM_PASS_PY = WF / "tb-gen" / "scripts" / "check_sim_pass.py"

_SIM_PASS_CASES = [
    ("good_tests_line", "TESTS=3 PASS=3 FAIL=0", 0),
    ("good_n_passed", "12 passed", 0),
    ("good_clean_iverilog", "0 errors, 0 warnings", 0),
    ("degraded_fail_count", "5 passed -- old run; FAIL=3 actual", 1),
    ("degraded_n_failed", "2 failed in 0.1s", 1),
    ("degraded_zero_tests", "TESTS=0 PASS=0 FAIL=0", 1),
    ("degraded_error_summary", "2 errors, 1 warning emitted", 1),
    ("degraded_empty", "", 1),
]


@skip_no_bash
@pytest.mark.parametrize("name,tool_output,expected_rc", _SIM_PASS_CASES)
def test_check_sim_pass_sim_variant_parity(tmp_path, name, tool_output, expected_rc):
    env = {"TOOL_OUTPUT": tool_output}
    # Ensure IP_NAME does not accidentally select the disk branch.
    env["IP_NAME"] = ""
    sh = _run_sh(SIM_PASS_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_PASS_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == expected_rc, (name, sh.stdout)


@skip_no_bash
@pytest.mark.parametrize("name,tool_output,expected_rc", _SIM_PASS_CASES)
def test_check_sim_pass_tbgen_variant_parity(tmp_path, name, tool_output, expected_rc):
    env = {"TOOL_OUTPUT": tool_output, "IP_NAME": ""}
    sh = _run_sh(TBGEN_SIM_PASS_SH, [], cwd=tmp_path, env=env)
    py = _run_py(TBGEN_SIM_PASS_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == expected_rc, (name, sh.stdout)


def test_tbgen_check_sim_pass_delegates_to_canonical():
    """The tb-gen copy is a thin delegator that re-execs the canonical script."""
    text = TBGEN_SIM_PASS_PY.read_text(encoding="utf-8")
    assert "check_sim_pass.py" in text
    assert "--variant" in text and "tb-gen" in text


# --------------------------------------------------------------------------- #
# coverage_build
# --------------------------------------------------------------------------- #
COV_BUILD_SH = WF / "coverage" / "scripts" / "coverage_build.sh"
COV_BUILD_PY = WF / "coverage" / "scripts" / "coverage_build.py"


@skip_no_bash
def test_coverage_build_missing_filelist_parity(tmp_path):
    # Default DUT gpio_pad, no filelist on disk -> ERROR exit 1 (both tools).
    sh = _run_sh(COV_BUILD_SH, [], cwd=tmp_path)
    py = _run_py(COV_BUILD_PY, [], cwd=tmp_path)
    _assert_parity(sh, py)
    assert sh.returncode == 1


@skip_no_bash
def test_coverage_build_dut_whitespace_strip_parity(tmp_path):
    sh = _run_sh(COV_BUILD_SH, ["my dut"], cwd=tmp_path)
    py = _run_py(COV_BUILD_PY, ["my dut"], cwd=tmp_path)
    _assert_parity(sh, py)
    # whitespace stripped -> filelist mydut/list/mydut.f
    assert "mydut/list/mydut.f" in sh.stdout


@skip_no_bash
def test_coverage_build_hook_cmd_args_parity(tmp_path):
    env = {"HOOK_CMD_ARGS": "widget"}
    sh = _run_sh(COV_BUILD_SH, [], cwd=tmp_path, env=env)
    py = _run_py(COV_BUILD_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)


@skip_no_bash
@pytest.mark.skipif(not HAVE_VERILATOR, reason="verilator not available")
def test_coverage_build_success_rc_parity(tmp_path):
    """Good fixture: real verilator coverage build.

    Asserts exit-code parity only — verilator prints non-deterministic
    Walltime/cpu/allocated lines that differ between any two runs.
    """
    dut = "tinymod"
    (tmp_path / dut / "rtl").mkdir(parents=True)
    (tmp_path / dut / "list").mkdir(parents=True)
    (tmp_path / dut / "rtl" / f"{dut}.sv").write_text(
        "module tinymod(input wire clk, input wire a, output reg y);\n"
        "  always @(posedge clk) y <= a;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (tmp_path / dut / "list" / f"{dut}.f").write_text(f"{dut}/rtl/{dut}.sv\n", encoding="utf-8")

    sh = _run_sh(COV_BUILD_SH, [dut], cwd=tmp_path)
    # clean build artifacts so the py rebuild starts comparable
    shutil.rmtree(tmp_path / f"build_{dut}_cov", ignore_errors=True)
    (tmp_path / f"build_{dut}_cov.verilator.log").unlink(missing_ok=True)
    py = _run_py(COV_BUILD_PY, [dut], cwd=tmp_path)
    _assert_parity(sh, py, check_stdout=False)
    assert sh.returncode == 0, sh.stdout
    # deterministic structural lines should match
    for marker in ("=== Verilator coverage build ===", "BUILD OK", "C++ source files:"):
        assert marker in sh.stdout and marker in py.stdout


# --------------------------------------------------------------------------- #
# check_pyuvm_structure  (ENFORCED gate)
# --------------------------------------------------------------------------- #
PYUVM_SH = WF / "tb-gen" / "scripts" / "check_pyuvm_structure.sh"
PYUVM_PY = WF / "tb-gen" / "scripts" / "check_pyuvm_structure.py"

_GOOD_TEST_PY = """\
import cocotb
from cocotb.triggers import RisingEdge
# pyuvm component usage so the gate passes whether or not pyuvm is importable:
# when pyuvm IS installed the import line satisfies the usage check; when it is
# not, the documented fallback reason below satisfies the fallback check.
try:
    import pyuvm  # noqa: F401
    from pyuvm import uvm_test, uvm_env, uvm_component  # noqa: F401
except ImportError:
    # pyuvm unavailable: cocotb-native fallback in use (fallback pyuvm reason).
    pyuvm = None

class WidgetTransaction:
    pass

class WidgetSequence:
    async def body(self):
        start_item(self.item)
        finish_item(self.item)

class WidgetDriver:
    async def drive_(self):
        pass

class WidgetMonitor:
    async def monitor_(self):
        pass

class WidgetScoreboard:
    def check(self, expected, got):
        if expected != got:
            raise AssertionError("mismatch")

class WidgetCoverage:
    coverpoint = 1

class WidgetEnv:
    pass

@cocotb.test()
async def test_widget(dut):
    assert dut is not None
"""

_GOOD_RUNNER_PY = """\
from cocotb.runner import get_runner

def main():
    runner = get_runner("icarus")

if __name__ == "__main__":
    main()
"""


def _make_pyuvm_ip(root: Path, ip: str = "widget") -> Path:
    tb = root / ip / "tb" / "cocotb"
    tb.mkdir(parents=True)
    (tb / f"test_{ip}.py").write_text(_GOOD_TEST_PY, encoding="utf-8")
    (tb / "test_runner.py").write_text(_GOOD_RUNNER_PY, encoding="utf-8")
    return root / ip


@skip_no_bash
def test_check_pyuvm_structure_good_parity(tmp_path):
    _make_pyuvm_ip(tmp_path)
    env = {"IP_NAME": "widget"}
    sh = _run_sh(PYUVM_SH, [], cwd=tmp_path, env=env)
    py = _run_py(PYUVM_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 0, sh.stdout


@skip_no_bash
def test_check_pyuvm_structure_empty_test_parity(tmp_path):
    """Degraded: empty test file -> missing structure FAILs, identical messages."""
    _make_pyuvm_ip(tmp_path)
    (tmp_path / "widget" / "tb" / "cocotb" / "test_widget.py").write_text("", encoding="utf-8")
    env = {"IP_NAME": "widget"}
    sh = _run_sh(PYUVM_SH, [], cwd=tmp_path, env=env)
    py = _run_py(PYUVM_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 1


@skip_no_bash
def test_check_pyuvm_structure_comment_only_keyword_parity(tmp_path):
    """Degraded: structural keyword present only in a comment must still FAIL.

    Exercises the comment-stripping hardening: a '# scoreboard' style mention
    is stripped before the structural checks.
    """
    ip_dir = _make_pyuvm_ip(tmp_path)
    test_path = ip_dir / "tb" / "cocotb" / "test_widget.py"
    text = test_path.read_text(encoding="utf-8")
    # Remove the real scoreboard class; leave only a comment-only mention.
    text = text.replace(
        'class WidgetScoreboard:\n'
        '    def check(self, expected, got):\n'
        '        if expected != got:\n'
        '            raise AssertionError("mismatch")',
        '# scoreboard note: expected vs got handled elsewhere\n'
        'class WidgetChecker:\n'
        '    def check(self, a, b):\n'
        '        raise AssertionError("x")',
    )
    test_path.write_text(text, encoding="utf-8")
    env = {"IP_NAME": "widget"}
    sh = _run_sh(PYUVM_SH, [], cwd=tmp_path, env=env)
    py = _run_py(PYUVM_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)


@skip_no_bash
def test_check_pyuvm_structure_missing_ip_parity(tmp_path):
    env = {"IP_NAME": "does_not_exist"}
    sh = _run_sh(PYUVM_SH, [], cwd=tmp_path, env=env)
    py = _run_py(PYUVM_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 1


# --------------------------------------------------------------------------- #
# check_tb_sim_evidence  (ENFORCED gate)
# --------------------------------------------------------------------------- #
SIM_EVID_SH = WF / "tb-gen" / "scripts" / "check_tb_sim_evidence.sh"
SIM_EVID_PY = WF / "tb-gen" / "scripts" / "check_tb_sim_evidence.py"

_EVID_TEST_PY = """\
import cocotb

@cocotb.test()
async def test_gizmo(dut):
    assert dut is not None
""" + "\n# padding " + ("x" * 600) + "\n"

_EVID_RUNNER_PY = """\
from cocotb.runner import get_runner

def main():
    get_runner("icarus")
""" + "\n# padding " + ("x" * 600) + "\n"


def _make_evid_ip(root: Path, ip: str = "gizmo") -> Path:
    tb = root / ip / "tb" / "cocotb"
    sim = root / ip / "sim"
    tb.mkdir(parents=True)
    sim.mkdir(parents=True)
    (tb / f"test_{ip}.py").write_text(_EVID_TEST_PY, encoding="utf-8")
    (tb / "test_runner.py").write_text(_EVID_RUNNER_PY, encoding="utf-8")
    return root / ip


def _write_results_xml(sim: Path, *, tests: int, failures: int, errors: int = 0) -> None:
    cases = "".join(
        f'<testcase name="t{i}">'
        + ("<failure>x</failure>" if i < failures else "")
        + "</testcase>"
        for i in range(max(tests, 0))
    )
    sim.joinpath("results.xml").write_text(
        '<?xml version="1.0"?>\n'
        f'<testsuites><testsuite name="g" tests="{tests}" '
        f'failures="{failures}" errors="{errors}">{cases}</testsuite></testsuites>\n',
        encoding="utf-8",
    )


def _touch_newer(paths: list[Path], base: float) -> None:
    stamp = base
    for p in paths:
        os.utime(p, (stamp, stamp))


@skip_no_bash
def test_check_tb_sim_evidence_good_pass_parity(tmp_path):
    ip = _make_evid_ip(tmp_path)
    sim = ip / "sim"
    _write_results_xml(sim, tests=2, failures=0)
    sim.joinpath("sim_report.txt").write_text("2 passed, 0 failed\n0 errors, 0 warnings\n", encoding="utf-8")
    # evidence newer than TB
    import time

    now = time.time() + 5
    _touch_newer([sim / "results.xml", sim / "sim_report.txt"], now)
    env = {"IP_NAME": "gizmo"}
    sh = _run_sh(SIM_EVID_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_EVID_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 0, sh.stdout


@skip_no_bash
def test_check_tb_sim_evidence_failures_no_escalation_parity(tmp_path):
    ip = _make_evid_ip(tmp_path)
    sim = ip / "sim"
    _write_results_xml(sim, tests=2, failures=2)
    sim.joinpath("sim_report.txt").write_text("0 passed, 2 failed\n", encoding="utf-8")
    import time

    now = time.time() + 5
    _touch_newer([sim / "results.xml", sim / "sim_report.txt"], now)
    env = {"IP_NAME": "gizmo"}
    sh = _run_sh(SIM_EVID_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_EVID_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 1


@skip_no_bash
def test_check_tb_sim_evidence_failures_with_escalation_parity(tmp_path):
    ip = _make_evid_ip(tmp_path)
    sim = ip / "sim"
    _write_results_xml(sim, tests=2, failures=2)
    sim.joinpath("sim_report.txt").write_text(
        "0 passed, 2 failed\n[SIM ESCALATE] rtl bug suspected\n", encoding="utf-8"
    )
    import time

    now = time.time() + 5
    _touch_newer([sim / "results.xml", sim / "sim_report.txt"], now)
    env = {"IP_NAME": "gizmo"}
    sh = _run_sh(SIM_EVID_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_EVID_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 0, sh.stdout


@skip_no_bash
def test_check_tb_sim_evidence_zero_tests_parity(tmp_path):
    ip = _make_evid_ip(tmp_path)
    sim = ip / "sim"
    _write_results_xml(sim, tests=0, failures=0)
    sim.joinpath("sim_report.txt").write_text("nothing ran\n", encoding="utf-8")
    import time

    now = time.time() + 5
    _touch_newer([sim / "results.xml", sim / "sim_report.txt"], now)
    env = {"IP_NAME": "gizmo"}
    sh = _run_sh(SIM_EVID_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_EVID_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 1


@skip_no_bash
def test_check_tb_sim_evidence_stale_failure_text_parity(tmp_path):
    """Degraded: XML reports 0 failures but report still carries FAIL=3 text."""
    ip = _make_evid_ip(tmp_path)
    sim = ip / "sim"
    _write_results_xml(sim, tests=2, failures=0)
    sim.joinpath("sim_report.txt").write_text(
        "2 passed, but earlier FAIL=3 left behind\n", encoding="utf-8"
    )
    import time

    now = time.time() + 5
    _touch_newer([sim / "results.xml", sim / "sim_report.txt"], now)
    env = {"IP_NAME": "gizmo"}
    sh = _run_sh(SIM_EVID_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_EVID_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 1


@skip_no_bash
def test_check_tb_sim_evidence_stale_evidence_parity(tmp_path):
    """Degraded: TB file is newer than the simulation evidence (freshness fail)."""
    ip = _make_evid_ip(tmp_path)
    sim = ip / "sim"
    _write_results_xml(sim, tests=2, failures=0)
    sim.joinpath("sim_report.txt").write_text("2 passed, 0 failed\n", encoding="utf-8")
    import time

    base = time.time()
    # evidence older, TB newer
    _touch_newer([sim / "results.xml", sim / "sim_report.txt"], base)
    _touch_newer([ip / "tb" / "cocotb" / "test_gizmo.py"], base + 10)
    env = {"IP_NAME": "gizmo"}
    sh = _run_sh(SIM_EVID_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_EVID_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 1


@skip_no_bash
def test_check_tb_sim_evidence_missing_ip_parity(tmp_path):
    env = {"IP_NAME": "ghost"}
    sh = _run_sh(SIM_EVID_SH, [], cwd=tmp_path, env=env)
    py = _run_py(SIM_EVID_PY, [], cwd=tmp_path, env=env)
    _assert_parity(sh, py)
    assert sh.returncode == 1


# --------------------------------------------------------------------------- #
# sim  (heavy runner)
# --------------------------------------------------------------------------- #
SIM_SH = WF / "tb-gen" / "scripts" / "sim.sh"
SIM_PY = WF / "tb-gen" / "scripts" / "sim.py"


def _run_sim(script, args, cwd, runner: str, *, py: bool):
    env = dict(os.environ)
    env["BENCHMARK_LOG"] = ".bench_py" if py else ".bench_sh"
    cmd = [sys.executable, str(script), *args] if py else ["bash", str(script), *args]
    return subprocess.run(
        cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
    )


@skip_no_bash
def test_sim_cocotb_pass_parity(tmp_path):
    runner = tmp_path / "g" / "tb" / "cocotb" / "test_runner.py"
    runner.parent.mkdir(parents=True)
    runner.write_text(
        "import sys\n"
        "if __name__ == \"__main__\":\n"
        "    print(\"[PASS] a\")\n"
        "    print(\"TESTS=1 PASS=1 FAIL=0\")\n"
        "    sys.exit(0)\n",
        encoding="utf-8",
    )
    rel = "g/tb/cocotb/test_runner.py"
    sh = _run_sim(SIM_SH, [rel], tmp_path, rel, py=False)
    py = _run_sim(SIM_PY, [rel], tmp_path, rel, py=True)
    _assert_parity(sh, py)
    assert sh.returncode == 0, sh.stdout


@skip_no_bash
def test_sim_cocotb_fail_parity(tmp_path):
    runner = tmp_path / "g" / "tb" / "cocotb" / "test_runner.py"
    runner.parent.mkdir(parents=True)
    runner.write_text(
        "import sys\n"
        "if __name__ == \"__main__\":\n"
        "    print(\"[FAIL] boom\")\n"
        "    print(\"TESTS=1 PASS=0 FAIL=1\")\n"
        "    sys.exit(1)\n",
        encoding="utf-8",
    )
    rel = "g/tb/cocotb/test_runner.py"
    sh = _run_sim(SIM_SH, [rel], tmp_path, rel, py=False)
    py = _run_sim(SIM_PY, [rel], tmp_path, rel, py=True)
    _assert_parity(sh, py)
    assert sh.returncode != 0


@skip_no_bash
def test_sim_no_testbench_parity(tmp_path):
    sh = _run_sim(SIM_SH, [], tmp_path, "", py=False)
    py = _run_sim(SIM_PY, [], tmp_path, "", py=True)
    _assert_parity(sh, py)
    assert sh.returncode == 1


@skip_no_bash
def test_sim_benchmark_log_content_parity(tmp_path):
    """The appended benchmark line (minus timestamp) must match byte-for-byte."""
    runner = tmp_path / "g" / "tb" / "cocotb" / "test_runner.py"
    runner.parent.mkdir(parents=True)
    runner.write_text(
        "import sys\n"
        "if __name__ == \"__main__\":\n"
        "    print(\"[PASS] a\")\n"
        "    print(\"TESTS=1 PASS=1 FAIL=0\")\n"
        "    sys.exit(0)\n",
        encoding="utf-8",
    )
    rel = "g/tb/cocotb/test_runner.py"
    _run_sim(SIM_SH, [rel], tmp_path, rel, py=False)
    _run_sim(SIM_PY, [rel], tmp_path, rel, py=True)

    def _strip_ts(path: Path) -> str:
        line = path.read_text(encoding="utf-8").strip()
        return line.split(" ", 1)[1] if " " in line else line

    assert _strip_ts(tmp_path / ".bench_sh") == _strip_ts(tmp_path / ".bench_py")
