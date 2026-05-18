"""Transaction / sequence-item definitions for the DMA scratch UI verification.

SSOT traceability:
  - io_list.interfaces  → port signal names and widths
  - function_model.transactions → transaction kinds and expected fields
  - registers.register_list     → CSR offset map
"""

from enum import IntEnum


class FsmState(IntEnum):
    IDLE = 0
    READ_REQ = 1
    WAIT_RDATA = 2
    WRITE_REQ = 3
    DONE = 4
    ERROR = 5


# ── CSR offset map (derived from SSOT registers) ──────────────────────
CSR_CTRL     = 0
CSR_STATUS   = 4
CSR_SRC_ADDR = 8
CSR_DST_ADDR = 12
CSR_LENGTH   = 16
CSR_PROGRESS = 20

VALID_CSR_OFFSETS = {CSR_CTRL, CSR_STATUS, CSR_SRC_ADDR, CSR_DST_ADDR, CSR_LENGTH, CSR_PROGRESS}

# ── CTRL register bit positions ───────────────────────────────────────
CTRL_START_BIT      = 0
CTRL_IRQ_DONE_EN    = 1
CTRL_IRQ_ERROR_EN   = 2
CTRL_SOFT_RESET     = 3

# ── STATUS register bit positions ─────────────────────────────────────
STATUS_BUSY_BIT  = 0
STATUS_DONE_BIT  = 1
STATUS_ERROR_BIT = 2


class CsrTransaction:
    """CSR request item carried over csr_if (valid/ready)."""

    def __init__(self, addr: int, is_write: bool, wdata: int = 0):
        self.addr = int(addr)
        self.is_write = bool(is_write)
        self.wdata = int(wdata) & 0xFFFFFFFF

    def __repr__(self):
        rw = "WR" if self.is_write else "RD"
        return f"CsrTxn({rw} @ 0x{self.addr:08X}, wdata=0x{self.wdata:08X})"


class CsrResponse:
    """CSR response observed on csr_rdata / csr_error."""

    def __init__(self, rdata: int = 0, error: bool = False):
        self.rdata = int(rdata) & 0xFFFFFFFF
        self.error = bool(error)

    def __repr__(self):
        err = " ERR" if self.error else ""
        return f"CsrResp(rdata=0x{self.rdata:08X}{err})"


class ReadBeat:
    """Observed read-data beat from the memory fabric."""

    def __init__(self, data: int):
        self.data = int(data) & 0xFFFFFFFF

    def __repr__(self):
        return f"ReadBeat(data=0x{self.data:08X})"


class WriteBeat:
    """Observed write beat sent to the memory fabric."""

    def __init__(self, addr: int, data: int, strb: int):
        self.addr = int(addr) & 0xFFFFFFFF
        self.data = int(data) & 0xFFFFFFFF
        self.strb = int(strb) & 0xF

    def __repr__(self):
        return f"WriteBeat(addr=0x{self.addr:08X}, data=0x{self.data:08X}, strb=0b{self.strb:04b})"


class DmaEvent:
    """Event record for scoreboard comparisons."""

    def __init__(self, cycle: int, kind: str, scenario_id: str = "",
                 fl_expected=None, rtl_observed=None, goal_id: str = ""):
        self.cycle = int(cycle)
        self.kind = str(kind)
        self.scenario_id = str(scenario_id)
        self.fl_expected = fl_expected
        self.rtl_observed = rtl_observed
        self.goal_id = str(goal_id)
        self.passed = None  # set after comparison

    def __repr__(self):
        status = "?" if self.passed is None else ("PASS" if self.passed else "FAIL")
        return (f"DmaEvent(cyc={self.cycle}, {self.kind}, {status}, "
                f"goal={self.goal_id}, sc={self.scenario_id})")
