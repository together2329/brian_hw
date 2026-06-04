from __future__ import annotations

import copy
from pathlib import Path

from .contract_reflection_helpers import first_map, make_contract_ip, write_json
from .test_semantic_contract_required_closure import (
    _run_contract_check,
    _semantic_contracts,
    _write_legacy_reflection,
    _write_stage_artifacts,
)


def test_required_contract_closure_rejects_missing_semantic_evidence_rows(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    source = copy.deepcopy(_semantic_contracts())
    obligation = first_map(first_map(source, "requirements"), "obligations")
    obligation["evidence_rows"] = []
    write_json(ip_dir / "verify" / "semantic_contracts.json", source)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1
    assert "missing evidence_rows" in result.stdout
