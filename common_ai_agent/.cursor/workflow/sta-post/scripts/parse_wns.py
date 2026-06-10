#!/usr/bin/env python3
"""parse_wns.py — Post-route WNS/TNS + per-clock skew parser.

Python port of the post-route parse_wns.sh; a 1:1 translation of its embedded
python heredoc. Writes <ip>/sta-post/out/wns.json with mode="post_route" plus
max_skew_ps / max_latency_ps per clock from skew.rpt.

Usage: parse_wns.py <ip>
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _rd(p: str) -> str:
    path = Path(p)
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _parse_paths(rpt: str) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for blk in re.split(r"^Startpoint:", rpt, flags=re.M)[1:]:
        m_clk = (
            re.search(r"Path Group:\s*(\S+)", blk)
            or re.search(r"clocked by\s+(\S+)\)", blk)
            or re.search(r"^Clock\s+(\S+)", blk, re.M)
        )
        m_slk = re.search(r"^\s*([+\-]?[\d.]+)\s+slack\b", blk, re.M)
        if m_clk and m_slk:
            try:
                out.append((m_clk.group(1), float(m_slk.group(1))))
            except ValueError:
                pass
    return out


def _run(
    ip: str,
    log_p: str,
    setup_p: str,
    hold_p: str,
    skew_p: str,
    sdc_p: str,
    out_p: str,
) -> None:
    log, setup, hold, skew, sdc = (
        _rd(log_p),
        _rd(setup_p),
        _rd(hold_p),
        _rd(skew_p),
        _rd(sdc_p),
    )
    # `log` is read to mirror the bash heredoc signature exactly; unused below.
    del log

    clocks = [
        {"name": m.group(1), "period_ns": float(m.group(2))}
        for m in re.finditer(
            r"create_clock\s+-name\s+(\S+)\s+-period\s+([\d.]+)", sdc
        )
    ]

    setup_paths = _parse_paths(setup)
    hold_paths = _parse_paths(hold)

    def stats(paths: list[tuple[str, float]], name: str):
        sl = [s for c, s in paths if c == name]
        if not sl:
            return (None, 0.0, 0)
        return (min(sl), sum(s for s in sl if s < 0), sum(1 for s in sl if s < 0))

    skews: dict[str, dict[str, object]] = {}
    for blk in re.split(r"^[Cc]lock\s+", skew, flags=re.M)[1:]:
        m_name = re.match(r"(\S+)", blk)
        m_max = re.search(r"max[_ ]?(?:skew|delay).*?([\d.]+)", blk)
        m_lat = re.search(r"max[_ ]?latency.*?([\d.]+)", blk)
        if m_name:
            skews[m_name.group(1).rstrip(":")] = {
                "max_skew_ps": float(m_max.group(1)) * 1000 if m_max else None,
                "max_latency_ps": float(m_lat.group(1)) * 1000 if m_lat else None,
            }

    def met(x):
        return x is not None and x >= 0

    clock_objs = []
    for c in clocks:
        s_wns, s_tns, s_viol = stats(setup_paths, c["name"])
        h_wns, h_tns, h_viol = stats(hold_paths, c["name"])
        sk = skews.get(c["name"], {})
        clock_objs.append(
            {
                "name": c["name"],
                "period_ns": c["period_ns"],
                "setup_wns_ns": s_wns,
                "setup_tns_ns": s_tns,
                "setup_violations": s_viol,
                "hold_wns_ns": h_wns,
                "hold_tns_ns": h_tns,
                "hold_violations": h_viol,
                "max_skew_ps": sk.get("max_skew_ps"),
                "max_latency_ps": sk.get("max_latency_ps"),
            }
        )

    obj = {
        "top": ip,
        "corner": Path(os.environ.get("SKY130_LIB", "")).name or "unknown",
        "mode": "post_route",
        "clocks": clock_objs,
        "summary": {
            "all_setup_met": all(met(c["setup_wns_ns"]) for c in clock_objs)
            if clock_objs
            else False,
            "all_hold_met": all(met(c["hold_wns_ns"]) for c in clock_objs)
            if clock_objs
            else False,
            "worst_setup_path": "",
            "worst_hold_path": "",
        },
    }
    Path(out_p).write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(f"[STA-POST] wrote {out_p}")
    for c in clock_objs:
        print(
            f"  {c['name']}@{c['period_ns']}ns: setup_wns={c['setup_wns_ns']} "
            f"hold_wns={c['hold_wns_ns']} skew={c['max_skew_ps']}ps"
        )


def main(argv: list[str]) -> int:
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    ip = argv[0] if argv else ""
    if not ip:
        print("[STA-POST] usage: parse_wns.py <ip>", file=sys.stderr)
        return 2

    out = f"{ip}/sta-post/out"
    log = f"{out}/sta.log"
    setup = f"{out}/setup.rpt"
    hold = f"{out}/hold.rpt"
    skew = f"{out}/skew.rpt"
    sdc = f"{ip}/sta/out/{ip}.sdc"
    json_p = f"{out}/wns.json"

    if not Path(log).is_file():
        print(f"[STA-POST] missing {log}", file=sys.stderr)
        return 2

    _run(ip, log, setup, hold, skew, sdc, json_p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
