"""Differential equivalence tests: misc workflow .sh scripts vs their .py ports.

Each test runs the original bash ``.sh`` (via ``bash``) and the new Python
``.py`` (via ``sys.executable``) over identical fixtures and asserts:

  * return-code parity, and
  * key-output parity (stdout, with volatile fields normalised).

The ``.sh`` side is skipped when no ``bash`` is on PATH.  Where a script invokes
an external tool (iverilog, verilator, verilator_coverage, yosys, genhtml) a
PATH-stubbed fake tool is injected so both sides see deterministic behaviour.

These ports reproduce CURRENT behaviour faithfully, including host-dependent
``grep -oP`` / ``set -e`` quirks (see the port docstrings and the porting
report for the flagged bash-isms).  Comparisons therefore use the same host the
``.sh`` runs on, so platform-specific behaviour is exercised identically on both
sides.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Locations.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_WF = _REPO_ROOT / "workflow"

_BASH = shutil.which("bash")
_needs_bash = pytest.mark.skipif(_BASH is None, reason="bash not available")


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


def _sh(script: Path):
    return [str(_BASH), str(script)]


def _py(script: Path):
    return [sys.executable, str(script)]


def _make_stub(directory: Path, name: str, body: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _strip_ts(text: str) -> str:
    """Normalise an ISO-ish leading timestamp at line start (benchmark logs)."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} ", "TS ", text, flags=re.M)


def _assert_parity(sh_script: Path, py_script: Path, args, cwd, *,
                   env=None, normalize=None):
    """Run both sides over the same cwd snapshot and assert rc + stdout parity.

    Because some scripts have on-disk side effects, each side runs in its own
    *copy* of the cwd (created under ``cwd`` so pytest's tmp_path cleanup
    removes them) so neither perturbs the other.  The two run dirs are returned
    so callers can additionally compare side-effect artifacts.
    """
    import tempfile

    normalize = normalize or (lambda s: s)

    sh_dir = Path(tempfile.mkdtemp(dir=str(cwd), prefix="_sh_"))
    py_dir = Path(tempfile.mkdtemp(dir=str(cwd), prefix="_py_"))

    # Copy the fixture tree into both run dirs (skip the run dirs themselves).
    for src, dst in ((cwd, sh_dir), (cwd, py_dir)):
        for item in Path(src).iterdir():
            if item in (sh_dir, py_dir) or item.name.startswith(("_sh_", "_py_")):
                continue
            target = dst / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    sh_rc, sh_out = _run(_sh(sh_script) + list(args), sh_dir, env)
    py_rc, py_out = _run(_py(py_script) + list(args), py_dir, env)

    # Each side runs in its own copy dir; collapse the differing run-dir paths
    # (and their realpath-resolved forms) to a stable placeholder so embedded
    # cwd echoes (e.g. find-mas's realpath header) compare equal.
    def _scrub_rundir(text: str, run_dir: Path) -> str:
        for p in {str(run_dir), os.path.realpath(str(run_dir))}:
            text = text.replace(p, "<RUNDIR>")
        return text

    sh_norm = normalize(_scrub_rundir(sh_out, sh_dir))
    py_norm = normalize(_scrub_rundir(py_out, py_dir))

    assert sh_rc == py_rc, (
        f"rc mismatch for {sh_script.name}: sh={sh_rc} py={py_rc}\n"
        f"--- sh ---\n{sh_out}\n--- py ---\n{py_out}"
    )
    assert sh_norm == py_norm, (
        f"stdout mismatch for {sh_script.name}\n"
        f"--- sh ---\n{sh_norm}\n--- py ---\n{py_norm}"
    )
    return sh_dir, py_dir


# ===========================================================================
# ssot-gen / gen_rtl.sh
# ===========================================================================
@_needs_bash
def test_gen_rtl_no_arg(tmp_path):
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "gen_rtl.sh", d / "gen_rtl.py", [], tmp_path)


@_needs_bash
def test_gen_rtl_with_module(tmp_path):
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "gen_rtl.sh", d / "gen_rtl.py", ["mymod"], tmp_path)


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


