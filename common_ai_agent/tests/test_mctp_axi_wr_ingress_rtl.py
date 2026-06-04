from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
INGRESS_RTL = REPO / "mctp_assembler_v3" / "rtl" / "mctp_assembler_v3_axi_wr_ingress.sv"


def test_axi_wr_ingress_fsm_references_declared_state_constants() -> None:
    text = INGRESS_RTL.read_text(encoding="utf-8")
    declared = {
        match.group(1)
        for match in re.finditer(r"\blocalparam\s+(?:\[[^\]]+\]\s+)?([A-Z][A-Z0-9_]*)\b", text)
    }
    referenced = set(re.findall(r"\bS_(?:IDLE|DATA|RESP)\b", text))

    assert referenced <= declared


def test_axi_wr_ingress_clears_stale_tlp_legal_on_new_aw() -> None:
    text = INGRESS_RTL.read_text(encoding="utf-8")
    idle_aw = re.search(r"if \(aw_fire\) begin(?P<body>.*?)state\s*<=\s*ACCEPT_AW;", text, re.S)

    assert idle_aw is not None
    assert re.search(r"tlp_legal\s*<=\s*1'b0", idle_aw.group("body")) is not None


def test_axi_wr_ingress_illegal_aw_clears_tlp_legal_before_response() -> None:
    text = INGRESS_RTL.read_text(encoding="utf-8")
    accept_aw = re.search(r"ACCEPT_AW: begin(?P<body>.*?)COLLECT_W:", text, re.S)

    assert accept_aw is not None
    assert re.search(r"tlp_legal\s*<=\s*1'b0", accept_aw.group("body")) is not None
