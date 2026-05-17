#!/usr/bin/env python3
"""uart_lite_real Functional Model — deterministic emit from SSOT YAML.

This model is the behavioral oracle for rtl-gen and tb-gen.
It describes WHAT the UART computes, independent of cycle timing.
The cycle_model handles when state changes occur.

SSOT source: yaml/uart_lite_real.ssot.yaml
"""

import copy
from collections import deque


class UartLiteRealFunctionalModel:
    """Functional model for uart_lite_real — APB4 UART transceiver."""

    def __init__(self, data_width=8, fifo_depth=16):
        self.DATA_WIDTH = data_width
        self.FIFO_DEPTH = fifo_depth

        # State variables (from SSOT function_model.state_variables)
        self.tx_fifo = deque()
        self.rx_fifo = deque()
        self.tx_active = False
        self.rx_active = False
        self.baud_div = 324
        self.parity_en = False
        self.parity_odd = False
        self.stop_bits = False  # False=1 stop, True=2 stop
        self.loopback = False
        self.break_send = False

        # Control enables
        self.tx_enable = False
        self.rx_enable = False

        # Sticky status flags
        self.frame_err = False
        self.parity_err = False
        self.overrun_err = False
        self.underrun_err = False

        # Interrupt enables
        self.tx_empty_en = False
        self.rx_not_empty_en = False
        self.rx_overrun_en = False
        self.frame_err_en = False
        self.parity_err_en = False

        # Interrupt pending
        self.tx_empty_pend = False
        self.rx_not_empty_pend = False
        self.rx_overrun_pend = False
        self.frame_err_pend = False
        self.parity_err_pend = False

        # Debug counters (free-running, wrap at 0xFFFFFFFF)
        self.bytes_tx = 0
        self.bytes_rx = 0
        self.frames_errored = 0
        self.parities_errored = 0

        # TX serialization state
        self.tx_shift_reg = 0
        self.tx_bit_count = 0

        # RX deserialization state
        self.rx_shift_reg = 0
        self.rx_bit_count = 0

        # Transaction log for scoreboard
        self.transaction_log = []

    # --- Register access interface ---

    def read_register(self, offset):
        """Read a register at the given byte offset. Returns (data, error)."""
        if offset == 0x00:  # CTRL
            data = (
                (int(self.tx_enable) << 0) |
                (int(self.rx_enable) << 1) |
                (int(self.loopback) << 2) |
                (int(self.break_send) << 3) |
                (int(self.parity_en) << 4) |
                (int(self.parity_odd) << 5) |
                (int(self.stop_bits) << 6)
            )
            return (data, False)
        elif offset == 0x04:  # STAT
            data = (
                (int(self.tx_fifo_full()) << 0) |
                (int(self.tx_fifo_empty()) << 1) |
                (int(self.rx_fifo_empty()) << 2) |
                (int(self.rx_fifo_full()) << 3) |
                (int(self.tx_active) << 4) |
                (int(self.rx_active) << 5) |
                (int(self.frame_err) << 6) |
                (int(self.parity_err) << 7) |
                (int(self.overrun_err) << 8) |
                (int(self.underrun_err) << 9)
            )
            return (data, False)
        elif offset == 0x08:  # BAUD
            return (self.baud_div & 0xFFFF, False)
        elif offset == 0x10:  # RXDATA
            if self.rx_fifo:
                data = self.rx_fifo.popleft()
                self._update_rx_pend()
                return (data & ((1 << self.DATA_WIDTH) - 1), False)
            else:
                return (0x00, False)
        elif offset == 0x14:  # INTEN
            data = (
                (int(self.tx_empty_en) << 0) |
                (int(self.rx_not_empty_en) << 1) |
                (int(self.rx_overrun_en) << 2) |
                (int(self.frame_err_en) << 3) |
                (int(self.parity_err_en) << 4)
            )
            return (data, False)
        elif offset == 0x18:  # INTPEND
            data = (
                (int(self.tx_empty_pend) << 0) |
                (int(self.rx_not_empty_pend) << 1) |
                (int(self.rx_overrun_pend) << 2) |
                (int(self.frame_err_pend) << 3) |
                (int(self.parity_err_pend) << 4)
            )
            return (data, False)
        elif offset == 0x20:  # DBG_BYTES_TX
            return (self.bytes_tx & 0xFFFFFFFF, False)
        elif offset == 0x24:  # DBG_BYTES_RX
            return (self.bytes_rx & 0xFFFFFFFF, False)
        elif offset == 0x28:  # DBG_FRAMES_ERR
            return (self.frames_errored & 0xFFFFFFFF, False)
        elif offset == 0x2C:  # DBG_PARITIES_ERR
            return (self.parities_errored & 0xFFFFFFFF, False)
        elif offset >= 0x30:
            return (0, True)  # PSLVERR
        else:
            # TXDATA is write-only, CLR_STAT is W1C write-only reads as 0
            return (0, False)

    def write_register(self, offset, data):
        """Write a register at the given byte offset. Returns error."""
        if offset >= 0x30:
            return True  # PSLVERR

        if offset == 0x00:  # CTRL
            self.tx_enable = bool(data & (1 << 0))
            self.rx_enable = bool(data & (1 << 1))
            self.loopback = bool(data & (1 << 2))
            self.break_send = bool(data & (1 << 3))
            self.parity_en = bool(data & (1 << 4))
            self.parity_odd = bool(data & (1 << 5))
            self.stop_bits = bool(data & (1 << 6))
            return False
        elif offset == 0x08:  # BAUD
            self.baud_div = data & 0xFFFF
            return False
        elif offset == 0x0C:  # TXDATA
            if not self.tx_fifo_full():
                self.tx_fifo.append(data & ((1 << self.DATA_WIDTH) - 1))
                self._update_tx_pend()
            # If full, data is discarded (no error flag per SSOT assumptions)
            return False
        elif offset == 0x14:  # INTEN
            self.tx_empty_en = bool(data & (1 << 0))
            self.rx_not_empty_en = bool(data & (1 << 1))
            self.rx_overrun_en = bool(data & (1 << 2))
            self.frame_err_en = bool(data & (1 << 3))
            self.parity_err_en = bool(data & (1 << 4))
            return False
        elif offset == 0x18:  # INTPEND W1C
            if data & (1 << 0):
                self.tx_empty_pend = False
            if data & (1 << 1):
                self.rx_not_empty_pend = False
            if data & (1 << 2):
                self.rx_overrun_pend = False
            if data & (1 << 3):
                self.frame_err_pend = False
            if data & (1 << 4):
                self.parity_err_pend = False
            return False
        elif offset == 0x1C:  # CLR_STAT W1C
            if data & (1 << 0):
                self.frame_err = False
            if data & (1 << 1):
                self.parity_err = False
            if data & (1 << 2):
                self.overrun_err = False
            if data & (1 << 3):
                self.underrun_err = False
            return False
        return False

    # --- FIFO helpers ---

    def tx_fifo_full(self):
        return len(self.tx_fifo) >= self.FIFO_DEPTH

    def tx_fifo_empty(self):
        return len(self.tx_fifo) == 0

    def rx_fifo_full(self):
        return len(self.rx_fifo) >= self.FIFO_DEPTH

    def rx_fifo_empty(self):
        return len(self.rx_fifo) == 0

    # --- Interrupt computation ---

    @property
    def uart_irq(self):
        """Combined interrupt output: OR of all enabled pending sources."""
        return (
            (self.tx_empty_pend and self.tx_empty_en) or
            (self.rx_not_empty_pend and self.rx_not_empty_en) or
            (self.rx_overrun_pend and self.rx_overrun_en) or
            (self.frame_err_pend and self.frame_err_en) or
            (self.parity_err_pend and self.parity_err_en)
        )

    def _update_tx_pend(self):
        """Update tx_empty pending when TX FIFO changes."""
        if self.tx_fifo_empty():
            self.tx_empty_pend = True

    def _update_rx_pend(self):
        """Update rx_not_empty pending when RX FIFO changes."""
        if not self.rx_fifo_empty():
            self.rx_not_empty_pend = True
        else:
            self.rx_not_empty_pend = False

    # --- Parity computation ---

    def compute_parity(self, data_byte):
        """Compute parity over DATA_WIDTH bits. Returns parity bit value."""
        mask = (1 << self.DATA_WIDTH) - 1
        bits = data_byte & mask
        ones = bin(bits).count('1')
        if self.parity_odd:
            return ones % 2 == 0  # odd parity: 1 if even number of 1s
        else:
            return ones % 2 == 1  # even parity: 1 if odd number of 1s

    # --- Transaction functions (from SSOT function_model.transactions) ---

    def tx_byte(self):
        """FM_TX_BYTE: Transmit one byte from TX FIFO.

        Preconditions: tx_enable, tx_fifo not empty, not tx_active, not break_send
        Returns: list of bits on tx line (start + data + parity + stop)
        """
        assert self.tx_enable, "TX not enabled"
        assert not self.tx_fifo_empty(), "TX FIFO empty"
        assert not self.tx_active, "TX already active"
        assert not self.break_send, "Break send active"

        d = self.tx_fifo.popleft()
        mask = (1 << self.DATA_WIDTH) - 1
        d &= mask

        # Build TX bit stream
        bits = []

        # Start bit
        bits.append(0)

        # Data bits LSB-first
        for i in range(self.DATA_WIDTH):
            bits.append((d >> i) & 1)

        # Parity bit
        if self.parity_en:
            bits.append(self.compute_parity(d))

        # Stop bit(s)
        bits.append(1)  # STOP1
        if self.stop_bits:
            bits.append(1)  # STOP2

        # Side effects
        self.bytes_tx = (self.bytes_tx + 1) & 0xFFFFFFFF
        self._update_tx_pend()

        self.transaction_log.append({
            'type': 'FM_TX_BYTE',
            'data': d,
            'bits': bits,
        })

        return bits

    def rx_byte(self, rx_bits):
        """FM_RX_BYTE: Receive one byte from rx bit stream.

        Preconditions: rx_enable, not rx_active, rx_fifo not full
        Args: rx_bits — list of bit values: [start, d0..dN, parity?, stop1, stop2?]
        Returns: (received_byte, errors)
        """
        assert self.rx_enable, "RX not enabled"
        assert not self.rx_active, "RX already active"

        idx = 0

        # Start bit
        start = rx_bits[idx]
        idx += 1
        if start != 0:
            # Spurious start
            self.transaction_log.append({
                'type': 'FM_RX_BYTE_SPURIOUS',
                'result': 'spurious_start',
            })
            return (None, [])

        # Data bits LSB-first
        d = 0
        for i in range(self.DATA_WIDTH):
            if idx < len(rx_bits):
                bit = rx_bits[idx]
                d |= (bit & 1) << i
                idx += 1

        errors = []

        # Parity check
        if self.parity_en:
            if idx < len(rx_bits):
                rx_parity = rx_bits[idx]
                idx += 1
                expected_parity = self.compute_parity(d)
                if rx_parity != expected_parity:
                    self.parity_err = True
                    self.parities_errored = (self.parities_errored + 1) & 0xFFFFFFFF
                    if self.parity_err_en:
                        self.parity_err_pend = True
                    errors.append('parity_err')

        # Stop bit(s)
        stop1 = rx_bits[idx] if idx < len(rx_bits) else 0
        idx += 1
        if stop1 != 1:
            self.frame_err = True
            self.frames_errored = (self.frames_errored + 1) & 0xFFFFFFFF
            if self.frame_err_en:
                self.frame_err_pend = True
            errors.append('frame_err')

        if self.stop_bits and idx < len(rx_bits):
            stop2 = rx_bits[idx]
            idx += 1
            if stop2 != 1:
                self.frame_err = True
                self.frames_errored = (self.frames_errored + 1) & 0xFFFFFFFF
                if self.frame_err_en:
                    self.frame_err_pend = True
                errors.append('frame_err')

        # Push to RX FIFO (if space, even on error)
        if not self.rx_fifo_full():
            self.rx_fifo.append(d)
            self.bytes_rx = (self.bytes_rx + 1) & 0xFFFFFFFF
            self.rx_not_empty_pend = True
        else:
            self.overrun_err = True
            if self.rx_overrun_en:
                self.rx_overrun_pend = True
            errors.append('overrun_err')

        self.transaction_log.append({
            'type': 'FM_RX_BYTE',
            'data': d,
            'errors': errors,
        })

        return (d, errors)

    def break_send_frame(self):
        """FM_BREAK_SEND: Force tx low for one full frame duration.

        Preconditions: break_send written to 1 via CTRL
        Returns: list of bits (all 0 for frame duration)
        """
        n_bits = 1 + self.DATA_WIDTH
        if self.parity_en:
            n_bits += 1
        n_bits += 1  # STOP1
        if self.stop_bits:
            n_bits += 1

        bits = [0] * n_bits  # All low

        # Self-clear
        self.break_send = False

        self.transaction_log.append({
            'type': 'FM_BREAK_SEND',
            'duration_bits': n_bits,
            'bits': bits,
        })

        return bits

    def loopback_connect(self):
        """FM_LOOPBACK: Connect tx output to rx input internally.

        When loopback=1, transmitted bytes appear as received bytes.
        """
        assert self.loopback, "Loopback not enabled"
        self.transaction_log.append({
            'type': 'FM_LOOPBACK',
            'status': 'connected',
        })

    # --- Reset ---

    def reset(self):
        """Async reset — clear all architectural state."""
        self.tx_fifo.clear()
        self.rx_fifo.clear()
        self.tx_active = False
        self.rx_active = False
        self.baud_div = 324
        self.parity_en = False
        self.parity_odd = False
        self.stop_bits = False
        self.loopback = False
        self.break_send = False
        self.tx_enable = False
        self.rx_enable = False
        self.frame_err = False
        self.parity_err = False
        self.overrun_err = False
        self.underrun_err = False
        self.tx_empty_en = False
        self.rx_not_empty_en = False
        self.rx_overrun_en = False
        self.frame_err_en = False
        self.parity_err_en = False
        self.tx_empty_pend = False
        self.rx_not_empty_pend = False
        self.rx_overrun_pend = False
        self.frame_err_pend = False
        self.parity_err_pend = False
        self.bytes_tx = 0
        self.bytes_rx = 0
        self.frames_errored = 0
        self.parities_errored = 0
        self.tx_shift_reg = 0
        self.tx_bit_count = 0
        self.rx_shift_reg = 0
        self.rx_bit_count = 0
        self.transaction_log = []


