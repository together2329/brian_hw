#!/usr/bin/env python3
"""Back-annotate scoreboard rows with the obligations they are evidence for.

Obligations are GENERATED from passing scoreboard rows (see
emit_semantic_contracts.py + emit_goal_contract_overlay.py), so at simulation
time a row cannot yet know which obligation_ids it grounds. This script runs
*after* verify/evidence_contract.json exists and emits an additive SIDECAR
(sim/scoreboard_obligation_links.json) that maps each evidence row
(goal_id, scenario_id) to the obligation_ids and contract_refs it satisfies.

It does NOT mutate the append-only sim/scoreboard_events.jsonl. The sidecar lets
check_evidence_contract (and signoff) match a row to its obligations directly by
reading the linkage instead of re-deriving it from evidence_rows[*].match.

Linkage is read from evidence_contract.json obligations' evidence_rows[*].match
(reusing the evidence_contract_json / evidence_contract_rows helpers); a single
row can map to multiple obligations, so obligation_ids/contract_refs aggregate.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.evidence_contract_json import (
    JsonMap,
    as_list as _as_list,
    as_map as _as_map,
    load_json as _load_json,
    strings as _strings,
    text as _text,
)
from workflow.contract_reflection.evidence_contract_rows import DEFAULT_SCOREBOARD


LABEL = "scoreboard_obligation_links"


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw_ip = Path(ip)
    if raw_ip.is_absolute():
        raise SystemExit(f"[{LABEL}] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw_ip).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[{LABEL}] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def _parse_args(argv: list[str]) -> tuple[str, Path]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: annotate_scoreboard_obligations.py <ip> [--root <root>]")
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


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_links(contract: JsonMap) -> list[JsonMap]:
    """Aggregate (artifact, goal_id, scenario_id) -> {obligation_ids, contract_refs}.

    Reads obligations' evidence_rows[*].match. Each match is the same
    (goal_id, scenario_id, ...) selector check_evidence_contract uses to bind a
    row to an obligation, so the sidecar matches the live verdict path exactly.
    """
    # Preserve first-seen order of rows for deterministic, stable output.
    order: list[tuple[str, str, str]] = []
    by_key: dict[tuple[str, str, str], dict[str, list[str]]] = {}
    for item in _as_list(contract.get("obligations")):
        obligation = _as_map(item)
        oid = _text(obligation.get("obligation_id"))
        if not oid:
            continue
        refs = _strings(obligation.get("contract_refs"))
        for row_ref in _as_list(obligation.get("evidence_rows")):
            ref = _as_map(row_ref)
            artifact = _text(ref.get("artifact")) or DEFAULT_SCOREBOARD
            match = _as_map(ref.get("match"))
            goal_id = _text(match.get("goal_id"))
            scenario_id = _text(match.get("scenario_id"))
            key = (artifact, goal_id, scenario_id)
            bucket = by_key.get(key)
            if bucket is None:
                bucket = {"obligation_ids": [], "contract_refs": []}
                by_key[key] = bucket
                order.append(key)
            if oid not in bucket["obligation_ids"]:
                bucket["obligation_ids"].append(oid)
            for cref in refs:
                if cref not in bucket["contract_refs"]:
                    bucket["contract_refs"].append(cref)

    links: list[JsonMap] = []
    for artifact, goal_id, scenario_id in order:
        bucket = by_key[(artifact, goal_id, scenario_id)]
        links.append(
            {
                "artifact": artifact,
                "goal_id": goal_id,
                "scenario_id": scenario_id,
                "obligation_ids": sorted(bucket["obligation_ids"]),
                "contract_refs": sorted(bucket["contract_refs"]),
            }
        )
    # Stable ordering across runs regardless of obligation iteration order.
    links.sort(key=lambda link: (link["artifact"], link["goal_id"], link["scenario_id"]))
    return links


def _analyze(ip_dir: Path) -> JsonMap:
    contract = _load_json(ip_dir / "verify" / "evidence_contract.json", LABEL)
    links = _build_links(contract)
    return {
        "generated_at": _utc(),
        "ip": ip_dir.name,
        "links": links,
        "schema_version": 1,
        "semantic_source_fingerprint": contract.get("semantic_source_fingerprint"),
        "summary": {
            "linked_rows": len(links),
            "obligations": len(_as_list(contract.get("obligations"))),
        },
        "type": "scoreboard_obligation_links",
    }


def main() -> int:
    ip, root = _parse_args(sys.argv[1:])
    ip_dir = _resolve_ip_dir(root, ip)
    report = _analyze(ip_dir)
    out = ip_dir / "sim" / "scoreboard_obligation_links.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        f"[{LABEL}] wrote {out}: "
        f"linked_rows={summary['linked_rows']} obligations={summary['obligations']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