@_needs_bash
@pytest.mark.skipif(not _have_cerberus(), reason="cerberus/pyyaml not installed")
def test_validate_yaml_no_schema(tmp_path):
    d = _WF / "ssot-gen" / "scripts"
    _assert_parity(d / "validate_yaml.sh", d / "validate_yaml.py", ["nomod"], tmp_path)


@_needs_bash
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
    _assert_parity(d / "validate_yaml.sh", d / "validate_yaml.py", ["mymod"], tmp_path)


@_needs_bash
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
    _assert_parity(d / "validate_yaml.sh", d / "validate_yaml.py", ["mymod"], tmp_path)


# ===========================================================================
# signoff / run_ip_signoff.sh  (usage / unknown-arg paths)
# ===========================================================================
@_needs_bash
def test_run_ip_signoff_no_ip(tmp_path):
    d = _WF / "signoff" / "scripts"
    _assert_parity(d / "run_ip_signoff.sh", d / "run_ip_signoff.py", [], tmp_path)


@_needs_bash
def test_run_ip_signoff_unknown_arg(tmp_path):
    d = _WF / "signoff" / "scripts"
    _assert_parity(
        d / "run_ip_signoff.sh", d / "run_ip_signoff.py",
        ["foo", "--bogus"], tmp_path, env={"IP_NAME": "foo"},
    )


# ===========================================================================
# ip-contract / run_derive_ip_contract.sh  (usage path; $0 == .sh path)
# ===========================================================================
@_needs_bash
def test_run_derive_ip_contract_no_arg(tmp_path):
    d = _WF / "ip-contract" / "scripts"
    _assert_parity(
        d / "run_derive_ip_contract.sh", d / "run_derive_ip_contract.py",
        [], tmp_path,
    )


# ===========================================================================
# spec-review / post_session.sh  (saves a session file)
# ===========================================================================
@_needs_bash
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
    sh_dir, py_dir = _assert_parity(
        d / "post_session.sh", d / "post_session.py", [], tmp_path,
        env=env, normalize=norm,
    )
    # Both wrote a session file with the same non-volatile body.
    sh_file = next((sh_dir / "bench" / "sessions").glob("*.txt"))
    py_file = next((py_dir / "bench" / "sessions").glob("*.txt"))
    drop_date = lambda t: "\n".join(
        l for l in t.splitlines() if not l.startswith("Date")
    )
    assert drop_date(sh_file.read_text()) == drop_date(py_file.read_text())


# ===========================================================================
# Benchmark-log writers (post_write / capture).  Compare the appended line.
# ===========================================================================
def _read_log(run_dir: Path, name: str = ".bench") -> str:
    p = run_dir / name
    return _strip_ts(p.read_text(encoding="utf-8")) if p.exists() else ""


def _parity_log(sh_script, py_script, args, tmp_path, env, log_name=".bench"):
    """Run both sides, assert rc + stdout parity, and return the two log texts."""
    import tempfile
    sh_dir = Path(tempfile.mkdtemp())
    py_dir = Path(tempfile.mkdtemp())
    try:
        for item in tmp_path.iterdir():
            for dst in (sh_dir, py_dir):
                t = dst / item.name
                shutil.copytree(item, t) if item.is_dir() else shutil.copy2(item, t)
        e_sh = dict(env); e_sh["BENCHMARK_LOG"] = log_name
        e_py = dict(env); e_py["BENCHMARK_LOG"] = log_name
        sh_rc, sh_out = _run(_sh(sh_script) + list(args), sh_dir, e_sh)
        py_rc, py_out = _run(_py(py_script) + list(args), py_dir, e_py)
        assert sh_rc == py_rc, f"rc {sh_rc} != {py_rc}"
        assert sh_out == py_out
        return _read_log(sh_dir, log_name), _read_log(py_dir, log_name)
    finally:
        shutil.rmtree(sh_dir, ignore_errors=True)
        shutil.rmtree(py_dir, ignore_errors=True)


