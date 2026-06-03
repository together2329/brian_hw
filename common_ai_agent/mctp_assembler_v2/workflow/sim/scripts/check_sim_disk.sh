#!/usr/bin/env bash
# check_sim_disk.sh — Disk-truth validator for sim tasks.
#
# Verifies real simulator artifacts exist + the result artifact contains real
# pass markers. Supports both legacy iverilog/vvp flows and cocotb Python
# runner flows on any platform where POSIX shell + Python are available.
#
# Exit 0 = sim ran for real and met success criteria.
# Exit 1 = artifacts missing OR report shows failures OR claim-only.

set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi
if [ -z "$IP" ] || [ ! -d "$IP" ]; then
    echo "[check_sim_disk] FAIL: cannot locate IP directory"
    exit 1
fi

REPORT="$IP/sim/sim_report.txt"
RESULTS_XML="$IP/sim/results.xml"
[ -f "$RESULTS_XML" ] || RESULTS_XML="$IP/tb/results.xml"
[ -f "$RESULTS_XML" ] || RESULTS_XML="$IP/tb/cocotb/results.xml"

# Compiled binary may be uart.out (iverilog), <ip>_simv (VCS), or cocotb's sim.vvp.
BIN_IV="$IP/sim/$IP.out"
BIN_VCS="$IP/sim/${IP}_simv"
BIN=""
if [ -f "$BIN_IV" ]; then BIN="$BIN_IV"; fi
if [ -z "$BIN" ] && [ -f "$BIN_VCS" ]; then BIN="$BIN_VCS"; fi
if [ -z "$BIN" ]; then
    BIN=$(find "$IP" -path "*/sim_build/sim.vvp" -type f 2>/dev/null | head -1)
fi
if [ -z "$BIN" ]; then
    BIN=$(find "$IP" -path "*/sim_build/*.vvp" -type f 2>/dev/null | head -1)
fi

MIN_BIN="${MIN_BIN:-1000}"
MIN_RPT="${MIN_RPT:-100}"
MIN_XML="${MIN_XML:-100}"

_size() { [ -f "$1" ] && wc -c < "$1" | tr -d ' ' || echo 0; }

if [ -z "$BIN" ]; then
    echo "[check_sim_disk] FAIL: no compiled binary at $BIN_IV, $BIN_VCS, or */sim_build/sim.vvp"
    exit 1
fi
BIN_SZ=$(_size "$BIN")
[ "$BIN_SZ" -lt "$MIN_BIN" ] && { echo "[check_sim_disk] FAIL: $BIN = ${BIN_SZ}B (need ≥${MIN_BIN})"; exit 1; }

RPT_SZ=$(_size "$REPORT")
XML_SZ=$(_size "$RESULTS_XML")
if [ "$RPT_SZ" -lt "$MIN_RPT" ] && [ "$XML_SZ" -lt "$MIN_XML" ]; then
    echo "[check_sim_disk] FAIL: need $REPORT or results.xml with real content"
    exit 1
fi

# Report sanity: must not contain failure markers in any common shape:
#   [FAIL] SCx_...      ← per-test [FAIL] tag (textbook ssot-tb format)
#   N FAILED            ← end-of-report tally  ("6 FAILED")
#   FAIL: ...           ← bare FAIL: prefix lines
#   got=0xxx, x_state   ← X-propagation symptoms
#   Errors: N (N > 0)   ← non-zero error tally
#   Warnings: N (N > 0) ← non-zero warning tally
#   FATAL / Aborted     ← simulator panic
if [ "$RPT_SZ" -ge "$MIN_RPT" ]; then
    if grep -qE '\[FAIL\]|FATAL|Aborted' "$REPORT" \
       || grep -qE '^[[:space:]]*FAIL:' "$REPORT" \
       || grep -qE 'got=0[xX][xX]+' "$REPORT" \
       || grep -qiE '[1-9][0-9]* (FAILED|failed|failures|errors)\b' "$REPORT"; then
        FAIL_LINE=$(grep -m1 -niE '\[FAIL\]|^[[:space:]]*FAIL:|FATAL|Aborted|[1-9][0-9]* (FAILED|failed)|got=0[xX][xX]+' "$REPORT")
        echo "[check_sim_disk] FAIL: $REPORT contains failure markers"
        echo "  → $FAIL_LINE"
        echo "  Hint: even when failures are 'DUT bugs', sim is NOT done — escalate via [SIM ESCALATE] or fix RTL and re-run."
        exit 1
    fi
