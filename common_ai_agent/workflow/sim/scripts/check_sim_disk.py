#!/usr/bin/env python3
"""check_sim_disk.py — Disk-truth validator for sim tasks.

Python port of check_sim_disk.sh for native-Windows portability.

Verifies real simulator artifacts exist + the result artifact contains real
pass markers. Supports both legacy iverilog/vvp flows and cocotb Python
runner flows on any platform where Python is available.

Exit 0 = sim ran for real and met success criteria.
Exit 1 = artifacts missing OR report shows failures OR claim-only.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _auto_detect_ip() -> str:
    """Replicate: find . -maxdepth 3 -type f -name '*.ssot.yaml'
    | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}'."""
    root = Path(".")
    matches: list[str] = []
    for pat in ("*/*/*.ssot.yaml", "*/*.ssot.yaml", "*.ssot.yaml"):
        for path in root.glob(pat):
            matches.append("./" + path.as_posix())

    def sort_key(item: str) -> str:
        parts = item.split("/")
        return parts[1] if len(parts) > 1 else ""

    matches.sort(key=sort_key)
    if not matches:
        return ""
    fields = matches[0].split("/")
    return fields[-3] if len(fields) >= 3 else ""


def _size(path: Path) -> int:
    return path.stat().st_size if path.is_file() else 0


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _find_first(ip: str, glob_suffix: str) -> str:
    """Port of: find "$IP" -path "<pattern>" -type f | head -1.

    find walks in directory order; we sort for deterministic 'first' selection
    which is acceptable for the disk-truth check (single match in practice)."""
    base = Path(ip)
    results = sorted(p for p in base.rglob("*") if p.is_file())
    rx = re.compile(glob_suffix)
    for p in results:
        if rx.search(p.as_posix()):
            return p.as_posix()
    return ""


def _parse_results_xml(path: str, bin_sz: int, xml_sz: int) -> int:
    """Port of the embedded python heredoc that inspects results.xml."""
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:  # noqa: BLE001 — match shell broad catch
        print(f"[check_sim_disk] FAIL: cannot parse {path}: {exc}")
        return 1

    # Phase 1: Sum tests/failures/errors/skipped from <testsuite> attributes.
    tests_attr = failures_attr = errors_attr = skipped_attr = 0
    testsuites = [root, *root.findall(".//testsuite")]
    for node in testsuites:
        tests_attr += int(float(node.attrib.get("tests", 0) or 0))
        failures_attr += int(float(node.attrib.get("failures", 0) or 0))
        errors_attr += int(float(node.attrib.get("errors", 0) or 0))
        skipped_attr += int(float(node.attrib.get("skipped", 0) or 0))

    # Phase 2: Fallback — count <testcase> elements when attributes absent.
    tests_elem = sum(len(list(ts.findall("testcase"))) for ts in testsuites)

    if tests_attr > 0:
        tests = tests_attr
        failures = failures_attr
        errors = errors_attr
        skipped = skipped_attr
    else:
        tests = tests_elem
        failures = 0
        errors = 0
        skipped = 0
        for ts in testsuites:
            for tc in ts.findall("testcase"):
                kids = list(tc)
                if any(k.tag == "failure" for k in kids):
                    failures += 1
                elif any(k.tag == "error" for k in kids):
                    errors += 1
                elif any(k.tag == "skipped" for k in kids):
                    skipped += 1

    if tests <= 0:
        print(f"[check_sim_disk] FAIL: {path} has no tests (attributes={tests_attr}, elements={tests_elem})")
        return 1
    if skipped and skipped == tests:
        print(f"[check_sim_disk] FAIL: all {tests} tests skipped")
        return 1
    if failures or errors:
        print(f"[check_sim_disk] FAIL: {path} tests={tests} failures={failures} errors={errors} skipped={skipped}")
        return 1

    # Phase 3: Reject lowercase pytest-style failure markers in <failure> text.
    for ts in testsuites:
        for tc in ts.findall("testcase"):
            for child in tc:
                if child.tag in ("failure", "error"):
                    msg = (child.text or "") + child.attrib.get("message", "")
                    if any(marker in msg.lower() for marker in ("failed", "error", "traceback")):
                        print(
                            f"[check_sim_disk] FAIL: {path} testcase '{tc.attrib.get('name', '?')}' "
                            f"has <{child.tag}> with failure marker: {msg[:120]}"
                        )
                        return 1

    source = "attr" if tests_attr > 0 else "elements"
    print(
        f"[check_sim_disk] PASS: bin={bin_sz}B results_xml={xml_sz}B tests={tests} "
        f"failures=0 errors=0 (source={source})"
    )
    return 0


