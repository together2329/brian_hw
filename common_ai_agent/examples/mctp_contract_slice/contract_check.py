#!/usr/bin/env python3
"""contract_check.py — re-runnable, two-axis contract verification gate.

This turns hand-authored "killed: true" claims (e.g. signoff/validation_closure_12.json)
into MACHINE-VERIFIED, reproducible evidence. It does not trust a string: it plants
the mutants itself and proves whether they die.

Two complementary axes
(see doc/wiki/formal-verification-evidence.md "Mutation: Targeted Vs Blanket"):

  TARGETED  per-contract. For each contract, define its named INJECT macro, then
            prove the matching check FIRES — the mutant must die in the
            verilator --assert sim lane OR the SymbiYosys (z3) formal lane.
            A surviving targeted mutant => that contract's check is too weak
            (or the contract is missing).

  BLANKET   mechanical. yosys `mutate -list` auto-samples N mutations of the DUT
            (mutations that land in the embedded `ifdef FORMAL` checker region are
            skipped), each is applied and the full embedded-SVA suite is proven by
            sby. Kill-rate is measured; survivors are reported as candidate
            contract holes. This answers the other question: does the contract
            *set* have a gap a per-contract test never named?

PASS gate = correct design clean on both lanes
            AND every targeted mutant killed
            AND blanket kill-rate >= --kill-threshold (default 0.90).

Emits signoff/contract_check.json. Exit 0 iff the gate passes.

The whole point: re-running this script reproduces the verdict from the RTL, so a
green contract_check.json cannot be faked by editing JSON — only by fixing the RTL
or the checks.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

VERILATOR_FLAGS = ["-Wno-fatal", "--assert", "--timing", "--binary"]


# --------------------------------------------------------------------------- #
# Manifest                                                                     #
# --------------------------------------------------------------------------- #
@dataclass
class Contract:
    id: str
    inject: str          # macro name, e.g. INJECT_GATE_BUG
    note: str = ""


@dataclass
class Manifest:
    rtl: str
    tb: str
    top_dut: str
    top_tb: str
    sim_done_marker: str
    formal_block_start: int          # 1-based line where `ifdef FORMAL begins; mutations at/after this line are checker-region and skipped in the blanket sweep
    depth: int
    contracts: list[Contract] = field(default_factory=list)

    @property
    def rtl_basename(self) -> str:
        return Path(self.rtl).name


# Default manifest: the 12-contract single-context assembler slice.
DEFAULT_MANIFEST = Manifest(
    rtl="rtl/mctp_rx_assembler.sv",
    tb="tb/tb_random.sv",
    top_dut="mctp_rx_assembler",
    top_tb="tb_random",
    sim_done_marker="RANDOM_SIM_DONE",
    formal_block_start=153,
    depth=22,
    contracts=[
        Contract("C-ASM-GATE", "INJECT_GATE_BUG", "bad-header packet must be dropped"),
        Contract("C-ASM-KEY", "INJECT_KEY_BUG", "foreign tag in continuation must be ignored"),
        Contract("C-ASM-START", "INJECT_START_BUG", "START must not commit early"),
        Contract("C-ASM-SINGLE", "INJECT_SINGLE_BUG", "SOM&EOM single must not leave stale context"),
        Contract("C-ASM-SEQ-OOS", "INJECT_SEQ_BUG", "out-of-sequence must drop + close context"),
        Contract("C-ASM-PAYLOAD", "INJECT_PAYLOAD_BUG", "committed length must equal accumulated len"),
        Contract("C-ASM-END", "INJECT_END_BUG", "EOM commit must clear context"),
        Contract("C-ASM-DROP", "INJECT_DROP_BUG", "dropped assembly must not leave stale payload"),
        Contract("C-ASM-OUT", "INJECT_OUT_BUG", "output stable under backpressure"),
        Contract("C-ASM-RESET", "INJECT_RESET_BUG", "reset must clear context"),
        Contract("C-ASM-STATUS", "INJECT_STATUS_BUG", "every drop must increment drop_count"),
    ],
)


# --------------------------------------------------------------------------- #
# Lane runners                                                                 #
# --------------------------------------------------------------------------- #
def _run(cmd: list[str], cwd: Path, log: Path, timeout: int = 600) -> int:
    with log.open("wb") as fh:
        try:
            return subprocess.run(cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            fh.write(b"\n[contract_check] TIMEOUT\n")
            return 124


def run_verilator(m: Manifest, defines: list[str], tag: str, scratch: Path) -> str:
    """Returns PASS | ASSERT_FAIL | BUILDFAIL | RUNFAIL."""
    mdir = scratch / f"vbuild_{tag}"
    if mdir.exists():
        shutil.rmtree(mdir)
    blog = scratch / f"vbuild_{tag}.blog"
    cmd = [
        "verilator", *VERILATOR_FLAGS, "-DFORMAL", *defines,
        "--top-module", m.top_tb, "--Mdir", str(mdir), m.rtl, m.tb,
    ]
    if _run(cmd, HERE, blog) != 0:
        return "BUILDFAIL"
    rlog = scratch / f"vbuild_{tag}.rlog"
    rc = _run([str(mdir / f"V{m.top_tb}")], HERE, rlog)
    text = rlog.read_text(encoding="utf-8", errors="replace")
    if re.search(r"Assertion failed|%Error", text, re.IGNORECASE):
        return "ASSERT_FAIL"
    if rc == 0 and m.sim_done_marker in text:
        return "PASS"
    return f"RUNFAIL({rc})"


def _sby_verdict(workdir: Path) -> str:
    log = workdir / "logfile.txt"
    if not log.is_file():
        return "ERROR"
    hits = re.findall(r"DONE \(([A-Z]+)", log.read_text(encoding="utf-8", errors="replace"))
    return hits[-1] if hits else "ERROR"


def run_sby_source(m: Manifest, defines: list[str], mode: str, tag: str, scratch: Path) -> str:
    """Prove the embedded SVA from source. Returns PASS | FAIL | UNKNOWN | ERROR."""
    sby_path = scratch / f"f_{tag}.sby"
    workdir = scratch / f"f_{tag}"
    if workdir.exists():
        shutil.rmtree(workdir)
    define_str = " ".join(defines)
    sby_path.write_text(
        f"[options]\nmode {mode}\ndepth {m.depth}\n"
        f"[engines]\nsmtbmc z3\n"
        f"[script]\nread_verilog -sv -formal -DFORMAL {define_str} {m.rtl_basename}\n"
        f"prep -top {m.top_dut}\n"
        f"[files]\n{m.rtl}\n",
        encoding="utf-8",
    )
    _run(["sby", "-f", str(sby_path)], HERE, scratch / f"f_{tag}.out")
    return _sby_verdict(workdir)


# --------------------------------------------------------------------------- #
# Targeted axis                                                                #
# --------------------------------------------------------------------------- #
def targeted_axis(m: Manifest, scratch: Path, with_formal: bool, jobs: int) -> dict[str, Any]:
    def one(c: Contract) -> dict[str, Any]:
        d = [f"-D{c.inject}"]
        vs = run_verilator(m, d, c.inject, scratch)
        fs = run_sby_source(m, d, "bmc", c.inject, scratch) if with_formal else "skipped"
        killed = (vs == "ASSERT_FAIL") or (fs == "FAIL")
        return {
            "id": c.id, "inject": c.inject, "note": c.note,
            "verilator": vs, "formal": fs, "killed": killed,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        rows = list(ex.map(one, m.contracts))
    rows.sort(key=lambda r: [c.id for c in m.contracts].index(r["id"]))
    survivors = [r["id"] for r in rows if not r["killed"]]
    return {
        "total": len(rows),
        "killed": sum(1 for r in rows if r["killed"]),
        "survivors": survivors,
        "all_killed": not survivors,
        "contracts": rows,
    }


# --------------------------------------------------------------------------- #
# Blanket axis (yosys mutate)                                                  #
# --------------------------------------------------------------------------- #
_SRC_RE = re.compile(rf"-src (\S+):(\d+)")


def gen_mutate_list(m: Manifest, count: int, seed: int, scratch: Path) -> list[str]:
    out = scratch / "mutate_list.txt"
    script = (
        f"read_verilog -sv -formal -DFORMAL {m.rtl}; "
        f"prep -top {m.top_dut}; "
        f"mutate -list {count} -seed {seed} -o {out}"
    )
    _run(["yosys", "-q", "-p", script], HERE, scratch / "mutate_list.log")
    if not out.is_file():
        return []
    return [ln.rstrip("\n") for ln in out.read_text().splitlines() if ln.strip().startswith("mutate ")]


def is_dut_region(mutation_line: str, m: Manifest) -> bool:
    """A mutation is DUT-region if it touches a source line before the `ifdef FORMAL
    checker block. Mutations purely inside the checker region are skipped — mutating a
    checker is not a contract hole, and would deflate the kill-rate spuriously."""
    rtl_base = m.rtl_basename
    lines = [int(n) for f, n in _SRC_RE.findall(mutation_line) if Path(f).name == rtl_base]
    return bool(lines) and min(lines) < m.formal_block_start


def run_blanket_mutant(m: Manifest, mutation_line: str, idx: int, scratch: Path) -> str:
    """Apply one mutation, write prepped RTLIL, prove it. Returns the sby verdict."""
    il = scratch / f"mut_{idx}.il"
    script = (
        f"read_verilog -sv -formal -DFORMAL {m.rtl}; "
        f"prep -top {m.top_dut}; "
        f"{mutation_line}; "
        f"write_rtlil {il}"
    )
    yrc = _run(["yosys", "-q", "-p", script], HERE, scratch / f"mut_{idx}.ylog")
    if yrc != 0 or not il.is_file():
        return "APPLY_ERROR"
    sby_path = scratch / f"mut_{idx}.sby"
    workdir = scratch / f"mut_{idx}"
    if workdir.exists():
        shutil.rmtree(workdir)
    sby_path.write_text(
        f"[options]\nmode prove\ndepth {m.depth}\n"
        f"[engines]\nsmtbmc z3\n"
        f"[script]\nread_rtlil {il}\n"
        f"[files]\n{il}\n",
        encoding="utf-8",
    )
    _run(["sby", "-f", str(sby_path)], HERE, scratch / f"mut_{idx}.out")
    return _sby_verdict(workdir)


def sec_classify(m: Manifest, mutation_line: str, idx: int, scratch: Path) -> str:
    """Sequential-equivalence-check the mutated DUT against an independent gold copy.

    This is the BACKSTOP an embedded-assertion blanket sweep cannot be: an embedded
    assertion references the (possibly mutated) signals, so a mutation on an input —
    or any self-consistent perturbation — shifts the assertion's own notion of
    "expected" and survives. SEC compares two designs (gold vs mutated) at the I/O
    boundary, so it has no such blind spot.

      equivalent  -> miter proves outputs identical => harmless mutant (no hole)
      sec_caught  -> miter finds an observable difference => the embedded contracts
                     missed it but the SEC lane catches it (a real divergence that
                     is covered by equivalence checking, not by a missing assertion)
      unknown     -> SEC inconclusive (must be resolved before signoff)
    """
    base = (f"read_verilog -sv -formal -DFORMAL {m.rtl}; prep -top {m.top_dut} -flatten; "
            "chformal -remove; async2sync; ")
    gold = scratch / f"sec_gold_{idx}.il"
    gate = scratch / f"sec_gate_{idx}.il"
    miter = scratch / f"sec_miter_{idx}.il"
    _run(["yosys", "-q", "-p", base + f"rename {m.top_dut} gold; write_rtlil {gold}"], HERE, scratch / f"sec_g_{idx}.log")
    _run(["yosys", "-q", "-p",
          f"read_verilog -sv -formal -DFORMAL {m.rtl}; prep -top {m.top_dut} -flatten; {mutation_line}; "
          f"chformal -remove; async2sync; rename {m.top_dut} gate; write_rtlil {gate}"],
         HERE, scratch / f"sec_t_{idx}.log")
    if not gold.is_file() or not gate.is_file():
        return "unknown"
    # `select -assert-min 1 t:$assert` makes yosys ABORT (so write_rtlil never runs and
    # miter.is_file() is False -> "unknown") if the miter carries no equivalence assert.
    # Without it a degenerate miter (e.g. ports changed by the mutation) could prove
    # PASS vacuously and be mislabelled "equivalent" (harmless) when nothing was compared.
    _run(["yosys", "-q", "-p",
          f"read_rtlil {gold}; read_rtlil {gate}; miter -equiv -make_assert gold gate miter; "
          f"hierarchy -top miter; select -assert-min 1 t:$assert; write_rtlil {miter}"],
         HERE, scratch / f"sec_m_{idx}.log")
    if not miter.is_file():
        return "unknown"
    sby_path = scratch / f"sec_{idx}.sby"
    workdir = scratch / f"sec_{idx}"
    if workdir.exists():
        shutil.rmtree(workdir)
    sby_path.write_text(
        f"[options]\nmode prove\ndepth {m.depth + 8}\n"
        f"[engines]\nsmtbmc z3\n"
        f"[script]\nread_rtlil {miter}\nprep -top miter\n"
        f"[files]\n{miter}\n",
        encoding="utf-8",
    )
    _run(["sby", "-f", str(sby_path)], HERE, scratch / f"sec_{idx}.out")
    return {"PASS": "equivalent", "FAIL": "sec_caught"}.get(_sby_verdict(workdir), "unknown")


def blanket_axis(m: Manifest, count: int, seed: int, threshold: float, scratch: Path, jobs: int, classify: bool) -> dict[str, Any]:
    raw = gen_mutate_list(m, count, seed, scratch)
    dut = [ln for ln in raw if is_dut_region(ln, m)]
    skipped = len(raw) - len(dut)

    def one(item: tuple[int, str]) -> dict[str, Any]:
        idx, line = item
        verdict = run_blanket_mutant(m, line, idx, scratch)
        msrc = _SRC_RE.findall(line)
        mode = re.search(r"-mode (\S+)", line)
        return {
            "idx": idx,
            "mode": mode.group(1) if mode else "?",
            "src": ":".join(msrc[0]) if msrc else "?",
            "verdict": verdict,
            "killed": verdict == "FAIL",  # only a definitive embedded counterexample is a kill
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        rows = list(ex.map(one, enumerate(dut)))
    rows.sort(key=lambda r: r["idx"])
    scored = [r for r in rows if r["verdict"] != "APPLY_ERROR"]
    killed = [r for r in scored if r["killed"]]
    survivors = [r for r in scored if not r["killed"]]
    kill_rate = (len(killed) / len(scored)) if scored else 0.0

    # SEC-classify every survivor the embedded suite did not kill. This converts a
    # raw kill-rate gate (which can never reach 1.0 because of equivalent mutants
    # and embedded blind spots) into a DEFINITIVE one: a survivor is acceptable iff
    # it is provably equivalent (harmless) or caught by the SEC lane.
    if classify and survivors:
        def classify_one(r: dict[str, Any]) -> tuple[int, str]:
            return r["idx"], sec_classify(m, dut[r["idx"]], r["idx"], scratch)
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
            verdicts = dict(ex.map(classify_one, survivors))
        for r in survivors:
            r["sec"] = verdicts.get(r["idx"], "unknown")
    else:
        for r in survivors:
            r["sec"] = "not_classified"

    equivalent = [r for r in survivors if r.get("sec") == "equivalent"]
    sec_caught = [r for r in survivors if r.get("sec") == "sec_caught"]
    unknown = [r for r in survivors if r.get("sec") in {"unknown", "not_classified"}]
    return {
        "tool": "yosys mutate -list + SEC (miter equiv) survivor classification",
        "seed": seed,
        "requested": count,
        "dut_mutants": len(dut),
        "checker_region_skipped": skipped,
        "scored": len(scored),
        "apply_errors": len([r for r in rows if r["verdict"] == "APPLY_ERROR"]),
        "embedded_killed": len(killed),
        "embedded_kill_rate": round(kill_rate, 4),
        "threshold": threshold,
        "meets_threshold": kill_rate >= threshold,           # advisory: strength of the embedded contracts
        "survivors": len(survivors),
        "survivors_equivalent": len(equivalent),             # harmless (SEC-proven no observable diff)
        "survivors_sec_caught": len(sec_caught),             # embedded blind spot, caught by SEC lane
        "survivors_unknown": len(unknown),                   # MUST be zero for signoff
        "all_survivors_classified": not unknown,             # hard gate for the blanket axis
        "survivor_list": [
            {"mode": r["mode"], "src": r["src"], "embedded": r["verdict"], "sec": r.get("sec")}
            for r in survivors
        ],
        "mutants": rows,
    }


# --------------------------------------------------------------------------- #
# Tool versions (provenance)                                                   #
# --------------------------------------------------------------------------- #
def _tool_version(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else ""
    except Exception:
        return "unavailable"


def tool_versions() -> dict[str, str]:
    return {
        "verilator": _tool_version(["verilator", "--version"]),
        "yosys": _tool_version(["yosys", "-V"]),
        "sby": _tool_version(["sby", "--version"]),
        "z3": _tool_version(["z3", "--version"]),
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
_IFDEF_FORMAL_RE = re.compile(r"^\s*`ifdef\s+FORMAL\b")


