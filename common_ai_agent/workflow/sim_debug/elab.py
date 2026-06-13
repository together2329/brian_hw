"""src/sim_debug_elab.py — SystemVerilog elaboration backends for
sim_debug workspace.

Strategy pattern: caller asks for a backend ("dual", "pyslang", "verilator",
or "slang"); we
dispatch to the matching implementation. Both shell out to a real SV
frontend so hierarchy + trace data is 100% accurate (regex extraction
broke on generate / macro / bind).

Public API:
  - get_backend(prefer: str) -> ElabBackend
  - ElabBackend.available() -> bool
  - ElabBackend.build_hierarchy(top, sources) -> dict
  - ElabBackend.trace_driver(scope, signal, sources) -> dict
  - status() -> {dual: bool, pyslang: bool, verilator: bool, slang: bool}

Cache: results memoize on (backend, top, sources hash, source mtimes)
to avoid re-elab on every UI click. Cache lives at
PROJECT_ROOT/.session/elab_cache/<key>.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional

from core.pyslang_compat import compile_files as compile_pyslang_files
from core.pyslang_compat import import_pyslang, syntax_tree_class
from core.pyslang_compat import root_symbol, source_manager as pyslang_source_manager


ELAB_CACHE_VERSION = "sim-debug-elab-v10-multi-driver-trace"


def _project_root() -> Path:
    return Path(os.getcwd()).resolve()


def _cache_dir() -> Path:
    d = _project_root() / ".session" / "elab_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_key(backend: str, top: str, sources: list[Path]) -> str:
    h = hashlib.sha1()
    h.update(ELAB_CACHE_VERSION.encode())
    h.update(b"\0")
    h.update(backend.encode())
    h.update(b"\0")
    h.update(top.encode())
    for s in sources:
        h.update(b"\0")
        h.update(str(s).encode())
        try:
            h.update(str(s.stat().st_mtime).encode())
        except OSError:
            pass
    return h.hexdigest()[:20]


def _cache_get(key: str) -> Optional[dict]:
    p = _cache_dir() / f"{key}.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _cache_put(key: str, data: dict) -> None:
    # Do not persist transient compiler/API errors. pyslang wheels have had
    # incompatible Python API shapes, and caching those failures makes the UI
    # look broken even after the environment or fallback logic is fixed.
    if data.get("error") and not data.get("tree"):
        return
    try:
        (_cache_dir() / f"{key}.json").write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


_SV_RESERVED = {
    "module", "endmodule", "always", "always_ff", "always_comb", "always_latch",
    "if", "else", "begin", "end", "case", "endcase", "casex", "casez", "for",
    "while", "assign", "wire", "reg", "logic", "input", "output", "inout",
    "parameter", "localparam", "function", "endfunction", "task", "endtask",
    "generate", "endgenerate", "return", "initial", "final", "typedef", "enum",
    "struct", "union", "package", "endpackage", "import", "export", "interface",
    "endinterface", "modport", "class", "endclass",
}


def _strip_sv_comments(text: str) -> str:
    """Remove comments while preserving line numbers for source links."""
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)
    return re.sub(r"//.*?$", "", text, flags=re.MULTILINE)


def _module_index_from_text(sources: list[Path]) -> dict[str, dict]:
    modules: dict[str, dict] = {}
    module_re = re.compile(r"^\s*module\s+([A-Za-z_]\w*)\b")
    endmodule_re = re.compile(r"^\s*endmodule\b")

    def _scan_module_token(lines: list[str], idx: int) -> str:
        for j in range(idx - 1, max(-1, idx - 40), -1):
            stripped = lines[j].strip()
            if not stripped or stripped.startswith(".") or stripped.startswith(")"):
                continue
            m = re.match(r"^([A-Za-z_]\w*)\s*(?:#\s*\(?\s*)?$", stripped)
            if m and m.group(1) not in _SV_RESERVED:
                return m.group(1)
            m = re.match(r"^([A-Za-z_]\w*)\s*#\s*\(", stripped)
            if m and m.group(1) not in _SV_RESERVED:
                return m.group(1)
            if stripped.endswith(";") or stripped.startswith(("module ", "endmodule")):
                break
        return ""

    def _instances(body_lines: list[str], base_line: int) -> list[dict]:
        out: list[dict] = []
        single_re = re.compile(
            r"^\s*([A-Za-z_]\w*)\s*(?:#\s*\(.*\)\s*)?\s+([A-Za-z_]\w*)\s*\("
        )
        close_param_re = re.compile(r"^\s*\)\s*([A-Za-z_]\w*)\s*\(")
        for idx, line in enumerate(body_lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("."):
                continue
            m = single_re.match(line)
            if m:
                mod_name, inst_name = m.group(1), m.group(2)
                if mod_name not in _SV_RESERVED and inst_name not in _SV_RESERVED:
                    out.append({"module": mod_name, "name": inst_name, "line": base_line + idx})
                    continue
            m = close_param_re.match(line)
            if m:
                mod_name = _scan_module_token(body_lines, idx)
                if mod_name:
                    out.append({"module": mod_name, "name": m.group(1), "line": base_line + idx})
        return out

    for src in sources:
        try:
            lines = _strip_sv_comments(src.read_text(encoding="utf-8", errors="replace")).splitlines()
        except OSError:
            continue
        cur_name = ""
        cur_start = 0
        cur_body: list[str] = []
        for line_no, line in enumerate(lines, start=1):
            if not cur_name:
                m = module_re.match(line)
                if m:
                    cur_name = m.group(1)
                    cur_start = line_no
                    cur_body = []
                continue
            if endmodule_re.match(line):
                insts = _instances(cur_body, cur_start + 1)
                prev = modules.get(cur_name)
                if prev is None or len(insts) >= len(prev.get("instances") or []):
                    modules[cur_name] = {
                        "file": src.as_posix(),
                        "line": cur_start,
                        "instances": insts,
                    }
                cur_name = ""
                cur_body = []
            else:
                cur_body.append(line)
    return modules


def _static_hierarchy(top: str, sources: list[Path], reason: str) -> dict:
    modules = _module_index_from_text(sources)
    if not modules:
        return {"error": f"pyslang compile: {reason}", "tree": None}

    instantiated = {
        inst.get("module")
        for meta in modules.values()
        for inst in meta.get("instances") or []
        if inst.get("module") in modules
    }
    chosen = top if top in modules else ""
    if not chosen:
        roots = [name for name in modules if name not in instantiated]
        chosen = roots[0] if roots else next(iter(modules))

    def _walk(module_name: str, inst_path: str, seen: set[str]) -> dict:
        meta = modules.get(module_name, {})
        children = []
        for inst in meta.get("instances") or []:
            child_mod = str(inst.get("module") or "")
            child_inst = str(inst.get("name") or child_mod or "?")
            child_path = f"{inst_path}.{child_inst}" if inst_path else child_inst
            if child_mod in modules and child_mod not in seen:
                children.append(_walk(child_mod, child_path, seen | {child_mod}))
            else:
                children.append({"name": child_path, "module": child_mod or child_inst, "children": []})
        return {"name": inst_path or module_name, "module": module_name, "children": children}

    module_files = {
        name: {"file": meta.get("file", ""), "line": int(meta.get("line") or 0)}
        for name, meta in modules.items()
    }
    return {
        "backend": "pyslang-text-fallback",
        "warning": f"pyslang compile failed; used static RTL hierarchy fallback: {reason}",
        "tree": _walk(chosen, chosen, {chosen}),
        "modules_found": sorted(modules),
        "module_files": module_files,
    }


def _dedupe_file_line(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        fl = str(row.get("file_line") or "")
        kind = str(row.get("kind") or row.get("access") or "")
        if not fl:
            continue
        key = (fl, kind)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _trace_payload(backend: str, drivers: list[dict], sinks: list[dict], **extra) -> dict:
    all_drivers = _dedupe_file_line(drivers)
    drivers = all_drivers[:20]
    driver_lines = {str(d.get("file_line") or "") for d in drivers if d.get("file_line")}
    deduped_sinks = [
        sk for sk in _dedupe_file_line(sinks)
        if str(sk.get("file_line") or "") not in driver_lines
    ]
    return {
        **extra,
        "backend": backend,
        "driver": drivers[0] if drivers else None,
        "drivers": drivers,
        "driver_count": len(all_drivers),
        "sinks": deduped_sinks[:20],
        "sink_count": len(deduped_sinks),
    }


def _balanced_paren(s: str, search_from: int) -> "str | None":
    """Text inside the first balanced (...) at/after `search_from`; the rest of
    the line when the parens span lines (best-effort)."""
    i = s.find("(", search_from)
    if i < 0:
        return None
    d = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                return s[i + 1:j].strip()
    return s[i + 1:].strip()


_IF_RE = re.compile(r"(?<![\w.$])if\s*\(")
_ELSEIF_RE = re.compile(r"\belse\s+if\s*\(")
_CASE_RE = re.compile(r"\b(?:unique0?\s+|priority\s+)?case[zx]?\s*\(")


def enclosing_conditions(block_text: str) -> dict:
    """Map each 0-based line offset of an always-block's text to the list of
    enclosing if / else-if / else / case conditions (outer → inner).

    Text-structural heuristic that matches the line-based driver scanner (the
    block is ``str(syntax)``), NOT a full AST — multi-line conditions and exotic
    styles may be approximate. Tuned for the synthesizable RTL this pipeline
    emits (consistent begin/end). `else` renders as ``!(<sibling-if>)`` when the
    sibling is known. Used to annotate each driver with the condition it fires
    under, so the user can find "where is X assigned under condition Y".
    """
    out: dict = {}
    # frames: {"kind": "block"|"case", "depth": int, "cond": str|None,
    #          "sel": str|None, "item": str|None}
    frames: list = []
    depth = 0
    last_popped = None  # cond of the just-closed if-BLOCK a following `else` negates
    last_if = None      # most recent if-cond (block OR one-line) for else negation
    for off, raw in enumerate(block_text.split("\n")):
        s = re.sub(r"//.*$", "", raw)
        stripped = s.strip()

        # 1) leading `end`/`endcase` close blocks opened above this line.
        lead = re.match(r"^((?:end\b|endcase\b|\s)*)", stripped)
        for _ in range(len(re.findall(r"\bend\b|\bendcase\b", lead.group(1))) if lead else 0):
            if frames:
                d = frames[-1]["depth"]
                popped = [f for f in frames if f["depth"] == d]
                if popped and popped[-1]["kind"] == "block":
                    last_popped = popped[-1]["cond"]
                frames[:] = [f for f in frames if f["depth"] < d]
                depth = max(0, depth - 1)

        # 2) conditions active for THIS line = open block conds + case-item conds.
        line_conds = []
        for f in frames:
            if f["kind"] == "block" and f["cond"]:
                line_conds.append(f["cond"])
            elif f["kind"] == "case" and f["item"]:
                line_conds.append(f["item"])

        # 3) the control header (if any) on this line.
        cond = None
        m_elif = _ELSEIF_RE.search(stripped)
        if m_elif:
            cond = _balanced_paren(stripped, m_elif.end() - 1)
            last_if = cond
        elif re.match(r"^(?:end\s+)?else\b", stripped):
            base = last_popped if last_popped is not None else last_if
            cond = f"!({base})" if base else "(else)"
        elif _IF_RE.search(stripped):
            m = _IF_RE.search(stripped)
            cond = _balanced_paren(stripped, m.end() - 1)
            last_if = cond
        elif _CASE_RE.search(stripped):
            m = _CASE_RE.search(stripped)
            sel = _balanced_paren(stripped, m.end() - 1)
            depth += 1
            frames.append({"kind": "case", "depth": depth, "cond": None, "sel": sel, "item": None})
        else:
            # a case item label (`IDLE:` / `A, B:` / `default:`) when inside a case.
            inner = frames[-1] if frames else None
            if inner and inner["kind"] == "case":
                mi = re.match(r"^(default|[A-Za-z_]\w[\w\s,]*?)\s*:(?!:)", stripped)
                if mi:
                    label = mi.group(1).strip()
                    sel = inner["sel"] or "case"
                    inner["item"] = "default" if label == "default" else f"{sel} == {label}"
                    line_conds = line_conds + ([inner["item"]] if inner["item"] else [])

        has_begin = re.search(r"\bbegin\b", s) is not None
        is_stmt = ("<=" in s or re.search(r"(?<![<>=!])=(?!=)", s)) and not has_begin
        # one-line body `if (C) stmt;` → C applies to this line only.
        if cond is not None and is_stmt:
            line_conds = line_conds + [cond]
        out[off] = line_conds

        # 4) `begin` opens a block carrying the header condition (first begin only).
        for k in range(len(re.findall(r"\bbegin\b", s))):
            depth += 1
            frames.append({"kind": "block", "depth": depth, "cond": cond if k == 0 else None,
                           "sel": None, "item": None})
            cond = None
    return out


def _static_trace_driver(signal: str, sources: list[Path], reason: str) -> dict:
    bare = signal.rsplit(".", 1)[-1]
    bare = re.sub(r"\s*\[[^\]]+\]\s*$", "", bare).strip()
    if not bare:
        return {"error": f"pyslang compile: {reason}", "driver": None, "drivers": [], "sinks": []}
    word_re = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(bare) + r"(?![A-Za-z0-9_])")
    assign_re = re.compile(r"<=|(?<![<>!=])=(?!=)")
    decl_re = re.compile(r"\b(input|output|inout|wire|reg|logic)\b[^;]*\b" + re.escape(bare) + r"\b")
    drivers: list[dict] = []
    decl = None
    sinks: list[dict] = []
    for src in sources:
        try:
            lines = _strip_sv_comments(src.read_text(encoding="utf-8", errors="replace")).splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if not word_re.search(line):
                continue
            fl = f"{src.as_posix()}:{line_no}"
            if decl is None and decl_re.search(line):
                decl = {"file_line": fl, "kind": "declaration (text fallback)"}
            m = assign_re.search(line)
            if m:
                lhs, rhs = line[:m.start()], line[m.end():]
                if word_re.search(lhs):
                    drivers.append({"file_line": fl, "kind": "assignment (text fallback)"})
                if word_re.search(rhs):
                    sinks.append({"file_line": fl, "context": bare, "access": "RD"})
            elif re.search(r"\.\s*[A-Za-z_]\w*\s*\(\s*" + re.escape(bare) + r"\s*\)", line):
                sinks.append({"file_line": fl, "context": bare, "access": "PORT"})
    if not drivers and decl is not None:
        drivers.append(decl)
    return _trace_payload(
        "pyslang-text-fallback",
        drivers,
        sinks,
        warning=f"pyslang compile failed; used static RTL trace fallback: {reason}",
    )


# ── Base ─────────────────────────────────────────────────────────
class ElabBackend:
    name = "abstract"

    def available(self) -> bool:
        raise NotImplementedError

    def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
        raise NotImplementedError

    def trace_driver(self, scope: str, signal: str, sources: list[Path]) -> dict:
        raise NotImplementedError

    def module_signals(self, top: str, module: str, sources: list[Path]) -> dict:
        raise NotImplementedError


# ── Signal helpers (shared by pyslang + text fallback) ───────────
def _width_from_type(type_text: str) -> int:
    """Best-effort bit width from a type string like 'logic[15:0]' → 16.

    Packed ranges multiply (`logic[1:0][7:0]` → 16). A bare scalar
    (`logic`, `wire`) is width 1. Anything we cannot parse returns 0 so
    the UI can fall back to showing the raw type string instead.
    """
    text = str(type_text or "")
    width = 1
    found = False
    for m in re.finditer(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", text):
        hi, lo = int(m.group(1)), int(m.group(2))
        width *= abs(hi - lo) + 1
        found = True
    return width if found else (1 if text.strip() else 0)


def _direction_label(direction_text: str) -> str:
    """Map pyslang ArgumentDirection.* → 'in' | 'out' | 'inout'."""
    d = str(direction_text or "").rsplit(".", 1)[-1].lower()
    if d.startswith("in") and "out" in d:
        return "inout"
    if d.startswith("out"):
        return "out"
    if d.startswith("in"):
        return "in"
    if "inout" in d or "ref" in d:
        return "inout"
    return "internal"


def _signal_counts(signals: list[dict]) -> dict:
    counts = {"in": 0, "out": 0, "inout": 0, "internal": 0, "total": 0}
    for s in signals:
        d = s.get("direction", "internal")
        if d in counts:
            counts[d] += 1
        counts["total"] += 1
    return counts


def _static_module_signals(module: str, sources: list[Path], reason: str) -> dict:
    """Regex fallback when pyslang cannot elaborate. Parses the module's
    ANSI port header for directions and the body for internal
    reg/wire/logic declarations. Coarse (no generate/macro awareness) but
    keeps the panel populated instead of blank."""
    mod_re = re.compile(r"\bmodule\s+" + re.escape(module) + r"\b")
    port_re = re.compile(
        r"\b(input|output|inout)\b\s*(?:wire|reg|logic|bit)?\s*(?:signed\s*)?"
        r"((?:\[[^\]]+\]\s*)*)([A-Za-z_]\w*)"
    )
    decl_re = re.compile(
        r"^\s*(?:wire|reg|logic|bit)\s+(?:signed\s+)?((?:\[[^\]]+\]\s*)*)([A-Za-z_]\w*)"
    )
    signals: list[dict] = []
    seen: set[str] = set()
    for src in sources:
        try:
            text = _strip_sv_comments(src.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if not mod_re.search(text):
            continue
        lines = text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            for m in port_re.finditer(line):
                name = m.group(3)
                if name in seen:
                    continue
                seen.add(name)
                rng = (m.group(2) or "").strip()
                signals.append({
                    "name": name,
                    "direction": _direction_label(m.group(1)),
                    "kind": "port",
                    "type": ("logic " + rng).strip() if rng else "logic",
                    "width": _width_from_type(rng) or 1,
                    "file": src.as_posix(), "line": line_no,
                    "file_line": f"{src.as_posix()}:{line_no}",
                })
            dm = decl_re.match(line)
            if dm and dm.group(2) not in seen and not port_re.search(line):
                name = dm.group(2)
                seen.add(name)
                rng = (dm.group(1) or "").strip()
                signals.append({
                    "name": name,
                    "direction": "internal",
                    "kind": "net",
                    "type": ("logic " + rng).strip() if rng else "logic",
                    "width": _width_from_type(rng) or 1,
                    "file": src.as_posix(), "line": line_no,
                    "file_line": f"{src.as_posix()}:{line_no}",
                })
        break
    return {
        "backend": "pyslang-text-fallback",
        "warning": f"pyslang elaboration unavailable; used static RTL signal scan: {reason}",
        "module": module,
        "signals": signals,
        "counts": _signal_counts(signals),
    }


# ── Verilator backend ────────────────────────────────────────────
class VerilatorElab(ElabBackend):
    """Uses `verilator --json-only` (replaces deprecated --xml-only in 5.x)."""

    name = "verilator"

    def available(self) -> bool:
        return shutil.which("verilator") is not None

    def _run(self, top: str, sources: list[Path]) -> Optional[dict]:
        if not sources:
            return None
        out_dir = _cache_dir() / f"verilator_{top}"
        out_dir.mkdir(exist_ok=True)
        out_json = out_dir / f"V{top}.tree.json"
        cmd = [
            "verilator", "--json-only",
            "-Wno-fatal",
            "-Wno-MULTITOP", "-Wno-MODDUP", "-Wno-DECLFILENAME",
            "-Wno-WIDTHEXPAND", "-Wno-WIDTHTRUNC", "-Wno-UNUSEDSIGNAL",
            "--top-module", top,
            "--Mdir", str(out_dir),
            "--json-only-output", str(out_json),
            *(str(s) for s in sources),
        ]
        try:
            subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                cwd=str(_project_root()),
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if not out_json.is_file():
            return None
        try:
            return json.loads(out_json.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _walk_modules(root, modules: dict, file_map: dict, srcs: list,
                      module_files: dict = None) -> None:
        """Walk Verilator AST JSON and collect AstModule + AstCell nodes.
        Also fills `module_files[mod_name] = {file, line}` so the
        frontend can jump to the *real* definition (e.g. `gpio_pad` is
        actually defined in `gpio_pad_wrapper.sv`, not the empty
        `gpio_pad.sv` stub)."""
        if not isinstance(root, dict):
            return
        node_type = root.get("type", "")
        if node_type == "MODULE" or node_type == "AstModule":
            mod_name = root.get("name", "")
            # Capture the module's defining file:line via its loc.
            mod_loc = root.get("loc", "")
            if module_files is not None and mod_loc and file_map:
                try:
                    fid, span = mod_loc.split(",", 1)
                    line_no = int(span.split(":", 1)[0])
                    fpath = file_map.get(fid, {}).get("filename", "")
                    if fpath and fpath != "<built-in>" and fpath != "<verilated_std>":
                        if mod_name not in module_files:
                            module_files[mod_name] = {"file": fpath, "line": line_no}
                except (ValueError, KeyError):
                    pass
            kids = []
            for cell in VerilatorElab._iter_kind(root, ("CELL", "AstCell")):
                inst_name = cell.get("name", "")
                # Resolve module via source line lookup. loc format:
                # "<file_id>,<line>:<col>,<line>:<col>". e.g. "g,49:7,49:13"
                cell_module = ""
                loc = cell.get("loc", "")
                if loc and file_map:
                    try:
                        fid, span = loc.split(",", 1)
                        line_no = int(span.split(":", 1)[0])
                        fpath = file_map.get(fid, {}).get("filename", "")
                        if fpath and fpath != "<built-in>":
                            cell_module = VerilatorElab._read_module_at_line(fpath, line_no, inst_name)
                    except (ValueError, KeyError):
                        pass
                kids.append({
                    "name": inst_name,
                    "module": cell_module or inst_name,
                })
            modules[mod_name] = kids
        # recurse
        for v in root.values() if isinstance(root, dict) else []:
            if isinstance(v, list):
                for item in v:
                    VerilatorElab._walk_modules(item, modules, file_map, srcs, module_files)
            elif isinstance(v, dict):
                VerilatorElab._walk_modules(v, modules, file_map, srcs, module_files)

    @staticmethod
    def _read_module_at_line(file_path: str, line_no: int, inst_name: str) -> str:
        """Resolve the module name for a Verilog instantiation. Verilator's
        cell `loc` points at the instance NAME line (e.g. `) u_core (`),
        which is several lines after the module name when parameters are
        passed via `#(...)`. So we scan backward up to 30 lines looking
        for the canonical instantiation prefix.

        Patterns handled:
        - `<module> <inst> (`               (single-line, no params)
        - `<module> #(<params>) <inst> (`   (single-line with inline params)
        - `<module> #(`  ...  `) <inst> (`  (multi-line params)
        """
        try:
            from pathlib import Path as _P
            lines = _P(file_path).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ""
        import re as _re

        _RESERVED = {
            "module", "endmodule", "always", "always_ff", "always_comb",
            "always_latch", "if", "else", "begin", "end", "case", "endcase",
            "casex", "casez", "for", "while", "assign", "wire", "reg",
            "logic", "input", "output", "inout", "parameter", "localparam",
            "function", "endfunction", "task", "endtask", "generate",
            "endgenerate", "return", "initial", "final", "typedef", "enum",
            "struct", "union", "package", "endpackage", "import", "export",
            "interface", "endinterface", "modport", "class", "endclass",
        }

        # Strategy 1: same line as inst_name OR next line. Pattern:
        #   ^\s*<module>\s*(?:#\(...\))?\s*<inst>\s*\(
        # works for single-line forms.
        same_line_pat = _re.compile(
            r"^\s*([A-Za-z_]\w*)\s*(?:#\s*\([^)]*\))?\s*"
            + _re.escape(inst_name) + r"\s*\("
        )
        for delta in (0, -1, 1):
            idx = line_no - 1 + delta
            if 0 <= idx < len(lines):
                m = same_line_pat.match(lines[idx])
                if m:
                    cand = m.group(1)
                    if cand not in _RESERVED:
                        return cand

        # Strategy 2: multi-line `<module> #(` ... `) <inst> (`. Walk
        # backward from the inst line; the FIRST plausible identifier
        # at column 0..N (i.e. a module name on its own) before any
        # `<inst> (` opening paren is our target.
        # Stop scanning at 30 lines back, an `endmodule`, or a `;` at
        # end-of-line that isn't part of `#(...)` (statement boundary).
        ident_pat = _re.compile(r"^\s*([A-Za-z_]\w*)\s*(?:#\s*\(|\(|$)")
        opening_pat = _re.compile(r"\bmodule\b|\bendmodule\b")
        for back in range(0, 30):
            idx = line_no - 1 - back
            if idx < 0:
                break
            line = lines[idx]
            if opening_pat.search(line):
                # crossed the enclosing module declaration; stop
                break
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            # Only accept a line whose first token is an identifier and
            # whose continuation strongly suggests an instantiation
            # header. A line that ends with `;` is a statement, skip it.
            if stripped.endswith(";"):
                continue
            m = ident_pat.match(line)
            if m:
                cand = m.group(1)
                if cand in _RESERVED:
                    continue
                # Heuristic: a module instantiation header line is
                # usually `<MOD>` followed by `#(` on same line, or
                # `<MOD>` alone. Accept the first match.
                return cand
        return ""

    @staticmethod
    def _iter_kind(node: dict, kinds: tuple) -> Iterable[dict]:
        if not isinstance(node, dict):
            return
        if node.get("type", "") in kinds:
            yield node
        for v in node.values():
            if isinstance(v, list):
                for item in v:
                    yield from VerilatorElab._iter_kind(item, kinds)
            elif isinstance(v, dict):
                yield from VerilatorElab._iter_kind(v, kinds)

    def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
        ast = self._run(top, sources)
        if ast is None:
            return {"error": "verilator failed", "tree": None}

        # Pull file_map from sibling meta.json so cell loc attrs resolve.
        out_dir = _cache_dir() / f"verilator_{top}"
        meta_path = out_dir / f"V{top}.tree.meta.json"
        file_map = {}
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
            file_map = meta.get("files", {}) or {}
        except (OSError, json.JSONDecodeError):
            pass

        modules: dict = {}
        module_files: dict = {}
        self._walk_modules(ast, modules, file_map, sources, module_files)

        def _build(mod_name: str, inst_path: str, visited: set) -> dict:
            if mod_name in visited:
                return {"name": inst_path or mod_name, "module": mod_name, "children": [], "cyclic": True}
            visited = visited | {mod_name}
            kids = []
            for c in modules.get(mod_name, []):
                child_path = f"{inst_path}.{c['name']}" if inst_path else c["name"]
                kids.append(_build(c["module"], child_path, visited))
            return {"name": inst_path or mod_name, "module": mod_name, "children": kids}

        tree = _build(top, top, set())
        return {
            "backend": "verilator",
            "tree": tree,
            "modules_found": list(modules.keys()),
            "module_files": module_files,
        }

    def trace_driver(self, top: str, signal: str, sources: list[Path]) -> dict:
        """Run verilator from `top` then walk the AST for nodes touching
        `signal`. Caller passes `top` (the elaboration root), not the
        signal scope — the scope's first segment may not be a real module
        name (e.g. it could be the signal itself for unscoped queries)."""
        ast = self._run(top, sources)
        if ast is None:
            return {"error": "verilator failed (top=" + top + ")", "driver": None, "drivers": [], "sinks": []}

        # Resolve loc → "<file>:<line>" using the meta.json file_map.
        out_dir = _cache_dir() / f"verilator_{top}"
        meta_path = out_dir / f"V{top}.tree.meta.json"
        file_map = {}
        try:
            file_map = (json.loads(meta_path.read_text(encoding="utf-8", errors="replace")) or {}).get("files", {}) or {}
        except (OSError, json.JSONDecodeError):
            pass

        def _human_loc(loc: str) -> str:
            if not loc:
                return ""
            try:
                fid, span = loc.split(",", 1)
                line = span.split(":", 1)[0]
                fpath = file_map.get(fid, {}).get("filename", "")
                return f"{fpath}:{line}" if fpath else loc
            except (ValueError, KeyError):
                return loc

        # Bare signal name (last segment) — most VCDs report scoped names
        # but the AST stores just the local var name.
        bare = signal.rsplit(".", 1)[-1]

        drivers: list[dict] = []
        sinks: list[dict] = []

        def _walk(node):
            if isinstance(node, list):
                for n in node:
                    _walk(n)
                return
            if not isinstance(node, dict):
                return
            t = node.get("type", "")
            # ASSIGNW / ALWAYS that mention bare signal → candidate driver.
            if t in ("ASSIGNW", "AstAssignW", "ALWAYS", "AstAlways"):
                blob = json.dumps(node)
                if bare in blob:
                    drivers.append({"file_line": _human_loc(node.get("loc", "")), "kind": t})
            # VARREF whose name == bare signal → sink.
            elif t in ("VARREF", "AstVarRef") and node.get("name", "") == bare:
                sinks.append({
                    "file_line": _human_loc(node.get("loc", "")),
                    "context": node.get("name", ""),
                    "access": node.get("access", ""),
                })
            for v in node.values():
                _walk(v)

        _walk(ast)
        return _trace_payload("verilator", drivers, sinks)


# ── Slang backend ────────────────────────────────────────────────
class SlangElab(ElabBackend):
    """Uses `slang --ast-json` for the most accurate elab tree."""

    name = "slang"

    def available(self) -> bool:
        return shutil.which("slang") is not None

    def _run(self, top: str, sources: list[Path]) -> Optional[dict]:
        if not sources:
            return None
        out = _cache_dir() / f"slang_{top}.ast.json"
        cmd = [
            "slang", "--top", top, "--ast-json", str(out),
            *(str(s) for s in sources),
        ]
        try:
            subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                cwd=str(_project_root()),
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if not out.is_file():
            return None
        try:
            return json.loads(out.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return None

    def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
        ast = self._run(top, sources)
        if ast is None:
            return {"error": "slang failed", "tree": None}

        def _walk(node, path) -> Optional[dict]:
            if not isinstance(node, dict):
                return None
            kind = node.get("kind", "")
            name = node.get("name", "")
            if kind == "Instance":
                inst_path = f"{path}.{name}" if path else name
                children = []
                for m in (node.get("body", {}).get("members") or []):
                    sub = _walk(m, inst_path)
                    if sub is not None:
                        children.append(sub)
                return {
                    "name": inst_path or name,
                    "module": node.get("body", {}).get("name", "") or name,
                    "children": children,
                }
            if kind == "Root":
                tops = []
                for m in (node.get("members") or []):
                    sub = _walk(m, "")
                    if sub is not None:
                        tops.append(sub)
                if len(tops) == 1:
                    return tops[0]
                return {"name": "$root", "module": "$root", "children": tops}
            return None

        tree = _walk(ast.get("design", ast), "")
        return {"backend": "slang", "tree": tree}

    def trace_driver(self, top: str, signal: str, sources: list[Path]) -> dict:
        ast = self._run(top, sources)
        if ast is None:
            return {"error": "slang failed (top=" + top + ")", "driver": None, "drivers": [], "sinks": []}

        # Slang's AST has Symbol nodes with `loc` (file:line). Walk and
        # collect any AssignmentExpression / AlwaysBlock that touches `signal`.
        drivers: list[dict] = []
        sinks: list[dict] = []

        def _walk(node):
            if not isinstance(node, (dict, list)):
                return
            if isinstance(node, list):
                for n in node:
                    _walk(n)
                return
            kind = node.get("kind", "")
            blob = json.dumps(node)
            if signal in blob:
                if kind in ("AlwaysBlock", "ContinuousAssign"):
                    drivers.append({"file_line": node.get("loc", ""), "kind": kind})
                elif kind == "ValueExpression":
                    sinks.append({"file_line": node.get("loc", ""), "context": node.get("symbol", "")})
            for v in node.values():
                _walk(v)

        _walk(ast)
        return _trace_payload("slang", drivers, sinks)


# ── pyslang backend (Python bindings to slang) ───────────────────
class PyslangElab(ElabBackend):
    """Direct Python bindings to slang. No subprocess, no JSON round-trip
    — the Compilation object lets us walk the elaborated symbol table
    natively, with file:line locations preserved on every Symbol."""

    name = "pyslang"

    def available(self) -> bool:
        pyslang, import_error = import_pyslang()
        if import_error:
            return False
        # Some pyslang wheels import successfully but expose a different
        # SyntaxTree surface. Treat importable pyslang as serviceable because
        # build_hierarchy/trace_driver can fall back to static RTL parsing
        # instead of making sim_debug show a blank hierarchy.
        return hasattr(pyslang, "Compilation") or self._syntax_tree_cls(pyslang) is not None

    @staticmethod
    def _syntax_tree_cls(pyslang):
        """Return the SyntaxTree class for the installed pyslang binding.

        pyslang has had a few Python packaging shapes. Current wheels expose
        `pyslang.SyntaxTree`; some builds nest generated classes under helper
        namespaces. Treat import-only pyslang as unavailable if no SyntaxTree
        API exists so the caller gets a clear backend-availability error
        instead of an AttributeError from the UI request path.
        """
        return syntax_tree_class(pyslang)

    def _compile(self, sources: list[Path]):
        pyslang, import_error = import_pyslang()
        if import_error:
            return None
        compiled = compile_pyslang_files(sources)
        if compiled.error:
            return ("error", compiled.error)
        return compiled.compilation

    @staticmethod
    def _loc_to_file_line(comp, sm, loc):
        """Convert a pyslang SourceLocation to '<file>:<line>'."""
        try:
            buf = loc.buffer
            line = sm.getLineNumber(loc)
            fname = sm.getFileName(buf)
            return f"{fname}:{line}", fname, int(line)
        except Exception:
            return "", "", 0

    def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
        comp = self._compile(sources)
        if comp is None:
            return {"error": "pyslang not importable", "tree": None}
        if isinstance(comp, tuple) and comp[0] == "error":
            fallback = _static_hierarchy(top, sources, comp[1])
            if fallback.get("tree"):
                return fallback
            return {"error": f"pyslang compile: {comp[1]}", "tree": None}

        try:
            sm = pyslang_source_manager(comp)
            root, root_error = root_symbol(comp)
            if root_error:
                raise RuntimeError(root_error)
        except Exception as e:
            return {"error": f"pyslang root: {e}", "tree": None}

        module_files: dict = {}
        seen_modules: set = set()

        def _resolve_loc(loc):
            """SourceLocation → (filename, line). Returns ('', 0) on failure."""
            try:
                line = sm.getLineNumber(loc)
                fname = sm.getFileName(loc)
                return (fname or "", int(line) if line else 0)
            except Exception:
                return ("", 0)

        def _record_module(symbol):
            """If `symbol` is an Instance, capture its definition's file:line
            (the *body* of the module, which is where the duplicate-name
            wrapper.sv ends up — what we want for click-to-source)."""
            try:
                defn = getattr(symbol, "definition", None)
                if defn is None:
                    return
                mod_name = getattr(defn, "name", "") or ""
                if not mod_name:
                    return
                seen_modules.add(mod_name)
                # Pick the definition with the LARGEST body (more members
                # → real implementation, not a stub). When duplicate
                # `module gpio_pad` exists, we want the one in
                # gpio_pad_wrapper.sv, not gpio_pad.sv.
                body = getattr(symbol, "body", None)
                if body is None:
                    return
                cur_count = sum(1 for _ in body)
                fname, line = _resolve_loc(body.location)
                if not fname:
                    return
                prev = module_files.get(mod_name)
                if prev is None or cur_count > prev.get("_member_count", 0):
                    module_files[mod_name] = {
                        "file": fname,
                        "line": line,
                        "_member_count": cur_count,
                    }
            except Exception:
                pass

        def _walk(symbol, inst_path):
            _record_module(symbol)
            kids = []
            try:
                body = getattr(symbol, "body", None)
                if body is not None:
                    for member in body:
                        mk = str(getattr(member, "kind", ""))
                        if "Instance" in mk and "Body" not in mk:
                            sub_name = getattr(member, "name", "") or "?"
                            sub_path = f"{inst_path}.{sub_name}" if inst_path else sub_name
                            kids.append(_walk(member, sub_path))
            except Exception:
                pass
            try:
                mod_name = symbol.definition.name if hasattr(symbol, "definition") and symbol.definition else (getattr(symbol, "name", "") or "")
            except Exception:
                mod_name = ""
            return {
                "name": inst_path or mod_name or top,
                "module": mod_name,
                "children": kids,
            }

        # Pick the top instance with the most members (handles duplicate
        # module declarations like gpio_pad.sv stub + gpio_pad_wrapper.sv).
        try:
            tops = list(root.topInstances)
            cand = None
            best_count = -1
            for inst in tops:
                # Filter by requested top name when given.
                inst_def_name = inst.definition.name if hasattr(inst, "definition") and inst.definition else inst.name
                if top and inst_def_name != top:
                    continue
                count = sum(1 for _ in inst.body) if hasattr(inst, "body") else 0
                if count > best_count:
                    best_count = count
                    cand = inst
            if cand is None and tops:
                cand = tops[0]
            tree = _walk(cand, top) if cand else None
        except Exception as e:
            return {"error": f"pyslang walk: {e}", "tree": None, "module_files": module_files}

        # Strip internal _member_count before returning.
        for v in module_files.values():
            v.pop("_member_count", None)

        return {
            "backend": "pyslang",
            "tree": tree,
            "modules_found": sorted(seen_modules),
            "module_files": module_files,
        }

    def trace_driver(self, top: str, signal: str, sources: list[Path]) -> dict:
        """Find the driver (LHS of assignment / always-block target) and
        sinks (RHS / read references) of `signal` across the elaborated
        design.

        Strategy — proper structural walker, not naïve text grep:

        1. Recurse from each top InstanceSymbol through its body and
           every nested InstanceSymbol body (handles full hierarchy).
        2. For each scope, classify members:
             - VariableSymbol / NetSymbol / PortSymbol → declaration.
               Capture as `decl` (used as fallback when no driver
               found, like for unconnected ports).
             - ContinuousAssignSymbol / ProceduralBlockSymbol → check
               its `syntax` source against `bare`. If the signal
               appears on the LHS of an assignment within this block,
               record as `driver`. If only on RHS, record as `sink`.
        3. LHS / RHS detection: split syntax at the first `<=` or `=`
           (after stripping `<= ... else <= ...` ambiguity by
           tokenising). Cheap but reliable for synthesizable RTL.

        Returns every distinct driver line found (up to 20) and up to 20
        sinks. `driver` is kept as the first entry for legacy callers.
        """
        comp = self._compile(sources)
        if comp is None:
            return {"error": "pyslang not importable", "driver": None, "drivers": [], "sinks": []}
        if isinstance(comp, tuple) and comp[0] == "error":
            fallback = _static_trace_driver(signal, sources, comp[1])
            if fallback.get("driver") or fallback.get("sinks"):
                return fallback
            return {"error": f"pyslang compile: {comp[1]}", "driver": None, "sinks": []}

        try:
            sm = pyslang_source_manager(comp)
            root, root_error = root_symbol(comp)
            if root_error:
                raise RuntimeError(root_error)
        except Exception as e:
            return {"error": f"pyslang root: {e}", "driver": None, "drivers": [], "sinks": []}

        import re as _re
        bare = signal.rsplit(".", 1)[-1]
        bare = _re.sub(r"\s*\[[^\]]+\]\s*$", "", bare).strip()
        # Word boundary regex so `dir` doesn't match `dir_reg`.
        word_re = _re.compile(r"(?<![A-Za-z0-9_])" + _re.escape(bare) + r"(?![A-Za-z0-9_])")

        decl = None       # declaration site (Port / Var / Net)
        drivers: list = []  # every distinct LHS assignment found
        sinks: list = []

        def _resolve_loc(loc):
            try:
                line = sm.getLineNumber(loc)
                fname = sm.getFileName(loc)
                return (fname or "", int(line) if line else 0)
            except Exception:
                return ("", 0)

        def _file_line(loc):
            f, l = _resolve_loc(loc)
            return f"{f}:{l}" if f else ""

        # Per-line classifier. ProceduralBlock.syntax is the ENTIRE always
        # text, so we scan it line by line (the block's str(syntax) lines map
        # 1:1 onto consecutive source lines from sourceRange.start) and decide,
        # for each line, whether `bare` is WRITTEN (the assignment target →
        # driver) or merely READ (RHS / a condition like `if (sig)` / a port
        # map `.x(sig)` → load). This lands the user on the exact statement
        # instead of the `always`/`assign` keyword, and counts reads that are
        # not on an assignment RHS (which the old splitter missed entirely).
        def _classify_line(line: str):
            """(is_write, is_read) for `bare` on one statement line."""
            line = _re.sub(r"//.*$", "", line)
            if not word_re.search(line):
                return (False, False)
            m_op = _re.search(r"<=(?!=)|(?<![<>=!])=(?!=)", line)
            if m_op is None:
                # No assignment operator → every occurrence is a read
                # (condition, port connection, bare expression).
                return (False, True)
            lhs = line[:m_op.start()]
            rhs = line[m_op.start():]
            # An operator reached while still inside open parens is a
            # comparison inside a condition (`if (a <= b)`), not an assignment.
            if lhs.count("(") - lhs.count(")") > 0:
                return (False, True)
            # The write target is the identifier (with optional bit/part
            # select) immediately to the left of the operator.
            tgt = _re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*$", lhs)
            target = tgt.group(1) if tgt else ""
            lhs_rest = lhs[:tgt.start(1)] if tgt else lhs
            is_write = (target == bare)
            is_read = bool(word_re.search(lhs_rest) or word_re.search(rhs))
            return (is_write, is_read)

        def _visit(scope):
            nonlocal decl
            try:
                iter(scope)
            except TypeError:
                return
            for m in scope:
                try:
                    kind = str(m.kind)
                except Exception:
                    kind = ""

                # 1) Declarations
                if "Variable" in kind or "Net" in kind or "Port" in kind:
                    name = getattr(m, "name", "") or ""
                    if name == bare and decl is None:
                        decl = {"file_line": _file_line(m.location), "kind": kind}
                    continue

                # 2) Assignments / always blocks — line-precise driver/load.
                if "ContinuousAssign" in kind or "ProceduralBlock" in kind:
                    syn = getattr(m, "syntax", None)
                    if syn is None:
                        continue
                    txt = str(syn)
                    if not word_re.search(txt):
                        continue
                    # Map str(syntax) line offsets onto real source lines via
                    # the syntax node's start location (NOT m.location, which
                    # for an always block is the `always` keyword line). A
                    # leading "\n" of trivia makes split()[0] an empty phantom
                    # whose newline inflates the line count, and getLineNumber
                    # reports the line AFTER the newline — so subtract one per
                    # leading newline to re-anchor onto the first real token.
                    try:
                        fname0, base_line = _resolve_loc(syn.sourceRange.start)
                    except Exception:
                        fname0, base_line = _resolve_loc(m.location)
                    base_line -= (len(txt) - len(txt.lstrip("\n")))
                    cond_map = enclosing_conditions(txt)
                    for off, raw_line in enumerate(txt.split("\n")):
                        is_w, is_r = _classify_line(raw_line)
                        if not (is_w or is_r):
                            continue
                        fl = f"{fname0}:{base_line + off}" if fname0 else ""
                        if is_w:
                            conds = cond_map.get(off, [])
                            drivers.append({
                                "file_line": fl, "kind": kind,
                                "condition": " & ".join(conds),
                                "conditions": conds,
                            })
                        if is_r and not is_w:
                            sinks.append({"file_line": fl, "context": bare, "access": "RD"})
                        elif is_r and is_w:
                            sinks.append({"file_line": fl, "context": bare, "access": "RW"})
                    continue

                # 3) Recurse into Instance bodies (cell instantiations)
                if "Instance" in kind and "Body" not in kind:
                    body = getattr(m, "body", None)
                    if body is not None:
                        _visit(body)

        visited_top = False

        def _visit_top_instances(filter_top: bool) -> None:
            nonlocal visited_top
            for inst in root.topInstances:
                # Match by definition name when caller specified `top`.
                if filter_top and top:
                    inst_def = inst.definition.name if hasattr(inst, "definition") and inst.definition else inst.name
                    if inst_def != top:
                        continue
                visited_top = True
                _visit(inst.body)

        try:
            _visit_top_instances(True)
            if top and not visited_top:
                # VCDs and directories often carry the IP name while the
                # actual elaborated top differs. Hierarchy already falls
                # back to the first top instance; tracing should do the
                # same so waveform clicks remain connected to source.
                _visit_top_instances(False)
        except Exception as e:
            return _trace_payload(
                "pyslang",
                drivers,
                sinks,
                error=f"pyslang walk: {e}",
            )

        # Fall back to declaration site as 'driver' when no LHS assign
        # found (e.g. signal is a top-level input port).
        if not drivers and decl is not None:
            drivers.append({"file_line": decl["file_line"], "kind": decl["kind"] + " (declaration)"})

        return _trace_payload("pyslang", drivers, sinks)

    def module_signals(self, top: str, module: str, sources: list[Path]) -> dict:
        """Return every declared signal of `module`: ports (with In/Out/
        InOut direction) and internal nets/variables, with type + bit
        width + file:line. Walks the elaborated symbol table, so generate
        blocks / macros / typedefs are resolved correctly (regex cannot).

        `module` is the DEFINITION name (e.g. clicked in the hierarchy
        tree). We locate the first elaborated instance of that definition
        — `top` only scopes which design root to search."""
        comp = self._compile(sources)
        if comp is None:
            return _static_module_signals(module, sources, "pyslang not importable")
        if isinstance(comp, tuple) and comp[0] == "error":
            fallback = _static_module_signals(module, sources, comp[1])
            if fallback.get("signals"):
                return fallback
            return {"error": f"pyslang compile: {comp[1]}", "module": module, "signals": []}

        try:
            sm = pyslang_source_manager(comp)
            root, root_error = root_symbol(comp)
            if root_error:
                raise RuntimeError(root_error)
        except Exception as e:
            return {"error": f"pyslang root: {e}", "module": module, "signals": []}

        def _resolve_loc(loc):
            try:
                line = sm.getLineNumber(loc)
                fname = sm.getFileName(loc)
                return (fname or "", int(line) if line else 0)
            except Exception:
                return ("", 0)

        def _defn_name(inst):
            try:
                defn = getattr(inst, "definition", None)
                return getattr(defn, "name", "") if defn else (getattr(inst, "name", "") or "")
            except Exception:
                return getattr(inst, "name", "") or ""

        # Locate the instance whose definition matches `module`. Prefer the
        # instance with the most body members (real impl over an empty stub,
        # mirroring build_hierarchy's duplicate-module handling).
        target = {"inst": None, "count": -1, "path": ""}

        def _find(inst, inst_path):
            try:
                if _defn_name(inst) == module:
                    count = sum(1 for _ in inst.body) if hasattr(inst, "body") else 0
                    if count > target["count"]:
                        target.update({"inst": inst, "count": count, "path": inst_path})
                body = getattr(inst, "body", None)
                if body is not None:
                    for member in body:
                        mk = str(getattr(member, "kind", ""))
                        if "Instance" in mk and "Body" not in mk:
                            sub = getattr(member, "name", "") or "?"
                            _find(member, f"{inst_path}.{sub}" if inst_path else sub)
            except Exception:
                pass

        try:
            tops = list(root.topInstances)
            roots = [i for i in tops if (not top or _defn_name(i) == top)] or tops
            for inst in roots:
                _find(inst, _defn_name(inst))
            # No instance of `module` found under the chosen top → search all.
            if target["inst"] is None and module:
                for inst in tops:
                    _find(inst, _defn_name(inst))
        except Exception as e:
            return {"error": f"pyslang walk: {e}", "module": module, "signals": []}

        inst = target["inst"]
        if inst is None:
            return {"error": f"module '{module}' not found in elaborated design",
                    "module": module, "signals": []}

        ports: list[dict] = []
        internals: list[dict] = []
        port_names: set[str] = set()
        try:
            for m in inst.body:
                kind = str(getattr(m, "kind", ""))
                name = getattr(m, "name", "") or ""
                if not name:
                    continue
                if kind.endswith("Port") and "Interface" not in kind:
                    fname, line = _resolve_loc(getattr(m, "location", None))
                    type_text = str(getattr(m, "type", "") or "")
                    port_names.add(name)
                    ports.append({
                        "name": name,
                        "direction": _direction_label(getattr(m, "direction", "")),
                        "kind": "port",
                        "type": type_text,
                        "width": _width_from_type(type_text),
                        "file": fname, "line": line,
                        "file_line": f"{fname}:{line}" if fname else "",
                    })
                elif kind.endswith("Variable") or kind.endswith("Net"):
                    fname, line = _resolve_loc(getattr(m, "location", None))
                    type_text = str(getattr(m, "type", "") or "")
                    internals.append({
                        "name": name,
                        "direction": "internal",
                        "kind": "net" if kind.endswith("Net") else "var",
                        "type": type_text,
                        "width": _width_from_type(type_text),
                        "file": fname, "line": line,
                        "file_line": f"{fname}:{line}" if fname else "",
                    })
        except Exception as e:
            return {"error": f"pyslang members: {e}", "module": module, "signals": ports}

        # Ports re-appear as backing Variables (verified: every port name is
        # also a VariableSymbol). Drop those duplicates so a port is shown
        # once, as a port — not twice.
        seen_internal: set[str] = set()
        deduped_internal: list[dict] = []
        for s in internals:
            if s["name"] in port_names or s["name"] in seen_internal:
                continue
            seen_internal.add(s["name"])
            deduped_internal.append(s)

        signals = ports + deduped_internal
        return {
            "backend": "pyslang",
            "module": module,
            "instance_path": target["path"],
            "signals": signals,
            "counts": _signal_counts(signals),
        }


def _compact_backend_result(name: str, result: dict) -> dict:
    return {
        "backend": name,
        "ok": bool(result.get("tree") or result.get("driver") or result.get("drivers") or result.get("sinks")),
        "error": result.get("error") or "",
        "warning": result.get("warning") or "",
        "modules_found": result.get("modules_found") or [],
        "driver": result.get("driver"),
        "driver_count": result.get("driver_count", len(result.get("drivers") or ([] if not result.get("driver") else [result.get("driver")]))),
        "sink_count": result.get("sink_count", len(result.get("sinks") or [])),
    }


def _hierarchy_crosscheck(results: dict[str, dict]) -> dict:
    def _real_modules(res: dict) -> set[str]:
        return {
            str(name)
            for name in (res.get("modules_found") or [])
            if str(name) and not str(name).startswith(("@", "$"))
        }

    module_sets = {
        name: _real_modules(res)
        for name, res in results.items()
        if res.get("tree")
    }
    if len(module_sets) < 2:
        return {"status": "single", "module_delta": {}}
    all_modules = set().union(*module_sets.values())
    return {
        "status": "match" if all(mods == all_modules for mods in module_sets.values()) else "mismatch",
        "module_delta": {
            name: sorted(all_modules - mods)
            for name, mods in module_sets.items()
            if all_modules - mods
        },
    }


def _merge_module_files(primary: dict, secondary: dict) -> dict:
    merged = dict(secondary or {})
    merged.update(primary or {})
    return merged


class DualElab(ElabBackend):
    """Run pyslang and Verilator side-by-side.

    pyslang remains the primary source/trace backend because it preserves
    rich file:line metadata in-process. Verilator runs as an independent
    structural cross-check. If pyslang cannot produce a usable result, the
    UI still gets Verilator's hierarchy instead of going blank.
    """

    name = "dual"
    order = ("pyslang", "verilator")

    def available(self) -> bool:
        return any(_BACKENDS[name].available() for name in self.order)

    def _run_each(self, method: str, *args) -> dict[str, dict]:
        results: dict[str, dict] = {}
        for name in self.order:
            backend = _BACKENDS[name]
            if not backend.available():
                results[name] = {"backend": name, "error": f"{name} not available"}
                continue
            try:
                result = getattr(backend, method)(*args)
            except Exception as exc:
                result = {"backend": name, "error": str(exc)}
            result = dict(result or {})
            result["backend"] = name
            results[name] = result
        return results

    def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
        results = self._run_each("build_hierarchy", top, sources)
        primary_name = next((name for name in self.order if results.get(name, {}).get("tree")), "")
        if not primary_name:
            return {
                "backend": "pyslang+verilator",
                "primary_backend": "",
                "tree": None,
                "error": "; ".join(
                    f"{name}: {res.get('error') or 'no tree'}"
                    for name, res in results.items()
                ),
                "backend_results": [_compact_backend_result(name, res) for name, res in results.items()],
            }
        primary = results[primary_name]
        secondary_name = next((name for name in self.order if name != primary_name), "")
        secondary = results.get(secondary_name, {})
        return {
            **primary,
            "backend": "pyslang+verilator",
            "primary_backend": primary_name,
            "module_files": _merge_module_files(primary.get("module_files") or {}, secondary.get("module_files") or {}),
            "backend_results": [_compact_backend_result(name, res) for name, res in results.items()],
            "crosscheck": _hierarchy_crosscheck(results),
        }

    def trace_driver(self, top: str, signal: str, sources: list[Path]) -> dict:
        results = self._run_each("trace_driver", top, signal, sources)
        primary_name = next(
            (
                name for name in self.order
                if results.get(name, {}).get("driver") or results.get(name, {}).get("drivers") or results.get(name, {}).get("sinks")
            ),
            "",
        )
        if not primary_name:
            return {
                "backend": "pyslang+verilator",
                "primary_backend": "",
                "driver": None,
                "sinks": [],
                "error": "; ".join(
                    f"{name}: {res.get('error') or 'no trace'}"
                    for name, res in results.items()
                ),
                "backend_results": [_compact_backend_result(name, res) for name, res in results.items()],
            }
        primary = results[primary_name]
        return {
            **primary,
            "backend": "pyslang+verilator",
            "primary_backend": primary_name,
            "backend_results": [_compact_backend_result(name, res) for name, res in results.items()],
        }


# ── Public API ───────────────────────────────────────────────────
_BACKENDS = {
    "dual":      DualElab(),
    "pyslang":   PyslangElab(),
    "verilator": VerilatorElab(),
    "slang":     SlangElab(),
}

_BACKEND_ALIASES = {
    "both": "dual",
    "all": "dual",
    "pyslang+verilator": "dual",
    "pyslang,verilator": "dual",
    "pyslang-verilator": "dual",
}


def _config_default_backend() -> str:
    """Resolve the default elab backend from .config / env. Priority:
       1. SIM_DEBUG_ELAB_BACKEND env var
       2. .config attribute SIM_DEBUG_ELAB_BACKEND (loaded by config.py)
       3. hardcoded fallback 'dual' (pyslang + Verilator)
    """
    import os
    env = os.environ.get("SIM_DEBUG_ELAB_BACKEND", "").strip().lower()
    env = _BACKEND_ALIASES.get(env, env)
    if env in _BACKENDS:
        return env
    try:
        import config as _cfg  # type: ignore
        v = getattr(_cfg, "SIM_DEBUG_ELAB_BACKEND", None)
        v = _BACKEND_ALIASES.get(str(v).lower(), str(v).lower()) if v else ""
        if v in _BACKENDS:
            return v
    except Exception:
        pass
    return "dual"


def get_backend(prefer: str = "") -> ElabBackend:
    """Return the requested backend. If `prefer` empty, use .config /
    env default. No silent fallback — if the requested elaborator is
    missing, raise ValueError so the caller can show an honest error
    rather than guessing with another backend behind the user's back."""
    prefer = (prefer or _config_default_backend()).lower()
    prefer = _BACKEND_ALIASES.get(prefer, prefer)
    if prefer not in _BACKENDS:
        raise ValueError(f"unknown elab backend '{prefer}'. Choose from: {sorted(_BACKENDS.keys())}")
    be = _BACKENDS[prefer]
    if not be.available():
        installed = [n for n, b in _BACKENDS.items() if b.available()]
        hint = f"installed: {installed}" if installed else "none installed"
        raise ValueError(
            f"requested backend '{prefer}' not available. {hint}. "
            f"Install with `pip install pyslang` / `brew install verilator` / build slang. "
            f"Override via SIM_DEBUG_ELAB_BACKEND env or .config SIM_DEBUG_ELAB_BACKEND="
        )
    return be


