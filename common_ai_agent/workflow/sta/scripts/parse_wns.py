#!/usr/bin/env python3
"""parse_wns.py — Extract per-clock setup/hold WNS+TNS from STA reports.

Python port of parse_wns.sh. Parses sta.log + setup.rpt + hold.rpt + the SDC and
writes <ip>/sta/out/wns.json, printing the same per-clock summary lines. The
parsing logic is a 1:1 translation of the bash script's embedded python heredoc.

Usage: parse_wns.py <ip_name>
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _rd(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def _parse_paths(rpt_text: str) -> list[tuple[str, float]]:
    paths: list[tuple[str, float]] = []
    for blk in re.split(r"^Startpoint:", rpt_text, flags=re.M)[1:]:
        m_clk = (
            re.search(r"Path Group:\s*(\S+)", blk)
            or re.search(r"clocked by\s+(\S+)\)", blk)
            or re.search(r"^Clock\s+(\S+)", blk, re.M)
        )
        m_slk = re.search(r"^\s*([+\-]?[\d.]+)\s+slack\b", blk, re.M)
        if m_clk and m_slk:
            try:
                paths.append((m_clk.group(1), float(m_slk.group(1))))
            except ValueError:
                pass
    return paths


def _worst(rpt_text: str) -> str:
    blk = re.split(r"^Startpoint:", rpt_text, flags=re.M)
    if len(blk) < 2:
        return ""
    body = blk[1]
    sp = re.search(r"^Startpoint:?\s*(.+)$", "Startpoint:" + body[:200], re.M)
    ep = re.search(r"Endpoint:\s*(.+)$", body[:400], re.M)
    sl = re.search(r"^\s*([+\-]?[\d.]+)\s+slack\b", body, re.M)
    parts: list[str] = []
    if sp:
        parts.append(sp.group(1).strip())
    if ep:
        parts.append("→ " + ep.group(1).strip())
    if sl:
        parts.append(f"(slack {sl.group(1)})")
    return " ".join(parts)


def _run(ip: str, log_p: str, setup_p: str, hold_p: str, sdc_p: str, out_p: str) -> None:
    log = _rd(log_p)
    setup = _rd(setup_p)
    hold = _rd(hold_p)
    sdc = _rd(sdc_p)

    clocks: list[dict[str, object]] = []
    for m in re.finditer(r"create_clock\s+-name\s+(\S+)\s+-period\s+([\d.]+)", sdc):
        clocks.append({"name": m.group(1), "period_ns": float(m.group(2))})

    setup_paths = _parse_paths(setup)
    hold_paths = _parse_paths(hold)

    def stats(paths: list[tuple[str, float]], clock_name: str):
        sl = [s for c, s in paths if c == clock_name]
        if not sl:
            return (None, 0.0, 0)
        wns = min(sl)
        tns = sum(s for s in sl if s < 0)
        viol = sum(1 for s in sl if s < 0)
        return (wns, tns, viol)

    m_w = re.search(r"^wns\s+([\-\d.]+)", log, re.M | re.I)
    m_t = re.search(r"^tns\s+([\-\d.]+)", log, re.M | re.I)
    global_setup_wns = float(m_w.group(1)) if m_w else None
    global_setup_tns = float(m_t.group(1)) if m_t else None

    clock_objs: list[dict[str, object]] = []
    for c in clocks:
        s_wns, s_tns, s_viol = stats(setup_paths, c["name"])
        h_wns, h_tns, h_viol = stats(hold_paths, c["name"])
        if s_wns is None and global_setup_wns is not None and len(clocks) == 1:
            s_wns, s_tns = global_setup_wns, (global_setup_tns or 0.0)
            s_viol = 1 if (s_wns < 0) else 0
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
            }
        )

    def met(slack):
        return slack is not None and slack >= 0

    all_setup = all(met(c["setup_wns_ns"]) for c in clock_objs) if clock_objs else False
    all_hold = all(met(c["hold_wns_ns"]) for c in clock_objs) if clock_objs else False

    obj = {
        "top": ip,
        "corner": Path(os.environ.get("SKY130_LIB", "")).name or "unknown",
        "clocks": clock_objs,
        "summary": {
            "all_setup_met": all_setup,
            "all_hold_met": all_hold,
            "worst_setup_path": _worst(setup),
            "worst_hold_path": _worst(hold),
        },
    }
    Path(out_p).write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(f"[STA] wrote {out_p}")
    for c in clock_objs:
        s = c["setup_wns_ns"]
        h = c["hold_wns_ns"]
        print(
            f"  {c['name']}@{c['period_ns']}ns: setup_wns={s} hold_wns={h} "
            f"setup_viol={c['setup_violations']}"
        )


def main(argv: list[str]) -> int:
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    ip = argv[0] if argv else ""
    if not ip:
        print("[STA] usage: parse_wns.py <ip_name>", file=sys.stderr)
        return 2

    out = f"{ip}/sta/out"
    log = f"{out}/sta.log"
    setup = f"{out}/setup.rpt"
    hold = f"{out}/hold.rpt"
    sdc = f"{out}/{ip}.sdc"
    json_p = f"{out}/wns.json"

    if not Path(log).is_file():
        print(f"[STA] missing {log}", file=sys.stderr)
        return 2

    _run(ip, log, setup, hold, sdc, json_p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
