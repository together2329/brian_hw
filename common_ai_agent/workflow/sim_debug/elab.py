"""src/sim_debug_elab.py — SystemVerilog elaboration backends for
sim_debug workspace.

Strategy pattern: caller asks for a backend ("verilator" or "slang"); we
dispatch to the matching implementation. Both shell out to a real SV
frontend so hierarchy + trace data is 100% accurate (regex extraction
broke on generate / macro / bind).

Public API:
  - get_backend(prefer: str) -> ElabBackend
  - ElabBackend.available() -> bool
  - ElabBackend.build_hierarchy(top, sources) -> dict
  - ElabBackend.trace_driver(scope, signal, sources) -> dict
  - status() -> {verilator: bool, slang: bool}

Cache: results memoize on (backend, top, sources hash, source mtimes)
to avoid re-elab on every UI click. Cache lives at
PROJECT_ROOT/.session/elab_cache/<key>.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional


def _project_root() -> Path:
    return Path(os.getcwd()).resolve()


def _cache_dir() -> Path:
    d = _project_root() / ".session" / "elab_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_key(backend: str, top: str, sources: list[Path]) -> str:
    h = hashlib.sha1()
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
        return json.loads(p.read_text())
    except Exception:
        return None


def _cache_put(key: str, data: dict) -> None:
    try:
        (_cache_dir() / f"{key}.json").write_text(json.dumps(data))
    except OSError:
        pass


# ── Base ─────────────────────────────────────────────────────────
class ElabBackend:
    name = "abstract"

    def available(self) -> bool:
        raise NotImplementedError

    def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
        raise NotImplementedError

    def trace_driver(self, scope: str, signal: str, sources: list[Path]) -> dict:
        raise NotImplementedError


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
                cmd, capture_output=True, text=True, timeout=60,
                cwd=str(_project_root()),
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if not out_json.is_file():
            return None
        try:
            return json.loads(out_json.read_text())
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
            meta = json.loads(meta_path.read_text())
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
            return {"error": "verilator failed (top=" + top + ")", "driver": None, "sinks": []}

        # Resolve loc → "<file>:<line>" using the meta.json file_map.
        out_dir = _cache_dir() / f"verilator_{top}"
        meta_path = out_dir / f"V{top}.tree.meta.json"
        file_map = {}
        try:
            file_map = (json.loads(meta_path.read_text()) or {}).get("files", {}) or {}
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

        driver = None
        sinks: list[dict] = []

        def _walk(node):
            nonlocal driver
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
                if bare in blob and driver is None:
                    driver = {"file_line": _human_loc(node.get("loc", "")), "kind": t}
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
        return {"backend": "verilator", "driver": driver, "sinks": sinks[:20]}


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
                cmd, capture_output=True, text=True, timeout=60,
                cwd=str(_project_root()),
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if not out.is_file():
            return None
        try:
            return json.loads(out.read_text())
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
            return {"error": "slang failed (top=" + top + ")", "driver": None, "sinks": []}

        # Slang's AST has Symbol nodes with `loc` (file:line). Walk and
        # collect any AssignmentExpression / AlwaysBlock that touches `signal`.
        driver = None
        sinks: list[dict] = []

        def _walk(node):
            nonlocal driver
            if not isinstance(node, (dict, list)):
                return
            if isinstance(node, list):
                for n in node:
                    _walk(n)
                return
            kind = node.get("kind", "")
            blob = json.dumps(node)
            if signal in blob:
                if kind in ("AlwaysBlock", "ContinuousAssign") and driver is None:
                    driver = {"file_line": node.get("loc", ""), "kind": kind}
                elif kind == "ValueExpression":
                    sinks.append({"file_line": node.get("loc", ""), "context": node.get("symbol", "")})
            for v in node.values():
                _walk(v)

        _walk(ast)
        return {"backend": "slang", "driver": driver, "sinks": sinks[:20]}


# ── pyslang backend (Python bindings to slang) ───────────────────
class PyslangElab(ElabBackend):
    """Direct Python bindings to slang. No subprocess, no JSON round-trip
    — the Compilation object lets us walk the elaborated symbol table
    natively, with file:line locations preserved on every Symbol."""

    name = "pyslang"

    def available(self) -> bool:
        try:
            import pyslang  # noqa: F401
            return True
        except Exception:
            return False

    def _compile(self, sources: list[Path]):
        try:
            import pyslang
        except ImportError:
            return None
        try:
            tree = pyslang.SyntaxTree
            comp = pyslang.Compilation()
            for s in sources:
                t = pyslang.SyntaxTree.fromFile(str(s))
                comp.addSyntaxTree(t)
            comp.getRoot()  # force elaboration
            return comp
        except Exception as e:
            return ("error", str(e))

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
            return {"error": f"pyslang compile: {comp[1]}", "tree": None}

        try:
            import pyslang
            sm = comp.sourceManager
            root = comp.getRoot()
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

        Returns the FIRST driver found (closest to top) and up to 20
        sinks. Multiple-driver designs would need merging — out of
        scope for v1.
        """
        comp = self._compile(sources)
        if comp is None:
            return {"error": "pyslang not importable", "driver": None, "sinks": []}
        if isinstance(comp, tuple) and comp[0] == "error":
            return {"error": f"pyslang compile: {comp[1]}", "driver": None, "sinks": []}

        try:
            sm = comp.sourceManager
            root = comp.getRoot()
        except Exception as e:
            return {"error": f"pyslang root: {e}", "driver": None, "sinks": []}

        bare = signal.rsplit(".", 1)[-1]
        # Word boundary regex so `dir` doesn't match `dir_reg`.
        import re as _re
        word_re = _re.compile(r"(?<![A-Za-z0-9_])" + _re.escape(bare) + r"(?![A-Za-z0-9_])")

        decl = None       # declaration site (Port / Var / Net)
        driver = None     # first LHS assignment found
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

        # Line-level statement extractor. ProceduralBlock.syntax gives
        # the ENTIRE always_ff text — too coarse for LHS/RHS. We split
        # into individual *assignment statements* (terminated by `;`)
        # and classify each one on its own.
        def _extract_assigns(syntax_text):
            """Return list of {'lhs_text','rhs_text'} per assignment."""
            if not syntax_text:
                return []
            txt = _re.sub(r"//.*?$", "", syntax_text, flags=_re.MULTILINE)
            txt = _re.sub(r"/\*.*?\*/", "", txt, flags=_re.DOTALL)
            # Drop sensitivity list `@(...)` so ports there aren't counted as LHS.
            txt = _re.sub(r"@\s*\([^)]*\)", "", txt)
            # Each statement ends with `;`. Split, keep substantive ones.
            stmts = [s.strip() for s in txt.split(";") if s.strip()]
            out = []
            for s in stmts:
                # Skip control flow keywords without assignment.
                if not _re.search(r"<=|(?<![<>!=])=(?!=)", s):
                    continue
                # Find the assignment operator (first `<=` or first standalone `=`)
                m_nba = _re.search(r"<=", s)
                m_ba  = _re.search(r"(?<![<>!=])=(?!=)", s)
                pos = None; op = None
                if m_nba and (not m_ba or m_nba.start() <= m_ba.start()):
                    pos, op = m_nba.start(), "<="
                elif m_ba:
                    pos, op = m_ba.start(), "="
                if pos is None:
                    continue
                lhs = s[:pos].strip()
                rhs = s[pos + len(op):].strip()
                # Drop `if (...)` prefix from LHS for proper analysis.
                lhs = _re.sub(r"^.*\b(if|else|begin|end|case|default|for|while)\b\s*", "", lhs, count=1)
                lhs = _re.sub(r"^.*\)", "", lhs).strip() if lhs.startswith("if") or "(" in lhs else lhs
                out.append({"lhs": lhs, "rhs": rhs})
            return out

        def _visit(scope):
            nonlocal decl, driver
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

                # 2) Assignments / always blocks — inspect syntax statement-by-statement
                if "ContinuousAssign" in kind or "ProceduralBlock" in kind:
                    syn = getattr(m, "syntax", None)
                    if syn is None:
                        continue
                    txt = str(syn)
                    if not word_re.search(txt):
                        continue
                    fl = _file_line(m.location)
                    is_lhs = False
                    is_rhs = False
                    for asn in _extract_assigns(txt):
                        if word_re.search(asn["lhs"]):
                            is_lhs = True
                        if word_re.search(asn["rhs"]):
                            is_rhs = True
                    if is_lhs and driver is None:
                        driver = {"file_line": fl, "kind": kind}
                    if is_rhs and not is_lhs:
                        sinks.append({"file_line": fl, "context": bare, "access": "RD"})
                    elif is_rhs and is_lhs:
                        sinks.append({"file_line": fl, "context": bare, "access": "RW"})
                    continue

                # 3) Recurse into Instance bodies (cell instantiations)
                if "Instance" in kind and "Body" not in kind:
                    body = getattr(m, "body", None)
                    if body is not None:
                        _visit(body)

        try:
            for inst in root.topInstances:
                # Match by definition name when caller specified `top`.
                if top:
                    inst_def = inst.definition.name if hasattr(inst, "definition") and inst.definition else inst.name
                    if inst_def != top:
                        continue
                _visit(inst.body)
        except Exception as e:
            return {"error": f"pyslang walk: {e}", "driver": driver, "sinks": sinks[:20]}

        # Fall back to declaration site as 'driver' when no LHS assign
        # found (e.g. signal is a top-level input port).
        if driver is None and decl is not None:
            driver = {"file_line": decl["file_line"], "kind": decl["kind"] + " (declaration)"}

        return {
            "backend": "pyslang",
            "driver": driver,
            "sinks": sinks[:20],
            "sink_count": len(sinks),
        }


