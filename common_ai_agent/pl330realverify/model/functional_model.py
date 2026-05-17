#!/usr/bin/env python3
"""Executable SSOT functional model for pl330realverify.

Generated from yaml/pl330realverify.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'pl330realverify', 'parameters': {'DATA_WIDTH': 64, 'ADDR_WIDTH': 32, 'ID_WIDTH': 6, 'NUM_CHANNELS': 8, 'NUM_EVENTS': 32, 'REG_ADDR_WIDTH': 12, 'MAX_BURST_LEN': 16, 'CLOCK_FREQ_MHZ': 500, 'RESET_POLARITY': 'active_low', 'SUPPORT_UNALIGNED': 0}, 'top_module': {'name': 'pl330realverify', 'file': 'rtl/pl330realverify.sv', 'version': '1.0', 'type': 'dma', 'quality_profile': 'production', 'description': 'PL330/DMA-330-like DMA controller verification target with APB4 register access, AXI4 memory transfer channels, wait-for-peripheral events, interrupts, debug command, and fault reporting.', 'reference_spec': 'ARM PL330/DMA-330 behavior class; user-defined engineering verification subset', 'target': {'technology': 'generic', 'clock_freq_mhz': 500, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'rd_buf', 'type': 'register', 'depth': 1, 'width': 64, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'reset': 0, 'description': 'Single-beat read-data buffer between AXI R capture and AXI W payload generation.'}, {'name': 'channel_state_bank', 'type': 'register_file', 'depth': 8, 'width': 96, 'read_ports': 2, 'write_ports': 2, 'latency': 0, 'reset': 0, 'description': 'Abstract storage for per-channel SAR/DAR/count/status/error in the engineering model.'}], 'no_sram_macros': True, 'note': 'No SRAM macro or FIFO is required in the baseline single-outstanding subset; future burst/multichannel issue queues require SSOT update.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 12, 'byte_addressable': True, 'channel_stride': 64, 'channel_base': 256, 'num_channels': 8}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero, ignore writes, and do not allocate storage.'}, 'register_list': [{'name': 'DBGSTATUS', 'offset': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Global debug and reset-observable status.', 'fields': [{'name': 'manager_busy', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'Manager/control path is executing.'}, {'name': 'num_channels_minus1', 'bits': [7, 4], 'access': 'ro', 'reset': 7, 'description': 'NUM_CHANNELS minus one for software discovery.'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'DBGCMD', 'offset': 12, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'debug', 'description': 'Debug command launch register.', 'write_side_effects': ['A completing APB write with dbgcmd=0 emits one debug_execute pulse when the manager is not busy.'], 'fields': [{'name': 'dbgcmd', 'bits': [1, 0], 'access': 'wo', 'reset': 0, 'write_effect': '0=execute debug command pulse; other values are ignored in this subset', 'description': 'Debug command selector.'}, {'name': 'channel', 'bits': [6, 4], 'access': 'wo', 'reset': 0, 'write_effect': 'Select target channel for debug execution when implemented', 'description': 'Target channel index.'}, {'name': 'reserved_31_7', 'bits': [31, 7], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'INTEN', 'offset': 32, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt enable register.', 'write_side_effects': ['Software writes update interrupt enable bits immediately; enabling an already-pending source may assert dmac_irq on the next cycle.'], 'fields': [{'name': 'ch_complete_en', 'bits': [7, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable per-channel completion interrupt', 'description': 'Completion interrupt enables.'}, {'name': 'ch_fault_en', 'bits': [15, 8], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable per-channel fault interrupt', 'description': 'Fault interrupt enables.'}, {'name': 'dbg_done_en', 'bits': [16, 16], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable debug-done interrupt', 'description': 'Debug completion interrupt enable.'}, {'name': 'reserved_31_17', 'bits': [31, 17], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'INTSTATUS', 'offset': 36, 'width': 32, 'access': 'w1c', 'reset': 0, 'category': 'interrupt', 'description': 'Raw interrupt status register with write-one-to-clear behavior.', 'write_side_effects': ['Writing one clears the corresponding pending interrupt bit; writing zero preserves the bit.'], 'fields': [{'name': 'ch_complete', 'bits': [7, 0], 'access': 'w1c', 'reset': 0, 'write_effect': '1 clears matching channel-complete pending bit', 'description': 'Per-channel completion pending status.'}, {'name': 'ch_fault', 'bits': [15, 8], 'access': 'w1c', 'reset': 0, 'write_effect': '1 clears matching channel-fault pending bit', 'description': 'Per-channel fault pending status.'}, {'name': 'dbg_done', 'bits': [16, 16], 'access': 'w1c', 'reset': 0, 'write_effect': '1 clears debug-done pending bit', 'description': 'Debug command completion pending status.'}, {'name': 'reserved_31_17', 'bits': [31, 17], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'CSR', 'offset': 256, 'width': 32, 'access': 'ro', 'reset': 0, 'repeat': 8, 'stride': 64, 'category': 'channel', 'description': 'Per-channel status register.', 'fields': [{'name': 'ch_status', 'bits': [3, 0], 'access': 'ro', 'reset': 0, 'description': '0=STOPPED, 1=EXECUTING, 2=WAITING_FOR_PERIPHERAL, 6=COMPLETED, 8=FAULTED.'}, {'name': 'error_code', 'bits': [7, 4], 'access': 'ro', 'reset': 0, 'description': '0=no error, 1=debug reject, 2=unaligned, 3=AXI read error, 4=AXI write error, 5=event timeout.'}, {'name': 'loop_remaining', 'bits': [15, 8], 'access': 'ro', 'reset': 0, 'description': 'Remaining beats in the active transfer, saturated to eight status bits.'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'SAR', 'offset': 264, 'width': 32, 'access': 'rw', 'reset': 0, 'repeat': 8, 'stride': 64, 'category': 'channel', 'description': 'Per-channel source address register.', 'write_side_effects': ['Software writes update the source address only while the channel is STOPPED or COMPLETED.'], 'fields': [{'name': 'src_addr', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Update source byte address when channel is not EXECUTING or WAITING_FOR_PERIPHERAL', 'description': 'Source byte address.'}]}, {'name': 'DAR', 'offset': 268, 'width': 32, 'access': 'rw', 'reset': 0, 'repeat': 8, 'stride': 64, 'category': 'channel', 'description': 'Per-channel destination address register.', 'write_side_effects': ['Software writes update the destination address only while the channel is STOPPED or COMPLETED.'], 'fields': [{'name': 'dst_addr', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Update destination byte address when channel is not EXECUTING or WAITING_FOR_PERIPHERAL', 'description': 'Destination byte address.'}]}, {'name': 'LOOP_CFG', 'offset': 272, 'width': 32, 'access': 'rw', 'reset': 0, 'repeat': 8, 'stride': 64, 'category': 'channel', 'description': 'Per-channel transfer loop and burst configuration.', 'write_side_effects': ['Software writes update transfer count and burst shape while the channel is idle.'], 'fields': [{'name': 'loop_count', 'bits': [7, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Encoded transfer count: zero means one beat, N means N+1 beats', 'description': 'Transfer count encoding.'}, {'name': 'burst_len', 'bits': [11, 8], 'access': 'rw', 'reset': 0, 'write_effect': 'Encoded AXI burst length: zero means one beat, N means N+1 beats', 'description': 'AXI burst length encoding.'}, {'name': 'reserved_31_12', 'bits': [31, 12], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'CONTROL', 'offset': 276, 'width': 32, 'access': 'rw', 'reset': 0, 'repeat': 8, 'stride': 64, 'category': 'channel', 'description': 'Per-channel control and start register.', 'write_side_effects': ['Writing start=1 while channel is STOPPED or COMPLETED accepts a transfer command and self-clears start.', 'Writing halt=1 while EXECUTING requests a graceful transition to STOPPED after the active beat.', 'fault_inject forces the declared fault path for verification.'], 'fields': [{'name': 'start', 'bits': [0, 0], 'access': 'rw1p', 'reset': 0, 'write_effect': '1 launches a transfer command and the stored bit self-clears', 'description': 'Start pulse.'}, {'name': 'halt', 'bits': [1, 1], 'access': 'rw1p', 'reset': 0, 'write_effect': '1 requests graceful halt and the stored bit self-clears', 'description': 'Halt pulse.'}, {'name': 'wfp_enable', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable wait-for-peripheral gating before read issue', 'description': 'Wait-for-peripheral enable.'}, {'name': 'wfp_event', 'bits': [12, 8], 'access': 'rw', 'reset': 0, 'write_effect': 'Select peripheral_events index used by WFP', 'description': 'Peripheral event index.'}, {'name': 'fault_inject', 'bits': [16, 16], 'access': 'rw', 'reset': 0, 'write_effect': 'Force channel fault on accepted start for verification', 'description': 'Fault injection enable.'}, {'name': 'reserved_31_17', 'bits': [31, 17], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'PC', 'offset': 280, 'width': 32, 'access': 'rw', 'reset': 0, 'repeat': 8, 'stride': 64, 'category': 'channel', 'description': 'Instruction/program counter placeholder for PL330-like program-flow observability.', 'write_side_effects': ['Software writes update PC while the channel is STOPPED; this engineering subset does not fetch external microcode.'], 'fields': [{'name': 'pc_addr', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Update observable program counter when idle', 'description': 'Program-counter/debug address.'}]}]}, 'function_model': {'purpose': 'Executable cycle-independent behavioral contract for PL330-like DMA transfer, wait-for-peripheral, debug command, APB register side effects, interrupt clear, and fault behavior.', 'constants': {'STATUS_STOPPED': 0, 'STATUS_EXECUTING': 1, 'STATUS_WAITING_FOR_PERIPHERAL': 2, 'STATUS_COMPLETED': 6, 'STATUS_FAULTED': 8, 'RESP_OKAY': 0, 'ERR_NONE': 0, 'ERR_DEBUG_REJECT': 1, 'ERR_UNALIGNED': 2, 'ERR_AXI_RD': 3, 'ERR_AXI_WR': 4, 'ERR_EVENT_TIMEOUT': 5}, 'state_variables': [{'name': 'sar', 'source': 'registers.SAR.src_addr', 'reset': 0, 'width': 32, 'description': 'Current source byte address for the selected channel.'}, {'name': 'dar', 'source': 'registers.DAR.dst_addr', 'reset': 0, 'width': 32, 'description': 'Current destination byte address for the selected channel.'}, {'name': 'loop_remaining', 'source': 'registers.LOOP_CFG.loop_count', 'reset': 0, 'width': 8, 'description': 'Number of transfer beats remaining, where encoded loop_count N loads N+1 beats.'}, {'name': 'status', 'source': 'registers.CSR.ch_status', 'reset': 0, 'width': 4, 'description': 'Architectural channel status code.'}, {'name': 'error_code', 'source': 'registers.CSR.error_code', 'reset': 0, 'width': 4, 'description': 'Architectural channel error code.'}, {'name': 'rd_buf', 'source': 'memory.rd_buf', 'reset': 0, 'width': 64, 'description': 'Last accepted AXI read data beat.'}, {'name': 'intstatus', 'source': 'registers.INTSTATUS', 'reset': 0, 'width': 32, 'description': 'Raw interrupt pending bits.'}, {'name': 'inten', 'source': 'registers.INTEN', 'reset': 0, 'width': 32, 'description': 'Interrupt enable bits.'}, {'name': 'pc', 'source': 'registers.PC.pc_addr', 'reset': 0, 'width': 32, 'description': 'Observable PL330-like program/debug address; no external microcode fetch in this subset.'}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset_architecture', 'preconditions': ['dmacresetn == 0'], 'inputs': ['dmacresetn'], 'outputs': ['All externally visible output valids and interrupt are deasserted during reset.'], 'output_rules': [{'name': 'irq_reset', 'port': 'dmac_irq', 'width': 1, 'expr': '0'}, {'name': 'pready_reset', 'port': 'pready', 'width': 1, 'expr': '0'}, {'name': 'pslverr_reset', 'port': 'pslverr', 'width': 1, 'expr': '0'}], 'state_updates': [{'name': 'sar', 'width': 32, 'expr': '0'}, {'name': 'dar', 'width': 32, 'expr': '0'}, {'name': 'loop_remaining', 'width': 8, 'expr': '0'}, {'name': 'status', 'width': 4, 'expr': '0'}, {'name': 'error_code', 'width': 4, 'expr': '0'}, {'name': 'rd_buf', 'width': 64, 'expr': '0'}, {'name': 'intstatus', 'width': 32, 'expr': '0'}, {'name': 'inten', 'width': 32, 'expr': '0'}], 'side_effects': ['All architectural state returns to declared reset values.']}, {'id': 'FM_APB_WRITE', 'name': 'apb_register_write', 'preconditions': ['dmacresetn == 1', 'psel == 1 and penable == 1 and pwrite == 1 and pready == 1'], 'inputs': ['paddr', 'pwdata', 'pstrb'], 'outputs': ['pready acknowledges the access; pslverr reports illegal address/access/strobe.'], 'output_rules': [{'name': 'apb_write_ready', 'port': 'pready', 'width': 1, 'expr': '1'}, {'name': 'apb_write_error', 'port': 'pslverr', 'width': 1, 'expr': '1 if illegal_apb_access == 1 else 0'}], 'state_updates': [{'name': 'inten', 'width': 32, 'expr': '((inten & (~write_mask_32)) | (pwdata & write_mask_32)) if (apb_addr_inten == 1 and illegal_apb_access == 0) else inten'}, {'name': 'intstatus', 'width': 32, 'expr': '(intstatus & (~pwdata)) if (apb_addr_intstatus == 1 and illegal_apb_access == 0) else intstatus'}, {'name': 'sar', 'width': 32, 'expr': 'pwdata if (apb_addr_sar == 1 and channel_idle == 1 and illegal_apb_access == 0) else sar'}, {'name': 'dar', 'width': 32, 'expr': 'pwdata if (apb_addr_dar == 1 and channel_idle == 1 and illegal_apb_access == 0) else dar'}], 'side_effects': ['Writable register fields update only through declared write_effect rules; reserved fields ignore writes.'], 'error_cases': [{'id': 'ERR_APB_ILLEGAL', 'condition': 'illegal_apb_access == 1', 'result': 'pslverr asserted for the completing access; architectural DMA transfer state is not modified.'}]}, {'id': 'FM_APB_READ', 'name': 'apb_register_read', 'preconditions': ['dmacresetn == 1', 'psel == 1 and penable == 1 and pwrite == 0 and pready == 1'], 'inputs': ['paddr'], 'outputs': ['prdata returns the decoded register value with reserved bits forced to zero.'], 'output_rules': [{'name': 'apb_read_ready', 'port': 'pready', 'width': 1, 'expr': '1'}, {'name': 'apb_read_error', 'port': 'pslverr', 'width': 1, 'expr': '1 if illegal_apb_access == 1 else 0'}, {'name': 'apb_read_data', 'port': 'prdata', 'width': 32, 'expr': '0 if illegal_apb_access == 1 else (register_read_value & 0xFFFFFFFF)'}], 'state_updates': [{'name': 'status', 'width': 4, 'expr': 'status'}], 'side_effects': ['APB reads do not alter architectural state.']}, {'id': 'FM_TRANSFER', 'name': 'single_or_multi_beat_memory_copy', 'preconditions': ['dmacresetn == 1', 'start_cmd == 1', 'fault_inject == 0', '(sar % (DATA_WIDTH // 8)) == 0', '(dar % (DATA_WIDTH // 8)) == 0'], 'inputs': ['rdata', 'rresp', 'bresp', 'loop_count'], 'outputs': ['Each successful beat writes the captured read data to the destination address.', 'Final successful beat sets status COMPLETED and raises the channel-complete pending bit.'], 'output_rules': [{'name': 'write_payload', 'port': 'wdata', 'width': 64, 'expr': 'rd_buf'}, {'name': 'write_strobes', 'port': 'wstrb', 'width': 8, 'expr': '(1 << (DATA_WIDTH // 8)) - 1'}, {'name': 'irq_after_transfer', 'port': 'dmac_irq', 'width': 1, 'expr': '1 if ((intstatus | complete_irq_mask) & inten) != 0 else 0'}], 'state_updates': [{'name': 'rd_buf', 'width': 64, 'expr': 'rdata if (rvalid == 1 and rready == 1 and rresp == 0) else rd_buf'}, {'name': 'sar', 'width': 32, 'expr': 'sar + (DATA_WIDTH // 8)'}, {'name': 'dar', 'width': 32, 'expr': 'dar + (DATA_WIDTH // 8)'}, {'name': 'loop_remaining', 'width': 8, 'expr': 'max(loop_remaining - 1, 0)'}, {'name': 'status', 'width': 4, 'expr': '6 if loop_remaining <= 1 else 1'}, {'name': 'error_code', 'width': 4, 'expr': '0'}, {'name': 'intstatus', 'width': 32, 'expr': 'intstatus | complete_irq_mask if loop_remaining <= 1 else intstatus'}], 'side_effects': ['SAR and DAR increment by DATA_WIDTH/8 bytes after each successful write response.', 'loop_remaining decrements after each successful write response.'], 'error_cases': [{'id': 'ERR_AXI_RD', 'condition': 'rvalid == 1 and rready == 1 and rresp != 0', 'result': 'status=FAULTED, error_code=ERR_AXI_RD, CH_FAULT pending set, no write for the failed beat.'}, {'id': 'ERR_AXI_WR', 'condition': 'bvalid == 1 and bready == 1 and bresp != 0', 'result': 'status=FAULTED, error_code=ERR_AXI_WR, CH_FAULT pending set.'}]}, {'id': 'FM_WFP', 'name': 'wait_for_peripheral_event', 'preconditions': ['dmacresetn == 1', 'start_cmd == 1', 'wfp_enable == 1'], 'inputs': ['peripheral_events', 'wfp_event'], 'outputs': ['Channel remains WAITING_FOR_PERIPHERAL until the selected event bit is sampled high.'], 'output_rules': [{'name': 'irq_during_wfp', 'port': 'dmac_irq', 'width': 1, 'expr': '1 if (intstatus & inten) != 0 else 0'}], 'state_updates': [{'name': 'status', 'width': 4, 'expr': '1 if selected_event == 1 else 2'}, {'name': 'loop_remaining', 'width': 8, 'expr': 'loop_remaining'}], 'side_effects': ['No AXI transaction is issued while selected_event is zero.']}, {'id': 'FM_FAULT', 'name': 'fault_completion', 'preconditions': ['dmacresetn == 1', 'fault_condition == 1'], 'inputs': ['fault_condition', 'fault_code'], 'outputs': ['Fault status is latched and a channel-fault pending interrupt is set.'], 'output_rules': [{'name': 'irq_after_fault', 'port': 'dmac_irq', 'width': 1, 'expr': '1 if ((intstatus | fault_irq_mask) & inten) != 0 else 0'}], 'state_updates': [{'name': 'status', 'width': 4, 'expr': '8'}, {'name': 'error_code', 'width': 4, 'expr': 'fault_code'}, {'name': 'intstatus', 'width': 32, 'expr': 'intstatus | fault_irq_mask'}], 'side_effects': ['First fault wins until software clears INTSTATUS and restarts the channel.'], 'error_cases': [{'id': 'ERR_UNALIGNED', 'condition': 'addresses_aligned == 0', 'result': 'status=FAULTED and error_code=ERR_UNALIGNED.'}, {'id': 'ERR_DEBUG_REJECT', 'condition': 'debug_execute == 1 and manager_busy == 1', 'result': 'debug command rejected without transfer side effects.'}]}, {'id': 'FM_IRQ_CLEAR', 'name': 'interrupt_write_one_to_clear', 'preconditions': ['dmacresetn == 1', 'apb_addr_intstatus == 1', 'psel == 1 and penable == 1 and pwrite == 1 and pready == 1'], 'inputs': ['pwdata'], 'outputs': ['dmac_irq reflects the enabled pending status after the W1C clear.'], 'output_rules': [{'name': 'irq_after_w1c', 'port': 'dmac_irq', 'width': 1, 'expr': '1 if ((intstatus & (~pwdata)) & inten) != 0 else 0'}], 'state_updates': [{'name': 'intstatus', 'width': 32, 'expr': 'intstatus & (~pwdata)'}], 'side_effects': ['Only bits written as one are cleared; bits written as zero retain their prior value.']}], 'invariants': ['not (write_beat_done == 1 and read_buffer_valid == 0)', 'not (status == 6 and error_code != 0)', 'not (status == 8 and error_code == 0)', '(intstatus & (~0x1FFFF)) == 0', 'loop_remaining >= 0'], 'reference_model_hint': 'tb-gen should build a Python scoreboard from transactions, output_rules, state_updates, and invariants; prose outputs are explanatory only.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract defining when PL330-like architectural state, AXI/APB valid-ready signals, interrupt outputs, and error status may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 or direct Python cycle model as a timing oracle; FunctionalModel remains the behavioral oracle.', 'clock': 'dmaclk', 'reset': {'assertion': 'dmacresetn low asynchronously clears architectural state and deasserts valid/ready output valids and dmac_irq.', 'deassertion': 'State is usable on the first rising dmaclk edge after synchronized deassertion.'}, 'latency': {'register_read': {'min_cycles': 1, 'max_cycles': 1, 'description': 'pready/prdata/pslverr complete in APB access phase.'}, 'register_write': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Writable side effects occur on the completing APB access cycle.'}, 'event_release': {'min_cycles': 1, 'max_cycles': 2, 'description': 'Selected peripheral event sampled then WFP state can advance.'}, 'single_beat_transfer': {'min_cycles': 5, 'max_cycles': None, 'description': 'Command accept, AR, R, AW/W, and B stages; max is unbounded under AXI backpressure.'}, 'interrupt_assertion': {'min_cycles': 1, 'max_cycles': 2, 'description': 'Pending enabled interrupt reflects terminal status or W1C clear within two cycles.'}}, 'handshake_rules': [{'id': 'APB_ACCESS', 'signal': 'pready', 'rule': 'pready asserts only for psel==1 and penable==1 and completes exactly one APB transfer.', 'sample_condition': 'psel == 1 and penable == 1'}, {'id': 'APB_READ_DATA', 'signal': 'prdata', 'rule': 'prdata is stable for the completing read access and reserved bits read zero.', 'sample_condition': 'psel == 1 and penable == 1 and pwrite == 0 and pready == 1'}, {'id': 'AXI_AR', 'signal': 'arvalid', 'rule': 'Hold arvalid and AR payload stable until arvalid and arready are sampled high.', 'sample_condition': 'arvalid == 1 and arready == 1'}, {'id': 'AXI_R', 'signal': 'rready', 'rule': 'Assert rready only when rd_buf can accept rdata; capture exactly one beat on rvalid and rready.', 'sample_condition': 'rvalid == 1 and rready == 1'}, {'id': 'AXI_AW', 'signal': 'awvalid', 'rule': 'Hold awvalid and AW payload stable until awvalid and awready are sampled high.', 'sample_condition': 'awvalid == 1 and awready == 1'}, {'id': 'AXI_W', 'signal': 'wvalid', 'rule': 'Hold wvalid, wdata, wstrb, and wlast stable until wvalid and wready are sampled high.', 'sample_condition': 'wvalid == 1 and wready == 1'}, {'id': 'AXI_B', 'signal': 'bready', 'rule': 'Assert bready while waiting for write response; consume bresp on bvalid and bready.', 'sample_condition': 'bvalid == 1 and bready == 1'}, {'id': 'IRQ_LEVEL', 'signal': 'dmac_irq', 'rule': 'dmac_irq equals the OR-reduction of intstatus & inten after reset, terminal updates, and W1C clears settle.', 'sample_condition': 'dmacresetn == 1'}], 'pipeline': [{'stage': 'S0_APB_ACCEPT', 'cycle': 0, 'action': 'Decode APB access, update configuration or emit start/halt/debug pulses.'}, {'stage': 'S1_CMD_ACCEPT', 'cycle': 1, 'action': 'Latch channel command, SAR, DAR, count, WFP configuration, and error precheck results.'}, {'stage': 'S2_WFP', 'cycle': '1..N', 'action': 'If WFP is enabled, hold state until selected peripheral event samples high.'}, {'stage': 'S3_ISSUE_READ', 'cycle': 'N..M', 'action': 'Drive AXI AR payload and hold until AR handshake.'}, {'stage': 'S4_CAPTURE_READ', 'cycle': 'M..P', 'action': 'Accept AXI R beat, classify rresp, and capture rdata into rd_buf.'}, {'stage': 'S5_ISSUE_WRITE', 'cycle': 'P..Q', 'action': 'Drive AXI AW and W payloads; each channel may complete independently but both must handshake before B wait.'}, {'stage': 'S6_WRITE_RESP', 'cycle': 'Q..R', 'action': 'Consume AXI B response, update address/count/status/interrupts.'}, {'stage': 'S7_TERMINAL', 'cycle': 'R+1', 'action': 'Post COMPLETED or FAULTED status and level interrupt state.'}], 'ordering': ['A write data beat must not be issued before the corresponding read data beat has been accepted into rd_buf.', 'A channel-complete interrupt pending bit is set only after the final successful B response.', 'A channel-fault interrupt pending bit is set on the first detected fault before any later completion status.', 'APB W1C clear does not clear configuration registers or address counters.', 'For each channel, at most one read burst and one write burst are outstanding in this engineering subset.'], 'backpressure': ['If arready is zero, AR payload remains stable and no read transaction is counted.', 'If rvalid is zero, rd_buf and downstream write stage remain stable.', 'If awready or wready is zero, write payload/address/control remain stable until handshakes occur.', 'If bvalid is zero, architectural completion/fault for that write is delayed.', 'APB accesses are not backpressured in the baseline beyond the single access phase.'], 'performance': {'frequency_mhz': 500, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No APB command gap, WFP disabled or already satisfied, no AXI backpressure, no AXI errors, aligned addresses.'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'per_channel': True, 'description': 'Single outstanding read/write in the engineering subset.'}, 'depth': {'pipeline_stages': 8, 'queue_depth': 1, 'rd_buffer_depth': 1, 'description': 'Visible cycle-model pipeline and buffering depth.'}}, 'observability': ['Every function_model transaction maps to one or more cycle_model stages and at least one coverage bin.', 'Waveform debug must show state, start_cmd, selected_event, AXI handshakes, rd_buf, status, error_code, intstatus, inten, and dmac_irq.']}, 'fcov_bins': [{'id': 'SC_RESET_APB_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_RESET_APB', 'description': 'Reset and APB discovery'}, {'id': 'SC_SINGLE_BEAT_COPY_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_SINGLE_BEAT_COPY', 'description': 'Single-beat DMA memory copy'}, {'id': 'SC_MULTI_BEAT_COPY_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_MULTI_BEAT_COPY', 'description': 'Multi-beat address and loop progression'}, {'id': 'SC_AXI_BACKPRESSURE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_AXI_BACKPRESSURE', 'description': 'AXI ready/valid hold behavior under backpressure'}, {'id': 'SC_WFP_EVENT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_WFP_EVENT', 'description': 'Wait-for-peripheral event gating'}, {'id': 'SC_AXI_READ_FAULT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_AXI_READ_FAULT', 'description': 'AXI read fault propagation'}, {'id': 'SC_AXI_WRITE_FAULT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC_AXI_WRITE_FAULT', 'description': 'AXI write fault propagation'}, {'id': 'SC_W1C_IRQ_CLEAR_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC_W1C_IRQ_CLEAR', 'description': 'Interrupt enable and W1C clear'}, {'id': 'SC_DEBUG_COMMAND_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC_DEBUG_COMMAND', 'description': 'Debug command pulse and rejection'}, {'id': 'fcov_reset', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_RESET', 'source_ref': 'function_model.transactions.FM_RESET', 'description': 'Reset architectural behavior observed.'}, {'id': 'fcov_apb_read', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APB_READ', 'source_ref': 'function_model.transactions.FM_APB_READ', 'description': 'APB read transaction observed.'}, {'id': 'fcov_apb_write', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APB_WRITE', 'source_ref': 'function_model.transactions.FM_APB_WRITE', 'description': 'APB write and side effects observed.'}, {'id': 'fcov_transfer', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TRANSFER', 'source_ref': 'function_model.transactions.FM_TRANSFER', 'description': 'Legal DMA copy behavior observed.'}, {'id': 'fcov_wfp', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_WFP', 'source_ref': 'function_model.transactions.FM_WFP', 'description': 'Wait-for-peripheral behavior observed.'}, {'id': 'fcov_fault_rd', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD', 'source_ref': 'function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD', 'description': 'Read error behavior observed.'}, {'id': 'fcov_fault_wr', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_WR', 'source_ref': 'function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_WR', 'description': 'Write error behavior observed.'}, {'id': 'fcov_irq_clear', 'class': 'side_effect', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_IRQ_CLEAR', 'source_ref': 'function_model.transactions.FM_IRQ_CLEAR', 'description': 'Interrupt W1C clear behavior observed.'}, {'id': 'ccov_apb_access', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.APB_ACCESS', 'source_ref': 'cycle_model.handshake_rules.APB_ACCESS', 'description': 'APB completing access observed.'}, {'id': 'ccov_axi_ar_hold', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.AXI_AR', 'source_ref': 'cycle_model.handshake_rules.AXI_AR', 'description': 'AR hold-until-ready behavior observed.'}, {'id': 'ccov_axi_r_capture', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.AXI_R', 'source_ref': 'cycle_model.handshake_rules.AXI_R', 'description': 'R channel capture observed.'}, {'id': 'ccov_axi_aw_w', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.AXI_AW', 'source_ref': 'cycle_model.handshake_rules.AXI_AW', 'description': 'AW/W independent handshake behavior observed.'}, {'id': 'ccov_axi_b', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.AXI_B', 'source_ref': 'cycle_model.handshake_rules.AXI_B', 'description': 'B response consumption observed.'}, {'id': 'ccov_irq_level', 'class': 'interrupt', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.IRQ_LEVEL', 'source_ref': 'cycle_model.handshake_rules.IRQ_LEVEL', 'description': 'Level interrupt combine observed.'}, {'id': 'ccov_pipeline_all_stages', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'Each declared pipeline stage observed.'}, {'id': 'ccov_channel_fsm', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions', 'source_ref': 'fsm.channel_fsm.transitions', 'description': 'Declared legal channel FSM transitions observed.'}, {'id': 'ccov_performance_outstanding', 'class': 'outstanding', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': 'Single-outstanding limit exercised.'}, {'id': 'ccov_performance_depth', 'class': 'depth', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': 'Declared pipeline/buffer depth exercised.'}, {'id': 'ccov_performance_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': 'No-backpressure throughput condition exercised.'}, {'id': 'function_reset_architecture', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_reset', 'description': 'reset_architecture'}, {'id': 'function_apb_register_write', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_apb_write', 'description': 'apb_register_write'}, {'id': 'function_apb_register_read', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_apb_read', 'description': 'apb_register_read'}, {'id': 'function_single_or_multi_beat_memory_copy', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_transfer', 'description': 'single_or_multi_beat_memory_copy'}, {'id': 'function_wait_for_peripheral_event', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_wfp', 'description': 'wait_for_peripheral_event'}, {'id': 'function_fault_completion', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_fault', 'description': 'fault_completion'}, {'id': 'function_interrupt_write_one_to_clear', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm_irq_clear', 'description': 'interrupt_write_one_to_clear'}, {'id': 'cycle_apb_access', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'id': 'APB_ACCESS', 'signal': 'pready', 'rule': 'pready asserts only for psel==1 and penable==1 and completes exactly one APB transfer.', 'sample_condition': 'psel == 1 and penable == 1'}"}, {'id': 'cycle_apb_read_data', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'id': 'APB_READ_DATA', 'signal': 'prdata', 'rule': 'prdata is stable for the completing read access and reserved bits read zero.', 'sample_condition': 'psel == 1 and penable == 1 and pwrite == 0 and pready == 1'}"}, {'id': 'cycle_axi_ar', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'id': 'AXI_AR', 'signal': 'arvalid', 'rule': 'Hold arvalid and AR payload stable until arvalid and arready are sampled high.', 'sample_condition': 'arvalid == 1 and arready == 1'}"}, {'id': 'cycle_axi_r', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'id': 'AXI_R', 'signal': 'rready', 'rule': 'Assert rready only when rd_buf can accept rdata; capture exactly one beat on rvalid and rready.', 'sample_condition': 'rvalid == 1 and rready == 1'}"}, {'id': 'cycle_axi_aw', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[4]', 'source_ref': 'cycle_model.handshake_rules[4]', 'description': "{'id': 'AXI_AW', 'signal': 'awvalid', 'rule': 'Hold awvalid and AW payload stable until awvalid and awready are sampled high.', 'sample_condition': 'awvalid == 1 and awready == 1'}"}, {'id': 'cycle_axi_w', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[5]', 'source_ref': 'cycle_model.handshake_rules[5]', 'description': "{'id': 'AXI_W', 'signal': 'wvalid', 'rule': 'Hold wvalid, wdata, wstrb, and wlast stable until wvalid and wready are sampled high.', 'sample_condition': 'wvalid == 1 and wready == 1'}"}, {'id': 'cycle_axi_b', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[6]', 'source_ref': 'cycle_model.handshake_rules[6]', 'description': "{'id': 'AXI_B', 'signal': 'bready', 'rule': 'Assert bready while waiting for write response; consume bresp on bvalid and bready.', 'sample_condition': 'bvalid == 1 and bready == 1'}"}, {'id': 'cycle_irq_level', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[7]', 'source_ref': 'cycle_model.handshake_rules[7]', 'description': "{'id': 'IRQ_LEVEL', 'signal': 'dmac_irq', 'rule': 'dmac_irq equals the OR-reduction of intstatus & inten after reset, terminal updates, and W1C clears settle.', 'sample_condition': 'dmacresetn == 1'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'pready/prdata/pslverr complete in APB access phase.'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Writable side effects occur on the completing APB access cycle.'}"}, {'id': 'cycle_latency_event_release', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.event_release', 'source_ref': 'cycle_model.latency.event_release', 'description': "{'min_cycles': 1, 'max_cycles': 2, 'description': 'Selected peripheral event sampled then WFP state can advance.'}"}, {'id': 'cycle_latency_single_beat_transfer', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.single_beat_transfer', 'source_ref': 'cycle_model.latency.single_beat_transfer', 'description': "{'min_cycles': 5, 'max_cycles': None, 'description': 'Command accept, AR, R, AW/W, and B stages; max is unbounded under AXI backpressure.'}"}, {'id': 'cycle_latency_interrupt_assertion', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.interrupt_assertion', 'source_ref': 'cycle_model.latency.interrupt_assertion', 'description': "{'min_cycles': 1, 'max_cycles': 2, 'description': 'Pending enabled interrupt reflects terminal status or W1C clear within two cycles.'}"}, {'id': 'cycle_pipeline_s0_apb_accept', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Decode APB access, update configuration or emit start/halt/debug pulses.'}, {'id': 'cycle_pipeline_s1_cmd_accept', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Latch channel command, SAR, DAR, count, WFP configuration, and error precheck results.'}, {'id': 'cycle_pipeline_s2_wfp', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'If WFP is enabled, hold state until selected peripheral event samples high.'}, {'id': 'cycle_pipeline_s3_issue_read', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Drive AXI AR payload and hold until AR handshake.'}, {'id': 'cycle_pipeline_s4_capture_read', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Accept AXI R beat, classify rresp, and capture rdata into rd_buf.'}, {'id': 'cycle_pipeline_s5_issue_write', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[5]', 'source_ref': 'cycle_model.pipeline[5]', 'description': 'Drive AXI AW and W payloads; each channel may complete independently but both must handshake before B wait.'}, {'id': 'cycle_pipeline_s6_write_resp', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[6]', 'source_ref': 'cycle_model.pipeline[6]', 'description': 'Consume AXI B response, update address/count/status/interrupts.'}, {'id': 'cycle_pipeline_s7_terminal', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[7]', 'source_ref': 'cycle_model.pipeline[7]', 'description': 'Post COMPLETED or FAULTED status and level interrupt state.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'A write data beat must not be issued before the corresponding read data beat has been accepted into rd_buf.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'A channel-complete interrupt pending bit is set only after the final successful B response.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'A channel-fault interrupt pending bit is set on the first detected fault before any later completion status.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'APB W1C clear does not clear configuration registers or address counters.'}, {'id': 'cycle_ordering_4', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[4]', 'source_ref': 'cycle_model.ordering[4]', 'description': 'For each channel, at most one read burst and one write burst are outstanding in this engineering subset.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'If arready is zero, AR payload remains stable and no read transaction is counted.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'If rvalid is zero, rd_buf and downstream write stage remain stable.'}, {'id': 'cycle_backpressure_2', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[2]', 'source_ref': 'cycle_model.backpressure[2]', 'description': 'If awready or wready is zero, write payload/address/control remain stable until handshakes occur.'}, {'id': 'cycle_backpressure_3', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[3]', 'source_ref': 'cycle_model.backpressure[3]', 'description': 'If bvalid is zero, architectural completion/fault for that write is delayed.'}, {'id': 'cycle_backpressure_4', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[4]', 'source_ref': 'cycle_model.backpressure[4]', 'description': 'APB accesses are not backpressured in the baseline beyond the single access phase.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 1, 'write_max': 1, 'per_channel': True, 'description': 'Single outstanding read/write in the engineering subset.'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 8, 'queue_depth': 1, 'rd_buffer_depth': 1, 'description': 'Visible cycle-model pipeline and buffering depth.'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '500'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_beats_per_cycle': 1, 'condition': 'No APB command gap, WFP disabled or already satisfied, no AXI backpressure, no AXI errors, aligned addresses.'}"}, {'id': 'fsm_channel_fsm_stopped_to_executing_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[0]', 'source_ref': 'fsm.channel_fsm.transitions[0]', 'description': 'start_cmd == 1 and fault_inject == 0 and addresses_aligned == 1'}, {'id': 'fsm_channel_fsm_stopped_to_fault_completing_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[1]', 'source_ref': 'fsm.channel_fsm.transitions[1]', 'description': 'start_cmd == 1 and (fault_inject == 1 or addresses_aligned == 0)'}, {'id': 'fsm_channel_fsm_executing_to_waiting_for_peripheral_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[2]', 'source_ref': 'fsm.channel_fsm.transitions[2]', 'description': 'wfp_enable == 1 and selected_event == 0'}, {'id': 'fsm_channel_fsm_waiting_for_peripheral_to_issue_read_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[3]', 'source_ref': 'fsm.channel_fsm.transitions[3]', 'description': 'selected_event == 1'}, {'id': 'fsm_channel_fsm_executing_to_issue_read_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[4]', 'source_ref': 'fsm.channel_fsm.transitions[4]', 'description': 'wfp_enable == 0 or selected_event == 1'}, {'id': 'fsm_channel_fsm_issue_read_to_wait_read_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[5]', 'source_ref': 'fsm.channel_fsm.transitions[5]', 'description': 'arvalid == 1 and arready == 1'}, {'id': 'fsm_channel_fsm_wait_read_to_issue_write_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[6]', 'source_ref': 'fsm.channel_fsm.transitions[6]', 'description': 'rvalid == 1 and rready == 1 and rresp == 0'}, {'id': 'fsm_channel_fsm_wait_read_to_fault_completing_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[7]', 'source_ref': 'fsm.channel_fsm.transitions[7]', 'description': 'rvalid == 1 and rready == 1 and rresp != 0'}, {'id': 'fsm_channel_fsm_issue_write_to_wait_write_resp_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[8]', 'source_ref': 'fsm.channel_fsm.transitions[8]', 'description': 'aw_handshake == 1 and w_handshake == 1'}, {'id': 'fsm_channel_fsm_wait_write_resp_to_completing_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[9]', 'source_ref': 'fsm.channel_fsm.transitions[9]', 'description': 'bvalid == 1 and bready == 1 and bresp == 0 and loop_remaining == 1'}, {'id': 'fsm_channel_fsm_wait_write_resp_to_issue_read_10', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[10]', 'source_ref': 'fsm.channel_fsm.transitions[10]', 'description': 'bvalid == 1 and bready == 1 and bresp == 0 and loop_remaining > 1'}, {'id': 'fsm_channel_fsm_wait_write_resp_to_fault_completing_11', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[11]', 'source_ref': 'fsm.channel_fsm.transitions[11]', 'description': 'bvalid == 1 and bready == 1 and bresp != 0'}, {'id': 'fsm_channel_fsm_completing_to_completed_12', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[12]', 'source_ref': 'fsm.channel_fsm.transitions[12]', 'description': 'complete_status_posted == 1'}, {'id': 'fsm_channel_fsm_fault_completing_to_faulted_13', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[13]', 'source_ref': 'fsm.channel_fsm.transitions[13]', 'description': 'fault_status_posted == 1'}, {'id': 'fsm_channel_fsm_completed_to_stopped_14', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[14]', 'source_ref': 'fsm.channel_fsm.transitions[14]', 'description': 'start_cmd == 0 and halt_cmd == 0'}, {'id': 'fsm_channel_fsm_faulted_to_stopped_15', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.channel_fsm.transitions[15]', 'source_ref': 'fsm.channel_fsm.transitions[15]', 'description': 'fault_clear == 1'}, {'id': 'fsm_register_fsm_apb_idle_to_apb_setup_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.register_fsm.transitions[0]', 'source_ref': 'fsm.register_fsm.transitions[0]', 'description': 'psel == 1 and penable == 0'}, {'id': 'fsm_register_fsm_apb_setup_to_apb_access_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.register_fsm.transitions[1]', 'source_ref': 'fsm.register_fsm.transitions[1]', 'description': 'psel == 1 and penable == 1'}, {'id': 'fsm_register_fsm_apb_access_to_apb_idle_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.register_fsm.transitions[2]', 'source_ref': 'fsm.register_fsm.transitions[2]', 'description': 'pready == 1'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_DEBUG_REJECT', 'condition': 'debug_execute == 1 and manager_busy == 1', 'architectural_effect': 'error_code=1, debug command rejected, DBG_DONE pending set when INTEN.dbg_done_en is enabled'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_UNALIGNED', 'condition': '((sar % (DATA_WIDTH // 8)) != 0 or (dar % (DATA_WIDTH // 8)) != 0) and SUPPORT_UNALIGNED == 0', 'architectural_effect': 'status=FAULTED, error_code=2, CH_FAULT pending set, no AXI issue'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'ERR_AXI_RD', 'condition': 'rvalid == 1 and rready == 1 and rresp != 0', 'architectural_effect': 'status=FAULTED, error_code=3, CH_FAULT pending set, no destination write for failed beat'}"}, {'id': 'error_error_3', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'id': 'ERR_AXI_WR', 'condition': 'bvalid == 1 and bready == 1 and bresp != 0', 'architectural_effect': 'status=FAULTED, error_code=4, CH_FAULT pending set, completion suppressed'}"}, {'id': 'error_error_4', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[4]', 'source_ref': 'error_handling.error_sources[4]', 'description': "{'id': 'ERR_EVENT_TIMEOUT', 'condition': 'event_timeout_enabled == 1 and event_wait_counter_expired == 1', 'architectural_effect': 'status=FAULTED, error_code=5, CH_FAULT pending set'}"}, {'id': 'error_error_5', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[5]', 'source_ref': 'error_handling.error_sources[5]', 'description': "{'id': 'ERR_APB_ILLEGAL', 'condition': 'psel == 1 and penable == 1 and illegal_apb_access == 1', 'architectural_effect': 'pslverr=1 for that access; DMA channel architectural state unchanged'}"}]}
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
