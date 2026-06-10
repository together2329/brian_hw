#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.evidence_contract_json import strings
from workflow.contract_reflection.sim_freshness import resolve_ip_dir, write_sim_freshness_check


def _parse_args(argv: list[str]) -> tuple[str, Path]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: check_sim_evidence_freshness.py <ip> [--root <root>]")
    ip = argv[0]
    root = Path(".")
    index = 1
    while index < len(argv):
        token = argv[index]
        if token != "--root":
            raise SystemExit(f"usage: unexpected argument {token!r}")
        if index + 1 >= len(argv):
            raise SystemExit("usage: --root requires a value")
        root = Path(argv[index + 1])
        index += 2
    return ip, root.resolve()


def main() -> int:
    ip, root = _parse_args(sys.argv[1:])
    ip_dir = resolve_ip_dir(root, ip, "sim_freshness")
    report = write_sim_freshness_check(ip_dir)
    out = ip_dir / "signoff" / "sim_evidence_freshness.json"
    print(f"[sim_freshness] {report['status']}: wrote {out}")
    for issue in strings(report.get("issues")):
        print(f"[sim_freshness] {issue}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
