"""Differential equivalence tests for the .sh -> .py gate/chain ports.

Each gate/chain shell script under workflow/ now has a same-named Python port
beside it. The contract is a 1:1 behavioral port: IDENTICAL CLI, exit codes, and
semantically identical stdout/stderr.

This module verifies that contract DIFFERENTIALLY: it runs the .sh and the .py
on the same minimal fixture and asserts identical streams + exit code.

Scope of the differential method (stated explicitly, per the porting brief):

  * We verify identical FIRST-FAILURE behavior and identical step ORDERING.
    Full green-chain fixtures (a real RTL+SSOT+sim toolchain) are too heavy to
    stand up here; the gate/chain scripts are designed to stop at the first
    failing gate, so a fixture that fails the first gate exercises the argument
    parsing, path resolution, gate invocation, message, and exit-code paths that
    a port can realistically get wrong. Where a script keeps running after a
    failure (set -uo pipefail, no -e), the fixture drives the WHOLE chain (e.g.
    build_gate G1..G8 + JSON artifact), so those cases are full-chain diffs.

  * The .sh and .py runs always use SEPARATE root directories. Several child
    gates mutate the filesystem (mkdir <ip>/tb/cocotb, write JSON artifacts), so
    a shared root would let the first run change state the second run observes —
    a fixture race, not a port divergence.

  * Two byte-level differences are EXPECTED and normalized away, because they are
    not part of the behavioral contract:
      - the embedded absolute root path (differs because the two runs use
        different temp roots) -> normalized to <ROOT>;
      - bash `cd` builtin's own diagnostic line ("<script>: line N: cd: ...:
        No such file or directory") which prefixes the script-authored error on
        a missing root. This is a bash-builtin message Python cannot reproduce
        byte-for-byte (it embeds bash's source path + line number). The
        script-authored line and the exit code DO match exactly.

  * The .sh side is run with `python3` on PATH pinned to sys.executable so child
    gate tracebacks come from the same interpreter on both sides.

If bash is unavailable, the .sh side is skipped and only py_compile + a few
py-only invariants run.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WF = REPO / "workflow"

SCRIPTS = {
    "stage_gate": WF / "req-gen" / "scripts" / "stage_gate",
    "build_gate": WF / "rtl-gen" / "scripts" / "build_gate",
    "new_ip_emit_chain": WF / "ssot-gen" / "scripts" / "new_ip_emit_chain",
    "run_mutation_guard": WF / "mutation" / "scripts" / "run_mutation_guard",
}

BASH = shutil.which("bash")
requires_bash = pytest.mark.skipif(BASH is None, reason="bash not available")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _pinned_path_env() -> dict[str, str]:
    """Return an env whose PATH resolves `python3` to sys.executable.

    The .sh ports call `python3` for child gates; pinning it to the same
    interpreter the .py port uses (sys.executable) removes interpreter-version
    skew from child tracebacks so the differential compares the gate logic, not
    two different Pythons.
    """
    env = dict(os.environ)
    bindir = Path(env.setdefault("_SHPORT_PYBIN", str(_pybin_dir())))
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    return env


_PYBIN_CACHE: Path | None = None


def _pybin_dir() -> Path:
    global _PYBIN_CACHE
    if _PYBIN_CACHE is not None:
        return _PYBIN_CACHE
    import tempfile

    d = Path(tempfile.mkdtemp(prefix="shport_pybin_"))
    link = d / "python3"
    try:
        link.symlink_to(sys.executable)
    except OSError:  # pragma: no cover - fallback for no-symlink filesystems
        link.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
        link.chmod(0o755)
    _PYBIN_CACHE = d
    return d


def _run_sh(script_base: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, str(script_base.with_suffix(".sh")), *args],
        capture_output=True,
        text=True,
        env=_pinned_path_env(),
    )


def _run_py(script_base: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script_base.with_suffix(".py")), *args],
        capture_output=True,
        text=True,
        env=_pinned_path_env(),
    )


def _norm(text: str, *roots: str) -> str:
    """Normalize away root-path prefixes (differ across the two temp roots)."""
    out = text
    for r in roots:
        if not r:
            continue
        rp = str(Path(r))
        out = out.replace(f"/private{rp}", "<ROOT>").replace(rp, "<ROOT>")
    return out


_BASH_CD_DIAG = re.compile(r"^.*: line \d+: cd: .*: No such file or directory\n", re.MULTILINE)


def _strip_bash_cd_diag(text: str) -> str:
    """Drop the bash `cd` builtin's own diagnostic line (not a contract msg)."""
    return _BASH_CD_DIAG.sub("", text)


