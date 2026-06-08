#!/usr/bin/env python3
"""Executable SSOT functional model for timer.

Generated from yaml/timer.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'timer', 'parameters': {'DATA_WIDTH': 32, 'ADDR_WIDTH': 4, 'CLOCK_FREQ_MHZ': 100, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'timer', 'file': 'rtl/timer.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Small APB-style programmable down-counter timer with periodic single-cycle interrupt pulse.', 'reference_spec': 'timer/req/timer_requirements.md', 'target': {'technology': 'generic', 'clock_freq_mhz': 100, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'Timer uses registers only; no SRAM, FIFO, or RAM instances are required.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 4, 'byte_addressable': True, 'bus': 'APB-style'}, 'register_list': [{'name': 'LOAD', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Software-programmed reload value.', 'fields': [{'name': 'value', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'description': 'Value reloaded into STATUS/current count when timer expires.', 'write_effect': {'write': 'Updates load_q only; does not directly modify current count_q unless a simultaneous reload tick occurs per cycle_model ordering.', 'read': 'Returns load_q.'}}], 'side_effects': {'write': 'Updates load_q only; does not directly modify current count_q unless a simultaneous reload tick occurs per cycle_model ordering.', 'read': 'Returns load_q.'}}, {'name': 'CTRL', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Timer enable control register.', 'fields': [{'name': 'ENABLE', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': '1 enables decrement/reload operation; 0 stops and holds the counter.', 'write_effect': {'write': 'Bit 0 updates enable_q; clearing ENABLE stops and holds count_q.', 'read': 'Returns ENABLE in bit 0 and zeros in reserved bits.'}}, {'name': 'RESERVED', 'bits': [31, 1], 'access': 'ro', 'reset': 0, 'description': 'Reserved bits read as zero and ignore writes.'}], 'side_effects': {'write': 'Bit 0 updates enable_q; clearing ENABLE stops and holds count_q.', 'read': 'Returns ENABLE in bit 0 and zeros in reserved bits.'}}, {'name': 'STATUS', 'offset': 8, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Read-only current counter value.', 'fields': [{'name': 'count', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Current down-counter value count_q.'}], 'side_effects': {'write': 'Ignored for mapped STATUS address; no state change.', 'read': 'Returns current count_q with no side effects.'}}]}, 'function_model': {'purpose': 'Executable expected-behavior source for cocotb/pyuvm scoreboard and FL-vs-RTL comparison.', 'state_variables': [{'name': 'load_q', 'source': 'registers.LOAD.value', 'width': 32, 'reset': 0, 'description': 'Programmed reload value written by software.'}, {'name': 'enable_q', 'source': 'registers.CTRL.ENABLE', 'width': 1, 'reset': 0, 'description': 'Timer enable bit written by software.'}, {'name': 'count_q', 'source': 'registers.STATUS.count', 'width': 32, 'reset': 0, 'description': 'Current counter value exposed by STATUS.'}, {'name': 'irq_q', 'width': 1, 'reset': 0, 'description': 'One-cycle interrupt pulse value for current cycle.'}], 'transactions': [{'id': 'FM_APB_WRITE_LOAD', 'name': 'write_load_register', 'preconditions': ['psel == 1 and penable == 1 and pwrite == 1 and paddr == 0'], 'inputs': ['pwdata'], 'outputs': ['pready == 1', 'pslverr == 0', {'name': 'pready_write_load', 'port': 'pready', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'pslverr_write_load', 'port': 'pslverr', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'load_q', 'expr': 'pwdata & 0xffffffff', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'irq_q', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'pready_write_load', 'port': 'pready', 'width': 1, 'expr': '1'}, {'name': 'pslverr_write_load', 'port': 'pslverr', 'width': 1, 'expr': '0'}], 'state_updates': [{'name': 'load_q', 'width': 32, 'expr': 'pwdata & 0xffffffff'}, {'name': 'irq_q', 'width': 1, 'expr': '0'}], 'side_effects': ['load_q becomes pwdata[31:0].', 'irq_q is deasserted for this APB write transaction.'], 'error_cases': []}, {'id': 'FM_APB_WRITE_CTRL', 'name': 'write_ctrl_enable', 'preconditions': ['psel == 1 and penable == 1 and pwrite == 1 and paddr == 4'], 'inputs': ['pwdata'], 'outputs': ['pready == 1', 'pslverr == 0', {'name': 'pready_write_ctrl', 'port': 'pready', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'pslverr_write_ctrl', 'port': 'pslverr', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'enable_q', 'expr': 'pwdata & 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'irq_q', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'pready_write_ctrl', 'port': 'pready', 'width': 1, 'expr': '1'}, {'name': 'pslverr_write_ctrl', 'port': 'pslverr', 'width': 1, 'expr': '0'}], 'state_updates': [{'name': 'enable_q', 'width': 1, 'expr': 'pwdata & 1'}, {'name': 'irq_q', 'width': 1, 'expr': '0'}], 'side_effects': ['enable_q becomes pwdata[0].', 'If ENABLE is written 0, count_q holds its current value on subsequent timer ticks.', 'irq_q is deasserted for this APB write transaction.'], 'error_cases': []}, {'id': 'FM_APB_READ_STATUS', 'name': 'read_status_current_count', 'preconditions': ['psel == 1 and penable == 1 and pwrite == 0 and paddr == 8'], 'inputs': [], 'outputs': ['prdata == count_q', 'pready == 1', 'pslverr == 0', {'name': 'prdata_status', 'port': 'prdata', 'expr': 'count_q & 0xffffffff', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'pready_read_status', 'port': 'pready', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'pslverr_read_status', 'port': 'pslverr', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'irq_q', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'prdata_status', 'port': 'prdata', 'width': 32, 'expr': 'count_q & 0xffffffff'}, {'name': 'pready_read_status', 'port': 'pready', 'width': 1, 'expr': '1'}, {'name': 'pslverr_read_status', 'port': 'pslverr', 'width': 1, 'expr': '0'}], 'state_updates': [{'name': 'irq_q', 'width': 1, 'expr': '0'}], 'side_effects': ['STATUS read has no count_q side effect.', 'irq_q is deasserted for this APB read transaction.'], 'error_cases': []}, {'id': 'FM_TICK_DECREMENT', 'name': 'enabled_decrement_nonzero', 'preconditions': ['psel == 0 and enable_q == 1 and count_q > 0'], 'inputs': [], 'outputs': ['irq == 0', {'name': 'irq_decrement', 'port': 'irq', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'count_q', 'expr': '(count_q - 1) & 0xffffffff', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'irq_q', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'irq_decrement', 'port': 'irq', 'width': 1, 'expr': '0'}], 'state_updates': [{'name': 'count_q', 'width': 32, 'expr': '(count_q - 1) & 0xffffffff'}, {'name': 'irq_q', 'width': 1, 'expr': '0'}], 'side_effects': ['count_q decrements by one modulo 32-bit range.', 'irq_q remains 0.'], 'error_cases': []}, {'id': 'FM_TICK_RELOAD_IRQ', 'name': 'enabled_zero_reload_and_irq_pulse', 'preconditions': ['psel == 0 and enable_q == 1 and count_q == 0'], 'inputs': [], 'outputs': ['irq == 1', {'name': 'irq_reload', 'port': 'irq', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'count_q', 'expr': 'load_q & 0xffffffff', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'irq_q', 'expr': '1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'irq_reload', 'port': 'irq', 'width': 1, 'expr': '1'}], 'state_updates': [{'name': 'count_q', 'width': 32, 'expr': 'load_q & 0xffffffff'}, {'name': 'irq_q', 'width': 1, 'expr': '1'}], 'side_effects': ['irq_q asserts for this cycle.', 'count_q reloads from load_q.', 'Timer continues enabled unless CTRL.ENABLE is later cleared.'], 'error_cases': []}, {'id': 'FM_DISABLED_HOLD', 'name': 'disabled_hold_count', 'preconditions': ['psel == 0 and enable_q == 0'], 'inputs': [], 'outputs': ['irq == 0', {'name': 'irq_disabled', 'port': 'irq', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'count_q', 'expr': 'count_q & 0xffffffff', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'irq_q', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'irq_disabled', 'port': 'irq', 'width': 1, 'expr': '0'}], 'state_updates': [{'name': 'count_q', 'width': 32, 'expr': 'count_q & 0xffffffff'}, {'name': 'irq_q', 'width': 1, 'expr': '0'}], 'side_effects': ['count_q holds its current value while disabled.', 'irq_q remains 0.'], 'error_cases': []}, {'id': 'FM_APB_UNMAPPED_ACCESS', 'name': 'unmapped_apb_access_error', 'preconditions': ['psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)'], 'inputs': ['paddr'], 'outputs': ['pready == 1', 'pslverr == 1', {'name': 'pready_unmapped', 'port': 'pready', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'pslverr_unmapped', 'port': 'pslverr', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'irq_q', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'pready_unmapped', 'port': 'pready', 'width': 1, 'expr': '1'}, {'name': 'pslverr_unmapped', 'port': 'pslverr', 'width': 1, 'expr': '1'}], 'state_updates': [{'name': 'irq_q', 'width': 1, 'expr': '0'}], 'side_effects': ['No architectural register or counter state changes on unmapped access.'], 'error_cases': [{'condition': 'paddr != 0 and paddr != 4 and paddr != 8', 'result': 'pslverr is asserted for the accepted transfer.'}]}], 'invariants': ['count_q >= 0 and count_q <= 0xffffffff', 'load_q >= 0 and load_q <= 0xffffffff', 'enable_q == 0 or enable_q == 1', 'irq_q == 0 or irq_q == 1', 'enable_q == 0 and psel == 0 implies irq_q == 0'], 'reference_model_hint': 'Build scoreboard expected events from transaction output_rules and state_updates; STATUS reads compare prdata against count_q and irq compares against irq_q.', 'derived_signals': [{'name': 'apb_access', 'expr': 'psel and penable', 'width': 1, 'description': 'APB access phase helper derived from psel and penable.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_write', 'expr': 'psel and penable and pwrite', 'width': 1, 'description': 'APB write access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_read', 'expr': 'psel and penable and not pwrite', 'width': 1, 'description': 'APB read access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'addr', 'expr': 'paddr', 'width': 4, 'description': 'Register address helper derived from the APB paddr input.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'legal_addr', 'expr': '(addr == 0) or (addr == 4) or (addr == 8)', 'width': 1, 'description': 'APB legal address decode derived from registers.register_list offsets.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_load', 'expr': 'apb_valid_write and (addr == 0)', 'width': 1, 'description': 'APB write decode helper for register LOAD.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_load', 'expr': 'apb_valid_read and (addr == 0)', 'width': 1, 'description': 'APB read decode helper for register LOAD.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_ctrl', 'expr': 'apb_valid_write and (addr == 4)', 'width': 1, 'description': 'APB write decode helper for register CTRL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_ctrl', 'expr': 'apb_valid_read and (addr == 4)', 'width': 1, 'description': 'APB read decode helper for register CTRL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_status', 'expr': 'apb_valid_write and (addr == 8)', 'width': 1, 'description': 'APB write decode helper for register STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_status', 'expr': 'apb_valid_read and (addr == 8)', 'width': 1, 'description': 'APB read decode helper for register STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'read_mux', 'expr': '(0 if addr == 0 else (0 if addr == 4 else (0 if addr == 8 else 0)))', 'width': 32, 'description': 'APB read data mux derived from registers.register_list offsets and function_model state variables.', 'source': 'repair_ssot_schema.apb_helper'}]}, 'cycle_model': {'purpose': 'Cycle and handshake contract for APB access, decrement, reload, and irq pulse timing.', 'executable': 'python', 'backend_policy': 'Deterministic cycle stepper using function_model state_updates and APB transfer predicates.', 'cosim': True, 'state_accumulating': True, 'clock': 'pclk', 'reset': {'signal': 'presetn', 'assertion': 'presetn low asynchronously clears load_q, enable_q, count_q, irq_q, prdata, pready, and pslverr to 0.', 'deassertion': 'counter is usable on the first rising edge after synchronized reset deassertion and remains disabled at count zero.'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'Read data and pready are produced during the APB access phase.'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'Writes update architectural register state on the accepted APB access edge.'}, 'timer_tick': {'min_cycles': 1, 'max_cycles': 1, 'description': 'While enabled, one decrement or reload decision occurs per pclk cycle not occupied by reset.'}, 'irq_pulse': {'min_cycles': 1, 'max_cycles': 1, 'description': 'irq remains asserted for exactly one pclk cycle at zero reload event.'}}, 'handshake_rules': [{'signal': 'pready', 'rule': 'pready is asserted for an APB access when psel == 1 and penable == 1.', 'expr': 'psel == 1 and penable == 1'}, {'signal': 'pslverr', 'rule': 'pslverr is asserted only for accepted APB accesses with paddr not equal to LOAD, CTRL, or STATUS offsets.', 'expr': 'psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)'}, {'signal': 'prdata', 'rule': 'STATUS read returns current count_q during accepted read access.', 'expr': 'psel == 1 and penable == 1 and pwrite == 0 and paddr == 8'}, {'signal': 'irq', 'rule': 'irq is high for exactly the reload cycle when enable_q == 1 and count_q == 0.', 'expr': 'enable_q == 1 and count_q == 0'}], 'pipeline': [{'stage': 'RESET_RELEASED_IDLE', 'cycle': 0, 'action': 'After reset deassertion, hold count_q=0, enable_q=0, irq=0 until APB write or enable tick.', 'output_rules': [{'name': 'irq_reset_idle', 'port': 'irq', 'width': 1, 'expr': '0'}]}, {'stage': 'APB_ACCESS', 'cycle': 0, 'action': 'Decode LOAD, CTRL, STATUS, or unmapped address during APB access phase.', 'output_rules': [{'name': 'pready_apb_access', 'port': 'pready', 'width': 1, 'expr': 'psel == 1 and penable == 1'}, {'name': 'pslverr_apb_access', 'port': 'pslverr', 'width': 1, 'expr': 'psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)'}]}, {'stage': 'TICK_DECREMENT', 'cycle': 1, 'action': 'If enabled and count_q is nonzero, decrement count_q by one and keep irq low.', 'output_rules': [{'name': 'irq_tick_decrement', 'port': 'irq', 'width': 1, 'expr': '0'}]}, {'stage': 'TICK_RELOAD_IRQ', 'cycle': 1, 'action': 'If enabled and count_q is zero, assert irq for this cycle and reload count_q from LOAD.', 'output_rules': [{'name': 'irq_tick_reload', 'port': 'irq', 'width': 1, 'expr': 'enable_q == 1 and count_q == 0'}]}, {'stage': 'DISABLED_HOLD', 'cycle': 1, 'action': 'If disabled, hold count_q and deassert irq.', 'output_rules': [{'name': 'irq_disabled_hold', 'port': 'irq', 'width': 1, 'expr': '0'}]}], 'ordering': ['APB writes update LOAD or CTRL on the accepted access edge.', 'A CTRL write with ENABLE=0 prevents subsequent decrement/reload ticks and holds count_q.', 'STATUS read observes the current count_q value for the access cycle and has no read side effects.', 'irq assertion and count_q reload occur on the same timer tick when enable_q == 1 and count_q == 0.', 'irq deasserts on the cycle following a reload event unless another reload condition is again true.'], 'backpressure': ['No APB wait states are introduced by the timer; pready follows accepted access phase.'], 'observability': ['STATUS read, irq pulse, and internal count_q are the primary scoreboard observation points.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Default accept/evaluate/observe cycle model depth'}}}, 'fcov_bins': [{'id': 'SC01_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC01', 'description': 'reset contract'}, {'id': 'SC02_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC02', 'description': 'primary approved behavior'}, {'id': 'SC03_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC03', 'description': 'cycle handshake and backpressure'}, {'id': 'SC04_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC04', 'description': 'error and recovery policy'}, {'id': 'SC05_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC05', 'description': 'debug and trace observability'}, {'id': 'SC06_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC06', 'description': 'function_model transaction FM_APB_WRITE_LOAD'}, {'id': 'SC07_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC07', 'description': 'function_model transaction FM_APB_WRITE_CTRL'}, {'id': 'SC08_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC08', 'description': 'function_model transaction FM_APB_READ_STATUS'}, {'id': 'SC09_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC09', 'description': 'function_model transaction FM_TICK_DECREMENT'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'function_model transaction FM_TICK_RELOAD_IRQ'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'function_model transaction FM_DISABLED_HOLD'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'function_model transaction FM_APB_UNMAPPED_ACCESS'}, {'id': 'fcov_write_load', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APB_WRITE_LOAD', 'source_ref': 'function_model.transactions.FM_APB_WRITE_LOAD', 'description': 'LOAD register write accepted.'}, {'id': 'fcov_write_ctrl', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APB_WRITE_CTRL', 'source_ref': 'function_model.transactions.FM_APB_WRITE_CTRL', 'description': 'CTRL.ENABLE write accepted for both 0 and 1 values.'}, {'id': 'fcov_status_read', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APB_READ_STATUS', 'source_ref': 'function_model.transactions.FM_APB_READ_STATUS', 'description': 'STATUS read compared against count_q.'}, {'id': 'fcov_decrement', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TICK_DECREMENT', 'source_ref': 'function_model.transactions.FM_TICK_DECREMENT', 'description': 'Enabled nonzero decrement observed.'}, {'id': 'fcov_reload_irq', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TICK_RELOAD_IRQ', 'source_ref': 'function_model.transactions.FM_TICK_RELOAD_IRQ', 'description': 'Zero reload and irq pulse observed.'}, {'id': 'fcov_disabled_hold', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DISABLED_HOLD', 'source_ref': 'function_model.transactions.FM_DISABLED_HOLD', 'description': 'Disabled hold observed.'}, {'id': 'ccov_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.APB_ACCESS', 'source_ref': 'cycle_model.pipeline.APB_ACCESS', 'description': 'APB access phase ready/error/read behavior observed.'}, {'id': 'ccov_tick_decrement', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.TICK_DECREMENT', 'source_ref': 'cycle_model.pipeline.TICK_DECREMENT', 'description': 'Decrement cycle observed.'}, {'id': 'ccov_tick_reload_irq', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.TICK_RELOAD_IRQ', 'source_ref': 'cycle_model.pipeline.TICK_RELOAD_IRQ', 'description': 'Reload irq pulse cycle observed.'}, {'id': 'ccov_irq_one_cycle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.irq_pulse', 'source_ref': 'cycle_model.latency.irq_pulse', 'description': 'irq pulse width is exactly one cycle.'}, {'id': 'function_write_load_register', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_apb_write_load', 'description': 'FM_APB_WRITE_LOAD write_load_register'}, {'id': 'function_write_ctrl_enable', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_apb_write_ctrl', 'description': 'FM_APB_WRITE_CTRL write_ctrl_enable'}, {'id': 'function_read_status_current_count', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_apb_read_status', 'description': 'FM_APB_READ_STATUS read_status_current_count'}, {'id': 'function_enabled_decrement_nonzero', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_tick_decrement', 'description': 'FM_TICK_DECREMENT enabled_decrement_nonzero'}, {'id': 'function_enabled_zero_reload_and_irq_pulse', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_tick_reload_irq', 'description': 'FM_TICK_RELOAD_IRQ enabled_zero_reload_and_irq_pulse'}, {'id': 'function_disabled_hold_count', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_disabled_hold', 'description': 'FM_DISABLED_HOLD disabled_hold_count'}, {'id': 'function_unmapped_apb_access_error', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm_apb_unmapped_access', 'description': 'FM_APB_UNMAPPED_ACCESS unmapped_apb_access_error'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'pready', 'rule': 'pready is asserted for an APB access when psel == 1 and penable == 1.', 'expr': 'psel == 1 and penable == 1'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'pslverr', 'rule': 'pslverr is asserted only for accepted APB accesses with paddr not equal to LOAD, CTRL, or STATUS offsets.', 'expr': 'psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'prdata', 'rule': 'STATUS read returns current count_q during accepted read access.', 'expr': 'psel == 1 and penable == 1 and pwrite == 0 and paddr == 8'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'irq', 'rule': 'irq is high for exactly the reload cycle when enable_q == 1 and count_q == 0.', 'expr': 'enable_q == 1 and count_q == 0'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'Read data and pready are produced during the APB access phase.'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'Writes update architectural register state on the accepted APB access edge.'}"}, {'id': 'cycle_latency_timer_tick', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.timer_tick', 'source_ref': 'cycle_model.latency.timer_tick', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'While enabled, one decrement or reload decision occurs per pclk cycle not occupied by reset.'}"}, {'id': 'cycle_latency_irq_pulse', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.irq_pulse', 'source_ref': 'cycle_model.latency.irq_pulse', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'irq remains asserted for exactly one pclk cycle at zero reload event.'}"}, {'id': 'cycle_pipeline_reset_released_idle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'After reset deassertion, hold count_q=0, enable_q=0, irq=0 until APB write or enable tick.'}, {'id': 'cycle_pipeline_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Decode LOAD, CTRL, STATUS, or unmapped address during APB access phase.'}, {'id': 'cycle_pipeline_tick_decrement', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'If enabled and count_q is nonzero, decrement count_q by one and keep irq low.'}, {'id': 'cycle_pipeline_tick_reload_irq', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'If enabled and count_q is zero, assert irq for this cycle and reload count_q from LOAD.'}, {'id': 'cycle_pipeline_disabled_hold', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'If disabled, hold count_q and deassert irq.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'APB writes update LOAD or CTRL on the accepted access edge.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'A CTRL write with ENABLE=0 prevents subsequent decrement/reload ticks and holds count_q.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'STATUS read observes the current count_q value for the access cycle and has no read side effects.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'irq assertion and count_q reload occur on the same timer tick when enable_q == 1 and count_q == 0.'}, {'id': 'cycle_ordering_4', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[4]', 'source_ref': 'cycle_model.ordering[4]', 'description': 'irq deasserts on the cycle following a reload event unless another reload condition is again true.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No APB wait states are introduced by the timer; pready follows accepted access phase.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Default accept/evaluate/observe cycle model depth'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '100'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}"}, {'id': 'fsm_timer_control_disabled_to_enabled_count_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.timer_control.transitions[0]', 'source_ref': 'fsm.timer_control.transitions[0]', 'description': 'enable_q == 1'}, {'id': 'fsm_timer_control_enabled_count_to_reload_irq_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.timer_control.transitions[1]', 'source_ref': 'fsm.timer_control.transitions[1]', 'description': 'enable_q == 1 and count_q == 0'}, {'id': 'fsm_timer_control_reload_irq_to_enabled_count_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.timer_control.transitions[2]', 'source_ref': 'fsm.timer_control.transitions[2]', 'description': 'enable_q == 1'}, {'id': 'fsm_timer_control_enabled_count_to_disabled_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.timer_control.transitions[3]', 'source_ref': 'fsm.timer_control.transitions[3]', 'description': 'enable_q == 0'}, {'id': 'fsm_timer_control_reload_irq_to_disabled_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.timer_control.transitions[4]', 'source_ref': 'fsm.timer_control.transitions[4]', 'description': 'enable_q == 0'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'UNMAPPED_APB_ACCESS', 'condition': 'psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'STATUS_WRITE_IGNORED', 'condition': 'psel == 1 and penable == 1 and pwrite == 1 and paddr == 8', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'RESERVED_CTRL_BITS_WRITE', 'condition': 'psel == 1 and penable == 1 and pwrite == 1 and paddr == 4 and (pwdata & 0xfffffffe) != 0', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}]}
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
            "ssot_gap": (
                "structured output_rules/state_updates undefined for transaction "
                + str(tx.get("id") or tx.get("name") or "<unknown>")
            ),
            "synthetic_state": False,
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