def self_check():
    """FL model self-check: basic smoke tests."""
    m = UartLiteRealFunctionalModel()

    # Reset state
    m.reset()
    assert m.tx_fifo_empty()
    assert m.rx_fifo_empty()
    assert not m.uart_irq

    # TX single byte (FM_TX_BYTE)
    m.tx_enable = True
    m.write_register(0x0C, 0xA5)  # TXDATA = 0xA5
    bits = m.tx_byte()
    # start(0) + 8 data LSB-first + stop(1) = 10 bits
    assert bits == [0, 1, 0, 1, 0, 0, 1, 0, 1, 1], f"TX bits mismatch: {bits}"
    assert m.bytes_tx == 1

    # RX single byte (FM_RX_BYTE)
    m.rx_enable = True
    rx_bits = [0, 1, 0, 1, 0, 0, 1, 0, 1, 1]  # 0xA5
    data, errors = m.rx_byte(rx_bits)
    assert data == 0xA5, f"RX data mismatch: {data:#x}"
    assert errors == []
    assert m.bytes_rx == 1

    # TX with even parity
    m.reset()
    m.tx_enable = True
    m.parity_en = True
    m.parity_odd = False
    m.write_register(0x0C, 0xA5)
    bits = m.tx_byte()
    # 0xA5 = 10100101 has 4 ones (even) -> even parity = 0
    assert bits == [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1], f"TX parity bits: {bits}"
    assert m.bytes_tx == 1

    # RX parity error
    m.rx_enable = True
    m.parity_en = True
    m.parity_odd = True  # expect odd parity
    rx_bits = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1]  # 0xA5, parity=0 (even), but expecting odd
    data, errors = m.rx_byte(rx_bits)
    assert data == 0xA5
    assert 'parity_err' in errors
    assert m.parity_err

    # RX framing error
    m.reset()
    m.rx_enable = True
    rx_bits = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0]  # stop bit = 0
    data, errors = m.rx_byte(rx_bits)
    assert 'frame_err' in errors
    assert m.frame_err

    # Break send
    m.reset()
    m.break_send = True
    bits = m.break_send_frame()
    assert all(b == 0 for b in bits)
    assert not m.break_send  # self-clears

    # Loopback
    m.reset()
    m.loopback = True
    m.loopback_connect()

    # FIFO overrun
    m.reset()
    m.rx_enable = True
    for i in range(m.FIFO_DEPTH):
        rx_bits = [0] + [0] * m.DATA_WIDTH + [1]
        m.rx_byte(rx_bits)
    assert m.rx_fifo_full()
    # 17th byte
    rx_bits = [0] + [0] * m.DATA_WIDTH + [1]
    data, errors = m.rx_byte(rx_bits)
    assert 'overrun_err' in errors
    assert m.overrun_err
    assert len(m.rx_fifo) == m.FIFO_DEPTH  # still 16

    print("FL model self-check: ALL PASS")


if __name__ == '__main__':
    self_check()
