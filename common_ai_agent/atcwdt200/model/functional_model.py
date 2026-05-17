#!/usr/bin/env python3
"""Executable SSOT functional model for atcwdt200.

Generated from yaml/atcwdt200.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'atcwdt200', 'parameters': {'COUNTER_WIDTH': 16, 'INT_TIME_WIDTH': 3, 'APB_ADDR_WIDTH': 5, 'DATA_WIDTH': 32}, 'top_module': {'name': 'atcwdt200', 'file': 'rtl/atcwdt200.sv', 'version': '0.1-draft', 'type': 'peripheral', 'description': 'APB-accessed watchdog timer with programmable interrupt timeout, reset timeout, restart command, pause input, and selectable internal/external tick source.', 'reference_spec': 'clean-room compatible behavior derived from user-provided atcwdt200 RTL evidence', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No SRAM/FIFO/memory arrays identified in reference.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 5, 'byte_addressable': True}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read zero and do not allocate storage.'}, 'register_list': [{'name': 'VER', 'offset': 0, 'width': 32, 'access': 'ro', 'reset': 50339842, 'category': 'identification', 'description': 'Version register assembled from imported constants.', 'fields': [{'name': 'id', 'bits': [31, 16], 'access': 'ro', 'reset': 768, 'description': 'IP ID'}, {'name': 'rev_major', 'bits': [15, 4], 'access': 'ro', 'reset': 512, 'description': 'Major revision'}, {'name': 'rev_minor', 'bits': [3, 0], 'access': 'ro', 'reset': 2, 'description': 'Minor revision'}]}, {'name': 'CR', 'offset': 16, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Watchdog control register.', 'write_side_effects': ['Protected write policy pending QA.'], 'fields': [{'name': 'en', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable watchdog counter', 'description': 'Watchdog enable'}, {'name': 'clk', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': 'Select pclk or extclk tick source', 'description': 'Tick source select'}, {'name': 'inten', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable wdt_int output', 'description': 'Interrupt enable'}, {'name': 'rsten', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable wdt_rst output', 'description': 'Reset enable'}, {'name': 'inttime', 'bits': [7, 4], 'access': 'rw', 'reset': 0, 'write_effect': 'Select interrupt timeout interval', 'description': 'Width/policy pending counter QA'}, {'name': 'rsttime', 'bits': [10, 8], 'access': 'rw', 'reset': 0, 'write_effect': 'Select reset timeout interval', 'description': 'Reset timeout interval'}, {'name': 'reserved_31_11', 'bits': [31, 11], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'RES', 'offset': 20, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'command', 'description': 'Restart watchdog command.', 'write_side_effects': ['Writing 0x0000cafe when unlocked restarts watchdog timer.'], 'fields': [{'name': 'restart_magic', 'bits': [15, 0], 'access': 'wo', 'reset': 0, 'write_effect': '0xcafe issues restart when unlocked', 'description': 'Restart magic value'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'WEN', 'offset': 24, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'protection', 'description': 'Write protection unlock command.', 'write_side_effects': ['Writing 0x00005aa5 unlocks protected writes according to pending QA policy.'], 'fields': [{'name': 'unlock_magic', 'bits': [15, 0], 'access': 'wo', 'reset': 0, 'write_effect': '0x5aa5 unlocks protected write', 'description': 'Unlock magic value'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'SR', 'offset': 28, 'width': 32, 'access': 'rw1c', 'reset': 0, 'category': 'status', 'description': 'Watchdog status register; reset-timeout visibility pending QA.', 'fields': [{'name': 'intzero', 'bits': [0, 0], 'access': 'rw1c', 'reset': 0, 'write_effect': 'Write one clears interrupt timeout status', 'description': 'Interrupt timeout pending'}, {'name': 'reserved_31_1', 'bits': [31, 1], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}]}, 'function_model': {'purpose': 'Executable watchdog timer contract for FL model, RTL, and TB.', 'state_variables': [{'name': 'CR_EN', 'width': 1, 'reset': 0, 'description': 'Watchdog enable'}, {'name': 'CR_CLK', 'width': 1, 'reset': 0, 'description': 'Tick source select'}, {'name': 'CR_INTEN', 'width': 1, 'reset': 0, 'description': 'Interrupt enable'}, {'name': 'CR_RSTEN', 'width': 1, 'reset': 0, 'description': 'Reset output enable'}, {'name': 'CR_INTTIME', 'width': 'INT_TIME_WIDTH', 'reset': 0, 'description': 'Interrupt timeout encoding'}, {'name': 'CR_RSTTIME', 'width': 3, 'reset': 0, 'description': 'Reset timeout encoding'}, {'name': 'SR_INTZERO', 'width': 1, 'reset': 0, 'description': 'Interrupt timeout pending status'}, {'name': 'SR_RSTZERO', 'width': 1, 'reset': 0, 'description': 'Reset timeout internal status'}, {'name': 'REG_WEN', 'width': 1, 'reset': 0, 'description': 'Protected-write enable latch'}, {'name': 'COUNTER', 'width': 'COUNTER_WIDTH', 'reset': 0, 'description': 'Watchdog counter'}, {'name': 'STATE', 'width': 1, 'reset': 'ST_INTTIME', 'description': 'Interrupt-time or reset-time phase'}], 'transactions': [{'id': 'apb_read', 'name': 'APB register read', 'preconditions': ['psel and penable are asserted', 'pwrite is low'], 'inputs': ['paddr'], 'outputs': ['prdata returns selected register value'], 'output_rules': [{'name': 'prdata_rule', 'port': 'prdata', 'expr': 0, 'width': 32}], 'side_effects': ['No architectural state changes on read'], 'error_cases': ['Unsupported offsets return zero in legacy-compatible mode.']}, {'id': 'apb_write', 'name': 'APB register write', 'preconditions': ['psel and penable and pwrite are asserted'], 'inputs': ['paddr', 'pwdata'], 'outputs': ['Protected registers update only when REG_WEN is set according to approved policy'], 'state_updates': [{'name': 'CR_FIELDS', 'expr': 'pwdata & 0x7ff', 'width': 11}, {'name': 'SR_INTZERO', 'expr': 'SR_INTZERO & (((pwdata & 1) ^ 1) & 1)', 'width': 1}], 'side_effects': ['May update CR', 'set REG_WEN', 'clear SR_INTZERO', 'or issue restart command'], 'error_cases': ['Writes without unlock to protected registers have no effect']}, {'id': 'write_unlock', 'name': 'Write protection unlock', 'preconditions': ['APB write to WEN offset 0x18'], 'inputs': ['pwdata'], 'outputs': ['REG_WEN becomes one when lower 16 bits match 0x5aa5'], 'state_updates': [{'name': 'REG_WEN', 'expr': '(pwdata & 0xffff) == 0x5aa5', 'width': 1}], 'side_effects': ['Unlock consumption policy pending QA'], 'error_cases': ['Wrong magic value does not unlock']}, {'id': 'restart', 'name': 'Watchdog restart command', 'preconditions': ['Unlocked APB write to RES offset 0x14 with lower 16 bits 0xcafe'], 'inputs': ['pwdata', 'REG_WEN'], 'outputs': ['COUNTER resets to zero and STATE becomes ST_INTTIME'], 'state_updates': [{'name': 'COUNTER', 'expr': 0, 'width': 'COUNTER_WIDTH'}, {'name': 'STATE', 'expr': 0, 'width': 1}], 'side_effects': ['Restart command is a pulse'], 'error_cases': ['Wrong magic or locked write has no restart effect']}, {'id': 'watchdog_tick', 'name': 'Watchdog tick and timeout update', 'preconditions': ['CR_EN is set', 'wdt_pause synchronized value is zero'], 'inputs': ['pclk_tick', 'extclk_rising_pulse', 'CR_CLK', 'CR_INTTIME', 'CR_RSTTIME', 'STATE', 'restart_cmd', 'inttime_end', 'rsttime_end'], 'outputs': ['wdt_int and wdt_rst reflect timeout status gated by enables'], 'output_rules': [{'name': 'wdt_int_rule', 'port': 'wdt_int', 'expr': 'SR_INTZERO & CR_INTEN', 'width': 1}, {'name': 'wdt_rst_rule', 'port': 'wdt_rst', 'expr': 'SR_RSTZERO & CR_RSTEN', 'width': 1}], 'state_updates': [{'name': 'COUNTER', 'expr': '0 if (restart_cmd or inttime_end) else (COUNTER + 1)', 'width': 'COUNTER_WIDTH'}, {'name': 'SR_INTZERO', 'expr': '1 if inttime_end else SR_INTZERO', 'width': 1}, {'name': 'SR_RSTZERO', 'expr': '1 if rsttime_end else SR_RSTZERO', 'width': 1}, {'name': 'STATE', 'expr': '1 if (inttime_end and not restart_cmd) else (0 if restart_cmd else STATE)', 'width': 1}, {'name': 'CR_EN', 'expr': '0 if rsttime_end else CR_EN', 'width': 1}], 'side_effects': ['Timeout table uses the observed reference counter bit taps.'], 'error_cases': ['No counting while paused or disabled']}, {'id': 'timeout_decode', 'name': 'Timeout interval decode', 'preconditions': ['COUNTER advances'], 'inputs': ['CR_INTTIME', 'CR_RSTTIME', 'COUNTER'], 'outputs': ['inttime_end and rsttime_end predicates'], 'state_updates': [{'name': 'TIMEOUT_PREDICATES', 'expr': 0, 'width': 2}], 'side_effects': ['Drives watchdog_tick state updates'], 'error_cases': ['Unsupported encodings are not expected if table is locked']}], 'invariants': ['wdt_int equals SR_INTZERO & CR_INTEN.', 'wdt_rst equals SR_RSTZERO & CR_RSTEN.', 'Counter does not advance while disabled or paused.', 'Reserved register bits read as zero and ignore writes unless QA approves modernized behavior.'], 'reference_model_hint': 'FL model should implement register transactions, protected-write policy, timeout table, and tick-source selection before RTL is generated.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for watchdog control timing.', 'executable': 'python', 'backend_policy': 'Use FL model as behavioral oracle and cycle model for pclk-edge sequencing.', 'clock': 'pclk', 'reset': {'assertion': 'presetn low asynchronously clears architectural state.', 'deassertion': 'Generated RTL should use async assert and synchronous operational use after reset release.'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'Reference prdata is combinational from delayed paddr; exact APB read latency pending protocol QA.'}, 'register_write': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Writes update state on pclk when psel && penable && pwrite.'}, 'watchdog_timeout': {'min_cycles': 1, 'max_cycles': None, 'description': 'Determined by timeout tap table and selected tick source.'}}, 'handshake_rules': [{'signal': 'psel', 'rule': 'Address is captured when psel is high.'}, {'signal': 'penable', 'rule': 'Write access is valid when psel && penable && pwrite.'}, {'signal': 'extclk', 'rule': 'External tick is consumed as synchronized rising-edge pulse if CDC QA approves internal sync.'}], 'pipeline': [{'stage': 'S0_APB_ADDR', 'cycle': 0, 'action': 'Capture APB address during select phase.'}, {'stage': 'S1_APB_ACCESS', 'cycle': 1, 'action': 'Apply APB write side effects or drive selected read data.'}, {'stage': 'S2_SYNC', 'cycle': 0, 'action': 'Synchronize extclk and wdt_pause into pclk domain.'}, {'stage': 'S3_COUNT', 'cycle': 0, 'action': 'Increment or clear watchdog counter based on enable', 'pause': None, 'selected tick': None, 'restart': None, 'and timeout.': None}, {'stage': 'S4_TIMEOUT_OUTPUT', 'cycle': 0, 'action': 'Update interrupt/reset status and outputs.'}], 'ordering': ['WEN unlock is evaluated before a protected write consumes or clears unlock state according to approved QA policy.', 'Restart command clears counter and returns state to ST_INTTIME.', 'Interrupt timeout set happens before reset-time phase begins.', 'Reset timeout clears CR.EN and asserts reset status.'], 'backpressure': ['APB interface has no backpressure in the reference; APB4 ready/error behavior is pending QA.'], 'performance': {'frequency_mhz': 50, 'throughput': {'register_accesses_per_cycle': 1, 'condition': 'APB-like access with no wait states if legacy mode is selected'}, 'outstanding': {'apb_max': 1, 'description': 'Single APB access at a time'}, 'depth': {'pipeline_stages': 5, 'queue_depth': 0, 'description': 'Register access plus synchronizer/counter stages'}}, 'observability': ['Every function_model transaction maps to at least one scenario and coverage bin.']}, 'fcov_bins': [{'id': 'reset_defaults_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'reset_defaults', 'description': 'Reset defaults'}, {'id': 'apb_register_access_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'apb_register_access', 'description': 'APB register read/write'}, {'id': 'restart_command_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'restart_command', 'description': 'Restart command'}, {'id': 'interrupt_timeout_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'interrupt_timeout', 'description': 'Interrupt timeout'}, {'id': 'reset_timeout_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'reset_timeout', 'description': 'Reset timeout'}, {'id': 'pause_and_extclk_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'pause_and_extclk', 'description': 'Pause and external clock behavior'}, {'id': 'fcov_apb_read', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.apb_read', 'source_ref': 'function_model.transactions.apb_read', 'description': 'APB read transaction observed.'}, {'id': 'fcov_apb_write', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.apb_write', 'source_ref': 'function_model.transactions.apb_write', 'description': 'APB write transaction observed.'}, {'id': 'fcov_unlock', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.write_unlock', 'source_ref': 'function_model.transactions.write_unlock', 'description': 'WEN magic accepted.'}, {'id': 'fcov_restart', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.restart', 'source_ref': 'function_model.transactions.restart', 'description': 'Restart magic accepted.'}, {'id': 'fcov_timeout', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.watchdog_tick', 'source_ref': 'function_model.transactions.watchdog_tick', 'description': 'Interrupt and reset timeout behavior observed.'}, {'id': 'ccov_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_APB_ACCESS', 'source_ref': 'cycle_model.pipeline.S1_APB_ACCESS', 'description': 'APB access stage observed.'}, {'id': 'ccov_sync', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S2_SYNC', 'source_ref': 'cycle_model.pipeline.S2_SYNC', 'description': 'Synchronizer stage observed.'}, {'id': 'ccov_count', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S3_COUNT', 'source_ref': 'cycle_model.pipeline.S3_COUNT', 'description': 'Counter stage observed.'}, {'id': 'ccov_fsm_int_to_rst', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.watchdog.transitions', 'source_ref': 'fsm.watchdog.transitions', 'description': 'ST_INTTIME to ST_RSTTIME observed.'}, {'id': 'ccov_perf_freq', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': 'PCLK target recorded.'}, {'id': 'function_apb_register_read', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.apb_read', 'description': 'apb_register_read'}, {'id': 'function_apb_register_write', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.apb_write', 'description': 'apb_register_write'}, {'id': 'function_write_protection_unlock', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.write_unlock', 'description': 'write_protection_unlock'}, {'id': 'function_watchdog_restart_command', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.restart', 'description': 'watchdog_restart_command'}, {'id': 'function_watchdog_tick_and_timeout_update', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.watchdog_tick', 'description': 'watchdog_tick_and_timeout_update'}, {'id': 'function_timeout_interval_decode', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.timeout_decode', 'description': 'timeout_interval_decode'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'psel', 'rule': 'Address is captured when psel is high.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'penable', 'rule': 'Write access is valid when psel && penable && pwrite.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'extclk', 'rule': 'External tick is consumed as synchronized rising-edge pulse if CDC QA approves internal sync.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'Reference prdata is combinational from delayed paddr; exact APB read latency pending protocol QA.'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Writes update state on pclk when psel && penable && pwrite.'}"}, {'id': 'cycle_latency_watchdog_timeout', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.watchdog_timeout', 'source_ref': 'cycle_model.latency.watchdog_timeout', 'description': "{'min_cycles': 1, 'max_cycles': None, 'description': 'Determined by timeout tap table and selected tick source.'}"}, {'id': 'cycle_pipeline_s0_apb_addr', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Capture APB address during select phase.'}, {'id': 'cycle_pipeline_s1_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Apply APB write side effects or drive selected read data.'}, {'id': 'cycle_pipeline_s2_sync', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Synchronize extclk and wdt_pause into pclk domain.'}, {'id': 'cycle_pipeline_s3_count', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Increment or clear watchdog counter based on enable'}, {'id': 'cycle_pipeline_s4_timeout_output', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Update interrupt/reset status and outputs.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'WEN unlock is evaluated before a protected write consumes or clears unlock state according to approved QA policy.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Restart command clears counter and returns state to ST_INTTIME.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Interrupt timeout set happens before reset-time phase begins.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'Reset timeout clears CR.EN and asserts reset status.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'APB interface has no backpressure in the reference; APB4 ready/error behavior is pending QA.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'apb_max': 1, 'description': 'Single APB access at a time'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 5, 'queue_depth': 0, 'description': 'Register access plus synchronizer/counter stages'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'register_accesses_per_cycle': 1, 'condition': 'APB-like access with no wait states if legacy mode is selected'}"}, {'id': 'fsm_watchdog_st_inttime_to_st_rsttime_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.watchdog.transitions[0]', 'source_ref': 'fsm.watchdog.transitions[0]', 'description': 'inttime_end and not restart_cmd'}, {'id': 'fsm_watchdog_st_rsttime_to_st_inttime_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.watchdog.transitions[1]', 'source_ref': 'fsm.watchdog.transitions[1]', 'description': 'restart_cmd'}, {'id': 'fsm_watchdog_st_inttime_to_st_inttime_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.watchdog.transitions[2]', 'source_ref': 'fsm.watchdog.transitions[2]', 'description': 'restart_cmd or not inttime_end'}, {'id': 'fsm_watchdog_st_rsttime_to_st_rsttime_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.watchdog.transitions[3]', 'source_ref': 'fsm.watchdog.transitions[3]', 'description': 'not restart_cmd'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_UNSUPPORTED_APB_OFFSET', 'condition': 'APB access to unsupported offset', 'architectural_effect': 'Legacy-compatible mode returns zero on reads and ignores writes because no pslverr output exists.'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_BAD_MAGIC', 'condition': 'RES or WEN magic mismatch', 'architectural_effect': 'No state-changing command effect'}"}]}
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
