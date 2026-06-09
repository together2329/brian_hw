from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "workflow" / "fl-model-gen" / "scripts" / "check_signature_drift.py"

_HASH_KEYS = ("ssot_hash", "transactions_hash", "invariants_hash", "expressions_hash")


def _write_signature(tmp_path: Path, ip: str, hashes: dict[str, Any]) -> Path:
    ip_dir = tmp_path / ip
    (ip_dir / "model").mkdir(parents=True)
    payload: dict[str, Any] = {"schema_version": 1, "type": "model_signature", "ip": ip}
    payload.update(hashes)
    (ip_dir / "model" / "model_signature.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return ip_dir


def _run(tmp_path: Path, ip: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), ip, "--root", str(tmp_path), *extra],
        text=True,
        capture_output=True,
    )


def _full_hashes() -> dict[str, str]:
    return {k: f"{k}_value_0123456789abcdef" for k in _HASH_KEYS}


def test_signature_drift_first_run_then_unchanged_is_ok(tmp_path: Path) -> None:
    """Regression: a normal lock then unchanged signature must stay OK."""
    ip = "sigip"
    _write_signature(tmp_path, ip, _full_hashes())
    first = _run(tmp_path, ip)
    assert first.returncode == 0, first.stdout + first.stderr
    second = _run(tmp_path, ip)
    assert second.returncode == 0, second.stdout + second.stderr


def test_signature_drift_detects_real_change(tmp_path: Path) -> None:
    """Regression: a genuine hash change after lock must report drift (exit 1)."""
    ip = "sigip"
    ip_dir = _write_signature(tmp_path, ip, _full_hashes())
    assert _run(tmp_path, ip).returncode == 0
    changed = _full_hashes()
    changed["ssot_hash"] = "ssot_hash_TAMPERED_value"
    (ip_dir / "model" / "model_signature.json").write_text(
        json.dumps({"schema_version": 1, "type": "model_signature", "ip": ip, **changed}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    result = _run(tmp_path, ip)
    assert result.returncode == 1
    assert "golden_changed" in result.stderr


def test_signature_drift_null_hashes_no_false_positive(tmp_path: Path) -> None:
    """D-M1: a lock created from null/absent hashes must not report spurious drift."""
    ip = "sigip"
    # Signature has no hash keys at all -> lock stores them as null.
    _write_signature(tmp_path, ip, {})
    first = _run(tmp_path, ip)
    assert first.returncode == 0, first.stdout + first.stderr
    second = _run(tmp_path, ip)
    assert second.returncode == 0, second.stdout + second.stderr


def test_signature_drift_first_run_prints_rebless_warning(tmp_path: Path) -> None:
    """Lock-integrity: first-run lock creation must warn prominently and list locked hashes."""
    ip = "sigip"
    _write_signature(tmp_path, ip, _full_hashes())
    result = _run(tmp_path, ip)
    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "RE-BLESS" in combined.upper()
    # Must name the locked hash keys so a reviewer can see what was blessed.
    for key in _HASH_KEYS:
        assert key in combined


def test_signature_drift_strict_fails_when_lock_absent(tmp_path: Path) -> None:
    """Lock-integrity: --strict exits 1 when the lock is absent but a signature exists."""
    ip = "sigip"
    _write_signature(tmp_path, ip, _full_hashes())
    result = _run(tmp_path, ip, "--strict")
    assert result.returncode == 1
    assert "lock" in (result.stdout + result.stderr).lower()


def test_signature_drift_strict_ok_after_lock_exists(tmp_path: Path) -> None:
    """--strict passes once the lock exists and matches."""
    ip = "sigip"
    _write_signature(tmp_path, ip, _full_hashes())
    # Establish lock (non-strict first run).
    assert _run(tmp_path, ip).returncode == 0
    result = _run(tmp_path, ip, "--strict")
    assert result.returncode == 0, result.stdout + result.stderr