@_needs_bash
def test_sim_post_write_no_log_when_grep_p_unsupported(tmp_path):
    # FLAGGED: sim/post_write has no fallback; on hosts where grep -oP fails the
    # path is empty and NOTHING is logged.
    d = _WF / "sim" / "scripts"
    sh_log, py_log = _parity_log(
        d / "post_write.sh", d / "post_write.py", [], tmp_path,
        {"HOOK_TOOL_ARGS": 'path="a/b.sv",x=1'},
    )
    assert sh_log == py_log


@_needs_bash
def test_rtl_post_write_fallback(tmp_path):
    d = _WF / "rtl-gen" / "scripts"
    sh_log, py_log = _parity_log(
        d / "post_write.sh", d / "post_write.py", [], tmp_path,
        {"HOOK_TOOL_ARGS": 'path="a/b.sv",x=1'},
    )
    assert sh_log == py_log
    assert "rtl_write" in sh_log


@_needs_bash
def test_tb_post_write_tc_fallback(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    sh_log, py_log = _parity_log(
        d / "post_write.sh", d / "post_write.py", [], tmp_path,
        {"HOOK_TOOL_ARGS": 'path="tc_x.sv",x=1'},
    )
    assert sh_log == py_log
    assert "tc_write" in sh_log


@_needs_bash
def test_sim_capture(tmp_path):
    d = _WF / "sim" / "scripts"
    out = "Compile error: foo\n[PASS] test1\nTESTS=2 PASS=2 FAIL=0"
    sh_log, py_log = _parity_log(
        d / "sim_capture.sh", d / "sim_capture.py", [], tmp_path,
        {"HOOK_TOOL_OUTPUT": out},
    )
    assert sh_log == py_log


@_needs_bash
def test_tb_sim_result_capture(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    out = "warning: minor\n[PASS] t1\nTESTS=1 PASS=1 FAIL=0"
    sh_log, py_log = _parity_log(
        d / "sim_result_capture.sh", d / "sim_result_capture.py", [], tmp_path,
        {"HOOK_TOOL_OUTPUT": out},
    )
    assert sh_log == py_log


@_needs_bash
def test_rtl_error_capture(tmp_path):
    d = _WF / "rtl-gen" / "scripts"
    out = "line ok\nERROR: bad thing\nfailed here\nmore"
    sh_log, py_log = _parity_log(
        d / "error_capture.sh", d / "error_capture.py", [], tmp_path,
        {"HOOK_TOOL_OUTPUT": out},
    )
    assert sh_log == py_log
    assert "rtl_errors" in sh_log


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


@_needs_bash
def test_sim_wave_info(tmp_path):
    (tmp_path / "test.vcd").write_text(_VCD, encoding="utf-8")
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "wave_info.sh", d / "wave_info.py", ["test.vcd"], tmp_path)


@_needs_bash
def test_sim_wave_info_none(tmp_path):
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "wave_info.sh", d / "wave_info.py", [], tmp_path)


@_needs_bash
def test_sim_debug_wave_info(tmp_path):
    (tmp_path / "test.vcd").write_text(_VCD, encoding="utf-8")
    d = _WF / "sim_debug" / "scripts"
    _assert_parity(d / "wave_info.sh", d / "wave_info.py", ["test.vcd"], tmp_path)


@_needs_bash
def test_sim_debug_wave_info_not_ascii(tmp_path):
    # ASCII-VCD guard path (exit 2).
    (tmp_path / "bad.vcd").write_bytes(b"\x00\x01\x02 binary not a vcd " * 20)
    d = _WF / "sim_debug" / "scripts"
    _assert_parity(d / "wave_info.sh", d / "wave_info.py", ["bad.vcd"], tmp_path)


@_needs_bash
def test_sig_search_no_arg(tmp_path):
    d = _WF / "sim_debug" / "scripts"
    _assert_parity(d / "sig_search.sh", d / "sig_search.py", [], tmp_path)


