import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "workflow" / "fl-model-gen" / "scripts" / "check_fl_model_artifacts.py"


def _write_valid_fl_fixture(root: Path, ip: str) -> Path:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir()
    (ip_dir / "cov").mkdir()
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
ip: gate_probe
function_model:
  transactions:
    - id: TX_WRITE
      name: Write payload
      output_rules:
        - name: resp
          expr: 0
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "model" / "functional_model.py").write_text(
        """
class FunctionalModel:
    def apply(self, txn):
        return {"resp": 0, "transaction_id": txn.get("id", "TX_WRITE")}


def run_self_check():
    return {
        "passed": True,
        "transaction_results": [
            {"transaction_id": "TX_WRITE", "passed": True, "result": {"resp": 0}}
        ],
    }
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "model" / "fl_model_check.json").write_text(
        json.dumps(
            {
                "passed": True,
                "transaction_results": [{"transaction_id": "TX_WRITE", "passed": True}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "model" / "decomposition.json").write_text(
        json.dumps(
            {
                "complete": True,
                "units": [
                    {
                        "name": "write_payload",
                        "kind": "datapath",
                        "source_sections": ["function_model.transactions.TX_WRITE"],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "fcov_plan.json").write_text(
        json.dumps(
            {
                "planned_before_rtl": True,
                "bins": [
                    {
                        "id": "TX_WRITE_seen",
                        "source": "function_model.transactions.TX_WRITE",
                        "description": "TX_WRITE covered",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return ip_dir


def test_check_fl_model_artifacts_passes_worker_authored_model(tmp_path: Path):
    ip = "gate_probe"
    ip_dir = _write_valid_fl_fixture(tmp_path, ip)

    proc = subprocess.run(
        [sys.executable, str(GATE), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads((ip_dir / "logs" / "gates" / "fl_model_gate.json").read_text())
    assert report["passed"] is True
    assert report["issues"] == []


def test_check_fl_model_artifacts_rejects_placeholder_model(tmp_path: Path):
    ip = "gate_probe"
    ip_dir = _write_valid_fl_fixture(tmp_path, ip)
    model_path = ip_dir / "model" / "functional_model.py"
    model_path.write_text(model_path.read_text(encoding="utf-8") + "\n# PLACEHOLDER\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(GATE), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 1
    assert "forbidden marker 'PLACEHOLDER'" in proc.stdout
