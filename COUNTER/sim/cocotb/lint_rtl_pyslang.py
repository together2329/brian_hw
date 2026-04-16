#!/usr/bin/env python3
"""RTL lint/link checker using pyslang Compilation API.

Runs a multi-file compile over the DMA RTL/TB sources and reports diagnostics,
with unresolved-reference summaries and policy controls via environment vars:

- RTL_WARN_AS_ERROR: treat warnings as errors for exit status (1/0, true/false)
- RTL_DIAG_ALLOWLIST: comma-separated diagnostic code names to include
- RTL_DIAG_SUPPRESS: comma-separated diagnostic code names to suppress
- RTL_LINT_JSON: output path for structured JSON artifact
- RTL_LINT_SARIF: output path for SARIF artifact
- RTL_LINT_BASELINE: path to baseline JSON artifact; when set, fail only on new diagnostics
- RTL_LINT_INCLUDE: comma-separated glob patterns to include (default: rtl/**/*.sv,tb/**/*.sv)
- RTL_LINT_EXCLUDE: comma-separated glob patterns to exclude from included files
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import pyslang


@dataclass(frozen=True)
class DiagView:
    diag: pyslang.Diagnostic
    code: str
    line: str
    file: str
    line_no: int
    col_no: int
    message: str


def _diag_code_text(code: object) -> str:
    """Return a concise diagnostic code label.

    pyslang currently stringifies as ``DiagCode(Name)``; trim wrapper for readability.
    """
    text = str(code)
    if text.startswith("DiagCode(") and text.endswith(")"):
        return text[len("DiagCode(") : -1]
    return text


def _parse_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _parse_code_set_env(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def _diag_fields(
    diag: pyslang.Diagnostic,
    code: str,
    engine: pyslang.DiagnosticEngine,
    sm: pyslang.SourceManager,
) -> tuple[str, int, int, str, str]:
    """Return normalized diagnostic fields and formatted line."""
    loc = diag.location
    file_name = str(sm.getFileName(loc))
    line_no = sm.getLineNumber(loc)
    col_no = sm.getColumnNumber(loc)
    message = engine.formatMessage(diag)
    line = f"{file_name}:{line_no}:{col_no}: {code}: {message}"
    return file_name, line_no, col_no, message, line


def _view_to_json(v: DiagView) -> dict[str, Any]:
    return {
        "severity": "error" if v.diag.isError() else "warning",
        "code": v.code,
        "file": v.file,
        "line": v.line_no,
        "column": v.col_no,
        "message": v.message,
        "formatted": v.line,
    }


def _sarif_level(v: DiagView) -> str:
    return "error" if v.diag.isError() else "warning"


def _view_to_sarif_result(v: DiagView, root: Path) -> dict[str, Any]:
    """Convert diagnostic into a SARIF result entry."""
    abs_file = (Path(v.file) if Path(v.file).is_absolute() else (Path.cwd() / v.file)).resolve()
    try:
        rel_uri = abs_file.relative_to(root).as_posix()
    except ValueError:
        rel_uri = abs_file.as_posix()

    return {
        "ruleId": v.code,
        "level": _sarif_level(v),
        "message": {"text": v.message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": rel_uri},
                    "region": {
                        "startLine": v.line_no,
                        "startColumn": v.col_no,
                    },
                }
            }
        ],
    }


def _sarif_log(files: list[Path], diagnostics: list[DiagView], root: Path) -> dict[str, Any]:
    rule_ids = sorted({v.code for v in diagnostics})
    rules = [
        {
            "id": rid,
            "name": rid,
            "shortDescription": {"text": rid},
        }
        for rid in rule_ids
    ]
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "pyslang",
                        "informationUri": "https://github.com/MikePopoloski/slang",
                        "rules": rules,
                    }
                },
                "artifacts": [{"location": {"uri": str(f)}} for f in files],
                "results": [_view_to_sarif_result(v, root) for v in diagnostics],
            }
        ],
    }


def _diag_key(diag: dict[str, Any]) -> tuple[str, str, str, int, int, str]:
    """Create a stable key for baseline comparisons."""
    return (
        str(diag.get("severity", "")),
        str(diag.get("code", "")),
        str(diag.get("file", "")),
        int(diag.get("line", 0) or 0),
        int(diag.get("column", 0) or 0),
        str(diag.get("message", "")),
    )


def _load_baseline(path: Path) -> list[dict[str, Any]]:
    """Load baseline diagnostics list from a prior JSON artifact."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("baseline JSON must be an object")
    diagnostics = data.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        raise ValueError("baseline JSON field 'diagnostics' must be a list")
    return diagnostics