@_needs_bash
def test_sig_search_hit_and_miss(tmp_path):
    (tmp_path / "test.vcd").write_text(_VCD, encoding="utf-8")
    d = _WF / "sim_debug" / "scripts"
    # Hit: exit 1 (the .sh's last [ HITS -eq 0 ] is false).
    _assert_parity(d / "sig_search.sh", d / "sig_search.py", ["clk"], tmp_path)
    # Miss: exit 0.
    _assert_parity(d / "sig_search.sh", d / "sig_search.py", ["nope_xyz"], tmp_path)


# ===========================================================================
# rtl-gen / find-mas.sh
# ===========================================================================
def _norm_find_mas(s: str) -> str:
    return re.sub(r"Modified: [0-9 :-]+", "Modified: TS", s)


@_needs_bash
def test_find_mas_empty(tmp_path):
    d = _WF / "rtl-gen" / "scripts"
    _assert_parity(d / "find-mas.sh", d / "find-mas.py", ["."], tmp_path,
                   normalize=_norm_find_mas)


@_needs_bash
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
    _assert_parity(d / "find-mas.sh", d / "find-mas.py", ["."], tmp_path,
                   normalize=_norm_find_mas)


@_needs_bash
def test_find_mas_module_name_env(tmp_path):
    ip = tmp_path / "myip"
    (ip / "mas").mkdir(parents=True)
    (ip / "mas" / "myip_mas.md").write_text("# MAS\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    _assert_parity(d / "find-mas.sh", d / "find-mas.py", ["."], tmp_path,
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


@_needs_bash
def test_tb_coverage_no_tc(tmp_path):
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "coverage.sh", d / "coverage.py", ["foo"], tmp_path)


@_needs_bash
def test_tb_coverage_missing_dut(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "coverage.sh", d / "coverage.py", ["nope"], tmp_path)


@_needs_bash
def test_gen_tc_generates_skeleton(tmp_path):
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    sh_dir, py_dir = _assert_parity(
        d / "gen_tc.sh", d / "gen_tc.py", ["foo"], tmp_path,
    )
    # Generated tc file must be byte-identical.
    assert (sh_dir / "tc_foo.sv").read_text() == (py_dir / "tc_foo.sv").read_text()


@_needs_bash
def test_gen_tc_already_exists(tmp_path):
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    (tmp_path / "tc_foo.sv").write_text("// existing\n", encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "gen_tc.sh", d / "gen_tc.py", ["foo"], tmp_path)


