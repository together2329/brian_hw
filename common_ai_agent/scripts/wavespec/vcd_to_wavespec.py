#!/usr/bin/env python3
"""Convert a VCD dump into a wavespec JSON for the interactive timing viewer.

Samples every signal on the rising edges of a chosen clock and emits
``{"title": ..., "signals": [{"name", "wave", "data"}]}`` — the exact format
consumed by interactive_ui/timing-diagram.html and timing-compare.html.

Wave token mapping (WaveDrom-ish subset the viewer understands):
  p          clock track (the sampled clock itself)
  0 / 1      scalar low / high
  .          hold previous value
  =          multi-bit bus value (label pulled from the "data" array)
  x          unknown / don't-care (any bit is x)
  z          high-Z

Typical use (window onto one transaction):
  vcd_to_wavespec.py atlas_flow_gpio_demo/sim/atlas_flow_gpio_demo.vcd \
      --clock PCLK --anchor "PWDATA=0x55" --pre 1 --cycles 5 \
      --signals PCLK PSEL PENABLE PWRITE PADDR PWDATA PREADY gpio_out
"""
from __future__ import annotations

import argparse
import json
import sys


def parse_header(lines):
    """Return (id2sig, name2id, value_start_index)."""
    id2sig, name2id = {}, {}
    i = 0
    for i, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("$var"):
            t = line.split()
            # $var <type> <width> <id> <name> [bits] $end
            kind, width, vid, name = t[1], int(t[2]), t[3], t[4]
            id2sig[vid] = {"name": name, "width": width, "kind": kind}
            name2id[name] = vid
        elif line.startswith("$enddefinitions"):
            return id2sig, name2id, i + 1
    raise ValueError("no $enddefinitions found — not a VCD?")


def collect_edges(lines, start, clock_id):
    """Walk the value-change section; snapshot all signals on each clock rise."""
    cur = {}
    edges = []  # list of (time, {id: raw_value})
    t = 0
    for raw in lines[start:]:
        line = raw.strip()
        if not line or line[0] == "$":
            continue
        if line[0] == "#":
            t = int(line[1:])
            continue
        if line[0] in "bBrR":  # vector / real
            tok = line.split()
            cur[tok[1]] = tok[0][1:]
            continue
        if line[0] in "01xXzZ":  # scalar
            val, vid = line[0], line[1:]
            prev = cur.get(vid)
            cur[vid] = val
            if vid == clock_id and val == "1" and prev == "0":
                edges.append((t, dict(cur)))
    return edges


def fmt(sig, raw):
    """Resolve a raw VCD value into (token, display) for one cell."""
    if raw is None:
        return "x", "x"
    if sig["width"] == 1:
        v = raw.lower()
        return (v, v) if v in ("0", "1", "x", "z") else ("x", "x")
    low = raw.lower()
    if "x" in low:
        return "x", "x"
    if "z" in low:
        return "z", "z"
    return "=", "0x%X" % int(raw, 2)


def canon(sig, display, want):
    """True if a cell display matches an --anchor target value `want`."""
    if sig["width"] == 1:
        return display == want.lower()
    try:
        return display != "x" and display != "z" and int(display, 16) == int(want, 16)
    except ValueError:
        return display == want


def build_wave(sig, vid, window, clock_id):
    if vid == clock_id:
        return "p" * len(window), []
    wave, data, prev = "", [], None
    for k, (_, snap) in enumerate(window):
        token, disp = fmt(sig, snap.get(vid))
        if k > 0 and disp == prev:
            wave += "."
        elif token == "=":
            wave += "="
            data.append(disp)
        else:
            wave += token
        prev = disp
    return wave, data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vcd")
    ap.add_argument("--clock", default=None, help="clock signal name (default: auto-detect *clk*)")
    ap.add_argument("--signals", nargs="*", default=None, help="signals to emit, in order (default: all non-param)")
    ap.add_argument("--anchor", default=None, help='window start: "NAME=VALUE" (first edge where it holds)')
    ap.add_argument("--pre", type=int, default=0, help="cycles to include before the anchor edge")
    ap.add_argument("--cycles", type=int, default=None, help="number of cycles (default: all from start)")
    ap.add_argument("--title", default=None)
    ap.add_argument("--list", action="store_true", help="list signals and exit")
    args = ap.parse_args(argv)

    with open(args.vcd) as f:
        lines = f.read().splitlines()
    id2sig, name2id, vstart = parse_header(lines)

    if args.list:
        for vid, s in id2sig.items():
            print(f"{s['name']:<20} w={s['width']:<3} kind={s['kind']} id={vid!r}")
        return 0

    # pick clock
    clock_name = args.clock
    if clock_name is None:
        for name, vid in name2id.items():
            if id2sig[vid]["width"] == 1 and ("clk" in name.lower() or "clock" in name.lower()):
                clock_name = name
                break
    if clock_name is None or clock_name not in name2id:
        ap.error(f"clock '{clock_name}' not found; use --clock (have: {', '.join(name2id)})")
    clock_id = name2id[clock_name]

    edges = collect_edges(lines, vstart, clock_id)
    if not edges:
        ap.error("no rising clock edges captured")

    # windowing
    start = 0
    if args.anchor:
        name, want = args.anchor.split("=", 1)
        vid = name2id[name]
        sig = id2sig[vid]
        start = 0
        for idx, (_, snap) in enumerate(edges):
            _, disp = fmt(sig, snap.get(vid))
            if canon(sig, disp, want):
                start = idx
                break
        start = max(0, start - args.pre)
    end = len(edges) if args.cycles is None else min(len(edges), start + args.cycles)
    window = edges[start:end]

    # choose signals
    if args.signals:
        chosen = [name2id[n] for n in args.signals if n in name2id]
        names = [n for n in args.signals if n in name2id]
    else:
        chosen, names = [], []
        for name, vid in name2id.items():
            if id2sig[vid]["kind"] != "parameter":
                chosen.append(vid)
                names.append(name)

    signals = []
    for vid, name in zip(chosen, names):
        wave, data = build_wave(id2sig[vid], vid, window, clock_id)
        sig = {"name": name, "wave": wave}
        if data:
            sig["data"] = data
        signals.append(sig)

    title = args.title or f"{args.vcd.split('/')[-1]}  ·  edges {start}–{end - 1}  ·  sampled @posedge {clock_name}"
    print(json.dumps({"title": title, "signals": signals}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
