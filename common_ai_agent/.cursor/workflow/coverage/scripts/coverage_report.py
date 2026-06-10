#!/usr/bin/env python3
"""coverage_report.py — Python port of coverage_report.sh (coverage).

Generate ``annotated/`` + ``.info`` from ``<DUT>/cov/merged.dat`` and write the
UI snapshot/history, then delegate to ``ssot_coverage_summary.py``.

CLI / env contract preserved (bash ``set -e``):
  * DUT = ``$HOOK_CMD_ARGS`` else first positional argument else ``gpio_pad``;
    spaces stripped.  ``--html`` / ``--no-html`` scanned across all args.
  * Missing ``<DUT>/cov/merged.dat`` ⇒ ERROR + exit 1.
  * HTML auto-enables when ``genhtml`` is on PATH (unless ``--no-html``).
  * Runs ``verilator_coverage`` for annotate + write-info, optional genhtml,
    computes the LCOV line/branch summary with the same awk idioms, writes
    ``coverage.json`` and appends ``history.jsonl``, then calls
    ``ssot_coverage_summary.py`` (rc 3 → soft note; other non-zero → propagate)
    and pretty-prints the SSOT-filtered summary.

Side-effect outputs match the .sh: annotated/, coverage.info, coverage.json,
history.jsonl, optional html/.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _run_tail(cmd: "list[str]", n: int) -> None:
    """Run cmd (2>&1) and print its last n lines, like ``... 2>&1 | tail -n``."""
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    lines = proc.stdout.splitlines()
    for line in lines[-n:]:
        print(line)


def _lcov_summary(info: Path) -> "tuple[int, int, int, int]":
    """Replicate the awk/grep LCOV counters.

    lines_total = grep -c "^DA:"
    lines_hit   = awk -F'[:,]' '/^DA:/ && $3 != "0" {n++}'
    brs_total   = grep -c "^BRDA:"
    brs_hit     = awk -F, '/^BRDA:/ {n=split; if last != "0" && last != "-" h++}'
    """
    lines_total = lines_hit = brs_total = brs_hit = 0
    try:
        text = info.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, 0, 0, 0
    for raw in text.splitlines():
        if raw.startswith("DA:"):
            lines_total += 1
            # awk -F'[:,]' field 3 (1-indexed): DA:line,hits → [DA, line, hits]
            parts = raw.replace(":", ",").split(",")
            if len(parts) >= 3 and parts[2] != "0":
                lines_hit += 1
        elif raw.startswith("BRDA:"):
            brs_total += 1
            # awk -F, last field
            fields = raw.split(",")
            last = fields[-1]
            if last not in ("0", "-"):
                brs_hit += 1
    return lines_total, lines_hit, brs_total, brs_hit


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    dut = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "") or "gpio_pad"
    want_html = False
    no_html = False
    for arg in argv:
        if arg == "--html":
            want_html = True
        elif arg == "--no-html":
            no_html = True
    dut = dut.replace(" ", "")

    out = Path(dut) / "cov"
    merged = out / "merged.dat"

    if not merged.is_file():
        print(f"ERROR: {merged} not found — run /coverage-merge first.")
        return 1

    if not want_html and not no_html and shutil.which("genhtml") is not None:
        want_html = True

    print("=== Annotated source ===")
    _run_tail(
        ["verilator_coverage", str(merged), "--annotate", str(out / "annotated") + "/"],
        5,
    )

    print("")
    print("=== LCOV .info ===")
    _run_tail(
        ["verilator_coverage", str(merged), "--write-info", str(out / "coverage.info")],
        3,
    )

    if want_html:
        if shutil.which("genhtml") is not None:
            print("")
            print("=== HTML report (genhtml) ===")
            proc = subprocess.run(
                ["genhtml", str(out / "coverage.info"), "-o", str(out / "html"), "--quiet"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            tail = proc.stdout.splitlines()[-5:]
            if proc.returncode != 0:
                print("WARN: genhtml exited non-zero — partial HTML may be present")
            else:
                for line in tail:
                    print(line)
            print(f"HTML index: {out / 'html'}/index.html")
        else:
            print("")
            print("WARN: genhtml not available — skipping HTML.")
            print("      Install with: brew install lcov   (provides genhtml)")

    print("")
    print("=== Raw LCOV summary (line / all BRDA %) ===")
    info = out / "coverage.info"
    lines_total, lines_hit, brs_total, brs_hit = _lcov_summary(info)

    if lines_total > 0:
        lpct = f"{(lines_hit / lines_total) * 100:.2f}"
        print(f"Lines    : {lines_hit}/{lines_total}  ({lpct}%)")
    else:
        lpct = "0.00"
        print("Lines    : 0/0  (no DA records — coverage.info empty?)")
    if brs_total > 0:
        bpct = f"{(brs_hit / brs_total) * 100:.2f}"
        print(f"All BRDA : {brs_hit}/{brs_total}  ({bpct}%)")
        print(
            "           raw Verilator BRDA may include toggle/expression bins; "
            "SSOT summary filters control-flow branches."
        )
    else:
        bpct = "0.00"

    # TOG_LINE=$(verilator_coverage merged 2>&1 | grep -i "total coverage" | head -1)
    tog_proc = subprocess.run(
        ["verilator_coverage", str(merged)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    tog_line = ""
    for line in tog_proc.stdout.splitlines():
        if "total coverage" in line.lower():
            tog_line = line
            break
    if tog_line:
        # echo "Overall  : ${TOG_LINE# }" — strip a single leading space.
        print(f"Overall  : {tog_line[1:] if tog_line.startswith(' ') else tog_line}")

    # Write coverage.json snapshot.
    timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    timestamp_epoch = int(time.time())
    coverage_json = out / "coverage.json"
    coverage_json.write_text(
        "{\n"
        f'  "timestamp_iso": "{timestamp_iso}",\n'
        f'  "timestamp_epoch": {timestamp_epoch},\n'
        f'  "dut": "{dut}",\n'
        f'  "lines":    {{ "hit": {lines_hit}, "total": {lines_total}, "pct": {lpct} }},\n'
        f'  "branches": {{ "hit": {brs_hit},   "total": {brs_total},   "pct": {bpct} }},\n'
        f'  "html_available": {1 if want_html else 0}\n'
        "}\n",
        encoding="utf-8",
    )

    out.mkdir(parents=True, exist_ok=True)
    history = out / "history.jsonl"
    with open(history, "a", encoding="utf-8") as handle:
        handle.write(
            '{"timestamp_iso":"%s","timestamp_epoch":%d,'
            '"lines":{"hit":%d,"total":%d,"pct":%s},'
            '"branches":{"hit":%d,"total":%d,"pct":%s}}\n'
            % (
                timestamp_iso, timestamp_epoch,
                lines_hit, lines_total, lpct,
                brs_hit, brs_total, bpct,
            )
        )
    # HIST_COUNT=$(wc -l < history.jsonl | tr -d ' ')
    hist_count = sum(1 for _ in open(history, "r", encoding="utf-8"))

    print("")
    print("=== SSOT coverage summary ===")
    sys.stdout.flush()  # keep print()/subprocess stdout interleaving in order
    script_dir = Path(__file__).resolve().parent
    summary_proc = subprocess.run(
        [sys.executable, str(script_dir / "ssot_coverage_summary.py"), dut]
    )
    rc = summary_proc.returncode
    if rc != 0:
        if rc == 3:
            print(
                "SSOT coverage goals are not fully closed; see "
                f"{out / 'coverage.json'} and {dut}/sim/coverage_report.md"
            )
        else:
            return rc

    # python3 - "${OUT}/coverage.json" : pretty SSOT-filtered summary.
    if coverage_json.is_file():
        doc = json.loads(coverage_json.read_text(encoding="utf-8", errors="replace"))
        lines = doc.get("lines") or {}
        branches = doc.get("branches") or {}
        print("")
        print("=== SSOT-filtered coverage summary ===")
        print(
            "Lines    : {}/{}  ({}%) target={} status={}".format(
                lines.get("hit", 0),
                lines.get("total", 0),
                lines.get("pct"),
                lines.get("target_pct"),
                "PASS" if lines.get("meets_target") else "BLOCKED",
            )
        )
        print(
            "Branches : {}/{}  ({}%) target={} status={}".format(
                branches.get("hit", 0),
                branches.get("total", 0),
                branches.get("pct"),
                branches.get("target_pct"),
                "PASS" if branches.get("meets_target") else "BLOCKED",
            )
        )

    print("")
    print(f"Annotated dir : {out / 'annotated'}/")
    print(f"LCOV info     : {out / 'coverage.info'}")
    print(f"JSON summary  : {out / 'coverage.json'}")
    print(f"History       : {out / 'history.jsonl'}  ({hist_count} runs)")
    if want_html:
        print(f"HTML report   : {out / 'html'}/index.html")
    print("")
    print("Next: /coverage-gaps     (find uncovered hot-spots)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