@_needs_bash
def test_gen_tc_dut_not_found(tmp_path):
    # Passing "foo.sv" makes the .sh look for "foo.sv.sv" (no .sv strip).
    (tmp_path / "foo.sv").write_text(_DUT_SV, encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(d / "gen_tc.sh", d / "gen_tc.py", ["foo.sv"], tmp_path)


# ===========================================================================
# tb-gen / check_no_ip_coverage_workarounds.sh
# ===========================================================================
@_needs_bash
def test_check_no_ip_coverage_workarounds_pass(tmp_path):
    (tmp_path / "myip" / "tb").mkdir(parents=True)
    (tmp_path / "myip" / "tb" / "test_runner.py").write_text("x", encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(
        d / "check_no_ip_coverage_workarounds.sh",
        d / "check_no_ip_coverage_workarounds.py",
        [], tmp_path, env={"IP_NAME": "myip"},
    )


@_needs_bash
def test_check_no_ip_coverage_workarounds_fail(tmp_path):
    (tmp_path / "myip" / "tb").mkdir(parents=True)
    (tmp_path / "myip" / "tb" / "my_coverage_summary.py").write_text("x", encoding="utf-8")
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(
        d / "check_no_ip_coverage_workarounds.sh",
        d / "check_no_ip_coverage_workarounds.py",
        [], tmp_path, env={"IP_NAME": "myip"},
    )


@_needs_bash
def test_check_no_ip_coverage_workarounds_no_dir(tmp_path):
    d = _WF / "tb-gen" / "scripts"
    _assert_parity(
        d / "check_no_ip_coverage_workarounds.sh",
        d / "check_no_ip_coverage_workarounds.py",
        [], tmp_path, env={"IP_NAME": "ghost"},
    )


# ===========================================================================
# coverage / coverage_gaps.sh
# ===========================================================================
@_needs_bash
def test_coverage_gaps_missing_annotated(tmp_path):
    d = _WF / "coverage" / "scripts"
    _assert_parity(d / "coverage_gaps.sh", d / "coverage_gaps.py", ["dut"], tmp_path)


@_needs_bash
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
    _assert_parity(d / "coverage_gaps.sh", d / "coverage_gaps.py", ["dut", "5"], tmp_path)


@_needs_bash
def test_coverage_gaps_top_flag(tmp_path):
    ann = tmp_path / "dut" / "cov" / "annotated"
    ann.mkdir(parents=True)
    (ann / "a.cov").write_text("%000000  x\n%000000  y\n%000000  z\n", encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_gaps.sh", d / "coverage_gaps.py", ["dut", "--top", "2"], tmp_path,
    )


# ===========================================================================
# coverage / coverage_merge.sh  (stub verilator_coverage)
# ===========================================================================
_VC_STUB = r"""
args=("$@")
for ((i=0;i<${#args[@]};i++)); do
  if [ "${args[$i]}" = "--write" ]; then j=$((i+1)); : > "${args[$j]}"; fi
done
echo "verilator_coverage: ${args[*]}"
"""


@_needs_bash
def test_coverage_merge_no_tool(tmp_path):
    d = _WF / "coverage" / "scripts"
    (tmp_path / "dut" / "cocotb").mkdir(parents=True)
    (tmp_path / "dut" / "cocotb" / "coverage.dat").write_text("x", encoding="utf-8")
    # PATH without verilator_coverage on either side.
    _assert_parity(
        d / "coverage_merge.sh", d / "coverage_merge.py", ["dut"], tmp_path,
        env={"PATH": "/usr/bin:/bin"},
    )


@_needs_bash
def test_coverage_merge_no_dat(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "verilator_coverage", _VC_STUB)
    (tmp_path / "dut").mkdir()
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_merge.sh", d / "coverage_merge.py", ["dut"], tmp_path,
        env={"PATH": f"{stubs}:/usr/bin:/bin"},
    )


@_needs_bash
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
        d / "coverage_merge.sh", d / "coverage_merge.py", ["dut"], tmp_path,
        env={"PATH": f"{stubs}:/usr/bin:/bin"}, normalize=norm,
    )


# ===========================================================================
# coverage / coverage_report.sh  (stub verilator_coverage; no genhtml)
# ===========================================================================
_VC_REPORT_STUB = r"""
args=("$@"); mode=""
for ((i=0;i<${#args[@]};i++)); do
  case "${args[$i]}" in
    --annotate) mode=annotate; ann="${args[$((i+1))]}";;
    --write-info) mode=info; info="${args[$((i+1))]}";;
  esac
done
if [ "$mode" = annotate ]; then mkdir -p "$ann"; echo "annotated written";
elif [ "$mode" = info ]; then
  printf 'SF:foo.sv\nDA:1,5\nDA:2,0\nBRDA:1,0,0,2\nBRDA:1,0,1,0\nend_of_record\n' > "$info"
  echo "info written";
else echo " Total coverage: 50.00%"; fi
"""


@_needs_bash
def test_coverage_report_no_merged(tmp_path):
    d = _WF / "coverage" / "scripts"
    (tmp_path / "dut" / "cov").mkdir(parents=True)
    _assert_parity(d / "coverage_report.sh", d / "coverage_report.py", ["dut"], tmp_path)


@_needs_bash
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
        d / "coverage_report.sh", d / "coverage_report.py", ["dut"], tmp_path,
        env={"PATH": f"{stubs}:/usr/bin:/bin"}, normalize=norm,
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


@_needs_bash
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_merge_two(tmp_path):
    sim = tmp_path / "vdut" / "sim"
    sim.mkdir(parents=True)
    (sim / "a.vcd").write_text(_VCD_A, encoding="utf-8")
    (sim / "b.vcd").write_text(_VCD_B, encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_merge.sh", d / "coverage_vcd_merge.py", ["vdut"], tmp_path,
    )


