"""Differential equivalence tests for the bash→python disk-check port.

A family of `check_*_disk.sh` (and a couple of converge-loop validators) were
ported to same-named `.py` files beside them for native-Windows portability.
This suite proves the ports are behaviorally equivalent to the originals by
running BOTH the old `.sh` (via `bash`) and the new `.py` (via the running
interpreter) against a good fixture plus >=2 degraded fixtures each, and
asserting:

  * exit-code parity on every fixture, and
  * the `.py` fail-output names the same defect (a stable substring of the
    failure line / verdict tag).

The `.sh` side is skipped when no POSIX `bash` is on PATH (e.g. clean Windows).
The `.py` side always runs, so the port keeps its own coverage on every host.

KNOWN PORTABILITY DIVERGENCE (flagged, exit codes still match):
  check_lint_pass.sh greps with `grep -oiP '\\d+(?= error)'`. `-P` (PCRE) is a
  GNU-grep feature; on a BSD/macOS `/usr/bin/grep` the option errors out and the
  numeric counts come back empty, so the FAIL line reads "? errors, ? warnings".
  The Python port reproduces the *intended* GNU behavior and prints the real
  counts. Exit codes are identical (0 on pass, 1 on fail) so rc-parity holds;
  only the cosmetic count text differs on BSD-grep hosts. Tests therefore assert
  rc-parity + the greppable verdict tag, not the exact count text.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_WORKFLOW = Path(__file__).resolve().parents[1] / "workflow"

# (script_id, sh_path, py_path)
_SCRIPTS = {
    "ssot_disk": _WORKFLOW / "ssot-gen" / "scripts" / "check_ssot_disk",
    "rtl_disk": _WORKFLOW / "rtl-gen" / "scripts" / "check_rtl_disk",
    "tb_disk": _WORKFLOW / "tb-gen" / "scripts" / "check_tb_disk",
    "sim_disk": _WORKFLOW / "sim" / "scripts" / "check_sim_disk",
    "lint_disk": _WORKFLOW / "lint" / "scripts" / "check_lint_disk",
    "architect_disk": _WORKFLOW / "architect" / "scripts" / "check_architect_disk",
    "lint_pass": _WORKFLOW / "eda" / "scripts" / "check_lint_pass",
    "unmapped": _WORKFLOW / "syn" / "scripts" / "check_unmapped",
}

_BASH = shutil.which("bash")
_needs_bash = pytest.mark.skipif(_BASH is None, reason="POSIX bash not on PATH")


# ──────────────────────────────────────────────────────────────────────────
# Runners
# ──────────────────────────────────────────────────────────────────────────
def _run_sh(stem: str, args, cwd: str, env: dict[str, str]):
    sh = f"{_SCRIPTS[stem]}.sh"
    return subprocess.run(
        [_BASH, sh, *args],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _run_py(stem: str, args, cwd: str, env: dict[str, str]):
    py = f"{_SCRIPTS[stem]}.py"
    return subprocess.run(
        [sys.executable, py, *args],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _clean_env(**overrides) -> dict[str, str]:
    """A minimal env that does not leak the harness's IP_NAME/ATLAS_* vars."""
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("ATLAS_")
        and k not in {"IP_NAME", "MIN_RTL", "MIN_PY", "MIN_TC", "MIN_TB", "MIN_F",
                      "MIN_BIN", "MIN_RPT", "MIN_XML", "MIN_YAML", "MIN_SECTIONS",
                      "TBD_LIMIT", "ALLOW_WARNINGS", "TOOL_OUTPUT", "SOC_SSOT",
                      "HOOK_CMD_ARGS"}
    }
    env.update({k: str(v) for k, v in overrides.items()})
    return env


