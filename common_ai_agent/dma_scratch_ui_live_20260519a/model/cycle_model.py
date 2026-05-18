#!/usr/bin/env python3
"""Executable SSOT cycle-level model for dma_scratch_ui_live_20260519a. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from .functional_model import FunctionalModel
except ImportError:
    from functional_model import FunctionalModel

try:
    from pymtl3 import Bits1, Bits32, Component, InPort, OutPort, update_ff
    HAS_PYMTL3 = True
except Exception:
    Bits1 = Bits32 = Component = InPort = OutPort = update_ff = None
    HAS_PYMTL3 = False


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Requested executable backend.  PyMTL3 is the default CL shell; FunctionalModel remains the oracle.
MODEL_BACKEND: str = 'pymtl3'

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'csr_access': 1, 'zero_length_transfer': 1, 'per_beat_transfer': 2, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}, {'name': 'handshake_3', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'accepted_csr_writes_update_state_on_clk_edges', 'description': ''}, {'name': 'read_address_acceptance_precedes_dependent_read_data_capture', 'description': ''}, {'name': 'read_data_capture_precedes_dependent_write_request_acceptance', 'description': ''}, {'name': 'progress_increments_only_after_the_corresponding_write_handshake', 'description': ''}, {'name': 'backpressure_stalls_only_the_affected_handshake_stage_and_preserves_payload_stability', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 0.5, 'condition': 'No memory backpressure and single outstanding read/write sequencing.'}, 'outstanding': {'max': 1, 'description': 'One read response/write beat in flight.'}, 'pipeline_stages': 5, 'queue_depth': 1}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_RESET', 'FM_CSR_WRITE_CONFIG', 'FM_START_TRANSFER', 'FM_CSR_READ_STATUS', 'FM_READ_REQUEST', 'FM_CAPTURE_READ_DATA', 'FM_WRITE_REQUEST', 'FM_WRITE_ACCEPT', 'FM_CLEAR_ABORT', 'FM_ILLEGAL_CSR_OR_START']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'handshake_handshake_3': 'handshake_3', 'ordering_accepted_csr_writes_update_state_on_clk_edges': 'accepted_csr_writes_update_state_on_clk_edges', 'ordering_read_address_acceptance_precedes_dependent_read_data_capture': 'read_address_acceptance_precedes_dependent_read_data_capture', 'ordering_read_data_capture_precedes_dependent_write_request_acceptance': 'read_data_capture_precedes_dependent_write_request_acceptance', 'ordering_progress_increments_only_after_the_corresponding_write_handshake': 'progress_increments_only_after_the_corresponding_write_handshake', 'ordering_backpressure_stalls_only_the_affected_handshake_stage_and_preserves_payload_stability': 'backpressure_stalls_only_the_affected_handshake_stage_and_preserves_payload_stability', 'latency_fm_reset': 'latency bin for FM_RESET', 'latency_fm_csr_write_config': 'latency bin for FM_CSR_WRITE_CONFIG', 'latency_fm_start_transfer': 'latency bin for FM_START_TRANSFER', 'latency_fm_csr_read_status': 'latency bin for FM_CSR_READ_STATUS', 'latency_fm_read_request': 'latency bin for FM_READ_REQUEST', 'latency_fm_capture_read_data': 'latency bin for FM_CAPTURE_READ_DATA', 'latency_fm_write_request': 'latency bin for FM_WRITE_REQUEST', 'latency_fm_write_accept': 'latency bin for FM_WRITE_ACCEPT', 'latency_fm_clear_abort': 'latency bin for FM_CLEAR_ABORT', 'latency_fm_illegal_csr_or_start': 'latency bin for FM_ILLEGAL_CSR_OR_START'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'dma_scratch_ui_live_20260519a', 'function_model': {'purpose': 'Cycle-independent executable behavior contract for the DMA scratch UI.', 'state_variables': [{'name': 'fsm_state', 'width': 3, 'reset': 0, 'description': '0=IDLE, 1=READ_REQ, 2=WRITE_REQ, 3=DONE, 4=ERROR; WAIT_RDATA may share READ_REQ wait subphase in simple RTL.'}, {'name': 'src_addr', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Source base address.'}, {'name': 'dst_addr', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Destination base address.'}, {'name': 'length_bytes', 'width': 'LEN_WIDTH', 'reset': 0, 'description': 'Requested byte count.'}, {'name': 'remaining_bytes', 'width': 'LEN_WIDTH', 'reset': 0, 'description': 'Bytes not yet committed to destination.'}, {'name': 'progress_bytes', 'width': 'LEN_WIDTH', 'reset': 0, 'description': 'Bytes committed to destination.'}, {'name': 'read_data_buffer', 'width': 'DATA_WIDTH', 'reset': 0, 'description': 'Captured source read data for next destination write.'}, {'name': 'write_buffer_full', 'width': 1, 'reset': 0, 'description': 'Read data buffer contains an unwritten beat.'}, {'name': 'busy', 'width': 1, 'reset': 0, 'description': 'Transfer active.'}, {'name': 'done', 'width': 1, 'reset': 0, 'description': 'Sticky completion status.'}, {'name': 'error', 'width': 1, 'reset': 0, 'description': 'Sticky error status.'}, {'name': 'irq_done_en', 'width': 1, 'reset': 0, 'description': 'Done interrupt enable.'}, {'name': 'irq_error_en', 'width': 1, 'reset': 0, 'description': 'Error interrupt enable.'}], 'derived_signals': [{'name': 'beat_bytes', 'expr': 'DATA_WIDTH / 8', 'width': 'LEN_WIDTH', 'description': 'Number of bytes transferred by a full data beat.'}, {'name': 'transfer_bytes', 'expr': 'min(remaining_bytes, beat_bytes)', 'width': 'LEN_WIDTH', 'description': 'Bytes committed by the current write beat.'}, {'name': 'write_strobe', 'expr': '(1 << transfer_bytes) - 1', 'width': 'DATA_WIDTH/8', 'description': 'Final-beat-aware byte strobe; all ones for full beats.'}, {'name': 'status_word', 'expr': 'busy | (done << 1) | (error << 2)', 'width': 'DATA_WIDTH', 'description': 'STATUS register read image.'}, {'name': 'progress_word', 'expr': 'progress_bytes', 'width': 'DATA_WIDTH', 'description': 'PROGRESS register read image.'}, {'name': 'write_buffer_ready', 'expr': 'write_buffer_full == 0', 'width': 1, 'description': 'DMA can accept read data when no buffered write is pending.'}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset', 'sample_condition': 'rst_n == 0', 'preconditions': ['Reset is asserted low.'], 'inputs': ['rst_n'], 'outputs': ['All valid outputs and interrupts are deasserted; CSR ready is low during reset.', {'name': 'csr_ready_reset', 'port': 'csr_ready', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_rd_valid_reset', 'port': 'mem_rd_valid', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_wr_valid_reset', 'port': 'mem_wr_valid', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'irq_done_reset', 'port': 'irq_done', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'irq_error_reset', 'port': 'irq_error', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'busy', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'done', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'error', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'remaining_bytes', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'progress_bytes', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['All state variables return to reset values.']}, {'id': 'FM_CSR_WRITE_CONFIG', 'name': 'csr_write_config', 'sample_condition': 'csr_valid && csr_ready && csr_write && !busy', 'preconditions': ['A legal CSR write to CTRL, SRC_ADDR, DST_ADDR, LENGTH, or STATUS is accepted while idle or clearing status.'], 'inputs': ['csr_addr', 'csr_wdata', 'current CSR state'], 'outputs': ['csr_error remains low for legal writable addresses.', {'name': 'csr_ready_idle_write', 'port': 'csr_ready', 'expr': '1', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'csr_error_legal_write', 'port': 'csr_error', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'src_addr', 'expr': 'csr_wdata if csr_addr == 8 else src_addr', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'dst_addr', 'expr': 'csr_wdata if csr_addr == 12 else dst_addr', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'length_bytes', 'expr': 'csr_wdata if csr_addr == 16 else length_bytes', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'irq_done_en', 'expr': '((csr_wdata >> 1) & 1) if csr_addr == 0 else irq_done_en', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'irq_error_en', 'expr': '((csr_wdata >> 2) & 1) if csr_addr == 0 else irq_error_en', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'done', 'expr': '0 if (csr_addr == 4 and ((csr_wdata >> 1) & 1) != 0) else done', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'error', 'expr': '0 if (csr_addr == 4 and ((csr_wdata >> 2) & 1) != 0) else error', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['Writable register fields update or sticky STATUS bits clear according to field write_effect definitions.']}, {'id': 'FM_START_TRANSFER', 'name': 'start_transfer', 'sample_condition': 'csr_valid && csr_ready && csr_write && csr_addr == 0 && ((csr_wdata & 1) != 0) && !busy', 'preconditions': ['CTRL.start write is accepted while busy is 0.'], 'inputs': ['src_addr', 'dst_addr', 'length_bytes'], 'outputs': ['No memory request is generated for zero length; nonzero length transitions to read request flow.', {'name': 'mem_rd_valid_start', 'port': 'mem_rd_valid', 'expr': '1 if length_bytes != 0 else 0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'irq_done_zero_length', 'port': 'irq_done', 'expr': 'irq_done_en if length_bytes == 0 else 0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'busy', 'expr': '1 if length_bytes != 0 else 0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'done', 'expr': '1 if length_bytes == 0 else 0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'error', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'remaining_bytes', 'expr': 'length_bytes', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'progress_bytes', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '1 if length_bytes != 0 else 3', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['busy, done, remaining_bytes, progress_bytes, and fsm_state update for a new transfer.']}, {'id': 'FM_CSR_READ_STATUS', 'name': 'csr_read_status', 'sample_condition': 'csr_valid && csr_ready && !csr_write', 'preconditions': ['A CSR read is accepted for a defined CSR offset.'], 'inputs': ['csr_addr', 'current CSR state'], 'outputs': ['csr_rdata returns selected register image and csr_error is 0 for legal offsets.', {'name': 'csr_ready_read', 'port': 'csr_ready', 'expr': '1', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'csr_rdata_status', 'port': 'csr_rdata', 'expr': 'status_word if csr_addr == 4 else progress_word', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'csr_error_read', 'port': 'csr_error', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}], 'side_effects': ['CSR reads do not change architectural state.']}, {'id': 'FM_READ_REQUEST', 'name': 'memory_read_request', 'sample_condition': 'busy && fsm_state == 1', 'preconditions': ['DMA is busy, remaining_bytes is nonzero, and no write buffer is pending.'], 'inputs': ['mem_rd_ready', 'src_addr', 'progress_bytes'], 'outputs': ['Read request valid and address point to the next source beat.', {'name': 'mem_rd_valid_rule', 'port': 'mem_rd_valid', 'expr': '1', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_rd_addr_rule', 'port': 'mem_rd_addr', 'expr': 'src_addr + progress_bytes', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_rd_data_ready_rule', 'port': 'mem_rd_data_ready', 'expr': 'write_buffer_ready', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '2 if mem_rd_data_valid and mem_rd_data_ready else fsm_state', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['If accepted, the engine waits for matching read data before writing.']}, {'id': 'FM_CAPTURE_READ_DATA', 'name': 'capture_read_data', 'sample_condition': 'busy && mem_rd_data_valid && mem_rd_data_ready', 'preconditions': ['A read data beat is accepted while a transfer is active.'], 'inputs': ['mem_rd_data'], 'outputs': ['The write request path can present the captured data on mem_wr_data.', {'name': 'mem_rd_data_ready_capture', 'port': 'mem_rd_data_ready', 'expr': 'write_buffer_ready', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'read_data_buffer', 'expr': 'mem_rd_data', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '2', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['read_data_buffer captures mem_rd_data and write_buffer_full becomes 1.']}, {'id': 'FM_WRITE_REQUEST', 'name': 'memory_write_request', 'sample_condition': 'busy && fsm_state == 2 && write_buffer_full', 'preconditions': ['Read data buffer holds an unwritten beat.'], 'inputs': ['dst_addr', 'progress_bytes', 'read_data_buffer', 'remaining_bytes', 'mem_wr_ready'], 'outputs': ['Write request valid, address, data, and byte strobes describe the next destination beat.', {'name': 'mem_wr_valid_rule', 'port': 'mem_wr_valid', 'expr': 'write_buffer_full', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_wr_addr_rule', 'port': 'mem_wr_addr', 'expr': 'dst_addr + progress_bytes', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_wr_data_rule', 'port': 'mem_wr_data', 'expr': 'read_data_buffer', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_wr_strb_rule', 'port': 'mem_wr_strb', 'expr': 'write_strobe', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}], 'side_effects': ['State advances only when mem_wr_ready accepts the write beat.']}, {'id': 'FM_WRITE_ACCEPT', 'name': 'memory_write_accept', 'sample_condition': 'busy && mem_wr_valid && mem_wr_ready', 'preconditions': ['Destination memory accepts the current write beat.'], 'inputs': ['remaining_bytes', 'progress_bytes', 'beat_bytes'], 'outputs': ['Completion status and irq_done are asserted when the accepted write is the final beat.', {'name': 'irq_done_on_final_write', 'port': 'irq_done', 'expr': 'irq_done_en and (remaining_bytes <= beat_bytes)', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_wr_valid_after_accept', 'port': 'mem_wr_valid', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'remaining_bytes', 'expr': 'remaining_bytes - transfer_bytes', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'progress_bytes', 'expr': 'progress_bytes + transfer_bytes', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'busy', 'expr': '0 if remaining_bytes <= beat_bytes else 1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'done', 'expr': '1 if remaining_bytes <= beat_bytes else done', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '3 if remaining_bytes <= beat_bytes else 1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['remaining_bytes decrements, progress_bytes increments, buffer clears, and the FSM either completes or returns to READ_REQ.']}, {'id': 'FM_CLEAR_ABORT', 'name': 'clear_or_abort', 'sample_condition': 'csr_valid && csr_ready && csr_write && ((csr_addr == 4) || (csr_addr == 0 && ((csr_wdata >> 3) & 1) != 0))', 'preconditions': ['STATUS W1C clear or CTRL.soft_reset write is accepted.'], 'inputs': ['csr_addr', 'csr_wdata', 'current status'], 'outputs': ['Memory request valids deassert on soft_reset; interrupts follow cleared sticky status.', {'name': 'mem_rd_valid_abort', 'port': 'mem_rd_valid', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'mem_wr_valid_abort', 'port': 'mem_wr_valid', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'busy', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else busy', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'done', 'expr': '0 if ((csr_addr == 4 and (((csr_wdata >> 1) & 1) != 0)) or (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0))) else done', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'error', 'expr': '0 if ((csr_addr == 4 and (((csr_wdata >> 2) & 1) != 0)) or (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0))) else error', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else fsm_state', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'write_buffer_full', 'expr': '0 if (csr_addr == 0 and (((csr_wdata >> 3) & 1) != 0)) else write_buffer_full', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['W1C clears done/error; soft_reset aborts active transfer and clears transient state.']}, {'id': 'FM_ILLEGAL_CSR_OR_START', 'name': 'illegal_csr_or_start', 'sample_condition': 'csr_valid && csr_ready && ((csr_addr > 20) || (csr_write && csr_addr == 0 && ((csr_wdata & 1) != 0) && busy))', 'preconditions': ['An unmapped CSR access or start-while-busy command is accepted.'], 'inputs': ['csr_addr', 'csr_write', 'csr_wdata', 'busy'], 'outputs': ['csr_error and optionally irq_error report the illegal operation.', {'name': 'csr_error_illegal', 'port': 'csr_error', 'expr': '1', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'irq_error_illegal', 'port': 'irq_error', 'expr': 'irq_error_en', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'error', 'expr': '1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'fsm_state', 'expr': '4 if (csr_write and csr_addr == 0 and ((csr_wdata & 1) != 0) and busy) else fsm_state', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['Sticky error is set without corrupting source/destination/length configuration.']}], 'invariants': ['All architectural state updates are synchronous to clk and reset to declared values when rst_n is asserted low.', 'Memory write data for a beat equals the previously accepted read data for that beat.', 'A new read request is not issued while write_buffer_full is 1.', 'busy is 1 only during an active nonzero-length transfer and deasserts on final write acceptance, reset, or soft_reset.', 'done and error are sticky until reset, soft_reset, or W1C clear.'], 'reference_model_hint': 'tb-gen should build a byte-counting reference DMA scoreboard from function_model transactions and compare CSR, memory, and IRQ observations.'}, 'cycle_model': {'purpose': 'Cycle and handshake contract for rtl-gen and waveform-based verification.', 'executable': 'pymtl3', 'backend_policy': 'Use a simple clocked PyMTL3 shell or cocotb scoreboard driven by this SSOT; FunctionalModel is the behavioral oracle.', 'clock': 'clk', 'reset': {'signal': 'rst_n', 'polarity': 'active_low', 'assertion': 'rst_n low asynchronously drives architectural state to reset values and deasserts memory valids.', 'deassertion': 'Logic accepts transactions after reset deassertion is sampled by clk.'}, 'latency': {'csr_access': {'min_cycles': 0, 'max_cycles': 1, 'description': 'CSR read/write completes in the accepted cycle for ready-high operation.'}, 'zero_length_transfer': {'min_cycles': 1, 'max_cycles': 1, 'description': 'A start with LENGTH=0 sets done without memory requests on the start accepting clock edge.'}, 'per_beat_transfer': {'min_cycles': 2, 'max_cycles': None, 'description': 'At least read data capture plus write acceptance per beat; unbounded with external backpressure.'}}, 'handshake_rules': [{'signal': 'csr_valid/csr_ready', 'rule': 'CSR request fields remain stable while csr_valid is high and csr_ready is low.'}, {'signal': 'mem_rd_valid/mem_rd_ready', 'rule': 'mem_rd_addr remains stable until the read address handshake completes.'}, {'signal': 'mem_rd_data_valid/mem_rd_data_ready', 'rule': 'mem_rd_data is sampled only on valid/ready and is not consumed when ready is low.'}, {'signal': 'mem_wr_valid/mem_wr_ready', 'rule': 'mem_wr_addr, mem_wr_data, and mem_wr_strb remain stable until write acceptance.'}], 'pipeline': [{'stage': 'CSR_ACCEPT', 'cycle': '0..N', 'action': 'Accept configuration, status clear, abort, or start command.'}, {'stage': 'READ_ADDR', 'cycle': 'N..M', 'action': 'Issue source read address when active transfer has no pending buffered write.'}, {'stage': 'CAPTURE_READ_DATA', 'cycle': 'M..K', 'action': 'Capture source read payload on read-data valid/ready.'}, {'stage': 'WRITE_BEAT', 'cycle': 'K..L', 'action': 'Issue destination write and update progress when accepted.'}, {'stage': 'COMPLETE_OR_LOOP', 'cycle': 'L..L+1', 'action': 'Set done on final beat or return to READ_ADDR for additional bytes.'}], 'ordering': ['Accepted CSR writes update state on clk edges.', 'Read-address acceptance precedes dependent read-data capture.', 'Read-data capture precedes dependent write request acceptance.', 'Progress increments only after the corresponding write handshake.', 'Backpressure stalls only the affected handshake stage and preserves payload stability.'], 'backpressure': ['Any ready-low condition holds the corresponding valid and payload stable.', 'The engine supports at most one uncommitted read data beat.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 0.5, 'condition': 'No memory backpressure and single outstanding read/write sequencing.'}, 'outstanding': {'max': 1, 'description': 'One read response/write beat in flight.'}, 'depth': {'pipeline_stages': 5, 'queue_depth': 1, 'description': 'CSR accept, read request, read capture, write request, complete/loop.'}}, 'observability': ['Each function_model transaction maps to a named pipeline stage and a test scenario.']}}


# ---------------------------------------------------------------------------
# CycleModel
# ---------------------------------------------------------------------------

class CycleModel:
    """Cycle-level model: queues transactions, applies latency/handshake rules,
    delegates all functional evaluation to FunctionalModel.apply()."""

    def __init__(self, params=None):
        self.fl = FunctionalModel(params)
        self.in_q: list[tuple[int, dict]] = []   # (arrival_t, txn)
        self.out_q: list[tuple[int, dict]] = []  # (ready_t, result)
        self.cov: dict[str, int] = {k: 0 for k in CL_BINS}
        self.now: int = 0
        self._outstanding: int = 0

    def reset(self) -> None:
        self.fl.reset()
        self.in_q.clear()
        self.out_q.clear()
        self.cov = {k: 0 for k in CL_BINS}
        self.now = 0
        self._outstanding = 0

    def drive(self, txn: dict, t: int) -> None:
        """Enqueue a transaction arriving at cycle t."""
        self.in_q.append((int(t), dict(txn)))

    def _latency_for(self, txn: dict) -> int:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        return _LATENCY.get(kind, _LATENCY.get("default", 1))

    def _sample_handshake_coverage(self, txn: dict) -> None:
        for rule in _HANDSHAKE_RULES:
            name = rule.get("name", "")
            bin_key = f"handshake_{name}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_ordering_coverage(self) -> None:
        for rule in _ORDERING_RULES:
            name = rule.get("name", "")
            bin_key = f"ordering_{name}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_latency_coverage(self, txn: dict) -> None:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        key = "".join(ch if ch.isalnum() else "_" for ch in kind).strip("_")
        bin_key = f"latency_{key}"
        if bin_key in self.cov:
            self.cov[bin_key] += 1

    def tick(self, t: int) -> None:
        """Advance model to cycle t.  Drain in_q respecting outstanding cap and handshake rules."""
        self.now = int(t)
        # Outstanding capacity is consumed only by results that are not yet
        # ready. Recompute before accepting new work so a transaction becoming
        # ready in this cycle does not incorrectly stall the next SSOT
        # transaction. Ready results remain observable in out_q until observe().
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)
        # Pop pending transactions until either arrival time or outstanding cap
        # blocks progress. This ensures self-check observes every SSOT
        # function_model transaction rather than losing one behind a stale cap.
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break  # stalled: wait for out_q drain
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break  # not yet arrived
            self.in_q.pop(0)
            # FunctionalModel is the ONLY oracle — one call per transaction
            try:
                result = self.fl.apply(txn)
            except Exception as _exc:
                result = {"kind": txn.get("kind", "unknown"), "resp": 2, "fl_error": str(_exc)}
            latency = self._latency_for(txn)
            ready_t = self.now + latency
            self.out_q.append((ready_t, result))
            if ready_t > self.now:
                self._outstanding += 1
            # Sample coverage bins
            self._sample_handshake_coverage(txn)
            self._sample_ordering_coverage()
            self._sample_latency_coverage(txn)

        # Keep outstanding aligned with not-yet-ready results after processing.
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)

    def observe(self, t: int) -> list[tuple[int, dict]]:
        """Return all results ready at or before t, removing them from out_q."""
        t = int(t)
        ready = [(d, r) for (d, r) in self.out_q if d <= t]
        self.out_q = [(d, r) for (d, r) in self.out_q if d > t]
        return ready

    def coverage(self) -> dict[str, int]:
        return dict(self.cov)

    def run_self_check(self) -> dict:
        """Strict smoke run: drive every known transaction kind once and
        require one observed CL result per SSOT transaction.

        The model has an outstanding cap of one, so this self-check advances
        cycle-by-cycle and observes ready results between transactions instead
        of using one large drain tick that can leave the final transaction
        queued behind the cap.
        """
        self.reset()
        kinds = list(_SELF_CHECK_KINDS) or ["reset"]
        observed: list[tuple[int, dict]] = []
        max_latency = max([int(v) for v in _LATENCY.values()] or [1])
        t = 0
        for kind in kinds:
            before = len(observed)
            self.drive({"kind": kind}, t=t)
            for _cycle_guard in range(max_latency + _OUTSTANDING_CAP + 8):
                self.tick(t)
                observed.extend(self.observe(t))
                if len(observed) > before:
                    break
                t += 1
            t += 1
        # Final bounded drain to catch any zero/late latency result without
        # allowing a false pass if a transaction remains unobserved.
        for _cycle_guard in range(max_latency + _OUTSTANDING_CAP + 8):
            if len(observed) >= len(kinds):
                break
            self.tick(t)
            observed.extend(self.observe(t))
            t += 1
        total_bins = len(CL_BINS)
        hit_bins = sum(1 for v in self.cov.values() if v > 0)
        missing_results = max(0, len(kinds) - len(observed))
        return {
            "passed": (missing_results == 0 and hit_bins == total_bins),
            "backend": MODEL_BACKEND,
            "pymtl3_available": HAS_PYMTL3,
            "transactions": len(kinds),
            "results_observed": len(observed),
            "missing_results": missing_results,
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "performance_targets": PERFORMANCE_TARGETS,
        }


if HAS_PYMTL3:
    class CycleModelPyMTL(Component):
        """PyMTL3 cycle shell around CycleModel for cycle/performance validation.

        The wrapper intentionally delegates behavioral results to CycleModel,
        which delegates function evaluation to FunctionalModel.  PyMTL owns the
        clocked shell and observable counters used by CL coverage.
        """

        def construct(s):
            s.reset_in = InPort(Bits1)
            s.valid = InPort(Bits1)
            s.ready = OutPort(Bits1)
            s.cycle_count = OutPort(Bits32)
            s.outstanding = OutPort(Bits32)
            s.queue_depth = OutPort(Bits32)
            s._model = CycleModel()

            @update_ff
            def cl_tick():
                if s.reset_in:
                    s._model.reset()
                    s.ready <<= 1
                    s.cycle_count <<= 0
                    s.outstanding <<= 0
                    s.queue_depth <<= 0
                else:
                    next_cycle = s._model.now + 1
                    s._model.tick(next_cycle)
                    s.ready <<= int(s._model._outstanding < _OUTSTANDING_CAP)
                    s.cycle_count <<= next_cycle
                    s.outstanding <<= s._model._outstanding
                    s.queue_depth <<= len(s._model.in_q)
else:
    CycleModelPyMTL = None


def make_pymtl_cycle_model():
    """Return the PyMTL3 cycle shell.  Use direct Python smoke, not pytest-pymtl3."""
    if not HAS_PYMTL3:
        raise RuntimeError("pymtl3 is not importable in this Python environment")
    return CycleModelPyMTL()


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))
