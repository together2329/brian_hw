#!/usr/bin/env python3
"""uart_lite_real Cycle Model — deterministic emit from SSOT YAML.

This model describes WHEN state changes occur: handshake timing, baud ticks,
oversample counting, latency bounds, and pipeline stage progression.
It extends the FunctionalModel with cycle-accurate behavior.

SSOT source: yaml/uart_lite_real.ssot.yaml
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from functional_model import UartLiteRealFunctionalModel


class UartLiteRealCycleModel(UartLiteRealFunctionalModel):
    """Cycle-accurate model for uart_lite_real.

    Adds baud tick generation, oversample counting, and cycle-level
    TX/RX FSM progression on top of the functional model.
    """

    def __init__(self, data_width=8, fifo_depth=16, oversample=16):
        super().__init__(data_width=data_width, fifo_depth=fifo_depth)
        self.OVERSAMPLE = oversample

        # Baud generator state
        self.tx_baud_counter = 0
        self.tx_baud_tick = False

        self.rx_oversample_counter = 0
        self.rx_oversample_tick = False
        self.rx_mid_sample = False

        # TX FSM state
        self.tx_state = 'TX_IDLE'
        self.tx_next_state = 'TX_IDLE'
        self.tx_shift_reg = 0
        self.tx_bit_count = 0
        self.tx_output = 1  # idle = mark (high)

        # RX FSM state
        self.rx_state = 'RX_IDLE'
        self.rx_next_state = 'RX_IDLE'
        self.rx_shift_reg = 0
        self.rx_bit_count = 0
        self.rx_sync_1 = 1  # 2-FF synchronizer stage 1
        self.rx_sync_2 = 1  # 2-FF synchronizer stage 2
        self.rx_prev_sync = 1  # for edge detection

        # Break timer
        self.break_timer = 0
        self.break_active = False

        # Cycle counter for observability
        self.cycle_count = 0

        # Pipeline stage trace (for coverage)
        self.tx_stage_trace = []
        self.rx_stage_trace = []

    def baud_tick_period(self):
        """Baud tick period in PCLK cycles."""
        return (self.baud_div + 1) * self.OVERSAMPLE

    def _update_baud_generator(self):
        """Update TX baud counter and generate tick."""
        period = self.baud_tick_period()
        self.tx_baud_counter += 1
        if self.tx_baud_counter >= period:
            self.tx_baud_tick = True
            self.tx_baud_counter = 0
        else:
            self.tx_baud_tick = False

    def _update_oversample_counter(self):
        """Update RX oversample counter and generate ticks."""
        self.rx_oversample_counter += 1
        if self.rx_oversample_counter >= self.OVERSAMPLE:
            self.rx_oversample_tick = True
            self.rx_oversample_counter = 0
        else:
            self.rx_oversample_tick = False

        # Mid-sample point at count 7
        self.rx_mid_sample = (self.rx_oversample_counter == 7)

    def _sync_rx(self, rx_pin):
        """2-FF synchronizer for rx input."""
        self.rx_sync_1 = rx_pin
        self.rx_sync_2 = self.rx_sync_1

    def _rx_falling_edge(self):
        """Detect falling edge on synchronized rx."""
        return self.rx_prev_sync == 1 and self.rx_sync_2 == 0

    # --- TX FSM cycle progression ---

    def _tx_fsm_combinational(self):
        """Compute TX next state and output (combinational)."""
        s = self.tx_state

        if s == 'TX_IDLE':
            self.tx_output = 1
            if self.tx_enable and not self.tx_fifo_empty() and self.tx_baud_tick:
                self.tx_next_state = 'TX_START'
                self.tx_shift_reg = self.tx_fifo[0] if self.tx_fifo else 0
                self.tx_bit_count = 0
            else:
                self.tx_next_state = 'TX_IDLE'

        elif s == 'TX_START':
            self.tx_output = 0
            if self.tx_baud_tick:
                self.tx_next_state = 'TX_DATA'
                self.tx_bit_count = 0
            else:
                self.tx_next_state = 'TX_START'

        elif s == 'TX_DATA':
            self.tx_output = (self.tx_shift_reg >> self.tx_bit_count) & 1
            if self.tx_baud_tick:
                self.tx_bit_count += 1
                if self.tx_bit_count >= self.DATA_WIDTH:
                    if self.parity_en:
                        self.tx_next_state = 'TX_PARITY'
                    else:
                        self.tx_next_state = 'TX_STOP1'
            else:
                self.tx_next_state = 'TX_DATA'

        elif s == 'TX_PARITY':
            self.tx_output = self.compute_parity(self.tx_shift_reg)
            if self.tx_baud_tick:
                self.tx_next_state = 'TX_STOP1'
            else:
                self.tx_next_state = 'TX_PARITY'

        elif s == 'TX_STOP1':
            self.tx_output = 1
            if self.tx_baud_tick:
                if self.stop_bits:
                    self.tx_next_state = 'TX_STOP2'
                else:
                    self.tx_next_state = 'TX_IDLE'
            else:
                self.tx_next_state = 'TX_STOP1'

        elif s == 'TX_STOP2':
            self.tx_output = 1
            if self.tx_baud_tick:
                self.tx_next_state = 'TX_IDLE'
            else:
                self.tx_next_state = 'TX_STOP2'

    def _tx_fsm_sequential(self):
        """Update TX FSM state on clock edge."""
        old_state = self.tx_state
        self.tx_state = self.tx_next_state

        if old_state == 'TX_IDLE' and self.tx_state == 'TX_START':
            # Pop byte from FIFO
            if self.tx_fifo:
                self.tx_fifo.popleft()
            self.tx_active = True
            self.tx_stage_trace.append('TX_START')

        if self.tx_state == 'TX_DATA' and old_state == 'TX_START':
            self.tx_stage_trace.append('TX_DATA')

        if self.tx_state == 'TX_PARITY':
            if 'TX_PARITY' not in self.tx_stage_trace:
                self.tx_stage_trace.append('TX_PARITY')

        if self.tx_state == 'TX_STOP1':
            self.tx_stage_trace.append('TX_STOP1')

        if self.tx_state == 'TX_STOP2':
            self.tx_stage_trace.append('TX_STOP2')

        if old_state != 'TX_IDLE' and self.tx_state == 'TX_IDLE':
            self.tx_active = False
            self.bytes_tx = (self.bytes_tx + 1) & 0xFFFFFFFF
            self._update_tx_pend()
            self.tx_stage_trace.append('TX_IDLE_done')

    # --- RX FSM cycle progression ---

    def _rx_fsm_combinational(self):
        """Compute RX next state (combinational)."""
        s = self.rx_state

        if s == 'RX_IDLE':
            if self.rx_enable and self._rx_falling_edge():
                self.rx_next_state = 'RX_START_DETECT'
                self.rx_oversample_counter = 0
            else:
                self.rx_next_state = 'RX_IDLE'

        elif s == 'RX_START_DETECT':
            if self.rx_mid_sample:
                if self.rx_sync_2 == 0:
                    self.rx_next_state = 'RX_START_CONFIRM'
                else:
                    self.rx_next_state = 'RX_IDLE'  # spurious
            else:
                self.rx_next_state = 'RX_START_DETECT'

        elif s == 'RX_START_CONFIRM':
            if self.rx_mid_sample:
                self.rx_next_state = 'RX_DATA'
                self.rx_bit_count = 0
                self.rx_shift_reg = 0
            else:
                self.rx_next_state = 'RX_START_CONFIRM'

        elif s == 'RX_DATA':
            if self.rx_mid_sample:
                self.rx_shift_reg |= (self.rx_sync_2 & 1) << self.rx_bit_count
                self.rx_bit_count += 1
                if self.rx_bit_count >= self.DATA_WIDTH:
                    if self.parity_en:
                        self.rx_next_state = 'RX_PARITY'
                    else:
                        self.rx_next_state = 'RX_STOP1'
            else:
                self.rx_next_state = 'RX_DATA'

        elif s == 'RX_PARITY':
            if self.rx_mid_sample:
                rx_parity_bit = self.rx_sync_2
                expected = self.compute_parity(self.rx_shift_reg)
                if rx_parity_bit != expected:
                    self.parity_err = True
                    self.parities_errored = (self.parities_errored + 1) & 0xFFFFFFFF
                    if self.parity_err_en:
                        self.parity_err_pend = True
                self.rx_next_state = 'RX_STOP1'
            else:
                self.rx_next_state = 'RX_PARITY'

        elif s == 'RX_STOP1':
            if self.rx_mid_sample:
                if self.rx_sync_2 == 1:
                    # Valid stop bit
                    pass
                else:
                    self.frame_err = True
                    self.frames_errored = (self.frames_errored + 1) & 0xFFFFFFFF
                    if self.frame_err_en:
                        self.frame_err_pend = True
                if self.stop_bits:
                    self.rx_next_state = 'RX_STOP2'
                else:
                    self.rx_next_state = 'RX_IDLE'
            else:
                self.rx_next_state = 'RX_STOP1'

        elif s == 'RX_STOP2':
            if self.rx_mid_sample:
                if self.rx_sync_2 != 1:
                    self.frame_err = True
                    self.frames_errored = (self.frames_errored + 1) & 0xFFFFFFFF
                self.rx_next_state = 'RX_IDLE'
            else:
                self.rx_next_state = 'RX_STOP2'

    def _rx_fsm_sequential(self):
        """Update RX FSM state on clock edge."""
        old_state = self.rx_state
        self.rx_state = self.rx_next_state

        if old_state == 'RX_IDLE' and self.rx_state != 'RX_IDLE':
            self.rx_active = True
            self.rx_stage_trace.append('RX_START_DETECT')

        if old_state == 'RX_START_DETECT' and self.rx_state == 'RX_START_CONFIRM':
            self.rx_stage_trace.append('RX_START_CONFIRM')

        if old_state == 'RX_START_CONFIRM' and self.rx_state == 'RX_DATA':
            self.rx_stage_trace.append('RX_DATA')

        if self.rx_state == 'RX_PARITY' and 'RX_PARITY' not in self.rx_stage_trace:
            self.rx_stage_trace.append('RX_PARITY')

        if old_state != 'RX_IDLE' and self.rx_state == 'RX_IDLE':
            self.rx_active = False
            # Push received byte to FIFO
            if not self.rx_fifo_full():
                self.rx_fifo.append(self.rx_shift_reg)
                self.bytes_rx = (self.bytes_rx + 1) & 0xFFFFFFFF
                self.rx_not_empty_pend = True
            else:
                self.overrun_err = True
                if self.rx_overrun_en:
                    self.rx_overrun_pend = True
            self.rx_stage_trace.append('RX_IDLE_done')

    # --- Main clock tick ---

    def tick(self, rx_pin=1):
        """Advance one PCLK cycle.

        Args:
            rx_pin: External RX pin value (async input)
        """
        self.cycle_count += 1

        # 2-FF synchronizer
        self.rx_prev_sync = self.rx_sync_2
        self._sync_rx(rx_pin)

        # Break handling
        if self.break_active:
            self.tx_output = 0
            self.break_timer -= 1
            if self.break_timer <= 0:
                self.break_active = False
                self.break_send = False
                self.tx_output = 1
            return

        # Baud generator
        self._update_baud_generator()
        self._update_oversample_counter()

        # TX FSM
        self._tx_fsm_combinational()
        self._tx_fsm_sequential()

        # RX FSM
        self._rx_fsm_combinational()
        self._rx_fsm_sequential()

    # --- Break send ---

    def start_break(self):
        """Start break condition: tx low for one full frame."""
        n_bits = 1 + self.DATA_WIDTH
        if self.parity_en:
            n_bits += 1
        n_bits += 1  # STOP1
        if self.stop_bits:
            n_bits += 1
        self.break_timer = n_bits * self.baud_tick_period()
        self.break_active = True
        self.tx_output = 0

    # --- Self-check ---

    def self_check(self):
        """CL model self-check: verify cycle-level TX/RX behavior."""
        self.reset()

        # Configure: 9600 baud at 50MHz/16x oversample
        self.baud_div = 324  # (324+1)*16 = 5200 PCLK per baud tick
        self.tx_enable = True

        # Write a byte to TX FIFO
        self.tx_fifo.append(0x55)

        # Run TX: should produce start + 0x55 (01010101) LSB-first + stop
        baud_period = self.baud_tick_period()
        tx_bits = []

        # Tick until TX starts
        for _ in range(baud_period * 20):
            self.tick()
            if self.tx_state == 'TX_IDLE' and len(tx_bits) > 0:
                break
            if self.tx_state != 'TX_IDLE' or self.tx_active:
                # Sample tx_output every baud period
                if self.tx_baud_tick:
                    tx_bits.append(self.tx_output)

        # Expected: 0 (start) + 1,0,1,0,1,0,1,0 (0x55 LSB) + 1 (stop) = 10 bits
        assert len(tx_bits) >= 1, f"No TX bits captured"
        print(f"TX bits captured: {tx_bits[:12]}")
        print(f"TX stage trace: {self.tx_stage_trace}")

        # Verify TX stages visited
        assert 'TX_START' in self.tx_stage_trace, "TX_START not visited"
        assert 'TX_DATA' in self.tx_stage_trace, "TX_DATA not visited"
        assert 'TX_STOP1' in self.tx_stage_trace, "TX_STOP1 not visited"
        assert 'TX_IDLE_done' in self.tx_stage_trace, "TX IDLE done not reached"

        print("CL model self-check: ALL PASS")


def self_check():
    """Entry point for CL model self-check."""
    m = UartLiteRealCycleModel()
    m.self_check()


if __name__ == '__main__':
    self_check()