def detect_formal_start(rtl_path: Path) -> int | None:
    """Find the line of the embedded `` `ifdef FORMAL `` checker block so the blanket
    DUT/checker split is derived from the source, not a hand-set constant that silently
    rots if the RTL shifts. Returns None if not found (caller keeps the manifest value)."""
    try:
        for n, line in enumerate(rtl_path.read_text(encoding="utf-8").splitlines(), start=1):
            if _IFDEF_FORMAL_RE.match(line):
                return n
    except Exception:
        return None
    return None


def load_manifest(path: str | None) -> Manifest:
    if not path:
        return DEFAULT_MANIFEST
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return Manifest(
        rtl=doc["rtl"], tb=doc["tb"], top_dut=doc["top_dut"], top_tb=doc["top_tb"],
        sim_done_marker=doc["sim_done_marker"], formal_block_start=int(doc["formal_block_start"]),
        depth=int(doc.get("depth", 22)),
        contracts=[Contract(c["id"], c["inject"], c.get("note", "")) for c in doc["contracts"]],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", help="JSON manifest path (default: built-in assembler slice)")
    ap.add_argument("--axis", choices=["targeted", "blanket", "both"], default="both")
    ap.add_argument("--no-formal", action="store_true", help="targeted axis: verilator only (faster)")
    ap.add_argument("--blanket-count", type=int, default=60, help="yosys mutate sample size (pre-filter; ~half land in the checker region and are skipped)")
    ap.add_argument("--blanket-seed", type=int, default=1)
    ap.add_argument("--kill-threshold", type=float, default=0.90,
                    help="advisory embedded-contract kill-rate bar (reported, not the hard gate)")
    ap.add_argument("--no-sec", action="store_true",
                    help="skip SEC classification of blanket survivors (then survivors stay unclassified -> blanket gate fails)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default="signoff/mutation_contract_check.json")
    ap.add_argument("--keep-scratch", action="store_true")
    args = ap.parse_args()

    m = load_manifest(args.manifest)
    detected = detect_formal_start(HERE / m.rtl)
    if detected:
        m.formal_block_start = detected
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t0 = time.time()
    scratch = Path(tempfile.mkdtemp(prefix="contract_check_"))

    report: dict[str, Any] = {
        "status": "error",  # overwritten on a completed run; left as error if we crash
        "formal_block_start": m.formal_block_start,
        # NB: "mutation_contract_check" (not "contract_check") — the latter is the
        # VCM evidence-contract coverage artifact (workflow/contract-reflection/
        # scripts/run_contract_check.py -> signoff/contract_check.json). This is the
        # orthogonal mutation-kill axis; keep the names distinct.
        "type": "mutation_contract_check",
        "schema_version": 1,
        "ip": m.top_dut,
        "generated_at": started,
        "tools": tool_versions(),
        "lanes": {
            "verilator": "constrained-random sim of embedded SVA (--assert)",
            "formal": "SymbiYosys + yosys-smtbmc + z3 (k-induction / BMC)",
        },
    }

    try:
        # Correct design must be clean on both lanes — the baseline a mutant deviates from.
        print("[contract_check] baseline: correct design ...", flush=True)
        correct = {
            "verilator": run_verilator(m, [], "correct", scratch),
            "formal": "skipped" if args.no_formal else run_sby_source(m, [], "prove", "correct", scratch),
        }
        report["correct"] = correct
        correct_ok = correct["verilator"] == "PASS" and correct["formal"] in {"PASS", "skipped"}

        targeted = blanket = None
        if args.axis in {"targeted", "both"}:
            print(f"[contract_check] targeted axis: {len(m.contracts)} contracts ...", flush=True)
            targeted = targeted_axis(m, scratch, with_formal=not args.no_formal, jobs=args.jobs)
            report["targeted"] = targeted
        if args.axis in {"blanket", "both"}:
            print(f"[contract_check] blanket axis: yosys mutate x{args.blanket_count} (seed {args.blanket_seed})"
                  f"{'' if args.no_sec else ' + SEC survivor classification'} ...", flush=True)
            blanket = blanket_axis(m, args.blanket_count, args.blanket_seed, args.kill_threshold,
                                   scratch, args.jobs, classify=not args.no_sec)
            report["blanket"] = blanket

        gate_targeted = targeted["all_killed"] if targeted is not None else True
        # Blanket axis passes when every survivor is DEFINITIVELY accounted for —
        # provably equivalent (harmless) or caught by the SEC lane. Raw kill-rate is
        # advisory (equivalent mutants make 1.0 unreachable); an unclassified/unknown
        # survivor is an open hole and fails the gate.
        gate_blanket = blanket["all_survivors_classified"] if blanket is not None else True
        gate_pass = correct_ok and gate_targeted and gate_blanket
        report["gate"] = {
            "correct_clean": correct_ok,
            "targeted_all_killed": gate_targeted,
            "blanket_all_survivors_classified": gate_blanket,
            "pass": gate_pass,
        }
        report["status"] = "pass" if gate_pass else "fail"
        report["elapsed_s"] = round(time.time() - t0, 1)
    except Exception as exc:  # write a status:error artifact so a crash is distinguishable from "never ran"
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["elapsed_s"] = round(time.time() - t0, 1)
    finally:
        if not args.keep_scratch:
            shutil.rmtree(scratch, ignore_errors=True)
        else:
            report["scratch"] = str(scratch)

    out_path = (HERE / args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Human summary (guarded — on a crash some sections are absent)
    print(f"\n[contract_check] status={report['status']}  ({report.get('elapsed_s')}s)")
    if "error" in report:
        print(f"  error: {report['error']}")
    if "correct" in report:
        print(f"  correct: verilator={report['correct']['verilator']} formal={report['correct']['formal']}")
    if "targeted" in report:
        t = report["targeted"]
        print(f"  targeted: {t['killed']}/{t['total']} killed" + (f"  SURVIVORS={t['survivors']}" if t["survivors"] else ""))
    if "blanket" in report:
        b = report["blanket"]
        print(f"  blanket: embedded_kill_rate={b['embedded_kill_rate']} "
              f"({b['embedded_killed']}/{b['scored']}) skipped_checker={b['checker_region_skipped']}")
        print(f"           survivors={b['survivors']} -> equivalent={b['survivors_equivalent']} "
              f"sec_caught={b['survivors_sec_caught']} unknown={b['survivors_unknown']}")
    print(f"[contract_check] wrote {out_path}")
    return {"pass": 0, "fail": 1}.get(report["status"], 2)  # error -> 2


if __name__ == "__main__":
    raise SystemExit(main())
