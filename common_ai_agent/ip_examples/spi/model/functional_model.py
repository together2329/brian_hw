#!/usr/bin/env python3
"""Executable SSOT functional model for spi.

Generated from yaml/spi.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'spi', 'parameters': {'APB_ADDR_WIDTH': 12, 'APB_DATA_WIDTH': 32, 'DATA_WIDTH': 8, 'FIFO_DEPTH': 16, 'NUM_CS': 4, 'PRESCALE_WIDTH': 16, 'CPOL_RESET': 0, 'CPHA_RESET': 0, 'LSB_FIRST_RESET': 0, 'PCLK_FREQ_MHZ': 100}, 'top_module': {'name': 'spi', 'file': 'rtl/spi.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'APB-lite controlled SPI master with programmable frame format, TX/RX FIFOs, interrupting, and debug observability.', 'reference_spec': 'Project requirement seed: spi/req/spi_requirements.md', 'target': {'technology': 'generic', 'clock_freq_mhz': 100, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'tx_fifo', 'type': 'sync_fifo', 'depth': 16, 'width': 32, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'Transmit frame queue'}, {'name': 'rx_fifo', 'type': 'sync_fifo', 'depth': 16, 'width': 32, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'Receive frame queue'}], 'note': 'FIFO_DEPTH parameter scales both queues; occupancy exported via STATUS/DEBUG'}, 'registers': {'config': {'register_width': 32, 'addr_width': 12, 'byte_addressable': True}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Control register', 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable transfer launches'}, {'name': 'start', 'bits': [1, 1], 'access': 'wo', 'reset': 0, 'description': 'Start pulse request'}, {'name': 'cpol', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Clock polarity'}, {'name': 'cpha', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Clock phase'}, {'name': 'lsb_first', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'description': '1=LSB first, 0=MSB first'}, {'name': 'continuous_cs', 'bits': [5, 5], 'access': 'rw', 'reset': 0, 'description': 'Hold CS across back-to-back frames'}, {'name': 'loopback', 'bits': [6, 6], 'access': 'rw', 'reset': 0, 'description': 'Internal MOSI->MISO loopback'}, {'name': 'soft_reset', 'bits': [7, 7], 'access': 'wo', 'reset': 0, 'description': 'Pulse to clear FIFOs/status and return idle'}, {'name': 'cs_sel', 'bits': [10, 8], 'access': 'rw', 'reset': 0, 'description': 'Active chip-select index'}, {'name': 'data_width_m1', 'bits': [15, 11], 'access': 'rw', 'reset': 7, 'description': 'Frame width minus one; legal width 4..32'}]}, {'name': 'STATUS', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 18, 'description': 'Status and sticky error bits', 'fields': [{'name': 'busy', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'Transfer in progress'}, {'name': 'tx_full', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': 'TX FIFO full level'}, {'name': 'tx_empty', 'bits': [2, 2], 'access': 'ro', 'reset': 1, 'description': 'TX FIFO empty level'}, {'name': 'rx_full', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'RX FIFO full level'}, {'name': 'rx_empty', 'bits': [4, 4], 'access': 'ro', 'reset': 1, 'description': 'RX FIFO empty level'}, {'name': 'done', 'bits': [5, 5], 'access': 'ro', 'reset': 0, 'description': 'Frame-complete sticky event'}, {'name': 'tx_overrun', 'bits': [6, 6], 'access': 'ro', 'reset': 0, 'description': 'TX write while full'}, {'name': 'rx_overrun', 'bits': [7, 7], 'access': 'ro', 'reset': 0, 'description': 'RX push while full'}, {'name': 'rx_underrun', 'bits': [8, 8], 'access': 'ro', 'reset': 0, 'description': 'RX read while empty'}, {'name': 'mode_fault', 'bits': [9, 9], 'access': 'ro', 'reset': 0, 'description': 'Illegal launch config'}, {'name': 'illegal_access', 'bits': [10, 10], 'access': 'ro', 'reset': 0, 'description': 'Illegal APB access'}, {'name': 'cs_active', 'bits': [11, 11], 'access': 'ro', 'reset': 0, 'description': 'Any CS asserted'}]}, {'name': 'PRESCALE', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'SCLK prescale divisor', 'fields': [{'name': 'divisor', 'bits': [15, 0], 'access': 'rw', 'reset': 0, 'description': 'Half-period cycles = divisor+1'}]}, {'name': 'TXDATA', 'offset': 12, 'width': 32, 'access': 'wo', 'reset': 0, 'description': 'TX FIFO push payload', 'fields': [{'name': 'tx_payload', 'bits': [31, 0], 'access': 'wo', 'reset': 0, 'description': 'Frame data; only lower frame width bits used'}]}, {'name': 'RXDATA', 'offset': 16, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'RX FIFO pop payload', 'fields': [{'name': 'rx_payload', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Received frame data'}]}, {'name': 'INT_MASK', 'offset': 20, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Interrupt enables', 'fields': [{'name': 'done_en', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable done interrupt'}, {'name': 'tx_overrun_en', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'Enable tx_overrun interrupt'}, {'name': 'rx_overrun_en', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Enable rx_overrun interrupt'}, {'name': 'rx_underrun_en', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Enable rx_underrun interrupt'}, {'name': 'mode_fault_en', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'description': 'Enable mode_fault interrupt'}, {'name': 'illegal_access_en', 'bits': [5, 5], 'access': 'rw', 'reset': 0, 'description': 'Enable illegal_access interrupt'}, {'name': 'tx_empty_en', 'bits': [6, 6], 'access': 'rw', 'reset': 0, 'description': 'Enable tx_empty level interrupt'}, {'name': 'rx_full_en', 'bits': [7, 7], 'access': 'rw', 'reset': 0, 'description': 'Enable rx_full level interrupt'}]}, {'name': 'INT_PENDING', 'offset': 24, 'width': 32, 'access': 'ro', 'reset': 64, 'description': 'Raw pending interrupt sources', 'fields': [{'name': 'done_pend', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'Sticky done pending'}, {'name': 'tx_overrun_pend', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': 'Sticky tx_overrun pending'}, {'name': 'rx_overrun_pend', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': 'Sticky rx_overrun pending'}, {'name': 'rx_underrun_pend', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'Sticky rx_underrun pending'}, {'name': 'mode_fault_pend', 'bits': [4, 4], 'access': 'ro', 'reset': 0, 'description': 'Sticky mode_fault pending'}, {'name': 'illegal_access_pend', 'bits': [5, 5], 'access': 'ro', 'reset': 0, 'description': 'Sticky illegal_access pending'}, {'name': 'tx_empty_level', 'bits': [6, 6], 'access': 'ro', 'reset': 1, 'description': 'Level pending mirrors tx_empty'}, {'name': 'rx_full_level', 'bits': [7, 7], 'access': 'ro', 'reset': 0, 'description': 'Level pending mirrors rx_full'}]}, {'name': 'INT_CLEAR', 'offset': 28, 'width': 32, 'access': 'wo', 'reset': 0, 'description': 'W1C for sticky pending/status bits', 'fields': [{'name': 'w1c', 'bits': [7, 0], 'access': 'wo', 'reset': 0, 'description': 'Write 1 clears corresponding sticky bits; level bits unaffected'}]}, {'name': 'CS_IDLE', 'offset': 32, 'width': 32, 'access': 'rw', 'reset': 15, 'description': 'Idle chip-select output value', 'fields': [{'name': 'cs_idle_val', 'bits': [7, 0], 'access': 'rw', 'reset': 15, 'description': 'Bit value driven on csn_o when idle'}]}, {'name': 'DEBUG', 'offset': 36, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Debug counters/state', 'fields': [{'name': 'tx_count', 'bits': [4, 0], 'access': 'ro', 'reset': 0, 'description': 'TX FIFO occupancy'}, {'name': 'rx_count', 'bits': [9, 5], 'access': 'ro', 'reset': 0, 'description': 'RX FIFO occupancy'}, {'name': 'bit_index', 'bits': [15, 10], 'access': 'ro', 'reset': 0, 'description': 'Current bit index in active frame'}, {'name': 'active_cs', 'bits': [18, 16], 'access': 'ro', 'reset': 0, 'description': 'Currently asserted CS index'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for SPI transactions independent of exact cycle latency.', 'state_variables': [{'name': 'ctrl_enable', 'source': 'registers.CTRL.enable', 'reset': 0, 'description': 'Global transfer enable'}, {'name': 'ctrl_mode', 'source': 'registers.CTRL.{cpol,cpha,lsb_first,continuous_cs,loopback}', 'reset': '{cpol:CPOL_RESET,cpha:CPHA_RESET,lsb_first:LSB_FIRST_RESET,continuous_cs:0,loopback:0}', 'description': 'Latched transfer mode'}, {'name': 'active_cs', 'source': 'registers.CTRL.cs_sel', 'reset': 0, 'description': 'Selected chip-select index'}, {'name': 'frame_bits', 'source': 'registers.CTRL.data_width_m1+1', 'reset': 8, 'description': 'Runtime frame bit count (legal 4..32)'}, {'name': 'prescale_div', 'source': 'registers.PRESCALE.divisor', 'reset': 0, 'description': 'SCLK half-period divisor'}, {'name': 'tx_fifo', 'source': 'memory.instances.tx_fifo', 'reset': 'empty', 'description': 'Pending TX frames'}, {'name': 'rx_fifo', 'source': 'memory.instances.rx_fifo', 'reset': 'empty', 'description': 'Received RX frames'}, {'name': 'busy', 'source': 'registers.STATUS.busy', 'reset': 0, 'description': 'Frame in progress'}, {'name': 'sticky_errors', 'source': 'registers.STATUS.{tx_overrun,rx_overrun,rx_underrun,mode_fault,illegal_access}', 'reset': 0, 'description': 'Sticky error latches'}, {'name': 'int_pending', 'source': 'registers.INT_PENDING', 'reset': 0, 'description': 'Pending interrupt sources'}], 'transactions': [{'id': 'FM_APB_TX_PUSH', 'name': 'apb_write_txdata', 'preconditions': ['APB write handshake to TXDATA'], 'inputs': ['PWDATA[DATA_WIDTH-1:0]'], 'outputs': ['TX FIFO occupancy increments by one when not full'], 'side_effects': ['If tx_fifo full, payload is discarded and STATUS.tx_overrun set', 'tx_empty/tx_full level indicators update'], 'error_cases': [{'condition': 'unsupported PSTRB for TXDATA width', 'result': 'PSLVERR asserted and STATUS.illegal_access set'}]}, {'id': 'FM_FRAME_LAUNCH', 'name': 'launch_frame', 'preconditions': ['CTRL.start pulse observed', 'ctrl_enable == 1', 'busy == 0', 'tx_fifo not empty', 'cs_sel in [0, NUM_CS-1]', 'frame_bits in [4, 32]'], 'outputs': ['busy transitions to 1', 'One TX word is consumed from TX FIFO for shift register load'], 'side_effects': ['csn_o drives exactly one active-low bit at selected CS', 'SCLK idle level driven per CPOL before first active edge'], 'error_cases': [{'condition': 'cs_sel illegal or frame_bits illegal', 'result': 'No frame activity; STATUS.mode_fault set; pending mode fault interrupt source raised'}, {'condition': 'CTRL.enable == 0 or tx_fifo empty or busy==1', 'result': 'Launch suppressed without consuming TX FIFO'}]}, {'id': 'FM_SHIFT_SAMPLE', 'name': 'shift_and_sample_bits', 'preconditions': ['busy == 1'], 'inputs': ['miso_i sampled on mode-dependent sample edges or internal mosi_o if loopback=1'], 'outputs': ['mosi_o presents serialized transmit bits with configured bit order', 'rx_shift_reg accumulates sampled bits'], 'side_effects': ['bit_index progresses from 0 to frame_bits-1', 'done asserted when terminal sample edge occurs'], 'error_cases': [{'condition': 'none during legal frame', 'result': 'normal completion'}]}, {'id': 'FM_FRAME_COMPLETE', 'name': 'complete_frame_and_store_rx', 'preconditions': ['terminal sample edge reached'], 'outputs': ['busy transitions to 0', 'STATUS.done pulse/latched event generated'], 'side_effects': ['If RX FIFO has space, received frame pushed; else discard and STATUS.rx_overrun set', 'CS deasserts to CS_IDLE unless continuous_cs holds across back-to-back frame', 'Interrupt pending bits update for done and FIFO level'], 'error_cases': [{'condition': 'RX FIFO full', 'result': 'received word dropped, rx_overrun sticky set'}]}, {'id': 'FM_APB_RX_POP', 'name': 'apb_read_rxdata', 'preconditions': ['APB read handshake to RXDATA'], 'outputs': ['Returns oldest RX word when FIFO non-empty'], 'side_effects': ['RX FIFO occupancy decrements on successful pop'], 'error_cases': [{'condition': 'RX FIFO empty', 'result': 'Read returns zero and STATUS.rx_underrun set'}]}, {'id': 'FM_INT_CLEAR', 'name': 'w1c_interrupt_and_status_clear', 'preconditions': ['APB write handshake to INT_CLEAR'], 'outputs': ['Selected sticky pending/status bits cleared'], 'side_effects': ['FIFO level-derived pending bits remain level-sensitive and unaffected by W1C'], 'error_cases': [{'condition': 'write to read-only register or bad byte strobes', 'result': 'PSLVERR asserted and STATUS.illegal_access set'}]}], 'invariants': ['Only one csn_o bit may be active-low during an active frame.', 'No frame launch consumes TX FIFO unless all launch preconditions are true.', 'irq_o equals OR(INT_PENDING & INT_MASK) at all times.', 'sclk_o is a generated output waveform; no internal sequential process is clocked by sclk_o.', 'Sticky bits clear only via reset or INT_CLEAR W1C semantics.'], 'reference_model_hint': 'tb-gen scoreboard should model FIFO queues, mode-dependent edge behavior, bit order, and sticky/level interrupt semantics from these transactions.'}, 'cycle_model': {'purpose': 'Cycle-level timing and handshake contract for APB access and SPI serial engine', 'executable': 'pymtl3', 'backend_policy': 'Use Python behavioral model for expected values and cycle checkers for ready/valid, edge timing, and status updates.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears control/FIFOs/status/interrupt pending and drives csn_o to CS_IDLE', 'deassertion': 'State is valid after first rising PCLK edge following synchronized PRESETn release'}, 'latency': {'apb_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'PRDATA/PREADY returned in same or next cycle; no multi-cycle wait-state required'}, 'apb_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'Register writes accepted in same or next cycle'}, 'frame_launch_to_first_sclk_toggle': {'min_cycles': 1, 'max_cycles': None, 'description': 'Depends on prescale divisor'}, 'frame_total': {'min_cycles': 2, 'max_cycles': None, 'description': 'Proportional to frame_bits and prescale, plus APB/control overhead'}}, 'handshake_rules': [{'signal': 'APB', 'rule': 'Transfer occurs when PSEL && PENABLE && PREADY; PSLVERR valid in same transfer.'}, {'signal': 'CTRL.start', 'rule': 'Sampled as pulse request; hardware may auto-clear start bit after acceptance.'}, {'signal': 'launch_gate', 'rule': 'Shift FSM leaves IDLE only when all launch preconditions are simultaneously true.'}, {'signal': 'sclk_o', 'rule': 'Half-period equals (PRESCALE.divisor+1) PCLK cycles; CPOL controls idle level.'}, {'signal': 'sample_edge', 'rule': 'CPHA selects whether first active edge launches then samples or samples then launches.'}], 'pipeline': [{'stage': 'S0_APB_CFG', 'cycle': 't', 'action': 'Program mode/prescale/CS and push TX words'}, {'stage': 'S1_LAUNCH_CHECK', 'cycle': 't+0..t+1', 'action': 'Evaluate launch preconditions and latch frame context'}, {'stage': 'S2_ASSERT_CS', 'cycle': 'next', 'action': 'Drive selected chip select active-low'}, {'stage': 'S3_SHIFT', 'cycle': 'repeating', 'action': 'Generate sclk_o edges and launch MOSI bits'}, {'stage': 'S4_SAMPLE', 'cycle': 'repeating', 'action': 'Sample MISO/loopback bit and advance bit_index'}, {'stage': 'S5_COMPLETE', 'cycle': 'terminal', 'action': 'Push RX word if possible, update done/errors/pending, manage CS hold/deassert'}], 'ordering': ['For each frame, TX dequeue precedes first MOSI launch edge.', 'Final RX sample precedes done event and interrupt pending update for completion.', 'INT_CLEAR W1C effects apply after the write transfer edge and before next irq_o observation edge.'], 'backpressure': ['TX backpressure appears as tx_full; writes are dropped with tx_overrun when full.', 'RX backpressure appears as rx_full at completion; received frame is dropped with rx_overrun when full.'], 'performance': {'throughput': 'One frame every frame_bits*2*(divisor+1) PCLK cycles in steady state, excluding optional inter-frame gap', 'max_sclk_hz_formula': 'PCLK_FREQ_MHZ*1e6 / (2*(PRESCALE+1))'}, 'observability': ['Probe launch_accept, sample_edge, shift_edge, bit_index, cs_active, tx_fifo_level, rx_fifo_level, done_event']}, 'fcov_bins': [{'id': 'SC_APB_CONFIG_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_APB_CONFIG', 'description': 'APB config/readback'}, {'id': 'SC_BASIC_TRANSFER_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_BASIC_TRANSFER', 'description': 'Basic frame transfer'}, {'id': 'SC_CPOL_CPHA_SWEEP_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_CPOL_CPHA_SWEEP', 'description': 'CPOL/CPHA sweep'}, {'id': 'SC_LSB_FIRST_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_LSB_FIRST', 'description': 'LSB-first ordering'}, {'id': 'SC_WIDTH_SWEEP_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_WIDTH_SWEEP', 'description': 'Frame width sweep'}, {'id': 'SC_FIFO_LIMITS_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_FIFO_LIMITS', 'description': 'FIFO boundary behavior'}, {'id': 'SC_IRQ_W1C_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC_IRQ_W1C', 'description': 'Interrupt mask and W1C'}, {'id': 'SC_ERROR_PATHS_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC_ERROR_PATHS', 'description': 'Error paths'}, {'id': 'SC_PRESCALE_TIMING_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC_PRESCALE_TIMING', 'description': 'Prescale timing'}, {'id': 'SC_LOOPBACK_DEBUG_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC_LOOPBACK_DEBUG', 'description': 'Loopback and debug observability'}, {'id': 'fcov_tx_push_ok', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APB_TX_PUSH', 'source_ref': 'function_model.transactions.FM_APB_TX_PUSH', 'description': 'TXDATA accepted path'}, {'id': 'fcov_tx_push_overrun', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APB_TX_PUSH', 'source_ref': 'function_model.transactions.FM_APB_TX_PUSH', 'description': 'TX full drop path'}, {'id': 'fcov_launch_suppress', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FRAME_LAUNCH', 'source_ref': 'function_model.transactions.FM_FRAME_LAUNCH', 'description': 'Launch suppression paths'}, {'id': 'fcov_frame_complete', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FRAME_COMPLETE', 'source_ref': 'function_model.transactions.FM_FRAME_COMPLETE', 'description': 'Normal frame completion'}, {'id': 'ccov_apb_handshake', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'APB transfer and PSLVERR timing'}, {'id': 'ccov_spi_pipeline', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'All SPI pipeline stages observed'}, {'id': 'ccov_fsm_transitions', 'class': 'fsm', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions', 'source_ref': 'fsm.channel_level.transitions', 'description': 'Legal transitions covered'}, {'id': 'function_apb_write_txdata', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_apb_tx_push', 'description': 'apb_write_txdata'}, {'id': 'function_launch_frame', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_frame_launch', 'description': 'launch_frame'}, {'id': 'function_shift_and_sample_bits', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_shift_sample', 'description': 'shift_and_sample_bits'}, {'id': 'function_complete_frame_and_store_rx', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_frame_complete', 'description': 'complete_frame_and_store_rx'}, {'id': 'function_apb_read_rxdata', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_apb_rx_pop', 'description': 'apb_read_rxdata'}, {'id': 'function_w1c_interrupt_and_status_clear', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_int_clear', 'description': 'w1c_interrupt_and_status_clear'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'APB', 'rule': 'Transfer occurs when PSEL && PENABLE && PREADY; PSLVERR valid in same transfer.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'CTRL.start', 'rule': 'Sampled as pulse request; hardware may auto-clear start bit after acceptance.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'launch_gate', 'rule': 'Shift FSM leaves IDLE only when all launch preconditions are simultaneously true.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'sclk_o', 'rule': 'Half-period equals (PRESCALE.divisor+1) PCLK cycles; CPOL controls idle level.'}"}, {'id': 'cycle_handshake_4', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[4]', 'source_ref': 'cycle_model.handshake_rules[4]', 'description': "{'signal': 'sample_edge', 'rule': 'CPHA selects whether first active edge launches then samples or samples then launches.'}"}, {'id': 'cycle_latency_apb_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.apb_read', 'source_ref': 'cycle_model.latency.apb_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'PRDATA/PREADY returned in same or next cycle; no multi-cycle wait-state required'}"}, {'id': 'cycle_latency_apb_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.apb_write', 'source_ref': 'cycle_model.latency.apb_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'Register writes accepted in same or next cycle'}"}, {'id': 'cycle_latency_frame_launch_to_first_sclk_toggle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.frame_launch_to_first_sclk_toggle', 'source_ref': 'cycle_model.latency.frame_launch_to_first_sclk_toggle', 'description': "{'min_cycles': 1, 'max_cycles': None, 'description': 'Depends on prescale divisor'}"}, {'id': 'cycle_latency_frame_total', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.frame_total', 'source_ref': 'cycle_model.latency.frame_total', 'description': "{'min_cycles': 2, 'max_cycles': None, 'description': 'Proportional to frame_bits and prescale, plus APB/control overhead'}"}, {'id': 'cycle_pipeline_s0_apb_cfg', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Program mode/prescale/CS and push TX words'}, {'id': 'cycle_pipeline_s1_launch_check', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Evaluate launch preconditions and latch frame context'}, {'id': 'cycle_pipeline_s2_assert_cs', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Drive selected chip select active-low'}, {'id': 'cycle_pipeline_s3_shift', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Generate sclk_o edges and launch MOSI bits'}, {'id': 'cycle_pipeline_s4_sample', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Sample MISO/loopback bit and advance bit_index'}, {'id': 'cycle_pipeline_s5_complete', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[5]', 'source_ref': 'cycle_model.pipeline[5]', 'description': 'Push RX word if possible, update done/errors/pending, manage CS hold/deassert'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'For each frame, TX dequeue precedes first MOSI launch edge.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Final RX sample precedes done event and interrupt pending update for completion.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'INT_CLEAR W1C effects apply after the write transfer edge and before next irq_o observation edge.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'TX backpressure appears as tx_full; writes are dropped with tx_overrun when full.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'RX backpressure appears as rx_full at completion; received frame is dropped with rx_overrun when full.'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': 'One frame every frame_bits*2*(divisor+1) PCLK cycles in steady state, excluding optional inter-frame gap'}, {'id': 'fsm_channel_level_idle_to_check_launch_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[0]', 'source_ref': 'fsm.channel_level.transitions[0]', 'description': 'start_pulse'}, {'id': 'fsm_channel_level_check_launch_to_assert_cs_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[1]', 'source_ref': 'fsm.channel_level.transitions[1]', 'description': 'launch_gate_true'}, {'id': 'fsm_channel_level_check_launch_to_error_suppress_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[2]', 'source_ref': 'fsm.channel_level.transitions[2]', 'description': 'illegal_cs_or_width'}, {'id': 'fsm_channel_level_check_launch_to_idle_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[3]', 'source_ref': 'fsm.channel_level.transitions[3]', 'description': 'launch_gate_false_without_fault'}, {'id': 'fsm_channel_level_assert_cs_to_shift_edge_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[4]', 'source_ref': 'fsm.channel_level.transitions[4]', 'description': 'prescale_tick'}, {'id': 'fsm_channel_level_shift_edge_to_sample_edge_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[5]', 'source_ref': 'fsm.channel_level.transitions[5]', 'description': 'mode_edge_progress'}, {'id': 'fsm_channel_level_sample_edge_to_shift_edge_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[6]', 'source_ref': 'fsm.channel_level.transitions[6]', 'description': 'bit_index_not_last'}, {'id': 'fsm_channel_level_sample_edge_to_complete_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[7]', 'source_ref': 'fsm.channel_level.transitions[7]', 'description': 'bit_index_last'}, {'id': 'fsm_channel_level_complete_to_assert_cs_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[8]', 'source_ref': 'fsm.channel_level.transitions[8]', 'description': 'continuous_cs_and_next_launch_ready'}, {'id': 'fsm_channel_level_complete_to_idle_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[9]', 'source_ref': 'fsm.channel_level.transitions[9]', 'description': 'otherwise'}, {'id': 'fsm_channel_level_error_suppress_to_idle_10', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_level.transitions[10]', 'source_ref': 'fsm.channel_level.transitions[10]', 'description': 'one_cycle_report_done'}, {'id': 'error_illegal_apb_address', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'name': 'illegal_apb_address', 'detect': 'decode miss', 'effect': 'PSLVERR=1 for transfer; STATUS.illegal_access sticky set; INT_PENDING.illegal_access_pend sticky set'}"}, {'id': 'error_unsupported_write_strobe', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'name': 'unsupported_write_strobe', 'detect': 'PSTRB mismatch for accessed register policy', 'effect': 'PSLVERR=1; STATUS.illegal_access set'}"}, {'id': 'error_access_policy_violation', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'name': 'access_policy_violation', 'detect': 'write RO or read side-effect misuse policy', 'effect': 'PSLVERR=1; STATUS.illegal_access set'}"}, {'id': 'error_tx_overrun', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'name': 'tx_overrun', 'detect': 'TXDATA write when tx_full=1', 'effect': 'drop write data; set STATUS.tx_overrun and INT pending'}"}, {'id': 'error_rx_overrun', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[4]', 'source_ref': 'error_handling.error_sources[4]', 'description': "{'name': 'rx_overrun', 'detect': 'frame completion when rx_full=1', 'effect': 'drop received frame; set STATUS.rx_overrun and INT pending'}"}, {'id': 'error_rx_underrun', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[5]', 'source_ref': 'error_handling.error_sources[5]', 'description': "{'name': 'rx_underrun', 'detect': 'RXDATA read when rx_empty=1', 'effect': 'return zero; set STATUS.rx_underrun and INT pending'}"}, {'id': 'error_mode_fault', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[6]', 'source_ref': 'error_handling.error_sources[6]', 'description': "{'name': 'mode_fault', 'detect': 'launch attempt with illegal cs_sel or data_width', 'effect': 'suppress frame launch; set STATUS.mode_fault and INT pending'}"}]}
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
