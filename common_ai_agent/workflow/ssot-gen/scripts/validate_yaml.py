#!/usr/bin/env python3
"""validate_yaml.py — Python port of validate_yaml.sh (ssot-gen).

Run Cerberus schema validation on all YAML SSOT files for a module.

CLI / env contract (preserved from bash ``set -euo pipefail``):
  * Module name = first positional argument else ``$HOOK_CMD_ARGS``; missing ⇒
    ``[ERROR] ...`` usage, exit 1.
  * Schema path = ``<module>/yaml/<module>_schema.yaml``.  Missing schema ⇒
    ``[SKIP] ...``, exit 0.
  * Validate every ``<module>/yaml/*.yaml`` except the schema file (shell-glob
    order, i.e. sorted).  PASS/FAIL printed per file; field errors printed on
    FAIL.  Exit 0 when all pass, exit 1 when any fail.

The per-file validation is performed inline (no python3 subprocess) but emits
exactly the same ``PASS`` / ``FAIL`` / ``ERROR: ...`` text the inline bash
heredoc produced.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _validate_one(yaml_file: Path, schema_path: Path) -> bool:
    """Return True on PASS, False on FAIL/ERROR; print like the bash heredoc."""
    import yaml  # imported lazily, mirroring the inline python in the .sh
    from cerberus import Validator

    try:
        with open(yaml_file) as handle:
            data = yaml.safe_load(handle)
        with open(schema_path) as handle:
            schema = yaml.safe_load(handle)
        validator = Validator(schema)
        if validator.validate(data):
            print("PASS")
            return True
        print("FAIL")
        for field, err in validator.errors.items():
            print(f"  {field}: {err}")
        return False
    except Exception as exc:  # noqa: BLE001 — mirror the broad bash `except`
        print(f"ERROR: {exc}")
        return False


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    module_name = argv[0] if argv else os.environ.get("HOOK_CMD_ARGS", "")
    if not module_name:
        print("[ERROR] Module name required. Usage: /validate-yaml <module_name>")
        return 1

    yaml_dir = Path(module_name) / "yaml"
    schema = yaml_dir / f"{module_name}_schema.yaml"

    if not schema.is_file():
        print(f"[SKIP] No schema file at {schema}")
        return 0

    print(f"=== YAML Schema Validation: {module_name} ===")
    fail_count = 0

    # Bash: for yaml_file in "$YAML_DIR"/*.yaml  (glob is sorted).
    #
    # FLAGGED BUG (preserved for equivalence): the .sh runs under
    # ``set -euo pipefail``.  The inner ``python3 ... 2>&1`` is a bare statement,
    # so a FAIL (the inline python's ``sys.exit(1)``) trips ``set -e`` and the
    # script EXITS IMMEDIATELY with status 1 — *before* reaching the
    # ``if [ $? -ne 0 ]`` check, the rest of the loop, or the summary line.
    # We reproduce that: stop at the first failing file and return 1 with no
    # ``=== ... VALIDATION FAILURE(S) ===`` summary.
    for yaml_file in sorted(yaml_dir.glob("*.yaml")):
        if yaml_file.name == f"{module_name}_schema.yaml":
            continue
        print(f"  validating {yaml_file.name} ... ", end="")
        # The bash printed the trailing PASS/FAIL on the same line via the
        # inner python's print(); replicate by not adding a newline above.
        sys.stdout.flush()
        if not _validate_one(yaml_file, schema):
            # set -e: abort the whole script on the first non-zero inner python.
            return 1

    if fail_count == 0:
        print("=== ALL YAML FILES VALIDATED ===")
        return 0
    print(f"=== {fail_count} VALIDATION FAILURE(S) ===")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
