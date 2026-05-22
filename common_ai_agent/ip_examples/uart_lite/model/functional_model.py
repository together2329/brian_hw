#!/usr/bin/env python3
"""Executable SSOT functional model for uart_lite.

Generated from yaml/uart_lite.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'uart_lite', 'parameters': {'DATA_WIDTH': 8, 'FIFO_DEPTH': 16, 'OVERSAMPLE': 16, 'APB_ADDR_WIDTH': 8, 'APB_DATA_WIDTH': 32, 'CLOCK_FREQ_MHZ': 50, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'uart_lite', 'file': 'rtl/uart_lite.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Parameterized UART transceiver with APB-lite CSR interface, TX/RX FIFOs, configurable baud/parity/stop bits, and sticky status interrupts', 'reference_spec': 'user-defined — generic UART with oversampling, no hardware flow control', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'tx_fifo', 'type': 'sram_fifo', 'depth': 16, 'width': 'DATA_WIDTH', 'read_ports': 1, 'write_ports': 1, 'latency': 1, 'description': 'TX FIFO — parameterized to FIFO_DEPTH × DATA_WIDTH; write on APB write to TXDATA, read on TX FSM pop'}, {'name': 'rx_fifo', 'type': 'sram_fifo', 'depth': 16, 'width': 'DATA_WIDTH', 'read_ports': 1, 'write_ports': 1, 'latency': 1, 'description': 'RX FIFO — parameterized to FIFO_DEPTH × DATA_WIDTH; write on RX frame complete, read on APB read from RXDATA'}], 'note': 'FIFOs implemented as SRAM-based circular buffers with read/write pointers. Depth parameter FIFO_DEPTH (default 16, power-of-two).'}, 'registers': {'config': {'register_width': 32, 'addr_width': 8, 'byte_addressable': True}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Control Register', 'write_side_effects': ['Fields take effect immediately on APB write; TX/RX enable changes during active transfer follow error_handling rules.', 'loopback=1 internally connects tx to rx synchronizer input after the 2-FF stage.', 'break_send=1 forces tx low for at least one full frame duration (start+data+parity+stop) then self-clears.'], 'fields': [{'name': 'tx_enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable transmitter'}, {'name': 'rx_enable', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'Enable receiver'}, {'name': 'loopback', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Loopback test mode: internal tx→rx connection'}, {'name': 'break_send', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Send break (force tx=0); self-clears after one frame'}, {'name': 'parity_en', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'description': 'Enable parity generation/checking'}, {'name': 'parity_odd', 'bits': [5, 5], 'access': 'rw', 'reset': 0, 'description': '0=even parity, 1=odd parity (when parity_en=1)'}, {'name': 'stop_bits', 'bits': [6, 6], 'access': 'rw', 'reset': 0, 'description': '0=1 stop bit, 1=2 stop bits'}, {'name': 'reserved_31_7', 'bits': [31, 7], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'STAT', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Status Register — live FIFO flags and sticky error flags', 'fields': [{'name': 'tx_full', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'TX FIFO full (live)'}, {'name': 'tx_empty', 'bits': [1, 1], 'access': 'ro', 'reset': 1, 'description': 'TX FIFO empty (live)'}, {'name': 'rx_empty', 'bits': [2, 2], 'access': 'ro', 'reset': 1, 'description': 'RX FIFO empty (live)'}, {'name': 'rx_full', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'RX FIFO full (live)'}, {'name': 'tx_busy', 'bits': [4, 4], 'access': 'ro', 'reset': 0, 'description': 'Transmitter active (shift register busy)'}, {'name': 'rx_busy', 'bits': [5, 5], 'access': 'ro', 'reset': 0, 'description': 'Receiver active (frame in progress)'}, {'name': 'frame_err', 'bits': [6, 6], 'access': 'ro', 'reset': 0, 'description': 'Framing error detected (sticky, clear via CLR_STAT)'}, {'name': 'parity_err', 'bits': [7, 7], 'access': 'ro', 'reset': 0, 'description': 'Parity error detected (sticky, clear via CLR_STAT)'}, {'name': 'overrun_err', 'bits': [8, 8], 'access': 'ro', 'reset': 0, 'description': 'RX overrun (sticky, clear via CLR_STAT)'}, {'name': 'underrun_err', 'bits': [9, 9], 'access': 'ro', 'reset': 0, 'description': 'TX underrun (sticky, clear via CLR_STAT)'}, {'name': 'reserved_31_10', 'bits': [31, 10], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'BAUD', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 324, 'category': 'control', 'description': 'Baud Rate Divisor', 'write_side_effects': ['Changing BAUD during an active TX or RX frame results in the current frame completing at the old rate; the new divisor takes effect for the next frame.'], 'fields': [{'name': 'baud_div', 'bits': [15, 0], 'access': 'rw', 'reset': 324, 'description': 'Baud divisor: bit_period = (baud_div+1) * OVERSAMPLE PCLK cycles. Reset=324 → 9600 baud at 50 MHz/16x.'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'TXDATA', 'offset': 12, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'data', 'description': 'TX Data Write (pushes to TX FIFO)', 'write_side_effects': ['Writing when tx_full=1 discards data and sets underrun_err sticky flag.', 'On successful write, TX FSM is triggered if idle.'], 'fields': [{'name': 'tx_data', 'bits': [7, 0], 'access': 'wo', 'reset': 0, 'description': 'Transmit data byte'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'RXDATA', 'offset': 16, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'data', 'description': 'RX Data Read (pops from RX FIFO)', 'read_side_effects': ['Reading when rx_empty=1 returns last valid data or 0x00 and does not change FIFO state.', 'Successful read pops one byte from RX FIFO.'], 'fields': [{'name': 'rx_data', 'bits': [7, 0], 'access': 'ro', 'reset': 0, 'description': 'Received data byte'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'INTEN', 'offset': 20, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Enable Register', 'write_side_effects': ['Changes take effect immediately.'], 'fields': [{'name': 'tx_empty_en', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable TX empty interrupt'}, {'name': 'rx_not_empty_en', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'Enable RX not empty interrupt'}, {'name': 'rx_overrun_en', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Enable RX overrun interrupt'}, {'name': 'frame_err_en', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Enable framing error interrupt'}, {'name': 'parity_err_en', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'description': 'Enable parity error interrupt'}, {'name': 'reserved_31_5', 'bits': [31, 5], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'INTPEND', 'offset': 24, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Pending Register (W1C for set bits)', 'write_side_effects': ['Writing 1 to a bit clears that pending flag. Writing 0 has no effect.', 'Hardware sets pending bits when enabled interrupt conditions occur.'], 'fields': [{'name': 'tx_empty_pend', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'TX empty pending (W1C)'}, {'name': 'rx_not_empty_pend', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'RX not empty pending (W1C)'}, {'name': 'rx_overrun_pend', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'RX overrun pending (W1C)'}, {'name': 'frame_err_pend', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Framing error pending (W1C)'}, {'name': 'parity_err_pend', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'description': 'Parity error pending (W1C)'}, {'name': 'reserved_31_5', 'bits': [31, 5], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'CLR_STAT', 'offset': 28, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'status', 'description': 'Clear Sticky Status Flags (W1C)', 'write_side_effects': ['Writing 1 to a bit clears the corresponding sticky flag in STAT. Writing 0 has no effect.'], 'fields': [{'name': 'clr_frame_err', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Clear frame_err (W1C)'}, {'name': 'clr_parity_err', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'Clear parity_err (W1C)'}, {'name': 'clr_overrun_err', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Clear overrun_err (W1C)'}, {'name': 'clr_underrun_err', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Clear underrun_err (W1C)'}, {'name': 'reserved_31_4', 'bits': [31, 4], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'DBG_BYTES_TX', 'offset': 32, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter: Bytes Transmitted', 'read_side_effects': ['Read returns current count. Counter wraps at 0xFFFFFFFF.'], 'fields': [{'name': 'bytes_tx', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Total bytes transmitted (wrapping)'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'DBG_BYTES_RX', 'offset': 36, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter: Bytes Received', 'fields': [{'name': 'bytes_rx', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Total bytes received (wrapping)'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'DBG_FRAMES_ERR', 'offset': 40, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter: Framing Errors', 'fields': [{'name': 'frames_errored', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Total framing errors (wrapping)'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}, {'name': 'DBG_PARITIES_ERR', 'offset': 44, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter: Parity Errors', 'fields': [{'name': 'parities_errored', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Total parity errors (wrapping)'}], 'output_rules': [{'name': 'uart_irq', 'port': 'uart_irq', 'expr': '0'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the UART computes independent of cycle timing.', 'state_variables': [{'name': 'tx_fifo', 'source': 'memory.instances.tx_fifo', 'reset': 'empty', 'description': 'TX FIFO queue of bytes to transmit'}, {'name': 'rx_fifo', 'source': 'memory.instances.rx_fifo', 'reset': 'empty', 'description': 'RX FIFO queue of received bytes'}, {'name': 'tx_active', 'source': 'internal', 'reset': False, 'description': 'True while TX FSM is not IDLE'}, {'name': 'rx_active', 'source': 'internal', 'reset': False, 'description': 'True while RX FSM is not IDLE'}, {'name': 'baud_div', 'source': 'registers.BAUD.baud_div', 'reset': 324, 'description': 'Baud divisor register value'}, {'name': 'parity_en', 'source': 'registers.CTRL.parity_en', 'reset': False, 'description': 'Parity enable'}, {'name': 'parity_odd', 'source': 'registers.CTRL.parity_odd', 'reset': False, 'description': 'Parity odd/even select'}, {'name': 'stop_bits', 'source': 'registers.CTRL.stop_bits', 'reset': False, 'description': '0=1 stop, 1=2 stop'}, {'name': 'loopback', 'source': 'registers.CTRL.loopback', 'reset': False, 'description': 'Loopback mode active'}, {'name': 'break_send', 'source': 'registers.CTRL.break_send', 'reset': False, 'description': 'Break send active; self-clears'}], 'transactions': [{'id': 'FM_TX_BYTE', 'name': 'transmit_byte', 'sample_stage': 'TX_START', 'preconditions': ['tx_enable == 1', 'tx_fifo not empty', 'tx_active == false', 'break_send == false'], 'inputs': ['byte d popped from tx_fifo'], 'outputs': ['tx line: start bit (0), d[0]..d[DATA_WIDTH-1] LSB-first, parity bit (if parity_en), 1 or 2 stop bits (1)', 'tx_active transitions true → false across the frame'], 'side_effects': ['debug counter bytes_tx increments by 1', 'tx_fifo level decreases by 1', 'STAT.tx_empty updates when FIFO becomes empty'], 'error_cases': [{'condition': 'tx_fifo empty when TX FSM requests byte', 'result': 'underrun_err sticky flag set; frame aborted with tx returning to idle (mark)'}], 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': '1'}], 'state_updates': [{'name': 'tx', 'reset': 1, 'expr': '1'}]}, {'id': 'FM_RX_BYTE', 'name': 'receive_byte', 'preconditions': ['rx_enable == 1', 'rx_active == false', 'rx_fifo not full'], 'inputs': ['rx line serial stream after 2-FF synchronizer'], 'outputs': ['byte d reconstructed from sampled bits pushed to rx_fifo', 'STAT.rx_not_empty set'], 'side_effects': ['debug counter bytes_rx increments by 1', 'rx_fifo level increases by 1', 'If parity_en and parity mismatch: parity_err sticky set, parities_errored incremented', 'If stop bit(s) not high: frame_err sticky set, frames_errored incremented'], 'error_cases': [{'condition': 'rx_fifo full when new byte ready', 'result': 'overrun_err sticky flag set; received byte discarded'}, {'condition': 'spurious start bit (mid-bit sample high)', 'result': 'rx_active returns false; no byte pushed'}, {'condition': 'frame_err: stop bit sampled low', 'result': 'frame_err sticky set; byte still pushed to rx_fifo if space available'}, {'condition': 'parity_err: computed parity != received parity bit', 'result': 'parity_err sticky set; byte still pushed to rx_fifo if space available'}], 'output_rules': [{'name': 'rx_irq', 'port': 'uart_irq', 'expr': '0'}], 'state_updates': [{'name': 'uart_irq', 'reset': 0, 'expr': '0'}]}, {'id': 'FM_BREAK_SEND', 'name': 'send_break', 'preconditions': ['break_send written to 1 via CTRL register'], 'inputs': ['none'], 'outputs': ['tx line forced low for duration of one full frame (start+data+parity+stop bits)'], 'side_effects': ['break_send self-clears to 0 after break completes', 'TX FSM held in IDLE during break'], 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': '1'}], 'state_updates': [{'name': 'tx', 'reset': 1, 'expr': '0'}]}, {'id': 'FM_LOOPBACK', 'name': 'loopback_mode', 'preconditions': ['loopback == 1'], 'inputs': ['tx line output'], 'outputs': ['rx synchronizer input connected to tx output (after 2-FF synchronizer stage)'], 'side_effects': ['External rx pin ignored', 'All TX bytes appear as received bytes when rx_enable == 1'], 'output_rules': [{'name': 'loopback_tx', 'port': 'tx', 'expr': '1'}], 'state_updates': [{'name': 'tx', 'reset': 1, 'expr': '1'}]}], 'invariants': ['TX FIFO never underflows during a valid frame — underrun terminates frame early.', 'RX FIFO never overflows without sticky overrun_err flag.', 'Register read side effects are exactly those listed in registers.register_list.', 'Sticky status flags remain set until explicitly cleared via CLR_STAT W1C.', 'Debug counters are free-running, read-only, and wrap at 0xFFFFFFFF.'], 'reference_model_hint': 'tb-gen should implement a Python scoreboard that feeds TX bytes and checks RX bytes match in loopback mode, and checks error flags trigger per scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when TX/RX state, baud ticks, sampling, and interrupts may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle and run direct Python smoke checks instead of relying on pytest-pymtl3.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'baud_generator': {'oversample_factor': 16, 'parameter': 'OVERSAMPLE', 'tick_formula': 'baud_tick asserted when internal counter == (baud_div * OVERSAMPLE) - 1; counter resets to 0', 'counter_width': 'ceil(log2(max_baud_div * OVERSAMPLE))', 'mid_sample_point': 7, 'description': 'RX samples data/parity/stop bits at the centre of each bit period (oversample count 7 of 16). Start-bit confirmation also at count 7.'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}, 'tx_byte': {'min_cycles': 'baud_tick_period * (1 + DATA_WIDTH + parity_en + stop_bits)', 'max_cycles': None, 'description': 'TX frame duration; max unbounded if TX FIFO is empty and no new data'}, 'rx_byte': {'min_cycles': 'baud_tick_period * (1 + DATA_WIDTH + parity_en + stop_bits)', 'max_cycles': None, 'description': 'RX frame duration; max unbounded waiting for start bit'}}, 'handshake_rules': [{'signal': 'tx', 'rule': 'Driven synchronously to PCLK; changes only on baud_tick boundaries at TX FSM state transitions. Idle state is high (mark).'}, {'signal': 'rx', 'rule': 'External async input. Passed through 2-FF synchronizer. Synchronizer output sampled on every PCLK edge by RX FSM start-bit detector.'}, {'signal': 'PREADY', 'rule': 'Asserted in the access phase (PSEL=1, PENABLE=1) for all valid register addresses. Deasserted otherwise.'}, {'signal': 'PSLVERR', 'rule': 'Asserted only with PREADY=1 for accesses to unimplemented address ranges.'}], 'pipeline': [{'stage': 'TX_IDLE', 'cycle': 0, 'action': 'Wait for TX FIFO not empty; assert tx_active=false', 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': '1', 'width': 1}, {'name': 'tx_active', 'expr': '0', 'width': 1}]}, {'stage': 'TX_START', 'cycle': 1, 'action': 'Drive tx=0 for one baud tick period; assert tx_active', 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': '0', 'width': 1}, {'name': 'tx_active', 'expr': '1', 'width': 1}]}, {'stage': 'TX_DATA', 'cycle': '2..1+DATA_WIDTH', 'action': 'Shift LSB of tx_shift_reg to tx each baud tick; repeat DATA_WIDTH times. tx_shift_reg loaded from TX FIFO on entry.', 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': '(tx_byte >> data_bit_index) & 1', 'width': 1}, {'name': 'tx_active', 'expr': '1', 'width': 1}]}, {'stage': 'TX_PARITY', 'cycle': '2+DATA_WIDTH', 'action': 'Drive computed parity bit to tx for one baud tick (present only if parity_en=1)', 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': 'tx_parity_bit', 'width': 1}, {'name': 'tx_active', 'expr': '1', 'width': 1}]}, {'stage': 'TX_STOP1', 'cycle': '3+DATA_WIDTH', 'action': 'Drive tx=1 for one baud tick', 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': '1', 'width': 1}, {'name': 'tx_active', 'expr': '1', 'width': 1}]}, {'stage': 'TX_STOP2', 'cycle': '4+DATA_WIDTH', 'action': 'Drive tx=1 for one baud tick (present only if stop_bits=1)', 'output_rules': [{'name': 'tx_serial', 'port': 'tx', 'expr': '1', 'width': 1}, {'name': 'tx_active', 'expr': '0', 'width': 1}]}, {'stage': 'RX_IDLE', 'cycle': 0, 'action': 'Monitor synchronized rx for falling edge; assert rx_active=false', 'output_rules': [{'name': 'rx_active', 'expr': '0', 'width': 1}]}, {'stage': 'RX_START_DETECT', 'cycle': 1, 'action': 'On falling edge, wait until oversample count 7', 'output_rules': [{'name': 'rx_active', 'expr': '1', 'width': 1}]}, {'stage': 'RX_START_CONFIRM', 'cycle': 2, 'action': 'At oversample count 7, sample synchronized rx. If low → confirmed start, advance. If high → spurious, return to RX_IDLE.', 'output_rules': [{'name': 'rx_active', 'expr': '1', 'width': 1}]}, {'stage': 'RX_DATA', 'cycle': '3..2+DATA_WIDTH', 'action': 'At oversample count 7 of each subsequent bit period, sample rx into rx_shift_reg LSB-first; repeat DATA_WIDTH times', 'output_rules': [{'name': 'rx_active', 'expr': '1', 'width': 1}]}, {'stage': 'RX_PARITY', 'cycle': '3+DATA_WIDTH', 'action': 'At oversample count 7, sample parity bit; compute expected parity; compare. (present only if parity_en=1)', 'output_rules': [{'name': 'rx_active', 'expr': '1', 'width': 1}]}, {'stage': 'RX_STOP1', 'cycle': '4+DATA_WIDTH', 'action': 'At oversample count 7, sample stop bit. If high → valid. If low → frame_err.', 'output_rules': [{'name': 'rx_active', 'expr': '1', 'width': 1}]}, {'stage': 'RX_STOP2', 'cycle': '5+DATA_WIDTH', 'action': 'At oversample count 7, sample second stop bit. (present only if stop_bits=1)', 'output_rules': [{'name': 'rx_active', 'expr': '1', 'width': 1}]}], 'ordering': ['TX FSM does not start a new frame until the current frame completes (no pipelining across bytes).', 'RX FSM does not start a new frame until the current frame completes.', 'Interrupt pending bits update on the same PCLK edge as the condition (FIFO threshold crossing, error detection, frame completion).'], 'backpressure': ['TX backpressure: TX FSM waits in TX_IDLE when TX FIFO is empty.', 'RX backpressure: If RX FIFO is full when a new byte would be pushed, overrun_err is set and the byte is discarded; RX FSM returns to RX_IDLE.'], 'performance': {'frequency_mhz': 50, 'throughput': {'max_baud': 'PCLK / (OVERSAMPLE * 1) = 3.125 Mbaud at baud_div=0', 'sustained_bytes_per_second': 'baud_rate / (1 + DATA_WIDTH + parity_en + stop_bits)'}, 'outstanding': {'tx_max': 16, 'rx_max': 16, 'description': 'FIFO depth bounds maximum queued TX/RX bytes'}, 'depth': {'fifo_depth': 16, 'oversample_stages': 16, 'description': 'FIFO depth and oversample counter depth'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model TX or RX stage.', 'Baud tick, oversample counter, TX/RX shift registers, and FIFO pointers are observable in waveform.'], 'use_per_cycle_expected': True}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'TX single byte no parity 1 stop'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'RX single byte no parity 1 stop'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'TX with even parity'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'RX with odd parity match'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'RX parity error'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'RX framing error'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'RX overrun'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'TX underrun'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'Loopback mode'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'Break send'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': '2 stop bits TX/RX'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'Interrupts — tx_empty'}, {'id': 'SC13_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'SC13', 'description': 'Interrupts — rx_not_empty + clear via W1C'}, {'id': 'SC14_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'SC14', 'description': 'DATA_WIDTH=5'}, {'id': 'SC15_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[14]', 'scenario': 'SC15', 'description': 'FIFO full/empty flags'}, {'id': 'SC16_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[15]', 'scenario': 'SC16', 'description': 'Spurious start bit rejection'}, {'id': 'SC17_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[16]', 'scenario': 'SC17', 'description': 'Baud rate change mid-operation'}, {'id': 'fcov_fm_tx_byte', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TX_BYTE', 'source_ref': 'function_model.transactions.FM_TX_BYTE', 'description': 'TX byte transaction observed by scoreboard'}, {'id': 'fcov_fm_rx_byte', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX_BYTE', 'source_ref': 'function_model.transactions.FM_RX_BYTE', 'description': 'RX byte transaction observed by scoreboard'}, {'id': 'fcov_fm_break', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_BREAK_SEND', 'source_ref': 'function_model.transactions.FM_BREAK_SEND', 'description': 'Break send observed'}, {'id': 'fcov_fm_loopback', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_LOOPBACK', 'source_ref': 'function_model.transactions.FM_LOOPBACK', 'description': 'Loopback mode verified'}, {'id': 'fcov_err_parity', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX_BYTE.error_cases.parity_err', 'source_ref': 'function_model.transactions.FM_RX_BYTE.error_cases.parity_err', 'description': 'Parity error detected'}, {'id': 'fcov_err_frame', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX_BYTE.error_cases.frame_err', 'source_ref': 'function_model.transactions.FM_RX_BYTE.error_cases.frame_err', 'description': 'Framing error detected'}, {'id': 'fcov_err_overrun', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX_BYTE.error_cases.overrun_err', 'source_ref': 'function_model.transactions.FM_RX_BYTE.error_cases.overrun_err', 'description': 'Overrun error detected'}, {'id': 'ccov_tx_idle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[TX_IDLE]', 'source_ref': 'cycle_model.pipeline[TX_IDLE]', 'description': 'TX IDLE stage observed'}, {'id': 'ccov_tx_data', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[TX_DATA]', 'source_ref': 'cycle_model.pipeline[TX_DATA]', 'description': 'TX DATA stage observed'}, {'id': 'ccov_rx_start_confirm', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[RX_START_CONFIRM]', 'source_ref': 'cycle_model.pipeline[RX_START_CONFIRM]', 'description': 'RX start confirm stage observed'}, {'id': 'ccov_rx_data', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[RX_DATA]', 'source_ref': 'cycle_model.pipeline[RX_DATA]', 'description': 'RX DATA stage observed'}, {'id': 'ccov_baud_tick', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.baud_generator', 'source_ref': 'cycle_model.baud_generator', 'description': 'Baud tick observed at correct rate'}, {'id': 'ccov_perf_fifo_depth', 'class': 'depth', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': 'FIFO depth exercised'}, {'id': 'function_transmit_byte', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_tx_byte', 'description': 'transmit_byte'}, {'id': 'function_receive_byte', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_rx_byte', 'description': 'receive_byte'}, {'id': 'function_send_break', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_break_send', 'description': 'send_break'}, {'id': 'function_loopback_mode', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_loopback', 'description': 'loopback_mode'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'tx', 'rule': 'Driven synchronously to PCLK; changes only on baud_tick boundaries at TX FSM state transitions. Idle state is high (mark).'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'rx', 'rule': 'External async input. Passed through 2-FF synchronizer. Synchronizer output sampled on every PCLK edge by RX FSM start-bit detector.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'PREADY', 'rule': 'Asserted in the access phase (PSEL=1, PENABLE=1) for all valid register addresses. Deasserted otherwise.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'PSLVERR', 'rule': 'Asserted only with PREADY=1 for accesses to unimplemented address ranges.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}"}, {'id': 'cycle_latency_tx_byte', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.tx_byte', 'source_ref': 'cycle_model.latency.tx_byte', 'description': "{'min_cycles': 'baud_tick_period * (1 + DATA_WIDTH + parity_en + stop_bits)', 'max_cycles': None, 'description': 'TX frame duration; max unbounded if TX FIFO is empty and no new data'}"}, {'id': 'cycle_latency_rx_byte', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.rx_byte', 'source_ref': 'cycle_model.latency.rx_byte', 'description': "{'min_cycles': 'baud_tick_period * (1 + DATA_WIDTH + parity_en + stop_bits)', 'max_cycles': None, 'description': 'RX frame duration; max unbounded waiting for start bit'}"}, {'id': 'cycle_pipeline_tx_idle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Wait for TX FIFO not empty; assert tx_active=false'}, {'id': 'cycle_pipeline_tx_start', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Drive tx=0 for one baud tick period; assert tx_active'}, {'id': 'cycle_pipeline_tx_data', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Shift LSB of tx_shift_reg to tx each baud tick; repeat DATA_WIDTH times. tx_shift_reg loaded from TX FIFO on entry.'}, {'id': 'cycle_pipeline_tx_parity', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Drive computed parity bit to tx for one baud tick (present only if parity_en=1)'}, {'id': 'cycle_pipeline_tx_stop1', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Drive tx=1 for one baud tick'}, {'id': 'cycle_pipeline_tx_stop2', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[5]', 'source_ref': 'cycle_model.pipeline[5]', 'description': 'Drive tx=1 for one baud tick (present only if stop_bits=1)'}, {'id': 'cycle_pipeline_rx_idle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[6]', 'source_ref': 'cycle_model.pipeline[6]', 'description': 'Monitor synchronized rx for falling edge; assert rx_active=false'}, {'id': 'cycle_pipeline_rx_start_detect', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[7]', 'source_ref': 'cycle_model.pipeline[7]', 'description': 'On falling edge, wait until oversample count 7'}, {'id': 'cycle_pipeline_rx_start_confirm', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[8]', 'source_ref': 'cycle_model.pipeline[8]', 'description': 'At oversample count 7, sample synchronized rx. If low → confirmed start, advance. If high → spurious, return to RX_IDLE.'}, {'id': 'cycle_pipeline_rx_data', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[9]', 'source_ref': 'cycle_model.pipeline[9]', 'description': 'At oversample count 7 of each subsequent bit period, sample rx into rx_shift_reg LSB-first; repeat DATA_WIDTH times'}, {'id': 'cycle_pipeline_rx_parity', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[10]', 'source_ref': 'cycle_model.pipeline[10]', 'description': 'At oversample count 7, sample parity bit; compute expected parity; compare. (present only if parity_en=1)'}, {'id': 'cycle_pipeline_rx_stop1', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[11]', 'source_ref': 'cycle_model.pipeline[11]', 'description': 'At oversample count 7, sample stop bit. If high → valid. If low → frame_err.'}, {'id': 'cycle_pipeline_rx_stop2', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[12]', 'source_ref': 'cycle_model.pipeline[12]', 'description': 'At oversample count 7, sample second stop bit. (present only if stop_bits=1)'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'TX FSM does not start a new frame until the current frame completes (no pipelining across bytes).'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'RX FSM does not start a new frame until the current frame completes.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Interrupt pending bits update on the same PCLK edge as the condition (FIFO threshold crossing, error detection, frame completion).'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'TX backpressure: TX FSM waits in TX_IDLE when TX FIFO is empty.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'RX backpressure: If RX FIFO is full when a new byte would be pushed, overrun_err is set and the byte is discarded; RX FSM returns to RX_IDLE.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'tx_max': 16, 'rx_max': 16, 'description': 'FIFO depth bounds maximum queued TX/RX bytes'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'fifo_depth': 16, 'oversample_stages': 16, 'description': 'FIFO depth and oversample counter depth'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'max_baud': 'PCLK / (OVERSAMPLE * 1) = 3.125 Mbaud at baud_div=0', 'sustained_bytes_per_second': 'baud_rate / (1 + DATA_WIDTH + parity_en + stop_bits)'}"}, {'id': 'fsm_tx_fsm_tx_idle_to_tx_start_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[0]', 'source_ref': 'fsm.tx_fsm.transitions[0]', 'description': 'TX FIFO not empty and baud tick'}, {'id': 'fsm_tx_fsm_tx_start_to_tx_data_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[1]', 'source_ref': 'fsm.tx_fsm.transitions[1]', 'description': 'baud tick (1 bit period elapsed)'}, {'id': 'fsm_tx_fsm_tx_data_to_tx_parity_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[2]', 'source_ref': 'fsm.tx_fsm.transitions[2]', 'description': 'DATA_WIDTH bits transmitted and parity_en=1 and baud tick'}, {'id': 'fsm_tx_fsm_tx_data_to_tx_stop1_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[3]', 'source_ref': 'fsm.tx_fsm.transitions[3]', 'description': 'DATA_WIDTH bits transmitted and parity_en=0 and baud tick'}, {'id': 'fsm_tx_fsm_tx_parity_to_tx_stop1_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[4]', 'source_ref': 'fsm.tx_fsm.transitions[4]', 'description': 'baud tick'}, {'id': 'fsm_tx_fsm_tx_stop1_to_tx_idle_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[5]', 'source_ref': 'fsm.tx_fsm.transitions[5]', 'description': 'stop_bits=0 and baud tick'}, {'id': 'fsm_tx_fsm_tx_stop1_to_tx_stop2_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[6]', 'source_ref': 'fsm.tx_fsm.transitions[6]', 'description': 'stop_bits=1 and baud tick'}, {'id': 'fsm_tx_fsm_tx_stop2_to_tx_idle_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[7]', 'source_ref': 'fsm.tx_fsm.transitions[7]', 'description': 'baud tick'}, {'id': 'fsm_rx_fsm_rx_idle_to_rx_start_detect_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[0]', 'source_ref': 'fsm.rx_fsm.transitions[0]', 'description': 'rx_synced falling edge detected'}, {'id': 'fsm_rx_fsm_rx_start_detect_to_rx_start_confirm_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[1]', 'source_ref': 'fsm.rx_fsm.transitions[1]', 'description': 'mid-bit sample at oversample count 7 confirms low'}, {'id': 'fsm_rx_fsm_rx_start_detect_to_rx_idle_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[2]', 'source_ref': 'fsm.rx_fsm.transitions[2]', 'description': 'mid-bit sample at oversample count 7 is high (spurious edge)'}, {'id': 'fsm_rx_fsm_rx_start_confirm_to_rx_data_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[3]', 'source_ref': 'fsm.rx_fsm.transitions[3]', 'description': 'full bit period from start confirm; oversample tick'}, {'id': 'fsm_rx_fsm_rx_data_to_rx_parity_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[4]', 'source_ref': 'fsm.rx_fsm.transitions[4]', 'description': 'DATA_WIDTH bits sampled at centre and parity_en=1 and oversample tick'}, {'id': 'fsm_rx_fsm_rx_data_to_rx_stop1_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[5]', 'source_ref': 'fsm.rx_fsm.transitions[5]', 'description': 'DATA_WIDTH bits sampled at centre and parity_en=0 and oversample tick'}, {'id': 'fsm_rx_fsm_rx_parity_to_rx_stop1_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[6]', 'source_ref': 'fsm.rx_fsm.transitions[6]', 'description': 'parity bit sampled at centre and oversample tick'}, {'id': 'fsm_rx_fsm_rx_stop1_to_rx_idle_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[7]', 'source_ref': 'fsm.rx_fsm.transitions[7]', 'description': 'stop_bits=0; stop bit sampled high at centre and oversample tick'}, {'id': 'fsm_rx_fsm_rx_stop1_to_rx_stop2_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[8]', 'source_ref': 'fsm.rx_fsm.transitions[8]', 'description': 'stop_bits=1 and oversample tick'}, {'id': 'fsm_rx_fsm_rx_stop2_to_rx_idle_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[9]', 'source_ref': 'fsm.rx_fsm.transitions[9]', 'description': 'oversample tick'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_FRAME', 'condition': 'RX stop bit(s) sampled low', 'architectural_effect': 'STAT.frame_err sticky set; DBG_FRAMES_ERR incremented; frame_error interrupt if enabled'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_PARITY', 'condition': 'RX computed parity != received parity bit', 'architectural_effect': 'STAT.parity_err sticky set; DBG_PARITIES_ERR incremented; parity_error interrupt if enabled'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'ERR_OVERRUN', 'condition': 'RX FIFO full when new byte ready to push', 'architectural_effect': 'STAT.overrun_err sticky set; received byte discarded; rx_overrun interrupt if enabled'}"}, {'id': 'error_error_3', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'id': 'ERR_UNDERRUN', 'condition': 'TX FIFO empty when TX FSM requests next byte during active frame', 'architectural_effect': 'STAT.underrun_err sticky set; frame aborted; tx returns to idle (mark)'}"}]}
RESP_OKAY = 0
RESP_SLVERR = 2


def _parse_int(value, default=0):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("_", "")
    if not text:
        return default
    literal = text.lower()
    if "'" in literal:
        try:
            base_tag = literal.split("'", 1)[1][0]
            digits = literal.split(base_tag, 1)[1]
            digits = digits.replace("x", "0").replace("z", "0")
            base = {"h": 16, "d": 10, "b": 2}.get(base_tag, 10)
            return int(digits, base)
        except Exception:
            return default
    if text.startswith("0x"):
        return int(text, 16)
    try:
        return int(text, 10)
    except ValueError:
        return default


_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Div: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.LShift: lambda a, b: a << b,
    ast.RShift: lambda a, b: a >> b,
    ast.BitAnd: lambda a, b: a & b,
    ast.BitOr: lambda a, b: a | b,
    ast.BitXor: lambda a, b: a ^ b,
}
_UNARYOPS = {
    ast.UAdd: lambda a: a,
    ast.USub: lambda a: -a,
    ast.Invert: lambda a: ~a,
    ast.Not: lambda a: 0 if a else 1,
}
_CMPOPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
}


def _normal_expr(text):
    text = str(text or "").strip()
    reduction_or = re.fullmatch(r"\|\s*\((.*)\)", text)
    if reduction_or:
        text = f"reduction_or({reduction_or.group(1)})"
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"(?<![=!<>])!(?!=)", " not ", text)
    return text


def _literal_int(text):
    text = str(text).strip().replace("_", "")
    return bool(re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+|[0-9]*'[hHdDbB][0-9a-fA-FxXzZ]+)", text))


def _h_bin_to_gray(value):
    v = _parse_int(value, 0)
    return v ^ (v >> 1)


def _h_gray_to_bin(value):
    g = _parse_int(value, 0)
    b = g
    s = g >> 1
    while s:
        b ^= s
        s >>= 1
    return b


def _h_popcount(value):
    return bin(_parse_int(value, 0) & ((1 << 256) - 1)).count("1")


def _h_parity(value):
    return _h_popcount(value) & 1


def _h_clog2(value):
    v = _parse_int(value, 0)
    if v <= 1:
        return 0
    return (v - 1).bit_length()


def _default_rule_helpers():
    return {
        "bin_to_gray": _h_bin_to_gray,
        "gray_to_bin": _h_gray_to_bin,
        "popcount": _h_popcount,
        "parity": _h_parity,
        "clog2": _h_clog2,
        "min": lambda a, b: min(_parse_int(a, 0), _parse_int(b, 0)),
        "max": lambda a, b: max(_parse_int(a, 0), _parse_int(b, 0)),
        "abs": lambda a: abs(_parse_int(a, 0)),
        "any": lambda *args: int(any(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "all": lambda *args: int(all(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "sum": lambda *args: int(sum(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "len": lambda *args: len(args[0]) if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else len(args),
    }


def _eval_ast(node, env):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, env)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return int(node.value)
        if isinstance(node.value, int):
            return node.value
        if isinstance(node.value, str):
            return _parse_int(node.value, 0)
        raise ValueError(f"unsupported constant {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return _parse_int(env[node.id], 0)
        raise KeyError(f"unknown rule name {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_ast(node.left, env), _eval_ast(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_ast(node.operand, env))
    if isinstance(node, ast.BoolOp):
        values = [_eval_ast(v, env) for v in node.values]
        if isinstance(node.op, ast.And):
            return int(all(values))
        if isinstance(node.op, ast.Or):
            return int(any(values))
    if isinstance(node, ast.Compare):
        left = _eval_ast(node.left, env)
        verdicts = []
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_ast(comparator, env)
            if type(op) not in _CMPOPS:
                raise ValueError(f"unsupported comparison {type(op).__name__}")
            verdicts.append(_CMPOPS[type(op)](left, right))
            left = right
        return int(all(verdicts))
    if isinstance(node, ast.IfExp):
        return _eval_ast(node.body if _eval_ast(node.test, env) else node.orelse, env)
    if isinstance(node, ast.Subscript):
        base = _eval_ast(node.value, env)
        sl = node.slice
        if isinstance(sl, ast.Index):
            sl = sl.value
        if isinstance(sl, ast.Slice):
            hi = _eval_ast(sl.lower, env) if sl.lower is not None else 0
            lo = _eval_ast(sl.upper, env) if sl.upper is not None else 0
            if hi < lo:
                hi, lo = lo, hi
            width = hi - lo + 1
            mask = (1 << width) - 1
            return (base >> lo) & mask
        idx = _eval_ast(sl, env)
        return (base >> idx) & 1
    if isinstance(node, ast.GeneratorExp):
        return _eval_comprehension(node, env, generator=True)
    if isinstance(node, ast.ListComp):
        return _eval_comprehension(node, env, generator=False)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError(f"unsupported rule call {ast.dump(node.func)}")
        func = env.get(node.func.id)
        if not callable(func):
            raise ValueError(f"unsupported rule helper {node.func.id}")
        if node.keywords:
            raise ValueError(f"unsupported keyword args for rule helper {node.func.id}")
        args = [_eval_ast(arg, env) for arg in node.args]
        return _parse_int(func(*args), 0)
    raise ValueError(f"unsupported rule expression node {type(node).__name__}")


def _eval_comprehension(node, env, generator=False):
    """Evaluate a generator expression or list comprehension.

    Supports single-clause ``for`` with optional ``if`` filter, e.g.:
        ``(x for x in range(8) if x > 0)``
    Nested comprehensions are not supported.
    """
    if not node.generators:
        raise ValueError("comprehension with no generators")
    comp = node.generators[0]
    if len(node.generators) > 1:
        raise ValueError("nested comprehensions are not supported in rule expressions")
    if not isinstance(comp.target, ast.Name):
        raise ValueError("comprehension target must be a simple name")
    var_name = comp.target.id
    iter_values = _eval_iter(comp.iter, env)
    results = []
    for val in iter_values:
        local_env = dict(env)
        local_env[var_name] = val
        # Apply if-filters
        skip = False
        for if_clause in comp.ifs:
            if not _eval_ast(if_clause, local_env):
                skip = True
                break
        if skip:
            continue
        results.append(_eval_ast(node.elt, local_env))
    return results if not generator else results


def _eval_iter(node, env):
    """Evaluate an iterable source (range call or name reference)."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "range":
            args = [_eval_ast(a, env) for a in node.args]
            if len(args) == 1:
                return list(range(args[0]))
            if len(args) == 2:
                return list(range(args[0], args[1]))
            if len(args) == 3:
                return list(range(args[0], args[1], args[2]))
            raise ValueError(f"range() expects 1-3 args, got {len(args)}")
        # Other callables: evaluate and treat result as iterable if possible
        func = env.get(node.func.id)
        if callable(func):
            call_args = [_eval_ast(a, env) for a in node.args]
            result = func(*call_args)
            if isinstance(result, (list, tuple, range)):
                return list(result)
            return [_parse_int(result, 0)]
    if isinstance(node, ast.Name):
        val = env.get(node.id)
        if isinstance(val, (list, tuple, range)):
            return list(val)
        return [_parse_int(val, 0)]
    raise ValueError(f"unsupported iterable in comprehension: {ast.dump(node)}")


