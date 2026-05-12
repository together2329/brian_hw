#!/usr/bin/env bash
# parse_wns.sh — Reuse the /sta parser logic, output <ip>/sta-post/out/wns.json
# with mode="post_route" + skew per clock from skew.rpt.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA-POST] usage: parse_wns.sh <ip>" >&2; exit 2; fi

OUT="${IP}/sta-post/out"
LOG="${OUT}/sta.log"
SETUP="${OUT}/setup.rpt"
HOLD="${OUT}/hold.rpt"
SKEW="${OUT}/skew.rpt"
SDC="${IP}/sta/out/${IP}.sdc"
JSON="${OUT}/wns.json"

[ ! -f "${LOG}" ] && { echo "[STA-POST] missing ${LOG}" >&2; exit 2; }

python3 - "${IP}" "${LOG}" "${SETUP}" "${HOLD}" "${SKEW}" "${SDC}" "${JSON}" <<'PY'
import json, re, sys, pathlib, os

ip, log_p, setup_p, hold_p, skew_p, sdc_p, out_p = sys.argv[1:8]
def rd(p): return pathlib.Path(p).read_text(errors="replace") if pathlib.Path(p).exists() else ""
log, setup, hold, skew, sdc = rd(log_p), rd(setup_p), rd(hold_p), rd(skew_p), rd(sdc_p)

clocks = [{"name": m.group(1), "period_ns": float(m.group(2))}
          for m in re.finditer(r"create_clock\s+-name\s+(\S+)\s+-period\s+([\d.]+)", sdc)]

def parse_paths(rpt):
    out = []
    for blk in re.split(r"^Startpoint:", rpt, flags=re.M)[1:]:
        m_clk = (re.search(r"Path Group:\s*(\S+)", blk)
                 or re.search(r"clocked by\s+(\S+)\)", blk)
                 or re.search(r"^Clock\s+(\S+)", blk, re.M))
        m_slk = re.search(r"^\s*([+\-]?[\d.]+)\s+slack\b", blk, re.M)
        if m_clk and m_slk:
            try: out.append((m_clk.group(1), float(m_slk.group(1))))
            except ValueError: pass
    return out

setup_paths = parse_paths(setup)
hold_paths  = parse_paths(hold)

def stats(paths, name):
    sl = [s for c, s in paths if c == name]
    if not sl: return (None, 0.0, 0)
    return (min(sl), sum(s for s in sl if s < 0), sum(1 for s in sl if s < 0))

# Clock skew per clock: parse skew.rpt format
# `clock <name>` followed by `... skew = <X> ns` or similar.
skews = {}
for blk in re.split(r"^[Cc]lock\s+", skew, flags=re.M)[1:]:
    m_name = re.match(r"(\S+)", blk)
    m_max  = re.search(r"max[_ ]?(?:skew|delay).*?([\d.]+)", blk)
    m_lat  = re.search(r"max[_ ]?latency.*?([\d.]+)", blk)
    if m_name:
        skews[m_name.group(1).rstrip(":")] = {
          "max_skew_ps":   float(m_max.group(1)) * 1000 if m_max else None,
          "max_latency_ps": float(m_lat.group(1)) * 1000 if m_lat else None,
        }

def met(x): return x is not None and x >= 0

clock_objs = []
for c in clocks:
    s_wns, s_tns, s_viol = stats(setup_paths, c["name"])
    h_wns, h_tns, h_viol = stats(hold_paths,  c["name"])
    sk = skews.get(c["name"], {})
    clock_objs.append({
      "name": c["name"], "period_ns": c["period_ns"],
      "setup_wns_ns": s_wns, "setup_tns_ns": s_tns, "setup_violations": s_viol,
      "hold_wns_ns":  h_wns, "hold_tns_ns":  h_tns, "hold_violations":  h_viol,
      "max_skew_ps":  sk.get("max_skew_ps"),
      "max_latency_ps": sk.get("max_latency_ps"),
    })

obj = {
  "top": ip,
  "corner": pathlib.Path(os.environ.get("SKY130_LIB", "")).name or "unknown",
  "mode":   "post_route",
  "clocks": clock_objs,
  "summary": {
    "all_setup_met": all(met(c["setup_wns_ns"]) for c in clock_objs) if clock_objs else False,
    "all_hold_met":  all(met(c["hold_wns_ns"])  for c in clock_objs) if clock_objs else False,
    "worst_setup_path": "",  # report.md derives from setup/hold rpt directly
    "worst_hold_path":  "",
  },
}
pathlib.Path(out_p).write_text(json.dumps(obj, indent=2))
print(f"[STA-POST] wrote {out_p}")
for c in clock_objs:
    print(f"  {c['name']}@{c['period_ns']}ns: setup_wns={c['setup_wns_ns']} hold_wns={c['hold_wns_ns']} skew={c['max_skew_ps']}ps")
PY