def _parse_patterns_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name, "")
    if not raw.strip():
        return default
    return [part.strip() for part in raw.split(",") if part.strip()]


def _discover_files(root: Path, include_patterns: list[str], exclude_patterns: list[str]) -> list[Path]:
    """Discover lint source files using include/exclude glob patterns."""
    files_set: set[Path] = set()
    for pattern in include_patterns:
        files_set.update(path for path in root.glob(pattern) if path.is_file())

    def _is_excluded(path: Path) -> bool:
        rel = PurePosixPath(path.relative_to(root).as_posix())
        return any(rel.match(pat) for pat in exclude_patterns)

    files = sorted(p for p in files_set if not _is_excluded(p))
    if not files:
        raise ValueError(
            "no RTL/TB sources discovered "
            f"(include={include_patterns}, exclude={exclude_patterns})"
        )
    return files


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    include_patterns = _parse_patterns_env(
        "RTL_LINT_INCLUDE", ["rtl/**/*.sv", "tb/**/*.sv"]
    )
    exclude_patterns = _parse_patterns_env("RTL_LINT_EXCLUDE", [])
    files = _discover_files(root, include_patterns, exclude_patterns)

    warn_as_error = _parse_bool_env("RTL_WARN_AS_ERROR", default=False)
    allowlist = _parse_code_set_env("RTL_DIAG_ALLOWLIST")
    suppressions = _parse_code_set_env("RTL_DIAG_SUPPRESS")
    baseline_path_raw = os.getenv("RTL_LINT_BASELINE", "").strip()
    baseline_path = Path(baseline_path_raw) if baseline_path_raw else None
    json_out = Path(
        os.getenv(
            "RTL_LINT_JSON",
            str(Path(__file__).resolve().with_name("lint_rtl_report.json")),
        )
    )
    sarif_out = Path(
        os.getenv(
            "RTL_LINT_SARIF",
            str(Path(__file__).resolve().with_name("lint_rtl_report.sarif")),
        )
    )

    comp = pyslang.Compilation()
    for f in files:
        tree = pyslang.SyntaxTree.fromFile(str(f))
        comp.addSyntaxTree(tree)

    sm = comp.sourceManager
    engine = pyslang.DiagnosticEngine(sm)

    all_views: list[DiagView] = []
    for d in comp.getAllDiagnostics():
        code = _diag_code_text(d.code)
        file_name, line_no, col_no, message, line = _diag_fields(d, code, engine, sm)
        all_views.append(
            DiagView(
                diag=d,
                code=code,
                line=line,
                file=file_name,
                line_no=line_no,
                col_no=col_no,
                message=message,
            )
        )

    suppressed = [v for v in all_views if v.code in suppressions]
    after_suppress = [v for v in all_views if v.code not in suppressions]

    if allowlist:
        allowlist_filtered = [v for v in after_suppress if v.code not in allowlist]
        effective = [v for v in after_suppress if v.code in allowlist]
    else:
        allowlist_filtered = []
        effective = after_suppress

    errors = [v for v in effective if v.diag.isError()]
    warnings = [v for v in effective if not v.diag.isError()]

    unresolved = [
        v
        for v in effective
        if "unresolved" in v.code.lower() or "undefined" in v.code.lower()
    ]

    policy_errors = len(errors) + (len(warnings) if warn_as_error else 0)

    current_json_diags = [_view_to_json(v) for v in effective]
    baseline_diagnostics: list[dict[str, Any]] = []
    baseline_error: str | None = None
    new_diagnostics: list[dict[str, Any]] = []
    resolved_diagnostics: list[dict[str, Any]] = []
    baseline_mode = baseline_path is not None
    baseline_applied = False

    if baseline_path is not None:
        try:
            baseline_diagnostics = _load_baseline(baseline_path)
            baseline_set = {_diag_key(d) for d in baseline_diagnostics}
            current_set = {_diag_key(d) for d in current_json_diags}
            new_diagnostics = [d for d in current_json_diags if _diag_key(d) not in baseline_set]
            resolved_diagnostics = [d for d in baseline_diagnostics if _diag_key(d) not in current_set]
            baseline_applied = True
            policy_errors = len(new_diagnostics)
        except Exception as exc:  # noqa: BLE001 - report as lint infra error
            baseline_error = f"{type(exc).__name__}: {exc}"
            policy_errors = 1

    print("[lint-rtl] files:")
    for f in files:
        print(f"  - {f}")

    print(
        "[lint-rtl] policy: "
        f"RTL_WARN_AS_ERROR={int(warn_as_error)} "
        f"RTL_DIAG_ALLOWLIST={','.join(sorted(allowlist)) if allowlist else '(all)'} "
        f"RTL_DIAG_SUPPRESS={','.join(sorted(suppressions)) if suppressions else '(none)'} "
        f"RTL_LINT_BASELINE={baseline_path if baseline_path else '(none)'} "
        f"RTL_LINT_INCLUDE={','.join(include_patterns)} "
        f"RTL_LINT_EXCLUDE={','.join(exclude_patterns) if exclude_patterns else '(none)'}"
    )

    print(
        "[lint-rtl] diagnostics: "
        f"errors={len(errors)} warnings={len(warnings)} total={len(effective)} "
        f"suppressed={len(suppressed)} allowlist_filtered={len(allowlist_filtered)} "
        f"policy_errors={policy_errors}"
    )

    if baseline_mode:
        if baseline_error is not None:
            print(f"[lint-rtl] baseline: ERROR: {baseline_error}")
        else:
            print(
                "[lint-rtl] baseline: "
                f"loaded={baseline_path} baseline_diags={len(baseline_diagnostics)} "
                f"new={len(new_diagnostics)} resolved={len(resolved_diagnostics)}"
            )

    if unresolved:
        print(f"[lint-rtl] unresolved-reference diagnostics ({len(unresolved)}):")
        for v in unresolved:
            print(f"  {v.line}")
    else:
        print("[lint-rtl] unresolved-reference diagnostics: none")

    if effective:
        print("[lint-rtl] full diagnostics:")
        for v in effective:
            print(f"  {v.line}")

    json_artifact = {
        "tool": "pyslang",
        "files": [str(f) for f in files],
        "policy": {
            "warn_as_error": warn_as_error,
            "allowlist": sorted(allowlist),
            "suppressions": sorted(suppressions),
            "baseline_mode": baseline_mode,
            "baseline_path": str(baseline_path) if baseline_path else None,
            "baseline_applied": baseline_applied,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
        },
        "counts": {
            "errors": len(errors),
            "warnings": len(warnings),
            "total": len(effective),
            "suppressed": len(suppressed),
            "allowlist_filtered": len(allowlist_filtered),
            "policy_errors": policy_errors,
            "unresolved": len(unresolved),
            "new_vs_baseline": len(new_diagnostics),
            "resolved_vs_baseline": len(resolved_diagnostics),
        },
        "diagnostics": current_json_diags,
        "unresolved_reference_diagnostics": [_view_to_json(v) for v in unresolved],
        "suppressed_diagnostics": [_view_to_json(v) for v in suppressed],
        "allowlist_filtered_diagnostics": [_view_to_json(v) for v in allowlist_filtered],
        "baseline": {
            "error": baseline_error,
            "baseline_diagnostics": baseline_diagnostics,
            "new_diagnostics": new_diagnostics,
            "resolved_diagnostics": resolved_diagnostics,
        },
        "status": "pass" if policy_errors == 0 else "fail",
    }
    sarif_artifact = _sarif_log(files, effective, root)

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(json_artifact, indent=2), encoding="utf-8")
    sarif_out.parent.mkdir(parents=True, exist_ok=True)
    sarif_out.write_text(json.dumps(sarif_artifact, indent=2), encoding="utf-8")
    print(f"[lint-rtl] json artifact: {json_out}")
    print(f"[lint-rtl] sarif artifact: {sarif_out}")

    return 1 if policy_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
