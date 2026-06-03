#!/usr/bin/env bash
# check_architect_disk.sh — Disk-truth validator for SoC architect tasks.
#
# Verifies soc.ssot.yaml actually exists with the four required top-level keys
# (clusters, instances, addrMap, connections) and parses as YAML.
#
# Inputs (env):
#   SOC_SSOT — path to soc.ssot.yaml (default: ./soc.ssot.yaml)
#
# Exit 0 = file exists, parses, has all four required keys, addrMap entries
#          have base+range, no detectable address-range overlap.
# Exit 1 = anything missing.

set -u

SOC="${SOC_SSOT:-./soc.ssot.yaml}"

[ -f "$SOC" ] || { echo "[check_architect_disk] FAIL: $SOC missing"; exit 1; }

SZ=$(wc -c < "$SOC" | tr -d ' ')
[ "$SZ" -lt 50 ] && { echo "[check_architect_disk] FAIL: $SOC too small (${SZ}B)"; exit 1; }

# Parse check via python (yaml stdlib if available, else PyYAML).
python3 - "$SOC" <<'PY' || exit 1
import sys, os
path = sys.argv[1]
try:
    import yaml
except ImportError:
    print("[check_architect_disk] FAIL: PyYAML not installed")
    sys.exit(1)

try:
    with open(path) as f:
        doc = yaml.safe_load(f)
except Exception as e:
    print(f"[check_architect_disk] FAIL: yaml parse error: {e}")
    sys.exit(1)

if not isinstance(doc, dict):
    print("[check_architect_disk] FAIL: top-level is not a mapping")
    sys.exit(1)

required = ["clusters", "instances", "addrMap", "connections"]
missing = [k for k in required if k not in doc]
if missing:
    print(f"[check_architect_disk] FAIL: missing keys: {missing}")
    sys.exit(1)

# addrMap structural + overlap check
am = doc.get("addrMap") or []
if not isinstance(am, list):
    print("[check_architect_disk] FAIL: addrMap must be a list")
    sys.exit(1)

ranges = []
for i, e in enumerate(am):
    if not isinstance(e, dict):
        print(f"[check_architect_disk] FAIL: addrMap[{i}] not a mapping")
        sys.exit(1)
    if "base" not in e or "range" not in e:
        print(f"[check_architect_disk] FAIL: addrMap[{i}] missing base/range")
        sys.exit(1)
    try:
        b = int(e["base"], 0) if isinstance(e["base"], str) else int(e["base"])
        r = int(e["range"], 0) if isinstance(e["range"], str) else int(e["range"])
    except (ValueError, TypeError):
        print(f"[check_architect_disk] FAIL: addrMap[{i}] base/range not int")
        sys.exit(1)
    ranges.append((b, b + r - 1, e.get("name", f"#{i}")))

ranges.sort()
for i in range(len(ranges) - 1):
    a_lo, a_hi, a_n = ranges[i]
    b_lo, b_hi, b_n = ranges[i + 1]
    if a_hi >= b_lo:
        print(f"[check_architect_disk] FAIL: addrMap overlap {a_n}@0x{a_lo:x}-0x{a_hi:x} vs {b_n}@0x{b_lo:x}-0x{b_hi:x}")
        sys.exit(1)

# instances must point at existing leaf SSOTs
inst = doc.get("instances") or []
for i, e in enumerate(inst):
    if not isinstance(e, dict):
        print(f"[check_architect_disk] FAIL: instances[{i}] not a mapping")
        sys.exit(1)
    sp = e.get("ssot")
    if sp and not os.path.isfile(sp):
        print(f"[check_architect_disk] FAIL: instances[{i}].ssot path missing on disk: {sp}")
        sys.exit(1)

n_cl = len(doc.get("clusters") or [])
n_in = len(inst)
n_am = len(am)
n_co = len(doc.get("connections") or [])
print(f"[check_architect_disk] PASS: soc.ssot.yaml = {os.path.getsize(path)}B, clusters={n_cl} instances={n_in} addrMap={n_am} connections={n_co}")
PY