# ── Public API ───────────────────────────────────────────────────
_BACKENDS = {
    "pyslang":   PyslangElab(),
    "verilator": VerilatorElab(),
    "slang":     SlangElab(),
}


def _config_default_backend() -> str:
    """Resolve the default elab backend from .config / env. Priority:
       1. SIM_DEBUG_ELAB_BACKEND env var
       2. .config attribute SIM_DEBUG_ELAB_BACKEND (loaded by config.py)
       3. hardcoded fallback 'pyslang'
    """
    import os
    env = os.environ.get("SIM_DEBUG_ELAB_BACKEND", "").strip().lower()
    if env in _BACKENDS:
        return env
    try:
        import config as _cfg  # type: ignore
        v = getattr(_cfg, "SIM_DEBUG_ELAB_BACKEND", None)
        if v and str(v).lower() in _BACKENDS:
            return str(v).lower()
    except Exception:
        pass
    return "pyslang"


def get_backend(prefer: str = "") -> ElabBackend:
    """Return the requested backend. If `prefer` empty, use .config /
    env default. No silent fallback — if the requested elaborator is
    missing, raise ValueError so the caller can show an honest error
    rather than guessing with another backend behind the user's back."""
    prefer = (prefer or _config_default_backend()).lower()
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
    res["backend"] = be.name
    _cache_put(key, res)
    return res


def trace_driver_cached(prefer: str, top: str, signal: str, sources: list[Path]) -> dict:
    be = get_backend(prefer)
    key = _cache_key(be.name + ":trace:" + top + ":" + signal, top, sources)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    res = be.trace_driver(top, signal, sources)
    res["backend"] = be.name
    _cache_put(key, res)
    return res