def status() -> dict:
    return {name: be.available() for name, be in _BACKENDS.items()}


def build_hierarchy_cached(prefer: str, top: str, sources: list[Path]) -> dict:
    be = get_backend(prefer)
    key = _cache_key(be.name, top, sources)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    res = be.build_hierarchy(top, sources)
    res.setdefault("backend", be.name)
    _cache_put(key, res)
    return res


def trace_driver_cached(prefer: str, top: str, signal: str, sources: list[Path]) -> dict:
    be = get_backend(prefer)
    key = _cache_key(be.name + ":trace:" + top + ":" + signal, top, sources)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    res = be.trace_driver(top, signal, sources)
    res.setdefault("backend", be.name)
    _cache_put(key, res)
    return res


def module_signals_cached(prefer: str, top: str, module: str, sources: list[Path]) -> dict:
    """Per-module signal list (ports + internal nets/vars). Always routed
    through pyslang — it is the only backend that exposes the elaborated
    symbol table with directions; `prefer` is accepted for call-site
    symmetry with the other cached helpers but does not switch backends.
    Falls back to the static RTL scan when pyslang cannot be imported."""
    be = _BACKENDS["pyslang"]
    key = _cache_key("pyslang:signals:" + top + ":" + module, top, sources)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    if be.available():
        res = be.module_signals(top, module, sources)
    else:
        res = _static_module_signals(module, sources, "pyslang backend unavailable")
    res.setdefault("backend", "pyslang")
    _cache_put(key, res)
    return res
