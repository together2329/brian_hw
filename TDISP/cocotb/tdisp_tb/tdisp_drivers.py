"""
TDISP Drivers u2014 cocotb driver classes for every interface on tdisp_top.

Each driver is an independent cocotb coroutine that interfaces with one
bus functional model from tdisp_buses.py.  All drivers follow the cocotb 2.x
async/await style and use RisingEdge/ReadOnly for race-free signal access.

Driver classes:
  TdispReqDriver     u2013 Sends TDISP request messages (byte-serial DOE RX)
  TdispRespReceiver  u2013 Receives TDISP response messages (byte-serial DOE TX)
  EgressTlpDriver    u2013 Drives per-TDI egress TLP transactions
  IngressTlpDriver   u2013 Drives per-TDI ingress TLP transactions
  RegWriteDriver     u2013 Drives per-TDI register write events

Timing conventions (derived from RTL analysis):
  - DOE RX: rx_ready is combinational (always 1 except ERROR state).
            Bytes captured on rx_valid && rx_ready at posedge clk.
  - DOE TX: tx_valid/tx_data/tx_last are registered outputs from the encoder.
            Testbench drives tx_ready; transfer occurs on tx_valid && tx_ready.
  - Egress/Ingress TLP: 1-cycle registered pipeline (out_valid <= in_valid).
            Single-cycle valid/data/last per beat.
  - Reg writes: consumed on reg_write_valid && tracking_enable at posedge clk.
            Must be held for exactly 1 cycle (cleared next cycle).
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, Timer, Event, First

from tdisp_buses import (
    DoeBus, RegWriteBus, EgressTlpBus, IngressTlpBus,
    TdispBuses,
)
from tdisp_constants import (
    TDISP_MSG_HEADER_SIZE,
    TdispMsgHeader,
    build_tdisp_message,
    parse_tdisp_message,
    RespCode,
    ReqCode,
    unpack_error_resp,
    REQ_CODE_NAMES,
    RESP_CODE_NAMES,
)

logger = logging.getLogger(__name__)


# ============================================================================
# TdispReqDriver u2014 Sends TDISP request messages over DOE RX transport
# ============================================================================

class TdispReqDriver:
    """Sends complete TDISP request messages byte-by-byte over the DOE RX
    (testbenchu2192DUT) AXI-Stream-like interface.

    The driver maintains an internal FIFO of outgoing messages.  A background
    coroutine drains the FIFO, sending one byte per clock cycle when the DUT
    asserts rx_ready.  Backpressure is handled naturally by waiting for
    rx_ready on each beat.

    Usage:
        driver = TdispReqDriver(doe_bus, dut)
        await driver.start()              # launches background drain coroutine
        await driver.send_message(msg_bytes)
        resp_hdr, resp_payload = await driver.send_and_wait(msg_bytes, receiver)
    """

    def __init__(self, doe_bus: DoeBus, dut):
        self._bus = doe_bus
        self._dut = dut
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._send_event = Event()
        self._task: Optional[cocotb.coroutine] = None
        self._idle = True
        self._bytes_sent = 0

    # --- Lifecycle ----------------------------------------------------------

    def start(self) -> cocotb.coroutine:
        """Start the background drain coroutine. Returns the task handle."""
        if self._task is not None:
            raise RuntimeError("TdispReqDriver already started")
        self._task = cocotb.start_soon(self._drain_loop())
        return self._task

    def stop(self):
        """Kill the background drain coroutine."""
        if self._task is not None:
            self._task.kill()
            self._task = None

    # --- Public API ---------------------------------------------------------

    async def send_message(self, msg: bytes):
        """Enqueue a complete TDISP message (header + payload) for sending.

        Returns immediately after enqueuing.  Use wait_drained() or
        wait_sent() to synchronize.
        """
        if len(msg) < TDISP_MSG_HEADER_SIZE:
            raise ValueError(
                f"Message too short: {len(msg)} bytes, "
                f"need at least {TDISP_MSG_HEADER_SIZE}"
            )
        await self._queue.put(msg)

    async def send_request(self, req_code: int, interface_id: int,
                           payload: bytes = b'') -> None:
        """Build and send a TDISP request message.

        Convenience wrapper around send_message() that constructs the header.
        """
        msg = build_tdisp_message(req_code, interface_id, payload)
        await self.send_message(msg)

    async def wait_sent(self, timeout_cycles: int = 10000):
        """Wait until all queued messages have been fully transmitted."""
        for _ in range(timeout_cycles):
            if self._queue.empty() and self._idle:
                return
            await RisingEdge(self._dut.clk)
        raise TimeoutError("TdispReqDriver: timed out waiting for queue drain")

    async def send_and_wait(self, msg: bytes,
                            timeout_cycles: int = 10000):
        """Send a message and wait until it has been fully clocked out."""
        await self.send_message(msg)
        await self.wait_sent(timeout_cycles)

    # --- Background drain coroutine -----------------------------------------

    async def _drain_loop(self):
        """Background loop: dequeue messages and send byte-by-byte."""
        while True:
            # Wait for a message in the queue
            msg = await self._queue.get()
            self._idle = False
            await self._send_bytes(msg)
            self._idle = True
            self._send_event.set()
            self._send_event.clear()

    async def _send_bytes(self, msg: bytes):
        """Send all bytes of a message over the DOE RX bus.

        Protocol (from tdisp_msg_codec RTL):
          - rx_ready is combinational (1 except in PARSE_ERROR)
          - Byte captured when rx_valid && rx_ready at posedge clk
          - rx_last asserted on the final byte

        Timing: drive signals AFTER posedge clk (in the delta cycle
        before the next edge) so they are sampled at the next rising edge.
        """
        bus = self._bus
        n = len(msg)

        for i, byte_val in enumerate(msg):
            is_last = (i == n - 1)

            # Wait for clock edge then drive
            await RisingEdge(self._dut.clk)

            bus.rx_data.value = byte_val & 0xFF
            bus.rx_valid.value = 1
            bus.rx_last.value = int(is_last)

            # Wait for DUT to accept (rx_ready)
            # rx_ready is usually 1, but we check to support backpressure
            for _ in range(1000):
                await ReadOnly()
                if int(bus.rx_ready.value):
                    break
                await RisingEdge(self._dut.clk)
            else:
                raise TimeoutError(
                    f"TdispReqDriver: rx_ready stayed low for 1000 cycles "
                    f"at byte {i}/{n}"
                )
            self._bytes_sent += 1

        # Deassert valid after last byte transfer
        await RisingEdge(self._dut.clk)
        bus.rx_valid.value = 0
        bus.rx_last.value = 0


# ============================================================================
# TdispRespReceiver u2014 Receives TDISP response messages from DOE TX transport
# ============================================================================

@dataclass
class TdispResponse:
    """Parsed TDISP response message."""
    header: TdispMsgHeader
    payload: bytes
    raw: bytes


class TdispRespReceiver:
    """Receives complete TDISP response messages from the DOE TX
    (DUTu2192testbench) AXI-Stream-like interface.

    A background coroutine continuously monitors tx_valid and collects bytes
    until tx_last is asserted.  Completed messages are placed into an
    asyncio.Queue for test code to consume.

    Usage:
        receiver = TdispRespReceiver(doe_bus, dut)
        await receiver.start()
        resp = await receiver.get_response(timeout_cycles=5000)
        print(f"Response code: {hex(resp.header.msg_type)}")
    """

    def __init__(self, doe_bus: DoeBus, dut):
        self._bus = doe_bus
        self._dut = dut
        self._queue: asyncio.Queue[TdispResponse] = asyncio.Queue()
        self._task: Optional[cocotb.coroutine] = None
        self._bytes_received = 0
        self._msgs_received = 0

    # --- Lifecycle ----------------------------------------------------------

    def start(self) -> cocotb.coroutine:
        """Start the background receive coroutine."""
        if self._task is not None:
            raise RuntimeError("TdispRespReceiver already started")
        self._task = cocotb.start_soon(self._receive_loop())
        return self._task

    def stop(self):
        """Kill the background receive coroutine."""
        if self._task is not None:
            self._task.kill()
            self._task = None

    # --- Public API ---------------------------------------------------------

    async def get_response(self,
                           timeout_cycles: int = 10000
                           ) -> TdispResponse:
        """Wait for and return the next TDISP response message.

        Raises TimeoutError if no response arrives within timeout_cycles.
        """
        # Poll with timeout
        for _ in range(timeout_cycles):
            try:
                return self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await RisingEdge(self._dut.clk)

        raise TimeoutError(
            f"TdispRespReceiver: no response after {timeout_cycles} cycles"
        )

    async def wait_response(self, timeout_cycles: int = 10000
                            ) -> TdispResponse:
        """Alias for get_response()."""
        return await self.get_response(timeout_cycles)

    @property
    def msgs_received(self) -> int:
        return self._msgs_received

    @property
    def bytes_received(self) -> int:
        return self._bytes_received

    # --- Background receive coroutine ---------------------------------------

    async def _receive_loop(self):
        """Background loop: collect TX bytes into complete messages."""
        while True:
            msg = await self._collect_message()
            if msg is not None:
                await self._queue.put(msg)

    async def _collect_message(self) -> Optional[TdispResponse]:
        """Collect bytes until tx_last, then parse into TdispResponse.

        Protocol (from tdisp_msg_codec encoder RTL):
          - tx_valid is registered, asserted while encoder is in ENC_HDR/ENC_PAYLOAD
          - tx_last asserted on final byte
          - Transfer occurs when tx_valid && tx_ready at posedge clk
        """
        bus = self._bus
        raw = bytearray()

        # Drive tx_ready continuously (testbench always accepts)
        bus.tx_ready.value = 1

        # Wait for first valid byte
        while True:
            await RisingEdge(self._dut.clk)
            await ReadOnly()
            if int(bus.tx_valid.value):
                break

        # Collect bytes
        while True:
            await ReadOnly()
            byte_val = int(bus.tx_valid.value) and int(bus.tx_data.value)
            last = int(bus.tx_last.value)
            valid = int(bus.tx_valid.value)

            if valid:
                raw.append(int(bus.tx_data.value) & 0xFF)
                self._bytes_received += 1

                if last:
                    break

            await RisingEdge(self._dut.clk)

        # Wait one more edge to ensure clean state
        await RisingEdge(self._dut.clk)

        self._msgs_received += 1

        # Parse the message
        if len(raw) < TDISP_MSG_HEADER_SIZE:
            logger.warning(
                "TdispRespReceiver: short message (%d bytes), treating as raw",
                len(raw),
            )
            hdr = TdispMsgHeader(version=0, msg_type=0)
            return TdispResponse(header=hdr, payload=bytes(raw), raw=bytes(raw))

        header, payload = parse_tdisp_message(bytes(raw))
        resp = TdispResponse(header=header, payload=payload, raw=bytes(raw))

        resp_name = RESP_CODE_NAMES.get(header.msg_type,
                                         f"UNKNOWN(0x{header.msg_type:02x})")
        logger.debug(
            "RX response: code=%s iface_id=0x%024x payload_len=%d",
            resp_name, header.interface_id, len(payload),
        )

        return resp


# ============================================================================
# EgressTlpDriver u2014 Drives egress TLP transactions (TDI as Requester)
# ============================================================================

@dataclass
class EgressTlpPacket:
    """Represents a single egress TLP transaction for driving."""
    data: int = 0
    last: bool = True
    is_memory_req: bool = False
    is_completion: bool = False
    is_msi: bool = False
    is_msix: bool = False
    is_msix_locked: bool = False
    is_ats_request: bool = False
    is_vdm: bool = False
    is_io_req: bool = False
    addr_type: int = 0
    access_tee_mem: bool = False
    access_non_tee_mem: bool = False


class EgressTlpDriver:
    """Drives per-TDI egress TLP transactions into tdisp_top.

    The TLP filter has a 1-cycle registered pipeline:
      eg_tlp_out_valid <= eg_tlp_valid   (at posedge clk)

    Each beat is a single-cycle valid pulse with all metadata flags.
    Multi-beat TLPs are sent as consecutive beats with last=True on the
    final beat.

    Usage:
        driver = EgressTlpDriver(buses.egress, dut)
        pkt = EgressTlpPacket(data=0xDEAD, last=True, is_memory_req=True)
        await driver.send_beat(tdi_idx=0, pkt)
    """

    def __init__(self, egress_bus: EgressTlpBus, dut):
        self._bus = egress_bus
        self._dut = dut

    async def send_beat(self, tdi_idx: int, pkt: EgressTlpPacket):
        """Send a single TLP beat for the given TDI.

        Drives all input signals, holds them for one clock cycle (posedge clk),
        then clears valid.  The DUT registers the inputs at the next rising
        edge, so the filter output appears one cycle later.
        """
        # Clear all TDI inputs first to avoid cross-contamination
        self._bus.clear_all_inputs()

        await RisingEdge(self._dut.clk)

        # Drive the beat
        self._bus.drive_input(
            tdi_idx,
            valid=True,
            data=pkt.data,
            last=pkt.last,
            is_memory_req=pkt.is_memory_req,
            is_completion=pkt.is_completion,
            is_msi=pkt.is_msi,
            is_msix=pkt.is_msix,
            is_msix_locked=pkt.is_msix_locked,
            is_ats_request=pkt.is_ats_request,
            is_vdm=pkt.is_vdm,
            is_io_req=pkt.is_io_req,
            addr_type=pkt.addr_type,
            access_tee_mem=pkt.access_tee_mem,
            access_non_tee_mem=pkt.access_non_tee_mem,
        )

        # Hold for one cycle u2014 DUT samples at next posedge clk
        await RisingEdge(self._dut.clk)

        # Deassert valid
        self._bus.clear_input(tdi_idx)

    async def send_packet(self, tdi_idx: int,
                          beats: List[EgressTlpPacket]):
        """Send a multi-beat TLP packet for the given TDI.

        Sends each beat in sequence with back-to-back valid assertions.
        The last beat must have last=True.
        """
        if not beats:
            return

        # Clear all inputs
        self._bus.clear_all_inputs()

        for beat in beats:
            await RisingEdge(self._dut.clk)
            self._bus.drive_input(
                tdi_idx,
                valid=True,
                data=beat.data,
                last=beat.last,
                is_memory_req=beat.is_memory_req,
                is_completion=beat.is_completion,
                is_msi=beat.is_msi,
                is_msix=beat.is_msix,
                is_msix_locked=beat.is_msix_locked,
                is_ats_request=beat.is_ats_request,
                is_vdm=beat.is_vdm,
                is_io_req=beat.is_io_req,
                addr_type=beat.addr_type,
                access_tee_mem=beat.access_tee_mem,
                access_non_tee_mem=beat.access_non_tee_mem,
            )

        # Deassert after last beat
        await RisingEdge(self._dut.clk)
        self._bus.clear_input(tdi_idx)

    async def send_idle(self, tdi_idx: int, cycles: int = 1):
        """Drive idle (valid=0) for a number of cycles on a TDI."""
        self._bus.clear_input(tdi_idx)
        for _ in range(cycles):
            await RisingEdge(self._dut.clk)


# ============================================================================
# IngressTlpDriver u2014 Drives ingress TLP transactions (TDI as Completer)
# ============================================================================

@dataclass
class IngressTlpPacket:
    """Represents a single ingress TLP transaction for driving."""
    data: int = 0
    last: bool = True
    xt_bit_in: bool = False
    t_bit_in: bool = False
    is_memory_req: bool = False
    is_completion: bool = False
    is_vdm: bool = False
    is_ats_request: bool = False
    target_is_non_tee_mem: bool = False
    on_bound_stream: bool = False
    ide_required: bool = False
    msix_table_locked: bool = False


class IngressTlpDriver:
    """Drives per-TDI ingress TLP transactions into tdisp_top.

    Same 1-cycle registered pipeline as egress:
      ig_tlp_out_valid <= ig_tlp_valid   (at posedge clk)

    Usage:
        driver = IngressTlpDriver(buses.ingress, dut)
        pkt = IngressTlpPacket(data=0xBEEF, last=True, is_memory_req=True,
                               xt_bit_in=True)
        await driver.send_beat(tdi_idx=0, pkt)
    """

    def __init__(self, ingress_bus: IngressTlpBus, dut):
        self._bus = ingress_bus
        self._dut = dut

    async def send_beat(self, tdi_idx: int, pkt: IngressTlpPacket):
        """Send a single ingress TLP beat for the given TDI."""
        self._bus.clear_all_inputs()

        await RisingEdge(self._dut.clk)

        self._bus.drive_input(
            tdi_idx,
            valid=True,
            data=pkt.data,
            last=pkt.last,
            xt_bit_in=pkt.xt_bit_in,
            t_bit_in=pkt.t_bit_in,
            is_memory_req=pkt.is_memory_req,
            is_completion=pkt.is_completion,
            is_vdm=pkt.is_vdm,
            is_ats_request=pkt.is_ats_request,
            target_is_non_tee_mem=pkt.target_is_non_tee_mem,
            on_bound_stream=pkt.on_bound_stream,
            ide_required=pkt.ide_required,
            msix_table_locked=pkt.msix_table_locked,
        )

        await RisingEdge(self._dut.clk)
        self._bus.clear_input(tdi_idx)

    async def send_packet(self, tdi_idx: int,
                          beats: List[IngressTlpPacket]):
        """Send a multi-beat ingress TLP packet."""
        if not beats:
            return

        self._bus.clear_all_inputs()

        for beat in beats:
            await RisingEdge(self._dut.clk)
            self._bus.drive_input(
                tdi_idx,
                valid=True,
                data=beat.data,
                last=beat.last,
                xt_bit_in=beat.xt_bit_in,
                t_bit_in=beat.t_bit_in,
                is_memory_req=beat.is_memory_req,
                is_completion=beat.is_completion,
                is_vdm=beat.is_vdm,
                is_ats_request=beat.is_ats_request,
                target_is_non_tee_mem=beat.target_is_non_tee_mem,
                on_bound_stream=beat.on_bound_stream,
                ide_required=beat.ide_required,
                msix_table_locked=beat.msix_table_locked,
            )

        await RisingEdge(self._dut.clk)
        self._bus.clear_input(tdi_idx)

    async def send_idle(self, tdi_idx: int, cycles: int = 1):
        """Drive idle (valid=0) for a number of cycles."""
        self._bus.clear_input(tdi_idx)
        for _ in range(cycles):
            await RisingEdge(self._dut.clk)


# ============================================================================
# RegWriteDriver u2014 Drives per-TDI register write events
# ============================================================================

@dataclass
class RegWriteEvent:
    """A single register write event for one TDI."""
    addr: int
    data: int
    mask: int = 0xF


class RegWriteDriver:
    """Drives per-TDI register write events into tdisp_top.

    From RTL analysis of tdisp_reg_tracker:
      - Writes consumed on reg_write_valid && tracking_enable at posedge clk
      - Must hold valid for exactly 1 cycle, then deassert

    The driver guarantees single-cycle pulse timing: drive addr/data/mask/valid
    before the rising edge, sample one cycle later, then clear valid.

    Usage:
        driver = RegWriteDriver(buses.regs, dut)
        evt = RegWriteEvent(addr=0x004, data=0x0007)
        await driver.write(tdi_idx=0, evt)
    """

    def __init__(self, reg_bus: RegWriteBus, dut):
        self._bus = reg_bus
        self._dut = dut
        self._writes_sent = 0

    async def write(self, tdi_idx: int, evt: RegWriteEvent):
        """Send a single register write event for one TDI.

        Timing:
          1. Clear all valid bits (safe starting state)
          2. Wait for rising edge
          3. Drive addr, data, mask, valid=1 for target TDI
          4. Wait for rising edge (DUT samples)
          5. Clear valid=0
          6. Wait for rising edge (clean deassert)
        """
        # Ensure clean state
        self._bus.clear_all()

        await RisingEdge(self._dut.clk)

        # Drive the write
        self._bus.drive_write(
            tdi_idx,
            addr=evt.addr,
            data=evt.data,
            mask=evt.mask,
        )

        # Hold for one cycle u2014 DUT samples at next posedge clk
        await RisingEdge(self._dut.clk)

        # Clear valid u2014 single-cycle pulse
        self._bus.clear_all()

        # Wait one more edge to ensure deassert is captured
        await RisingEdge(self._dut.clk)

        self._writes_sent += 1

    async def write_multiple(self, writes: List[tuple]):
        """Send multiple register writes in sequence.

        Each tuple is (tdi_idx, RegWriteEvent).
        """
        for tdi_idx, evt in writes:
            await self.write(tdi_idx, evt)

    async def write_raw(self, tdi_idx: int, *,
                        addr: int, data: int, mask: int = 0xF):
        """Convenience: send a register write without constructing a dataclass."""
        await self.write(tdi_idx, RegWriteEvent(addr=addr, data=data,
                                                 mask=mask))

    @property
    def writes_sent(self) -> int:
        return self._writes_sent


# ============================================================================
# DriverManager u2014 Convenience: creates and manages all drivers at once
# ============================================================================

class DriverManager:
    """Creates and manages all TDISP drivers for a test.

    Usage:
        from tdisp_buses import TdispBuses

        buses = TdispBuses(dut, num_tdi=2)
        dm = DriverManager(buses, dut)
        await dm.start_all()

        # Send a GET_VERSION request
        from tdisp_constants import ReqCode, make_interface_id
        await dm.req_driver.send_request(
            ReqCode.GET_TDISP_VERSION,
            make_interface_id(tdi_index=0),
        )
        await dm.req_driver.wait_sent()

        # Receive the response
        resp = await dm.resp_receiver.get_response()

        # Stop when done
        await dm.stop_all()
    """

    def __init__(self, buses: TdispBuses, dut):
        self.dut = dut
        self.req_driver = TdispReqDriver(buses.doe, dut)
        self.resp_receiver = TdispRespReceiver(buses.doe, dut)
        self.egress_driver = EgressTlpDriver(buses.egress, dut)
        self.ingress_driver = IngressTlpDriver(buses.ingress, dut)
        self.reg_driver = RegWriteDriver(buses.regs, dut)
        self._started = False

    async def start_all(self):
        """Start all background driver coroutines."""
        if self._started:
            raise RuntimeError("DriverManager already started")
        self.req_driver.start()
        self.resp_receiver.start()
        self._started = True
        logger.info("DriverManager: all drivers started")

    async def stop_all(self):
        """Stop all background driver coroutines."""
        self.req_driver.stop()
        self.resp_receiver.stop()
        self._started = False
        logger.info("DriverManager: all drivers stopped")

    async def send_req_and_get_resp(self, req_code: int,
                                     interface_id: int,
                                     payload: bytes = b'',
                                     send_timeout: int = 10000,
                                     resp_timeout: int = 10000
                                     ) -> TdispResponse:
        """Convenience: send a request and wait for its response.

        Combines send_request(), wait_sent(), and get_response().
        """
        await self.req_driver.send_request(req_code, interface_id, payload)
        await self.req_driver.wait_sent(timeout_cycles=send_timeout)
        return await self.resp_receiver.get_response(
            timeout_cycles=resp_timeout
        )
