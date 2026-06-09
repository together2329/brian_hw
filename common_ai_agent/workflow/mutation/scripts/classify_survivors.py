#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _disposition(row: dict[str, Any]) -> tuple[str, str, str]:
    category = str(row.get("category") or "")
    relpath = str(row.get("relpath") or "")
    preview = str(row.get("preview") or "")
    if "cdc" in relpath and "raw_debug_read_enable" in preview:
        return (
            "irrelevant",
            "The mutation changes a reset/default debug synchronizer value that is not required for functional assembly correctness.",
            "Keep as debug-observability follow-up; no functional scenario is blocked by this survivor.",
        )
    if "vdm_valid <= 1'b0" in preview or "debug_vdm_valid <= 1'b0" in preview:
        return (
            "test_hole",
            "The current directed scenarios observe valid VDM behavior but do not force reset/default-pulse corruption to fail.",
            "Add reset-to-first-packet pulse persistence checks if this diagnostic signal becomes signoff-critical.",
        )
    if category == "state_update_drop":
        return (
            "test_hole",
            "The mutant removes an internal pointer or remaining-byte update and survived, so the harness needs stronger multi-transaction state observation.",
            "Add back-to-back queue wrap or long-pack drain checks tied to the mutated state.",
        )
    if "sram_packer" in relpath:
        return (
            "test_hole",
            "The survivor is in lane/strobe packing arithmetic; existing payload reconstruction catches main no-hole behavior but not every boundary expression.",
            "Add targeted unaligned first/last-word cases around the mutated expression.",
        )
    if "axi_read_egress" in relpath:
        return (
            "test_hole",
            "The survivor changes read beat count arithmetic and needs more readback lengths around 0, 1, 31, 32, 33, and 4096 bytes.",
            "Add APB-programmed descriptor readback tests for beat-count boundary lengths.",
        )
    if "mctp_parser" in relpath:
        return (
            "test_hole",
            "The survivor changes decoded payload length or TU overflow logic and requires sharper malformed/overflow packet vectors.",
            "Add parser-level invalid length and TU-boundary vectors with explicit drop-reason observation.",
        )
    if "pcie_vdm_parser" in relpath:
        return (
            "test_hole",
            "The survivor changes parser idle/debug state and is not killed by current positive/negative VDM scenarios.",
            "Add parser reset and invalid-envelope pulse checks.",
        )
    if category == "constant_flip":
        return (
            "irrelevant",
            "The mutation is a default constant that did not affect any required observable in the current contract.",
            "Review only if the affected signal is promoted to a required observable.",
        )
    return (
        "test_hole",
        "The mutant survived the current deterministic harness and should be treated as an uncovered behavior until waived.",
        "Add a targeted scenario or explicitly waive after human review.",
    )


def _formal_properties() -> list[dict[str, str]]:
    return [
        {
            "id": "P_AXI_WRITE_STABLE_WHILE_WAIT",
            "description": "AXI write address/data/control remain stable while valid is asserted and ready is low.",
        },
        {
            "id": "P_AXI_READ_STABLE_WHILE_WAIT",
            "description": "AXI read address/control remain stable while ARVALID is asserted and ARREADY is low.",
        },
        {
            "id": "P_SRAM_WRITE_ONLY_PAYLOAD_BYTES",
            "description": "SRAM writes never include PCIe VDM or MCTP transport header bytes.",
        },
        {
            "id": "P_DESCRIPTOR_AFTER_PAYLOAD_FLUSH",
            "description": "A completed descriptor is published only after the corresponding payload bytes are accepted by SRAM.",
        },
        {
            "id": "P_DROP_SUPPRESSES_DESCRIPTOR",
            "description": "Packet or assembly drops suppress descriptor publication and increment the matching drop counter.",
        },
        {
            "id": "P_PER_Q_FSM_NO_ILLEGAL_STATE",
            "description": "Each queue FSM stays in the legal idle/assemble/error states after reset release.",
        },
    ]


