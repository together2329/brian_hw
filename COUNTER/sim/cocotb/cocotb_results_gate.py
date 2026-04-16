#!/usr/bin/env python3
"""Parse cocotb JUnit results.xml and enforce a failing-test quality gate.

Also emits a structured JSON artifact for CI/report tooling.
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _collect_testcases(root: ET.Element) -> list[ET.Element]:
    return list(root.findall(".//testcase"))


def _failure_record(tc: ET.Element, kind: str, node: ET.Element) -> dict[str, Any]:
    classname = tc.get("classname", "")
    name = tc.get("name", "")
    message = node.get("message", "").strip()
    text = (node.text or "").strip()
    detail = message or text or "(no detail)"
    return {
        "kind": kind,
        "classname": classname,
        "name": name,
        "detail": detail,
    }


def _testcase_name(classname: str, name: str) -> str:
    return f"{classname}.{name}" if classname else name


def _build_json_artifact(
    xml_path: Path,
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "tool": "cocotb-results-gate",
        "input": str(xml_path),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "failing_tests": [
            {
                "kind": item["kind"],
                "test": f"{item['classname']}.{item['name']}"
                if item["classname"]
                else item["name"],
                "classname": item["classname"],
                "name": item["name"],
                "detail": item["detail"],
            }
            for item in failures
        ],
        "status": "pass" if failed == 0 else "fail",
    }


def main() -> int:
    xml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results.xml")
    json_path = Path(
        os.getenv(
            "COCOTB_RESULTS_JSON",
            str(Path(__file__).resolve().with_name("cocotb_results_gate.json")),
        )
    )

    if not xml_path.exists():
        print(f"[results-gate] ERROR: results file not found: {xml_path}")
        return 2

    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        print(f"[results-gate] ERROR: invalid XML in {xml_path}: {exc}")
        return 2

    testcases = _collect_testcases(root)
    failures: list[dict[str, Any]] = []

    for tc in testcases:
        for node in tc.findall("failure"):
            failures.append(_failure_record(tc, "failure", node))
        for node in tc.findall("error"):
            failures.append(_failure_record(tc, "error", node))

    skipped = sum(len(tc.findall("skipped")) for tc in testcases)
    failed = len(failures)
    total = len(testcases)
    passed = max(total - failed - skipped, 0)

    print(f"[results-gate] file: {xml_path}")
    print(
        "[results-gate] summary: "
        f"total={total} passed={passed} failed={failed} skipped={skipped}"
    )

    if failures:
        print(f"[results-gate] failing tests ({len(failures)}):")
        for item in failures:
            label = _testcase_name(item["classname"], item["name"])
            print(f"  - {item['kind']}: {label}: {item['detail']}")
    else:
        print("[results-gate] failing tests: none")

    artifact = _build_json_artifact(
        xml_path=xml_path,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        failures=failures,
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"[results-gate] json artifact: {json_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
