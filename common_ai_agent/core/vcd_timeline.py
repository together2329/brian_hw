"""core/vcd_timeline.py — minimal stdlib VCD reader with a real time→value
timeline, for server-side waveform queries by the `sim_debug` agent tool.

The existing workflow/coverage/adapters/vcd_toggle.py aggregates toggles but
drops timestamps; this keeps per-signal (time, value) so we can answer
"when does X first rise" and "value of X at t". Scope: scalar + vector value
changes, `#<time>` markers, `$var`/`$timescale`. No strength/real-precision
modelling — enough for debug navigation.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_VAR_RE = re.compile(r"\$var\s+\w+\s+(\d+)\s+(\S+)\s+(.+?)\s*\$end")
_TS_RE = re.compile(r"\$timescale\s+(.+?)\s*\$end", re.DOTALL)


class VcdTimeline:
    def __init__(self) -> None:
        self.timescale: str = "ns"
        # id → list[(time, value_str)]
        self.changes: Dict[str, List[Tuple[int, str]]] = {}
        # id → {"name", "scope", "width"}
        self.meta: Dict[str, dict] = {}
        # Exact full-path lookup and ambiguity-aware leaf lookup. Bare leaf names
        # resolve only when they identify exactly one VCD id.
        self._by_full: Dict[str, str] = {}
        self._by_leaf: Dict[str, Set[str]] = {}
        self._canonical_full_by_id: Dict[str, str] = {}
        self.t_min: int = 0
        self.t_max: int = 0

    # ── lookup ────────────────────────────────────────────────────
    def resolve_signal(self, signal: str, scope: str = "") -> Optional[dict]:
        """Resolve a signal to one concrete VCD row.

        Resolution order is intentionally conservative:
          1. explicit scope + name
          2. exact full path
          3. unique hierarchy suffix (for top/testbench stripped tool calls)
          4. unique leaf

        Ambiguous suffix/leaf matches return None instead of silently picking the
        first VCD declaration.
        """
        s = _norm_lookup(signal)
        if not s:
            return None
        wanted_scope = _norm_lookup(scope)
        if wanted_scope:
            scoped_keys = [f"{wanted_scope}.{s}"]
            leaf = s.rsplit(".", 1)[-1]
            if leaf != s:
                scoped_keys.append(f"{wanted_scope}.{leaf}")
            for key in scoped_keys:
                vid = self._by_full.get(key)
                if vid:
                    return self._resolved_row(vid, key)
            matches = {
                full: vid
                for full, vid in self._by_full.items()
                for key in scoped_keys
                if full == key or full.endswith("." + key)
            }
            ids = set(matches.values())
            if len(ids) == 1:
                full = next(iter(matches.keys()))
                return self._resolved_row(next(iter(ids)), full)
            return None

        vid = self._by_full.get(s)
        if vid:
            return self._resolved_row(vid, s)

        if "." in s:
            matches = {
                full: vid
                for full, vid in self._by_full.items()
                if full == s or full.endswith("." + s)
            }
            ids = set(matches.values())
            if len(ids) == 1:
                full = next(iter(matches.keys()))
                return self._resolved_row(next(iter(ids)), full)
            if len(ids) > 1:
                return None

        leaf = s.rsplit(".", 1)[-1]
        ids = self._by_leaf.get(leaf) or set()
        if len(ids) == 1:
            vid = next(iter(ids))
            return self._resolved_row(vid, self._canonical_full_by_id.get(vid, leaf))
        return None

    def resolve_id(self, signal: str, scope: str = "") -> Optional[str]:
        """Map a signal name to a VCD id when it resolves unambiguously."""
        row = self.resolve_signal(signal, scope)
        return str(row["id"]) if row else None

    def _resolved_row(self, vid: str, full: str) -> dict:
        m = self.meta.get(vid, {})
        name = str(m.get("name") or full.rsplit(".", 1)[-1])
        scope = str(m.get("scope") or "")
        if full and "." in full:
            scope, name = full.rsplit(".", 1)
        return {
            "id": vid,
            "name": name,
            "scope": scope,
            "full": full or (f"{scope}.{name}" if scope else name),
            "width": m.get("width"),
        }

    def match_signals(self, pattern: str, limit: int = 40) -> List[str]:
        try:
            rx = re.compile(pattern, re.I)
        except re.error:
            rx = re.compile(re.escape(pattern), re.I)
        seen, out = set(), []
        for full in self._by_full.keys():
            name = full.rsplit(".", 1)[-1]
            if (rx.search(name) or rx.search(full)) and full not in seen:
                seen.add(full)
                out.append(full)
                if len(out) >= limit:
                    break
        return out

    def time_range(self) -> Tuple[int, int]:
        return (self.t_min, self.t_max)

    # ── queries ───────────────────────────────────────────────────
    def edges(self, signal: str, kind: str = "rising", scope: str = "") -> List[int]:
        """Times where `signal` transitions. kind: rising|falling|any.
        For multi-bit signals only 'any' is meaningful."""
        vid = self.resolve_id(signal, scope)
        if not vid:
            return []
        series = self.changes.get(vid) or []
        out: List[int] = []
        prev: Optional[str] = None
        for t, v in series:
            cur = _scalar(v)
            if prev is not None:
                if kind == "any" and v != prev_raw:
                    out.append(t)
                elif kind == "rising" and prev != "1" and cur == "1":
                    out.append(t)
                elif kind == "falling" and prev != "0" and cur == "0":
                    out.append(t)
            prev, prev_raw = cur, v
        return out

    def value_at(self, signal: str, t: int, scope: str = "") -> Optional[str]:
        vid = self.resolve_id(signal, scope)
        if not vid:
            return None
        series = self.changes.get(vid) or []
        val: Optional[str] = None
        for ct, v in series:
            if ct > t:
                break
            val = v
        return val


def _scalar(v: str) -> str:
    """Reduce a value string to a single logic char for edge classification.
    Multi-bit → '1' if any bit set, '0' if all zero, else 'x'."""
    v = str(v)
    if len(v) == 1:
        return v.lower()
    s = v.lower().lstrip("b")
    if all(c == "0" for c in s):
        return "0"
    if any(c in "xz" for c in s):
        return "x"
    return "1"


def _norm_lookup(value: str) -> str:
    s = re.sub(r"\s*\[[^\]]*\]\s*$", "", str(value or "")).strip()
    s = s.replace("/", ".")
    if s.startswith("$root."):
        s = s[len("$root."):]
    return s.lower()


def load(path) -> VcdTimeline:
    tl = VcdTimeline()
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")

    mts = _TS_RE.search(text)
    if mts:
        m = re.search(r"[a-zµ]s", mts.group(1))
        tl.timescale = m.group(0) if m else mts.group(1).strip().split()[-1]

    scope_stack: List[str] = []
    in_defs = True
    cur_t = 0
    seen_t = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if in_defs:
            if line.startswith("$scope"):
                parts = line.split()
                if len(parts) >= 3:
                    scope_stack.append(parts[2])
                continue
            if line.startswith("$upscope"):
                if scope_stack:
                    scope_stack.pop()
                continue
            if line.startswith("$var"):
                mv = _VAR_RE.search(line)
                if mv:
                    width = int(mv.group(1))
                    vid = mv.group(2)
                    name = mv.group(3).strip()
                    # drop any [msb:lsb] suffix from the declared name
                    bare = re.sub(r"\s*\[[^\]]*\]\s*$", "", name).strip()
                    scope = ".".join(scope_stack)
                    tl.meta.setdefault(vid, {"name": bare, "scope": scope, "width": width})
                    full = f"{scope}.{bare}".lower() if scope else bare.lower()
                    leaf = bare.lower()
                    tl._by_full.setdefault(full, vid)
                    tl._by_leaf.setdefault(leaf, set()).add(vid)
                    tl._canonical_full_by_id.setdefault(vid, full)
                continue
            if line.startswith("$enddefinitions"):
                in_defs = False
                continue
            continue
        # ── value-change body ──
        c0 = line[0]
        if c0 == "#":
            try:
                cur_t = int(line[1:])
            except ValueError:
                continue
            if not seen_t:
                tl.t_min = cur_t
                seen_t = True
            tl.t_max = max(tl.t_max, cur_t)
            continue
        if c0 == "$":
            continue  # $dumpvars/$end/$dumpall...
        if c0 in "bB":
            sp = line.find(" ")
            if sp < 0:
                continue
            val, vid = line[:sp], line[sp + 1:].strip()
        elif c0 in "rR":
            sp = line.find(" ")
            if sp < 0:
                continue
            val, vid = line[:sp], line[sp + 1:].strip()
        else:
            val, vid = c0, line[1:].strip()
        if not vid:
            continue
        tl.changes.setdefault(vid, []).append((cur_t, val))
    return tl
