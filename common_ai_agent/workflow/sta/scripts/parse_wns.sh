#!/usr/bin/env bash
# parse_wns.sh — Extract per-clock setup/hold WNS+TNS from sta.log + setup.rpt + hold.rpt.
# Args: <ip_name>
# Writes <ip>/sta/out/wns.json
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA] usage: parse_wns.sh <ip_name>" >&2; exit 2; fi

OUT="${IP}/sta/out"
LOG="${OUT}/sta.log"
SETUP="${OUT}/setup.rpt"
HOLD="${OUT}/hold.rpt"
SDC="${OUT}/${IP}.sdc"
JSON="${OUT}/wns.json"

if [ ! -f "${LOG}" ]; then echo "[STA] missing ${LOG}" >&2; exit 2; fi

python3 - "${IP}" "${LOG}" "${SETUP}" "${HOLD}" "${SDC}" "${JSON}" <<'PY'
import json, re, sys, pathlib, os

ip, log_p, setup_p, hold_p, sdc_p, out_p = sys.argv[1:7]
log   = pathlib.Path(log_p).read_text(errors="replace")
setup = pathlib.Path(setup_p).read_text(errors="replace") if pathlib.Path(setup_p).exists() else ""
hold  = pathlib.Path(hold_p).read_text(errors="replace")  if pathlib.Path(hold_p).exists()  else ""
sdc   = pathlib.Path(sdc_p).read_text(errors="replace")   if pathlib.Path(sdc_p).exists()   else ""

# Clocks from SDC: capture name + period.
clocks = []
for m in re.finditer(r"create_clock\s+-name\s+(\S+)\s+-period\s+([\d.]+)", sdc):
    clocks.append({"name": m.group(1), "period_ns": float(m.group(2))})

# OpenSTA report_wns / report_tns are global; we approximate per-clock by
# walking the per-path entries in setup.rpt / hold.rpt and bucketing by
# their clock name. Each path entry has a "Clock <name>" line.
def parse_paths(rpt_text):
    # OpenSTA report_checks output uses "Path Group: <clk>" — the older
    # "Clock <name>" form is rare. Try Path Group first, then fall back.
    paths = []
    for blk in re.split(r"^Startpoint:", rpt_text, flags=re.M)[1:]:
        m_clk = (re.search(r"Path Group:\s*(\S+)", blk)
                 or re.search(r"clocked by\s+(\S+)\)", blk)
                 or re.search(r"^Clock\s+(\S+)", blk, re.M))
        m_slk = re.search(r"^\s*([+\-]?[\d.]+)\s+slack\b", blk, re.M)
        if m_clk and m_slk:
            try:
                paths.append((m_clk.group(1), float(m_slk.group(1))))
            except ValueError:
                pass
    return paths

setup_paths = parse_paths(setup)
hold_paths  = parse_paths(hold)

def stats(paths, clock_name):
    sl = [s for c, s in paths if c == clock_name]
    if not sl:
        return (None, 0.0, 0)
    wns = min(sl)
    tns = sum(s for s in sl if s < 0)
    viol = sum(1 for s in sl if s < 0)
    return (wns, tns, viol)

# Fallback: scan the log for global report_wns / report_tns numbers.
m_w = re.search(r"^wns\s+([\-\d.]+)", log, re.M | re.I)
m_t = re.search(r"^tns\s+([\-\d.]+)", log, re.M | re.I)
global_setup_wns = float(m_w.group(1)) if m_w else None
global_setup_tns = float(m_t.group(1)) if m_t else None

clock_objs = []
for c in clocks:
    s_wns, s_tns, s_viol = stats(setup_paths, c["name"])
    h_wns, h_tns, h_viol = stats(hold_paths,  c["name"])
    if s_wns is None and global_setup_wns is not None and len(clocks) == 1:
        s_wns, s_tns = global_setup_wns, (global_setup_tns or 0.0)
        s_viol = 1 if (s_wns < 0) else 0
    clock_objs.append({
        "name": c["name"],
        "period_ns": c["period_ns"],
        "setup_wns_ns": s_wns,
        "setup_tns_ns": s_tns,
        "setup_violations": s_viol,
        "hold_wns_ns":  h_wns,
        "hold_tns_ns":  h_tns,
        "hold_violations": h_viol,
    })

def met(slack):
    return slack is not None and slack >= 0

all_setup = all(met(c["setup_wns_ns"]) for c in clock_objs) if clock_objs else False
all_hold  = all(met(c["hold_wns_ns"])  for c in clock_objs) if clock_objs else False

# Worst path one-liners — first non-passing path in each rpt, else first path.
def worst(rpt_text):
    blk = re.split(r"^Startpoint:", rpt_text, flags=re.M)
    if len(blk) < 2: return ""
    body = blk[1]
    sp = re.search(r"^Startpoint:?\s*(.+)$", "Startpoint:" + body[:200], re.M)
    ep = re.search(r"Endpoint:\s*(.+)$", body[:400], re.M)
    sl = re.search(r"^\s*([+\-]?[\d.]+)\s+slack\b", body, re.M)
    parts = []
    if sp: parts.append(sp.group(1).strip())
    if ep: parts.append("→ " + ep.group(1).strip())
    if sl: parts.append(f"(slack {sl.group(1)})")
    return " ".join(parts)

obj = {
  "top": ip,
  "corner": pathlib.Path(os.environ.get("SKY130_LIB", "")).name or "unknown",
  "clocks": clock_objs,
  "summary": {
    "all_setup_met": all_setup,
    "all_hold_met":  all_hold,
    "worst_setup_path": worst(setup),
    "worst_hold_path":  worst(hold),
  },
}
pathlib.Path(out_p).write_text(json.dumps(obj, indent=2))
print(f"[STA] wrote {out_p}")
for c in clock_objs:
    s = c["setup_wns_ns"]; h = c["hold_wns_ns"]
    print(f"  {c['name']}@{c['period_ns']}ns: setup_wns={s} hold_wns={h} setup_viol={c['setup_violations']}")
PY