def main(argv: list[str]) -> int:
    ip = os.environ.get("IP_NAME") or (argv[0] if argv else "")
    if not ip:
        ip = _auto_detect_ip()

    if not ip or not Path(ip).is_dir():
        print("[check_sim_disk] FAIL: cannot locate IP directory")
        return 1

    report = Path(ip) / "sim" / "sim_report.txt"
    results_xml = Path(ip) / "sim" / "results.xml"
    if not results_xml.is_file():
        results_xml = Path(ip) / "tb" / "results.xml"
    if not results_xml.is_file():
        results_xml = Path(ip) / "tb" / "cocotb" / "results.xml"

    bin_iv = Path(ip) / "sim" / f"{ip}.out"
    bin_vcs = Path(ip) / "sim" / f"{ip}_simv"
    bin_path = ""
    if bin_iv.is_file():
        bin_path = bin_iv.as_posix()
    if not bin_path and bin_vcs.is_file():
        bin_path = bin_vcs.as_posix()
    if not bin_path:
        bin_path = _find_first(ip, r"/sim_build/sim\.vvp$")
    if not bin_path:
        bin_path = _find_first(ip, r"/sim_build/.*\.vvp$")
    if not bin_path:
        # cocotb_test-based generated runners (emit_goal_scoreboard_cocotb) build
        # into sim/cocotb_build/<ip>.vvp rather than sim_build/sim.vvp.
        # (ported from the main-side .sh improvement at merge time)
        bin_path = _find_first(ip, r"/cocotb_build/.*\.vvp$")

    min_bin = int(os.environ.get("MIN_BIN", "1000"))
    min_rpt = int(os.environ.get("MIN_RPT", "100"))
    min_xml = int(os.environ.get("MIN_XML", "100"))

    if not bin_path:
        print(
            f"[check_sim_disk] FAIL: no compiled binary at {bin_iv.as_posix()}, "
            f"{bin_vcs.as_posix()}, */sim_build/*.vvp, or */cocotb_build/*.vvp"
        )
        return 1
    bin_sz = _size(Path(bin_path))
    if bin_sz < min_bin:
        print(f"[check_sim_disk] FAIL: {bin_path} = {bin_sz}B (need ≥{min_bin})")
        return 1

    rpt_sz = _size(report)
    xml_sz = _size(results_xml)
    if rpt_sz < min_rpt and xml_sz < min_xml:
        print(f"[check_sim_disk] FAIL: need {report.as_posix()} or results.xml with real content")
        return 1

    report_text = _read(report)
    report_lines = report_text.splitlines()

    # Report sanity: must not contain failure markers in any common shape.
    if rpt_sz >= min_rpt:
        re_fail_a = re.compile(r"\[FAIL\]|FATAL|Aborted")
        re_fail_b = re.compile(r"^[ \t]*FAIL:")
        re_fail_c = re.compile(r"got=0[xX][xX]+")
        re_fail_d = re.compile(r"[1-9][0-9]* (FAILED|failed|failures|errors)\b", re.IGNORECASE)
        if (
            any(re_fail_a.search(line) for line in report_lines)
            or any(re_fail_b.search(line) for line in report_lines)
            or any(re_fail_c.search(line) for line in report_lines)
            or any(re_fail_d.search(line) for line in report_lines)
        ):
            # grep -m1 -niE '\[FAIL\]|^[[:space:]]*FAIL:|FATAL|Aborted|[1-9][0-9]* (FAILED|failed)|got=0[xX][xX]+'
            re_first = re.compile(
                r"\[FAIL\]|^[ \t]*FAIL:|FATAL|Aborted|[1-9][0-9]* (FAILED|failed)|got=0[xX][xX]+",
                re.IGNORECASE,
            )
            fail_line = ""
            for idx, line in enumerate(report_lines, 1):
                if re_first.search(line):
                    fail_line = f"{idx}:{line}"
                    break
            print(f"[check_sim_disk] FAIL: {report.as_posix()} contains failure markers")
            print(f"  → {fail_line}")
            print(
                "  Hint: even when failures are 'DUT bugs', sim is NOT done — escalate via "
                "[SIM ESCALATE] or fix RTL and re-run."
            )
            return 1

    # Must contain a positive pass signature.
    re_pass = re.compile(
        r"all PASS|[0-9]+/[0-9]+ PASS|0 errors, 0 warnings|All tests passed|"
        r"All [0-9]+ tests passed|TESTS=[0-9]+ PASS=[0-9]+ FAIL=0"
    )
    if rpt_sz >= min_rpt and any(re_pass.search(line) for line in report_lines):
        print(f"[check_sim_disk] PASS: bin={bin_sz}B report={rpt_sz}B")
        return 0

    if xml_sz >= min_xml:
        return _parse_results_xml(results_xml.as_posix(), bin_sz, xml_sz)

    print(f"[check_sim_disk] FAIL: no positive pass signature in {report.as_posix()} or {results_xml.as_posix()}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
