#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SCRIPT_DIR/../../../.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/ulw-reqwiki-c003.XXXXXX")
trap 'rm -rf "$TMP_ROOT"; echo "C003_TEMP_CLEANUP removed=$TMP_ROOT"' EXIT

cd "$REPO"

python3 - "$TMP_ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
ip_dir = root / "quality_ip"
(ip_dir / "verify").mkdir(parents=True, exist_ok=True)
(ip_dir / "sim").mkdir(parents=True, exist_ok=True)
(ip_dir / "verify" / "ip_contract.json").write_text(
    json.dumps(
        {
            "observability": {
                "required_rtl_observed": [
                    "sram_wr_valid",
                    "sram_wr_strb",
                    "readback_valid",
                    "pready",
                ]
            }
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

def row(scenario_id, observed):
    return {
        "goal_id": "EQ_" + scenario_id,
        "scenario_id": scenario_id,
        "cycle": 1,
        "stimulus": {"kind": scenario_id},
        "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"ok": 1}},
        "rtl_observed": observed,
        "passed": True,
        "mismatch": "",
        "coverage_refs": [scenario_id + "_covered"],
    }

rows = [
    row(
        "SC_SRAM_PACK_NO_HOLES",
        {
            "sram_wr_valid": 1,
            "sram_wr_addr": 32,
            "sram_wr_data": 1234,
            "sram_wr_strb": 15,
            "readback_valid": 0,
            "pready": 0,
        },
    ),
    row("SC_PACKET_DROP", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 0, "pready": 0}),
    row("SC_AXI_READBACK", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 1, "readback_last": 1, "pready": 0}),
    row("SC_APB_REGISTER", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 0, "pready": 1}),
]
(ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
    "".join(json.dumps(item, sort_keys=True) + "\n" for item in rows),
    encoding="utf-8",
)
print("C003_TEMP_IP_READY root=" + str(root))
PY

python3 workflow/sim_debug/scripts/check_simulation_quality.py \
  quality_ip \
  --root "$TMP_ROOT" \
  --require-class memory_pack \
  --require-class drop \
  --require-class readback \
  --require-class register

python3 - "$TMP_ROOT" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads((Path(sys.argv[1]) / "quality_ip/sim/simulation_quality.json").read_text(encoding="utf-8"))
assert report["status"] == "pass", report
assert report["summary"]["rows"] == 4, report
for class_name in ("memory_pack", "drop", "readback", "register"):
    assert report["classes"][class_name] >= 1, report
print("C003_REPORT_PASS rows=4 classes=memory_pack,drop,readback,register")
PY

python3 -m pytest tests/test_simulation_quality_gate.py -q

echo "C003_SIM_QUALITY_PASS tmux_session=${ULW_TMUX_SESSION:-unknown}"