@_needs_bash
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_merge_none(tmp_path):
    (tmp_path / "vdut").mkdir()
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_merge.sh", d / "coverage_vcd_merge.py", ["vdut"], tmp_path,
    )


@_needs_bash
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_toggle_text(tmp_path):
    sim = tmp_path / "vdut" / "sim"
    sim.mkdir(parents=True)
    (sim / "a.vcd").write_text(_VCD_A, encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_toggle.sh", d / "coverage_vcd_toggle.py", ["vdut"], tmp_path,
    )


@_needs_bash
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_toggle_json(tmp_path):
    sim = tmp_path / "vdut" / "sim"
    sim.mkdir(parents=True)
    (sim / "a.vcd").write_text(_VCD_A, encoding="utf-8")
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_toggle.sh", d / "coverage_vcd_toggle.py",
        ["vdut", "--json"], tmp_path,
    )


@_needs_bash
@pytest.mark.skipif(not _adapters_present(), reason="vcd adapters missing")
def test_coverage_vcd_toggle_no_vcd(tmp_path):
    (tmp_path / "vdut").mkdir()
    d = _WF / "coverage" / "scripts"
    _assert_parity(
        d / "coverage_vcd_toggle.sh", d / "coverage_vcd_toggle.py", ["vdut"], tmp_path,
    )


# ===========================================================================
# sim / compile.sh + sim.sh  (stub iverilog/vvp)
# ===========================================================================
_IVERILOG_OK = 'echo "iverilog: fake compile of $*"\necho "warning: minor"\nexit 0\n'
_VVP_OK = 'echo "[PASS] test_one"\necho "TESTS=1 PASS=1 FAIL=0"\nexit 0\n'


