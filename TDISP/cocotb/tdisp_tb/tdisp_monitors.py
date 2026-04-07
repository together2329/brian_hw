"""
TDISP Monitors u2014 passive observers for every output interface on tdisp_top.

Each monitor runs as an independent cocotb background coroutine that samples
DUT outputs on every clock edge (via RisingEdge + ReadOnly) and publishes
structured event records to an asyncio.Queue.

Monitor classes:
  TxMonitor         u2014 Observes DOE TX responses, parses complete messages
  StateMonitor      u2014 Tracks per-TDI FSM state transitions with logging
  IrqMonitor        u2014 Detects error IRQ rising edges per TDI
  TlpEgMonitor      u2014 Captures egress TLP filter output packets per TDI
  TlpIgMonitor      u2014 Captures ingress TLP filter output packets per TDI

All monitors are strictly passive u2014 they never drive any DUT signals.
They can coexist with drivers (e.g. TdispRespReceiver drives tx_ready while
TxMonitor passively observes the same tx_valid/tx_data/tx_last).

Usage:
    buses = TdispBuses(dut, num_tdi=2)
    mon = MonitorManager(buses, dut)
    mon.start_all()

    ev = await mon.state_monitor.get_event(timeout_cycles=1000)
    print(f"TDI {ev.tdi_idx}: {ev.old_state_name} -> {ev.new_state_name}")

    mon.stop_all()
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from cocotb.utils import get_sim_time

from tdisp_buses import (
    DoeBus, EgressTlpBus, IngressTlpBus, StatusBus, TdispBuses,
)
from tdisp_constants import (
    TDISP_MSG_HEADER_SIZE,
    TdispMsgHeader,
    parse_tdisp_message,
    tdi_state_name,
    RESP_CODE_NAMES,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Event dataclasses u2014 structured records published by each monitor
# ============================================================================

@dataclass
class TxMessageEvent:
    """A complete TDISP response message observed on DOE TX."""
    header: TdispMsgHeader
    payload: bytes
    raw: bytes
    timestamp: float  # sim time in ns

    @property
    def resp_name(self) -> str:
        return RESP_CODE_NAMES.get(
            self.header.msg_type,
            f"UNKNOWN(0x{self.header.msg_type:02x})",
        )


@dataclass
class StateTransitionEvent:
    """A per-TDI FSM state transition detected by StateMonitor."""
    tdi_idx: int
    old_state: int
    new_state: int
    timestamp: float

    @property
    def old_state_name(self) -> str:
        return tdi_state_name(self.old_state)

    @property
    def new_state_name(self) -> str:
        return tdi_state_name(self.new_state)


@dataclass
class IrqEvent:
    """An error IRQ rising-edge event on a TDI."""
    tdi_idx: int
    timestamp: float


@dataclass
class EgressTlpEvent:
    """A complete egress TLP packet observed on the filter output."""
    tdi_idx: int
    beats: List[Dict]
    rejected: bool
    timestamp: float

    @property
    def num_beats(self) -> int:
        return len(self.beats)

    @property
    def data_values(self) -> List[int]:
        return [b["out_data"] for b in self.beats]


@dataclass
class IngressTlpEvent:
    """A complete ingress TLP packet observed on the filter output."""
    tdi_idx: int
    beats: List[Dict]
    rejected: bool
    timestamp: float

    @property
    def num_beats(self) -> int:
        return len(self.beats)

    @property
    def data_values(self) -> List[int]:
        return [b["out_data"] for b in self.beats]


# ============================================================================
# TxMonitor u2014 Observes DOE TX responses (passive)
# ============================================================================

class TxMonitor:
    """Passively observes DOE TX (DUTu2192testbench) response messages.

    Collects bytes when tx_valid is asserted.  A separate driver or
    testbench is responsible for driving tx_ready u2014 this monitor does
    NOT drive any signals.

    Complete messages (terminated by tx_last) are parsed and published
    as TxMessageEvent records to an asyncio.Queue.

    Timing: samples tx_valid/tx_data/tx_last in the ReadOnly phase
    after each RisingEdge, matching the RTL registered-output timing.
    """

    def __init__(self, doe_bus: DoeBus, dut):
        self._bus = doe_bus
        self._dut = dut
        self._queue: asyncio.Queue[TxMessageEvent] = asyncio.Queue()
        self._task: Optional[cocotb.coroutine] = None
        self._msgs_observed = 0
        self._bytes_observed = 0

    # --- Lifecycle ----------------------------------------------------------

    def start(self) -> cocotb.coroutine:
        """Start the background monitor coroutine."""
        if self._task is not None:
            raise RuntimeError("TxMonitor already started")
        self._task = cocotb.start_soon(self._monitor_loop())
        return self._task

    def stop(self):
        """Kill the background monitor coroutine."""
        if self._task is not None:
            self._task.kill()
            self._task = None

    # --- Public API ---------------------------------------------------------

    async def get_event(self, timeout_cycles: int = 10000) -> TxMessageEvent:
        """Wait for the next TX message event with timeout."""
        for _ in range(timeout_cycles):
            try:
                return self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await RisingEdge(self._dut.clk)
        raise TimeoutError(
            f"TxMonitor: no message after {timeout_cycles} cycles"
        )

    @property
    def msgs_observed(self) -> int:
        return self._msgs_observed

    @property
    def bytes_observed(self) -> int:
        return self._bytes_observed

    # --- Background coroutine -----------------------------------------------

    async def _monitor_loop(self):
        bus = self._bus
        while True:
            # Wait for first valid byte of a new message
            while True:
                await RisingEdge(self._dut.clk)
                await ReadOnly()
                if int(bus.tx_valid.value):
                    break

            raw = bytearray()
            raw.append(int(bus.tx_data.value) & 0xFF)
            self._bytes_observed += 1

            # Single-byte message (unlikely but handle gracefully)
            if int(bus.tx_last.value):
                self._publish(bytes(raw))
                continue

            # Collect remaining bytes until tx_last
            while True:
                await RisingEdge(self._dut.clk)
                await ReadOnly()
                if int(bus.tx_valid.value):
                    raw.append(int(bus.tx_data.value) & 0xFF)
                    self._bytes_observed += 1
                    if int(bus.tx_last.value):
                        break

            self._publish(bytes(raw))

    def _publish(self, raw: bytes):
        self._msgs_observed += 1
        sim_time = get_sim_time("ns")

        if len(raw) < TDISP_MSG_HEADER_SIZE:
            logger.warning("TxMonitor: short message (%d bytes)", len(raw))
            hdr = TdispMsgHeader(version=0, msg_type=0)
        else:
            hdr, _ = parse_tdisp_message(raw)

        event = TxMessageEvent(
            header=hdr,
            payload=raw[TDISP_MSG_HEADER_SIZE:],
            raw=raw,
            timestamp=sim_time,
        )
        self._queue.put_nowait(event)
        logger.debug(
            "TxMonitor: msg #%d code=%s len=%d t=%.1fns",
            self._msgs_observed, event.resp_name, len(raw), sim_time,
        )


# ============================================================================
# StateMonitor u2014 Per-TDI FSM state transition tracker
# ============================================================================

class StateMonitor:
    """Monitors tdi_state_out[NUM_TDI-1:0] for FSM state transitions.

    On every clock edge, compares each TDI's current state to the previous
    value.  When a transition is detected, a StateTransitionEvent is
    published to the queue and logged at INFO level.

    The full transition history is also kept in self.transitions for
    post-run analysis.
    """

    def __init__(self, status_bus: StatusBus, dut, *, num_tdi: int = 2):
        self._bus = status_bus
        self._dut = dut
        self._num_tdi = num_tdi
        self._queue: asyncio.Queue[StateTransitionEvent] = asyncio.Queue()
        self._task: Optional[cocotb.coroutine] = None
        self._transitions: List[StateTransitionEvent] = []

    def start(self) -> cocotb.coroutine:
        if self._task is not None:
            raise RuntimeError("StateMonitor already started")
        self._task = cocotb.start_soon(self._monitor_loop())
        return self._task

    def stop(self):
        if self._task is not None:
            self._task.kill()
            self._task = None

    async def get_event(self, timeout_cycles: int = 10000
                        ) -> StateTransitionEvent:
        """Wait for the next state transition event with timeout."""
        for _ in range(timeout_cycles):
            try:
                return self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await RisingEdge(self._dut.clk)
        raise TimeoutError(
            f"StateMonitor: no transition after {timeout_cycles} cycles"
        )

    @property
    def transitions(self) -> List[StateTransitionEvent]:
        """Return a copy of all observed transitions."""
        return list(self._transitions)

    @property
    def transition_count(self) -> int:
        return len(self._transitions)

    # --- Background coroutine -----------------------------------------------

    async def _monitor_loop(self):
        # Capture initial states after first clock edge
        await RisingEdge(self._dut.clk)
        await ReadOnly()
        prev = [self._bus.get_tdi_state(i) for i in range(self._num_tdi)]

        logger.debug(
            "StateMonitor: initial states = %s",
            [tdi_state_name(s) for s in prev],
        )

        while True:
            await RisingEdge(self._dut.clk)
            await ReadOnly()
            for i in range(self._num_tdi):
                cur = self._bus.get_tdi_state(i)
                if cur != prev[i]:
                    sim_time = get_sim_time("ns")
                    ev = StateTransitionEvent(
                        tdi_idx=i,
                        old_state=prev[i],
                        new_state=cur,
                        timestamp=sim_time,
                    )
                    self._transitions.append(ev)
                    self._queue.put_nowait(ev)
                    logger.info(
                        "StateMonitor: TDI[%d] %s u2192 %s  t=%.1fns",
                        i, ev.old_state_name, ev.new_state_name, sim_time,
                    )
                prev[i] = cur


# ============================================================================
# IrqMonitor u2014 Error IRQ rising-edge detector
# ============================================================================

class IrqMonitor:
    """Monitors tdi_error_irq[NUM_TDI-1:0] for rising edges (0u21921).

    Detects assertion of error IRQs and publishes IrqEvent records.
    Deassertion (1u21920) is NOT reported u2014 only rising edges.
    """

    def __init__(self, status_bus: StatusBus, dut, *, num_tdi: int = 2):
        self._bus = status_bus
        self._dut = dut
        self._num_tdi = num_tdi
        self._queue: asyncio.Queue[IrqEvent] = asyncio.Queue()
        self._task: Optional[cocotb.coroutine] = None
        self._irq_count = 0

    def start(self) -> cocotb.coroutine:
        if self._task is not None:
            raise RuntimeError("IrqMonitor already started")
        self._task = cocotb.start_soon(self._monitor_loop())
        return self._task

    def stop(self):
        if self._task is not None:
            self._task.kill()
            self._task = None

    async def get_event(self, timeout_cycles: int = 10000) -> IrqEvent:
        """Wait for the next IRQ rising-edge event with timeout."""
        for _ in range(timeout_cycles):
            try:
                return self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await RisingEdge(self._dut.clk)
        raise TimeoutError(
            f"IrqMonitor: no IRQ after {timeout_cycles} cycles"
        )

    @property
    def irq_count(self) -> int:
        return self._irq_count

    # --- Background coroutine -----------------------------------------------

    async def _monitor_loop(self):
        await RisingEdge(self._dut.clk)
        await ReadOnly()
        prev = [self._bus.get_error_irq(i) for i in range(self._num_tdi)]

        while True:
            await RisingEdge(self._dut.clk)
            await ReadOnly()
            for i in range(self._num_tdi):
                cur = self._bus.get_error_irq(i)
                if cur and not prev[i]:
                    sim_time = get_sim_time("ns")
                    ev = IrqEvent(tdi_idx=i, timestamp=sim_time)
                    self._irq_count += 1
                    self._queue.put_nowait(ev)
                    logger.info(
                        "IrqMonitor: TDI[%d] error IRQ asserted  t=%.1fns",
                        i, sim_time,
                    )
                prev[i] = cur


# ============================================================================
# TlpEgMonitor u2014 Egress TLP filter output packet capture
# ============================================================================

class TlpEgMonitor:
    """Passively captures egress TLP packets from the filter output.

    Monitors eg_tlp_out_valid_per_tdi for each TDI.  When valid is high,
    collects the beat (out_data, out_last, xt_bit, t_bit, reject).
    A complete packet is published when out_last=1.

    RTL timing: eg_tlp_out_* signals are registered outputs from the
    filter (1-cycle pipeline).  They are stable during ReadOnly.
    """

    def __init__(self, egress_bus: EgressTlpBus, dut, *, num_tdi: int = 2):
        self._bus = egress_bus
        self._dut = dut
        self._num_tdi = num_tdi
        self._queue: asyncio.Queue[EgressTlpEvent] = asyncio.Queue()
        self._task: Optional[cocotb.coroutine] = None
        self._pkt_count = 0

    def start(self) -> cocotb.coroutine:
        if self._task is not None:
            raise RuntimeError("TlpEgMonitor already started")
        self._task = cocotb.start_soon(self._monitor_loop())
        return self._task

    def stop(self):
        if self._task is not None:
            self._task.kill()
            self._task = None

    async def get_event(self, timeout_cycles: int = 10000
                        ) -> EgressTlpEvent:
        """Wait for the next egress TLP packet event with timeout."""
        for _ in range(timeout_cycles):
            try:
                return self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await RisingEdge(self._dut.clk)
        raise TimeoutError(
            f"TlpEgMonitor: no packet after {timeout_cycles} cycles"
        )

    @property
    def pkt_count(self) -> int:
        return self._pkt_count

    # --- Background coroutine -----------------------------------------------

    async def _monitor_loop(self):
        active_beats: List[List[Dict]] = [[] for _ in range(self._num_tdi)]

        while True:
            await RisingEdge(self._dut.clk)
            await ReadOnly()

            for i in range(self._num_tdi):
                sample = self._bus.sample_output(i)

                if sample["out_valid"]:
                    active_beats[i].append(sample)

                    if sample["out_last"]:
                        self._publish(i, active_beats[i])
                        active_beats[i] = []

    def _publish(self, tdi_idx: int, beats: List[Dict]):
        self._pkt_count += 1
        sim_time = get_sim_time("ns")
        rejected = any(b.get("reject", 0) for b in beats)

        ev = EgressTlpEvent(
            tdi_idx=tdi_idx,
            beats=beats,
            rejected=rejected,
            timestamp=sim_time,
        )
        self._queue.put_nowait(ev)
        logger.debug(
            "TlpEgMonitor: TDI[%d] pkt #%d beats=%d reject=%d t=%.1fns",
            tdi_idx, self._pkt_count, len(beats), int(rejected), sim_time,
        )


# ============================================================================
# TlpIgMonitor u2014 Ingress TLP filter output packet capture
# ============================================================================

class TlpIgMonitor:
    """Passively captures ingress TLP packets from the filter output.

    Monitors ig_tlp_out_valid_per_tdi for each TDI.  Collects beats until
    out_last=1, then publishes an IngressTlpEvent.

    RTL timing: ig_tlp_out_* signals are registered outputs from the
    filter (1-cycle pipeline).  They are stable during ReadOnly.
    """

    def __init__(self, ingress_bus: IngressTlpBus, dut, *, num_tdi: int = 2):
        self._bus = ingress_bus
        self._dut = dut
        self._num_tdi = num_tdi
        self._queue: asyncio.Queue[IngressTlpEvent] = asyncio.Queue()
        self._task: Optional[cocotb.coroutine] = None
        self._pkt_count = 0

    def start(self) -> cocotb.coroutine:
        if self._task is not None:
            raise RuntimeError("TlpIgMonitor already started")
        self._task = cocotb.start_soon(self._monitor_loop())
        return self._task

    def stop(self):
        if self._task is not None:
            self._task.kill()
            self._task = None

    async def get_event(self, timeout_cycles: int = 10000
                        ) -> IngressTlpEvent:
        """Wait for the next ingress TLP packet event with timeout."""
        for _ in range(timeout_cycles):
            try:
                return self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await RisingEdge(self._dut.clk)
        raise TimeoutError(
            f"TlpIgMonitor: no packet after {timeout_cycles} cycles"
        )

    @property
    def pkt_count(self) -> int:
        return self._pkt_count

    # --- Background coroutine -----------------------------------------------

    async def _monitor_loop(self):
        active_beats: List[List[Dict]] = [[] for _ in range(self._num_tdi)]

        while True:
            await RisingEdge(self._dut.clk)
            await ReadOnly()

            for i in range(self._num_tdi):
                sample = self._bus.sample_output(i)

                if sample["out_valid"]:
                    active_beats[i].append(sample)

                    if sample["out_last"]:
                        self._publish(i, active_beats[i])
                        active_beats[i] = []

    def _publish(self, tdi_idx: int, beats: List[Dict]):
        self._pkt_count += 1
        sim_time = get_sim_time("ns")
        rejected = any(b.get("reject", 0) for b in beats)

        ev = IngressTlpEvent(
            tdi_idx=tdi_idx,
            beats=beats,
            rejected=rejected,
            timestamp=sim_time,
        )
        self._queue.put_nowait(ev)
        logger.debug(
            "TlpIgMonitor: TDI[%d] pkt #%d beats=%d reject=%d t=%.1fns",
            tdi_idx, self._pkt_count, len(beats), int(rejected), sim_time,
        )


# ============================================================================
# MonitorManager u2014 Convenience: creates and manages all monitors at once
# ============================================================================

class MonitorManager:
    """Creates and manages all TDISP monitors for a test.

    Usage:
        buses = TdispBuses(dut, num_tdi=2)
        mon = MonitorManager(buses, dut)
        mon.start_all()

        # Wait for a state transition
        ev = await mon.state_monitor.get_event()
        print(f"TDI {ev.tdi_idx}: {ev.old_state_name} -> {ev.new_state_name}")

        mon.stop_all()
    """

    def __init__(self, buses: TdispBuses, dut):
        self.dut = dut
        num_tdi = buses.status.num_tdi

        self.tx_monitor = TxMonitor(buses.doe, dut)
        self.state_monitor = StateMonitor(buses.status, dut, num_tdi=num_tdi)
        self.irq_monitor = IrqMonitor(buses.status, dut, num_tdi=num_tdi)
        self.egress_monitor = TlpEgMonitor(buses.egress, dut, num_tdi=num_tdi)
        self.ingress_monitor = TlpIgMonitor(
            buses.ingress, dut, num_tdi=num_tdi
        )
        self._started = False

    def start_all(self):
        """Start all background monitor coroutines."""
        if self._started:
            raise RuntimeError("MonitorManager already started")
        self.tx_monitor.start()
        self.state_monitor.start()
        self.irq_monitor.start()
        self.egress_monitor.start()
        self.ingress_monitor.start()
        self._started = True
        logger.info("MonitorManager: all monitors started")

    def stop_all(self):
        """Stop all background monitor coroutines."""
        self.tx_monitor.stop()
        self.state_monitor.stop()
        self.irq_monitor.stop()
        self.egress_monitor.stop()
        self.ingress_monitor.stop()
        self._started = False
        logger.info("MonitorManager: all monitors stopped")
