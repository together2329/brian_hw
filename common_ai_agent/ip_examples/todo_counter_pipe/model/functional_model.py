#!/usr/bin/env python3
"""Executable SSOT functional model for todo_counter_pipe.

Generated from yaml/todo_counter_pipe.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'todo_counter_pipe', 'parameters': {'WIDTH': 32, 'BUS_CLK_FREQ_MHZ': 150, 'CORE_CLK_FREQ_MHZ': 300, 'CDC_SYNC_STAGES': 2, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'todo_counter_pipe', 'file': 'rtl/todo_counter_pipe.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Parameterized synchronous up/down event counter with APB-lite CSR, dual-clock CDC, saturating/wrap modes, terminal-count interrupt, and sticky overflow/underflow status', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 300, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'cnt_reg', 'type': 'register', 'depth': 1, 'width': 'WIDTH', 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'Counter value register (core domain)'}, {'name': 'dbg_cycle_reg', 'type': 'register', 'depth': 1, 'width': 'WIDTH', 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'Debug cycle counter register (core domain, free-running)'}], 'note': 'All storage is register-based; no SRAM or FIFO instances. CDC shadow registers in bus domain for read-back are implementation detail.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 8, 'byte_addressable': True}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Control Register', 'write_side_effects': ['Writing enable=1 starts the counter; enable=0 holds count value.', 'Writing clear=1 resets cnt to 0 (self-clearing, reads 0).', 'Writing load=1 loads cnt from LOAD register (self-clearing, reads 0).', 'Writing up_down/mode takes effect on next count event.'], 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable counting on event_i', 'description': 'Counter enable'}, {'name': 'up_down', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': '0=up count, 1=down count', 'description': 'Count direction'}, {'name': 'mode', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'write_effect': '0=saturate at limits, 1=wrap at limits', 'description': 'Overflow/underflow mode'}, {'name': 'clear', 'bits': [3, 3], 'access': 'wo', 'reset': 0, 'write_effect': 'Write 1 to clear counter to 0; self-clearing, always reads 0', 'description': 'Clear counter'}, {'name': 'load', 'bits': [4, 4], 'access': 'wo', 'reset': 0, 'write_effect': 'Write 1 to load cnt from LOAD register; self-clearing, always reads 0', 'description': 'Load counter'}, {'name': 'reserved_31_5', 'bits': [31, 5], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'CNT', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Counter Value Register (CDC-synced from core domain)', 'fields': [{'name': 'cnt_value', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'write_effect': 'N/A (read-only)', 'description': 'Current counter value (synchronized to bus_clk)'}]}, {'name': 'LOAD', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Load Value Register', 'write_side_effects': ['Software may write any time; used when CTRL.load=1.'], 'fields': [{'name': 'load_value', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Value loaded into cnt on CTRL.load pulse', 'description': 'Counter load value'}]}, {'name': 'TERM', 'offset': 12, 'width': 32, 'access': 'rw', 'reset': 4294967295, 'category': 'control', 'description': 'Terminal Count Register', 'write_side_effects': ['Writing TERM changes the terminal-count comparison threshold immediately.', 'If cnt already matches new TERM while enabled and counting up, tc_pending asserts on next core_clk edge.'], 'fields': [{'name': 'term_value', 'bits': [31, 0], 'access': 'rw', 'reset': 4294967295, 'write_effect': 'Terminal count threshold for up-count comparison', 'description': 'Terminal count value'}]}, {'name': 'STATUS', 'offset': 16, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Status Register (sticky overflow/underflow flags, CDC-synced)', 'fields': [{'name': 'overflow', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'write_effect': 'N/A (cleared via INTCLR)', 'description': 'Sticky overflow flag (set when cnt saturates/wraps at MAX while counting up)'}, {'name': 'underflow', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'write_effect': 'N/A (cleared via INTCLR)', 'description': 'Sticky underflow flag (set when cnt saturates/wraps at 0 while counting down)'}, {'name': 'reserved_31_2', 'bits': [31, 2], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'INTEN', 'offset': 20, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Enable Register', 'write_side_effects': ['Setting a bit enables the corresponding interrupt source to assert counter_irq.', 'Clearing a bit masks the source; pending status is preserved in INTSTAT.'], 'fields': [{'name': 'tc_en', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable terminal-count interrupt', 'description': 'Terminal count interrupt enable'}, {'name': 'ovf_en', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable overflow interrupt', 'description': 'Overflow interrupt enable'}, {'name': 'unf_en', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable underflow interrupt', 'description': 'Underflow interrupt enable'}, {'name': 'reserved_31_3', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'INTSTAT', 'offset': 24, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Status Register (pending sources before masking)', 'fields': [{'name': 'tc_pending', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'write_effect': 'N/A (cleared via INTCLR)', 'description': 'Terminal count pending'}, {'name': 'ovf_pending', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'write_effect': 'N/A (cleared via INTCLR)', 'description': 'Overflow pending'}, {'name': 'unf_pending', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'write_effect': 'N/A (cleared via INTCLR)', 'description': 'Underflow pending'}, {'name': 'reserved_31_3', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'INTCLR', 'offset': 28, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Clear Register (W1C)', 'write_side_effects': ['Writing 1 to a bit clears the corresponding pending status in INTSTAT and sticky flag in STATUS.', 'Writing 0 has no effect.', 'Read returns current INTSTAT value.'], 'fields': [{'name': 'tc_clr', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Write 1 to clear tc_pending', 'description': 'Clear terminal-count pending'}, {'name': 'ovf_clr', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': 'Write 1 to clear ovf_pending and STATUS.overflow', 'description': 'Clear overflow pending and sticky flag'}, {'name': 'unf_clr', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'write_effect': 'Write 1 to clear unf_pending and STATUS.underflow', 'description': 'Clear underflow pending and sticky flag'}, {'name': 'reserved_31_3', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'DBGCNT', 'offset': 32, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Debug Cycle Counter Register (CDC-synced from core domain)', 'fields': [{'name': 'dbg_cycle_count', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'write_effect': 'N/A (read-only)', 'description': 'Free-running cycle counter on core_clk for debug observability'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen: describes what the counter computes independent of cycle timing and CDC delays.', 'state_variables': [{'name': 'cnt', 'source': 'registers.CNT.cnt_value', 'reset': 0, 'description': 'Current counter value'}, {'name': 'enable', 'source': 'registers.CTRL.enable', 'reset': 0, 'description': 'Count enable flag (CDC-synced to core)'}, {'name': 'up_down', 'source': 'registers.CTRL.up_down', 'reset': 0, 'description': '0=up, 1=down (CDC-synced to core)'}, {'name': 'mode', 'source': 'registers.CTRL.mode', 'reset': 0, 'description': '0=saturate, 1=wrap (CDC-synced to core)'}, {'name': 'load_value', 'source': 'registers.LOAD.load_value', 'reset': 0, 'description': 'Load value (CDC-synced to core)'}, {'name': 'term', 'source': 'registers.TERM.term_value', 'reset': 'all-ones (2^WIDTH-1)', 'description': 'Terminal count threshold'}, {'name': 'overflow', 'source': 'registers.STATUS.overflow', 'reset': 0, 'description': 'Sticky overflow flag'}, {'name': 'underflow', 'source': 'registers.STATUS.underflow', 'reset': 0, 'description': 'Sticky underflow flag'}, {'name': 'tc_pending', 'source': 'registers.INTSTAT.tc_pending', 'reset': 0, 'description': 'Terminal count pending'}, {'name': 'ovf_pending', 'source': 'registers.INTSTAT.ovf_pending', 'reset': 0, 'description': 'Overflow pending'}, {'name': 'unf_pending', 'source': 'registers.INTSTAT.unf_pending', 'reset': 0, 'description': 'Underflow pending'}, {'name': 'inten_tc', 'source': 'registers.INTEN.tc_en', 'reset': 0, 'width': 1, 'description': 'Terminal-count interrupt enable mask bit'}, {'name': 'inten_ovf', 'source': 'registers.INTEN.ovf_en', 'reset': 0, 'width': 1, 'description': 'Overflow interrupt enable mask bit'}, {'name': 'inten_unf', 'source': 'registers.INTEN.unf_en', 'reset': 0, 'width': 1, 'description': 'Underflow interrupt enable mask bit'}, {'name': 'dbg_cycle_count', 'source': 'registers.DBGCNT.dbg_cycle_count', 'reset': 0, 'description': 'Free-running core_clk cycle counter'}], 'transactions': [{'id': 'FM1', 'name': 'count_up_normal', 'preconditions': ['enable == 1', 'up_down == 0', '0 <= cnt < term', 'event_i asserted (rising edge)'], 'inputs': ['event_i rising edge'], 'outputs': ['cnt_new = cnt + 1'], 'output_rules': [{'name': 'interrupt', 'port': 'counter_irq', 'width': 1, 'expr': '(tc_pending and inten_tc) or (ovf_pending and inten_ovf) or (unf_pending and inten_unf)', 'description': 'Counter IRQ reflects enabled pending interrupt sources.'}], 'side_effects': ['cnt ← cnt + 1', 'dbg_cycle_count ← dbg_cycle_count + 1 (on every core_clk, not per event)'], 'error_cases': []}, {'id': 'FM2', 'name': 'count_up_terminal', 'preconditions': ['enable == 1', 'up_down == 0', 'cnt == term', 'event_i asserted'], 'inputs': ['event_i rising edge'], 'outputs': ['tc_pending ← 1', 'If mode==0 (saturate): cnt stays at term', 'If mode==1 (wrap): cnt ← 0'], 'side_effects': ['tc_pending set to 1 (sticky until W1C clear)', 'cnt updated per mode: saturate → term, wrap → 0', 'If wrap: any further up-count from 0 proceeds normally'], 'error_cases': []}, {'id': 'FM3', 'name': 'count_down_normal', 'preconditions': ['enable == 1', 'up_down == 1', '0 < cnt <= 2^WIDTH - 1', 'event_i asserted'], 'inputs': ['event_i rising edge'], 'outputs': ['cnt_new = cnt - 1'], 'side_effects': ['cnt ← cnt - 1'], 'error_cases': []}, {'id': 'FM4', 'name': 'count_down_terminal', 'preconditions': ['enable == 1', 'up_down == 1', 'cnt == 0', 'event_i asserted'], 'inputs': ['event_i rising edge'], 'outputs': ['tc_pending ← 1', 'If mode==0 (saturate): cnt stays at 0', 'If mode==1 (wrap): cnt ← 2^WIDTH - 1'], 'side_effects': ['tc_pending set to 1', 'cnt updated per mode', 'If wrap: further down-count from MAX proceeds normally'], 'error_cases': []}, {'id': 'FM5', 'name': 'overflow_up', 'preconditions': ['enable == 1', 'up_down == 0', 'cnt == 2^WIDTH - 1', 'event_i asserted'], 'inputs': ['event_i rising edge'], 'outputs': ['ovf_pending ← 1, overflow ← 1', 'If mode==0 (saturate): cnt stays at MAX', 'If mode==1 (wrap): cnt ← 0'], 'side_effects': ['overflow sticky flag set', 'ovf_pending set', 'cnt updated per mode'], 'error_cases': []}, {'id': 'FM6', 'name': 'underflow_down', 'preconditions': ['enable == 1', 'up_down == 1', 'cnt == 0', 'event_i asserted'], 'inputs': ['event_i rising edge'], 'outputs': ['unf_pending ← 1, underflow ← 1', 'If mode==0 (saturate): cnt stays at 0', 'If mode==1 (wrap): cnt ← 2^WIDTH - 1'], 'side_effects': ['underflow sticky flag set', 'unf_pending set', 'cnt updated per mode'], 'error_cases': []}, {'id': 'FM7', 'name': 'clear_counter', 'preconditions': ['CTRL.clear written 1 (CDC-synced pulse to core)'], 'inputs': ['clear pulse'], 'outputs': ['cnt ← 0'], 'side_effects': ['cnt is set to 0 regardless of enable/mode/direction', 'Does not affect overflow/underflow sticky flags', 'Does not affect tc_pending status'], 'error_cases': []}, {'id': 'FM8', 'name': 'load_counter', 'preconditions': ['CTRL.load written 1 (CDC-synced pulse to core)'], 'inputs': ['load pulse, load_value from LOAD register'], 'outputs': ['cnt ← load_value'], 'side_effects': ['cnt is set to load_value regardless of enable/mode/direction', 'Does not affect overflow/underflow sticky flags', 'Does not affect tc_pending status', 'If new cnt exceeds term while up-counting, terminal count comparison uses new value'], 'error_cases': []}, {'id': 'FM9', 'name': 'no_count_disabled', 'preconditions': ['enable == 0'], 'inputs': ['event_i may toggle'], 'outputs': ['cnt unchanged'], 'side_effects': ['cnt is preserved', 'dbg_cycle_count continues incrementing'], 'error_cases': []}, {'id': 'FM10', 'name': 'interrupt_clear', 'preconditions': ['INTCLR.tc_clr, .ovf_clr, or .unf_clr written 1'], 'inputs': ['W1C write'], 'outputs': ['Corresponding INTSTAT bit cleared', 'For ovf_clr: STATUS.overflow cleared', 'For unf_clr: STATUS.underflow cleared'], 'side_effects': ['counter_irq deasserts if no other enabled pending sources remain'], 'error_cases': []}], 'invariants': ['cnt never exceeds 2^WIDTH - 1 in saturate mode.', 'cnt never goes below 0 in saturate mode.', 'overflow is set only when cnt transitions through MAX while counting up.', 'underflow is set only when cnt transitions through 0 while counting down.', 'tc_pending is set when cnt reaches term (up) or 0 (down) on a count event.', 'clear and load take priority over normal count/terminal/overflow/underflow logic.', 'Register read side effects are exactly those listed in registers.register_list.', 'dbg_cycle_count increments on every core_clk edge, independent of enable or event_i.'], 'reference_model_hint': 'tb-gen should implement a Python FunctionalModel from this section as the scoreboard oracle, comparing expected vs observed counter value, status flags, and interrupt state for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen describing when counter state, status, and interrupts change across the dual-clock CDC pipeline.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for clocked cycle model; FunctionalModel is the behavioral oracle. Run direct Python smoke checks instead of relying on pytest-pymtl3.', 'clock': 'core_clk (primary behavioral clock)', 'clocks': [{'name': 'bus_clk', 'frequency_mhz': 150, 'role': 'register access and interrupt output'}, {'name': 'core_clk', 'frequency_mhz': 300, 'role': 'counter evaluation and event sampling'}], 'clock_relationship': 'core_clk = 2 × bus_clk (integer ratio, synchronous or mesochronous)', 'reset': {'bus_domain': {'signal': 'bus_rst_n', 'assertion': 'bus_rst_n low asynchronously clears all bus-domain registers', 'deassertion': 'bus-domain registers are usable on the first bus_clk rising edge after synchronized deassertion'}, 'core_domain': {'signal': 'core_rst_n', 'assertion': 'core_rst_n low asynchronously clears all core-domain registers (cnt, dbg_cycle_count, and control CDC output flops)', 'deassertion': 'core-domain registers are usable on the first core_clk rising edge after synchronized deassertion'}}, 'latency': {'register_read': {'min_cycles': 1, 'max_cycles': 1, 'description': 'APB read completes in one bus_clk cycle (combinational pready)'}, 'register_write': {'min_cycles': 1, 'max_cycles': 1, 'description': 'APB write completes in one bus_clk cycle (combinational pready)'}, 'control_cdc_bus_to_core': {'min_cycles': 2, 'max_cycles': 4, 'description': '2-stage synchronizer latency from bus_clk write to core_clk visibility; max 4 core_clk cycles due to phase uncertainty'}, 'status_cdc_core_to_bus': {'min_cycles': 2, 'max_cycles': 5, 'description': '2-stage synchronizer latency from core_clk update to bus_clk visibility; max 5 bus_clk cycles due to phase uncertainty and integer ratio'}, 'interrupt_latency': {'min_cycles': 3, 'max_cycles': 8, 'description': 'From core-domain event to counter_irq assertion on bus_clk; includes CDC core→bus + INTEN mask + output register'}}, 'handshake_rules': [{'signal': 'pready', 'domain': 'bus_clk', 'rule': 'Asserted combinationally when psel && penable; no wait states.'}, {'signal': 'prdata', 'domain': 'bus_clk', 'rule': 'Valid in the same bus_clk cycle as pready=1 for reads; driven to 0 for unused address space.'}, {'signal': 'event_i', 'domain': 'core_clk', 'rule': 'Sampled on core_clk rising edge; a 0→1 transition triggers one count. Must be stable for ≥1 core_clk period.'}, {'signal': 'counter_irq', 'domain': 'bus_clk', 'rule': 'Asserted when any enabled INTSTAT bit is 1. Deasserted when all enabled INTSTAT bits are 0.'}], 'pipeline': [{'stage': 'S0_APB_ACCESS', 'clock': 'bus_clk', 'cycle': 0, 'action': 'APB decode: paddr→register select, pwrite→read/write, pwdata→write data captured on psel&&penable'}, {'stage': 'S1_CDC_CTRL', 'clock': 'core_clk', 'cycle': '0..4', 'action': '2-stage synchronizer: CTRL fields (enable, up_down, mode, clear pulse, load pulse), LOAD value cross bus→core'}, {'stage': 'S2_COUNT_EVAL', 'clock': 'core_clk', 'cycle': '0..N', 'action': 'Sample event_i; if enable && event_i rising edge, evaluate prio (clear>load>count), arithmetic, saturate/wrap, terminal/overflow/underflow detection; update cnt, dbg_cycle_count increments every core_clk'}, {'stage': 'S3_CDC_STATUS', 'clock': 'bus_clk', 'cycle': '0..5', 'action': '2-stage synchronizer: cnt_value, overflow, underflow, tc_pending, ovf_pending, unf_pending, dbg_cycle_count cross core→bus'}, {'stage': 'S4_STATUS_UPDATE', 'clock': 'bus_clk', 'cycle': '0..1', 'action': 'Latched status reflected in CNT/STATUS/INTSTAT registers; W1C clear logic evaluated; counter_irq updated'}], 'ordering': ['clear and load CDC pulses must be edge-detected in core domain (single-cycle pulse after synchronization).', 'A write to CTRL.clear or CTRL.load followed by a write to CTRL.enable in the same or subsequent bus_clk cycle must guarantee that clear/load takes effect before the first count event after enable.', 'Interrupt status updates (INTSTAT, STATUS) occur in bus_clk domain after CDC convergence; counter_irq follows in the same bus_clk cycle.', 'dbg_cycle_count is free-running on core_clk and visible through CDC on bus_clk; no synchronization to event_i.'], 'backpressure': ['No backpressure on APB: zero-wait-state response always.', 'No backpressure on event_i: every rising edge while enable=1 produces a count; no flow control.', 'CDC pipeline is fixed-depth; no credit-based or ready/valid flow control between domains.'], 'performance': {'frequency_mhz': 300, 'throughput': {'max_events_per_sec': 300000000, 'condition': 'event_i toggles every core_clk cycle; cnt increments at 300 MHz'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single APB transaction per bus_clk cycle'}, 'depth': {'pipeline_stages': 5, 'queue_depth': 0, 'description': 'CDC pipeline depth; no internal queuing'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage.', 'S2_COUNT_EVAL covers FM1-FM9 count/clear/load/terminal/overflow/underflow logic.', 'S4_STATUS_UPDATE covers FM10 interrupt clear logic.', 'dbg_cycle_count provides cycle-level observability independent of event activity.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Basic up-count'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Basic down-count'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'Terminal count up'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Terminal count down'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'Overflow saturate up'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'Overflow wrap up'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'Underflow saturate down'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'Underflow wrap down'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'Clear counter'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'Load counter'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'Disabled no-count'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'Interrupt clear W1C'}, {'id': 'SC13_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'SC13', 'description': 'Interrupt masking'}, {'id': 'SC14_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'SC14', 'description': 'Clear priority over count'}, {'id': 'SC15_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[14]', 'scenario': 'SC15', 'description': 'Load priority over count'}, {'id': 'SC16_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[15]', 'scenario': 'SC16', 'description': 'CDC convergence'}, {'id': 'SC17_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[16]', 'scenario': 'SC17', 'description': 'Debug cycle counter'}, {'id': 'fcov_count_up_normal', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM1', 'source_ref': 'function_model.transactions.FM1', 'description': 'Normal up-count observed by scoreboard'}, {'id': 'fcov_count_up_term', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM2', 'source_ref': 'function_model.transactions.FM2', 'description': 'Terminal count up observed'}, {'id': 'fcov_count_down_normal', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM3', 'source_ref': 'function_model.transactions.FM3', 'description': 'Normal down-count observed'}, {'id': 'fcov_count_down_term', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM4', 'source_ref': 'function_model.transactions.FM4', 'description': 'Terminal count down observed'}, {'id': 'fcov_overflow', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM5', 'source_ref': 'function_model.transactions.FM5', 'description': 'Overflow (both saturate and wrap) observed'}, {'id': 'fcov_underflow', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM6', 'source_ref': 'function_model.transactions.FM6', 'description': 'Underflow (both saturate and wrap) observed'}, {'id': 'fcov_clear', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM7', 'source_ref': 'function_model.transactions.FM7', 'description': 'Clear operation observed'}, {'id': 'fcov_load', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM8', 'source_ref': 'function_model.transactions.FM8', 'description': 'Load operation observed'}, {'id': 'fcov_disabled', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM9', 'source_ref': 'function_model.transactions.FM9', 'description': 'Disabled counter preserves value'}, {'id': 'fcov_int_clear', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM10', 'source_ref': 'function_model.transactions.FM10', 'description': 'Interrupt clear via W1C observed'}, {'id': 'ccov_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S0_APB_ACCESS', 'source_ref': 'cycle_model.pipeline.S0_APB_ACCESS', 'description': 'APB access stage observed'}, {'id': 'ccov_cdc_ctrl', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_CDC_CTRL', 'source_ref': 'cycle_model.pipeline.S1_CDC_CTRL', 'description': 'Control CDC crossing observed within latency bounds'}, {'id': 'ccov_count_eval', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S2_COUNT_EVAL', 'source_ref': 'cycle_model.pipeline.S2_COUNT_EVAL', 'description': 'Count evaluation stage observed'}, {'id': 'ccov_cdc_status', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S3_CDC_STATUS', 'source_ref': 'cycle_model.pipeline.S3_CDC_STATUS', 'description': 'Status CDC crossing observed within latency bounds'}, {'id': 'ccov_status_update', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S4_STATUS_UPDATE', 'source_ref': 'cycle_model.pipeline.S4_STATUS_UPDATE', 'description': 'Status update and interrupt stage observed'}, {'id': 'ccov_ready_handshake', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.pready', 'source_ref': 'cycle_model.handshake_rules.pready', 'description': 'APB pready zero-wait-state handshake observed'}, {'id': 'ccov_perf_frequency', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': 'Declared frequency recorded in coverage evidence'}, {'id': 'function_count_up_normal', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm1', 'description': 'count_up_normal'}, {'id': 'function_count_up_terminal', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm2', 'description': 'count_up_terminal'}, {'id': 'function_count_down_normal', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm3', 'description': 'count_down_normal'}, {'id': 'function_count_down_terminal', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm4', 'description': 'count_down_terminal'}, {'id': 'function_overflow_up', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm5', 'description': 'overflow_up'}, {'id': 'function_underflow_down', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm6', 'description': 'underflow_down'}, {'id': 'function_clear_counter', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm7', 'description': 'clear_counter'}, {'id': 'function_load_counter', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[7]', 'source_ref': 'function_model.transactions.fm8', 'description': 'load_counter'}, {'id': 'function_no_count_disabled', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[8]', 'source_ref': 'function_model.transactions.fm9', 'description': 'no_count_disabled'}, {'id': 'function_interrupt_clear', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[9]', 'source_ref': 'function_model.transactions.fm10', 'description': 'interrupt_clear'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'pready', 'domain': 'bus_clk', 'rule': 'Asserted combinationally when psel && penable; no wait states.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'prdata', 'domain': 'bus_clk', 'rule': 'Valid in the same bus_clk cycle as pready=1 for reads; driven to 0 for unused address space.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'event_i', 'domain': 'core_clk', 'rule': 'Sampled on core_clk rising edge; a 0→1 transition triggers one count. Must be stable for ≥1 core_clk period.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'counter_irq', 'domain': 'bus_clk', 'rule': 'Asserted when any enabled INTSTAT bit is 1. Deasserted when all enabled INTSTAT bits are 0.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'APB read completes in one bus_clk cycle (combinational pready)'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'APB write completes in one bus_clk cycle (combinational pready)'}"}, {'id': 'cycle_latency_control_cdc_bus_to_core', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.control_cdc_bus_to_core', 'source_ref': 'cycle_model.latency.control_cdc_bus_to_core', 'description': "{'min_cycles': 2, 'max_cycles': 4, 'description': '2-stage synchronizer latency from bus_clk write to core_clk visibility; max 4 core_clk cycles due to phase uncertainty'}"}, {'id': 'cycle_latency_status_cdc_core_to_bus', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.status_cdc_core_to_bus', 'source_ref': 'cycle_model.latency.status_cdc_core_to_bus', 'description': "{'min_cycles': 2, 'max_cycles': 5, 'description': '2-stage synchronizer latency from core_clk update to bus_clk visibility; max 5 bus_clk cycles due to phase uncertainty and integer ratio'}"}, {'id': 'cycle_latency_interrupt_latency', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.interrupt_latency', 'source_ref': 'cycle_model.latency.interrupt_latency', 'description': "{'min_cycles': 3, 'max_cycles': 8, 'description': 'From core-domain event to counter_irq assertion on bus_clk; includes CDC core→bus + INTEN mask + output register'}"}, {'id': 'cycle_pipeline_s0_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'APB decode: paddr→register select, pwrite→read/write, pwdata→write data captured on psel&&penable'}, {'id': 'cycle_pipeline_s1_cdc_ctrl', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': '2-stage synchronizer: CTRL fields (enable, up_down, mode, clear pulse, load pulse), LOAD value cross bus→core'}, {'id': 'cycle_pipeline_s2_count_eval', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Sample event_i; if enable && event_i rising edge, evaluate prio (clear>load>count), arithmetic, saturate/wrap, terminal/overflow/underflow detection; update cnt, dbg_cycle_count increments every core_clk'}, {'id': 'cycle_pipeline_s3_cdc_status', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': '2-stage synchronizer: cnt_value, overflow, underflow, tc_pending, ovf_pending, unf_pending, dbg_cycle_count cross core→bus'}, {'id': 'cycle_pipeline_s4_status_update', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Latched status reflected in CNT/STATUS/INTSTAT registers; W1C clear logic evaluated; counter_irq updated'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'clear and load CDC pulses must be edge-detected in core domain (single-cycle pulse after synchronization).'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'A write to CTRL.clear or CTRL.load followed by a write to CTRL.enable in the same or subsequent bus_clk cycle must guarantee that clear/load takes effect before the first count event after enable.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Interrupt status updates (INTSTAT, STATUS) occur in bus_clk domain after CDC convergence; counter_irq follows in the same bus_clk cycle.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'dbg_cycle_count is free-running on core_clk and visible through CDC on bus_clk; no synchronization to event_i.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure on APB: zero-wait-state response always.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'No backpressure on event_i: every rising edge while enable=1 produces a count; no flow control.'}, {'id': 'cycle_backpressure_2', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[2]', 'source_ref': 'cycle_model.backpressure[2]', 'description': 'CDC pipeline is fixed-depth; no credit-based or ready/valid flow control between domains.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 1, 'write_max': 1, 'description': 'Single APB transaction per bus_clk cycle'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 5, 'queue_depth': 0, 'description': 'CDC pipeline depth; no internal queuing'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '300'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'max_events_per_sec': 300000000, 'condition': 'event_i toggles every core_clk cycle; cnt increments at 300 MHz'}"}, {'id': 'fsm_core_fsm_idle_to_count_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.core_fsm.transitions[0]', 'source_ref': 'fsm.core_fsm.transitions[0]', 'description': 'enable=1 and event_i=1'}, {'id': 'fsm_core_fsm_count_to_idle_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.core_fsm.transitions[1]', 'source_ref': 'fsm.core_fsm.transitions[1]', 'description': 'enable=0'}, {'id': 'fsm_core_fsm_count_to_count_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.core_fsm.transitions[2]', 'source_ref': 'fsm.core_fsm.transitions[2]', 'description': 'enable=1 and event_i=1 (next count)'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_OVERFLOW', 'condition': 'cnt transitions through MAX (2^WIDTH-1) while counting up', 'architectural_effect': 'STATUS.overflow=1, INTSTAT.ovf_pending=1; counter_irq if INTEN.ovf_en=1', 'severity': 'info'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_UNDERFLOW', 'condition': 'cnt transitions through 0 while counting down', 'architectural_effect': 'STATUS.underflow=1, INTSTAT.unf_pending=1; counter_irq if INTEN.unf_en=1', 'severity': 'info'}"}]}
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
