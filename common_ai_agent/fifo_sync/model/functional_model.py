#!/usr/bin/env python3
"""Executable SSOT functional model for fifo_sync.

Generated from yaml/fifo_sync.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'fifo_sync', 'parameters': {'DATA_WIDTH': 32, 'DEPTH': 16, 'ALMOST_FULL_THRESHOLD': 15, 'ALMOST_EMPTY_THRESHOLD': 1, 'COUNT_WIDTH': '$clog2(DEPTH+1)', 'USE_OUTPUT_REGISTER': 0, 'USE_APB': 1, 'USE_ECC': 0, 'CLOCK_FREQ_MHZ': 50}, 'top_module': {'name': 'fifo_sync', 'file': 'rtl/fifo_sync.sv', 'version': '1.0', 'type': 'memory', 'description': 'Parameterized synchronous FIFO with optional APB-lite CSR, single-clock domain, 1-cycle latency', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'fifo_ram', 'type': 'register_array', 'depth': 'DEPTH', 'width': 'DATA_WIDTH', 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'Simple dual-port register array for FIFO storage; implemented as behavioral reg array'}], 'note': 'Memory is implemented as a behavioral register array (not SRAM macro) for portability and parameterization.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 4, 'byte_addressable': True, 'num_channels': 1}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'FIFO_STATUS', 'offset': 0, 'width': 32, 'access': 'ro', 'reset': 5, 'category': 'status', 'description': 'FIFO status flags and fill count', 'fields': [{'name': 'empty', 'bits': [0, 0], 'access': 'ro', 'reset': 1, 'description': '1=FIFO empty'}, {'name': 'full', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': '1=FIFO full'}, {'name': 'almost_empty', 'bits': [2, 2], 'access': 'ro', 'reset': 1, 'description': '1=FIFO at or below almost-empty threshold'}, {'name': 'almost_full', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': '1=FIFO at or above almost-full threshold'}, {'name': 'count', 'bits': [11, 4], 'access': 'ro', 'reset': 0, 'description': 'Current fill count (0..DEPTH)'}, {'name': 'reserved_31_12', 'bits': [31, 12], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'FIFO_CONFIG', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'config', 'description': 'FIFO threshold configuration', 'write_side_effects': ['Writing almost_full_thresh updates ALMOST_FULL_THRESHOLD comparison value.', 'Writing almost_empty_thresh updates ALMOST_EMPTY_THRESHOLD comparison value.', 'Thresholds take effect on the next clock edge after write acceptance.'], 'fields': [{'name': 'almost_full_thresh', 'bits': [7, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Update almost-full threshold', 'description': 'Almost-full threshold (default set by parameter ALMOST_FULL_THRESHOLD)'}, {'name': 'almost_empty_thresh', 'bits': [15, 8], 'access': 'rw', 'reset': 0, 'write_effect': 'Update almost-empty threshold', 'description': 'Almost-empty threshold (default set by parameter ALMOST_EMPTY_THRESHOLD)'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'FIFO_CONTROL', 'offset': 8, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'control', 'description': 'FIFO control actions', 'write_side_effects': ['Writing flush=1 triggers a synchronous flush; self-clearing after one cycle.'], 'fields': [{'name': 'flush', 'bits': [0, 0], 'access': 'wo', 'reset': 0, 'write_effect': 'Pulse flush; clears all pointers and count', 'description': 'Flush command (write 1 to trigger, auto-clears)'}, {'name': 'reserved_31_1', 'bits': [31, 1], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the synchronous FIFO computes independent of cycle timing.', 'state_variables': [{'name': 'wr_ptr', 'source': 'fifo_sync_ptrs', 'reset': 0, 'description': 'Binary write pointer; wraps at DEPTH'}, {'name': 'rd_ptr', 'source': 'fifo_sync_ptrs', 'reset': 0, 'description': 'Binary read pointer; wraps at DEPTH'}, {'name': 'count', 'source': 'fifo_sync_ptrs', 'reset': 0, 'description': 'Current number of valid entries (0..DEPTH)'}, {'name': 'mem', 'source': 'fifo_sync_mem', 'reset': 0, 'description': 'Storage array [0..DEPTH-1] each DATA_WIDTH wide'}], 'transactions': [{'id': 'FM1', 'name': 'push', 'preconditions': ['wr_en_i == 1', 'full_o == 0 (count < DEPTH)', 'flush_i == 0'], 'inputs': ['wr_data_i[DATA_WIDTH-1:0]'], 'output_rules': [{'name': 'full_o', 'expr': '(count + 1 - pop_accepted) == DEPTH', 'width': 1, 'port': 'full_o'}, {'name': 'almost_full_o', 'expr': '(count + 1 - pop_accepted) >= ALMOST_FULL_THRESHOLD', 'width': 1, 'port': 'almost_full_o'}, {'name': 'count_o', 'expr': 'count + 1 - pop_accepted', 'width': '$clog2(DEPTH+1)', 'port': 'count_o'}], 'state_updates': [{'name': 'mem[wr_ptr]', 'reset': 0, 'expr': 'wr_data_i'}, {'name': 'wr_ptr', 'reset': 0, 'expr': '(wr_ptr + 1) % DEPTH'}, {'name': 'count', 'reset': 0, 'expr': 'count + 1 - pop_accepted'}], 'side_effects': ['Architectural state updated per output_rules'], 'error_cases': [], 'outputs': ['full_o = (count + 1 - pop_accepted) == DEPTH', 'almost_full_o = (count + 1 - pop_accepted) >= ALMOST_FULL_THRESHOLD', 'count_o = count + 1 - pop_accepted']}, {'id': 'FM2', 'name': 'pop', 'preconditions': ['rd_en_i == 1', 'empty_o == 0 (count > 0)', 'flush_i == 0'], 'inputs': ['mem[rd_ptr]'], 'output_rules': [{'name': 'rd_data_o', 'expr': 'mem[rd_ptr]', 'width': 'DATA_WIDTH', 'port': 'rd_data_o'}, {'name': 'empty_o', 'expr': '(count - 1 + push_accepted) == 0', 'width': 1, 'port': 'empty_o'}, {'name': 'almost_empty_o', 'expr': '(count - 1 + push_accepted) <= ALMOST_EMPTY_THRESHOLD', 'width': 1, 'port': 'almost_empty_o'}, {'name': 'count_o', 'expr': 'count - 1 + push_accepted', 'width': '$clog2(DEPTH+1)', 'port': 'count_o'}], 'state_updates': [{'name': 'rd_ptr', 'reset': 0, 'expr': '(rd_ptr + 1) % DEPTH'}, {'name': 'count', 'reset': 0, 'expr': 'count - 1 + push_accepted'}], 'side_effects': ['Popped entry storage is invalidated (no read-again guarantee)'], 'error_cases': [], 'outputs': ['rd_data_o = mem[rd_ptr]', 'empty_o = (count - 1 + push_accepted) == 0', 'almost_empty_o = (count - 1 + push_accepted) <= ALMOST_EMPTY_THRESHOLD', 'count_o = count - 1 + push_accepted']}, {'id': 'FM3', 'name': 'simultaneous_push_pop', 'preconditions': ['wr_en_i == 1 and rd_en_i == 1', 'full_o == 0 and empty_o == 0', 'flush_i == 0'], 'inputs': ['wr_data_i[DATA_WIDTH-1:0]', 'mem[rd_ptr]'], 'output_rules': [{'name': 'rd_data_o', 'expr': 'mem[rd_ptr]', 'width': 'DATA_WIDTH', 'port': 'rd_data_o'}, {'name': 'full_o', 'expr': 'count == DEPTH - 1', 'width': 1, 'port': 'full_o'}, {'name': 'empty_o', 'expr': 'count == 1', 'width': 1, 'port': 'empty_o'}, {'name': 'count_o', 'expr': 'count', 'width': '$clog2(DEPTH+1)', 'port': 'count_o'}], 'state_updates': [{'name': 'mem[wr_ptr]', 'reset': 0, 'expr': 'wr_data_i'}, {'name': 'wr_ptr', 'reset': 0, 'expr': '(wr_ptr + 1) % DEPTH'}, {'name': 'rd_ptr', 'reset': 0, 'expr': '(rd_ptr + 1) % DEPTH'}, {'name': 'count', 'reset': 0, 'expr': 'count'}], 'side_effects': ['count is unchanged because push and pop cancel'], 'error_cases': [], 'outputs': ['rd_data_o = mem[rd_ptr]', 'full_o = count == DEPTH - 1', 'empty_o = count == 1', 'count_o = count']}, {'id': 'FM4', 'name': 'overflow_reject', 'preconditions': ['wr_en_i == 1', 'full_o == 1 (count == DEPTH)'], 'inputs': [], 'output_rules': [{'name': 'full_o', 'expr': '1', 'width': 1, 'port': 'full_o'}, {'name': 'count_o', 'expr': 'DEPTH', 'width': '$clog2(DEPTH+1)', 'port': 'count_o'}], 'state_updates': [], 'side_effects': ['Write rejected silently; no data corruption'], 'error_cases': [], 'outputs': ['full_o = 1', 'count_o = DEPTH']}, {'id': 'FM5', 'name': 'underflow_reject', 'preconditions': ['rd_en_i == 1', 'empty_o == 1 (count == 0)'], 'inputs': [], 'output_rules': [{'name': 'empty_o', 'expr': '1', 'width': 1, 'port': 'empty_o'}, {'name': 'rd_data_o', 'expr': 'previous_value_or_zero', 'width': 'DATA_WIDTH', 'port': 'rd_data_o'}, {'name': 'count_o', 'expr': '0', 'width': '$clog2(DEPTH+1)', 'port': 'count_o'}], 'state_updates': [], 'side_effects': ['Read rejected silently; rd_data_o holds previous value (not guaranteed)'], 'error_cases': [], 'outputs': ['empty_o = 1', 'rd_data_o = previous_value_or_zero', 'count_o = 0']}, {'id': 'FM6', 'name': 'flush', 'preconditions': ['flush_i == 1'], 'inputs': [], 'output_rules': [{'name': 'empty_o', 'expr': '1', 'width': 1, 'port': 'empty_o'}, {'name': 'full_o', 'expr': '0', 'width': 1, 'port': 'full_o'}, {'name': 'almost_full_o', 'expr': '0', 'width': 1, 'port': 'almost_full_o'}, {'name': 'almost_empty_o', 'expr': '1', 'width': 1, 'port': 'almost_empty_o'}, {'name': 'count_o', 'expr': '0', 'width': '$clog2(DEPTH+1)', 'port': 'count_o'}], 'state_updates': [{'name': 'wr_ptr', 'reset': 0, 'expr': '0'}, {'name': 'rd_ptr', 'reset': 0, 'expr': '0'}, {'name': 'count', 'reset': 0, 'expr': '0'}], 'side_effects': ['All FIFO entries invalidated; memory contents become undefined', 'Flush takes precedence over concurrent push/pop'], 'error_cases': [], 'outputs': ['empty_o = 1', 'full_o = 0', 'almost_full_o = 0', 'almost_empty_o = 1', 'count_o = 0']}], 'invariants': ['count is always in range [0, DEPTH].', 'full_o == 1 if and only if count == DEPTH.', 'empty_o == 1 if and only if count == 0.', 'wr_ptr and rd_ptr are always in range [0, DEPTH-1].', 'No read data changes unless rd_en_i is accepted or flush occurs.', 'Simultaneous push/pop leaves count unchanged.', 'Overflow and underflow are silently rejected with no state corruption.'], 'reference_model_hint': 'tb-gen should implement a Python deque-based scoreboard model; push/pop/flush map directly to deque.append()/popleft()/clear().'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when FIFO state, flags, and data outputs may change relative to PCLK edges.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears wr_ptr, rd_ptr, count to 0; all flags reflect empty state.', 'deassertion': 'State is usable on the first rising PCLK edge after synchronized deassertion.'}, 'latency': {'push_accept': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Data written on the rising edge when wr_en_i && !full_o; flags update on the same edge.'}, 'pop_combinational': {'min_cycles': 0, 'max_cycles': 0, 'description': 'When USE_OUTPUT_REGISTER=0, rd_data_o is combinational from mem[rd_ptr]; flags update 1 cycle after rd_en_i acceptance.'}, 'pop_registered': {'min_cycles': 1, 'max_cycles': 1, 'description': 'When USE_OUTPUT_REGISTER=1, rd_data_o appears 1 cycle after rd_en_i acceptance; flags update on the acceptance edge.'}, 'flush': {'min_cycles': 1, 'max_cycles': 1, 'description': 'All pointers and count cleared on the rising edge when flush_i=1; flags update on the same edge.'}, 'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB CSR read: pready always 1 (0 wait states).'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB CSR write: pready always 1 (0 wait states).'}}, 'handshake_rules': [{'signal': 'wr_en_i', 'rule': 'Sampled on rising PCLK; data accepted only when full_o=0. Full flag gates write acceptance.'}, {'signal': 'rd_en_i', 'rule': 'Sampled on rising PCLK; data consumed only when empty_o=0. Empty flag gates read acceptance.'}, {'signal': 'full_o', 'rule': 'Combinational function of count and push/pop acceptance in the current cycle. Updates after each clock edge.'}, {'signal': 'empty_o', 'rule': 'Combinational function of count and push/pop acceptance in the current cycle. Updates after each clock edge.'}, {'signal': 'flush_i', 'rule': 'Synchronous; takes precedence over push/pop. Clears all pointers and count on the rising edge.'}], 'pipeline': [{'stage': 'S0_SAMPLE_INPUTS', 'cycle': 0, 'action': 'Sample wr_en_i, rd_en_i, flush_i, wr_data_i on rising PCLK edge'}, {'stage': 'S1_EVAL_ACCEPT', 'cycle': 0, 'action': 'Combinational: determine push_accepted = wr_en_i && !full_o && !flush_i; pop_accepted = rd_en_i && !empty_o && !flush_i'}, {'stage': 'S2_UPDATE_PTRS', 'cycle': 0, 'action': 'Update wr_ptr, rd_ptr, count registers based on push/pop acceptance'}, {'stage': 'S3_WRITE_MEM', 'cycle': 0, 'action': 'Write wr_data_i to mem[wr_ptr] when push_accepted'}, {'stage': 'S4_UPDATE_FLAGS', 'cycle': 1, 'action': 'Flags (full, empty, almost_full, almost_empty, count) reflect new pointer state'}], 'ordering': ['Push data is captured into memory in the same cycle as pointer update.', 'Pop data is available combinationally from memory (USE_OUTPUT_REGISTER=0) or one cycle later (USE_OUTPUT_REGISTER=1).', 'Flush clears all state in the cycle it is sampled; concurrent push/pop are ignored.', 'Flag updates are visible on the cycle after pointer/count changes.'], 'backpressure': ['full_o provides natural backpressure to the writer; the writer must deassert wr_en_i or accept rejection.', 'empty_o provides natural backpressure to the reader; the reader must deassert rd_en_i or accept undefined data.'], 'performance': {'frequency_mhz': 50, 'throughput': {'sustained_ops_per_cycle': 1, 'condition': 'At least one of push or pop accepted per cycle; simultaneous push/pop sustains 2 ops/cycle'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single-port push and single-port pop per cycle'}, 'depth': {'pipeline_stages': 1, 'queue_depth': 'DEPTH parameter', 'description': 'Single pipeline stage; storage depth equals DEPTH parameter'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Push single entry'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Pop single entry'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'Fill to full'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Overflow rejection'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'Underflow rejection'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'Simultaneous push and pop'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'Simultaneous push and pop at boundary'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'Flush when partially full'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'Flush when full'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'Flush during simultaneous push/pop'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'Almost full threshold'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'Almost empty threshold'}, {'id': 'SC13_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'SC13', 'description': 'APB CSR read status'}, {'id': 'SC14_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'SC14', 'description': 'APB CSR write config'}, {'id': 'SC15_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[14]', 'scenario': 'SC15', 'description': 'APB CSR flush'}, {'id': 'SC16_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[15]', 'scenario': 'SC16', 'description': 'APB error response'}, {'id': 'SC17_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[16]', 'scenario': 'SC17', 'description': 'Wrap-around pointer'}, {'id': 'SC18_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[17]', 'scenario': 'SC18', 'description': 'Output register mode'}, {'id': 'SC19_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[18]', 'scenario': 'SC19', 'description': 'Reset behavior'}, {'id': 'SC20_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[19]', 'scenario': 'SC20', 'description': 'Reset deassertion'}, {'id': 'fcov_fm1_push', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM1', 'source_ref': 'function_model.transactions.FM1', 'description': 'Legal push (FM1) observed by scoreboard with correct output_rules'}, {'id': 'fcov_fm2_pop', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM2', 'source_ref': 'function_model.transactions.FM2', 'description': 'Legal pop (FM2) observed by scoreboard with correct rd_data_o'}, {'id': 'fcov_fm3_simul', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM3', 'source_ref': 'function_model.transactions.FM3', 'description': 'Simultaneous push/pop (FM3) with count unchanged'}, {'id': 'fcov_fm4_overflow', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM4', 'source_ref': 'function_model.transactions.FM4', 'description': 'Overflow rejection (FM4) observed'}, {'id': 'fcov_fm5_underflow', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM5', 'source_ref': 'function_model.transactions.FM5', 'description': 'Underflow rejection (FM5) observed'}, {'id': 'fcov_fm6_flush', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM6', 'source_ref': 'function_model.transactions.FM6', 'description': 'Flush (FM6) clears all state'}, {'id': 'ccov_push_1cycle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.push_accept', 'source_ref': 'cycle_model.latency.push_accept', 'description': 'Push acceptance completes in exactly 1 cycle'}, {'id': 'ccov_pop_comb', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pop_combinational', 'source_ref': 'cycle_model.latency.pop_combinational', 'description': 'Combinational pop read (USE_OUTPUT_REGISTER=0) observed'}, {'id': 'ccov_pop_reg', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pop_registered', 'source_ref': 'cycle_model.latency.pop_registered', 'description': 'Registered pop read (USE_OUTPUT_REGISTER=1) observed'}, {'id': 'ccov_flush_1cycle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.flush', 'source_ref': 'cycle_model.latency.flush', 'description': 'Flush completes in exactly 1 cycle'}, {'id': 'ccov_csr_0wait', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': 'APB CSR read with 0 wait states observed'}, {'id': 'ccov_simul_same_cycle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'Simultaneous push/pop completes in same cycle'}, {'id': 'ccov_flush_priority', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.flush_i', 'source_ref': 'cycle_model.handshake_rules.flush_i', 'description': 'Flush priority over concurrent push/pop observed'}, {'id': 'ccov_ptr_wrap', 'class': 'boundary', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S2_UPDATE_PTRS', 'source_ref': 'cycle_model.pipeline.S2_UPDATE_PTRS', 'description': 'Pointer wrap-around observed at S2_UPDATE_PTRS stage (wr_ptr and rd_ptr)'}, {'id': 'function_push', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm1', 'description': 'push'}, {'id': 'function_pop', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm2', 'description': 'pop'}, {'id': 'function_simultaneous_push_pop', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm3', 'description': 'simultaneous_push_pop'}, {'id': 'function_overflow_reject', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm4', 'description': 'overflow_reject'}, {'id': 'function_underflow_reject', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm5', 'description': 'underflow_reject'}, {'id': 'function_flush', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm6', 'description': 'flush'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'wr_en_i', 'rule': 'Sampled on rising PCLK; data accepted only when full_o=0. Full flag gates write acceptance.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'rd_en_i', 'rule': 'Sampled on rising PCLK; data consumed only when empty_o=0. Empty flag gates read acceptance.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'full_o', 'rule': 'Combinational function of count and push/pop acceptance in the current cycle. Updates after each clock edge.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'empty_o', 'rule': 'Combinational function of count and push/pop acceptance in the current cycle. Updates after each clock edge.'}"}, {'id': 'cycle_handshake_4', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[4]', 'source_ref': 'cycle_model.handshake_rules[4]', 'description': "{'signal': 'flush_i', 'rule': 'Synchronous; takes precedence over push/pop. Clears all pointers and count on the rising edge.'}"}, {'id': 'cycle_latency_push_accept', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.push_accept', 'source_ref': 'cycle_model.latency.push_accept', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Data written on the rising edge when wr_en_i && !full_o; flags update on the same edge.'}"}, {'id': 'cycle_latency_pop_combinational', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pop_combinational', 'source_ref': 'cycle_model.latency.pop_combinational', 'description': "{'min_cycles': 0, 'max_cycles': 0, 'description': 'When USE_OUTPUT_REGISTER=0, rd_data_o is combinational from mem[rd_ptr]; flags update 1 cycle after rd_en_i acceptance.'}"}, {'id': 'cycle_latency_pop_registered', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pop_registered', 'source_ref': 'cycle_model.latency.pop_registered', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'When USE_OUTPUT_REGISTER=1, rd_data_o appears 1 cycle after rd_en_i acceptance; flags update on the acceptance edge.'}"}, {'id': 'cycle_latency_flush', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.flush', 'source_ref': 'cycle_model.latency.flush', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'All pointers and count cleared on the rising edge when flush_i=1; flags update on the same edge.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB CSR read: pready always 1 (0 wait states).'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB CSR write: pready always 1 (0 wait states).'}"}, {'id': 'cycle_pipeline_s0_sample_inputs', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Sample wr_en_i, rd_en_i, flush_i, wr_data_i on rising PCLK edge'}, {'id': 'cycle_pipeline_s1_eval_accept', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Combinational: determine push_accepted = wr_en_i && !full_o && !flush_i; pop_accepted = rd_en_i && !empty_o && !flush_i'}, {'id': 'cycle_pipeline_s2_update_ptrs', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Update wr_ptr, rd_ptr, count registers based on push/pop acceptance'}, {'id': 'cycle_pipeline_s3_write_mem', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Write wr_data_i to mem[wr_ptr] when push_accepted'}, {'id': 'cycle_pipeline_s4_update_flags', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Flags (full, empty, almost_full, almost_empty, count) reflect new pointer state'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Push data is captured into memory in the same cycle as pointer update.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Pop data is available combinationally from memory (USE_OUTPUT_REGISTER=0) or one cycle later (USE_OUTPUT_REGISTER=1).'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Flush clears all state in the cycle it is sampled; concurrent push/pop are ignored.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'Flag updates are visible on the cycle after pointer/count changes.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'full_o provides natural backpressure to the writer; the writer must deassert wr_en_i or accept rejection.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'empty_o provides natural backpressure to the reader; the reader must deassert rd_en_i or accept undefined data.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 1, 'write_max': 1, 'description': 'Single-port push and single-port pop per cycle'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 1, 'queue_depth': 'DEPTH parameter', 'description': 'Single pipeline stage; storage depth equals DEPTH parameter'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_ops_per_cycle': 1, 'condition': 'At least one of push or pop accepted per cycle; simultaneous push/pop sustains 2 ops/cycle'}"}, {'id': 'fsm_ptr_fsm_empty_to_normal_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[0]', 'source_ref': 'fsm.ptr_fsm.transitions[0]', 'description': 'push_accepted && count becomes > ALMOST_EMPTY_THRESHOLD'}, {'id': 'fsm_ptr_fsm_empty_to_almost_empty_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[1]', 'source_ref': 'fsm.ptr_fsm.transitions[1]', 'description': 'push_accepted && count becomes <= ALMOST_EMPTY_THRESHOLD && count > 0'}, {'id': 'fsm_ptr_fsm_almost_empty_to_empty_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[2]', 'source_ref': 'fsm.ptr_fsm.transitions[2]', 'description': 'pop_accepted && count becomes 0'}, {'id': 'fsm_ptr_fsm_almost_empty_to_normal_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[3]', 'source_ref': 'fsm.ptr_fsm.transitions[3]', 'description': 'push_accepted && count > ALMOST_EMPTY_THRESHOLD'}, {'id': 'fsm_ptr_fsm_normal_to_almost_full_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[4]', 'source_ref': 'fsm.ptr_fsm.transitions[4]', 'description': 'push_accepted && count >= ALMOST_FULL_THRESHOLD'}, {'id': 'fsm_ptr_fsm_normal_to_almost_empty_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[5]', 'source_ref': 'fsm.ptr_fsm.transitions[5]', 'description': 'pop_accepted && count <= ALMOST_EMPTY_THRESHOLD'}, {'id': 'fsm_ptr_fsm_almost_full_to_full_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[6]', 'source_ref': 'fsm.ptr_fsm.transitions[6]', 'description': 'push_accepted && count == DEPTH'}, {'id': 'fsm_ptr_fsm_almost_full_to_normal_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[7]', 'source_ref': 'fsm.ptr_fsm.transitions[7]', 'description': 'pop_accepted && count < ALMOST_FULL_THRESHOLD'}, {'id': 'fsm_ptr_fsm_full_to_almost_full_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ptr_fsm.transitions[8]', 'source_ref': 'fsm.ptr_fsm.transitions[8]', 'description': 'pop_accepted && count == DEPTH-1'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_OVERFLOW', 'condition': 'wr_en_i=1 while full_o=1', 'architectural_effect': 'Write rejected silently; no state change', 'propagation': 'full_o remains 1; no error flag or interrupt'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_UNDERFLOW', 'condition': 'rd_en_i=1 while empty_o=1', 'architectural_effect': 'Read rejected silently; rd_data_o holds previous value (undefined)', 'propagation': 'empty_o remains 1; no error flag or interrupt'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'ERR_APB_UNSUPPORTED', 'condition': 'APB access to unmapped offset', 'architectural_effect': 'pslverr=1, prdata=0', 'propagation': 'Single-cycle error response on APB'}"}]}
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