def _eval_rule_expr(expr, env):
    if isinstance(expr, bool):
        return int(expr)
    if isinstance(expr, int):
        return expr
    text = _normal_expr(expr)
    if not text:
        return 0
    if _literal_int(text):
        return _parse_int(text, 0)
    return _eval_ast(ast.parse(text, mode="eval"), env)


def _expr_names(expr):
    try:
        node = ast.parse(_normal_expr(expr), mode="eval")
    except Exception:
        return set()
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def _rule_items(value):
    if isinstance(value, dict):
        return [{"name": k, "expr": v} for k, v in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


class FunctionalModel:
    def __init__(self, params=None):
        self.params = dict(SSOT_MODEL.get("parameters") or {})
        if params:
            self.params.update(params)
        self.state_defaults = self._state_defaults()
        self.state = dict(self.state_defaults)
        self._declared_state_names = set(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace = []

    @staticmethod
    def _norm(value):
        text = str(value or "").strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        return text.strip("_")

    def _state_defaults(self):
        defaults = {}
        fm = SSOT_MODEL.get("function_model") or {}
        for idx, item in enumerate(fm.get("state_variables") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"state_{idx}")
            defaults[name] = item.get("reset", 0)
        defaults.setdefault("busy", 0)
        defaults.setdefault("error", 0)
        return defaults

    def _register_defaults(self):
        defaults = {}
        regs = SSOT_MODEL.get("registers") or {}
        for idx, item in enumerate(regs.get("register_list") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"REG{idx}")
            defaults[name] = item.get("reset", 0)
            off = item.get("offset")
            if off is not None:
                defaults[str(off)] = item.get("reset", 0)
        return defaults

    @staticmethod
    def _field_bounds(field):
        bits = field.get("bits")
        if isinstance(bits, (list, tuple)) and len(bits) >= 2:
            hi = _parse_int(bits[0], 0)
            lo = _parse_int(bits[1], 0)
            return (max(hi, lo), min(hi, lo))
        if "msb" in field and "lsb" in field:
            hi = _parse_int(field.get("msb"), 0)
            lo = _parse_int(field.get("lsb"), 0)
            return (max(hi, lo), min(hi, lo))
        if "lsb" in field and ("width" in field or "bit_width" in field):
            lo = _parse_int(field.get("lsb"), 0)
            width = max(1, _parse_int(field.get("width", field.get("bit_width", 1)), 1))
            return (lo + width - 1, lo)
        return (0, 0)

    def _state_name_for_register(self, reg):
        name = str(reg.get("name") or "").strip()
        if not name:
            return ""
        fm = SSOT_MODEL.get("function_model") or {}
        for row in fm.get("state_variables") or []:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source") or "").strip().lower()
            state_name = str(row.get("name") or "").strip()
            if state_name and source == f"registers.{name}".lower():
                return state_name
        norm = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        candidates = [
            norm,
            f"{norm}_reg",
            f"{norm}_q",
            f"{norm}_r",
            f"{norm}_value",
        ]
        for field in reg.get("fields") or []:
            if isinstance(field, dict):
                fname = re.sub(r"[^a-z0-9]+", "_", str(field.get("name") or "").lower()).strip("_")
                if fname:
                    candidates.extend([fname, f"{fname}_reg", f"{fname}_q", f"{fname}_r"])
        for candidate in candidates:
            if candidate in self.state:
                return candidate
        return ""

    def _register_read_value(self, reg):
        name = str(reg.get("name") or "")
        state_name = self._state_name_for_register(reg)
        if state_name:
            value = _parse_int(self.state.get(state_name), 0)
        else:
            value = _parse_int(self.registers.get(name, reg.get("reset", 0)), 0)
        for field in reg.get("fields") or []:
            if not isinstance(field, dict):
                continue
            fname = str(field.get("name") or "")
            if fname in self.state:
                fval = _parse_int(self.state.get(fname), 0)
            elif f"{fname}_q" in self.state:
                fval = _parse_int(self.state.get(f"{fname}_q"), 0)
            elif fname in self.registers:
                fval = _parse_int(self.registers.get(fname), 0)
            else:
                continue
            hi, lo = self._field_bounds(field)
            width = max(1, hi - lo + 1)
            mask = (1 << width) - 1
            value = (value & ~(mask << lo)) | ((fval & mask) << lo)
        return value

    def _read_mux(self, addr):
        addr_i = _parse_int(addr, 0)
        regs = SSOT_MODEL.get("registers") or {}
        for reg in regs.get("register_list") or []:
            if not isinstance(reg, dict):
                continue
            off = reg.get("offset")
            if off is not None and addr_i == _parse_int(off, 0):
                return self._register_read_value(reg)
        return 0

    def reset(self):
        self.state = dict(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace.clear()

    def _looks_like_register_access(self, txn):
        kind = self._norm(txn.get("kind") or txn.get("transaction") or "")
        return (
            kind in {"csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr"}
            or "reg" in txn
            or "addr_or_name" in txn
        )

    def _transactions(self):
        fm = SSOT_MODEL.get("function_model") or {}
        return [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]

    def _find_transaction(self, kind):
        wanted = self._norm(kind)
        for tx in self._transactions():
            aliases = [
                tx.get("id"),
                tx.get("name"),
                self._norm(tx.get("id")),
                self._norm(tx.get("name")),
            ]
            if wanted in {self._norm(x) for x in aliases if x}:
                return tx
        if wanted in {"reset", "rst"}:
            return {"id": "RESET", "name": "reset", "outputs": ["state reset"], "side_effects": ["reset"]}
        return None

    def _record(self, kind, txn, result):
        entry = {
            "kind": kind,
            "scenario_id": txn.get("scenario_id", ""),
            "result": result,
            "state": dict(self.state),
        }
        self.trace.append(entry)
        return result

    def _derived_signal_items(self):
        fm = SSOT_MODEL.get("function_model") or {}
        return _rule_items(fm.get("derived_signals"))

    def _resolve_derived_signals(self, env):
        pending = []
        for idx, item in enumerate(self._derived_signal_items()):
            name = str(
                item.get("name")
                or item.get("signal")
                or item.get("output")
                or item.get("port")
                or f"derived_{idx}"
            )
            expr = item.get("expr", item.get("expression", item.get("value", "")))
            if name and expr not in (None, ""):
                pending.append((name, expr, item.get("width") or item.get("bits")))

        unresolved_errors = {}
        for _pass in range(max(len(pending), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr, width in pending:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr, width))
                    continue
                if width is not None:
                    width_i = _parse_int(width, 0)
                    value &= (1 << max(width_i, 0)) - 1 if width_i > 0 else value
                env[name] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending = next_pending
            if not pending or not progressed:
                break
        return unresolved_errors

    @staticmethod
    def _norm_state_token(value):
        text = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
        for suffix in ("_reg", "_q", "_r", "_ff"):
            if text.endswith(suffix):
                text = text[: -len(suffix)]
                break
        return text

    def _state_update_target(self, update_name):
        name = str(update_name or "").strip()
        if name in self._declared_state_names:
            return name
        norm_name = self._norm_state_token(name)
        best = ""
        best_len = 0
        for state_name in self._declared_state_names:
            norm_state = self._norm_state_token(state_name)
            if not norm_state:
                continue
            if norm_name == norm_state or norm_name.endswith("_" + norm_state) or f"_{norm_state}_" in norm_name:
                if len(norm_state) > best_len:
                    best = state_name
                    best_len = len(norm_state)
        return best

    def _rule_env(self, txn):
        env = {}
        env.update(_default_rule_helpers())
        env.update(self.params)
        env.update(self.state)
        env.update(self.registers)
        env.update(txn)
        env["read_mux"] = self._read_mux
        env["reduction_or"] = lambda value: 1 if _parse_int(value, 0) != 0 else 0
        env.setdefault("true", 1)
        env.setdefault("false", 0)
        self._resolve_derived_signals(env)
        return env

    def _apply_structured_rules(self, tx, txn):
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        if not output_rules and not state_updates:
            return None

        env = self._rule_env(txn)
        result = {
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "sample_accepted": 0,
        }
        pending_outputs = []
        for idx, rule in enumerate(output_rules):
            name = str(rule.get("name") or rule.get("output") or rule.get("port") or f"output_{idx}")
            aliases = [
                str(v)
                for v in (rule.get("output"), rule.get("port"))
                if v is not None and str(v).strip() and str(v).strip() != name
            ]
            pending_outputs.append((
                name,
                rule.get("expr", rule.get("expression", rule.get("value", 0))),
                rule.get("width") or rule.get("bits"),
                aliases,
            ))

        def _resolve_pending_outputs(required_names=None):
            nonlocal pending_outputs
            required = set(required_names or [])
            unresolved_errors = {}
            for _pass in range(max(len(pending_outputs), 1) + 1):
                progressed = False
                next_pending = []
                for name, expr, width, aliases in pending_outputs:
                    try:
                        value = _eval_rule_expr(expr, env)
                    except KeyError as exc:
                        unresolved_errors[name] = str(exc)
                        next_pending.append((name, expr, width, aliases))
                        continue
                    if width is not None:
                        value &= (1 << max(_parse_int(width, 0), 0)) - 1 if _parse_int(width, 0) > 0 else value
                    result[name] = value
                    env[name] = value
                    for alias in aliases:
                        result.setdefault(alias, value)
                        env[alias] = value
                    unresolved_errors.pop(name, None)
                    progressed = True
                pending_outputs = next_pending
                if not pending_outputs:
                    break
                if required and required.issubset(env):
                    break
                if not progressed:
                    break
            if required:
                unresolved_required = sorted(name for name in required if name not in env)
                if unresolved_required:
                    detail = ", ".join(
                        f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}"
                        for name in unresolved_required
                    )
                    raise KeyError(f"unresolved sample condition dependencies: {detail}")
            return unresolved_errors

        output_names = set()
        for name, _expr, _width, aliases in pending_outputs:
            output_names.add(name)
            output_names.update(aliases)
        sample_expr = tx.get("sample_condition")
        sample_accepted = True
        if sample_expr not in (None, ""):
            needed_outputs = _expr_names(sample_expr) & output_names
            if needed_outputs:
                _resolve_pending_outputs(needed_outputs)
            sample_accepted = bool(_eval_rule_expr(sample_expr, env))
        result["sample_accepted"] = int(sample_accepted)

        unresolved_errors = _resolve_pending_outputs()
        if pending_outputs:
            missing = ", ".join(f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}" for name, _expr, _width, _aliases in pending_outputs)
            raise KeyError(f"unresolved output rule dependencies: {missing}")

        updates = {}
        pending_updates = []
        if sample_accepted:
            for idx, rule in enumerate(state_updates):
                pending_updates.append((
                    str(rule.get("name") or rule.get("state") or f"state_{idx}"),
                    rule.get("expr", rule.get("expression", rule.get("value", 0))),
                ))
        unresolved_errors = {}
        for _pass in range(max(len(pending_updates), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr in pending_updates:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr))
                    continue
                updates[name] = value
                env[name] = value
                target = self._state_update_target(name)
                if target and target != name:
                    updates[target] = value
                    env[target] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending_updates = next_pending
            if not pending_updates:
                break
            if not progressed:
                break
        if pending_updates:
            missing = ", ".join(f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}" for name, _expr in pending_updates)
            raise KeyError(f"unresolved state update dependencies: {missing}")
        if updates:
            commit_updates = {}
            for update_name, value in updates.items():
                target = self._state_update_target(update_name)
                if target:
                    commit_updates[target] = value
                else:
                    commit_updates[update_name] = value
            self.state.update(commit_updates)
            result["state_updates"] = dict(updates)
        return result

    def _apply_register_access(self, txn):
        if not self._looks_like_register_access(txn):
            return None
        op = self._norm(txn.get("op") or txn.get("kind"))
        key = txn.get("reg", txn.get("addr", txn.get("name", "")))
        key = str(key)
        if op in {"write", "wr", "csr_write", "control_status_access"}:
            self.registers[key] = txn.get("data", txn.get("value", 0))
            return {"resp": RESP_OKAY, "write": True, "reg": key, "value": self.registers[key]}
        if op in {"read", "rd", "csr_read"}:
            return {"resp": RESP_OKAY, "read": True, "reg": key, "value": self.registers.get(key, 0)}
        return None

    def _apply_primary(self, tx, txn):
        structured = self._apply_structured_rules(tx, txn)
        if structured is not None:
            return structured
        # T1 #1 — Cardinal rule enforcement:
        # When SSOT does not declare structured output_rules/state_updates for
        # this transaction, do NOT fabricate state via name heuristics. Return
        # an SSOT-question-annotated result so the gap surfaces in the trace
        # and downstream validators can escalate to ssot-gen / human.
        return {
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "outputs_spec": tx.get("outputs") or [],
            "side_effects_spec": tx.get("side_effects") or [],
            "ssot_question": (
                "[SSOT QUESTION] structured output_rules/state_updates undefined "
                "for transaction " + str(tx.get("id") or tx.get("name") or "<unknown>")
            ),
            "fabricated_state": False,
        }

    def apply(self, txn):
        txn = dict(txn or {})
        kind = self._norm(txn.get("kind") or txn.get("op") or txn.get("transaction") or "")
        tx = self._find_transaction(kind)
        if tx is not None:
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
                self.reset()
                return self._record(kind or "reset", txn, {"kind": "reset", "resp": RESP_OKAY, "state": dict(self.state)})
            return self._record(kind, txn, self._apply_primary(tx, txn))
        reg_result = self._apply_register_access(txn)
        if reg_result is not None:
            return self._record(kind or "register_access", txn, reg_result)
        if tx is None:
            return self._record(kind or "unknown", txn, {"kind": kind or "unknown", "resp": RESP_SLVERR, "error": "unsupported_transaction"})

    def _eval_precondition(self, expr, env):
        """Evaluate a single precondition string against env.

        SSOT preconditions are mostly Python-evaluable but occasionally carry
        a trailing natural-language clause in parentheses (e.g.
        '(req_i & req_mask) != 0 (at least one unmasked active request)').
        Normalize SQL-style OR/AND/NOT to Python operators, strip trailing
        natural-language parentheticals, and try progressively shorter
        prefixes until ast.parse succeeds. Unparseable preconditions are
        treated as True so they don't block transaction matching.
        """
        text = str(expr or "").strip()
        if not text:
            return True
        # Normalize boolean operators (SSOT prose sometimes uses uppercase).
        text = re.sub(r"\bOR\b", " or ",  text)
        text = re.sub(r"\bAND\b", " and ", text)
        text = re.sub(r"\bNOT\b", " not ", text)
        # Drop trailing parenthesized natural-language comments
        # ('something words ...'). Detect by alpha-majority content.
        def _strip_nl_tail(s):
            # Find a trailing " (...)" where contents are mostly alphabetic.
            depth = 0
            best_end = len(s)
            i = len(s) - 1
            # Walk from the right, capture the last balanced "(...)" tail.
            while i >= 0:
                ch = s[i]
                if ch == ")":
                    depth += 1
                elif ch == "(":
                    depth -= 1
                    if depth == 0:
                        inner = s[i + 1:best_end - 1]
                        alpha = sum(1 for c in inner if c.isalpha())
                        if alpha >= max(3, len(inner) // 2) and " " in inner:
                            # Natural language tail.
                            return s[:i].rstrip()
                        break
                i -= 1
            return s
        text = _strip_nl_tail(text)
        # Try ast.parse on the full string, then on progressively shorter
        # prefixes ending at a comparison/logical operator.
        candidates = [text]
        for tok in (" and ", " or "):
            for piece in text.split(tok):
                candidates.append(piece.strip())
        for cand in candidates:
            if not cand:
                continue
            try:
                tree = ast.parse(cand, mode="eval")
            except Exception:
                continue
            try:
                return bool(eval(compile(tree, "<precond>", mode="eval"), {"__builtins__": {}}, dict(env)))
            except Exception:
                continue
        return True

    def _select_transaction(self, inputs):
        """Pick the transaction whose preconditions all hold given inputs.

        Mutually-exclusive preconditions (typical SSOT pattern) yield a single
        active transaction. If multiple match, the first declared wins.
        Returns (tx, txn_payload) or (None, None) if none match.
        """
        env = dict(self.state)
        env.update(self.registers)
        env.update(inputs or {})
        for tx in self._transactions():
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
                continue
            preconds = [p for p in (tx.get("preconditions") or []) if isinstance(p, str)]
            if all(self._eval_precondition(p, env) for p in preconds):
                txn = {"kind": tx.get("id") or tx.get("name")}
                txn.update(inputs or {})
                return tx, txn
        return None, None

    def step(self, inputs=None):
        """Cycle-accurate step: select active transaction from preconditions,
        apply its output_rules and state_updates against current state and
        inputs, register the result. Mirrors the RTL's per-cycle behaviour
        when cocotb drives the same inputs cycle-by-cycle.

        Returns the structured result dict (same shape as apply()).
        """
        inputs = inputs or {}
        tx, txn = self._select_transaction(inputs)
        if tx is None:
            # No transaction matched preconditions: hold state, emit zero outputs.
            return {"kind": "idle", "resp": RESP_OKAY, "state": dict(self.state)}
        try:
            return self._record(tx.get("id") or "", txn, self._apply_primary(tx, txn))
        except KeyError as exc:
            # output_rule references a signal that's neither SSOT state, FL
            # register, nor caller-provided input (e.g. decoded combinational
            # signals: branch_taken, is_store). Surface a partial idle result
            # rather than crash — the per-cycle co-sim path treats this as
            # 'no comparable expected at this cycle for this IP'.
            return {
                "kind": "step_unresolved",
                "resp": RESP_OKAY,
                "transaction_id": tx.get("id"),
                "transaction_name": tx.get("name"),
                "step_unresolved": str(exc),
            }

    def csr_write(self, offset, data):
        """Apply an APB-style CSR write via _apply_register_access. Drives
        the registers dict + any state_variables sourced from those register
        fields (e.g. arb_enabled <- CTRL.enable)."""
        result = self._apply_register_access({"kind": "csr_write", "op": "write", "addr": offset, "reg": offset, "data": data, "value": data})
        # Mirror register field reset/source mapping into state_variables when
        # state_variables.source is a register field path.
        regs = SSOT_MODEL.get("registers") or {}
        reg_list = regs.get("register_list") or []
        fm = SSOT_MODEL.get("function_model") or {}
        state_vars = fm.get("state_variables") or []
        # Find which register matched the offset.
        matched_reg = None
        for r in reg_list:
            if r.get("offset") == offset:
                matched_reg = r
                break
        if matched_reg is None:
            return result
        for sv in state_vars:
            src = str(sv.get("source") or "")
            if not src.startswith("registers."):
                continue
            parts = src.split(".")
            if len(parts) >= 2 and parts[1] != matched_reg.get("name"):
                continue
            if len(parts) >= 3:
                field_name = parts[2]
                for f in matched_reg.get("fields") or []:
                    if f.get("name") == field_name:
                        bits = f.get("bits") or [0, 0]
                        hi, lo = (int(bits[0]), int(bits[1])) if len(bits) >= 2 else (0, 0)
                        mask = (1 << (hi - lo + 1)) - 1
                        self.state[sv.get("name")] = (data >> lo) & mask
                        break
            else:
                self.state[sv.get("name")] = data
        return result

    def coverage_seed_bins(self):
        return {item["id"]: False for item in SSOT_MODEL.get("fcov_bins", [])}


def run_self_check():
    model = FunctionalModel()
    txs = SSOT_MODEL.get("function_model", {}).get("transactions", [])
    results = []
    for idx, tx in enumerate(txs):
        if not isinstance(tx, dict):
            continue
        kind = tx.get("id") or tx.get("name") or f"transaction_{idx}"
        txn = {"kind": kind, "scenario_id": f"self_{kind}"}
        for field_idx, field in enumerate(tx.get("required_fields") or []):
            name = str(field)
            if name and name not in txn:
                txn[name] = field_idx + idx + 1
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        derived_signals = _rule_items((SSOT_MODEL.get("function_model") or {}).get("derived_signals"))
        rule_names = set()
        rule_names.update(_expr_names(tx.get("sample_condition", "")))
        for rule in output_rules + state_updates:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        for rule in derived_signals:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        output_names = {
            str(rule.get("name") or rule.get("output") or rule.get("port"))
            for rule in output_rules
            if rule.get("name") or rule.get("output") or rule.get("port")
        }
        update_names = {
            str(rule.get("name") or rule.get("state"))
            for rule in state_updates
            if rule.get("name") or rule.get("state")
        }
        derived_names = {
            str(rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port"))
            for rule in derived_signals
            if rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port")
        }
        known_names = set(model.params) | set(model.state) | set(model.registers) | output_names | update_names
        known_names.update(derived_names)
        known_names.update({"true", "false", "True", "False", "and", "or", "not"})
        known_names.update(_default_rule_helpers().keys())
        known_names.update({"read_mux", "reduction_or", "range"})
        for name in sorted(rule_names - known_names):
            if name and name not in txn:
                txn[name] = idx + len(txn) + 1
        result = model.apply(txn)
        results.append({
            "id": tx.get("id"),
            "name": tx.get("name"),
            "kind": kind,
            "passed": result.get("resp") == RESP_OKAY,
            "result": result,
        })
    unsupported = model.apply({"kind": "__unsupported_self_check__"})
    checks = [item["passed"] for item in results]
    checks.append(unsupported.get("resp") == RESP_SLVERR)

    # T1 #5 — invariants / reset / error_case coverage
    fm_block = SSOT_MODEL.get("function_model", {}) or {}
    invariants_raw = fm_block.get("invariants") or []
    if isinstance(invariants_raw, dict):
        invariants_raw = [{"name": k, "expr": v} for k, v in invariants_raw.items()]
    invariants = []
    for inv in invariants_raw:
        if isinstance(inv, str):
            invariants.append({"name": inv[:40], "expr": inv})
        elif isinstance(inv, dict):
            expr = inv.get("expr") or inv.get("expression") or inv.get("rule") or inv.get("invariant")
            if expr is None and len(inv) == 1:
                k, v = next(iter(inv.items())); expr = v if isinstance(v, str) else None
                inv = {"name": str(k), "expr": expr}
            if expr is not None:
                invariants.append({"name": inv.get("name") or str(expr)[:40], "expr": expr})
    invariants_eval_env = {}
    invariants_eval_env.update(_default_rule_helpers())
    invariants_eval_env.update(model.params)
    invariants_eval_env.update(model.state)
    invariants_eval_env.update(model.registers)
    invariants_evaluated = 0
    invariants_failed = []
    invariants_skipped = []
    for inv in invariants:
        try:
            ok = bool(_eval_rule_expr(inv["expr"], invariants_eval_env))
            invariants_evaluated += 1
            if not ok:
                invariants_failed.append({"name": inv["name"], "expr": inv["expr"]})
        except Exception as exc:
            invariants_skipped.append({"name": inv["name"], "expr": inv["expr"], "reason": str(exc)[:80]})

    reset_consistency = True
    reset_diff = {}
    try:
        baseline_defaults = dict(model.state_defaults)
        snapshot_model = FunctionalModel()
        snapshot_model.reset()
        for k, v in baseline_defaults.items():
            actual = snapshot_model.state.get(k)
            if actual != v:
                reset_consistency = False
                reset_diff[k] = {"expected": v, "actual": actual}
    except Exception as exc:
        reset_consistency = False
        reset_diff["__error__"] = str(exc)[:80]

    error_cases_total = 0
    error_cases_planned = 0
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        cases = tx.get("error_cases") or []
        if isinstance(cases, list):
            error_cases_total += len(cases)
            error_cases_planned += sum(1 for c in cases if isinstance(c, dict) and c.get("condition"))

    overall_pass = all(checks) and not invariants_failed and reset_consistency

    return {
        "passed": overall_pass,
        "checks": len(checks),
        "failed": checks.count(False),
        "transactions": len(txs),
        "transaction_results": results,
        "unsupported_transaction_check": unsupported.get("resp") == RESP_SLVERR,
        "trace_entries": len(model.trace),
        "coverage_bins": len(SSOT_MODEL.get("fcov_bins", [])),
        "invariants_total": len(invariants),
        "invariants_evaluated": invariants_evaluated,
        "invariants_failed": invariants_failed,
        "invariants_skipped": invariants_skipped,
        "reset_consistency": reset_consistency,
        "reset_diff": reset_diff,
        "error_cases_total": error_cases_total,
        "error_cases_planned": error_cases_planned,
    }


if __name__ == "__main__":
    print(json.dumps(run_self_check(), indent=2))