def _assert_equivalent(
    base: Path,
    sh_args: list[str],
    py_args: list[str],
    *,
    sh_root: str = "",
    py_root: str = "",
    strip_bash_cd: bool = False,
) -> tuple[subprocess.CompletedProcess, subprocess.CompletedProcess]:
    sh = _run_sh(base, sh_args)
    py = _run_py(base, py_args)

    sh_out = _norm(sh.stdout, sh_root)
    py_out = _norm(py.stdout, py_root)
    sh_err = _norm(sh.stderr, sh_root)
    py_err = _norm(py.stderr, py_root)
    if strip_bash_cd:
        sh_err = _strip_bash_cd_diag(sh_err)
        py_err = _strip_bash_cd_diag(py_err)

    assert sh.returncode == py.returncode, (
        f"exit code differs: sh={sh.returncode} py={py.returncode}\n"
        f"sh.err={sh.stderr!r}\npy.err={py.stderr!r}"
    )
    assert sh_out == py_out, f"stdout differs:\n--sh--\n{sh_out}\n--py--\n{py_out}"
    assert sh_err == py_err, f"stderr differs:\n--sh--\n{sh_err}\n--py--\n{py_err}"
    return sh, py


# ---------------------------------------------------------------------------
# 0. structural: every .sh has a same-named .py and all ports py_compile
# ---------------------------------------------------------------------------
def test_every_sh_has_py_port():
    for name, base in SCRIPTS.items():
        assert base.with_suffix(".sh").is_file(), f"missing source .sh for {name}"
        assert base.with_suffix(".py").is_file(), f"missing .py port for {name}"


def test_all_ports_py_compile():
    import py_compile

    for base in SCRIPTS.values():
        py_compile.compile(str(base.with_suffix(".py")), doraise=True)


# ---------------------------------------------------------------------------
# 1. stage_gate
# ---------------------------------------------------------------------------
@requires_bash
def test_stage_gate_unknown_flag():
    _assert_equivalent(SCRIPTS["stage_gate"], ["tb", "ip", "--bogus"], ["tb", "ip", "--bogus"])


@requires_bash
def test_stage_gate_usage_missing_ip():
    _assert_equivalent(SCRIPTS["stage_gate"], ["tb"], ["tb"])


@requires_bash
def test_stage_gate_usage_missing_stage():
    _assert_equivalent(SCRIPTS["stage_gate"], [], [])


