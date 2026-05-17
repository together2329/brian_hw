#!/usr/bin/env python3
"""Transaction/sequence-item models for pl330realverify cocotb/pyuvm TB."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ApbTxn:
    addr: int = 0
    write: bool = False
    data: int = 0
    strb: int = 0xF
    expected_rdata: Optional[int] = None
    expected_pslverr: int = 0


@dataclass
class AxiReadTxn:
    addr: int = 0
    len_beat: int = 0
    id_val: int = 0
    resp_data: list = field(default_factory=list)
    resp_rresp: list = field(default_factory=list)


@dataclass
class AxiWriteTxn:
    addr: int = 0
    len_beat: int = 0
    id_val: int = 0
    wdata: list = field(default_factory=list)
    wstrb: list = field(default_factory=list)
    bresp: int = 0


@dataclass
class EventStimulus:
    event_vector: int = 0
    selected_bit: int = 0
    assert_delay_cycles: int = 0


@dataclass
class DmaCommand:
    channel: int = 0
    sar: int = 0
    dar: int = 0
    loop_count: int = 0
    burst_len: int = 0
    wfp_enable: bool = False
    wfp_event: int = 0
    fault_inject: bool = False
    enable_irq_complete: bool = False
    enable_irq_fault: bool = False


@dataclass
class ScoreboardEvent:
    goal_id: str = ""
    scenario_id: str = ""
    cycle: int = 0
    stimulus: dict = field(default_factory=dict)
    fl_expected: dict = field(default_factory=dict)
    rtl_observed: dict = field(default_factory=dict)
    passed: bool = False
    mismatch: str = ""
    coverage_refs: list = field(default_factory=list)
