"""Compatibility helpers for pyslang Python binding drift.

The pyslang wheel has changed shape across builds: some expose
``pyslang.SyntaxTree`` directly, some expose generated classes in nested
namespaces, and diagnostic formatting methods are not stable. Keep those
differences behind this module so UI/workflow code can degrade cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
from pathlib import Path
from typing import Any, Iterable, Optional


@dataclass
class PyslangCompileResult:
    pyslang: Any = None
    compilation: Any = None
    trees: list[Any] = field(default_factory=list)
    source_manager: Any = None
    diagnostics: list[Any] = field(default_factory=list)
    error: str = ""


def import_pyslang() -> tuple[Any, str]:
    """Import pyslang and return ``(module, error)``.

    Import failures are returned as strings instead of raised so callers
    can fall back to regex/static analysis without blanking the UI.
    """
    try:
        return importlib.import_module("pyslang"), ""
    except Exception as exc:
        return None, f"pyslang import failed: {exc}"


def module_location(pyslang: Any) -> str:
    return str(getattr(pyslang, "__file__", "<unknown>"))


def syntax_tree_class(pyslang: Any) -> Any:
    direct = getattr(pyslang, "SyntaxTree", None)
    if direct is not None:
        return direct
    for ns_name in ("syntax", "parsing", "ast"):
        ns = getattr(pyslang, ns_name, None)
        candidate = getattr(ns, "SyntaxTree", None) if ns is not None else None
        if candidate is not None:
            return candidate
    return None


def _read_text(path: Optional[Path]) -> str:
    if path is None:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def make_syntax_tree(
    pyslang: Any,
    *,
    path: str | Path | None = None,
    text: str | None = None,
) -> tuple[Any, str]:
    """Create a SyntaxTree using whichever constructor exists."""
    tree_cls = syntax_tree_class(pyslang)
    if tree_cls is None:
        return None, (
            "installed pyslang package does not expose a SyntaxTree API "
            f"(module={module_location(pyslang)})"
        )

    path_obj = Path(path) if path is not None else None
    path_str = str(path_obj) if path_obj is not None else "<memory>"

    if path_obj is not None and hasattr(tree_cls, "fromFile"):
        try:
            return tree_cls.fromFile(path_str), ""
        except TypeError:
            pass
        except Exception as exc:
            if text is None:
                try:
                    text = _read_text(path_obj)
                except Exception:
                    return None, f"pyslang SyntaxTree.fromFile failed for {path_str}: {exc}"

    if text is None:
        text = _read_text(path_obj)

    from_text = getattr(tree_cls, "fromText", None)
    if from_text is None:
        return None, "installed pyslang SyntaxTree lacks fromFile/fromText"

    errors = []
    for args in ((text, path_str), (text,)):
        try:
            return from_text(*args), ""
        except TypeError as exc:
            errors.append(str(exc))
        except Exception as exc:
            return None, f"pyslang SyntaxTree.fromText failed for {path_str}: {exc}"
    return None, "pyslang SyntaxTree.fromText signature mismatch: " + " | ".join(errors)


def make_compilation(pyslang: Any) -> tuple[Any, str]:
    comp_cls = getattr(pyslang, "Compilation", None)
    if comp_cls is None:
        return None, (
            "installed pyslang package does not expose a Compilation API "
            f"(module={module_location(pyslang)})"
        )

    candidates = [()]
    bag_cls = getattr(pyslang, "Bag", None)
    if bag_cls is not None:
        try:
            candidates.append((bag_cls(),))
        except Exception:
            pass

    errors = []
    for args in candidates:
        try:
            return comp_cls(*args), ""
        except TypeError as exc:
            errors.append(str(exc))
        except Exception as exc:
            return None, f"pyslang Compilation creation failed: {exc}"
    return None, "pyslang Compilation signature mismatch: " + " | ".join(errors)


def add_syntax_tree(compilation: Any, tree: Any) -> str:
    add_one = getattr(compilation, "addSyntaxTree", None)
    if add_one is not None:
        try:
            add_one(tree)
            return ""
        except TypeError:
            pass
        except Exception as exc:
            return f"pyslang addSyntaxTree failed: {exc}"

    add_many = getattr(compilation, "addSyntaxTrees", None)
    if add_many is not None:
        try:
            add_many([tree])
            return ""
        except Exception as exc:
            return f"pyslang addSyntaxTrees failed: {exc}"

    return "installed pyslang Compilation lacks addSyntaxTree/addSyntaxTrees"


def root_symbol(compilation: Any) -> tuple[Any, str]:
    for name in ("getRoot", "getRootSymbol"):
        method = getattr(compilation, name, None)
        if method is not None:
            try:
                return method(), ""
            except Exception as exc:
                return None, f"pyslang {name} failed: {exc}"
    root = getattr(compilation, "root", None)
    if root is not None:
        return root, ""
    return None, "installed pyslang Compilation lacks getRoot/getRootSymbol"


def top_instances(compilation: Any) -> list[Any]:
    root, _ = root_symbol(compilation)
    if root is None:
        return []
    try:
        return list(getattr(root, "topInstances", []) or [])
    except Exception:
        return []


def collect_diagnostics(compilation: Any, trees: Iterable[Any] = ()) -> list[Any]:
    for name in ("getAllDiagnostics", "getSemanticDiagnostics", "getParseDiagnostics"):
        method = getattr(compilation, name, None)
        if method is None:
            continue
        try:
            return list(method() or [])
        except Exception:
            pass

    diags: list[Any] = []
    for tree in trees:
        try:
            diags.extend(list(getattr(tree, "diagnostics", []) or []))
        except Exception:
            pass
    return diags


def source_manager(compilation: Any = None, trees: Iterable[Any] = ()) -> Any:
    sm = getattr(compilation, "sourceManager", None) if compilation is not None else None
    if sm is not None:
        return sm
    for tree in trees:
        sm = getattr(tree, "sourceManager", None)
        if sm is not None:
            return sm
    return None


def diagnostic_is_error(diag: Any) -> bool:
    is_error = getattr(diag, "isError", None)
    if callable(is_error):
        try:
            return bool(is_error())
        except Exception:
            pass
    severity = str(getattr(diag, "severity", "") or getattr(diag, "level", ""))
    return "error" in severity.lower()


def diagnostic_line(diag: Any, sm: Any) -> int:
    loc = getattr(diag, "location", None)
    if loc is None:
        return 0
    if sm is not None:
        get_line = getattr(sm, "getLineNumber", None)
        if get_line is not None:
            try:
                return int(get_line(loc) or 0)
            except Exception:
                pass
    for attr in ("line", "lineNumber"):
        val = getattr(loc, attr, None)
        if val is not None:
            try:
                return int(val)
            except Exception:
                pass
    return 0


def diagnostic_message(pyslang: Any, diag: Any, sm: Any = None) -> str:
    engine_cls = getattr(pyslang, "DiagnosticEngine", None)
    if engine_cls is not None:
        for args in ((sm,), ()):
            try:
                engine = engine_cls(*args)
            except TypeError:
                continue
            except Exception:
                break
            for method_name in ("formatMessage", "formatDiagnostic", "getMessage"):
                method = getattr(engine, method_name, None)
                if method is None:
                    continue
                try:
                    msg = method(diag)
                    if msg:
                        return str(msg)
                except Exception:
                    pass
    msg = getattr(diag, "message", None)
    if msg:
        return str(msg)
    return str(diag)


def compile_files(files: Iterable[str | Path]) -> PyslangCompileResult:
    pyslang, import_error = import_pyslang()
    if import_error:
        return PyslangCompileResult(error=import_error)

    comp, comp_error = make_compilation(pyslang)
    if comp_error:
        return PyslangCompileResult(pyslang=pyslang, error=comp_error)

    trees = []
    for file_path in files:
        path = Path(file_path)
        tree, tree_error = make_syntax_tree(pyslang, path=path)
        if tree_error:
            return PyslangCompileResult(
                pyslang=pyslang,
                compilation=comp,
                trees=trees,
                source_manager=source_manager(comp, trees),
                error=tree_error,
            )
        err = add_syntax_tree(comp, tree)
        if err:
            return PyslangCompileResult(
                pyslang=pyslang,
                compilation=comp,
                trees=trees,
                source_manager=source_manager(comp, trees),
                error=err,
            )
        trees.append(tree)

    sm = source_manager(comp, trees)
    root, root_error = root_symbol(comp)
    if root_error:
        return PyslangCompileResult(
            pyslang=pyslang,
            compilation=comp,
            trees=trees,
            source_manager=sm,
            diagnostics=collect_diagnostics(comp, trees),
            error=root_error,
        )

    return PyslangCompileResult(
        pyslang=pyslang,
        compilation=comp,
        trees=trees,
        source_manager=sm,
        diagnostics=collect_diagnostics(comp, trees),
        error="",
    )


def can_compile_probe() -> tuple[bool, str]:
    pyslang, import_error = import_pyslang()
    if import_error:
        return False, import_error
    comp, comp_error = make_compilation(pyslang)
    if comp_error:
        return False, comp_error
    tree, tree_error = make_syntax_tree(
        pyslang,
        text="module __pyslang_probe; endmodule\n",
        path="__pyslang_probe.sv",
    )
    if tree_error:
        return False, tree_error
    add_error = add_syntax_tree(comp, tree)
    if add_error:
        return False, add_error
    _, root_error = root_symbol(comp)
    if root_error:
        return False, root_error
    return True, ""
