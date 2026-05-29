#!/usr/bin/env python3
"""Streaming VCD analysis for mctp_assembler SC_VALID / ingress debug."""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_VCD = Path(__file__).resolve().parents[1] / "sim" / "cocotb_build" / "mctp_assembler.vcd"

# Hierarchical suffixes (unique enough in this design)
WANT_SUFFIXES = (
    "cfg_enable",
    "cfg_enable_apb",
    "u_ingress.enable_lat_q",
    "u_ingress.tlp_valid_q",
    "u_ingress.byte_count_q",
    "u_ingress.malformed_q",
    "u_ingress.state_q",
    "tlp_valid",
    "tlp_ready",
    "process_active_q",
    "pkt_valid",
    "pkt_ready",
    "mctp_valid",
    "parse_fail",
    "s_axi_awvalid",
    "s_axi_awready",
    "s_axi_wvalid",
    "s_axi_wready",
    "s_axi_wlast",
    "s_axi_bvalid",
    "sram_wr_valid",
    "vdm_valid",
    "vdm_bad_vendor",
    "wr_byte_valid",
    "desc_fifo_count",
)

ING_STATES = {0: "IDLE", 1: "ADDR", 2: "DATA", 3: "RESP"}


def match_path(path: str) -> str | None:
    for suffix in WANT_SUFFIXES:
        if path.endswith(suffix) or path == suffix:
            return suffix
    return None


def parse_header(f) -> tuple[dict[str, str], dict[str, int]]:
    code_to_path: dict[str, str] = {}
    code_width: dict[str, int] = {}
    scope_stack: list[str] = []
    for raw in f:
        line = raw.strip()
        if line.startswith("$scope"):
            scope_stack.append(line.split()[2])
        elif line.startswith("$upscope"):
            if scope_stack:
                scope_stack.pop()
        elif line.startswith("$var"):
            parts = line.split()
            width = int(parts[2])
            code = parts[3]
            sym = parts[4]
            path = ".".join(scope_stack + [sym])
            code_to_path[code] = path
            code_width[code] = width
        elif line.startswith("$enddefinitions"):
            break
    return code_to_path, code_width


def short_name(path: str) -> str:
    key = match_path(path)
    return key or path.split(".")[-1]


def analyze(vcd_path: Path, t_max: int = 200_000_000) -> None:
    aw_times: list[int] = []
    handshake_windows: list[list[tuple[int, dict[str, int]]]] = []
    current_window: list[tuple[int, dict[str, int]]] | None = None
    window_until = 0

    with vcd_path.open("r", encoding="utf-8", errors="replace") as f:
        code_to_path, _code_width = parse_header(f)
        picked = {code: short_name(path) for code, path in code_to_path.items() if match_path(path)}
        rev = picked
        values = {code: 0 for code in picked}
        time = 0
        prev_aw = 0

        def snapshot() -> dict[str, int]:
            out: dict[str, int] = {}
            for code, name in rev.items():
                out[name] = values[code]
            return out

        for raw in f:
            line = raw.strip()
            if not line or "\x00" in line:
                continue
            if line.startswith("#"):
                try:
                    time = int(line[1:].split()[0])
                except ValueError:
                    continue
                if time > t_max:
                    break
                snap = snapshot()
                aw = snap.get("s_axi_awvalid", 0) & snap.get("s_axi_awready", 0)
                if aw and not prev_aw:
                    aw_times.append(time)
                    current_window = [(time, snap.copy())]
                    window_until = time + 120_000
                elif current_window is not None and time <= window_until:
                    current_window.append((time, snap.copy()))
                elif current_window is not None and time > window_until:
                    handshake_windows.append(current_window)
                    current_window = None
                prev_aw = aw
                continue
            if line[0] == "b":
                bits, code = line[1:].split()
                if code in picked:
                    values[code] = int(bits, 2)
            elif line[0] in "01xXzZ" and len(line) >= 2:
                code = line[1:]
                if code in picked:
                    values[code] = 1 if line[0] == "1" else 0

    if current_window:
        handshake_windows.append(current_window)

    print(f"VCD: {vcd_path} ({vcd_path.stat().st_size // (1024*1024)} MiB)")
    print(f"Tracked signals: {sorted(set(rev.values()))}")
    print(f"AW handshakes found: {len(aw_times)}")
    if not aw_times:
        print("No AW handshake in VCD — sim may have timed out before AXI or VCD truncated.")
        return

    for idx, (t0, window) in enumerate(zip(aw_times, handshake_windows)):
        print(f"\n{'='*72}")
        print(f"AW burst #{idx} @ {t0} ps")
        print(f"{'='*72}")
        for t, s in window:
            ing = s.get("u_ingress.state_q", -1)
            ing_s = ING_STATES.get(ing, str(ing))
            print(
                f"{t:>10}  aw={s.get('s_axi_awvalid',0)}/{s.get('s_axi_awready',0)} "
                f"w={s.get('s_axi_wvalid',0)}/{s.get('s_axi_wready',0)} wl={s.get('s_axi_wlast',0)} "
                f"b={s.get('s_axi_bvalid',0)}  en={s.get('cfg_enable',0)} en_apb={s.get('cfg_enable_apb',0)} "
                f"en_lat={s.get('u_ingress.enable_lat_q',0)} "
                f"ing={ing_s}  tlp={s.get('tlp_valid',0)}/{s.get('u_ingress.tlp_valid_q',0)} "
                f"tr={s.get('tlp_ready',0)} bc={s.get('u_ingress.byte_count_q',0)} "
                f"mal={s.get('u_ingress.malformed_q',0)}  proc={s.get('process_active_q',0)} "
                f"mctp={s.get('mctp_valid',0)} vdm={s.get('vdm_valid',0)} badv={s.get('vdm_bad_vendor',0)} "
                f"pkt={s.get('pkt_valid',0)}/{s.get('pkt_ready',0)} sram={s.get('sram_wr_valid',0)} "
                f"desc={s.get('desc_fifo_count',0)}"
            )
        # summary at end of window
        if window:
            _, last = window[-1]
            print(
                f"  => end: tlp_valid={last.get('tlp_valid',0)} byte_count={last.get('u_ingress.byte_count_q',0)} "
                f"mctp_valid={last.get('mctp_valid',0)} desc_fifo={last.get('desc_fifo_count',0)} "
                f"sram_wr_valid={last.get('sram_wr_valid',0)}"
            )


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VCD
    analyze(path)
