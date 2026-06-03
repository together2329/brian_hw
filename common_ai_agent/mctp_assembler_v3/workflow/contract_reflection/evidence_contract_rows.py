from __future__ import annotations

from pathlib import Path

from workflow.contract_reflection.evidence_contract_json import JsonMap, as_list, as_map, load_rows, strings, text


DEFAULT_SCOREBOARD = "sim/scoreboard_events.jsonl"
ALLOWED_SCOREBOARD_ARTIFACTS = {DEFAULT_SCOREBOARD, "sim/contract_v2_events.jsonl"}
RowsByArtifact = dict[str, list[JsonMap]]


def load_scoreboard_rows(ip_dir: Path, contract: JsonMap) -> RowsByArtifact:
    artifacts = {DEFAULT_SCOREBOARD}
    for item in as_list(contract.get("obligations")):
        obligation = as_map(item)
        for row_ref in as_list(obligation.get("evidence_rows")):
            artifact = text(as_map(row_ref).get("artifact"))
            if artifact:
                artifacts.add(artifact)
    return {artifact: load_rows(_artifact_path(ip_dir, artifact), "evidence_contract") for artifact in sorted(artifacts)}


def matching_rows(obligation: JsonMap, rows_by_artifact: RowsByArtifact) -> list[JsonMap]:
    matches: list[JsonMap] = []
    evidence_rows = as_list(obligation.get("evidence_rows"))
    for item in evidence_rows:
        data = as_map(item)
        artifact = text(data.get("artifact")) or DEFAULT_SCOREBOARD
        expected = as_map(data.get("match"))
        for row in rows_by_artifact.get(artifact, []):
            if all(row.get(key) == value for key, value in expected.items()):
                matches.append(row)
    if evidence_rows:
        return matches
    scenarios = set(strings(obligation.get("scenario_ids")))
    return [row for row in rows_by_artifact.get(DEFAULT_SCOREBOARD, []) if text(row.get("scenario_id")) in scenarios]


def _artifact_path(ip_dir: Path, artifact: str) -> Path:
    raw = Path(artifact)
    if not artifact or raw.is_absolute():
        raise SystemExit("[evidence_contract] FAIL: evidence row artifact path escapes IP root")
    if artifact not in ALLOWED_SCOREBOARD_ARTIFACTS:
        raise SystemExit("[evidence_contract] FAIL: evidence row artifact is not an allowed simulator scoreboard artifact")
    path = (ip_dir / raw).resolve()
    try:
        _ = path.relative_to(ip_dir.resolve())
    except ValueError as exc:
        raise SystemExit("[evidence_contract] FAIL: evidence row artifact path escapes IP root") from exc
    return path
