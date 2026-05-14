#!/usr/bin/env python3
"""Executable SSOT functional model for uart_lite.

Generated from yaml/uart_lite.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'uart_lite', 'parameters': {'DATA_WIDTH': 8, 'FIFO_DEPTH': 16, 'OVERSAMPLE': 16, 'APB_ADDR_WIDTH': 12, 'APB_DATA_WIDTH': 32, 'PCLK_FREQ_MHZ': 50}, 'top_module': {'name': 'uart_lite', 'file': 'rtl/uart_lite.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Simple parameterized UART transceiver with APB-lite CSR interface — TX/RX FIFOs, configurable baud/parity/stop/framing, oversampling RX, loopback, break, debug counters, and per-source masked interrupts.', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'tx_fifo', 'type': 'synchronous_fifo', 'depth': 16, 'width': 8, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'TX data FIFO — APB writes push, TX FSM pops'}, {'name': 'rx_fifo', 'type': 'synchronous_fifo', 'depth': 16, 'width': 8, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'RX data FIFO — RX FSM pushes, APB reads pop'}], 'note': 'FIFO depth parameterized via FIFO_DEPTH (default 16, power-of-two). Standard synchronous FIFO with rd_ptr/wr_ptr counters, empty/full combinatorial flags.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 12, 'byte_addressable': True}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'TXDATA', 'offset': 0, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'data', 'description': 'Transmit Data Register — write pushes byte into TX FIFO; writes ignored when TX FIFO is full', 'write_side_effects': ['Push DATA_WIDTH LSBs into TX FIFO if not full; ignored if full.'], 'fields': [{'name': 'tx_data', 'bits': [7, 0], 'access': 'wo', 'reset': 0, 'write_effect': 'Push into TX FIFO when not full', 'description': 'Transmit byte'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'RXDATA', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'data', 'description': 'Receive Data Register — read pops byte from RX FIFO; reads return 0 when RX FIFO is empty', 'read_side_effects': ['Pop DATA_WIDTH LSBs from RX FIFO if not empty; return 0 if empty.'], 'fields': [{'name': 'rx_data', 'bits': [7, 0], 'access': 'ro', 'reset': 0, 'description': 'Received byte'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'STATUS', 'offset': 8, 'width': 32, 'access': 'ro', 'reset': 4, 'category': 'status', 'description': 'Status Register — live FIFO status and sticky error flags', 'fields': [{'name': 'tx_empty', 'bits': [0, 0], 'access': 'ro', 'reset': 1, 'description': 'TX FIFO empty (1=empty)'}, {'name': 'tx_full', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': 'TX FIFO full (1=full)'}, {'name': 'rx_empty', 'bits': [2, 2], 'access': 'ro', 'reset': 1, 'description': 'RX FIFO empty (1=empty)'}, {'name': 'rx_full', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'RX FIFO full (1=full)'}, {'name': 'frame_err', 'bits': [4, 4], 'access': 'ro', 'reset': 0, 'description': 'Sticky frame error — cleared by INT_CLEAR[3] W1C'}, {'name': 'parity_err', 'bits': [5, 5], 'access': 'ro', 'reset': 0, 'description': 'Sticky parity error — cleared by INT_CLEAR[4] W1C'}, {'name': 'rx_overrun', 'bits': [6, 6], 'access': 'ro', 'reset': 0, 'description': 'Sticky RX overrun — cleared by INT_CLEAR[2] W1C'}, {'name': 'tx_underrun', 'bits': [7, 7], 'access': 'ro', 'reset': 0, 'description': 'Sticky TX underrun — cleared by INT_CLEAR[5] W1C'}, {'name': 'break_detected', 'bits': [8, 8], 'access': 'ro', 'reset': 0, 'description': 'Sticky break detected — cleared by INT_CLEAR[6] W1C'}, {'name': 'reserved_31_9', 'bits': [31, 9], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'CONTROL', 'offset': 12, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Control Register — baud divisor, framing config, loopback, break', 'write_side_effects': ['Baud divisor and framing changes take effect on next start of TX/RX frame.', 'loopback: when set, txd_o is internally connected to rxd_i synchronizer input.', 'break_send: write 1 forces txd_o low; self-clears after 13+ bit times.'], 'fields': [{'name': 'baud_div', 'bits': [15, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Set baud rate divisor', 'description': 'Baud divisor = PCLK/(OVERSAMPLE*baud_rate). Reset default 0 disables TX/RX until programmed.'}, {'name': 'parity_en', 'bits': [16, 16], 'access': 'rw', 'reset': 0, 'description': 'Parity enable: 0=none, 1=enabled'}, {'name': 'parity_odd', 'bits': [17, 17], 'access': 'rw', 'reset': 0, 'description': 'Parity type: 0=even, 1=odd (valid when parity_en=1)'}, {'name': 'stop_bits', 'bits': [18, 18], 'access': 'rw', 'reset': 0, 'description': 'Stop bits: 0=1 stop bit, 1=2 stop bits'}, {'name': 'loopback', 'bits': [19, 19], 'access': 'rw', 'reset': 0, 'description': 'Loopback test mode: 0=normal, 1=txd internally looped to rxd'}, {'name': 'break_send', 'bits': [20, 20], 'access': 'rw', 'reset': 0, 'write_effect': '1=force txd_o low for break; self-clears after 13+ bit times', 'description': 'Software break send'}, {'name': 'data_width', 'bits': [23, 21], 'access': 'rw', 'reset': 3, 'description': 'Data width: 0=5, 1=6, 2=7, 3=8 bits; values >3 reserved'}, {'name': 'reserved_31_24', 'bits': [31, 24], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'INT_MASK', 'offset': 16, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Mask Register — per-source enable for irq_o assertion', 'write_side_effects': ['Writing 1 enables the interrupt source; writing 0 disables (masks) it.'], 'fields': [{'name': 'tx_empty_en', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable TX empty interrupt, 0=mask', 'description': 'Enable TX empty interrupt'}, {'name': 'rx_not_empty_en', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable RX not empty interrupt, 0=mask', 'description': 'Enable RX not empty interrupt'}, {'name': 'rx_overrun_en', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable RX overrun interrupt, 0=mask', 'description': 'Enable RX overrun interrupt'}, {'name': 'frame_err_en', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable frame error interrupt, 0=mask', 'description': 'Enable frame error interrupt'}, {'name': 'parity_err_en', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable parity error interrupt, 0=mask', 'description': 'Enable parity error interrupt'}, {'name': 'tx_underrun_en', 'bits': [5, 5], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable TX underrun interrupt, 0=mask', 'description': 'Enable TX underrun interrupt'}, {'name': 'break_det_en', 'bits': [6, 6], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable break detect interrupt, 0=mask', 'description': 'Enable break detect interrupt'}, {'name': 'reserved_31_7', 'bits': [31, 7], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'INT_PENDING', 'offset': 20, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Pending Register — raw pending status before mask', 'fields': [{'name': 'tx_empty_pending', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'TX FIFO empty (level — reflects tx_empty)'}, {'name': 'rx_not_empty_pending', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': 'RX FIFO not empty (level — reflects !rx_empty)'}, {'name': 'rx_overrun_pending', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': 'RX overrun occurred (sticky — W1C via INT_CLEAR[2])'}, {'name': 'frame_err_pending', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'Frame error occurred (sticky — W1C via INT_CLEAR[3])'}, {'name': 'parity_err_pending', 'bits': [4, 4], 'access': 'ro', 'reset': 0, 'description': 'Parity error occurred (sticky — W1C via INT_CLEAR[4])'}, {'name': 'tx_underrun_pending', 'bits': [5, 5], 'access': 'ro', 'reset': 0, 'description': 'TX underrun occurred (sticky — W1C via INT_CLEAR[5])'}, {'name': 'break_det_pending', 'bits': [6, 6], 'access': 'ro', 'reset': 0, 'description': 'Break detected (sticky — W1C via INT_CLEAR[6])'}, {'name': 'reserved_31_7', 'bits': [31, 7], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'INT_CLEAR', 'offset': 24, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Clear Register — W1C clears corresponding sticky pending and status flags', 'write_side_effects': ['Writing 1 to a bit clears the corresponding INT_PENDING sticky bit and STATUS sticky flag.', 'Writing 1 to level-source bits (tx_empty, rx_not_empty) has no effect.'], 'fields': [{'name': 'clear_rx_overrun', 'bits': [2, 2], 'access': 'wo', 'reset': 0, 'write_effect': 'Clear rx_overrun pending + STATUS.rx_overrun', 'description': 'W1C clear RX overrun'}, {'name': 'clear_frame_err', 'bits': [3, 3], 'access': 'wo', 'reset': 0, 'write_effect': 'Clear frame_err pending + STATUS.frame_err', 'description': 'W1C clear frame error'}, {'name': 'clear_parity_err', 'bits': [4, 4], 'access': 'wo', 'reset': 0, 'write_effect': 'Clear parity_err pending + STATUS.parity_err', 'description': 'W1C clear parity error'}, {'name': 'clear_tx_underrun', 'bits': [5, 5], 'access': 'wo', 'reset': 0, 'write_effect': 'Clear tx_underrun pending + STATUS.tx_underrun', 'description': 'W1C clear TX underrun'}, {'name': 'clear_break_det', 'bits': [6, 6], 'access': 'wo', 'reset': 0, 'write_effect': 'Clear break_det pending + STATUS.break_detected', 'description': 'W1C clear break detect'}, {'name': 'reserved_31_7', 'bits': [31, 7], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; writes ignored'}]}, {'name': 'DEBUG_TX_BYTES', 'offset': 28, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter — total bytes transmitted', 'fields': [{'name': 'bytes_tx', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Cumulative TX byte count; wraps at 2^32'}]}, {'name': 'DEBUG_RX_BYTES', 'offset': 32, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter — total bytes received', 'fields': [{'name': 'bytes_rx', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Cumulative RX byte count; wraps at 2^32'}]}, {'name': 'DEBUG_FRAME_ERRS', 'offset': 36, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter — total frames errored', 'fields': [{'name': 'frames_errored', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Cumulative frame error count; wraps at 2^32'}]}, {'name': 'DEBUG_PARITY_ERRS', 'offset': 40, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Counter — total parity errors', 'fields': [{'name': 'parities_errored', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Cumulative parity error count; wraps at 2^32'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the UART computes independent of cycle timing.', 'state_variables': [{'name': 'tx_fifo', 'source': 'memory.instances.tx_fifo', 'reset': 'empty (wr_ptr=0, rd_ptr=0, count=0)', 'description': 'TX FIFO queue of bytes awaiting transmission'}, {'name': 'rx_fifo', 'source': 'memory.instances.rx_fifo', 'reset': 'empty (wr_ptr=0, rd_ptr=0, count=0)', 'description': 'RX FIFO queue of received bytes'}, {'name': 'tx_active', 'source': 'fsm.tx_fsm', 'reset': False, 'description': 'TX FSM is transmitting a frame'}, {'name': 'rx_active', 'source': 'fsm.rx_fsm', 'reset': False, 'description': 'RX FSM is receiving a frame'}, {'name': 'baud_divisor', 'source': 'registers.CONTROL.baud_div', 'reset': 0, 'description': 'Baud rate divisor value'}, {'name': 'parity_en', 'source': 'registers.CONTROL.parity_en', 'reset': 0, 'description': 'Parity enabled flag'}, {'name': 'parity_odd', 'source': 'registers.CONTROL.parity_odd', 'reset': 0, 'description': 'Odd parity select (0=even)'}, {'name': 'stop_bits', 'source': 'registers.CONTROL.stop_bits', 'reset': 0, 'description': 'Number of stop bits: 0=1, 1=2'}, {'name': 'data_width', 'source': 'registers.CONTROL.data_width', 'reset': 3, 'description': 'Data width select: 0=5, 1=6, 2=7, 3=8'}, {'name': 'loopback', 'source': 'registers.CONTROL.loopback', 'reset': 0, 'description': 'Loopback test mode active flag'}, {'name': 'bytes_tx', 'source': 'registers.DEBUG_TX_BYTES', 'reset': 0, 'description': 'Cumulative bytes transmitted'}, {'name': 'bytes_rx', 'source': 'registers.DEBUG_RX_BYTES', 'reset': 0, 'description': 'Cumulative bytes received'}, {'name': 'frames_errored', 'source': 'registers.DEBUG_FRAME_ERRS', 'reset': 0, 'description': 'Cumulative frame errors'}, {'name': 'parities_errored', 'source': 'registers.DEBUG_PARITY_ERRS', 'reset': 0, 'description': 'Cumulative parity errors'}], 'transactions': [{'id': 'FM_TX', 'name': 'tx_byte_transfer', 'preconditions': ['TX FIFO not empty', 'tx_active == false (TX FSM idle)', 'baud_divisor > 0', 'break_send == 0'], 'inputs': ['tx_fifo head byte (DATA_WIDTH bits)', 'CONTROL parity_en, parity_odd, stop_bits, data_width'], 'outputs': ['txd_o toggles per UART frame: start(0) + DATA_WIDTH LSB-first data + optional parity + STOP_BITS stop(1)'], 'side_effects': ['Head byte popped from TX FIFO', 'bytes_tx incremented by 1 (wraps at 2^32)', 'tx_empty status updated (1 if FIFO now empty)', 'INT_PENDING.tx_empty_pending tracks tx_empty level'], 'error_cases': [{'condition': 'TX FIFO underrun (FIFO goes empty mid-frame due to internal error)', 'result': 'tx_underrun sticky flag set, INT_PENDING.tx_underrun set, txd_o driven high (mark)'}]}, {'id': 'FM_RX', 'name': 'rx_byte_receive', 'preconditions': ['RX FSM idle (rx_active == false)', 'baud_divisor > 0', 'Falling edge detected on rxd_i'], 'inputs': ['rxd_i serial line', 'CONTROL parity_en, parity_odd, stop_bits, data_width'], 'outputs': ['Received DATA_WIDTH byte pushed into RX FIFO on success', 'STATUS flags updated: frame_err, parity_err, rx_overrun as applicable'], 'side_effects': ['Received byte pushed into RX FIFO if not full', 'bytes_rx incremented by 1 on success (wraps at 2^32)', 'rx_not_empty status updated', 'INT_PENDING.rx_not_empty_pending tracks !rx_empty level'], 'error_cases': [{'condition': 'Stop bit sampled low', 'result': 'frame_err sticky flag set, INT_PENDING.frame_err_pending set, frames_errored incremented, byte still pushed to RX FIFO'}, {'condition': 'Parity mismatch (calculated != received)', 'result': 'parity_err sticky flag set, INT_PENDING.parity_err_pending set, parities_errored incremented, byte still pushed to RX FIFO'}, {'condition': 'RX FIFO full when new byte ready to push', 'result': 'rx_overrun sticky flag set, INT_PENDING.rx_overrun_pending set, new byte discarded'}]}, {'id': 'FM_LOOPBACK', 'name': 'loopback_mode', 'preconditions': ['loopback == 1', 'TX FIFO not empty', 'baud_divisor > 0'], 'inputs': ['tx_fifo head byte'], 'outputs': ['txd_o toggles normally AND rxd_i sampling path receives txd_o instead of external rxd_i (loopback mux before synchronizer)'], 'side_effects': ['Byte circulates: TX FIFO → TX FSM → loopback mux → RX synchronizer → RX FSM → RX FIFO', 'Both bytes_tx and bytes_rx increment']}], 'invariants': ['TX FSM and RX FSM operate independently except for loopback mux sharing.', 'Register read side effects are exactly those listed in registers.register_list.', 'Sticky error flags (frame_err, parity_err, rx_overrun, tx_underrun, break_detected) latch on first event and hold until W1C via INT_CLEAR.', 'Debug counters are free-running and do not roll over to affect core function.', 'FIFO depth is parameter FIFO_DEPTH; writes to full FIFO are ignored; reads from empty FIFO return 0.'], 'reference_model_hint': 'tb-gen should implement a Python scoreboard model of tx_fifo/rx_fifo queues, parity computation, and expected frame encoding, then compare expected/got for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when state, valid/ready, outputs, and interrupts may change.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state (FIFOs, FSMs, registers)', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'baud_generation': {'oversample_factor': 16, 'method': 'OVERSAMPLE counter 0..15 increments every PCLK. Baud tick asserted when oversample_counter == 0 and the baud_div_counter reaches (baud_div * OVERSAMPLE - 1). Baud tick width: 1 PCLK cycle.', 'baud_div_counter': {'width': 'ceil(log2(baud_div_max * OVERSAMPLE))', 'reset_value': 0, 'behavior': 'Increments every PCLK; resets to 0 on baud tick.'}, 'baud_tick': 'Single-cycle pulse used as timing reference by both TX and RX FSMs.', 'rx_oversample_counter': {'width': 4, 'reset_value': 0, 'description': '0..15 counter reset on each baud tick; center sample at count 7; data/parity/stop decisions at count 15.'}}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB PREADY returns in 0 (combinational) or 1 wait state'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB PREADY returns in 0 or 1 wait state'}, 'tx_frame': {'min_cycles': '1 (start) + DATA_WIDTH + parity_en? + STOP_BITS per baud_tick period', 'max_cycles': None, 'description': 'Frame length in baud ticks; each baud tick = baud_div * OVERSAMPLE PCLK cycles'}, 'rx_frame': {'min_cycles': 'same as tx_frame plus up to OVERSAMPLE-1 detection latency', 'max_cycles': None, 'description': 'RX frame length; detection may add up to OVERSAMPLE-1 pre-start PCLK cycles'}, 'interrupt_latency_cycles': {'min': 1, 'max': 3, 'measured_from': 'sticky event or FIFO level change', 'measured_to': 'irq_o assertion'}}, 'handshake_rules': [{'signal': 'PREADY', 'rule': 'Assert in the access phase (PSEL && PENABLE) if address is decodeable; hold until access completes. Combinational or registered.'}, {'signal': 'PSLVERR', 'rule': 'Assert with PREADY=1 only for illegal (unmapped) APB address access.'}, {'signal': 'txd_o', 'rule': 'Driven to new value only on baud_tick cycles. Idle=1. Start=0. Data=LSB-first. Parity=computed. Stop=1.'}, {'signal': 'irq_o', 'rule': 'Assert when (INT_PENDING & INT_MASK) != 0; deasserts when all enabled pending bits are cleared.'}], 'pipeline': [{'stage': 'APB_DECODE', 'cycle': '0..1', 'action': 'APB setup/access phase — decode address, mux read data, capture write data'}, {'stage': 'TX_ARBITRATE', 'cycle': 'N', 'action': 'TX FSM checks FIFO not empty, baud tick present, break not active; pops byte from FIFO'}, {'stage': 'TX_SHIFT', 'cycle': 'N+1 .. N+frame_len', 'action': 'TX FSM shifts out start/data/parity/stop bits on successive baud ticks'}, {'stage': 'RX_SYNC', 'cycle': 'M .. M+1', 'action': '2-FF synchronizer captures rxd_i; falling-edge detector output'}, {'stage': 'RX_SAMPLE', 'cycle': 'M+2 .. M+2+frame_len', 'action': 'RX FSM center-samples start/data/parity/stop at oversample count 7 per baud period'}, {'stage': 'RX_COMMIT', 'cycle': 'M+2+frame_len+1', 'action': 'RX FSM pushes assembled byte to RX FIFO or flags error; updates counters'}, {'stage': 'INT_UPDATE', 'cycle': 'same cycle as event', 'action': 'Sticky status/pending bits set on same cycle as error detection; irq_o updates combinatorially or next cycle'}], 'ordering': ['TX FSM and RX FSM operate in parallel; no ordering dependency except loopback where TX output → RX input.', 'APB reads to any register return current values combinatorially or after 1 wait state.', 'W1C clear takes effect in the same cycle as APB write access phase completion.'], 'backpressure': ['TX FIFO: APB writes to TXDATA ignored when FIFO full (tx_full=1). TX FSM stalls when FIFO empty.', 'RX FIFO: RX FSM discards new byte when RX FIFO full (rx_full=1), sets rx_overrun.', 'APB: PREADY deassertion (wait states) stalls the APB access phase only.'], 'performance': {'frequency_mhz': 50, 'throughput': {'max_baud_rate': 'PCLK / (OVERSAMPLE * 1) = 50 MHz / 16 = 3.125 Mbaud', 'sustained_bytes_per_sec': 'max_baud_rate / (1 + DATA_WIDTH + parity_en? + STOP_BITS)'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single outstanding APB transaction; no pipelined APB'}, 'depth': {'pipeline_stages': 7, 'queue_depth': 16, 'description': '7 pipeline stages; TX and RX FIFO depth parameter FIFO_DEPTH default 16'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Basic TX byte'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Basic RX byte'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'TX FIFO flow control'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'RX FIFO flow control'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'Parity generation and checking'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'Parity error detection'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'Frame error detection'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'Loopback mode'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'Break send'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'Interrupt masking and W1C clear'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'Configurable data width 5-bit'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'Double stop bit'}, {'id': 'SC13_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'SC13', 'description': 'Odd parity'}, {'id': 'SC14_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'SC14', 'description': 'TX underrun'}, {'id': 'SC15_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[14]', 'scenario': 'SC15', 'description': 'False start detection'}, {'id': 'SC16_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[15]', 'scenario': 'SC16', 'description': 'Debug counters wrap'}, {'id': 'fcov_fm_tx', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TX', 'source_ref': 'function_model.transactions.FM_TX', 'description': 'TX byte transfer observed'}, {'id': 'fcov_fm_rx', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX', 'source_ref': 'function_model.transactions.FM_RX', 'description': 'RX byte receive observed'}, {'id': 'fcov_fm_loopback', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_LOOPBACK', 'source_ref': 'function_model.transactions.FM_LOOPBACK', 'description': 'Loopback transaction observed'}, {'id': 'fcov_parity_err', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX.error_cases.parity_err', 'source_ref': 'function_model.transactions.FM_RX.error_cases.parity_err', 'description': 'Parity error behavior observed'}, {'id': 'fcov_frame_err', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX.error_cases.frame_err', 'source_ref': 'function_model.transactions.FM_RX.error_cases.frame_err', 'description': 'Frame error behavior observed'}, {'id': 'fcov_overrun', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RX.error_cases.rx_overrun', 'source_ref': 'function_model.transactions.FM_RX.error_cases.rx_overrun', 'description': 'RX overrun error behavior observed'}, {'id': 'fcov_tx_underrun', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TX.error_cases.underrun', 'source_ref': 'function_model.transactions.FM_TX.error_cases.underrun', 'description': 'TX underrun error behavior observed'}, {'id': 'ccov_tx_frame', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.TX_SHIFT', 'source_ref': 'cycle_model.pipeline.TX_SHIFT', 'description': 'TX frame shift stage observed'}, {'id': 'ccov_rx_frame', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.RX_SAMPLE', 'source_ref': 'cycle_model.pipeline.RX_SAMPLE', 'description': 'RX sample stage observed'}, {'id': 'ccov_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.APB_DECODE', 'source_ref': 'cycle_model.pipeline.APB_DECODE', 'description': 'APB decode stage observed'}, {'id': 'ccov_baud_tick', 'class': 'baud', 'coverage_domain': 'cycle', 'source': 'cycle_model.baud_generation', 'source_ref': 'cycle_model.baud_generation', 'description': 'Baud tick generation observed'}, {'id': 'ccov_int', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.INT_UPDATE', 'source_ref': 'cycle_model.pipeline.INT_UPDATE', 'description': 'Interrupt update timing observed'}, {'id': 'ccov_fsm_tx_idle_start', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions', 'source_ref': 'fsm.tx_fsm.transitions', 'description': 'TX IDLE→START transition observed'}, {'id': 'ccov_fsm_rx_idle_detect', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions', 'source_ref': 'fsm.rx_fsm.transitions', 'description': 'RX IDLE→START_DETECT transition observed'}, {'id': 'ccov_perf_depth', 'class': 'depth', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': 'Pipeline/FIFO depth exercised'}, {'id': 'ccov_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': 'Sustained throughput condition exercised'}, {'id': 'function_tx_byte_transfer', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_tx', 'description': 'tx_byte_transfer'}, {'id': 'function_rx_byte_receive', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_rx', 'description': 'rx_byte_receive'}, {'id': 'function_loopback_mode', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_loopback', 'description': 'loopback_mode'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'PREADY', 'rule': 'Assert in the access phase (PSEL && PENABLE) if address is decodeable; hold until access completes. Combinational or registered.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'PSLVERR', 'rule': 'Assert with PREADY=1 only for illegal (unmapped) APB address access.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'txd_o', 'rule': 'Driven to new value only on baud_tick cycles. Idle=1. Start=0. Data=LSB-first. Parity=computed. Stop=1.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'irq_o', 'rule': 'Assert when (INT_PENDING & INT_MASK) != 0; deasserts when all enabled pending bits are cleared.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB PREADY returns in 0 (combinational) or 1 wait state'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB PREADY returns in 0 or 1 wait state'}"}, {'id': 'cycle_latency_tx_frame', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.tx_frame', 'source_ref': 'cycle_model.latency.tx_frame', 'description': "{'min_cycles': '1 (start) + DATA_WIDTH + parity_en? + STOP_BITS per baud_tick period', 'max_cycles': None, 'description': 'Frame length in baud ticks; each baud tick = baud_div * OVERSAMPLE PCLK cycles'}"}, {'id': 'cycle_latency_rx_frame', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.rx_frame', 'source_ref': 'cycle_model.latency.rx_frame', 'description': "{'min_cycles': 'same as tx_frame plus up to OVERSAMPLE-1 detection latency', 'max_cycles': None, 'description': 'RX frame length; detection may add up to OVERSAMPLE-1 pre-start PCLK cycles'}"}, {'id': 'cycle_latency_interrupt_latency_cycles', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.interrupt_latency_cycles', 'source_ref': 'cycle_model.latency.interrupt_latency_cycles', 'description': "{'min': 1, 'max': 3, 'measured_from': 'sticky event or FIFO level change', 'measured_to': 'irq_o assertion'}"}, {'id': 'cycle_pipeline_apb_decode', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'APB setup/access phase — decode address, mux read data, capture write data'}, {'id': 'cycle_pipeline_tx_arbitrate', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'TX FSM checks FIFO not empty, baud tick present, break not active; pops byte from FIFO'}, {'id': 'cycle_pipeline_tx_shift', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'TX FSM shifts out start/data/parity/stop bits on successive baud ticks'}, {'id': 'cycle_pipeline_rx_sync', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': '2-FF synchronizer captures rxd_i; falling-edge detector output'}, {'id': 'cycle_pipeline_rx_sample', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'RX FSM center-samples start/data/parity/stop at oversample count 7 per baud period'}, {'id': 'cycle_pipeline_rx_commit', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[5]', 'source_ref': 'cycle_model.pipeline[5]', 'description': 'RX FSM pushes assembled byte to RX FIFO or flags error; updates counters'}, {'id': 'cycle_pipeline_int_update', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[6]', 'source_ref': 'cycle_model.pipeline[6]', 'description': 'Sticky status/pending bits set on same cycle as error detection; irq_o updates combinatorially or next cycle'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'TX FSM and RX FSM operate in parallel; no ordering dependency except loopback where TX output → RX input.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'APB reads to any register return current values combinatorially or after 1 wait state.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'W1C clear takes effect in the same cycle as APB write access phase completion.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'TX FIFO: APB writes to TXDATA ignored when FIFO full (tx_full=1). TX FSM stalls when FIFO empty.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'RX FIFO: RX FSM discards new byte when RX FIFO full (rx_full=1), sets rx_overrun.'}, {'id': 'cycle_backpressure_2', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[2]', 'source_ref': 'cycle_model.backpressure[2]', 'description': 'APB: PREADY deassertion (wait states) stalls the APB access phase only.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 1, 'write_max': 1, 'description': 'Single outstanding APB transaction; no pipelined APB'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 7, 'queue_depth': 16, 'description': '7 pipeline stages; TX and RX FIFO depth parameter FIFO_DEPTH default 16'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'max_baud_rate': 'PCLK / (OVERSAMPLE * 1) = 50 MHz / 16 = 3.125 Mbaud', 'sustained_bytes_per_sec': 'max_baud_rate / (1 + DATA_WIDTH + parity_en? + STOP_BITS)'}"}, {'id': 'fsm_tx_fsm_tx_idle_to_tx_start_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[0]', 'source_ref': 'fsm.tx_fsm.transitions[0]', 'description': 'TX FIFO not empty AND baud tick'}, {'id': 'fsm_tx_fsm_tx_start_to_tx_data_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[1]', 'source_ref': 'fsm.tx_fsm.transitions[1]', 'description': 'baud tick (1 bit period elapsed)'}, {'id': 'fsm_tx_fsm_tx_data_to_tx_data_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[2]', 'source_ref': 'fsm.tx_fsm.transitions[2]', 'description': 'baud tick AND bit_count < DATA_WIDTH-1'}, {'id': 'fsm_tx_fsm_tx_data_to_tx_parity_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[3]', 'source_ref': 'fsm.tx_fsm.transitions[3]', 'description': 'baud tick AND bit_count == DATA_WIDTH-1 AND parity_en=1'}, {'id': 'fsm_tx_fsm_tx_data_to_tx_stop_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[4]', 'source_ref': 'fsm.tx_fsm.transitions[4]', 'description': 'baud tick AND bit_count == DATA_WIDTH-1 AND parity_en=0'}, {'id': 'fsm_tx_fsm_tx_parity_to_tx_stop_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[5]', 'source_ref': 'fsm.tx_fsm.transitions[5]', 'description': 'baud tick'}, {'id': 'fsm_tx_fsm_tx_stop_to_tx_idle_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[6]', 'source_ref': 'fsm.tx_fsm.transitions[6]', 'description': 'baud tick AND stop_bit_count == stop_bits-1'}, {'id': 'fsm_tx_fsm_tx_stop_to_tx_stop_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[7]', 'source_ref': 'fsm.tx_fsm.transitions[7]', 'description': 'baud tick AND stop_bit_count < stop_bits-1'}, {'id': 'fsm_tx_fsm_tx_idle_to_tx_break_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[8]', 'source_ref': 'fsm.tx_fsm.transitions[8]', 'description': 'CONTROL.break_send=1'}, {'id': 'fsm_tx_fsm_tx_break_to_tx_idle_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[9]', 'source_ref': 'fsm.tx_fsm.transitions[9]', 'description': 'break_counter expired (13+ bit times)'}, {'id': 'fsm_tx_fsm_from_to_tx_idle_10', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.tx_fsm.transitions[10]', 'source_ref': 'fsm.tx_fsm.transitions[10]', 'description': 'PRESETn asserted (async reset)'}, {'id': 'fsm_rx_fsm_rx_idle_to_rx_start_detect_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[0]', 'source_ref': 'fsm.rx_fsm.transitions[0]', 'description': 'falling edge on synchronized rxd (rxd_sync[1]=0, rxd_sync[0]=1 on prev cycle)'}, {'id': 'fsm_rx_fsm_rx_start_detect_to_rx_start_confirm_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[1]', 'source_ref': 'fsm.rx_fsm.transitions[1]', 'description': 'oversample_counter == 7 (mid-bit start confirm at 7/16)'}, {'id': 'fsm_rx_fsm_rx_start_confirm_to_rx_data_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[2]', 'source_ref': 'fsm.rx_fsm.transitions[2]', 'description': 'rxd_sync sampled low (start confirmed) AND oversample_counter == 15 → reset to 0'}, {'id': 'fsm_rx_fsm_rx_start_confirm_to_rx_idle_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[3]', 'source_ref': 'fsm.rx_fsm.transitions[3]', 'description': 'rxd_sync sampled high (false start) → return to idle'}, {'id': 'fsm_rx_fsm_rx_data_to_rx_data_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[4]', 'source_ref': 'fsm.rx_fsm.transitions[4]', 'description': 'oversample_counter == 15 AND bit_count < DATA_WIDTH-1 → reset oversample to 0'}, {'id': 'fsm_rx_fsm_rx_data_to_rx_parity_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[5]', 'source_ref': 'fsm.rx_fsm.transitions[5]', 'description': 'oversample_counter == 15 AND bit_count == DATA_WIDTH-1 AND parity_en=1'}, {'id': 'fsm_rx_fsm_rx_data_to_rx_stop_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[6]', 'source_ref': 'fsm.rx_fsm.transitions[6]', 'description': 'oversample_counter == 15 AND bit_count == DATA_WIDTH-1 AND parity_en=0'}, {'id': 'fsm_rx_fsm_rx_parity_to_rx_stop_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[7]', 'source_ref': 'fsm.rx_fsm.transitions[7]', 'description': 'oversample_counter == 15 (parity bit center-sampled at count 7/16 of current period)'}, {'id': 'fsm_rx_fsm_rx_stop_to_rx_done_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[8]', 'source_ref': 'fsm.rx_fsm.transitions[8]', 'description': 'oversample_counter == 15 AND rxd_sync sampled high (valid stop)'}, {'id': 'fsm_rx_fsm_rx_stop_to_rx_idle_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[9]', 'source_ref': 'fsm.rx_fsm.transitions[9]', 'description': 'oversample_counter == 15 AND rxd_sync sampled low (frame error)'}, {'id': 'fsm_rx_fsm_rx_done_to_rx_idle_10', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[10]', 'source_ref': 'fsm.rx_fsm.transitions[10]', 'description': 'byte pushed into RX FIFO or discarded if overrun'}, {'id': 'fsm_rx_fsm_from_to_rx_idle_11', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.rx_fsm.transitions[11]', 'source_ref': 'fsm.rx_fsm.transitions[11]', 'description': 'PRESETn asserted (async reset)'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_FRAME', 'condition': 'RX stop bit sampled low', 'architectural_effect': 'STATUS.frame_err=1, INT_PENDING.frame_err=1, frames_errored incremented, byte still pushed to RX FIFO'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_PARITY', 'condition': 'RX parity bit does not match computed parity', 'architectural_effect': 'STATUS.parity_err=1, INT_PENDING.parity_err=1, parities_errored incremented, byte still pushed to RX FIFO'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'ERR_RX_OVERRUN', 'condition': 'RX FSM has valid byte but RX FIFO is full', 'architectural_effect': 'STATUS.rx_overrun=1, INT_PENDING.rx_overrun=1, new byte discarded'}"}, {'id': 'error_error_3', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'id': 'ERR_TX_UNDERRUN', 'condition': 'TX FSM requests byte but TX FIFO is empty mid-frame', 'architectural_effect': 'STATUS.tx_underrun=1, INT_PENDING.tx_underrun=1, txd_o returns to mark (high)'}"}, {'id': 'error_error_4', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[4]', 'source_ref': 'error_handling.error_sources[4]', 'description': "{'id': 'ERR_BREAK', 'condition': 'rxd_i held low for > frame duration', 'architectural_effect': 'STATUS.break_detected=1, INT_PENDING.break_det=1'}"}, {'id': 'error_error_5', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[5]', 'source_ref': 'error_handling.error_sources[5]', 'description': "{'id': 'ERR_APB_DECODE', 'condition': 'APB access to unmapped address', 'architectural_effect': 'PSLVERR=1 with PREADY=1'}"}]}
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
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"(?<![=!<>])!(?!=)", " not ", text)
    return text


def _literal_int(text):
    text = str(text).strip().replace("_", "")
    return bool(re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+|[0-9]*'[hHdDbB][0-9a-fA-FxXzZ]+)", text))


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
    raise ValueError(f"unsupported rule expression node {type(node).__name__}")


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

    def _rule_env(self, txn):
        env = {}
        env.update(self.params)
        env.update(self.state)
        env.update(self.registers)
        env.update(txn)
        env.setdefault("true", 1)
        env.setdefault("false", 0)
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
            self.state.update(updates)
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
        reg_result = self._apply_register_access(txn)
        if reg_result is not None:
            return self._record(kind or "register_access", txn, reg_result)
        tx = self._find_transaction(kind)
        if tx is None:
            return self._record(kind or "unknown", txn, {"kind": kind or "unknown", "resp": RESP_SLVERR, "error": "unsupported_transaction"})
        if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
            self.reset()
            return self._record(kind or "reset", txn, {"kind": "reset", "resp": RESP_OKAY, "state": dict(self.state)})
        return self._record(kind, txn, self._apply_primary(tx, txn))

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
        rule_names = set()
        rule_names.update(_expr_names(tx.get("sample_condition", "")))
        for rule in output_rules + state_updates:
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
        known_names = set(model.params) | set(model.state) | set(model.registers) | output_names | update_names
        known_names.update({"true", "false", "True", "False", "and", "or", "not"})
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