def _assert_parity(stem, args, cwd, env, *, expect_rc=None, py_names: str = ""):
    """Run sh (when bash present) and py; assert rc-parity + defect naming.

    Returns (sh_rc, py_rc) so callers can build the report matrix manually.
    """
    py = _run_py(stem, args, cwd, env)
    if expect_rc is not None:
        assert py.returncode == expect_rc, f"py rc={py.returncode} out={py.stdout}{py.stderr}"
    if py_names:
        combined = py.stdout + py.stderr
        assert py_names in combined, f"py output missing '{py_names}': {combined!r}"
    sh_rc = None
    if _BASH is not None:
        sh = _run_sh(stem, args, cwd, env)
        sh_rc = sh.returncode
        assert sh.returncode == py.returncode, (
            f"[{stem}] rc mismatch sh={sh.returncode} py={py.returncode}\n"
            f"sh.out={sh.stdout}{sh.stderr}\npy.out={py.stdout}{py.stderr}"
        )
    return sh_rc, py.returncode


# ──────────────────────────────────────────────────────────────────────────
# Fixture builders (return tmp project root path)
# ──────────────────────────────────────────────────────────────────────────
def _mk(tmp_factory) -> Path:
    return Path(tempfile.mkdtemp(dir=tmp_factory))


_STARTER_SSOT_GOOD = (
    "top_module:\n"
    "  name: myip\n"
    "io_list:\n"
    "  interfaces: []\n"
    "function_model:\n"
    "  description: does a real thing with sufficiently descriptive prose text here\n"
)


