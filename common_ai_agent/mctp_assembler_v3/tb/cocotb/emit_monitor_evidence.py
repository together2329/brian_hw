#!/usr/bin/env python3
"""Emit sim/monitor_evidence.json from GENUINE monitor runs.

NO FABRICATION: every one of the six checks is copied from a real monitor's
emitted evidence file — a cocotb test that verified the property against the
live DUT this run. The emitter NEVER hard-codes a check true; if a source
evidence file is missing or its check is not true, the corresponding check is
left false (and the gate fails), and the missing source is recorded.

Sources (each produced by a real test in the authoritative run):
  * sim/sram_write_evidence.json  (test_sram_write_monitor.sram_write_monitor):
      sram_payload_no_holes, sram_payload_only, sram_no_header_or_pad_write
      (exact strobed-address set vs the payload window over 4 content scenarios,
       incl. SC_RB_4096 full 4096 B + byte-exact readback), plus
      axi_write_protocol_pass (bvalid & bresp==OKAY on every write burst) and
      axi_read_protocol_pass (arready + rresp==OKAY + exactly one rlast on final).
  * sim/apb_desc_readback_evidence.json (test_apb_desc_readback):
      apb_per_q_readback_pass (walk the descriptor FIFO head-by-head over APB:
      STATUS.descriptor_available tracks occupancy, active_context_count
      decrements per pop, distinct head DESC words, full flag set/clear).

The six gate checks (workflow/signoff check_verification_hardening):
  sram_payload_no_holes, sram_payload_only, sram_no_header_or_pad_write,
  axi_write_protocol_pass, axi_read_protocol_pass, apb_per_q_readback_pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IP_DIR = HERE.parent.parent
IP = IP_DIR.name

SRAM_EVID = IP_DIR / "sim" / "sram_write_evidence.json"
APB_EVID = IP_DIR / "sim" / "apb_desc_readback_evidence.json"
OUT_PATH = IP_DIR / "sim" / "monitor_evidence.json"

GATE_CHECKS = (
    "sram_payload_no_holes",
    "sram_payload_only",
    "sram_no_header_or_pad_write",
    "axi_write_protocol_pass",
    "axi_read_protocol_pass",
    "apb_per_q_readback_pass",
)


def _load(path: Path) -> tuple[dict, str | None]:
    if not path.is_file():
        return {}, f"missing {path.relative_to(IP_DIR)}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return {}, f"{path.relative_to(IP_DIR)}: {exc}"


def main() -> int:
    checks: dict[str, bool] = {k: False for k in GATE_CHECKS}
    sources: dict[str, str] = {}
    problems: list[str] = []

    sram, err = _load(SRAM_EVID)
    if err:
        problems.append(err)
    else:
        sc = sram.get("checks") if isinstance(sram.get("checks"), dict) else {}
        for key in ("sram_payload_no_holes", "sram_payload_only",
                    "sram_no_header_or_pad_write", "axi_write_protocol_pass",
                    "axi_read_protocol_pass"):
            checks[key] = sc.get(key) is True
            sources[key] = str(SRAM_EVID.relative_to(IP_DIR))
        if sram.get("status") != "pass":
            problems.append(f"{SRAM_EVID.relative_to(IP_DIR)} status != pass")

    apb, err = _load(APB_EVID)
    if err:
        problems.append(err)
    else:
        checks["apb_per_q_readback_pass"] = apb.get("apb_per_q_readback_pass") is True
        sources["apb_per_q_readback_pass"] = str(APB_EVID.relative_to(IP_DIR))

    overall = all(checks.values())
    status = "pass" if overall else "fail"

    payload = {
        "ip": IP,
        "status": status,
        "checks": checks,
        "sources": sources,
        "problems": problems,
        "note": ("Each check is copied from a real monitor's evidence emitted by a "
                 "cocotb test that verified it against the live DUT this run. No "
                 "check is hand-set; a missing/false source leaves the check false."),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[emit_monitor_evidence] status={status} checks={checks} "
          f"problems={problems} -> {OUT_PATH.relative_to(IP_DIR.parent)}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
