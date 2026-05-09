"""Fold-range extractor used by ATLAS PreviewPane.

Given a SystemVerilog or YAML source file, return a list of foldable
line ranges plus a kind/label for each. The frontend wraps each range
in a ``<details>`` block.

The two extractors here are deliberately small and forgiving:
- pyslang is best-effort. Macro-only / preprocessor-heavy files may
  parse partially; we return whatever ranges we can.
- PyYAML's ``compose`` walks the document as a tree of nodes, each of
  which carries ``start_mark.line`` / ``end_mark.line`` (0-based). We
  emit 1-based line numbers to match the frontend's gutter.

Both extractors short-circuit on empty input and never raise — callers
can treat the empty list as "no folds, render plainly".
"""

from __future__ import annotations

from typing import Any, List, Dict


def _yaml_label_for_seq_item(item) -> str:
    """Pick a human-friendly label for a sequence's mapping item.

    Prefers ``name``/``id``/``goal_id``/``scenario_id`` keys when
    present; otherwise returns an empty label so the caller can fall
    back to a positional ``[i]``.
    """
    try:
        for key, val in item.value:
            k = getattr(key, "value", None)
            if k in ("name", "id", "goal_id", "scenario_id"):
                vstr = getattr(val, "value", "")
                return f"{k}: {vstr}"
    except Exception:
        pass
    return ""


def extract_yaml_folds(text: str) -> List[Dict[str, Any]]:
    """Return all multi-line Mapping/Sequence/Scalar nodes.

    Threshold: only emit a fold when the node spans 2+ lines
    (``end_line - start_line >= 1``). Single-line scalars are skipped
    so the UI doesn't drown in micro-folds.
    """
    if not text or not text.strip():
        return []
    try:
        import yaml  # type: ignore
    except Exception:
        return []
    try:
        node = yaml.compose(text)
    except Exception:
        return []
    if node is None:
        return []

    ranges: List[Dict[str, Any]] = []

    def add(kind: str, label: str, start: int, end: int) -> None:
        if end - start >= 1:
            ranges.append({
                "kind": kind,
                "label": label,
                "line_start": start + 1,
                "line_end": end + 1,
            })

    def walk(n, path: str = "") -> None:
        try:
            import yaml as _yaml  # type: ignore
        except Exception:
            return
        if isinstance(n, _yaml.MappingNode):
            for key_node, val_node in n.value:
                key_str = getattr(key_node, "value", str(key_node))
                if isinstance(val_node, (_yaml.MappingNode, _yaml.SequenceNode)):
                    s = key_node.start_mark.line
                    e = val_node.end_mark.line
                    kind = "section" if not path else "sub-section"
                    label = f"{path}{key_str}" if path else key_str
                    add(kind, label, s, e)
                    walk(val_node, path=f"{path}{key_str}." if path else f"{key_str}.")
                elif isinstance(val_node, _yaml.ScalarNode):
                    s = key_node.start_mark.line
                    e = val_node.end_mark.line
                    if e - s >= 1:
                        label = f"{path}{key_str}" if path else key_str
                        add("scalar", label, s, e)
        elif isinstance(n, _yaml.SequenceNode):
            for i, item in enumerate(n.value):
                if isinstance(item, _yaml.MappingNode):
                    lbl = _yaml_label_for_seq_item(item) or f"[{i}]"
                    s = item.start_mark.line
                    e = item.end_mark.line
                    label = f"{path}{lbl}" if path else lbl
                    add("item", label, s, e)
                    walk(item, path=f"{path}{lbl}/" if path else f"{lbl}/")
                elif isinstance(item, _yaml.SequenceNode):
                    s = item.start_mark.line
                    e = item.end_mark.line
                    label = f"{path}[{i}]"
                    add("item", label, s, e)
                    walk(item, path=f"{path}[{i}]/")

    walk(node)
    ranges.sort(key=lambda r: (r["line_start"], -r["line_end"]))
    return ranges


_VERILOG_KIND_LABEL = {
    "SyntaxKind.ModuleDeclaration":   "module",
    "SyntaxKind.AlwaysFFBlock":       "always_ff",
    "SyntaxKind.AlwaysCombBlock":     "always_comb",
    "SyntaxKind.AlwaysBlock":         "always",
    "SyntaxKind.AlwaysLatchBlock":    "always_latch",
    "SyntaxKind.InitialBlock":        "initial",
    "SyntaxKind.FunctionDeclaration": "function",
    "SyntaxKind.TaskDeclaration":     "task",
    "SyntaxKind.LoopGenerate":        "generate-loop",
    "SyntaxKind.IfGenerate":          "generate-if",
    "SyntaxKind.CaseStatement":       "case",
}


def extract_verilog_folds(text: str) -> List[Dict[str, Any]]:
    """Return foldable ranges for a SystemVerilog/Verilog source.

    Threshold: only emit a fold when the construct spans 3+ lines.
    Anything shorter (e.g. ``assign foo = bar;``) is too small to be
    worth a UI control. The extractor is best-effort; preprocessor
    pragmas that confuse pyslang produce a partial AST and we keep
    whatever ranges did parse.
    """
    if not text or not text.strip():
        return []
    try:
        import pyslang  # type: ignore
    except Exception:
        return []
    try:
        tree = pyslang.SyntaxTree.fromText(text)
    except Exception:
        return []
    if tree is None:
        return []
    src_mgr = tree.sourceManager
    if src_mgr is None:
        return []

    def line_of(token):
        try:
            return src_mgr.getLineNumber(token.location)
        except Exception:
            return None

    ranges: List[Dict[str, Any]] = []

    def visit(node) -> None:
        kind_name = str(getattr(node, "kind", ""))
        if kind_name not in _VERILOG_KIND_LABEL:
            return
        kind = _VERILOG_KIND_LABEL[kind_name]
        try:
            start = line_of(node.getFirstToken())
            end = line_of(node.getLastToken())
        except Exception:
            return
        if start is None or end is None or end - start < 2:
            return
        label = kind
        if kind == "module":
            try:
                label = f"module {str(node.header.name.valueText)}"
            except Exception:
                pass
        elif kind in ("always_ff", "always_comb", "always", "always_latch", "initial"):
            label = f"{kind} (L{start})"
        elif kind in ("function", "task"):
            try:
                label = f"{kind} {str(node.name.valueText)}"
            except Exception:
                label = kind
        elif kind == "case":
            label = f"case (L{start})"
        ranges.append({
            "kind": kind,
            "label": label,
            "line_start": start,
            "line_end": end,
        })

    try:
        tree.root.visit(visit)
    except Exception:
        pass
    ranges.sort(key=lambda r: (r["line_start"], -r["line_end"]))
    return ranges


def folds_for_path(path: str, text: str) -> List[Dict[str, Any]]:
    """Dispatch to the right extractor by file extension.

    Unknown extensions return an empty list — frontend then renders
    the raw source and the universal drag-select-comment still works.
    """
    p = (path or "").lower()
    if p.endswith((".v", ".sv", ".vh", ".svh")):
        return extract_verilog_folds(text)
    if p.endswith((".yaml", ".yml")):
        return extract_yaml_folds(text)
    return []
