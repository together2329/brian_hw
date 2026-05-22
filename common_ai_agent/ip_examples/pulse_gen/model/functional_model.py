#!/usr/bin/env python3
"""Executable SSOT functional model for pulse_gen.

Generated from yaml/pulse_gen.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'pulse_gen', 'parameters': {'PULSE_WIDTH_CYCLES': 1, 'PULSE_POLARITY': 'active_high', 'PULSE_OUT_WIDTH': 1, 'APB_ADDR_WIDTH': 8, 'CLOCK_FREQ_MHZ': 50, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'pulse_gen', 'file': 'rtl/pulse_gen.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'One-shot pulse generator with parameterized width, APB-Lite CSR configuration, and single-cycle trigger-to-output latency.', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No SRAM/FIFO/Register-file storage — all state held in flip-flops (FSM state, counter, config registers).'}, 'registers': {'config': {'register_width': 32, 'addr_width': 8, 'byte_addressable': True, 'channel_stride': 0, 'channel_base': 0, 'num_channels': 1}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Pulse control register — trigger fire and polarity select', 'write_side_effects': ['Writing fire=1 when STATUS.busy=0 initiates a new pulse (software trigger).', 'Writing fire=1 when STATUS.busy=1 is silently ignored (non-reentrant).', 'Polarity change takes effect on the next pulse; ongoing pulse is unaffected.'], 'fields': [{'name': 'fire', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'self-clearing trigger pulse; write 1 to fire', 'description': 'Software trigger (auto-clears after one PCLK)'}, {'name': 'polarity', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': '0=active_high, 1=active_low; applies to next pulse', 'description': 'Pulse polarity override'}, {'name': 'enable', 'bits': [2, 2], 'access': 'rw', 'reset': 1, 'write_effect': '0=generator disabled (triggers ignored), 1=enabled', 'description': 'Global enable'}, {'name': 'hw_trig_en', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'write_effect': '0=hardware trigger disabled, 1=trigger_i sampled', 'description': 'Hardware trigger enable'}, {'name': 'reserved_31_4', 'bits': [31, 4], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'STATUS', 'offset': 4, 'width': 32, 'access': 'mixed', 'reset': 0, 'category': 'status', 'description': 'Pulse generator status — busy flag and done indicator', 'write_side_effects': ['Writing 1 to done (W1C) clears the done flag and deasserts irq_o if no other pending source.'], 'fields': [{'name': 'busy', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': '1 = pulse output is currently asserted (pulse in progress)'}, {'name': 'done', 'bits': [1, 1], 'access': 'w1c', 'reset': 0, 'write_effect': 'W1C: writing 1 clears this bit and deasserts irq_o', 'description': 'Pulse completed flag'}, {'name': 'fired_count', 'bits': [17, 2], 'access': 'ro', 'reset': 0, 'description': 'Monotonically increasing count of completed pulses (wraps at 2^16)'}, {'name': 'reserved_31_18', 'bits': [31, 18], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'PULSE_WIDTH', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 1, 'category': 'config', 'description': 'Pulse width in PCLK cycles — overrides PULSE_WIDTH_CYCLES parameter at runtime', 'write_side_effects': ['New width applies to the next pulse; an in-progress pulse uses the width latched at its trigger time.', 'Value 0 is illegal and maps to 1 cycle (minimum pulse width is 1 PCLK).'], 'fields': [{'name': 'width', 'bits': [15, 0], 'access': 'rw', 'reset': 1, 'write_effect': 'Set pulse width in PCLK cycles (min 1)', 'description': 'Pulse width in PCLK cycles'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'INT_ENABLE', 'offset': 12, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Interrupt enable mask', 'fields': [{'name': 'done_ie', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': '0=disable done interrupt, 1=enable', 'description': 'Pulse-done interrupt enable'}, {'name': 'reserved_31_1', 'bits': [31, 1], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'ID', 'offset': 16, 'width': 32, 'access': 'ro', 'reset': 65568, 'category': 'debug', 'description': 'IP identification register', 'fields': [{'name': 'revision', 'bits': [7, 0], 'access': 'ro', 'reset': 32, 'description': 'Minor revision (0x20 = v0.32)'}, {'name': 'id', 'bits': [31, 8], 'access': 'ro', 'reset': 256, 'description': 'IP identifier (0x100 = pulse_gen)'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the IP computes independent of cycle timing.', 'state_variables': [{'name': 'fsm_state', 'source': 'fsm.pulse_fsm', 'reset': 'IDLE', 'description': 'Current FSM state'}, {'name': 'pulse_counter', 'source': 'internal counter', 'reset': 0, 'description': 'Elapsed pulse cycles in current pulse'}, {'name': 'latched_width', 'source': 'registers.PULSE_WIDTH.width', 'reset': 1, 'description': 'Pulse width captured at trigger time'}, {'name': 'latched_polarity', 'source': 'registers.CTRL.polarity', 'reset': 0, 'description': 'Polarity captured at trigger time (0=active_high)'}, {'name': 'ctrl_fire', 'source': 'registers.CTRL.fire', 'reset': 0, 'description': 'Software trigger — self-clearing'}, {'name': 'ctrl_enable', 'source': 'registers.CTRL.enable', 'reset': 1, 'description': 'Global enable gate'}, {'name': 'ctrl_hw_trig_en', 'source': 'registers.CTRL.hw_trig_en', 'reset': 0, 'description': 'Hardware trigger enable'}, {'name': 'status_busy', 'source': 'registers.STATUS.busy', 'reset': 0, 'description': 'Pulse in progress'}, {'name': 'status_done', 'source': 'registers.STATUS.done', 'reset': 0, 'description': 'Pulse completed (W1C clearable)'}, {'name': 'fired_count', 'source': 'registers.STATUS.fired_count', 'reset': 0, 'description': 'Monotonic count of completed pulses'}], 'transactions': [{'id': 'FM_FIRE', 'name': 'fire_pulse', 'preconditions': ['ctrl_enable == 1', 'status_busy == 0', '(ctrl_fire == 1) or (trigger_i == 1 and ctrl_hw_trig_en == 1)'], 'inputs': ['trigger event: ctrl_fire or trigger_i level', 'latched_width = max(registers.PULSE_WIDTH.width, 1)', 'latched_polarity = registers.CTRL.polarity'], 'outputs': [{'name': 'pulse_out_active', 'expr': "latched_polarity ? 1'b0 : 1'b1", 'width': 'PULSE_OUT_WIDTH', 'port': 'pulse_out', 'description': 'Active-level assertion during PULSE state'}, {'name': 'pulse_out_idle', 'expr': "latched_polarity ? 1'b1 : 1'b0", 'width': 'PULSE_OUT_WIDTH', 'port': 'pulse_out', 'description': 'Idle-level when not in PULSE state'}, {'name': 'irq_o', 'expr': 'status_done & INT_ENABLE.done_ie', 'width': 1, 'port': 'irq_o', 'description': 'Interrupt output driven by done status AND enable'}], 'output_rules': [{'name': 'pulse_out_active', 'expr': "latched_polarity ? 1'b0 : 1'b1", 'width': 'PULSE_OUT_WIDTH', 'port': 'pulse_out', 'description': 'Active-level assertion during PULSE state'}, {'name': 'pulse_out_idle', 'expr': "latched_polarity ? 1'b1 : 1'b0", 'width': 'PULSE_OUT_WIDTH', 'port': 'pulse_out', 'description': 'Idle-level when not in PULSE state'}, {'name': 'irq_o', 'expr': 'status_done & INT_ENABLE.done_ie', 'width': 1, 'port': 'irq_o', 'description': 'Interrupt output driven by done status AND enable'}], 'side_effects': ['fsm_state transitions: IDLE → PULSE → DONE → IDLE', 'pulse_counter increments each PCLK cycle while in PULSE state', 'fired_count increments by 1 at PULSE→DONE transition', 'ctrl_fire auto-clears to 0 after one PCLK cycle (self-clearing trigger)'], 'state_updates': [{'name': 'fsm_state', 'reset': 'IDLE', 'expr': 'IDLE→PULSE on trigger; PULSE→DONE when counter==width-1; DONE→IDLE after 1 cycle or W1C'}, {'name': 'pulse_counter', 'reset': 0, 'expr': '0 in IDLE/DONE; increments each cycle in PULSE'}, {'name': 'latched_width', 'reset': 1, 'expr': 'captured from PULSE_WIDTH register at trigger; held constant during PULSE'}, {'name': 'latched_polarity', 'reset': 0, 'expr': 'captured from CTRL.polarity at trigger; held constant during PULSE'}, {'name': 'status_busy', 'reset': 0, 'expr': '1 while fsm_state==PULSE; 0 otherwise'}, {'name': 'status_done', 'reset': 0, 'expr': 'set to 1 at PULSE→DONE transition; cleared by W1C write to STATUS.done'}, {'name': 'fired_count', 'reset': 0, 'expr': 'fired_count + 1 at PULSE→DONE transition; wraps at 2^16'}, {'name': 'ctrl_fire', 'reset': 0, 'expr': 'set to 1 by APB write; auto-clears to 0 after one PCLK'}], 'error_cases': [{'condition': 'trigger while status_busy==1', 'result': 'trigger ignored — non-reentrant; no error status raised'}, {'condition': 'PULSE_WIDTH.width written as 0', 'result': 'treated as width=1 on next trigger; no error raised'}, {'condition': 'ctrl_enable==0 when trigger arrives', 'result': 'trigger ignored; no pulse, no status change'}]}], 'invariants': ['pulse_out is at idle_level whenever fsm_state != PULSE.', 'pulse_out is never asserted for more or fewer cycles than latched_width.', 'STATUS.busy and pulse_out active are always coincident.', 'A new pulse cannot start while STATUS.busy==1 (non-reentrant).', 'irq_o is a pure combinational function of STATUS.done and INT_ENABLE.done_ie.', 'ctrl_fire is self-clearing: it is 1 for exactly one PCLK cycle after being written.'], 'reference_model_hint': 'tb-gen should implement a Python/C++ reference model that tracks fsm_state, pulse_counter, and latched_width, compares pulse_out waveform cycle-by-cycle, and checks irq_o = done & ie every cycle.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when state, outputs, and interrupts may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all state: FSM→IDLE, counter→0, STATUS→0, pulse_out→idle_level.', 'deassertion': 'State is usable on the first rising PCLK edge after synchronized deassertion.'}, 'latency': {'trigger_to_pulse_assert': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Rising PCLK edge after trigger acceptance drives pulse_out active (1-cycle latency)'}, 'pulse_assert_to_deassert': {'min_cycles': 1, 'max_cycles': 65536, 'description': 'Depends on latched_width: deassert after exactly latched_width cycles'}, 'pulse_done_to_irq': {'min_cycles': 0, 'max_cycles': 0, 'description': 'irq_o is combinational from STATUS.done & INT_ENABLE.done_ie; same cycle as done assertion'}, 'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'Zero-wait-state APB: PRDATA valid in access phase'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'Zero-wait-state APB: PWRITE accepted in access phase'}}, 'handshake_rules': [{'signal': 'PREADY', 'rule': 'Always 1 — zero-wait-state APB-Lite slave; no backpressure.'}, {'signal': 'PSLVERR', 'rule': 'Asserted only for unsupported address offsets; tied low for legal addresses.'}, {'signal': 'pulse_out', 'rule': 'Changes only on PCLK rising edges; glitch-free between edges.'}, {'signal': 'trigger_i', 'rule': 'Sampled on PCLK rising edge; must be stable at setup/hold time.'}], 'pipeline': [{'stage': 'S0_IDLE', 'cycle': 0, 'action': 'Sample trigger (CTRL.fire or trigger_i); if accepted, latch width/polarity and transition to PULSE'}, {'stage': 'S1_PULSE_COUNT', 'cycle': '1..W', 'action': 'Assert pulse_out at active level; increment pulse_counter each cycle; W = latched_width'}, {'stage': 'S2_DONE', 'cycle': 'W+1', 'action': 'Deassert pulse_out; set STATUS.done=1; increment fired_count; irq_o asserts if enabled; transition to IDLE'}], 'ordering': ['Trigger acceptance and pulse_out assertion are separated by exactly 1 PCLK cycle.', 'STATUS.done is set on the same rising edge that pulse_out deasserts.', 'irq_o reflects STATUS.done combinational — no extra cycle of interrupt latency.', 'ctrl_fire auto-clears on the rising edge after it was written (1-cycle self-clear).'], 'backpressure': ['No backpressure possible: zero-wait-state APB and no data-path handshake on pulse_out.'], 'performance': {'frequency_mhz': 50, 'throughput': {'sustained_pulses_per_cycle': '1/max(latched_width+1, 2)', 'condition': 'Back-to-back triggers with no W1C clear delay'}, 'outstanding': {'pulse_max': 1, 'description': 'Non-reentrant: only one pulse at a time'}, 'depth': {'pipeline_stages': 1, 'queue_depth': 1, 'description': 'Single-pulse FSM; no buffering'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.', 'STATUS.busy directly observable via APB read; pulse_out directly observable on output port.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Software single-cycle pulse'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Hardware trigger pulse'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'Multi-cycle pulse width'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Back-to-back pulses'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'Non-reentrant rejection'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'Disabled trigger rejection'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'Polarity inversion'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'Interrupt enable/disable'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'W1C STATUS.done clear'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'Runtime width change'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'Reset clears all state'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'APB illegal address'}, {'id': 'SC13_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'SC13', 'description': 'PULSE_WIDTH=0 clamp'}, {'id': 'SC14_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'SC14', 'description': 'fired_count wrap'}, {'id': 'SC15_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[14]', 'scenario': 'SC15', 'description': 'Simultaneous SW+HW trigger'}, {'id': 'fcov_fm_fire', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FIRE', 'source_ref': 'function_model.transactions.FM_FIRE', 'description': 'Legal FM_FIRE pulse observed by scoreboard'}, {'id': 'fcov_sw_trigger', 'class': 'trigger_source', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FIRE.preconditions[ctrl_fire]', 'source_ref': 'function_model.transactions.FM_FIRE.preconditions[ctrl_fire]', 'description': 'Software trigger path exercised'}, {'id': 'fcov_hw_trigger', 'class': 'trigger_source', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FIRE.preconditions[trigger_i]', 'source_ref': 'function_model.transactions.FM_FIRE.preconditions[trigger_i]', 'description': 'Hardware trigger path exercised'}, {'id': 'fcov_polarity_high', 'class': 'output_polarity', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FIRE.output_rules[pulse_out_active]', 'source_ref': 'function_model.transactions.FM_FIRE.output_rules[pulse_out_active]', 'description': 'Active-high pulse observed'}, {'id': 'fcov_polarity_low', 'class': 'output_polarity', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FIRE.output_rules[pulse_out_idle]', 'source_ref': 'function_model.transactions.FM_FIRE.output_rules[pulse_out_idle]', 'description': 'Active-low pulse observed'}, {'id': 'fcov_width_var', 'class': 'config', 'coverage_domain': 'function', 'source': 'function_model.state_variables[latched_width]', 'source_ref': 'function_model.state_variables[latched_width]', 'description': 'Runtime width change across pulses observed'}, {'id': 'fcov_err_busy_reject', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_FIRE.error_cases[trigger while busy]', 'source_ref': 'function_model.transactions.FM_FIRE.error_cases[trigger while busy]', 'description': 'Non-reentrant trigger rejection observed'}, {'id': 'ccov_idle_to_pulse', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S0_IDLE', 'source_ref': 'cycle_model.pipeline.S0_IDLE', 'description': 'Trigger acceptance stage observed'}, {'id': 'ccov_pulse_count', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_PULSE_COUNT', 'source_ref': 'cycle_model.pipeline.S1_PULSE_COUNT', 'description': 'Pulse counting stage observed'}, {'id': 'ccov_done', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S2_DONE', 'source_ref': 'cycle_model.pipeline.S2_DONE', 'description': 'Completion stage observed'}, {'id': 'ccov_1cycle_latency', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.trigger_to_pulse_assert', 'source_ref': 'cycle_model.latency.trigger_to_pulse_assert', 'description': '1-cycle trigger-to-pulse latency confirmed'}, {'id': 'ccov_fsm_all_states', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'fsm.pulse_fsm.states', 'source_ref': 'fsm.pulse_fsm.states', 'description': 'All FSM states visited: IDLE, PULSE, DONE'}, {'id': 'ccov_fsm_all_transitions', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pulse_fsm.transitions', 'source_ref': 'fsm.pulse_fsm.transitions', 'description': 'All FSM transitions exercised'}, {'id': 'ccov_irq_combinational', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pulse_done_to_irq', 'source_ref': 'cycle_model.latency.pulse_done_to_irq', 'description': 'Zero-cycle irq_o latency confirmed (combinational)'}, {'id': 'function_fire_pulse', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_fire', 'description': 'fire_pulse'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'PREADY', 'rule': 'Always 1 — zero-wait-state APB-Lite slave; no backpressure.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'PSLVERR', 'rule': 'Asserted only for unsupported address offsets; tied low for legal addresses.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'pulse_out', 'rule': 'Changes only on PCLK rising edges; glitch-free between edges.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'trigger_i', 'rule': 'Sampled on PCLK rising edge; must be stable at setup/hold time.'}"}, {'id': 'cycle_latency_trigger_to_pulse_assert', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.trigger_to_pulse_assert', 'source_ref': 'cycle_model.latency.trigger_to_pulse_assert', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Rising PCLK edge after trigger acceptance drives pulse_out active (1-cycle latency)'}"}, {'id': 'cycle_latency_pulse_assert_to_deassert', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pulse_assert_to_deassert', 'source_ref': 'cycle_model.latency.pulse_assert_to_deassert', 'description': "{'min_cycles': 1, 'max_cycles': 65536, 'description': 'Depends on latched_width: deassert after exactly latched_width cycles'}"}, {'id': 'cycle_latency_pulse_done_to_irq', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pulse_done_to_irq', 'source_ref': 'cycle_model.latency.pulse_done_to_irq', 'description': "{'min_cycles': 0, 'max_cycles': 0, 'description': 'irq_o is combinational from STATUS.done & INT_ENABLE.done_ie; same cycle as done assertion'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'Zero-wait-state APB: PRDATA valid in access phase'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'Zero-wait-state APB: PWRITE accepted in access phase'}"}, {'id': 'cycle_pipeline_s0_idle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Sample trigger (CTRL.fire or trigger_i); if accepted, latch width/polarity and transition to PULSE'}, {'id': 'cycle_pipeline_s1_pulse_count', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Assert pulse_out at active level; increment pulse_counter each cycle; W = latched_width'}, {'id': 'cycle_pipeline_s2_done', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Deassert pulse_out; set STATUS.done=1; increment fired_count; irq_o asserts if enabled; transition to IDLE'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Trigger acceptance and pulse_out assertion are separated by exactly 1 PCLK cycle.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'STATUS.done is set on the same rising edge that pulse_out deasserts.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'irq_o reflects STATUS.done combinational — no extra cycle of interrupt latency.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'ctrl_fire auto-clears on the rising edge after it was written (1-cycle self-clear).'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure possible: zero-wait-state APB and no data-path handshake on pulse_out.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'pulse_max': 1, 'description': 'Non-reentrant: only one pulse at a time'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 1, 'queue_depth': 1, 'description': 'Single-pulse FSM; no buffering'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_pulses_per_cycle': '1/max(latched_width+1, 2)', 'condition': 'Back-to-back triggers with no W1C clear delay'}"}, {'id': 'fsm_pulse_fsm_idle_to_pulse_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pulse_fsm.transitions[0]', 'source_ref': 'fsm.pulse_fsm.transitions[0]', 'description': '(CTRL.fire==1 || (trigger_i==1 && CTRL.hw_trig_en==1)) && CTRL.enable==1 && STATUS.busy==0'}, {'id': 'fsm_pulse_fsm_pulse_to_pulse_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pulse_fsm.transitions[1]', 'source_ref': 'fsm.pulse_fsm.transitions[1]', 'description': 'pulse_counter < latched_width - 1'}, {'id': 'fsm_pulse_fsm_pulse_to_done_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pulse_fsm.transitions[2]', 'source_ref': 'fsm.pulse_fsm.transitions[2]', 'description': 'pulse_counter == latched_width - 1'}, {'id': 'fsm_pulse_fsm_done_to_idle_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pulse_fsm.transitions[3]', 'source_ref': 'fsm.pulse_fsm.transitions[3]', 'description': 'STATUS.done cleared via W1C write or auto-clear after 1 cycle'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_WIDTH_ZERO', 'condition': 'PULSE_WIDTH.width == 0', 'architectural_effect': 'Treated as width=1; no error status; functional behavior preserved by min-clamp'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_TRIG_WHILE_BUSY', 'condition': 'Trigger asserted while STATUS.busy==1', 'architectural_effect': 'Ignored silently — non-reentrant; no error raised'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'ERR_DISABLED_TRIGGER', 'condition': 'Trigger while CTRL.enable==0', 'architectural_effect': 'Ignored; no state change'}"}, {'id': 'error_error_3', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'id': 'ERR_APB_ILLEGAL_ADDR', 'condition': 'APB access to unsupported offset', 'architectural_effect': 'PSLVERR=1, PRDATA=0'}"}]}
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
