"""Differential equivalence tests for the syn-stage .sh → .py ports.

Each shell script under ``workflow/syn/scripts/`` (except ``check_unmapped.sh``,
owned elsewhere) has a same-named ``.py`` port. These tests assert *invocation
parity*: identical CLI surface, exit codes, and semantically identical
output/artifacts.

The real EDA tools (yosys / openroad / sta) are absent on CI. The differential
technique here is a PATH-stub fake tool: a tiny executable named ``yosys`` (etc.)
that appends its argv to a log and emits the minimal canned stdout/files each
wrapper expects. We prepend the stub dir to PATH, run OLD ``.sh`` vs NEW ``.py``
on the same fixture, then compare recorded argv sequences, exit codes, and
produced artifacts. We also test the tool-missing path (no stub on PATH).

For the pure writers/parsers (write_*.sh, parse_*.sh) we compare the generated
file bytes / parsed values directly — no tool needed.

Run: ``pytest tests/test_sh_port_syn.py -q``
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
# differential is meaningful rather than both-fail-on-missing-PDK).
BUNDLED_LIB = REPO / "pdk" / "sky130" / "lib" / "sky130_fd_sc_hd__ss_100C_1v40.lib"

bash = shutil.which("bash")
pytestmark = pytest.mark.skipif(bash is None, reason="bash not available")


# --------------------------------------------------------------------------- #
# Fixture helpers
# --------------------------------------------------------------------------- #
def _make_ip(root: Path, ip: str = "demo_ip", top: str = "demo_top") -> Path:
    """Create a minimal IP tree: yaml/ssot, list/filelist, rtl source."""
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
    """Write an executable PATH-stub that logs its argv then runs ``body``."""
    stub_dir.mkdir(parents=True, exist_ok=True)
    script = stub_dir / name
    script.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$*" >> {json.dumps(str(argv_log))}\n'
        f"{body}\n"
        "exit 0\n",
        encoding="utf-8",
    )
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
    # Strip any pre-set PDK vars so both sh and py exercise pdk_env default
    # resolution identically.
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


def _norm(text: str) -> str:
    """Drop a trailing-newline difference for stdout comparison."""
    return text.rstrip("\n")


# --------------------------------------------------------------------------- #
# pdk_env: module + CLI parity vs source pdk_env.sh
# --------------------------------------------------------------------------- #
def test_pdk_env_cli_matches_sourced_sh(tmp_path: pytest.TempPathFactory) -> None:
    keys = [
        "PDK_ROOT",
        "SKY130_PDK_ROOT",
        "PDK_LIB_PATH",
        "SKY130_LIB",
        "SKY130_TLEF",
        "SKY130_LEF",
        "SKY130_TRACKS",
        "SKY130_RCX_RULES",
    ]
    sh_snippet = (
        f"source {json.dumps(str(SCRIPTS / 'pdk_env.sh'))}\n"
        + "\n".join(f'printf "%s=%s\\n" {k} "${k}"' for k in keys)
    )
    env = dict(os.environ)
    for k in keys:
        env.pop(k, None)
    sh = subprocess.run(
        [bash, "-c", sh_snippet], capture_output=True, text=True, env=env
    )
    py = subprocess.run(
        [sys.executable, str(SCRIPTS / "pdk_env.py")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert sh.returncode == 0, sh.stderr
    assert py.returncode == 0, py.stderr
    assert _norm(sh.stdout) == _norm(py.stdout)


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
# Pure writer: write_yosys_script — byte-identical run.ys
# --------------------------------------------------------------------------- #
def test_write_yosys_script_artifact_parity(tmp_path: Path) -> None:
    assert BUNDLED_LIB.is_file(), "bundled liberty missing — differential is vacuous"

    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)

    sh = _run([bash, str(SYN / "write_yosys_script.sh"), "demo_ip"], sh_root)
    py = _run([sys.executable, str(SYN / "write_yosys_script.py"), "demo_ip"], py_root)

    assert sh.returncode == py.returncode == 0, (sh.stderr, py.stderr)
    sh_ys = (sh_root / "demo_ip" / "syn" / "run.ys").read_text()
    py_ys = (py_root / "demo_ip" / "syn" / "run.ys").read_text()
    # Paths embedded are absolute under each root; normalise the root prefix.
    assert sh_ys.replace(str(sh_root), "") == py_ys.replace(str(py_root), "")


def test_write_yosys_script_usage_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "write_yosys_script.sh")], tmp_path)
    py = _run([sys.executable, str(SYN / "write_yosys_script.py")], tmp_path)
    assert sh.returncode == py.returncode == 2
    assert "usage:" in sh.stderr.lower()
    assert "usage:" in py.stderr.lower()


def test_write_yosys_script_hook_cmd_args(tmp_path: Path) -> None:
    """No positional arg → both fall back to HOOK_CMD_ARGS."""
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)
    env = dict(os.environ)
    env["HOOK_CMD_ARGS"] = "demo_ip"
    for k in ("SKY130_LIB", "PDK_ROOT"):
        env.pop(k, None)
    sh = subprocess.run(
        [bash, str(SYN / "write_yosys_script.sh")],
        cwd=str(sh_root),
        env=env,
        capture_output=True,
        text=True,
    )
    py = subprocess.run(
        [sys.executable, str(SYN / "write_yosys_script.py")],
        cwd=str(py_root),
        env=env,
        capture_output=True,
        text=True,
    )
    assert sh.returncode == py.returncode == 0, (sh.stderr, py.stderr)
    assert (sh_root / "demo_ip" / "syn" / "run.ys").is_file()
    assert (py_root / "demo_ip" / "syn" / "run.ys").is_file()


# --------------------------------------------------------------------------- #
# Pure parser: parse_area — byte-identical area.json
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
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_ip = _make_ip(sh_root)
    py_ip = _make_ip(py_root)
    _seed_area_inputs(sh_ip)
    _seed_area_inputs(py_ip)

    sh = _run([bash, str(SYN / "parse_area.sh"), "demo_ip"], sh_root)
    py = _run([sys.executable, str(SYN / "parse_area.py"), "demo_ip"], py_root)

    assert sh.returncode == py.returncode == 0, (sh.stderr, py.stderr)
    sh_json = json.loads((sh_ip / "syn" / "out" / "area.json").read_text())
    py_json = json.loads((py_ip / "syn" / "out" / "area.json").read_text())
    assert sh_json == py_json
    # And the parsed values are the ones we seeded.
    assert sh_json["total_cells"] == 23
    assert sh_json["by_kind"]["sequential"]["cells"] == 10  # dfrtp


def test_parse_area_missing_log_rc(tmp_path: Path) -> None:
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)
    sh = _run([bash, str(SYN / "parse_area.sh"), "demo_ip"], sh_root)
    py = _run([sys.executable, str(SYN / "parse_area.py"), "demo_ip"], py_root)
    assert sh.returncode == py.returncode == 2


# --------------------------------------------------------------------------- #
# Pure writer: write_report — markdown parity (minus the embedded timestamp)
# --------------------------------------------------------------------------- #
def _strip_date(md: str) -> str:
    return re.sub(r"^- date    :.*$", "- date    : <DATE>", md, flags=re.M)


def test_write_report_artifact_parity(tmp_path: Path) -> None:
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_ip = _make_ip(sh_root)
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
    for ip_dir in (sh_ip, py_ip):
        out = ip_dir / "syn" / "out"
        out.mkdir(parents=True, exist_ok=True)
        (out / "area.json").write_text(json.dumps(area), encoding="utf-8")
        (out / "syn.log").write_text("Warning: something\n", encoding="utf-8")
        (out / "synth.v").write_text("module demo_top(); endmodule\n", encoding="utf-8")

    sh = _run([bash, str(SYN / "write_report.sh"), "demo_ip"], sh_root)
    py = _run([sys.executable, str(SYN / "write_report.py"), "demo_ip"], py_root)

    assert sh.returncode == py.returncode == 0, (sh.stderr, py.stderr)
    sh_md = (sh_ip / "syn" / "out" / "syn.report.md").read_text()
    py_md = (py_ip / "syn" / "out" / "syn.report.md").read_text()
    assert _strip_date(sh_md) == _strip_date(py_md)


# --------------------------------------------------------------------------- #
# preflight — stdout/stderr + rc parity (tools absent → required yosys missing)
# --------------------------------------------------------------------------- #
def _norm_preflight(text: str, root: Path) -> str:
    """Normalise volatile lines: cwd/scripts path and root prefix."""
    out = text.replace(str(root), "<ROOT>")
    out = re.sub(r"^\[SYN PREFLIGHT\] cwd=.*$", "[SYN PREFLIGHT] cwd=<CWD>", out, flags=re.M)
    out = re.sub(
        r"^\[SYN PREFLIGHT\] scripts=.*$", "[SYN PREFLIGHT] scripts=<DIR>", out, flags=re.M
    )
    return out


def test_preflight_no_ip_parity(tmp_path: Path) -> None:
    """No IP arg: env + tool diagnostics; rc 3 when required yosys is absent."""
    # Ensure yosys is not resolvable: run with a PATH that has no yosys.
    clean_path = str(Path(sys.executable).parent)
    sh = _run([bash, str(SYN / "preflight.sh")], tmp_path, extra_path=None)
    py = _run([sys.executable, str(SYN / "preflight.py")], tmp_path, extra_path=None)
    # rc parity is the load-bearing assertion (3 if yosys missing, 0/4 if present).
    assert sh.returncode == py.returncode
    assert _norm_preflight(sh.stdout, tmp_path) == _norm_preflight(py.stdout, tmp_path)


def test_preflight_with_ip_parity(tmp_path: Path) -> None:
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)
    sh = _run([bash, str(SYN / "preflight.sh"), "demo_ip"], sh_root)
    py = _run([sys.executable, str(SYN / "preflight.py"), "demo_ip"], py_root)
    assert sh.returncode == py.returncode
    assert _norm_preflight(sh.stdout, sh_root) == _norm_preflight(py.stdout, py_root)


def test_preflight_missing_ip_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "preflight.sh"), "nope_ip"], tmp_path)
    py = _run([sys.executable, str(SYN / "preflight.py"), "nope_ip"], tmp_path)
    assert sh.returncode == py.returncode  # 2 (IP dir missing)
    assert sh.returncode == 2


# --------------------------------------------------------------------------- #
# run_yosys — PATH-stub differential (argv log + artifacts + rc)
# --------------------------------------------------------------------------- #
def _run_yosys_stub_body(net_rel: str) -> str:
    """Stub yosys: honour ``-l <log>`` by writing a canned log, plus synth.v."""
    return textwrap.dedent(
        f"""\
        log=""
        prev=""
        for a in "$@"; do
          if [ "$prev" = "-l" ]; then log="$a"; fi
          prev="$a"
        done
        if [ -n "$log" ]; then printf 'canned yosys log\\n' > "$log"; fi
        # emit the mapped netlist the wrapper's downstream expects
        mkdir -p "$(dirname "{net_rel}")"
        printf 'module demo_top(); endmodule\\n' > "{net_rel}"
        echo "stub yosys stdout"
        """
    )


def test_run_yosys_stub_argv_and_rc_parity(tmp_path: Path) -> None:
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_ip = _make_ip(sh_root)
    py_ip = _make_ip(py_root)
    # run.ys must exist for run_yosys
    for ip_dir in (sh_ip, py_ip):
        (ip_dir / "syn" / "out").mkdir(parents=True, exist_ok=True)
        (ip_dir / "syn" / "run.ys").write_text("stat\n", encoding="utf-8")

    sh_argv = tmp_path / "sh_argv.log"
    py_argv = tmp_path / "py_argv.log"
    sh_stub = tmp_path / "sh_bin"
    py_stub = tmp_path / "py_bin"
    net_rel = "demo_ip/syn/out/synth.v"
    _make_stub(sh_stub, "yosys", sh_argv, _run_yosys_stub_body(net_rel))
    _make_stub(py_stub, "yosys", py_argv, _run_yosys_stub_body(net_rel))

    sh = _run([bash, str(SYN / "run_yosys.sh"), "demo_ip"], sh_root, extra_path=str(sh_stub))
    py = _run([sys.executable, str(SYN / "run_yosys.py"), "demo_ip"], py_root, extra_path=str(py_stub))

    assert sh.returncode == py.returncode == 0, (sh.stderr, py.stderr)
    # argv parity: the stub records "yosys -l <log> <script>". Normalise roots.
    sh_args = sh_argv.read_text().replace(str(sh_root), "<ROOT>")
    py_args = py_argv.read_text().replace(str(py_root), "<ROOT>")
    assert sh_args == py_args
    # both wrote a syn.log
    assert (sh_ip / "syn" / "out" / "syn.log").is_file()
    assert (py_ip / "syn" / "out" / "syn.log").is_file()


def test_run_yosys_tool_missing_rc(tmp_path: Path) -> None:
    """No yosys on PATH → rc 3 for both (tool-missing path parity)."""
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_ip = _make_ip(sh_root)
    py_ip = _make_ip(py_root)
    for ip_dir in (sh_ip, py_ip):
        (ip_dir / "syn").mkdir(parents=True, exist_ok=True)
        (ip_dir / "syn" / "run.ys").write_text("stat\n", encoding="utf-8")

    # Build a minimal PATH that contains bash + python but deliberately NO
    # yosys, so the tool-missing branch is exercised deterministically even
    # when the host has yosys installed.
    minimal = tmp_path / "minbin"
    minimal.mkdir()
    for tool in (bash, sys.executable, shutil.which("python3"), shutil.which("env")):
        if tool and Path(tool).exists():
            link = minimal / Path(tool).name
            if not link.exists():
                os.symlink(tool, link)
    min_path = str(minimal)

    sh = _run([bash, str(SYN / "run_yosys.sh"), "demo_ip"], sh_root, override_path=min_path)
    py = _run(
        [sys.executable, str(SYN / "run_yosys.py"), "demo_ip"],
        py_root,
        override_path=min_path,
    )
    assert sh.returncode == py.returncode == 3, (sh.stderr, py.stderr)
    assert "yosys not on PATH" in sh.stderr
    assert "yosys not on PATH" in py.stderr


# --------------------------------------------------------------------------- #
# run_synth — PATH-stub differential (yosys -p script, argv, artifacts, rc)
# --------------------------------------------------------------------------- #
def test_run_synth_stub_parity(tmp_path: Path) -> None:
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)

    sh_argv = tmp_path / "sh_argv.log"
    py_argv = tmp_path / "py_argv.log"
    sh_stub = tmp_path / "sh_bin"
    py_stub = tmp_path / "py_bin"
    # Stub yosys -p: parse "-p <script>", create the netlist/json the script names.
    stub_body = textwrap.dedent(
        """\
        script=""
        prev=""
        for a in "$@"; do
          if [ "$prev" = "-p" ]; then script="$a"; fi
          prev="$a"
        done
        echo "Printing statistics"
        echo "   Number of cells: 1"
        # Pull write_verilog / write_json targets out of the script & touch them.
        net=$(printf '%s\\n' "$script" | sed -n 's/.*write_verilog -noattr -noexpr "\\([^"]*\\)".*/\\1/p')
        js=$(printf '%s\\n'  "$script" | sed -n 's/.*write_json "\\([^"]*\\)".*/\\1/p')
        [ -n "$net" ] && { mkdir -p "$(dirname "$net")"; echo "module demo_top(); endmodule" > "$net"; }
        [ -n "$js" ]  && { mkdir -p "$(dirname "$js")"; echo "{}" > "$js"; }
        """
    )
    _make_stub(sh_stub, "yosys", sh_argv, stub_body)
    _make_stub(py_stub, "yosys", py_argv, stub_body)

    sh = _run([bash, str(SYN / "run_synth.sh"), "demo_ip"], sh_root, extra_path=str(sh_stub))
    py = _run([sys.executable, str(SYN / "run_synth.py"), "demo_ip"], py_root, extra_path=str(py_stub))

    assert sh.returncode == py.returncode == 0, (sh.stderr, py.stderr)
    # The full yosys -p script text recorded by the stub must match (root-normalised).
    sh_args = sh_argv.read_text().replace(str(sh_root), "<ROOT>")
    py_args = py_argv.read_text().replace(str(py_root), "<ROOT>")
    assert sh_args == py_args
    # Artifacts created.
    for root in (sh_root, py_root):
        assert (root / "demo_ip" / "syn" / "demo_ip.netlist.v").is_file()
        assert (root / "demo_ip" / "syn" / "demo_ip.synth.json").is_file()
        assert (root / "demo_ip" / "syn" / "synth.log").is_file()


def test_run_synth_unknown_flag_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "run_synth.sh"), "demo_ip", "--bogus"], tmp_path)
    py = _run([sys.executable, str(SYN / "run_synth.py"), "demo_ip", "--bogus"], tmp_path)
    assert sh.returncode == py.returncode == 2
    assert "unknown flag" in sh.stderr
    assert "unknown flag" in py.stderr


def test_run_synth_no_ip_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "run_synth.sh")], tmp_path)
    py = _run([sys.executable, str(SYN / "run_synth.py")], tmp_path)
    assert sh.returncode == py.returncode == 2


# --------------------------------------------------------------------------- #
# run_openroad — PATH-stub differential (TCL gen, argv, artifacts, rc)
# --------------------------------------------------------------------------- #
def test_run_openroad_missing_pdk_rc(tmp_path: Path) -> None:
    """Empty $HOME → ~/src/OpenROAD PDK absent → rc 1 for both.

    We override HOME at an empty temp dir so the missing-PDK branch is
    exercised deterministically regardless of the host's real ~/src/OpenROAD.
    """
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    home_env = {"HOME": str(empty_home)}
    sh = _run([bash, str(SYN / "run_openroad.sh"), "demo_ip"], sh_root, env_extra=home_env)
    py = _run(
        [sys.executable, str(SYN / "run_openroad.py"), "demo_ip"],
        py_root,
        env_extra=home_env,
    )
    assert sh.returncode == py.returncode == 1, (sh.stderr, py.stderr)
    assert "missing PDK file" in sh.stderr
    assert "missing PDK file" in py.stderr


def test_run_openroad_stub_tcl_and_argv_parity(tmp_path: Path) -> None:
    """Stub PDK (fake HOME) + stub openroad → byte-identical TCL, argv, rc.

    HOME points at a temp tree holding the three PDK files plus
    ``sky130hd.tracks``; a PATH-stub ``openroad`` logs its argv and creates the
    DEF its TCL names. We compare the generated openroad_run.tcl, the recorded
    argv, and the produced artifacts between .sh and .py.
    """
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_ip = _make_ip(sh_root)
    py_ip = _make_ip(py_root)
    # Seed the synth netlist run_openroad requires.
    for ip_dir in (sh_ip, py_ip):
        (ip_dir / "syn").mkdir(parents=True, exist_ok=True)
        (ip_dir / "syn" / "demo_ip.netlist.v").write_text(
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

    sh_argv = tmp_path / "sh_or.log"
    py_argv = tmp_path / "py_or.log"
    sh_stub = tmp_path / "sh_orbin"
    py_stub = tmp_path / "py_orbin"
    # Stub openroad: log argv, create the DEF named by ``write_def`` in the TCL.
    stub_body = textwrap.dedent(
        """\
        tcl="${@: -1}"
        def=$(sed -n 's/^write_def \\(.*\\)$/\\1/p' "$tcl" | head -1)
        [ -n "$def" ] && { mkdir -p "$(dirname "$def")"; echo "stub def" > "$def"; }
        echo "Design area 1 um^2 1% utilization"
        echo "stub openroad ok"
        """
    )
    _make_stub(sh_stub, "openroad", sh_argv, stub_body)
    _make_stub(py_stub, "openroad", py_argv, stub_body)

    sh = _run(
        [bash, str(SYN / "run_openroad.sh"), "demo_ip"],
        sh_root,
        extra_path=str(sh_stub),
        env_extra=home_env,
    )
    py = _run(
        [sys.executable, str(SYN / "run_openroad.py"), "demo_ip"],
        py_root,
        extra_path=str(py_stub),
        env_extra=home_env,
    )
    assert sh.returncode == py.returncode == 0, (sh.stdout, sh.stderr, py.stdout, py.stderr)

    # Generated TCL parity (root-normalised; HOME identical between runs).
    sh_tcl = (sh_ip / "pnr" / "openroad_run.tcl").read_text().replace(str(sh_root), "<ROOT>")
    py_tcl = (py_ip / "pnr" / "openroad_run.tcl").read_text().replace(str(py_root), "<ROOT>")
    assert sh_tcl == py_tcl
    # argv parity (openroad -no_init -exit <tcl>).
    sh_args = sh_argv.read_text().replace(str(sh_root), "<ROOT>")
    py_args = py_argv.read_text().replace(str(py_root), "<ROOT>")
    assert sh_args == py_args
    # DEF + log + report artifacts.
    for root in (sh_root, py_root):
        assert (root / "demo_ip" / "pnr" / "demo_ip.def").is_file()
        assert (root / "demo_ip" / "pnr" / "openroad.log").is_file()
        assert (root / "demo_ip" / "pnr" / "pnr_report.txt").is_file()


def test_run_openroad_unknown_flag_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "run_openroad.sh"), "--bogus"], tmp_path)
    py = _run([sys.executable, str(SYN / "run_openroad.py"), "--bogus"], tmp_path)
    assert sh.returncode == py.returncode == 2


def test_run_openroad_no_ip_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "run_openroad.sh")], tmp_path)
    py = _run([sys.executable, str(SYN / "run_openroad.py")], tmp_path)
    assert sh.returncode == py.returncode == 2


# --------------------------------------------------------------------------- #
# run_sta — usage/flag/rc parity (tool-stub path covered via run_synth delegate)
# --------------------------------------------------------------------------- #
def test_run_sta_no_liberty_rc(tmp_path: Path) -> None:
    """No liberty candidate found → rc 1 for both."""
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)
    # Point at an explicit non-existent liberty so the default search is skipped
    # and both immediately hit the "no liberty file" branch.
    sh = _run(
        [bash, str(SYN / "run_sta.sh"), "demo_ip", "--liberty", str(tmp_path / "nope.lib")],
        sh_root,
    )
    py = _run(
        [sys.executable, str(SYN / "run_sta.py"), "demo_ip", "--liberty", str(tmp_path / "nope.lib")],
        py_root,
    )
    assert sh.returncode == py.returncode == 1
    assert "no liberty file" in sh.stderr
    assert "no liberty file" in py.stderr


def test_run_sta_stub_tcl_and_argv_parity(tmp_path: Path) -> None:
    """Stub yosys (run_synth delegate) + stub sta → sta_run.tcl + argv parity."""
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    sh_ip = _make_ip(sh_root)
    py_ip = _make_ip(py_root)

    # Explicit liberty so the default candidate search is bypassed.
    liberty = tmp_path / "stub.lib"
    liberty.write_text("/* stub liberty */\n", encoding="utf-8")

    sh_argv = tmp_path / "sh_sta.log"
    py_argv = tmp_path / "py_sta.log"
    sh_stub = tmp_path / "sh_stabin"
    py_stub = tmp_path / "py_stabin"

    # Stub yosys -p (for run_synth delegate): create the netlist its script names.
    yosys_body = textwrap.dedent(
        """\
        script=""
        prev=""
        for a in "$@"; do
          if [ "$prev" = "-p" ]; then script="$a"; fi
          prev="$a"
        done
        echo "Printing statistics"
        net=$(printf '%s\\n' "$script" | sed -n 's/.*write_verilog -noattr -noexpr "\\([^"]*\\)".*/\\1/p')
        js=$(printf '%s\\n'  "$script" | sed -n 's/.*write_json "\\([^"]*\\)".*/\\1/p')
        [ -n "$net" ] && { mkdir -p "$(dirname "$net")"; echo "module demo_top(); endmodule" > "$net"; }
        [ -n "$js" ]  && { mkdir -p "$(dirname "$js")"; echo "{}" > "$js"; }
        """
    )
    sta_body = 'echo "stub sta report"'
    for stub, log in ((sh_stub, sh_argv), (py_stub, py_argv)):
        _make_stub(stub, "yosys", log, yosys_body)
        _make_stub(stub, "sta", log, sta_body)

    sh = _run(
        [bash, str(SYN / "run_sta.sh"), "demo_ip", "--liberty", str(liberty)],
        sh_root,
        extra_path=str(sh_stub),
    )
    py = _run(
        [sys.executable, str(SYN / "run_sta.py"), "demo_ip", "--liberty", str(liberty)],
        py_root,
        extra_path=str(py_stub),
    )
    assert sh.returncode == py.returncode == 0, (sh.stdout, sh.stderr, py.stdout, py.stderr)

    sh_tcl = (sh_ip / "syn" / "sta_run.tcl").read_text().replace(str(sh_root), "<ROOT>")
    py_tcl = (py_ip / "syn" / "sta_run.tcl").read_text().replace(str(py_root), "<ROOT>")
    assert sh_tcl == py_tcl
    # The stub log holds both yosys -p ... and sta -no_init -exit ... argv lines.
    sh_args = sh_argv.read_text().replace(str(sh_root), "<ROOT>")
    py_args = py_argv.read_text().replace(str(py_root), "<ROOT>")
    assert sh_args == py_args
    for root in (sh_root, py_root):
        assert (root / "demo_ip" / "syn" / "sta_report.txt").is_file()


def test_run_sta_unknown_flag_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "run_sta.sh"), "demo_ip", "--bogus"], tmp_path)
    py = _run([sys.executable, str(SYN / "run_sta.py"), "demo_ip", "--bogus"], tmp_path)
    assert sh.returncode == py.returncode == 2


def test_run_sta_no_ip_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "run_sta.sh")], tmp_path)
    py = _run([sys.executable, str(SYN / "run_sta.py")], tmp_path)
    assert sh.returncode == py.returncode == 2


# --------------------------------------------------------------------------- #
# auto_syn — orchestrator: usage + missing-IP rc parity
# --------------------------------------------------------------------------- #
def test_auto_syn_no_ip_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "auto_syn.sh")], tmp_path)
    py = _run([sys.executable, str(SYN / "auto_syn.py")], tmp_path)
    assert sh.returncode == py.returncode == 2


def test_auto_syn_missing_ip_dir_rc(tmp_path: Path) -> None:
    sh = _run([bash, str(SYN / "auto_syn.sh"), "nope_ip"], tmp_path)
    py = _run([sys.executable, str(SYN / "auto_syn.py"), "nope_ip"], tmp_path)
    assert sh.returncode == py.returncode == 2


def test_auto_syn_full_pipeline_stub_parity(tmp_path: Path) -> None:
    """End-to-end pipeline with a stub yosys: same final HANDOFF + artifacts."""
    sh_root = tmp_path / "sh"
    py_root = tmp_path / "py"
    _make_ip(sh_root)
    _make_ip(py_root)

    sh_argv = tmp_path / "sh_argv.log"
    py_argv = tmp_path / "py_argv.log"
    sh_stub = tmp_path / "sh_bin"
    py_stub = tmp_path / "py_bin"
    # Stub yosys for the auto_syn pipeline: honour -l <log>, write a stat block
    # into the log AND the synth.v the write_yosys_script run.ys names.
    stub_body = textwrap.dedent(
        """\
        log=""
        prev=""
        for a in "$@"; do
          if [ "$prev" = "-l" ]; then log="$a"; fi
          prev="$a"
        done
        if [ -n "$log" ]; then
          {
            echo "=== demo_top ==="
            echo ""
            echo "      1    5.005   cells"
            echo "      1    5.005   sky130_fd_sc_hd__inv_1"
          } > "$log"
        fi
        # The run.ys names an absolute write_verilog target; recover & create it.
        script="${@: -1}"
        net=$(sed -n 's/.*write_verilog -noattr "\\([^"]*\\)".*/\\1/p' "$script")
        [ -n "$net" ] && { mkdir -p "$(dirname "$net")"; echo "module demo_top(); endmodule" > "$net"; }
        echo "stub yosys ok"
        """
    )
    _make_stub(sh_stub, "yosys", sh_argv, stub_body)
    _make_stub(py_stub, "yosys", py_argv, stub_body)

    # The stub dir is prepended to PATH, so it deterministically shadows any
    # real yosys on the host — the differential runs unconditionally.
    sh = _run([bash, str(SYN / "auto_syn.sh"), "demo_ip"], sh_root, extra_path=str(sh_stub))
    py = _run([sys.executable, str(SYN / "auto_syn.py"), "demo_ip"], py_root, extra_path=str(py_stub))

    assert sh.returncode == py.returncode == 0, (sh.stdout, sh.stderr, py.stdout, py.stderr)
    # Final HANDOFF line parity (root-normalised).
    sh_handoff = [ln for ln in sh.stdout.splitlines() if "SYN HANDOFF" in ln]
    py_handoff = [ln for ln in py.stdout.splitlines() if "SYN HANDOFF" in ln]
    assert sh_handoff and py_handoff
    assert sh_handoff[0].replace(str(sh_root), "<ROOT>") == py_handoff[0].replace(
        str(py_root), "<ROOT>"
    )
    # area.json + report produced in both.
    for root in (sh_root, py_root):
        assert (root / "demo_ip" / "syn" / "out" / "area.json").is_file()
        assert (root / "demo_ip" / "syn" / "out" / "syn.report.md").is_file()