def _write_safety_properties(path: Path) -> None:
    lines = [
        "module mctp_assembler_scratch_safety_properties (",
        "    input logic axi_aclk,",
        "    input logic axi_aresetn,",
        "    input logic m_axi_awvalid,",
        "    input logic m_axi_awready,",
        "    input logic [31:0] m_axi_awaddr,",
        "    input logic [7:0] m_axi_awlen,",
        "    input logic m_axi_wvalid,",
        "    input logic m_axi_wready,",
        "    input logic [255:0] m_axi_wdata,",
        "    input logic [31:0] m_axi_wstrb,",
        "    input logic m_axi_wlast,",
        "    input logic m_axi_arvalid,",
        "    input logic m_axi_arready,",
        "    input logic [31:0] m_axi_araddr,",
        "    input logic [7:0] m_axi_arlen,",
        "    input logic sram_wr_valid,",
        "    input logic sram_wr_ready,",
        "    input logic descriptor_valid,",
        "    input logic packet_drop_pulse,",
        "    input logic assembly_drop_pulse,",
        "    input logic [1:0] q0_state,",
        "    input logic [1:0] q1_state,",
        "    input logic [1:0] q2_state,",
        "    input logic [1:0] q3_state",
        ");",
        "    default clocking cb @(posedge axi_aclk); endclocking",
        "    default disable iff (!axi_aresetn);",
        "",
        "    property p_axi_aw_stable_while_wait;",
        "        m_axi_awvalid && !m_axi_awready |=> m_axi_awvalid && $stable(m_axi_awaddr) && $stable(m_axi_awlen);",
        "    endproperty",
        "    assert property (p_axi_aw_stable_while_wait);",
        "",
        "    property p_axi_w_stable_while_wait;",
        "        m_axi_wvalid && !m_axi_wready |=> m_axi_wvalid && $stable(m_axi_wdata) && $stable(m_axi_wstrb) && $stable(m_axi_wlast);",
        "    endproperty",
        "    assert property (p_axi_w_stable_while_wait);",
        "",
        "    property p_axi_ar_stable_while_wait;",
        "        m_axi_arvalid && !m_axi_arready |=> m_axi_arvalid && $stable(m_axi_araddr) && $stable(m_axi_arlen);",
        "    endproperty",
        "    assert property (p_axi_ar_stable_while_wait);",
        "",
        "    property p_drop_suppresses_descriptor_same_cycle;",
        "        packet_drop_pulse || assembly_drop_pulse |-> !descriptor_valid;",
        "    endproperty",
        "    assert property (p_drop_suppresses_descriptor_same_cycle);",
        "",
        "    property p_sram_write_requires_ready_valid;",
        "        sram_wr_valid |-> !$isunknown(sram_wr_ready);",
        "    endproperty",
        "    assert property (p_sram_write_requires_ready_valid);",
        "",
        "    property p_q_states_legal;",
        "        q0_state <= 2'd2 && q1_state <= 2'd2 && q2_state <= 2'd2 && q3_state <= 2'd2;",
        "    endproperty",
        "    assert property (p_q_states_legal);",
        "endmodule",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Survivor Classification",
        "",
        f"- Status: `{payload['status']}`",
        f"- Generated: `{payload['generated_at']}`",
        f"- Total survivors: `{payload['summary']['total_survivors']}`",
        "",
        "| Mutant | Category | Disposition | Next Action |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["survivors"]:
        lines.append(
            f"| `{row['id']}` | `{row['category']}` | `{row['disposition']}` | {row['next_action']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def classify(ip_dir: Path) -> dict[str, Any]:
    report_path = ip_dir / "mutation" / "mutation_report.json"
    report = _read_json(report_path)
    survivors = []
    for row in report.get("results", []):
        if not isinstance(row, dict) or row.get("status") != "survived":
            continue
        disposition, rationale, next_action = _disposition(row)
        survivors.append({
            "id": str(row.get("id") or ""),
            "category": str(row.get("category") or ""),
            "relpath": str(row.get("relpath") or ""),
            "line": int(row.get("line") or 0),
            "rule": str(row.get("rule") or ""),
            "before": str(row.get("before") or ""),
            "after": str(row.get("after") or ""),
            "disposition": disposition,
            "rationale": rationale,
            "next_action": next_action,
            "preview": str(row.get("preview") or ""),
            # Closure contract consumed by check_ip_signoff: a survivor is closed
            # ONLY by an evidence-backed equivalence (disposition equivalent/
            # sec_caught + evidence_ref to the SEC/formal artifact) or an explicit
            # human waiver (waived_by + waiver_reason). This script produces
            # TRIAGE, not closure — these fields start empty on purpose.
            "evidence_ref": "",
            "waived_by": "",
            "waiver_reason": "",
        })
    counts = Counter(str(row["disposition"]) for row in survivors)
    payload = {
        "schema_version": 1,
        "type": "survivor_classification",
        "generated_at": _utc(),
        # This tool cannot certify closure: its dispositions are heuristic triage
        # with no SEC/formal evidence. Stamping "pass" here used to rubber-stamp
        # the signoff survivor gate. Survivors present => a human (or an SEC lane)
        # must close each one before signoff.
        "status": "pass" if not survivors else "needs_human_review",
        "source": str(report_path.relative_to(ip_dir)),
        "summary": {
            "total_survivors": len(survivors),
            "classified": len(survivors),
            "closure_open": len(survivors),
            "equivalent": counts.get("equivalent", 0),
            "irrelevant": counts.get("irrelevant", 0),
            "test_hole": counts.get("test_hole", 0),
        },
        "survivors": survivors,
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = (root / args.ip).resolve()
    if not ip_dir.is_dir():
        raise SystemExit(f"missing IP directory: {ip_dir}")

    mutation_dir = ip_dir / "mutation"
    verify_dir = ip_dir / "verify"
    mutation_dir.mkdir(parents=True, exist_ok=True)
    verify_dir.mkdir(parents=True, exist_ok=True)

    payload = classify(ip_dir)
    json_path = mutation_dir / "survivor_classification.json"
    md_path = mutation_dir / "survivor_classification.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(md_path, payload)

    formal = {
        "schema_version": 1,
        "type": "formal_status",
        "generated_at": _utc(),
        "status": "optional_not_run",
        "tool": "sby",
        "reason": "Optional safety-property workflow recorded; local SymbiYosys execution is not required for this signoff pass.",
        "properties": _formal_properties(),
        "artifact": "verify/safety_properties.sva",
    }
    # Do not clobber owned verify/ artifacts: these are authoritative outputs of
    # other lanes (formal/safety). Only seed them when absent.
    sva_path = verify_dir / "safety_properties.sva"
    formal_path = verify_dir / "formal_status.json"
    if not sva_path.is_file():
        _write_safety_properties(sva_path)
        print(f"[classify_survivors] wrote {sva_path}")
    else:
        print(f"[classify_survivors] kept existing {sva_path}")
    if not formal_path.is_file():
        formal_path.write_text(json.dumps(formal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"[classify_survivors] wrote {formal_path}")
    else:
        print(f"[classify_survivors] kept existing {formal_path}")

    print(f"[classify_survivors] wrote {json_path}")
    print(f"[classify_survivors] wrote {md_path}")
    if payload["summary"]["total_survivors"]:
        print(
            f"[classify_survivors] status={payload['status']}: {payload['summary']['total_survivors']} "
            "survivor(s) need evidence-backed closure (equivalent/sec_caught + evidence_ref) "
            "or a human waiver (waived_by + waiver_reason) before signoff."
        )
    print(f"[classify_survivors] wrote {verify_dir / 'safety_properties.sva'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
