"""core/sim_debug_analyze.py — server-side VCD + pyslang analysis behind the
`sim_debug` agent tool's `trace` / `find` / `value` actions.

- trace : pyslang driver + load sites (file:line) for a signal — reuses
          workflow/sim_debug/elab.py + the shared source/top resolvers.
- find  : VCD timeline — time of a signal's Nth edge (core/vcd_timeline.py).
- value : VCD timeline — value of a signal at a given time.

Each returns readable text for the agent AND pushes a UI intent so the open
Sim Debug panel jumps/shows the result.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional


def _project_root() -> Path:
    return Path(os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd())


def _find_vcd(root: Path, ip: str) -> Optional[Path]:
    """Newest .vcd under <ip>/sim (mirrors src/atlas_api_vcd.py locations)."""
    ip = str(ip or "").strip().strip("/")
    if not ip:
        return None
    globs = [
        f"{ip}/sim/*.vcd",
        f"{ip}/sim/**/*.vcd",
        f"*/{ip}/sim/*.vcd",
        f"*/{ip}/sim/**/*.vcd",
    ]
    found: List[Path] = []
    for g in globs:
        found.extend(root.glob(g))
        if found:
            break
    found = [f for f in found if f.is_file()]
    if not found:
        return None
    return max(found, key=lambda f: f.stat().st_mtime)


def _load_elab(root: Path):
    """Load workflow/sim_debug/elab.py (by path, like the API does)."""
    import importlib.util as ilu
    elab_path = root / "workflow" / "sim_debug" / "elab.py"
    if not elab_path.is_file():
        raise FileNotFoundError(f"elab module not found at {elab_path}")
    spec = ilu.spec_from_file_location("sim_debug_elab_tool", str(elab_path))
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _resolve_sources_and_top(root: Path, ip: str, signal: str = ""):
    try:
        from sim_debug_sources import resolve_elab_sources
    except Exception:
        from src.sim_debug_sources import resolve_elab_sources  # type: ignore
    try:
        from atlas_sim_debug_top import resolve_sim_debug_top
    except Exception:
        from src.atlas_sim_debug_top import resolve_sim_debug_top  # type: ignore
    sources = resolve_elab_sources(root, "", ip)
    top_info = resolve_sim_debug_top(root, ip=ip, requested_top="")
    top = top_info.get("top") or ip or (signal.split(".", 1)[0] if signal else "")
    return sources, top


# ── trace (pyslang) ──────────────────────────────────────────────
def trace_signal(ip: str, signal: str) -> dict:
    root = _project_root()
    sig = str(signal or "").strip()
    if not sig:
        return {"error": "no signal given"}
    try:
        sources, top = _resolve_sources_and_top(root, ip, sig)
    except Exception as e:
        return {"error": f"source/top resolution failed: {e}"}
    if not sources:
        return {"error": f"no RTL sources found for ip '{ip}'"}
    try:
        elab = _load_elab(root)
        res = elab.trace_driver_cached("", top, sig, sources)
    except Exception as e:
        return {"error": f"pyslang trace failed: {e}"}
    res = dict(res or {})
    res["top"] = top
    return res


# ── find / value (VCD) ───────────────────────────────────────────
def _load_timeline(ip: str):
    root = _project_root()
    vcd = _find_vcd(root, ip)
    if vcd is None:
        return None, None
    try:
        from core.vcd_timeline import load
    except Exception:
        from vcd_timeline import load  # type: ignore
    return load(vcd), vcd


def _walk_hierarchy(tree: dict) -> List[dict]:
    out: List[dict] = []

    def rec(node: dict):
        if not isinstance(node, dict):
            return
        name = str(node.get("name") or "").strip()
        module = str(node.get("module") or "").strip()
        if name or module:
            out.append({"name": name, "module": module})
        for child in node.get("children") or []:
            rec(child)

    rec(tree or {})
    return out


def _norm_key(value: str) -> str:
    return str(value or "").strip().replace("/", ".").lower()


def _module_has_signal(module_signals, top: str, module: str, sources: List[Path], name: str, cache: dict) -> bool:
    key = str(module or "")
    if not key:
        return False
    if key not in cache:
        try:
            cache[key] = dict(module_signals("", top, key, sources))
        except Exception as e:
            cache[key] = {"error": str(e), "signals": []}
    leaf = _norm_key(name).rsplit(".", 1)[-1]
    for sig in cache[key].get("signals") or []:
        if _norm_key(sig.get("name", "")) == leaf:
            return True
    return False


def _candidate_from_hierarchy(ip: str, signal: str, scope: str, tl) -> dict:
    root = _project_root()
    sig = str(signal or "").strip()
    sig_scope = str(scope or "").strip()
    if not sig and not sig_scope:
        return {"status": "unresolved", "candidates": []}
    try:
        sources, top = _resolve_sources_and_top(root, ip, sig)
        elab = _load_elab(root)
        hierarchy = dict(elab.build_hierarchy_cached("", top, sources))
        module_signals = elab.module_signals_cached
    except Exception as e:
        return {"status": "unresolved", "error": f"pyslang hierarchy resolution failed: {e}", "candidates": []}

    nodes = _walk_hierarchy(hierarchy.get("tree") or {})
    if not nodes:
        return {"status": "unresolved", "candidates": []}

    wanted = _norm_key(sig)
    wanted_scope = _norm_key(sig_scope)
    prefix = ""
    leaf = wanted.rsplit(".", 1)[-1]
    if "." in wanted:
        prefix, leaf = wanted.rsplit(".", 1)
    scope_or_prefix = wanted_scope or prefix
    sig_cache = {}
    candidates: List[dict] = []

    def add_if_valid(node: dict) -> None:
        path = str(node.get("name") or "").strip()
        module = str(node.get("module") or "").strip()
        if not path or not module:
            return
        if not _module_has_signal(module_signals, top, module, sources, leaf, sig_cache):
            return
        resolved = tl.resolve_signal(leaf, path) if tl is not None else None
        full = resolved.get("full") if resolved else f"{path}.{leaf}"
        item = {
            "module": module,
            "scope": path,
            "name": leaf,
            "resolved_signal": full,
            "in_vcd": bool(resolved),
        }
        key = (_norm_key(full), _norm_key(path), leaf)
        if not any((c["_key"] == key) for c in candidates):
            item["_key"] = key
            candidates.append(item)

    if scope_or_prefix:
        for node in nodes:
            path_key = _norm_key(node.get("name", ""))
            module_key = _norm_key(node.get("module", ""))
            if path_key == scope_or_prefix or path_key.endswith("." + scope_or_prefix):
                add_if_valid(node)
            elif module_key == scope_or_prefix:
                add_if_valid(node)
    else:
        for node in nodes:
            add_if_valid(node)

    for c in candidates:
        c.pop("_key", None)

    in_vcd = [c for c in candidates if c.get("in_vcd")]
    if len(in_vcd) == 1:
        return {"status": "resolved", "source": "pyslang", **in_vcd[0]}
    if len(in_vcd) > 1:
        return {"status": "ambiguous", "candidates": in_vcd[:12]}
    if len(candidates) == 1:
        return {"status": "rtl_not_dumped", "source": "pyslang", **candidates[0]}
    if len(candidates) > 1:
        return {"status": "ambiguous", "candidates": candidates[:12]}
    return {"status": "unresolved", "candidates": []}


def resolve_wave_signal(ip: str, signal: str, scope: str = "") -> dict:
    """Resolve a tool-supplied signal before pushing it to the waveform UI.

    VCD lookup is authoritative for dumped waveform rows. If that misses, use
    pyslang/elab hierarchy to prove that `Module.pin` or `instance.pin` is a real
    RTL declaration/pin and map it back onto a concrete VCD scope.
    """
    sig = str(signal or "").strip()
    sig_scope = str(scope or "").strip()
    tl, vcd = _load_timeline(ip)
    if tl is not None:
        resolved = tl.resolve_signal(sig, sig_scope)
        if resolved:
            return {
                "status": "resolved",
                "source": "vcd",
                "signal": sig,
                "resolved_signal": resolved.get("full") or sig,
                "scope": resolved.get("scope", ""),
                "name": resolved.get("name", ""),
                "vcd": str(vcd),
            }

    checked = _candidate_from_hierarchy(ip, sig, sig_scope, tl)
    if checked.get("status") in ("resolved", "rtl_not_dumped", "ambiguous"):
        checked["signal"] = sig
        checked["vcd"] = str(vcd) if vcd is not None else ""
        return checked

    hints = tl.match_signals(sig, limit=8) if tl is not None else []
    return {
        "status": "unresolved",
        "signal": sig,
        "scope": sig_scope,
        "error": f"signal '{sig}' not in VCD",
        "did_you_mean": hints,
        "vcd": str(vcd) if vcd is not None else "",
    }


def find_event(ip: str, signal: str, edge: str = "rising", nth: int = 1, scope: str = "") -> dict:
    tl, vcd = _load_timeline(ip)
    if tl is None:
        return {"error": f"no VCD found under {ip}/sim"}
    edge = (edge or "rising").lower()
    if edge not in ("rising", "falling", "any"):
        edge = "rising"
    resolved = tl.resolve_signal(signal, scope)
    if resolved is None:
        checked = _candidate_from_hierarchy(ip, signal, scope, tl)
        if checked.get("status") == "resolved":
            resolved = {
                "full": checked.get("resolved_signal"),
                "scope": checked.get("scope", ""),
                "name": checked.get("name", ""),
            }
        elif checked.get("status") == "rtl_not_dumped":
            return {"error": f"signal '{signal}' is a real RTL signal/pin but is not dumped in this VCD",
                    "did_you_mean": [checked.get("resolved_signal", "")], "vcd": str(vcd)}
        elif checked.get("status") == "ambiguous":
            cands = [c.get("resolved_signal", "") for c in checked.get("candidates", []) if c.get("resolved_signal")]
            return {"error": f"signal '{signal}' is ambiguous; pass scope=... or a full VCD path",
                    "did_you_mean": cands, "vcd": str(vcd)}
        else:
            hint = tl.match_signals(signal, limit=8)
            return {"error": f"signal '{signal}' not in VCD", "did_you_mean": hint, "vcd": str(vcd)}
    resolved_signal = resolved.get("full") or signal
    times = tl.edges(resolved_signal, edge)
    try:
        n = max(1, int(nth))
    except (TypeError, ValueError):
        n = 1
    if not times:
        return {"signal": signal, "resolved_signal": resolved_signal,
                "scope": resolved.get("scope", ""), "name": resolved.get("name", ""),
                "edge": edge, "time": None, "count": 0,
                "time_range": tl.time_range(), "timescale": tl.timescale, "vcd": str(vcd)}
    idx = min(n, len(times)) - 1
    return {"signal": signal, "resolved_signal": resolved_signal,
            "scope": resolved.get("scope", ""), "name": resolved.get("name", ""),
            "edge": edge, "time": times[idx], "nth": n,
            "count": len(times), "all_times": times[:20],
            "time_range": tl.time_range(), "timescale": tl.timescale, "vcd": str(vcd)}


def signal_value(ip: str, signal: str, at: int, scope: str = "") -> dict:
    tl, vcd = _load_timeline(ip)
    if tl is None:
        return {"error": f"no VCD found under {ip}/sim"}
    resolved = tl.resolve_signal(signal, scope)
    if resolved is None:
        checked = _candidate_from_hierarchy(ip, signal, scope, tl)
        if checked.get("status") == "resolved":
            resolved = {
                "full": checked.get("resolved_signal"),
                "scope": checked.get("scope", ""),
                "name": checked.get("name", ""),
            }
        elif checked.get("status") == "rtl_not_dumped":
            return {"error": f"signal '{signal}' is a real RTL signal/pin but is not dumped in this VCD",
                    "did_you_mean": [checked.get("resolved_signal", "")]}
        elif checked.get("status") == "ambiguous":
            cands = [c.get("resolved_signal", "") for c in checked.get("candidates", []) if c.get("resolved_signal")]
            return {"error": f"signal '{signal}' is ambiguous; pass scope=... or a full VCD path",
                    "did_you_mean": cands}
        else:
            return {"error": f"signal '{signal}' not in VCD", "did_you_mean": tl.match_signals(signal, 8)}
    try:
        t = int(float(at))
    except (TypeError, ValueError):
        return {"error": "`at` (ns) must be a number"}
    resolved_signal = resolved.get("full") or signal
    return {"signal": signal, "resolved_signal": resolved_signal,
            "scope": resolved.get("scope", ""), "name": resolved.get("name", ""),
            "at": t, "value": tl.value_at(resolved_signal, t),
            "timescale": tl.timescale, "vcd": str(vcd)}


# ── dispatcher (called by core.tools.sim_debug) ──────────────────
def run_sim_debug_analysis(action: str, ip: str = "", signal: str = "",
                           edge: str = "rising", nth: int = 1, at=None,
                           push_intent=None, scope: str = "") -> str:
    sig = str(signal or "").strip()
    sig_scope = str(scope or "").strip()
    where = ip or "active IP"

    if action == "trace":
        if not sig:
            return "[sim_debug trace: signal required]"
        r = trace_signal(ip, sig)
        if r.get("error"):
            return f"[sim_debug trace: {r['error']}]"
        if push_intent:
            push_intent(ip, "trace", signal=sig, scope=(sig_scope or None))
        drv = r.get("driver") or {}
        drivers = r.get("drivers") or ([drv] if drv else [])
        sinks = r.get("sinks") or []
        lines = [f"Sim Debug trace of '{sig}' (top {r.get('top','?')}, {where}):"]
        # Every place the signal is assigned, WITH the condition it fires under
        # (find "where is X set under condition Y"). The structural driving view.
        lines.append(f"  drivers ({r.get('driver_count', len(drivers))}):")
        for d in drivers[:12]:
            cond = str(d.get("condition") or "").strip()
            cond_s = f"  ⟵ when {cond}" if cond else ""
            lines.append(f"    {d.get('file_line','?')}{cond_s}  [{d.get('kind','')}]")
        if not drivers:
            lines.append("    (none)")
        if sinks:
            lines.append(f"  loads ({r.get('sink_count', len(sinks))}):")
            for s in sinks[:10]:
                lines.append(f"    {s.get('file_line','?')}  {s.get('access','')}")
        else:
            lines.append("  loads: (none found)")
        lines.append("  → shown in the Sim Debug trace popover.")
        return "\n".join(lines)

    if action == "find":
        if not sig:
            return "[sim_debug find: signal required]"
        r = find_event(ip, sig, edge, nth, sig_scope)
        if r.get("error"):
            dym = r.get("did_you_mean")
            return f"[sim_debug find: {r['error']}" + (f"; did you mean: {', '.join(dym)}" if dym else "") + "]"
        ts = r.get("timescale", "ns")
        t = r.get("time")
        resolved_sig = r.get("resolved_signal") or sig
        resolved_note = f" (resolved {resolved_sig})" if resolved_sig != sig else ""
        if t is None:
            return f"No {r['edge']} edge of '{sig}'{resolved_note} found in the VCD ({where})."
        if push_intent:
            tmin, tmax = r.get("time_range", (0, 0))
            pad = max(1, (tmax - tmin) // 20) if tmax > tmin else max(1, abs(t) // 10 or 1)
            push_intent(ip, "goto", t_start=max(tmin, t - pad), t_end=min(tmax, t + pad),
                        cursor_a=t, signals=[resolved_sig])
        return (f"'{sig}'{resolved_note} {r['edge']} edge #{r.get('nth',1)} at {t} {ts} "
                f"(of {r.get('count',0)} total; {where}). Jumped the panel there with the signal shown.")

    if action == "value":
        if not sig:
            return "[sim_debug value: signal required]"
        r = signal_value(ip, sig, at, sig_scope)
        if r.get("error"):
            return f"[sim_debug value: {r['error']}]"
        resolved_sig = r.get("resolved_signal") or sig
        resolved_note = f" (resolved {resolved_sig})" if resolved_sig != sig else ""
        if push_intent:
            push_intent(ip, "cursor", cursor_a=r["at"], signals=[resolved_sig])
        return f"'{sig}'{resolved_note} = {r.get('value')} at {r['at']} {r.get('timescale','ns')} ({where})."

    return f"[sim_debug: action '{action}' not supported by analysis]"
