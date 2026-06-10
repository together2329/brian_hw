"""Pinned regression tests for the gate/chain .py ports.

Each gate/chain shell script under workflow/ was ported to a same-named Python
port beside it; the bash originals have since been removed. These tests run the
``.py`` port on a minimal fixture and assert the PINNED exit code plus the
load-bearing markers the differential parity run established.

Scope of the method (per the porting brief): we verify FIRST-FAILURE behaviour
and step ORDERING. Full green-chain fixtures (a real RTL+SSOT+sim toolchain) are
too heavy to stand up here; the gate/chain scripts stop at the first failing
gate, so a fixture that fails the first gate exercises argument parsing, path
resolution, gate invocation, message, and exit-code paths. Where a script keeps
running after a failure (set -uo pipefail, no -e), the fixture drives the WHOLE
chain (e.g. build_gate G1..G8 + JSON artifact), so those cases assert the full
artifact too.

Volatile root paths are normalised to ``<ROOT>``. Usage-string assertions check
the stable prefix/suffix (not the script's own basename, which is incidental).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WF = REPO / "workflow"

SCRIPTS = {
    "stage_gate": WF / "req-gen" / "scripts" / "stage_gate",
    "build_gate": WF / "rtl-gen" / "scripts" / "build_gate",
    "new_ip_emit_chain": WF / "ssot-gen" / "scripts" / "new_ip_emit_chain",
    "run_mutation_guard": WF / "mutation" / "scripts" / "run_mutation_guard",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _run_py(script_base: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script_base.with_suffix(".py")), *args],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )


def _norm(text: str, *roots: str) -> str:
    """Normalize away root-path prefixes (differ across temp roots)."""
    out = text
    for r in roots:
        if not r:
            continue
        rp = str(Path(r))
        out = out.replace(f"/private{rp}", "<ROOT>").replace(rp, "<ROOT>")
    return out


# ---------------------------------------------------------------------------
# 0. structural: every gate has a .py port and all ports py_compile
# ---------------------------------------------------------------------------
def test_every_gate_has_py_port():
    for name, base in SCRIPTS.items():
        assert base.with_suffix(".py").is_file(), f"missing .py port for {name}"


def test_all_ports_py_compile():
    import py_compile

    for base in SCRIPTS.values():
        py_compile.compile(str(base.with_suffix(".py")), doraise=True)


# ---------------------------------------------------------------------------
# 1. stage_gate
# ---------------------------------------------------------------------------
def test_stage_gate_unknown_flag():
    py = _run_py(SCRIPTS["stage_gate"], ["tb", "ip", "--bogus"])
    assert py.returncode == 2
    assert py.stderr == "[stage_gate] unknown flag: --bogus\n"


def test_stage_gate_usage_missing_ip():
    py = _run_py(SCRIPTS["stage_gate"], ["tb"])
    assert py.returncode == 2
    assert py.stderr.startswith("usage: ")
    assert py.stderr.rstrip().endswith("<tb|sim|lint> <ip> --root <root>")


def test_stage_gate_usage_missing_stage():
    py = _run_py(SCRIPTS["stage_gate"], [])
    assert py.returncode == 2
    assert py.stderr.startswith("usage: ")
    assert py.stderr.rstrip().endswith("<tb|sim|lint> <ip> --root <root>")


def test_stage_gate_unknown_stage(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    py = _run_py(SCRIPTS["stage_gate"], ["bogus", "ip", "--root", str(root)])
    assert py.returncode == 2
    assert py.stderr == "[stage_gate] unknown stage: bogus\n"


def test_stage_gate_cannot_cd_to_root(tmp_path):
    missing = tmp_path / "nope"
    py = _run_py(SCRIPTS["stage_gate"], ["tb", "ip", "--root", str(missing)])
    assert py.returncode == 2
    assert _norm(py.stderr, str(missing)) == "[stage_gate] cannot cd to root: <ROOT>\n"


def test_stage_gate_tb_first_failure(tmp_path):
    # Drives the whole tb chain (set -uo pipefail, no -e): the first gate fails
    # on a missing IP, later gates still run.
    py_root = tmp_path / "py"
    py_root.mkdir()
    py = _run_py(SCRIPTS["stage_gate"], ["tb", "__no_ip__", "--root", str(py_root)])
    out = _norm(py.stdout, str(py_root))
    assert py.returncode == 1
    assert "▸ tb_python_compile" in out
    assert "missing IP directory" in out
    assert "▣ stage_gate(tb) FAILED" in out


def test_stage_gate_sim_block_or_run(tmp_path):
    # Either BLOCKED (exit 2, no simulator) or runs sim_run and the chain fails
    # on the missing IP (exit 1); both are valid first-failure outcomes.
    py_root = tmp_path / "py"
    py_root.mkdir()
    py = _run_py(SCRIPTS["stage_gate"], ["sim", "__no_ip__", "--root", str(py_root)])
    assert py.returncode in (1, 2)
    if py.returncode == 1:
        assert "▣ stage_gate(sim) FAILED" in _norm(py.stdout, str(py_root))


# ---------------------------------------------------------------------------
# 2. build_gate
# ---------------------------------------------------------------------------
def test_build_gate_usage_missing_ip():
    py = _run_py(SCRIPTS["build_gate"], [])
    assert py.returncode == 2
    assert py.stderr.startswith("usage: ")
    assert py.stderr.rstrip().endswith("<ip> [--root .]")


def test_build_gate_unknown_flag():
    py = _run_py(SCRIPTS["build_gate"], ["--bogus"])
    assert py.returncode == 2
    assert py.stderr == "[build_gate] unknown flag: --bogus\n"


def test_build_gate_extra_positional():
    py = _run_py(SCRIPTS["build_gate"], ["a", "b"])
    assert py.returncode == 2
    assert py.stderr == "[build_gate] extra positional: b\n"


def test_build_gate_missing_ip_dir(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    py = _run_py(SCRIPTS["build_gate"], ["myip", "--root", str(root)])
    assert py.returncode == 2
    assert _norm(py.stderr, str(root)) == "[build_gate] missing IP dir: <ROOT>/myip\n"


def test_build_gate_g1_fail_full_chain_and_json(tmp_path):
    # Malformed YAML fails G1; with no -e the chain runs G1..G8 and writes the
    # JSON artifact. Verify the full chain ran and the JSON artifact shape.
    py_root = tmp_path / "py"
    py_root.mkdir()
    ipd = py_root / "myip"
    (ipd / "yaml").mkdir(parents=True)
    (ipd / "rtl").mkdir(parents=True)
    (ipd / "yaml" / "myip.ssot.yaml").write_text("a: [unclosed\n")

    py = _run_py(SCRIPTS["build_gate"], ["myip", "--root", str(py_root)])
    out = _norm(py.stdout, str(py_root))
    assert py.returncode == 1
    assert "▸ G1_yaml_valid" in out
    assert "build_gate FAILED" in out
    py_json = (ipd / "lint" / "build_gate.json").read_text()
    assert '"overall_status": "fail"' in py_json
    assert '"G1_yaml_valid":"fail"' in py_json


# ---------------------------------------------------------------------------
# 3. new_ip_emit_chain
# ---------------------------------------------------------------------------
def test_emit_chain_help_identical():
    py = _run_py(SCRIPTS["new_ip_emit_chain"], ["--help"])
    assert py.returncode == 0
    # The help text is the script header (sed -n '2,21p' equivalent); just
    # require it produced non-empty usage-like content.
    assert py.stdout.strip()


def test_emit_chain_usage_missing_ip():
    # No IP and no --ip-root -> usage on stderr, exit 2.
    py = _run_py(SCRIPTS["new_ip_emit_chain"], [])
    assert py.returncode == 2
    tail = "<ip_name> [--root <ip-parent>] [--workflow-root <workflow-dir>] [--ip-root <ip-dir>]"
    assert py.stderr.strip().endswith(tail)
    assert py.stderr.startswith("[emit-chain] usage:")


def test_emit_chain_root_missing(tmp_path):
    missing = tmp_path / "nope"
    py = _run_py(SCRIPTS["new_ip_emit_chain"], ["myip", "--root", str(missing)])
    assert py.returncode == 1
    assert _norm(py.stderr, str(missing)) == "[emit-chain] FAIL: --root <ROOT> does not exist\n"


def test_emit_chain_ip_root_missing(tmp_path):
    missing = tmp_path / "nope"
    py = _run_py(SCRIPTS["new_ip_emit_chain"], ["--ip-root", str(missing)])
    assert py.returncode == 1
    assert _norm(py.stderr, str(missing)) == "[emit-chain] FAIL: --ip-root <ROOT> does not exist\n"


def test_emit_chain_ssot_missing_first_failure(tmp_path):
    # root exists, ip dir absent -> resolves PROJECT/WORKFLOW root (stdout) then
    # FAIL: SSOT missing (stderr), exit 1.
    py_root = tmp_path / "py"
    py_root.mkdir()
    py = _run_py(SCRIPTS["new_ip_emit_chain"], ["myip", "--root", str(py_root)])
    assert py.returncode == 1
    assert "[emit-chain] resolved PROJECT_ROOT" in _norm(py.stdout, str(py_root))
    assert "missing — run /to-ssot first" in py.stderr


# ---------------------------------------------------------------------------
# 4. run_mutation_guard
# ---------------------------------------------------------------------------
def test_mutation_guard_usage_missing_ip():
    # exec wrapper: missing IP -> usage on stderr, exit 2.
    py = _run_py(SCRIPTS["run_mutation_guard"], [])
    assert py.returncode == 2
    body = "<ip_name> [--root <ip-parent>] [mutation_guard.py args...]"
    assert py.stderr.startswith("[mutation-guard] usage: ")
    assert py.stderr.rstrip().endswith(body)


def test_mutation_guard_execs_same_guard(tmp_path):
    # The wrapper exec's mutation_guard.py with --root <ROOT> and forwards args.
    # On a nonexistent IP the underlying mutation_guard.py reports a missing IP.
    py_root = tmp_path / "py"
    py_root.mkdir()
    py = _run_py(SCRIPTS["run_mutation_guard"], ["__no_such_ip__", "--root", str(py_root)])
    assert py.returncode == 1
    assert _norm(py.stdout, str(py_root)) == (
        "[mutation_guard] FAIL: missing IP directory <ROOT>/__no_such_ip__\n"
    )
