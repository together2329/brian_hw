#!/usr/bin/env python3
"""vcd_merge.py — Concatenate multiple VCD files into one.

Mode: 'concat' — each input VCD is appended after the previous one. The time
markers (`#<n>`) are offset so the merged output forms one continuous timeline.

Constraints (concat mode):
- All inputs must have the SAME header (same $scope/$var declarations and
  identifier characters). Concat assumes the same DUT was simulated.
- All inputs must use the same $timescale. If they differ we bail with a
  clear error rather than silently rescaling.
- Empty inputs (no #<time> markers) are skipped.

Output: single VCD on stdout (or to --out path) with the union of all body
sections, time-shifted, plus provenance comments showing which input
contributed each segment.

No external dependencies — only Python stdlib. VCD parsing is done with
simple line scanning since the format is straightforward.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class VcdParts:
    """A parsed VCD split into header / body."""
    header: str           # everything up to and INCLUDING $enddefinitions
    body: str             # value-change section (after $enddefinitions)
    timescale: str        # e.g. "1ns" — extracted for comparison
    var_signature: str    # canonical signature of all $var lines, for compat check
    last_time: int        # max #<time> seen in body, used as offset for next file
    src_path: str         # original path, for provenance comments


def _parse_vcd(path: str) -> VcdParts:
    """Read a VCD file, return its parts split at $enddefinitions."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")

    if "$enddefinitions" not in text:
        raise ValueError(f"{path}: no $enddefinitions marker — corrupt VCD?")

    # Find the `$enddefinitions ... $end` block. We can't just search for the
    # next "$end" after `$enddefinitions` because "$end" is a SUBSTRING of
    # "$enddefinitions" itself — Python's str.index finds zero-distance hits.
    # Skip past the directive name first, THEN look for its closing $end.
    h_idx = text.index("$enddefinitions")
    after_directive = h_idx + len("$enddefinitions")
    end_idx = text.index("$end", after_directive)
    header = text[: end_idx + len("$end")]
    body = text[end_idx + len("$end") :].lstrip("\n")

    # Extract timescale — first $timescale ... $end block
    timescale = ""
    if "$timescale" in header:
        ts_start = header.index("$timescale") + len("$timescale")
        ts_end = header.index("$end", ts_start)
        timescale = header[ts_start:ts_end].strip()

    # Build a signature of all $var declarations so we can check that two VCDs
    # describe the same DUT. We don't compare verbatim — we sort and join the
    # `width identifier name` triples, which are what actually matters.
    var_lines: list = []
    for line in header.splitlines():
        line = line.strip()
        if line.startswith("$var "):
            # `$var wire 1 ! signal_a $end` → "wire 1 ! signal_a"
            parts = line.split()
            if len(parts) >= 5:
                var_lines.append(" ".join(parts[1:5]))
    var_signature = "\n".join(sorted(var_lines))

    # Find the largest #<time> marker in the body so we know how much to
    # shift the NEXT file's body by. VCD time markers are always whole
    # nonnegative integers in raw form (#1234, possibly very large).
    last_time = 0
    for line in body.splitlines():
        if line.startswith("#"):
            try:
                t = int(line[1:].strip())
                if t > last_time:
                    last_time = t
            except ValueError:
                # Skip malformed time markers (rare)
                continue

    return VcdParts(
        header=header,
        body=body,
        timescale=timescale,
        var_signature=var_signature,
        last_time=last_time,
        src_path=path,
    )


def _shift_body(body: str, offset: int) -> str:
    """Add `offset` to every #<time> line in `body`."""
    if offset == 0:
        return body
    out_lines: list = []
    for line in body.splitlines():
        if line.startswith("#"):
            try:
                t = int(line[1:].strip())
                out_lines.append(f"#{t + offset}")
                continue
            except ValueError:
                pass
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if body.endswith("\n") else "")


def merge_concat(inputs: List[str], out_path: str = "") -> str:
    """Concat-merge all `inputs` into one VCD. Return the merged text.

    If `out_path` is given, also writes to that path.
    Raises ValueError if inputs are incompatible (different DUTs or timescales).
    """
    if not inputs:
        raise ValueError("no input VCDs provided")

    # Parse all up front so we can validate compatibility before writing.
    parsed: List[VcdParts] = []
    for p in inputs:
        if not Path(p).exists():
            raise FileNotFoundError(p)
        parsed.append(_parse_vcd(p))

    # Validate all share the same timescale and var signature.
    base = parsed[0]
    for cur in parsed[1:]:
        if cur.timescale != base.timescale:
            raise ValueError(
                f"timescale mismatch: {base.src_path} has {base.timescale!r}, "
                f"{cur.src_path} has {cur.timescale!r} — cannot concat-merge."
            )
        if cur.var_signature != base.var_signature:
            # Print diff hint
            base_set = set(base.var_signature.split("\n"))
            cur_set = set(cur.var_signature.split("\n"))
            missing = base_set - cur_set
            extra = cur_set - base_set
            hint = ""
            if missing:
                hint += f"\n  Only in {base.src_path}: {next(iter(missing))[:80]}…"
            if extra:
                hint += f"\n  Only in {cur.src_path}:  {next(iter(extra))[:80]}…"
            raise ValueError(
                f"var declarations differ between {base.src_path} and "
                f"{cur.src_path} — concat assumes same DUT.{hint}"
            )

    # Build output: base header (rewritten with comment), then each body
    # shifted by the cumulative offset.
    out_parts: List[str] = []
    # Provenance comment block at the very top (before $date)
    provenance = ["$comment", f"  vcd_merge.py concat of {len(inputs)} VCD(s):"]
    for p in inputs:
        provenance.append(f"    - {p}")
    provenance.append("$end")
    out_parts.append("\n".join(provenance))

    out_parts.append(base.header)

    # Track cumulative shift. The first body keeps its native times.
    cumulative = 0
    for i, cur in enumerate(parsed):
        if i == 0:
            shifted = cur.body
            segment_start = 0
        else:
            shifted = _shift_body(cur.body, cumulative)
            segment_start = cumulative

        # Add a comment showing where this segment came from
        out_parts.append(
            f"$comment segment {i + 1}: {cur.src_path} "
            f"(time {segment_start}..{segment_start + cur.last_time}) $end"
        )
        out_parts.append(shifted)

        # Advance cumulative by this body's max time
        cumulative += cur.last_time

    merged = "\n".join(out_parts)
    if not merged.endswith("\n"):
        merged += "\n"

    if out_path:
        Path(out_path).write_text(merged, encoding="utf-8")

    return merged


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Concat-merge VCD files.")
    p.add_argument("inputs", nargs="+", help="Input VCD files (in concat order)")
    p.add_argument("--out", "-o", default="", help="Output path (default: stdout)")
    p.add_argument(
        "--mode", choices=["concat"], default="concat",
        help="Merge mode (only 'concat' supported currently)",
    )
    args = p.parse_args(argv)

    try:
        merged = merge_concat(args.inputs, args.out)
    except (ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if not args.out:
        sys.stdout.write(merged)
    else:
        # Print summary stats
        lines = merged.count("\n")
        size_kb = len(merged) // 1024
        print(f"Merged {len(args.inputs)} VCD(s) → {args.out}")
        print(f"  Lines : {lines:,}")
        print(f"  Size  : {size_kb:,} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