fi

# Must contain a positive pass signature.
if [ "$RPT_SZ" -ge "$MIN_RPT" ] && grep -qE 'all PASS|[0-9]+/[0-9]+ PASS|0 errors, 0 warnings|All tests passed|All [0-9]+ tests passed|TESTS=[0-9]+ PASS=[0-9]+ FAIL=0' "$REPORT"; then
    echo "[check_sim_disk] PASS: bin=${BIN_SZ}B report=${RPT_SZ}B"
    exit 0
fi

if [ "$XML_SZ" -ge "$MIN_XML" ]; then
    python3 - "$RESULTS_XML" "$BIN_SZ" "$XML_SZ" <<'PY'
import sys
import xml.etree.ElementTree as ET

path, bin_sz, xml_sz = sys.argv[1:4]
try:
    root = ET.parse(path).getroot()
except Exception as exc:
    print(f"[check_sim_disk] FAIL: cannot parse {path}: {exc}")
    raise SystemExit(1)

# ── Phase 1: Sum tests/failures/errors/skipped from <testsuite> attributes ──
tests_attr = failures_attr = errors_attr = skipped_attr = 0
testsuites = [root, *root.findall('.//testsuite')]
for node in testsuites:
    tests_attr    += int(float(node.attrib.get('tests', 0) or 0))
    failures_attr += int(float(node.attrib.get('failures', 0) or 0))
    errors_attr   += int(float(node.attrib.get('errors', 0) or 0))
    skipped_attr  += int(float(node.attrib.get('skipped', 0) or 0))

# ── Phase 2: Fallback — count <testcase> elements when attributes absent ──
# Some JUnit producers (e.g. cocotb) omit tests="N" on <testsuite>.
# In that case, count actual <testcase> child elements.
tests_elem = sum(len(list(ts.findall('testcase'))) for ts in testsuites)

if tests_attr > 0:
    tests = tests_attr
    failures = failures_attr
    errors = errors_attr
    skipped = skipped_attr
else:
    # Attribute fallback: use element counts.
    tests = tests_elem
    # Count <failure> and <error> children of <testcase>.
    failures = 0
    errors = 0
    skipped = 0
    for ts in testsuites:
        for tc in ts.findall('testcase'):
            kids = list(tc)
            if any(k.tag == 'failure' for k in kids):
                failures += 1
            elif any(k.tag == 'error' for k in kids):
                errors += 1
            elif any(k.tag == 'skipped' for k in kids):
                skipped += 1

if tests <= 0:
    print(f"[check_sim_disk] FAIL: {path} has no tests (attributes={tests_attr}, elements={tests_elem})")
    raise SystemExit(1)
if skipped and skipped == tests:
    print(f"[check_sim_disk] FAIL: all {tests} tests skipped")
    raise SystemExit(1)
if failures or errors:
    print(f"[check_sim_disk] FAIL: {path} tests={tests} failures={failures} errors={errors} skipped={skipped}")
    raise SystemExit(1)

# ── Phase 3: Reject lowercase pytest-style failure markers in <failure> text ──
# pytest produces <failure message="FAILED ..."> or <failure> with lowercase
# text like "failed", "error".  Reject if present.
for ts in testsuites:
    for tc in ts.findall('testcase'):
        for child in tc:
            if child.tag in ('failure', 'error'):
                msg = (child.text or '') + (child.attrib.get('message', ''))
                if any(marker in msg.lower() for marker in ('failed', 'error', 'traceback')):
                    print(f"[check_sim_disk] FAIL: {path} testcase '{tc.attrib.get('name', '?')}' "
                          f"has <{child.tag}> with failure marker: {msg[:120]}")
                    raise SystemExit(1)

print(f"[check_sim_disk] PASS: bin={bin_sz}B results_xml={xml_sz}B tests={tests} failures=0 errors=0"
      f" (source={'attr' if tests_attr > 0 else 'elements'})")
PY
    exit $?
fi

echo "[check_sim_disk] FAIL: no positive pass signature in $REPORT or $RESULTS_XML"
exit 1