@requires_bash
def test_stage_gate_unknown_stage(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    _assert_equivalent(
        SCRIPTS["stage_gate"],
        ["bogus", "ip", "--root", str(root)],
        ["bogus", "ip", "--root", str(root)],
        sh_root=str(root),
        py_root=str(root),
    )


@requires_bash
def test_stage_gate_cannot_cd_to_root(tmp_path):
    # The script-authored "[stage_gate] cannot cd to root: ..." + exit 2 match;
    # the bash `cd` builtin's own diagnostic is stripped (see module docstring).
    missing = tmp_path / "nope"
    _assert_equivalent(
        SCRIPTS["stage_gate"],
        ["tb", "ip", "--root", str(missing)],
        ["tb", "ip", "--root", str(missing)],
        sh_root=str(missing),
        py_root=str(missing),
        strip_bash_cd=True,
    )


@requires_bash
def test_stage_gate_tb_first_failure(tmp_path):
    # Drives the whole tb chain (set -uo pipefail, no -e): the first gate fails
    # on a missing IP, later gates still run. Separate roots avoid the child
    # mkdir/JSON race.
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_root.mkdir()
    py_root.mkdir()
    sh, _ = _assert_equivalent(
        SCRIPTS["stage_gate"],
        ["tb", "__no_ip__", "--root", str(sh_root)],
        ["tb", "__no_ip__", "--root", str(py_root)],
        sh_root=str(sh_root),
        py_root=str(py_root),
    )
    assert sh.returncode == 1
    assert "▣ stage_gate(tb) FAILED" in sh.stdout


@requires_bash
def test_stage_gate_sim_block_or_run(tmp_path):
    # Either BLOCKED (exit 2, no simulator) or runs sim_run; the port must take
    # the SAME branch the shell does (depends on iverilog/verilator presence).
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_root.mkdir()
    py_root.mkdir()
    _assert_equivalent(
        SCRIPTS["stage_gate"],
        ["sim", "__no_ip__", "--root", str(sh_root)],
        ["sim", "__no_ip__", "--root", str(py_root)],
        sh_root=str(sh_root),
        py_root=str(py_root),
    )


# ---------------------------------------------------------------------------
# 2. build_gate
# ---------------------------------------------------------------------------
@requires_bash
def test_build_gate_usage_missing_ip():
    _assert_equivalent(SCRIPTS["build_gate"], [], [])


@requires_bash
def test_build_gate_unknown_flag():
    _assert_equivalent(SCRIPTS["build_gate"], ["--bogus"], ["--bogus"])


@requires_bash
def test_build_gate_extra_positional():
    _assert_equivalent(SCRIPTS["build_gate"], ["a", "b"], ["a", "b"])


@requires_bash
def test_build_gate_missing_ip_dir(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    _assert_equivalent(
        SCRIPTS["build_gate"],
        ["myip", "--root", str(root)],
        ["myip", "--root", str(root)],
        sh_root=str(root),
        py_root=str(root),
    )


@requires_bash
def test_build_gate_g1_fail_full_chain_and_json(tmp_path):
    # Malformed YAML fails G1; with no -e the chain runs G1..G8 and writes the
    # JSON artifact. Verifies full stdout/stderr + byte-identical build_gate.json.
    def _mk(root: Path) -> Path:
        ipd = root / "myip"
        (ipd / "yaml").mkdir(parents=True)
        (ipd / "rtl").mkdir(parents=True)
        (ipd / "yaml" / "myip.ssot.yaml").write_text("a: [unclosed\n")
        return ipd

    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_root.mkdir()
    py_root.mkdir()
    sh_ipd = _mk(sh_root)
    py_ipd = _mk(py_root)

    sh, _ = _assert_equivalent(
        SCRIPTS["build_gate"],
        ["myip", "--root", str(sh_root)],
        ["myip", "--root", str(py_root)],
        sh_root=str(sh_root),
        py_root=str(py_root),
    )
    assert sh.returncode == 1
    sh_json = (sh_ipd / "lint" / "build_gate.json").read_text()
    py_json = (py_ipd / "lint" / "build_gate.json").read_text()
    assert _norm(sh_json, str(sh_root)) == _norm(py_json, str(py_root))
    # Spot-check the JSON shape is what both produced.
    assert '"overall_status": "fail"' in sh_json
    assert '"G1_yaml_valid":"fail"' in sh_json


# ---------------------------------------------------------------------------
# 3. new_ip_emit_chain
# ---------------------------------------------------------------------------
@requires_bash
def test_emit_chain_help_identical():
    sh = _run_sh(SCRIPTS["new_ip_emit_chain"], ["--help"])
    py = _run_py(SCRIPTS["new_ip_emit_chain"], ["--help"])
    assert sh.returncode == 0 and py.returncode == 0
    assert sh.stdout == py.stdout  # byte-identical sed -n '2,21p'


@requires_bash
def test_emit_chain_usage_missing_ip():
    # No IP and no --ip-root -> usage on stderr, exit 2. $0 differs (.sh vs .py),
    # so compare the contract tail of the message, not the whole line.
    sh = _run_sh(SCRIPTS["new_ip_emit_chain"], [])
    py = _run_py(SCRIPTS["new_ip_emit_chain"], [])
    assert sh.returncode == py.returncode == 2
    tail = "<ip_name> [--root <ip-parent>] [--workflow-root <workflow-dir>] [--ip-root <ip-dir>]"
    assert sh.stderr.strip().endswith(tail)
    assert py.stderr.strip().endswith(tail)
    assert sh.stderr.startswith("[emit-chain] usage:")
    assert py.stderr.startswith("[emit-chain] usage:")


@requires_bash
def test_emit_chain_root_missing(tmp_path):
    missing = tmp_path / "nope"
    _assert_equivalent(
        SCRIPTS["new_ip_emit_chain"],
        ["myip", "--root", str(missing)],
        ["myip", "--root", str(missing)],
        sh_root=str(missing),
        py_root=str(missing),
    )


@requires_bash
def test_emit_chain_ip_root_missing(tmp_path):
    missing = tmp_path / "nope"
    _assert_equivalent(
        SCRIPTS["new_ip_emit_chain"],
        ["--ip-root", str(missing)],
        ["--ip-root", str(missing)],
        sh_root=str(missing),
        py_root=str(missing),
    )


@requires_bash
def test_emit_chain_ssot_missing_first_failure(tmp_path):
    # root exists, ip dir absent -> resolves PROJECT/WORKFLOW root (stdout) then
    # FAIL: SSOT missing (stderr), exit 1. Exercises path resolution + the first
    # stop-on-fail gate. Separate roots; merged-order verified by stream compare.
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_root.mkdir()
    py_root.mkdir()
    sh, _ = _assert_equivalent(
        SCRIPTS["new_ip_emit_chain"],
        ["myip", "--root", str(sh_root)],
        ["myip", "--root", str(py_root)],
        sh_root=str(sh_root),
        py_root=str(py_root),
    )
    assert sh.returncode == 1
    assert "missing — run /to-ssot first" in sh.stderr


# ---------------------------------------------------------------------------
# 4. run_mutation_guard
# ---------------------------------------------------------------------------
@requires_bash
def test_mutation_guard_usage_missing_ip():
    # exec wrapper: missing IP -> usage on stderr, exit 2. The ONLY byte-level
    # difference is $0 (the script's own name, .sh vs .py) — legitimately
    # script-specific. Compare exit code + the message body excluding $0.
    sh = _run_sh(SCRIPTS["run_mutation_guard"], [])
    py = _run_py(SCRIPTS["run_mutation_guard"], [])
    assert sh.returncode == py.returncode == 2
    body = "<ip_name> [--root <ip-parent>] [mutation_guard.py args...]"
    assert sh.stderr.startswith("[mutation-guard] usage: ")
    assert py.stderr.startswith("[mutation-guard] usage: ")
    assert sh.stderr.rstrip().endswith(body)
    assert py.stderr.rstrip().endswith(body)
    # the .sh names the .sh, the .py names the .py — both end in their own name
    assert ".sh " in sh.stderr or sh.stderr.split()[2].endswith(".sh")
    assert ".py " in py.stderr or py.stderr.split()[2].endswith(".py")


@requires_bash
def test_mutation_guard_execs_same_guard(tmp_path):
    # The wrapper exec's mutation_guard.py with --root <ROOT> and forwards args.
    # Both run the SAME underlying script, so on a nonexistent IP the underlying
    # mutation_guard.py output + exit code must match between .sh and .py.
    # Use an explicit --root so the default (ip_examples) cwd-dependence is
    # removed and both sides hit the same missing-IP path identically.
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_root.mkdir()
    py_root.mkdir()
    _assert_equivalent(
        SCRIPTS["run_mutation_guard"],
        ["__no_such_ip__", "--root", str(sh_root)],
        ["__no_such_ip__", "--root", str(py_root)],
        sh_root=str(sh_root),
        py_root=str(py_root),
    )