# ──────────────────────────────────────────────────────────────────────────
# check_unmapped
# ──────────────────────────────────────────────────────────────────────────
class TestUnmapped:
    def _mk_ip(self, root: Path, netlist_body: str, ssot: str | None = None):
        (root / "myip" / "syn" / "out").mkdir(parents=True, exist_ok=True)
        (root / "myip" / "syn" / "out" / "synth.v").write_text(netlist_body, encoding="utf-8")
        if ssot is not None:
            (root / "myip" / "yaml").mkdir(parents=True, exist_ok=True)
            (root / "myip" / "yaml" / "myip.ssot.yaml").write_text(ssot, encoding="utf-8")

    def test_clean(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ip(root, "module foo;\n  sky130_fd_sc_hd__inv_1 u1 (.A(a), .Y(y));\nendmodule\n")
        _assert_parity("unmapped", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="[SYN]")

    def test_unmapped_cells(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ip(root, "module foo;\n  $_AND_ u1 (.A(a), .B(b), .Y(y));\nendmodule\n")
        _assert_parity("unmapped", ["myip"], str(root), _clean_env(), expect_rc=7, py_names="[SYN UNMAPPED]")

    def test_unintended_latch(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ip(root, "module foo;\n  sky130_fd_sc_hd__dlxtp_1 u1 (.D(d), .Q(q));\nendmodule\n", ssot="x: 1\n")
        _assert_parity("unmapped", ["myip"], str(root), _clean_env(), expect_rc=8, py_names="[SYN UNINTENDED LATCH]")

    def test_declared_latch_ok(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ip(
            root,
            "module foo;\n  sky130_fd_sc_hd__dlxtp_1 u1 (.D(d), .Q(q));\nendmodule\n",
            ssot="latch_intended: true\n",
        )
        _assert_parity("unmapped", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="declared in SSOT")

    def test_missing_netlist(self, tmp_path):
        root = _mk(tmp_path)
        (root / "myip").mkdir()
        _assert_parity("unmapped", ["myip"], str(root), _clean_env(), expect_rc=2, py_names="missing")


# ──────────────────────────────────────────────────────────────────────────
# check_lint_pass
# ──────────────────────────────────────────────────────────────────────────
class TestLintPass:
    def test_clean(self, tmp_path):
        env = _clean_env(TOOL_OUTPUT="Lint check done: 0 errors 0 warnings")
        _assert_parity("lint_pass", [], str(tmp_path), env, expect_rc=0, py_names="Lint PASS")

    def test_dirty(self, tmp_path):
        env = _clean_env(TOOL_OUTPUT="found 3 errors and 2 warnings")
        _assert_parity("lint_pass", [], str(tmp_path), env, expect_rc=1, py_names="Lint FAIL")

    def test_empty(self, tmp_path):
        env = _clean_env(TOOL_OUTPUT="")
        _assert_parity("lint_pass", [], str(tmp_path), env, expect_rc=1, py_names="Lint FAIL")


# ──────────────────────────────────────────────────────────────────────────
# check_lint_disk
# ──────────────────────────────────────────────────────────────────────────
class TestLintDisk:
    def _mk_report(self, root: Path, body: str):
        (root / "myip" / "lint").mkdir(parents=True, exist_ok=True)
        (root / "myip" / "lint" / "lint_report.txt").write_text(body, encoding="utf-8")

    def test_clean(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_report(root, "RTL lint complete: 0 errors, 0 warnings. lint clean.\n")
        _assert_parity("lint_disk", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="PASS")

    def test_errors(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_report(root, "Design lint: 5 errors found, FAIL on rule X\n")
        _assert_parity("lint_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="error markers")

    def test_warnings_strict(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_report(root, "Lint summary: 0 errors, 4 warnings detected in design here\n")
        _assert_parity("lint_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="warning markers")

    def test_warnings_allowed(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_report(root, "Lint summary: 0 errors, 4 warnings detected, no issues blocking\n")
        env = _clean_env(ALLOW_WARNINGS="1")
        _assert_parity("lint_disk", ["myip"], str(root), env, expect_rc=0, py_names="PASS")

    def test_missing_report(self, tmp_path):
        root = _mk(tmp_path)
        (root / "myip").mkdir()
        _assert_parity("lint_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="missing")


# ──────────────────────────────────────────────────────────────────────────
# check_architect_disk
# ──────────────────────────────────────────────────────────────────────────
class TestArchitectDisk:
    def _mk_soc(self, root: Path, body: str):
        (root / "soc.ssot.yaml").write_text(body, encoding="utf-8")

    def test_good(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_soc(
            root,
            "clusters: [a]\ninstances: []\naddrMap:\n"
            "  - {name: r1, base: 0x0, range: 0x1000}\n"
            "  - {name: r2, base: 0x1000, range: 0x1000}\nconnections: []\n",
        )
        _assert_parity("architect_disk", [], str(root), _clean_env(), expect_rc=0, py_names="PASS")

    def test_missing_key(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_soc(root, "clusters: [a]\ninstances: []\naddrMap: []\n# no connections key present at all here\n")
        _assert_parity("architect_disk", [], str(root), _clean_env(), expect_rc=1, py_names="missing keys")

    def test_overlap(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_soc(
            root,
            "clusters: [a]\ninstances: []\naddrMap:\n"
            "  - {name: r1, base: 0x0, range: 0x2000}\n"
            "  - {name: r2, base: 0x1000, range: 0x1000}\nconnections: []\n",
        )
        _assert_parity("architect_disk", [], str(root), _clean_env(), expect_rc=1, py_names="overlap")

    def test_missing_file(self, tmp_path):
        root = _mk(tmp_path)
        _assert_parity("architect_disk", [], str(root), _clean_env(), expect_rc=1, py_names="missing")


# ──────────────────────────────────────────────────────────────────────────
# check_rtl_disk
# ──────────────────────────────────────────────────────────────────────────
class TestRtlDisk:
    def _mk_ip(self, root: Path, rtl_body: str, filelist: str):
        (root / "myip" / "list").mkdir(parents=True, exist_ok=True)
        (root / "myip" / "rtl").mkdir(parents=True, exist_ok=True)
        (root / "myip" / "rtl" / "myip.v").write_text(rtl_body, encoding="utf-8")
        (root / "myip" / "list" / "myip.f").write_text(filelist, encoding="utf-8")

    def test_good(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ip(root, "module myip;\nendmodule\n" + ("// pad\n" * 60), "rtl/myip.v\n")
        _assert_parity("rtl_disk", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="PASS")

    def test_too_small(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ip(root, "x", "rtl/myip.v\n")
        _assert_parity("rtl_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="need")

    def test_missing_referenced(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ip(root, "module myip;\nendmodule\n" + ("// pad\n" * 60), "rtl/ghost.v\n")
        _assert_parity("rtl_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="missing file")

    def test_missing_filelist(self, tmp_path):
        root = _mk(tmp_path)
        (root / "myip").mkdir()
        _assert_parity("rtl_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="missing")


# ──────────────────────────────────────────────────────────────────────────
# check_tb_disk
# ──────────────────────────────────────────────────────────────────────────
class TestTbDisk:
    def _mk_cocotb(self, root: Path, test_body: str, runner_body: str):
        d = root / "myip" / "tb" / "cocotb"
        d.mkdir(parents=True, exist_ok=True)
        (d / "test_myip.py").write_text(test_body, encoding="utf-8")
        (d / "test_runner.py").write_text(runner_body, encoding="utf-8")

    def test_cocotb_good(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_cocotb(
            root,
            "import cocotb\n@cocotb.test()\nasync def t(dut):\n    assert 1\n" + ("# pad\n" * 100),
            "from cocotb.runner import get_runner\n" + ("# pad\n" * 100),
        )
        _assert_parity("tb_disk", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="PASS")

    def test_cocotb_too_small(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_cocotb(root, "import cocotb\n", "from cocotb.runner import get_runner\n" + ("# pad\n" * 100))
        _assert_parity("tb_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="need")

    def test_cocotb_no_import(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_cocotb(root, "print('hi')\n" + ("# pad\n" * 100), "from cocotb.runner import get_runner\n" + ("# pad\n" * 100))
        _assert_parity("tb_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="does not import cocotb")

    def test_legacy_sv_good(self, tmp_path):
        root = _mk(tmp_path)
        ip = root / "myip"
        (ip / "tc").mkdir(parents=True)
        (ip / "tb").mkdir(parents=True)
        (ip / "list").mkdir(parents=True)
        (ip / "tc" / "tc_myip.sv").write_text("// tc\n" + ("x" * 1100), encoding="utf-8")
        (ip / "tb" / "tb_myip.sv").write_text("// tb\n" + ("x" * 600), encoding="utf-8")
        (ip / "list" / "myip.f").write_text("tb_myip.sv\ntc_myip.sv\n" + ("# pad\n" * 5), encoding="utf-8")
        _assert_parity("tb_disk", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="PASS")

    def test_no_layout(self, tmp_path):
        root = _mk(tmp_path)
        (root / "myip").mkdir()
        _assert_parity("tb_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="contradicts")


# ──────────────────────────────────────────────────────────────────────────
# check_sim_disk
# ──────────────────────────────────────────────────────────────────────────
class TestSimDisk:
    def _mk_bin(self, root: Path):
        d = root / "myip" / "sim"
        d.mkdir(parents=True, exist_ok=True)
        (d / "myip.out").write_bytes(os.urandom(2000))
        return d

    def test_xml_pass(self, tmp_path):
        root = _mk(tmp_path)
        d = self._mk_bin(root)
        (d / "results.xml").write_text(
            '<?xml version="1.0"?>\n<testsuites>\n'
            '  <testsuite name="s" tests="3" failures="0" errors="0" skipped="0">\n'
            '    <testcase name="t1"/>\n    <testcase name="t2"/>\n    <testcase name="t3"/>\n'
            "  </testsuite>\n</testsuites>\n",
            encoding="utf-8",
        )
        _assert_parity("sim_disk", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="PASS")

    def test_report_pass(self, tmp_path):
        root = _mk(tmp_path)
        d = self._mk_bin(root)
        (d / "sim_report.txt").write_text(
            "Simulation finished.\nResults: all PASS\n0 errors, 0 warnings observed in run.\n" + ("info line\n" * 5),
            encoding="utf-8",
        )
        _assert_parity("sim_disk", ["myip"], str(root), _clean_env(), expect_rc=0, py_names="PASS")

    def test_xml_failures(self, tmp_path):
        root = _mk(tmp_path)
        d = self._mk_bin(root)
        (d / "results.xml").write_text(
            '<?xml version="1.0"?>\n<testsuites>\n'
            '  <testsuite name="s" tests="3" failures="1" errors="0" skipped="0">\n'
            '    <testcase name="t1"/>\n'
            '    <testcase name="t2"><failure message="boom">FAILED</failure></testcase>\n'
            '    <testcase name="t3"/>\n'
            "  </testsuite>\n</testsuites>\n",
            encoding="utf-8",
        )
        _assert_parity("sim_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="failures=1")

    def test_report_failure_markers(self, tmp_path):
        root = _mk(tmp_path)
        d = self._mk_bin(root)
        (d / "sim_report.txt").write_text(
            "Simulation finished.\n[FAIL] SC1_basic mismatch detected here\n" + ("info line\n" * 5),
            encoding="utf-8",
        )
        _assert_parity("sim_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="failure markers")

    def test_no_binary(self, tmp_path):
        root = _mk(tmp_path)
        (root / "myip" / "sim").mkdir(parents=True)
        _assert_parity("sim_disk", ["myip"], str(root), _clean_env(), expect_rc=1, py_names="no compiled binary")


# ──────────────────────────────────────────────────────────────────────────
# check_ssot_disk  (starter mode — keeps fixtures compact while exercising the
# CLI/mode/size/section/parse/TBD chain end-to-end)
# ──────────────────────────────────────────────────────────────────────────
class TestSsotDisk:
    def _mk_ssot(self, root: Path, body: str, name: str = "myip.ssot.yaml"):
        d = root / "myip" / "yaml"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(body, encoding="utf-8")

    def test_starter_good(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ssot(root, _STARTER_SSOT_GOOD)
        env = _clean_env(ATLAS_RUN_MODE="starter")
        _assert_parity("ssot_disk", ["myip"], str(root), env, expect_rc=0, py_names="PASS")

    def test_too_small(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ssot(root, "top_module: x\n")  # < 120 bytes
        env = _clean_env(ATLAS_RUN_MODE="starter")
        _assert_parity("ssot_disk", ["myip"], str(root), env, expect_rc=1, py_names="need ≥120")

    def test_missing_sections(self, tmp_path):
        root = _mk(tmp_path)
        # >=120 bytes, parses, but only 1 of the 3 required section keys present.
        body = "top_module:\n  name: myip\n" + ("# filler comment line to inflate byte count past the floor\n" * 4)
        self._mk_ssot(root, body)
        env = _clean_env(ATLAS_RUN_MODE="starter")
        _assert_parity("ssot_disk", ["myip"], str(root), env, expect_rc=1, py_names="top-level section keys")

    def test_model_validation_fail(self, tmp_path):
        root = _mk(tmp_path)
        # All 3 section keys present + big enough, but function_model is empty so
        # the embedded model validator rejects it.
        body = (
            "top_module:\n  name: myip\n"
            "io_list:\n  interfaces: []\n"
            "function_model: {}\n"
            + ("# pad comment to clear the 120-byte floor here for the validator\n" * 3)
        )
        self._mk_ssot(root, body)
        env = _clean_env(ATLAS_RUN_MODE="starter")
        _assert_parity("ssot_disk", ["myip"], str(root), env, expect_rc=1, py_names="failed YAML/model validation")

    def test_bad_mode(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ssot(root, _STARTER_SSOT_GOOD)
        _assert_parity("ssot_disk", ["--mode", "bogus", "myip"], str(root), _clean_env(), expect_rc=1, py_names="--mode must be")

    def test_missing_yaml(self, tmp_path):
        root = _mk(tmp_path)
        (root / "myip" / "yaml").mkdir(parents=True)
        env = _clean_env(ATLAS_RUN_MODE="starter")
        _assert_parity("ssot_disk", ["myip"], str(root), env, expect_rc=1, py_names="no SSOT YAML")

    def test_underscore_naming(self, tmp_path):
        root = _mk(tmp_path)
        self._mk_ssot(root, _STARTER_SSOT_GOOD, name="myip_ssot.yaml")
        env = _clean_env(ATLAS_RUN_MODE="starter")
        _assert_parity("ssot_disk", ["myip"], str(root), env, expect_rc=0, py_names="PASS")


# ──────────────────────────────────────────────────────────────────────────
# py_compile gate — every ported file must byte-compile.
# ──────────────────────────────────────────────────────────────────────────
def test_all_ports_py_compile():
    import py_compile

    for stem, base in _SCRIPTS.items():
        path = f"{base}.py"
        assert Path(path).is_file(), f"missing port for {stem}: {path}"
        py_compile.compile(path, doraise=True)
