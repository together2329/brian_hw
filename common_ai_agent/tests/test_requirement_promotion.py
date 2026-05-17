from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "workflow" / "req-gen" / "scripts" / "promote_requirement_review.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(f"promote_requirement_review_{time.time_ns()}", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promote_requirement_review_requires_explicit_human_approver(tmp_path: Path):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        mod.promote(ip, tmp_path, source=source, approved_by="")

    assert "approved-by" in str(exc.value)


def test_promote_requirement_review_rejects_placeholder_approver_for_real_promotion(
    tmp_path: Path,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        mod.promote(ip, tmp_path, source=source, approved_by="dryrun")

    assert "real human approver" in str(exc.value)
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


@pytest.mark.parametrize(
    "approved_by",
    [
        "dryrun",
        "dry-run",
        "dry_run",
        "dry run",
        "test",
        "placeholder",
        "unknown",
        "none",
        "n/a",
        "N.A.",
    ],
)
def test_promote_requirement_review_rejects_placeholder_approver_variants(
    tmp_path: Path,
    approved_by: str,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        mod.promote(ip, tmp_path, source=source, approved_by=approved_by)

    assert "real human approver" in str(exc.value)
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


@pytest.mark.parametrize("approved_by", ["dryrun", "dry-run", "dry_run", "dry run", "test", "unknown", "n/a"])
def test_promote_requirement_review_allows_placeholder_approver_variants_for_dry_run(
    tmp_path: Path,
    approved_by: str,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")

    manifest = mod.promote(ip, tmp_path, source=source, approved_by=approved_by, dry_run=True)

    assert manifest["dry_run"] is True
    assert manifest["approved_by"] == approved_by.strip()
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


def test_promote_requirement_review_cli_rejects_placeholder_approver_for_real_promotion(
    tmp_path: Path,
):
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            ip,
            "--root",
            ".",
            "--source",
            f"{ip}/doc/{ip}_requirement_review.md",
            "--approved-by",
            "dryrun",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "real human approver" in result.stderr
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


def test_promote_requirement_review_writes_req_and_manifest(tmp_path: Path):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")

    manifest = mod.promote(ip, tmp_path, source=source, approved_by="brian", decision_note="approved in chat")

    target = tmp_path / ip / "req" / f"{ip}_requirements.md"
    manifest_path = tmp_path / ip / "req" / "approval_manifest.json"
    assert target.is_file()
    assert manifest_path.is_file()
    text = target.read_text(encoding="utf-8")
    assert "Approval status: approved" in text
    assert "Approved by: brian" in text
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["approved_by"] == "brian"
    assert saved["target"] == f"{ip}/req/{ip}_requirements.md"
    assert saved["target_sha256"] == manifest["target_sha256"]

    with pytest.raises(SystemExit) as exc:
        mod.promote(ip, tmp_path, source=source, approved_by="brian")
    assert "already exists" in str(exc.value)


def test_promote_requirement_review_resolves_relative_source_against_root(tmp_path: Path):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")

    manifest = mod.promote(
        ip,
        tmp_path,
        source=Path(f"{ip}/doc/{ip}_requirement_review.md"),
        approved_by="brian",
    )

    assert manifest["source"] == f"{ip}/doc/{ip}_requirement_review.md"
    assert manifest["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert (tmp_path / ip / "req" / f"{ip}_requirements.md").is_file()


def test_promote_requirement_review_removes_review_only_pending_status(tmp_path: Path):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "# Review\n\n"
        "Approval status: pending user review. This file is evidence for review, not a\n"
        "human-approved requirement artifact.\n\n"
        + ("locked CPU scope\n" * 120),
        encoding="utf-8",
    )

    mod.promote(ip, tmp_path, source=source, approved_by="brian")

    target = tmp_path / ip / "req" / f"{ip}_requirements.md"
    text = target.read_text(encoding="utf-8")
    assert "Approval status: approved" in text
    assert "pending user review" not in text
    assert "not a human-approved requirement artifact" not in text


def test_promote_requirement_review_resolves_open_review_decision(tmp_path: Path):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.promote(ip, tmp_path, source=source, approved_by="brian")

    resolved = json.loads(review.read_text(encoding="utf-8"))
    assert resolved["status"] == "resolved"
    assert resolved["resolution"]["decision"] == "approved"
    assert resolved["resolution"]["approved_by"] == "brian"
    assert manifest["resolved_review_decision"] == f"{ip}/review/decision_needed_req_requirement_approval.json"


def test_promote_requirement_review_dry_run_validates_without_writing_or_resolving(
    tmp_path: Path,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.promote(ip, tmp_path, source=source, approved_by="dryrun", dry_run=True)

    assert manifest["dry_run"] is True
    assert manifest["target"] == f"{ip}/req/{ip}_requirements.md"
    assert manifest["target_sha256_preview"] == manifest["target_sha256"]
    assert "approved_at_utc" in manifest["note"]
    assert "approved_by" in manifest["note"]
    assert "decision_note" in manifest["note"]
    assert manifest["would_resolve_review_decision"] == f"{ip}/review/decision_needed_req_requirement_approval.json"
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()
    assert json.loads(review.read_text(encoding="utf-8"))["status"] == "review_decision_needed"


def test_promote_requirement_review_cli_dry_run_does_not_write_req_artifacts(
    tmp_path: Path,
):
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            ip,
            "--root",
            ".",
            "--source",
            f"{ip}/doc/{ip}_requirement_review.md",
            "--approved-by",
            "dryrun",
            "--dry-run",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "dry-run ok; would write" in result.stdout
    assert "dry-run approved_at_utc=" in result.stdout
    assert "dry-run source_sha256=" in result.stdout
    assert "dry-run target_sha256=" in result.stdout
    assert "dry-run ok; would resolve" in result.stdout
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()
    assert json.loads(review.read_text(encoding="utf-8"))["status"] == "review_decision_needed"


def test_promote_requirement_review_cli_dry_run_json_outputs_manifest_preview(
    tmp_path: Path,
):
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            ip,
            "--root",
            ".",
            "--source",
            f"{ip}/doc/{ip}_requirement_review.md",
            "--approved-by",
            "dryrun",
            "--dry-run",
            "--json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["dry_run"] is True
    assert manifest["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert manifest["target"] == f"{ip}/req/{ip}_requirements.md"
    assert manifest["target_sha256_preview"] == manifest["target_sha256"]
    assert "approved_at_utc" in manifest["note"]
    assert "approved_by" in manifest["note"]
    assert "decision_note" in manifest["note"]
    assert manifest["would_resolve_review_decision"] == f"{ip}/review/decision_needed_req_requirement_approval.json"
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()
    assert json.loads(review.read_text(encoding="utf-8"))["status"] == "review_decision_needed"


def test_promote_requirement_review_cli_json_outputs_written_manifest(
    tmp_path: Path,
):
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            ip,
            "--root",
            ".",
            "--source",
            f"{ip}/doc/{ip}_requirement_review.md",
            "--approved-by",
            "brian",
            "--decision-note",
            "approved in test",
            "--json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    saved_manifest = json.loads((tmp_path / ip / "req" / "approval_manifest.json").read_text(encoding="utf-8"))
    assert manifest == saved_manifest
    assert manifest["approved_by"] == "brian"
    assert manifest["target"] == f"{ip}/req/{ip}_requirements.md"
    assert manifest["resolved_review_decision"] == f"{ip}/review/decision_needed_req_requirement_approval.json"
    assert not manifest.get("dry_run")
    assert (tmp_path / ip / "req" / f"{ip}_requirements.md").is_file()
    assert json.loads(review.read_text(encoding="utf-8"))["status"] == "resolved"


def test_promote_requirement_review_refuses_stale_approval_target_before_writing_req(
    tmp_path: Path,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": "0" * 64,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc:
        mod.promote(ip, tmp_path, source=source, approved_by="brian")

    assert "approval_target sha256 does not match" in str(exc.value)
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


def test_promote_requirement_review_accepts_matching_approval_target(tmp_path: Path):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.promote(ip, tmp_path, source=source, approved_by="brian")

    assert manifest["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert (tmp_path / ip / "req" / f"{ip}_requirements.md").is_file()


def test_promote_requirement_review_refuses_stale_machine_evidence_snapshot(
    tmp_path: Path,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    ssot = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    ssot.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    ssot.write_text("ip: cpu_ref\n", encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    },
                    "machine_evidence_snapshot": {
                        "ssot_sha256": "1" * 64,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc:
        mod.promote(ip, tmp_path, source=source, approved_by="brian")

    assert "machine_evidence_snapshot ssot_sha256 does not match" in str(exc.value)
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


def test_promote_requirement_review_accepts_matching_machine_evidence_snapshot(
    tmp_path: Path,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    ssot = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    ssot.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    ssot.write_text("ip: cpu_ref\n", encoding="utf-8")
    review.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    },
                    "machine_evidence_snapshot": {
                        "ssot_sha256": hashlib.sha256(ssot.read_bytes()).hexdigest(),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.promote(ip, tmp_path, source=source, approved_by="brian")

    assert manifest["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert (tmp_path / ip / "req" / f"{ip}_requirements.md").is_file()


def test_promote_requirement_review_refuses_malformed_review_decision_before_writing_req(
    tmp_path: Path,
):
    mod = _load_module()
    ip = "cpu_ref"
    source = tmp_path / ip / "doc" / f"{ip}_requirement_review.md"
    review = tmp_path / ip / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    review.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("locked CPU scope\n" * 120), encoding="utf-8")
    review.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        mod.promote(ip, tmp_path, source=source, approved_by="brian")

    assert "cannot parse review decision" in str(exc.value)
    assert not (tmp_path / ip / "req" / f"{ip}_requirements.md").exists()
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


def test_atomic_write_text_uses_unique_tmp_names_under_concurrency(tmp_path: Path):
    mod = _load_module()
    import threading

    target = tmp_path / "out.txt"
    barrier = threading.Barrier(2)
    errors: list[str] = []

    def write(text: str) -> None:
        try:
            barrier.wait()
            for _ in range(20):
                mod._atomic_write_text(target, text)
        except Exception as exc:
            errors.append(str(exc))

    t1 = threading.Thread(target=write, args=("a\n",))
    t2 = threading.Thread(target=write, args=("b\n",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert errors == []
    assert target.read_text(encoding="utf-8") in {"a\n", "b\n"}
    assert list(tmp_path.glob("out.txt.tmp*")) == []
