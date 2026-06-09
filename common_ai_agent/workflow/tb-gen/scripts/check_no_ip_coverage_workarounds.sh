#!/usr/bin/env bash
# Reject per-IP coverage workaround artifacts from tb-gen.
#
# Static/code coverage must be produced by workflow/coverage. TB-gen may emit
# functional bins and waveform setup, but it must not create one-off Verilator
# harnesses or summary parsers under an IP TB directory to force coverage DONE.
set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi
if [ -z "$IP" ] || [ ! -d "$IP" ]; then
    echo "[check_no_ip_coverage_workarounds] FAIL: cannot locate IP directory"
    exit 1
fi

BAD=""
if [ -d "$IP/tb" ]; then
    # Portable: walk the whole tb/ tree (any depth, including tb/ root) and
    # match forbidden coverage-workaround artifacts by name. Avoids ** globs,
    # which require globstar (absent in macOS bash 3.2 and off by default).
    BAD=$(find "$IP/tb" -type f \( \
        -name '*coverage_summary*.py' -o \
        -name '*cov_harness*.sv' -o \
        -name '*coverage_harness*.sv' -o \
        -name '*verilator*harness*.sv' \
        \) 2>/dev/null | sort -u)
fi

if [ -n "$BAD" ]; then
    echo "[check_no_ip_coverage_workarounds] FAIL: IP-specific coverage workaround artifacts found"
    printf "%s\n" "$BAD"
    echo "Static/code coverage must use workflow/coverage generic tools and SSOT summary."
    exit 1
fi

echo "[check_no_ip_coverage_workarounds] PASS: no IP-specific coverage workaround artifacts under $IP/tb"
