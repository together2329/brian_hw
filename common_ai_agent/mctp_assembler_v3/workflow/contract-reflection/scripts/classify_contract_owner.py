#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.owner_routing import route_from_reports


def _parse_args(argv: list[str]) -> tuple[str, Path]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: classify_contract_owner.py <ip> [--root <root>]")
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


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw = Path(ip)
    if raw.is_absolute():
        raise SystemExit(f"[contract_owner] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[contract_owner] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def main() -> int:
    ip, root = _parse_args(sys.argv[1:])
    ip_dir = _resolve_ip_dir(root, ip)
    report = route_from_reports(ip_dir)
    out = ip_dir / "signoff" / "contract_owner_routing.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[contract_owner] {report['status']}: owner={report['owner_workflow'] or '-'} wrote {out}")
    if report.get("reason"):
        print(f"[contract_owner] reason: {report['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
