#!/usr/bin/env python3
"""Executable SSOT functional model for dma_scratch_ui_live_20260519a.

Generated from yaml/dma_scratch_ui_live_20260519a.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'dma_scratch_ui_live_20260519a', 'parameters': {'ADDR_WIDTH': 32, 'DATA_WIDTH': 32, 'LEN_WIDTH': 16}, 'top_module': {'name': 'dma_scratch_ui_live_20260519a', 'file': 'rtl/dma_scratch_ui_live_20260519a.sv', 'version': '0.1.0', 'type': 'synthesizable_rtl', 'description': 'Single-clock scratch DMA controller with a simple CSR valid/ready UI, source-to-destination copy engine, progress tracking, sticky status, and done/error IRQ outputs.', 'target': {'technology': 'generic', 'clock_freq_mhz': 100, 'area_um2': None, 'power_mw': None}, 'quality_profile': 'standard', 'reference_spec': 'user-defined'}, 'memory': {'instances': [], 'addressing': {'policy': 'External memory address channels use byte addresses and in-order completion.', 'byte_strobe_policy': 'mem_wr_strb masks the final beat when LENGTH is not a multiple of DATA_WIDTH/8.'}, 'storage_policy': 'Only control/status registers and one read-data buffer may be implemented internally.'}, 'registers': {'config': {'base_offset': 0, 'register_width': 32, 'access_policy': 'CSR offsets are byte addresses; unmapped accesses set csr_error and reads return zero.'}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Control register for start, interrupt enables, and software abort.', 'fields': [{'name': 'start', 'bits': [0, 0], 'access': 'w1p', 'reset': 0, 'description': 'Writing 1 starts one transfer when idle; reads as 0.', 'write_effect': 'Writing 1 while !busy creates start_pulse; writing 1 while busy sets error.'}, {'name': 'irq_done_en', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'Enable irq_done level output.', 'write_effect': 'CSR write updates irq_done_en from csr_wdata[1].'}, {'name': 'irq_error_en', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Enable irq_error level output.', 'write_effect': 'CSR write updates irq_error_en from csr_wdata[2].'}, {'name': 'soft_reset', 'bits': [3, 3], 'access': 'w1p', 'reset': 0, 'description': 'Writing 1 aborts the active transfer and clears transient state.', 'write_effect': 'Writing 1 clears busy, done, error, progress, remaining byte count, and buffered data state.'}, {'name': 'reserved', 'bits': [31, 4], 'access': 'reserved', 'reset': 0, 'description': 'Reserved bits read as zero and ignore writes.', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'STATUS', 'offset': 4, 'width': 32, 'access': 'rw1c', 'reset': 0, 'description': 'Sticky and live transfer status.', 'fields': [{'name': 'busy', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'High while a nonzero-length transfer is active.'}, {'name': 'done', 'bits': [1, 1], 'access': 'rw1c', 'reset': 0, 'description': 'Sticky transfer completion bit.', 'write_effect': 'Writing 1 clears done; writing 0 leaves done unchanged.'}, {'name': 'error', 'bits': [2, 2], 'access': 'rw1c', 'reset': 0, 'description': 'Sticky error bit for illegal CSR or illegal start while busy.', 'write_effect': 'Writing 1 clears error; writing 0 leaves error unchanged.'}, {'name': 'reserved', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'description': 'Reserved bits read as zero and ignore writes.', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'SRC_ADDR', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Source base byte address.', 'fields': [{'name': 'src_addr', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'description': 'Source base byte address captured for the next transfer.', 'write_effect': 'CSR write updates src_addr when the engine is idle.'}]}, {'name': 'DST_ADDR', 'offset': 12, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Destination base byte address.', 'fields': [{'name': 'dst_addr', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'description': 'Destination base byte address captured for the next transfer.', 'write_effect': 'CSR write updates dst_addr when the engine is idle.'}]}, {'name': 'LENGTH', 'offset': 16, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Requested transfer length in bytes.', 'fields': [{'name': 'length_bytes', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'description': 'Requested byte length for the next transfer; zero length completes immediately with no memory request.', 'write_effect': 'CSR write updates length_bytes when the engine is idle.'}]}, {'name': 'PROGRESS', 'offset': 20, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Number of bytes completed in the current or most recent transfer.', 'fields': [{'name': 'progress_bytes', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Completed byte count.'}]}]}, 'function_model': {'purpose': 'Cycle-independent executable behavior contract for the DMA scratch UI.', 'state_variables': [{'name': 'fsm_state', 'width': 3, 'reset': 0, 'description': '0=IDLE, 1=READ_REQ, 2=WRITE_REQ, 3=DONE, 4=ERROR; WAIT_RDATA may share READ_REQ wait subphase in simple RTL.'}, {'name': 'src_addr', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Source base address.'}, {'name': 'dst_addr', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Destination base address.'}, {'name': 'length_bytes', 'width': 'LEN_WIDTH', 'reset': 0, 'description': 'Requested byte count.'}, {'name': 'remaining_bytes', 'width': 'LEN_WIDTH', 'reset': 0, 'description': 'Bytes not yet committed to destination.'}, {'name': 'progress_bytes', 'width': 'LEN_WIDTH', 'reset': 0, 'description': 'Bytes committed to destination.'}, {'name': 'read_data_buffer', 'width': 'DATA_WIDTH', 'reset': 0, 'description': 'Captured source read data for next destination write.'}, {'name': 'write_buffer_full', 'width': 1, 'reset': 0, 'description': 'Read data buffer contains an unwritten beat.'}, {'name': 'busy', 'width': 1, 'reset': 0, 'description': 'Transfer active.'}, {'name': 'done', 'width': 1, 'reset': 0, 'description': 'Sticky completion status.'}, {'name': 'error', 'width': 1, 'reset': 0, 'description': 'Sticky error status.'}, {'name': 'irq_done_en', 'width': 1, 'reset': 0, 'description': 'Done interrupt enable.'}, {'name': 'irq_error_en', 'width': 1, 'reset': 0, 'description': 'Error interrupt enable.'}], 'derived_signals': [{'name': 'beat_bytes', 'expr': 'DATA_WIDTH / 8', 'width': 'LEN_WIDTH', 'description': 'Number of bytes transferred by a full data beat.'}, {'name': 'transfer_bytes', 'expr': 'min(remaining_bytes, beat_bytes)', 'width': 'LEN_WIDTH', 'description': 'Bytes committed by the current write beat.'}, {'name': 'write_strobe', 'expr': '(1 << transfer_bytes) - 1', 'width': 'DATA_WIDTH/8', 'description': 'Final-beat-aware byte strobe; all ones for full beats.'}, {'name': 'status_word', 'expr': 'busy | (done << 1) | (error << 2)', 'width': 'DATA_WIDTH', 'description': 'STATUS register read image.'}, {'name': 'progress_word', 'expr': 'progress_bytes', 'width': 'DATA_WIDTH', 'description': 'PROGRESS register read image.'}, {'name': 'write_buffer_ready', 'expr': 'write_buffer_full == 0', 'width': 1, 'description': 'DMA can accept read data when no buffered write is pending.'}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset', 'sample_condition': 'rst_n == 0', 'preconditions': ['Reset is asserted low.'], 'inputs': ['rst_n'], 'outputs': ['All valid outputs and interrupts are deasserted; CSR ready is low during reset.', {'name': 'csr_ready_reset', 'port': 'csr_ready', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_rd_valid_reset', 'port': 'mem_rd_valid', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_wr_valid_reset', 'port': 'mem_wr_valid', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'irq_done_reset', 'port': 'irq_done', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'irq_error_reset', 'port': 'irq_error', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'busy', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'done', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'error', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'remaining_bytes', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'progress_bytes', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['All state variables return to reset values.'], 'state_updates': [{'name': 'fsm_state', 'expr': '0', 'width': 3}, {'name': 'busy', 'expr': '0', 'width': 1}, {'name': 'done', 'expr': '0', 'width': 1}, {'name': 'error', 'expr': '0', 'width': 1}, {'name': 'remaining_bytes', 'expr': '0', 'width': 'LEN_WIDTH'}, {'name': 'progress_bytes', 'expr': '0', 'width': 'LEN_WIDTH'}, {'name': 'write_buffer_full', 'expr': '0', 'width': 1}], 'output_rules': [{'name': 'csr_ready_reset', 'port': 'csr_ready', 'expr': '0', 'width': 1}, {'name': 'mem_rd_valid_reset', 'port': 'mem_rd_valid', 'expr': '0', 'width': 1}, {'name': 'mem_wr_valid_reset', 'port': 'mem_wr_valid', 'expr': '0', 'width': 1}, {'name': 'irq_done_reset', 'port': 'irq_done', 'expr': '0', 'width': 1}, {'name': 'irq_error_reset', 'port': 'irq_error', 'expr': '0', 'width': 1}]}, {'id': 'FM_CSR_WRITE_CONFIG', 'name': 'csr_write_config', 'sample_condition': 'csr_valid && csr_ready && csr_write && !busy', 'preconditions': ['A legal CSR write to CTRL, SRC_ADDR, DST_ADDR, LENGTH, or STATUS is accepted while idle or clearing status.'], 'inputs': ['csr_addr', 'csr_wdata', 'current CSR state'], 'outputs': ['csr_error remains low for legal writable addresses.', {'name': 'csr_ready_idle_write', 'port': 'csr_ready', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'csr_error_legal_write', 'port': 'csr_error', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'src_addr', 'expr': 'csr_wdata if csr_addr == 8 else src_addr', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'dst_addr', 'expr': 'csr_wdata if csr_addr == 12 else dst_addr', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'length_bytes', 'expr': 'csr_wdata if csr_addr == 16 else length_bytes', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'irq_done_en', 'expr': '((csr_wdata >> 1) & 1) if csr_addr == 0 else irq_done_en', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'irq_error_en', 'expr': '((csr_wdata >> 2) & 1) if csr_addr == 0 else irq_error_en', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'done', 'expr': '0 if (csr_addr == 4 and ((csr_wdata >> 1) & 1) != 0) else done', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'error', 'expr': '0 if (csr_addr == 4 and ((csr_wdata >> 2) & 1) != 0) else error', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['Writable register fields update or sticky STATUS bits clear according to field write_effect definitions.'], 'output_rules': [{'name': 'csr_ready_idle_write', 'port': 'csr_ready', 'expr': '1', 'width': 1}, {'name': 'csr_error_legal_write', 'port': 'csr_error', 'expr': '0', 'width': 1}], 'state_updates': [{'name': 'src_addr', 'expr': 'csr_wdata if csr_addr == 8 else src_addr', 'width': 'ADDR_WIDTH'}, {'name': 'dst_addr', 'expr': 'csr_wdata if csr_addr == 12 else dst_addr', 'width': 'ADDR_WIDTH'}, {'name': 'length_bytes', 'expr': 'csr_wdata if csr_addr == 16 else length_bytes', 'width': 'LEN_WIDTH'}, {'name': 'irq_done_en', 'expr': '((csr_wdata >> 1) & 1) if csr_addr == 0 else irq_done_en', 'width': 1}, {'name': 'irq_error_en', 'expr': '((csr_wdata >> 2) & 1) if csr_addr == 0 else irq_error_en', 'width': 1}, {'name': 'done', 'expr': '0 if (csr_addr == 4 and ((csr_wdata >> 1) & 1) != 0) else done', 'width': 1}, {'name': 'error', 'expr': '0 if (csr_addr == 4 and ((csr_wdata >> 2) & 1) != 0) else error', 'width': 1}]}, {'id': 'FM_START_TRANSFER', 'name': 'start_transfer', 'sample_condition': 'csr_valid && csr_ready && csr_write && csr_addr == 0 && ((csr_wdata & 1) != 0) && !busy', 'preconditions': ['CTRL.start write is accepted while busy is 0.'], 'inputs': ['src_addr', 'dst_addr', 'length_bytes'], 'outputs': ['No memory request is generated for zero length; nonzero length transitions to read request flow.', {'name': 'mem_rd_valid_start', 'port': 'mem_rd_valid', 'expr': '1 if length_bytes != 0 else 0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'irq_done_zero_length', 'port': 'irq_done', 'expr': 'irq_done_en if length_bytes == 0 else 0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'busy', 'expr': '1 if length_bytes != 0 else 0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'done', 'expr': '1 if length_bytes == 0 else 0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'error', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'remaining_bytes', 'expr': 'length_bytes', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'progress_bytes', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '1 if length_bytes != 0 else 3', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['busy, done, remaining_bytes, progress_bytes, and fsm_state update for a new transfer.'], 'output_rules': [{'name': 'mem_rd_valid_start', 'port': 'mem_rd_valid', 'expr': '1 if length_bytes != 0 else 0', 'width': 1}, {'name': 'irq_done_zero_length', 'port': 'irq_done', 'expr': 'irq_done_en if length_bytes == 0 else 0', 'width': 1}], 'state_updates': [{'name': 'busy', 'expr': '1 if length_bytes != 0 else 0', 'width': 1}, {'name': 'done', 'expr': '1 if length_bytes == 0 else 0', 'width': 1}, {'name': 'error', 'expr': '0', 'width': 1}, {'name': 'remaining_bytes', 'expr': 'length_bytes', 'width': 'LEN_WIDTH'}, {'name': 'progress_bytes', 'expr': '0', 'width': 'LEN_WIDTH'}, {'name': 'fsm_state', 'expr': '1 if length_bytes != 0 else 3', 'width': 3}]}, {'id': 'FM_CSR_READ_STATUS', 'name': 'csr_read_status', 'sample_condition': 'csr_valid && csr_ready && !csr_write', 'preconditions': ['A CSR read is accepted for a defined CSR offset.'], 'inputs': ['csr_addr', 'current CSR state'], 'outputs': ['csr_rdata returns selected register image and csr_error is 0 for legal offsets.', {'name': 'csr_ready_read', 'port': 'csr_ready', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'csr_rdata_status', 'port': 'csr_rdata', 'expr': 'status_word if csr_addr == 4 else progress_word', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'csr_error_read', 'port': 'csr_error', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}], 'side_effects': ['CSR reads do not change architectural state.'], 'output_rules': [{'name': 'csr_ready_read', 'port': 'csr_ready', 'expr': '1', 'width': 1}, {'name': 'csr_rdata_status', 'port': 'csr_rdata', 'expr': 'status_word if csr_addr == 4 else progress_word', 'width': 'DATA_WIDTH'}, {'name': 'csr_error_read', 'port': 'csr_error', 'expr': '0', 'width': 1}]}, {'id': 'FM_READ_REQUEST', 'name': 'memory_read_request', 'sample_condition': 'busy && fsm_state == 1', 'preconditions': ['DMA is busy, remaining_bytes is nonzero, and no write buffer is pending.'], 'inputs': ['mem_rd_ready', 'src_addr', 'progress_bytes'], 'outputs': ['Read request valid and address point to the next source beat.', {'name': 'mem_rd_valid_rule', 'port': 'mem_rd_valid', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_rd_addr_rule', 'port': 'mem_rd_addr', 'expr': 'src_addr + progress_bytes', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_rd_data_ready_rule', 'port': 'mem_rd_data_ready', 'expr': 'write_buffer_ready', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '2 if mem_rd_data_valid and mem_rd_data_ready else fsm_state', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['If accepted, the engine waits for matching read data before writing.'], 'output_rules': [{'name': 'mem_rd_valid_rule', 'port': 'mem_rd_valid', 'expr': '1', 'width': 1}, {'name': 'mem_rd_addr_rule', 'port': 'mem_rd_addr', 'expr': 'src_addr + progress_bytes', 'width': 'ADDR_WIDTH'}, {'name': 'mem_rd_data_ready_rule', 'port': 'mem_rd_data_ready', 'expr': 'write_buffer_ready', 'width': 1}], 'state_updates': [{'name': 'fsm_state', 'expr': '2 if mem_rd_data_valid and mem_rd_data_ready else fsm_state', 'width': 3}]}, {'id': 'FM_CAPTURE_READ_DATA', 'name': 'capture_read_data', 'sample_condition': 'busy && mem_rd_data_valid && mem_rd_data_ready', 'preconditions': ['A read data beat is accepted while a transfer is active.'], 'inputs': ['mem_rd_data'], 'outputs': ['The write request path can present the captured data on mem_wr_data.', {'name': 'mem_rd_data_ready_capture', 'port': 'mem_rd_data_ready', 'expr': 'write_buffer_ready', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'read_data_buffer', 'expr': 'mem_rd_data', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '2', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['read_data_buffer captures mem_rd_data and write_buffer_full becomes 1.'], 'output_rules': [{'name': 'mem_rd_data_ready_capture', 'port': 'mem_rd_data_ready', 'expr': 'write_buffer_ready', 'width': 1}], 'state_updates': [{'name': 'read_data_buffer', 'expr': 'mem_rd_data', 'width': 'DATA_WIDTH'}, {'name': 'write_buffer_full', 'expr': '1', 'width': 1}, {'name': 'fsm_state', 'expr': '2', 'width': 3}]}, {'id': 'FM_WRITE_REQUEST', 'name': 'memory_write_request', 'sample_condition': 'busy && fsm_state == 2 && write_buffer_full', 'preconditions': ['Read data buffer holds an unwritten beat.'], 'inputs': ['dst_addr', 'progress_bytes', 'read_data_buffer', 'remaining_bytes', 'mem_wr_ready'], 'outputs': ['Write request valid, address, data, and byte strobes describe the next destination beat.', {'name': 'mem_wr_valid_rule', 'port': 'mem_wr_valid', 'expr': 'write_buffer_full', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_wr_addr_rule', 'port': 'mem_wr_addr', 'expr': 'dst_addr + progress_bytes', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_wr_data_rule', 'port': 'mem_wr_data', 'expr': 'read_data_buffer', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_wr_strb_rule', 'port': 'mem_wr_strb', 'expr': 'write_strobe', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}], 'side_effects': ['State advances only when mem_wr_ready accepts the write beat.'], 'output_rules': [{'name': 'mem_wr_valid_rule', 'port': 'mem_wr_valid', 'expr': 'write_buffer_full', 'width': 1}, {'name': 'mem_wr_addr_rule', 'port': 'mem_wr_addr', 'expr': 'dst_addr + progress_bytes', 'width': 'ADDR_WIDTH'}, {'name': 'mem_wr_data_rule', 'port': 'mem_wr_data', 'expr': 'read_data_buffer', 'width': 'DATA_WIDTH'}, {'name': 'mem_wr_strb_rule', 'port': 'mem_wr_strb', 'expr': 'write_strobe', 'width': 'DATA_WIDTH/8'}]}, {'id': 'FM_WRITE_ACCEPT', 'name': 'memory_write_accept', 'sample_condition': 'busy && mem_wr_valid && mem_wr_ready', 'preconditions': ['Destination memory accepts the current write beat.'], 'inputs': ['remaining_bytes', 'progress_bytes', 'beat_bytes'], 'outputs': ['Completion status and irq_done are asserted when the accepted write is the final beat.', {'name': 'irq_done_on_final_write', 'port': 'irq_done', 'expr': 'irq_done_en and (remaining_bytes <= beat_bytes)', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_wr_valid_after_accept', 'port': 'mem_wr_valid', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'remaining_bytes', 'expr': 'remaining_bytes - transfer_bytes', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'progress_bytes', 'expr': 'progress_bytes + transfer_bytes', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '0', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'busy', 'expr': '0 if remaining_bytes <= beat_bytes else 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'done', 'expr': '1 if remaining_bytes <= beat_bytes else done', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '3 if remaining_bytes <= beat_bytes else 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['remaining_bytes decrements, progress_bytes increments, buffer clears, and the FSM either completes or returns to READ_REQ.'], 'output_rules': [{'name': 'irq_done_on_final_write', 'port': 'irq_done', 'expr': 'irq_done_en and (remaining_bytes <= beat_bytes)', 'width': 1}, {'name': 'mem_wr_valid_after_accept', 'port': 'mem_wr_valid', 'expr': '0', 'width': 1}], 'state_updates': [{'name': 'remaining_bytes', 'expr': 'remaining_bytes - transfer_bytes', 'width': 'LEN_WIDTH'}, {'name': 'progress_bytes', 'expr': 'progress_bytes + transfer_bytes', 'width': 'LEN_WIDTH'}, {'name': 'write_buffer_full', 'expr': '0', 'width': 1}, {'name': 'busy', 'expr': '0 if remaining_bytes <= beat_bytes else 1', 'width': 1}, {'name': 'done', 'expr': '1 if remaining_bytes <= beat_bytes else done', 'width': 1}, {'name': 'fsm_state', 'expr': '3 if remaining_bytes <= beat_bytes else 1', 'width': 3}]}, {'id': 'FM_CLEAR_ABORT', 'name': 'clear_or_abort', 'sample_condition': 'csr_valid && csr_ready && csr_write && ((csr_addr == 4) || (csr_addr == 0 && ((csr_wdata >> 3) & 1) != 0))', 'preconditions': ['STATUS W1C clear or CTRL.soft_reset write is accepted.'], 'inputs': ['csr_addr', 'csr_wdata', 'current status'], 'outputs': ['Memory request valids deassert on soft_reset; interrupts follow cleared sticky status.', {'name': 'mem_rd_valid_abort', 'port': 'mem_rd_valid', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'mem_wr_valid_abort', 'port': 'mem_wr_valid', 'expr': '0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'busy', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else busy', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'done', 'expr': '0 if ((csr_addr == 4 and (((csr_wdata >> 1) & 1) != 0)) or (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0))) else done', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'error', 'expr': '0 if ((csr_addr == 4 and (((csr_wdata >> 2) & 1) != 0)) or (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0))) else error', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else fsm_state', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else write_buffer_full', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['W1C clears done/error; soft_reset aborts active transfer and clears transient state.'], 'output_rules': [{'name': 'mem_rd_valid_abort', 'port': 'mem_rd_valid', 'expr': '0', 'width': 1, 'repair_note': 'Removed self-referential output fallback; transaction precondition/sample_condition owns rule applicability.'}, {'name': 'mem_wr_valid_abort', 'port': 'mem_wr_valid', 'expr': '0', 'width': 1, 'repair_note': 'Removed self-referential output fallback; transaction precondition/sample_condition owns rule applicability.'}], 'state_updates': [{'name': 'busy', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else busy', 'width': 1}, {'name': 'done', 'expr': '0 if ((csr_addr == 4 and (((csr_wdata >> 1) & 1) != 0)) or (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0))) else done', 'width': 1}, {'name': 'error', 'expr': '0 if ((csr_addr == 4 and (((csr_wdata >> 2) & 1) != 0)) or (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0))) else error', 'width': 1}, {'name': 'fsm_state', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else fsm_state', 'width': 3}, {'name': 'write_buffer_full', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else write_buffer_full', 'width': 1}]}, {'id': 'FM_ILLEGAL_CSR_OR_START', 'name': 'illegal_csr_or_start', 'sample_condition': 'csr_valid && csr_ready && ((csr_addr > 20) || (csr_write && csr_addr == 0 && ((csr_wdata & 1) != 0) && busy))', 'preconditions': ['An unmapped CSR access or start-while-busy command is accepted.'], 'inputs': ['csr_addr', 'csr_write', 'csr_wdata', 'busy'], 'outputs': ['csr_error and optionally irq_error report the illegal operation.', {'name': 'csr_error_illegal', 'port': 'csr_error', 'expr': '1', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'irq_error_illegal', 'port': 'irq_error', 'expr': 'irq_error_en', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'error', 'expr': '1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '4 if (csr_write and csr_addr == 0 and ((csr_wdata & 1) != 0) and busy) else fsm_state', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['Sticky error is set without corrupting source/destination/length configuration.'], 'output_rules': [{'name': 'csr_error_illegal', 'port': 'csr_error', 'expr': '1', 'width': 1}, {'name': 'irq_error_illegal', 'port': 'irq_error', 'expr': 'irq_error_en', 'width': 1}], 'state_updates': [{'name': 'error', 'expr': '1', 'width': 1}, {'name': 'fsm_state', 'expr': '4 if (csr_write and csr_addr == 0 and ((csr_wdata & 1) != 0) and busy) else fsm_state', 'width': 3}]}], 'invariants': ['All architectural state updates are synchronous to clk and reset to declared values when rst_n is asserted low.', 'Memory write data for a beat equals the previously accepted read data for that beat.', 'A new read request is not issued while write_buffer_full is 1.', 'busy is 1 only during an active nonzero-length transfer and deasserts on final write acceptance, reset, or soft_reset.', 'done and error are sticky until reset, soft_reset, or W1C clear.'], 'reference_model_hint': 'tb-gen should build a byte-counting reference DMA scoreboard from function_model transactions and compare CSR, memory, and IRQ observations.'}, 'cycle_model': {'purpose': 'Cycle and handshake contract for rtl-gen and waveform-based verification.', 'executable': 'pymtl3', 'backend_policy': 'Use a simple clocked PyMTL3 shell or cocotb scoreboard driven by this SSOT; FunctionalModel is the behavioral oracle.', 'clock': 'clk', 'reset': {'signal': 'rst_n', 'polarity': 'active_low', 'assertion': 'rst_n low asynchronously drives architectural state to reset values and deasserts memory valids.', 'deassertion': 'Logic accepts transactions after reset deassertion is sampled by clk.'}, 'latency': {'csr_access': {'min_cycles': 0, 'max_cycles': 1, 'description': 'CSR read/write completes in the accepted cycle for ready-high operation.'}, 'zero_length_transfer': {'min_cycles': 1, 'max_cycles': 1, 'description': 'A start with LENGTH=0 sets done without memory requests on the start accepting clock edge.'}, 'per_beat_transfer': {'min_cycles': 2, 'max_cycles': None, 'description': 'At least read data capture plus write acceptance per beat; unbounded with external backpressure.'}}, 'handshake_rules': [{'signal': 'csr_valid/csr_ready', 'rule': 'CSR request fields remain stable while csr_valid is high and csr_ready is low.'}, {'signal': 'mem_rd_valid/mem_rd_ready', 'rule': 'mem_rd_addr remains stable until the read address handshake completes.'}, {'signal': 'mem_rd_data_valid/mem_rd_data_ready', 'rule': 'mem_rd_data is sampled only on valid/ready and is not consumed when ready is low.'}, {'signal': 'mem_wr_valid/mem_wr_ready', 'rule': 'mem_wr_addr, mem_wr_data, and mem_wr_strb remain stable until write acceptance.'}], 'pipeline': [{'stage': 'CSR_ACCEPT', 'cycle': '0..N', 'action': 'Accept configuration, status clear, abort, or start command.'}, {'stage': 'READ_ADDR', 'cycle': 'N..M', 'action': 'Issue source read address when active transfer has no pending buffered write.'}, {'stage': 'CAPTURE_READ_DATA', 'cycle': 'M..K', 'action': 'Capture source read payload on read-data valid/ready.'}, {'stage': 'WRITE_BEAT', 'cycle': 'K..L', 'action': 'Issue destination write and update progress when accepted.'}, {'stage': 'COMPLETE_OR_LOOP', 'cycle': 'L..L+1', 'action': 'Set done on final beat or return to READ_ADDR for additional bytes.'}], 'ordering': ['Accepted CSR writes update state on clk edges.', 'Read-address acceptance precedes dependent read-data capture.', 'Read-data capture precedes dependent write request acceptance.', 'Progress increments only after the corresponding write handshake.', 'Backpressure stalls only the affected handshake stage and preserves payload stability.'], 'backpressure': ['Any ready-low condition holds the corresponding valid and payload stable.', 'The engine supports at most one uncommitted read data beat.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 0.5, 'condition': 'No memory backpressure and single outstanding read/write sequencing.'}, 'outstanding': {'max': 1, 'description': 'One read response/write beat in flight.'}, 'depth': {'pipeline_stages': 5, 'queue_depth': 1, 'description': 'CSR accept, read request, read capture, write request, complete/loop.'}}, 'observability': ['Each function_model transaction maps to a named pipeline stage and a test scenario.']}, 'fcov_bins': [{'id': 'SC01_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC01', 'description': 'reset_defaults'}, {'id': 'SC02_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC02', 'description': 'csr_programming_readback'}, {'id': 'SC03_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC03', 'description': 'illegal_csr_access'}, {'id': 'SC04_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC04', 'description': 'zero_length_transfer'}, {'id': 'SC05_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC05', 'description': 'single_beat_copy'}, {'id': 'SC06_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC06', 'description': 'multi_beat_copy'}, {'id': 'SC07_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC07', 'description': 'partial_final_beat'}, {'id': 'SC08_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC08', 'description': 'read_backpressure'}, {'id': 'SC09_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC09', 'description': 'write_backpressure'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'soft_reset_abort'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'status_w1c_irq_clear'}, {'id': 'fcov_tx_all', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions', 'source_ref': 'function_model.transactions', 'description': 'Each named transaction sampled at least once.'}, {'id': 'fcov_error', 'class': 'error_path', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ILLEGAL_CSR_OR_START', 'source_ref': 'function_model.transactions.FM_ILLEGAL_CSR_OR_START', 'description': 'Illegal CSR and start-while-busy errors observed.'}, {'id': 'fcov_strobe', 'class': 'datapath', 'coverage_domain': 'function', 'source': 'function_model.derived_signals.write_strobe', 'source_ref': 'function_model.derived_signals.write_strobe', 'description': 'Full and partial write strobes observed.'}, {'id': 'ccov_handshakes', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'CSR, read address, read data, and write handshakes observed.'}, {'id': 'ccov_pipeline', 'class': 'cycle_rule', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'All declared pipeline stages observed.'}, {'id': 'ccov_backpressure', 'class': 'stall', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure', 'source_ref': 'cycle_model.backpressure', 'description': 'Read and write stall cases observed.'}, {'id': 'function_reset', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_reset', 'description': 'reset'}, {'id': 'function_csr_write_config', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_csr_write_config', 'description': 'csr_write_config'}, {'id': 'function_start_transfer', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_start_transfer', 'description': 'start_transfer'}, {'id': 'function_csr_read_status', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_csr_read_status', 'description': 'csr_read_status'}, {'id': 'function_memory_read_request', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_read_request', 'description': 'memory_read_request'}, {'id': 'function_capture_read_data', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_capture_read_data', 'description': 'capture_read_data'}, {'id': 'function_memory_write_request', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm_write_request', 'description': 'memory_write_request'}, {'id': 'function_memory_write_accept', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[7]', 'source_ref': 'function_model.transactions.fm_write_accept', 'description': 'memory_write_accept'}, {'id': 'function_clear_or_abort', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[8]', 'source_ref': 'function_model.transactions.fm_clear_abort', 'description': 'clear_or_abort'}, {'id': 'function_illegal_csr_or_start', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[9]', 'source_ref': 'function_model.transactions.fm_illegal_csr_or_start', 'description': 'illegal_csr_or_start'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'csr_valid/csr_ready', 'rule': 'CSR request fields remain stable while csr_valid is high and csr_ready is low.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'mem_rd_valid/mem_rd_ready', 'rule': 'mem_rd_addr remains stable until the read address handshake completes.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'mem_rd_data_valid/mem_rd_data_ready', 'rule': 'mem_rd_data is sampled only on valid/ready and is not consumed when ready is low.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'mem_wr_valid/mem_wr_ready', 'rule': 'mem_wr_addr, mem_wr_data, and mem_wr_strb remain stable until write acceptance.'}"}, {'id': 'cycle_latency_csr_access', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.csr_access', 'source_ref': 'cycle_model.latency.csr_access', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'CSR read/write completes in the accepted cycle for ready-high operation.'}"}, {'id': 'cycle_latency_zero_length_transfer', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.zero_length_transfer', 'source_ref': 'cycle_model.latency.zero_length_transfer', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'A start with LENGTH=0 sets done without memory requests on the start accepting clock edge.'}"}, {'id': 'cycle_latency_per_beat_transfer', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.per_beat_transfer', 'source_ref': 'cycle_model.latency.per_beat_transfer', 'description': "{'min_cycles': 2, 'max_cycles': None, 'description': 'At least read data capture plus write acceptance per beat; unbounded with external backpressure.'}"}, {'id': 'cycle_pipeline_csr_accept', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Accept configuration, status clear, abort, or start command.'}, {'id': 'cycle_pipeline_read_addr', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Issue source read address when active transfer has no pending buffered write.'}, {'id': 'cycle_pipeline_capture_read_data', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Capture source read payload on read-data valid/ready.'}, {'id': 'cycle_pipeline_write_beat', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Issue destination write and update progress when accepted.'}, {'id': 'cycle_pipeline_complete_or_loop', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Set done on final beat or return to READ_ADDR for additional bytes.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Accepted CSR writes update state on clk edges.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Read-address acceptance precedes dependent read-data capture.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Read-data capture precedes dependent write request acceptance.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'Progress increments only after the corresponding write handshake.'}, {'id': 'cycle_ordering_4', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[4]', 'source_ref': 'cycle_model.ordering[4]', 'description': 'Backpressure stalls only the affected handshake stage and preserves payload stability.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'Any ready-low condition holds the corresponding valid and payload stable.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'The engine supports at most one uncommitted read data beat.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'max': 1, 'description': 'One read response/write beat in flight.'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 5, 'queue_depth': 1, 'description': 'CSR accept, read request, read capture, write request, complete/loop.'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '100'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_beats_per_cycle': 0.5, 'condition': 'No memory backpressure and single outstanding read/write sequencing.'}"}, {'id': 'fsm_control_idle_to_done_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[0]', 'source_ref': 'fsm.control.transitions[0]', 'description': "{'from': 'IDLE', 'to': 'DONE', 'when': 'start_pulse && length_bytes == 0'}"}, {'id': 'fsm_control_idle_to_read_req_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[1]', 'source_ref': 'fsm.control.transitions[1]', 'description': "{'from': 'IDLE', 'to': 'READ_REQ', 'when': 'start_pulse && length_bytes != 0'}"}, {'id': 'fsm_control_idle_to_error_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[2]', 'source_ref': 'fsm.control.transitions[2]', 'description': "{'from': 'IDLE', 'to': 'ERROR', 'when': 'start_pulse && busy'}"}, {'id': 'fsm_control_read_req_to_wait_rdata_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[3]', 'source_ref': 'fsm.control.transitions[3]', 'description': "{'from': 'READ_REQ', 'to': 'WAIT_RDATA', 'when': 'mem_rd_valid && mem_rd_ready'}"}, {'id': 'fsm_control_wait_rdata_to_write_req_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[4]', 'source_ref': 'fsm.control.transitions[4]', 'description': "{'from': 'WAIT_RDATA', 'to': 'WRITE_REQ', 'when': 'mem_rd_data_valid && mem_rd_data_ready'}"}, {'id': 'fsm_control_write_req_to_done_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[5]', 'source_ref': 'fsm.control.transitions[5]', 'description': "{'from': 'WRITE_REQ', 'to': 'DONE', 'when': 'mem_wr_valid && mem_wr_ready && remaining_bytes <= beat_bytes'}"}, {'id': 'fsm_control_write_req_to_read_req_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[6]', 'source_ref': 'fsm.control.transitions[6]', 'description': "{'from': 'WRITE_REQ', 'to': 'READ_REQ', 'when': 'mem_wr_valid && mem_wr_ready && remaining_bytes > beat_bytes'}"}, {'id': 'fsm_control_read_req_wait_rdata_write_req_to_idle_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[7]', 'source_ref': 'fsm.control.transitions[7]', 'description': "{'from': ['READ_REQ', 'WAIT_RDATA', 'WRITE_REQ'], 'to': 'IDLE', 'when': 'soft_reset_pulse'}"}, {'id': 'fsm_control_done_to_idle_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[8]', 'source_ref': 'fsm.control.transitions[8]', 'description': "{'from': 'DONE', 'to': 'IDLE', 'when': 'done is cleared and no new start is pending'}"}, {'id': 'fsm_control_error_to_idle_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[9]', 'source_ref': 'fsm.control.transitions[9]', 'description': "{'from': 'ERROR', 'to': 'IDLE', 'when': 'error is cleared and no new start is pending'}"}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_ILLEGAL_CSR', 'condition': 'CSR address is not one of 0, 4, 8, 12, 16, or 20.', 'architectural_effect': 'Assert csr_error for the accepted access, set sticky error, and assert irq_error if enabled.'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_START_WHILE_BUSY', 'condition': 'CTRL.start is written with 1 while busy is already 1.', 'architectural_effect': 'Assert csr_error, set sticky error, keep the active transfer state intact, and assert irq_error if enabled.'}"}]}
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