@_needs_bash
def test_sim_compile_with_stub(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "iverilog", _IVERILOG_OK)
    (tmp_path / "tb_foo.sv").write_text("module tb_foo; endmodule\n", encoding="utf-8")
    d = _WF / "sim" / "scripts"
    sh_log, py_log = _parity_log(
        d / "compile.sh", d / "compile.py", ["tb_foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert sh_log == py_log


@_needs_bash
def test_sim_compile_no_tb(tmp_path):
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "compile.sh", d / "compile.py", [], tmp_path)


@_needs_bash
def test_sim_run_with_stub(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "iverilog", _IVERILOG_OK)
    _make_stub(stubs, "vvp", _VVP_OK)
    (tmp_path / "tb_foo.sv").write_text("module tb_foo; endmodule\n", encoding="utf-8")
    d = _WF / "sim" / "scripts"
    sh_log, py_log = _parity_log(
        d / "sim.sh", d / "sim.py", ["tb_foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert sh_log == py_log


@_needs_bash
def test_sim_run_no_tb(tmp_path):
    d = _WF / "sim" / "scripts"
    _assert_parity(d / "sim.sh", d / "sim.py", [], tmp_path,
                   env={"PATH": "/usr/bin:/bin"})


# ===========================================================================
# sim / write_report.sh
# ===========================================================================
@_needs_bash
def test_write_report(tmp_path):
    (tmp_path / ".benchmark").write_text(
        "2026-06-10T09:01:00 sim=PASS errors=0 warnings=2 pass=3 fail=0 tb=tb_foo.sv\n"
        "2026-06-10T09:02:00 sim_capture=PASS errors=0 warnings=0 pass=3 fail=0\n",
        encoding="utf-8",
    )
    d = _WF / "sim" / "scripts"

    def norm(s: str) -> str:
        return re.sub(r"Date      : .*", "Date      : TS", s)

    sh_dir, py_dir = _assert_parity(
        d / "write_report.sh", d / "write_report.py", [], tmp_path,
        env={"BENCHMARK_LOG": ".benchmark", "PATH": "/usr/bin:/bin"},
        normalize=norm,
    )
    sh_rep = norm((sh_dir / "sim_report.txt").read_text())
    py_rep = norm((py_dir / "sim_report.txt").read_text())
    assert sh_rep == py_rep


# ===========================================================================
# rtl-gen / lint.sh + syn_check.sh  (stub verilator / yosys / iverilog)
# ===========================================================================
_VERILATOR_OK = 'echo "verilator: linting $*"\necho "%Warning-WIDTH: trivial"\nexit 0\n'


@_needs_bash
def test_rtl_lint_with_stub(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "verilator", _VERILATOR_OK)
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    sh_log, py_log = _parity_log(
        d / "lint.sh", d / "lint.py", ["foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert sh_log == py_log


@_needs_bash
def test_rtl_lint_no_tool(tmp_path):
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    _assert_parity(d / "lint.sh", d / "lint.py", ["foo.sv"], tmp_path,
                   env={"PATH": "/usr/bin:/bin"})


@_needs_bash
def test_rtl_syn_check_iverilog_fallback(tmp_path):
    # No yosys on PATH ⇒ iverilog fallback branch.
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "iverilog", 'echo "iverilog strict: $*"\nexit 0\n')
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    sh_log, py_log = _parity_log(
        d / "syn_check.sh", d / "syn_check.py", ["foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert sh_log == py_log


@_needs_bash
def test_rtl_syn_check_yosys(tmp_path):
    stubs = tmp_path / "stubs"
    _make_stub(stubs, "yosys", 'echo "yosys: $*"\necho "Done."\nexit 0\n')
    (tmp_path / "foo.sv").write_text("module foo; endmodule\n", encoding="utf-8")
    d = _WF / "rtl-gen" / "scripts"
    sh_log, py_log = _parity_log(
        d / "syn_check.sh", d / "syn_check.py", ["foo.sv"], tmp_path,
        {"PATH": f"{stubs}:/usr/bin:/bin"},
    )
    assert sh_log == py_log


# ===========================================================================
# disk_diff.sh  (rtl-gen / ssot-gen / tb-gen — identical originals)
# ===========================================================================
@pytest.mark.parametrize("wf", ["rtl-gen", "ssot-gen", "tb-gen"])
@_needs_bash
def test_disk_diff_first_then_change(tmp_path, wf):
    d = _WF / wf / "scripts"
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "a.sv").write_text("x", encoding="utf-8")

    # Use isolated TMPDIR + workspace per side so snapshots don't collide.
    import tempfile
    sh_tmp = Path(tempfile.mkdtemp())
    py_tmp = Path(tempfile.mkdtemp())
    sh_proj = Path(tempfile.mkdtemp())
    py_proj = Path(tempfile.mkdtemp())
    try:
        for dst in (sh_proj, py_proj):
            shutil.copy2(proj / "a.sv", dst / "a.sv")

        base = {
            "ACTIVE_WORKSPACE": "ws",
            "ATLAS_DISK_WATCH": "./",
            "PATH": "/usr/bin:/bin",
        }
        # First run: just snapshots, no output.
        sh_rc, sh_out = _run(
            _sh(d / "disk_diff.sh"), sh_proj, {**base, "TMPDIR": str(sh_tmp)}
        )
        py_rc, py_out = _run(
            _py(d / "disk_diff.py"), py_proj, {**base, "TMPDIR": str(py_tmp)}
        )
        assert sh_rc == py_rc == 0
        assert sh_out == py_out == ""

        # Add a file, remove a.sv → second run reports a change.
        for dst in (sh_proj, py_proj):
            (dst / "b.sv").write_text("y", encoding="utf-8")
            (dst / "a.sv").unlink()

        sh_rc, sh_out = _run(
            _sh(d / "disk_diff.sh"), sh_proj, {**base, "TMPDIR": str(sh_tmp)}
        )
        py_rc, py_out = _run(
            _py(d / "disk_diff.py"), py_proj, {**base, "TMPDIR": str(py_tmp)}
        )

        def scrub(s: str) -> str:
            return re.sub(r" \d+ \d+$", " SZ MT", s, flags=re.M)

        assert sh_rc == py_rc
        assert scrub(sh_out) == scrub(py_out)
    finally:
        for p in (sh_tmp, py_tmp, sh_proj, py_proj):
            shutil.rmtree(p, ignore_errors=True)
