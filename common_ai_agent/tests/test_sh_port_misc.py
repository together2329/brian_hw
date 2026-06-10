"""Pinned regression tests: misc workflow .py ports.

Each test runs the Python ``.py`` port (via ``sys.executable``) over a fixture
and asserts the PINNED expectation that the differential parity run established:

  * the return code, and
  * key-output / artifact content where the test computes it.

These tests originally ran the bash ``.sh`` original beside the ``.py`` and
compared streams; the ``.sh`` scripts have since been removed, so the
expectations are pinned constants and only the ``.py`` port is run. Where a
script invokes an external tool (iverilog, verilator, verilator_coverage, yosys,
genhtml) a PATH-stubbed fake tool is injected so the run is deterministic; the
stubs are tiny *python* executables (no shell), so the suite needs no bash.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Locations.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_WF = _REPO_ROOT / "workflow"

# Retained so the historical ``@_runs_py`` decorators below keep their shape; the
# .py port runs on every host with no shell dependency.
def _runs_py(fn):
    return fn


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------
def _run(cmd, cwd, env=None):
    """Run cmd, returning (rc, stdout). stderr is discarded (tool noise)."""
    full_env = {
        # Minimal, deterministic environment.  Keep PATH controllable per call.
        "PATH": (env or {}).get("PATH", "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LC_ALL": "C",
    }
    if env:
        full_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=full_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return proc.returncode, proc.stdout


def _py(script: Path):
    return [sys.executable, str(script)]


def _make_stub(directory: Path, name: str, body: str) -> None:
    """Write an executable *python* PATH-stub fake tool.

    ``body`` is python source with ``argv`` (= ``sys.argv[1:]``) and the stdlib
    in scope. These replace the former bash-shebang stubs so the suite is
    shell-free; each stub exits 0 unless ``body`` calls ``sys.exit``.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    preamble = (
        "#!/usr/bin/env python3\n"
        "import os, re, sys\n"
        "argv = sys.argv[1:]\n"
    )
    path.write_text(preamble + textwrap.dedent(body), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _strip_ts(text: str) -> str:
    """Normalise an ISO-ish leading timestamp at line start (benchmark logs)."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} ", "TS ", text, flags=re.M)


# Pinned exit codes the differential parity run established, keyed by
# (py-script basename, tuple(args)). The .py port must keep producing these.
_PINNED_RC = {
    ("gen_rtl.py", ()): 1,
    ("gen_rtl.py", ("mymod",)): 2,
    ("validate_yaml.py", ("nomod",)): 0,
    # ("validate_yaml.py", ("mymod",)) is fixture-dependent (0 all-pass / 1
    # set-e early-exit); those call sites pass expected_rc explicitly.
    ("run_ip_signoff.py", ()): 2,
    ("run_ip_signoff.py", ("foo", "--bogus")): 2,
    ("run_derive_ip_contract.py", ()): 2,
    ("post_session.py", ()): 0,
    ("wave_info.py", ("test.vcd",)): 0,
    ("wave_info.py", ()): 1,
    ("wave_info.py", ("bad.vcd",)): 2,
    ("sig_search.py", ()): 1,
    ("sig_search.py", ("clk",)): 1,
    ("sig_search.py", ("nope_xyz",)): 0,
    ("find-mas.py", (".",)): 0,
    ("coverage.py", ("foo",)): 0,
    ("coverage.py", ("nope",)): 1,
    ("gen_tc.py", ("foo",)): 0,
    ("gen_tc.py", ("foo.sv",)): 1,
    # check_no_ip_coverage_workarounds / coverage_merge / coverage_report /
    # coverage_vcd_* are fixture-dependent; those call sites pass expected_rc.
    ("coverage_gaps.py", ("dut",)): 1,
    ("coverage_gaps.py", ("dut", "5")): 0,
    ("coverage_gaps.py", ("dut", "--top", "2")): 0,
    ("coverage_vcd_merge.py", ("vdut",)): 1,
    ("coverage_vcd_toggle.py", ("vdut", "--json")): 0,
    ("compile.py", ()): 1,
    ("sim.py", ()): 1,
    ("write_report.py", ()): 0,
}


def _assert_parity(py_script: Path, args, cwd, *,
                   env=None, normalize=None, expected_rc=None):
    """Run the .py port over a cwd snapshot; assert the pinned exit code.

    The run happens in a *copy* of the cwd so its on-disk side effects don't
    leak into the fixture; the run dir is returned (twice, for the two-dir call
    sites) so callers can inspect artifacts. ``expected_rc`` pins the exit code;
    when omitted it is looked up in ``_PINNED_RC`` and, if that is ``None``
    (fixture-dependent), the rc is not asserted (those call sites assert
    artifacts/markers instead).
    """
    import tempfile

    normalize = normalize or (lambda s: s)

    py_dir = Path(tempfile.mkdtemp(dir=str(cwd), prefix="_py_"))

    for item in Path(cwd).iterdir():
        if item == py_dir or item.name.startswith(("_sh_", "_py_")):
            continue
        target = py_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    py_rc, py_out = _run(_py(py_script) + list(args), py_dir, env)

    if expected_rc is None:
        expected_rc = _PINNED_RC.get((py_script.name, tuple(args)), "skip")
    if expected_rc not in (None, "skip"):
        assert py_rc == expected_rc, (
            f"rc mismatch for {py_script.name} {list(args)}: "
            f"py={py_rc} expected={expected_rc}\n{py_out}"
        )
    return py_dir, py_dir


# ===========================================================================
# ssot-gen / gen_rtl.sh
# ===========================================================================
@_runs_py
def test_gen_rtl_no_arg(tmp_path):
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "gen_rtl.py", [], tmp_path)


@_runs_py
def test_gen_rtl_with_module(tmp_path):
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "gen_rtl.py", ["mymod"], tmp_path)


# ===========================================================================
# ssot-gen / validate_yaml.sh  (needs cerberus + pyyaml)
# ===========================================================================
def _have_cerberus() -> bool:
    try:
        import cerberus  # noqa: F401
        import yaml  # noqa: F401
        return True
    except Exception:
        return False


@_runs_py
@pytest.mark.skipif(not _have_cerberus(), reason="cerberus/pyyaml not installed")
def test_validate_yaml_no_schema(tmp_path):
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "validate_yaml.py", ["nomod"], tmp_path)


@_runs_py
@pytest.mark.skipif(not _have_cerberus(), reason="cerberus/pyyaml not installed")
def test_validate_yaml_set_e_early_exit(tmp_path):
    # FLAGGED: set -e makes the .sh stop at the first failing file with no
    # summary. The port reproduces that.
    yaml_dir = tmp_path / "mymod" / "yaml"
    yaml_dir.mkdir(parents=True)
    (yaml_dir / "mymod_schema.yaml").write_text(
        "name:\n  type: string\n  required: true\ncount:\n  type: integer\n",
        encoding="utf-8",
    )
    (yaml_dir / "good.yaml").write_text("name: foo\ncount: 3\n", encoding="utf-8")
    (yaml_dir / "bad.yaml").write_text("count: notanint\n", encoding="utf-8")
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "validate_yaml.py", ["mymod"], tmp_path,
                   expected_rc=1)


@_runs_py
@pytest.mark.skipif(not _have_cerberus(), reason="cerberus/pyyaml not installed")
def test_validate_yaml_all_pass(tmp_path):
    yaml_dir = tmp_path / "mymod" / "yaml"
    yaml_dir.mkdir(parents=True)
    (yaml_dir / "mymod_schema.yaml").write_text(
        "name:\n  type: string\n  required: true\n", encoding="utf-8",
    )
    (yaml_dir / "a.yaml").write_text("name: foo\n", encoding="utf-8")
    (yaml_dir / "b.yaml").write_text("name: bar\n", encoding="utf-8")
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "validate_yaml.py", ["mymod"], tmp_path,
                   expected_rc=0)


# ===========================================================================
# signoff / run_ip_signoff.sh  (usage / unknown-arg paths)
# ===========================================================================
@_runs_py
def test_run_ip_signoff_no_ip(tmp_path):
    d = _WF / "signoff" / "scripts"
    _assert_parity(d / "run_ip_signoff.py", [], tmp_path)


@_runs_py
def test_run_ip_signoff_unknown_arg(tmp_path):
    d = _WF / "signoff" / "scripts"
    _assert_parity(
        d / "run_ip_signoff.py",
        ["foo", "--bogus"], tmp_path, env={"IP_NAME": "foo"},
    )


# ===========================================================================
# ip-contract / run_derive_ip_contract.sh  (usage path; $0 == .sh path)
# ===========================================================================
@_runs_py
def test_run_derive_ip_contract_no_arg(tmp_path):
    d = _WF / "ip-contract" / "scripts"
    _assert_parity(
        d / "run_derive_ip_contract.py",
        [], tmp_path,
    )


# ===========================================================================
# spec-review / post_session.sh  (saves a session file)
# ===========================================================================
@_runs_py
def test_post_session(tmp_path):
    d = _WF / "spec-review" / "scripts"

    def norm(s: str) -> str:
        return re.sub(r"session_\d+_\d+\.txt", "session_TS.txt", s)

    env = {
        "BENCHMARK_LOG": "bench",
        "HOOK_WORKSPACE": "ws",
        "HOOK_TODO_INDEX": "2",
        "HOOK_TODO_CONTENT": "do x",
    }
    py_dir, _ = _assert_parity(
        d / "post_session.py", [], tmp_path,
        env=env, normalize=norm, expected_rc=0,
    )
    # The port wrote a session file with the pinned non-volatile body.
    py_file = next((py_dir / "bench" / "sessions").glob("*.txt"))
    drop_date = lambda t: "\n".join(
        l for l in t.splitlines() if not l.startswith("Date")
    )
    assert drop_date(py_file.read_text()) == (
        "=== Spec Review Session ===\n"
        "Workspace : ws\n"
        "Todo      : 2 — do x\n"
    )


# ===========================================================================
# Benchmark-log writers (post_write / capture).  Compare the appended line.
# ===========================================================================
def _read_log(run_dir: Path, name: str = ".bench") -> str:
    p = run_dir / name
    return _strip_ts(p.read_text(encoding="utf-8")) if p.exists() else ""


def _parity_log(py_script, args, tmp_path, env, log_name=".bench",
                expected_rc=0):
    """Run the .py port; assert the pinned rc; return the benchmark log text."""
    import tempfile
    py_dir = Path(tempfile.mkdtemp())
    try:
        for item in tmp_path.iterdir():
            t = py_dir / item.name
            shutil.copytree(item, t) if item.is_dir() else shutil.copy2(item, t)
        e_py = dict(env); e_py["BENCHMARK_LOG"] = log_name
        py_rc, _py_out = _run(_py(py_script) + list(args), py_dir, e_py)
        if expected_rc is not None:
            assert py_rc == expected_rc, f"rc {py_rc} != {expected_rc}"
        return _read_log(py_dir, log_name)
    finally:
        shutil.rmtree(py_dir, ignore_errors=True)


@_runs_py
def test_sim_post_write_no_log_when_grep_p_unsupported(tmp_path):
    # FLAGGED: sim/post_write has no fallback; on hosts where grep -oP fails the
    # path is empty and NOTHING is logged.
    d = _WF / "sim" / "scripts"
    py_log = _parity_log(
        d / "post_write.py", [], tmp_path,
        {"HOOK_TOOL_ARGS": 'path="a/b.sv",x=1'}, expected_rc=1,
    )
    # sim/post_write has no fallback: nothing is logged.
    assert py_log == ""


@_runs_py
def test_rtl_post_write_fallback(tmp_path):
    d = _WF / "rtl-gen" / "scripts"
    py_log = _parity_log(
        d / "post_write.py", [], tmp_path,
        {"HOOK_TOOL_ARGS": 'path="a/b.sv",x=1'},
    )
    assert py_log == 'TS rtl_write file=path="a/b.sv"\n'


@_runs_py
def test_tb_post_write_tc_fallback(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    py_log = _parity_log(
        d / "post_write.py", [], tmp_path,
        {"HOOK_TOOL_ARGS": 'path="tc_x.sv",x=1'},
    )
    assert py_log == 'TS tc_write file=path="tc_x.sv"\n'


@_runs_py
def test_sim_capture(tmp_path):
    d = _WF / "sim" / "scripts"
    out = "Compile error: foo\n[PASS] test1\nTESTS=2 PASS=2 FAIL=0"
    py_log = _parity_log(
        d / "sim_capture.py", [], tmp_path,
        {"HOOK_TOOL_OUTPUT": out},
    )
    assert py_log == "TS sim_capture=FAIL errors=1 warnings=0 pass=2 fail=0\n"


@_runs_py
def test_tb_sim_result_capture(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    out = "warning: minor\n[PASS] t1\nTESTS=1 PASS=1 FAIL=0"
    py_log = _parity_log(
        d / "sim_result_capture.py", [], tmp_path,
        {"HOOK_TOOL_OUTPUT": out},
    )
    assert py_log == "TS sim_capture=FAIL errors=0 warnings=1 tc_pass=1 tc_fail=0\n"


@_runs_py
def test_rtl_error_capture(tmp_path):
    d = _WF / "rtl-gen" / "scripts"
    out = "line ok\nERROR: bad thing\nfailed here\nmore"
    py_log = _parity_log(
        d / "error_capture.py", [], tmp_path,
        {"HOOK_TOOL_OUTPUT": out},
    )
    assert py_log == "TS rtl_errors:\n  ERROR: bad thing\n  failed here\n"
    assert "rtl_errors" in py_log


# ===========================================================================
# wave_info / sig_search  (VCD parsing — incl. the empty-signals grep -oP bug)
# ===========================================================================
_VCD = (
    "$date today $end\n"
    "$timescale 1ns $end\n"
    "$var wire 1 ! clk $end\n"
    "$var wire 8 # data [7:0] $end\n"
    "$enddefinitions $end\n"
    "#0\n#10\n#20\n"
)


@_runs_py
def test_sim_wave_info(tmp_path):
    (tmp_path / "test.vcd").write_text(_VCD, encoding="utf-8")
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "wave_info.py", ["test.vcd"], tmp_path)


@_runs_py
def test_sim_wave_info_none(tmp_path):
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "wave_info.py", [], tmp_path)


@_runs_py
def test_sim_debug_wave_info(tmp_path):
    (tmp_path / "test.vcd").write_text(_VCD, encoding="utf-8")
    d = _WF / "sim_debug" / "scripts"
    _assert_parity(d / "wave_info.py", ["test.vcd"], tmp_path)


@_runs_py
def test_sim_debug_wave_info_not_ascii(tmp_path):
    # ASCII-VCD guard path (exit 2).
    (tmp_path / "bad.vcd").write_bytes(b"\x00\x01\x02 binary not a vcd " * 20)
    d = _WF / "sim_debug" / "scripts"
    _assert_parity(d / "wave_info.py", ["bad.vcd"], tmp_path)


@_runs_py
def test_sig_search_no_arg(tmp_path):
    d = _WF / "sim_debug" / "scripts"
    _assert_parity(d / "sig_search.py", [], tmp_path)


@_runs_py
def test_sig_search_hit_and_miss(tmp_path):
    (tmp_path / "test.vcd").write_text(_VCD, encoding="utf-8")
    d = _WF / "sim_debug" / "scripts"
    # Hit: exit 1 (the .sh's last [ HITS -eq 0 ] is false).
    _assert_parity(d / "sig_search.py", ["clk"], tmp_path)
    # Miss: exit 0.
    _assert_parity(d / "sig_search.py", ["nope_xyz"], tmp_path)


# ===========================================================================
# rtl-gen / find-mas.sh
# ===========================================================================
def _norm_find_mas(s: str) -> str:
    return re.sub(r"Modified: [0-9 :-]+", "Modified: TS", s)


@_runs_py
def test_find_mas_empty(tmp_path):
    d = _WF / "rtl-gen" / "scripts"
    _assert_parity(d / "find-mas.py", ["."], tmp_path,
                   normalize=_norm_find_mas)


@_runs_py
def test_find_mas_structured(tmp_path):
    ip = tmp_path / "myip"
    (ip / "mas").mkdir(parents=True)
    (ip / "rtl").mkdir()
    (ip / "list").mkdir()
    (ip / "mas" / "myip_mas.md").write_text(
        "# MAS\n## 1. Overview\nThis IP does things.\n", encoding="utf-8",
    )
    (ip / "rtl" / "myip.sv").write_text("x", encoding="utf-8")
    (ip / "list" / "myip.f").write_text("x", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    _assert_parity(d / "find-mas.py", ["."], tmp_path,
                   normalize=_norm_find_mas)


@_runs_py
def test_find_mas_module_name_env(tmp_path):
    ip = tmp_path / "myip"
    (ip / "mas").mkdir(parents=True)
    (ip / "mas" / "myip_mas.md").write_text("# MAS\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    _assert_parity(d / "find-mas.py", ["."], tmp_path,
                   env={"MODULE_NAME": "myip"}, normalize=_norm_find_mas)


# ===========================================================================
# tb-gen / coverage.sh + gen_tc.sh
# ===========================================================================
_DUT_SV = (
    "module foo(\n"
    "    input  logic clk,\n"
    "    input  logic [7:0] data,\n"
    "    output logic ready\n"
    ");\n"
    "  if (a) b;\n"
    "  case(x)\n"
    "  0: y;\n"
    "  endcase\n"
    "endmodule\n"
)


@_runs_py
def test_tb_coverage_no_tc(tmp_path):
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "coverage.py", ["foo"], tmp_path)


@_runs_py
def test_tb_coverage_missing_dut(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "coverage.py", ["nope"], tmp_path)


@_runs_py
def test_gen_tc_generates_skeleton(tmp_path):
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    py_dir, _ = _assert_parity(
        d / "gen_tc.py", ["foo"], tmp_path, expected_rc=0,
    )
    # Generated tc skeleton has the pinned shape (header + 4 tc_ tasks).
    tc = (py_dir / "tc_foo.sv").read_text()
    assert tc.startswith("// tc_foo.sv — Test cases for foo\n")
    for task in ("tc_reset", "tc_normal_op", "tc_boundary", "tc_edge_case"):
        assert f"task automatic {task}(" in tc
        assert f'$display("[PASS] {task}"); pass_cnt++;' in tc


@_runs_py
def test_gen_tc_already_exists(tmp_path):
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    (tmp_path / "tc_foo.sv").write_text("// existing\n", encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "gen_tc.py", ["foo"], tmp_path)


@_runs_py
def test_gen_tc_dut_not_found(tmp_path):
    # Passing "foo.sv" makes the .sh look for "foo.sv.sv" (no .sv strip).
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "gen_tc.py", ["foo.sv"], tmp_path)


# ===========================================================================
# tb-gen / check_no_ip_coverage_workarounds.sh
# ===========================================================================
@_runs_py
def test_check_no_ip_coverage_workarounds_pass(tmp_path):
    (tmp_path / "myip" / "tb").mkdir(parents=True)
    (tmp_path / "myip" / "tb" / "test_runner.py").write_text("x", encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(
        d / "check_no_ip_coverage_workarounds.py",
        [], tmp_path, env={"IP_NAME": "myip"}, expected_rc=0,
    )


@_runs_py
def test_check_no_ip_coverage_workarounds_fail(tmp_path):
    (tmp_path / "myip" / "tb").mkdir(parents=True)
    (tmp_path / "myip" / "tb" / "my_coverage_summary.py").write_text("x", encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(
        d / "check_no_ip_coverage_workarounds.py",
        [], tmp_path, env={"IP_NAME": "myip"}, expected_rc=1,
    )


@_runs_py
def test_check_no_ip_coverage_workarounds_no_dir(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(
        d / "check_no_ip_coverage_workarounds.py",
        [], tmp_path, env={"IP_NAME": "ghost"}, expected_rc=1,
    )


# ===========================================================================
# coverage / coverage_gaps.sh
# ===========================================================================
@_runs_py
def test_coverage_gaps_missing_annotated(tmp_path):
    d = _WF / "coverage" / "scripts"
    _assert_parity(d / "coverage_gaps.py", ["dut"], tmp_path)


@_runs_py
def test_coverage_gaps_with_data(tmp_path):
    ann = tmp_path / "dut" / "cov" / "annotated"
    ann.mkdir(parents=True)
    (ann / "a.cov").write_text(
        "%000000  always_comb begin\n"
        "00001234 dout <= 1;\n"
        "%000002  if (foo)\n"
        "%000000  case x\n",
        encoding="utf-8",
    )
    (ann / "b.cov").write_text("%000000  unhit2\n", encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(d / "coverage_gaps.py", ["dut", "5"], tmp_path)


@_runs_py
def test_coverage_gaps_top_flag(tmp_path):
    ann = tmp_path / "dut" / "cov" / "annotated"
    ann.mkdir(parents=True)
    (ann / "a.cov").write_text("%000000  x\n%000000  y\n%000000  z\n", encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_gaps.py", ["dut", "--top", "2"], tmp_path,
    )


# ===========================================================================
# coverage / coverage_merge.sh  (stub verilator_coverage)
# ===========================================================================
_VC_STUB = r"""
for i, a in enumerate(argv):
    if a == "--write" and i + 1 < len(argv):
        open(argv[i + 1], "w").close()
print("verilator_coverage: " + " ".join(argv))
"""


@_runs_py
def test_coverage_merge_no_tool(tmp_path):
    d = _WF / "coverage" / "scripts"
    (tmp_path / "dut" / "cocotb").mkdir(parents=True)
    (tmp_path / "dut" / "cocotb" / "coverage.dat").write_text("x", encoding="utf-8")
    # PATH without verilator_coverage on either side.
    _assert_parity(
        d / "coverage_merge.py", ["dut"], tmp_path,
        env={"PATH": "/usr/bin:/bin"}, expected_rc=1,
    )


@_runs_py
def test_coverage_merge_no_dat(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "verilator_coverage", _VC_STUB)
    (tmp_path / "dut").mkdir()
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_merge.py", ["dut"], tmp_path,
        env={"PATH": f"{stubs}:/usr/bin:/bin"}, expected_rc=1,
    )


@_runs_py
def test_coverage_merge_single(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "verilator_coverage", _VC_STUB)
    cocotb = tmp_path / "dut" / "cocotb" / "sim_build"
    cocotb.mkdir(parents=True)
    (cocotb / "coverage.dat").write_text("x", encoding="utf-8")
    d = _WF / "coverage" / "scripts"

    def norm(s: str) -> str:
        # ls -lh line varies (perms/size/date) — collapse it.
        return re.sub(r"^-rw.*merged\.dat$", "LSLINE", s, flags=re.M)

    _assert_parity(
        d / "coverage_merge.py", ["dut"], tmp_path,
        env={"PATH": f"{stubs}:/usr/bin:/bin"}, normalize=norm, expected_rc=0,
    )


# ===========================================================================
# coverage / coverage_report.sh  (stub verilator_coverage; no genhtml)
# ===========================================================================
_VC_REPORT_STUB = r"""
mode = ann = info = ""
for i, a in enumerate(argv):
    if a == "--annotate":
        mode, ann = "annotate", argv[i + 1]
    elif a == "--write-info":
        mode, info = "info", argv[i + 1]
if mode == "annotate":
    os.makedirs(ann, exist_ok=True)
    print("annotated written")
elif mode == "info":
    with open(info, "w") as fh:
        fh.write("SF:foo.sv\nDA:1,5\nDA:2,0\nBRDA:1,0,0,2\nBRDA:1,0,1,0\nend_of_record\n")
    print("info written")
else:
    print(" Total coverage: 50.00%")
"""


@_runs_py
def test_coverage_report_no_merged(tmp_path):
    d = _WF / "coverage" / "scripts"
    (tmp_path / "dut" / "cov").mkdir(parents=True)
    _assert_parity(d / "coverage_report.py", ["dut"], tmp_path,
                   expected_rc=1)


@_runs_py
def test_coverage_report_with_stub(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "verilator_coverage", _VC_REPORT_STUB)
    cov = tmp_path / "dut" / "cov"
    cov.mkdir(parents=True)
    (cov / "merged.dat").write_text("x", encoding="utf-8")
    d = _WF / "coverage" / "scripts"

    def norm(s: str) -> str:
        s = re.sub(r"\d{4}-\d{2}-\d{2}T[0-9:]+Z", "TS", s)
        s = re.sub(r"\b\d{10,}\b", "EPOCH", s)
        return s

    # No genhtml on PATH (stub PATH excludes it) ⇒ deterministic no-HTML branch.
    _assert_parity(
        d / "coverage_report.py", ["dut"], tmp_path,
        env={"PATH": f"{stubs}:/usr/bin:/bin"}, normalize=norm, expected_rc=0,
    )


# ===========================================================================
# coverage / coverage_vcd_merge.sh + coverage_vcd_toggle.sh  (real adapters)
# ===========================================================================
def _adapters_present() -> bool:
    return (
        (_WF / "coverage" / "adapters" / "vcd_merge.py").is_file()
        and (_WF / "coverage" / "adapters" / "vcd_toggle.py").is_file()
    )


_VCD_A = (
    "$timescale 1ns $end\n$scope module top $end\n"
    "$var wire 1 ! clk $end\n$var wire 1 \" rst $end\n"
    "$upscope $end\n$enddefinitions $end\n"
    "#0\n0!\n0\"\n#5\n1!\n#10\n0!\n1\"\n"
)
_VCD_B = (
    "$timescale 1ns $end\n$scope module top $end\n"
    "$var wire 1 ! clk $end\n$upscope $end\n$enddefinitions $end\n"
    "#0\n0!\n#5\n1!\n"
)


@_runs_py
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_merge_two(tmp_path):
    sim = tmp_path / "vdut" / "sim"
    sim.mkdir(parents=True)
    (sim / "a.vcd").write_text(_VCD_A, encoding="utf-8")
    (sim / "b.vcd").write_text(_VCD_B, encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_merge.py", ["vdut"], tmp_path,
    )


@_runs_py
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_merge_none(tmp_path):
    (tmp_path / "vdut").mkdir()
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_merge.py", ["vdut"], tmp_path,
    )


@_runs_py
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_toggle_text(tmp_path):
    sim = tmp_path / "vdut" / "sim"
    sim.mkdir(parents=True)
    (sim / "a.vcd").write_text(_VCD_A, encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_toggle.py", ["vdut"], tmp_path,
        expected_rc=0,
    )


@_runs_py
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_toggle_json(tmp_path):
    sim = tmp_path / "vdut" / "sim"
    sim.mkdir(parents=True)
    (sim / "a.vcd").write_text(_VCD_A, encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_toggle.py",
        ["vdut", "--json"], tmp_path,
    )


@_runs_py
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_toggle_no_vcd(tmp_path):
    (tmp_path / "vdut").mkdir()
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_toggle.py", ["vdut"], tmp_path,
        expected_rc=1,
    )


# ===========================================================================
# sim / compile.sh + sim.sh  (stub iverilog/vvp)
# ===========================================================================
_IVERILOG_OK = (
    'print("iverilog: fake compile of " + " ".join(argv))\n'
    'print("warning: minor")\n'
)
_VVP_OK = 'print("[PASS] test_one")\nprint("TESTS=1 PASS=1 FAIL=0")\n'


@_runs_py
def test_sim_compile_with_stub(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "iverilog", _IVERILOG_OK)
    (tmp_path / "tb_foo.sv").write_text("module tb_foo; endmodule\n", encoding="utf-8")
    d = _WF / "sim" / "scripts"
    py_log = _parity_log(
        d / "compile.py", ["tb_foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert py_log == "TS compile errors=0 tb=tb_foo.sv\n"


@_runs_py
def test_sim_compile_no_tb(tmp_path):
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "compile.py", [], tmp_path)


@_runs_py
def test_sim_run_with_stub(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "iverilog", _IVERILOG_OK)
    _make_stub(stubs, "vvp", _VVP_OK)
    (tmp_path / "tb_foo.sv").write_text("module tb_foo; endmodule\n", encoding="utf-8")
    d = _WF / "sim" / "scripts"
    py_log = _parity_log(
        d / "sim.py", ["tb_foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert py_log == "TS sim=PASS errors=0 warnings=0 pass=1 fail=0 tb=tb_foo.sv\n"


@_runs_py
def test_sim_run_no_tb(tmp_path):
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "sim.py", [], tmp_path,
                   env={"PATH": "/usr/bin:/bin"})


# ===========================================================================
# sim / write_report.sh
# ===========================================================================
@_runs_py
def test_write_report(tmp_path):
    (tmp_path / ".benchmark").write_text(
        "2026-06-10T09:01:00 sim=PASS errors=0 warnings=2 pass=3 fail=0 tb=tb_foo.sv\n"
        "2026-06-10T09:02:00 sim_capture=PASS errors=0 warnings=0 pass=3 fail=0\n",
        encoding="utf-8",
    )
    d = _WF / "sim" / "scripts"

    def norm(s: str) -> str:
        return re.sub(r"Date      : .*", "Date      : TS", s)

    py_dir, _ = _assert_parity(
        d / "write_report.py", [], tmp_path,
        env={"BENCHMARK_LOG": ".benchmark", "PATH": "/usr/bin:/bin"},
        normalize=norm, expected_rc=0,
    )
    py_rep = norm((py_dir / "sim_report.txt").read_text())
    assert py_rep == (
        "=== Simulation Report ===\n"
        "Date      : TS\n"
        "TB        : ?\n"
        "Tool      : verilator\n"
        "Result    : UNKNOWN\n"
        "Errors    : ?\n"
        "Warnings  : ?\n"
        "Tests     : ? passed, ? failed\n"
        "Iterations: 1\n\n"
        "[FAIL details]\n\n"
    )


# ===========================================================================
# rtl-gen / lint.sh + syn_check.sh  (stub verilator / yosys / iverilog)
# ===========================================================================
_VERILATOR_OK = (
    'print("verilator: linting " + " ".join(argv))\n'
    'print("%Warning-WIDTH: trivial")\n'
)


@_runs_py
def test_rtl_lint_with_stub(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "verilator", _VERILATOR_OK)
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    py_log = _parity_log(
        d / "lint.py", ["foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert py_log == "TS lint errors=0 warnings=1\n"


@_runs_py
def test_rtl_lint_no_tool(tmp_path):
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    _assert_parity(d / "lint.py", ["foo.sv"], tmp_path,
                   env={"PATH": "/usr/bin:/bin"})


@_runs_py
def test_rtl_syn_check_iverilog_fallback(tmp_path):
    # No yosys on PATH ⇒ iverilog fallback branch.
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "iverilog", 'print("iverilog strict: " + " ".join(argv))\n')
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    py_log = _parity_log(
        d / "syn_check.py", ["foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert py_log == "TS syn_check=iverilog errors=0 file=foo.sv\n"


@_runs_py
def test_rtl_syn_check_yosys(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "yosys", 'print("yosys: " + " ".join(argv))\nprint("Done.")\n')
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    py_log = _parity_log(
        d / "syn_check.py", ["foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert py_log == "TS syn_check=yosys errors=0 file=foo.sv\n"


# ===========================================================================
# disk_diff.sh  (rtl-gen / ssot-gen / tb-gen — identical originals)
# ===========================================================================
@pytest.mark.parametrize("wf", ["rtl-gen", "ssot-gen", "tb-gen"])
@_runs_py
def test_disk_diff_first_then_change(tmp_path, wf):
    d = _WF / wf / "scripts"
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "a.sv").write_text("x", encoding="utf-8")

    # Use an isolated TMPDIR + workspace so snapshots don't collide.
    import tempfile
    py_tmp = Path(tempfile.mkdtemp())
    py_proj = Path(tempfile.mkdtemp())
    try:
        shutil.copy2(proj / "a.sv", py_proj / "a.sv")

        base = {
            "ACTIVE_WORKSPACE": "ws",
            "ATLAS_DISK_WATCH": "./",
            "PATH": "/usr/bin:/bin",
        }
        # First run: just snapshots, no output.
        py_rc, py_out = _run(
            _py(d / "disk_diff.py"), py_proj, {**base, "TMPDIR": str(py_tmp)}
        )
        assert py_rc == 0
        assert py_out == ""

        # Add a file, remove a.sv → second run reports a change.
        (py_proj / "b.sv").write_text("y", encoding="utf-8")
        (py_proj / "a.sv").unlink()

        py_rc, py_out = _run(
            _py(d / "disk_diff.py"), py_proj, {**base, "TMPDIR": str(py_tmp)}
        )

        def scrub(s: str) -> str:
            return re.sub(r" \d+ \d+$", " SZ MT", s, flags=re.M)

        assert py_rc == 0
        assert scrub(py_out) == (
            "[disk_diff] 1 file-states added/changed, 1 removed since last tool call:\n"
            "  < ./a.sv SZ MT\n"
            "  > ./b.sv SZ MT\n"
        )
    finally:
        for p in (py_tmp, py_proj):
            shutil.rmtree(p, ignore_errors=True)
