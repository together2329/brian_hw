"""Finding 31 — refresh_rtl_provenance CREATE mode: blesses only workflow-
fingerprinted RTL, still refuses manual RTL."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow" / "rtl-gen" / "scripts" / "refresh_rtl_provenance.py"


def _mk_ip(tmp_path, ip, fingerprints: bool):
    (tmp_path / ip / "yaml").mkdir(parents=True)
    (tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"top_module:\n  name: {ip}\n", encoding="utf-8")
    rtl = tmp_path / ip / "rtl"
    rtl.mkdir()
    (rtl / f"{ip}.sv").write_text(f"module {ip}(); endmodule\n", encoding="utf-8")
    (rtl / "rtl_todo_plan.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
    if fingerprints:
        (rtl / "rtl_authoring_plan.json").write_text("{}", encoding="utf-8")


def _run(ip, root):
    return subprocess.run([sys.executable, str(SCRIPT), ip, "--root", str(root)],
                          capture_output=True, text=True, timeout=30)


def test_create_with_authoring_fingerprints(tmp_path):
    _mk_ip(tmp_path, "ipa", fingerprints=True)
    r = _run("ipa", tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    doc = json.loads((tmp_path / "ipa" / "rtl" / "rtl_authoring_provenance.json").read_text())
    assert doc["agent"] == "common_ai_agent" and doc["workflow"] == "rtl-gen"
    assert "rtl/ipa.sv" in doc["rtl_files"]


def test_refuses_manual_rtl_without_fingerprints(tmp_path):
    _mk_ip(tmp_path, "ipb", fingerprints=False)
    r = _run("ipb", tmp_path)
    assert r.returncode != 0
    assert "refusing to bless manual RTL" in (r.stdout + r.stderr)
    assert not (tmp_path / "ipb" / "rtl" / "rtl_authoring_provenance.json").exists()
