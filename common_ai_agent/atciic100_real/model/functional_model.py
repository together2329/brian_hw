#!/usr/bin/env python3
"""Executable SSOT functional model for atciic100_real.

Generated from yaml/atciic100_real.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'atciic100_real', 'parameters': {'DATA_WIDTH': 8, 'FIFO_DEPTH': 8, 'INDEX_WIDTH': 3, 'TP_AUTOACK': 1, 'CLOCK_FREQ_MHZ': 40, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'atciic100_real', 'version': '1.0', 'type': 'peripheral', 'description': 'I2C Master/Slave Controller with APB interface, DMA, and glitch suppression.', 'reference_spec': 'Andes ATCIIC100 Data Sheet DS091_V1.3', 'target': {'technology': 'generic', 'clock_freq_mhz': 40, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'tx_rx_fifo', 'type': 'fifo', 'depth': 'FIFO_DEPTH', 'width': 8, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'Bidirectional Data FIFO'}]}, 'registers': {'config': {'register_width': 32, 'addr_width': 6, 'byte_addressable': True}, 'register_list': [{'name': 'ID', 'offset': 0, 'width': 32, 'access': 'ro', 'reset': 514, 'category': 'info', 'description': 'Device ID', 'fields': [{'name': 'ID', 'bits': [15, 0], 'access': 'ro', 'reset': 514, 'description': '0x0202'}]}, {'name': 'REV', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 4098, 'category': 'info', 'description': 'Revision ID', 'fields': [{'name': 'MAJOR', 'bits': [31, 20], 'access': 'ro', 'reset': 256, 'description': 'Major Rev'}, {'name': 'MINOR', 'bits': [19, 16], 'access': 'ro', 'reset': 2, 'description': 'Minor Rev'}]}, {'name': 'CFG', 'offset': 8, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'info', 'description': 'Hardware Config', 'fields': [{'name': 'FIFO_DEPTH', 'bits': [3, 0], 'access': 'ro', 'reset': 8, 'description': 'Log2(FIFO Depth)'}]}, {'name': 'INT_EN', 'offset': 12, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt Enable', 'fields': [{'name': 'EN', 'bits': [15, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable bits matching INT_ST'}]}, {'name': 'INT_ST', 'offset': 16, 'width': 32, 'access': 'rw1c', 'reset': 1, 'category': 'status', 'description': 'Interrupt Status', 'fields': [{'name': 'FIFOEmpty', 'bits': [0, 0], 'access': 'ro', 'reset': 1, 'description': 'FIFO Empty'}, {'name': 'FIFOFull', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': 'FIFO Full'}, {'name': 'FIFOHalf', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': 'FIFO Half'}, {'name': 'AddrHit', 'bits': [3, 3], 'access': 'rw1c', 'reset': 0, 'description': 'Address Hit'}, {'name': 'ArbLose', 'bits': [4, 4], 'access': 'rw1c', 'reset': 0, 'description': 'Arbitration Lost'}, {'name': 'Stop', 'bits': [5, 5], 'access': 'rw1c', 'reset': 0, 'description': 'Stop Detected'}, {'name': 'Start', 'bits': [6, 6], 'access': 'rw1c', 'reset': 0, 'description': 'Start Detected'}, {'name': 'ByteTrans', 'bits': [7, 7], 'access': 'rw1c', 'reset': 0, 'description': 'Byte Transmitted'}, {'name': 'ByteRecv', 'bits': [8, 8], 'access': 'rw1c', 'reset': 0, 'description': 'Byte Received'}, {'name': 'Cmpl', 'bits': [9, 9], 'access': 'rw1c', 'reset': 0, 'description': 'Completion'}, {'name': 'ACK', 'bits': [10, 10], 'access': 'ro', 'reset': 0, 'description': 'Last ACK Value'}, {'name': 'BusBusy', 'bits': [11, 11], 'access': 'ro', 'reset': 0, 'description': 'Bus Busy'}, {'name': 'GenCall', 'bits': [12, 12], 'access': 'ro', 'reset': 0, 'description': 'General Call'}, {'name': 'LineSCL', 'bits': [13, 13], 'access': 'ro', 'reset': 0, 'description': 'SCL Line State'}, {'name': 'LineSDA', 'bits': [14, 14], 'access': 'ro', 'reset': 0, 'description': 'SDA Line State'}]}, {'name': 'ADDR', 'offset': 20, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'I2C Address', 'fields': [{'name': 'Addr', 'bits': [9, 0], 'access': 'rw', 'reset': 0, 'description': 'Target/Self Address'}]}, {'name': 'DATA', 'offset': 24, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'data', 'description': 'Data FIFO Port', 'fields': [{'name': 'Data', 'bits': [7, 0], 'access': 'rw', 'reset': 0, 'description': 'FIFO Write/Read'}]}, {'name': 'CMD', 'offset': 28, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Command Register', 'fields': [{'name': 'CMD', 'bits': [2, 0], 'access': 'rw', 'reset': 0, 'description': '0=None, 1=Issue TX, 2=ACK, 3=NACK, 4=Clear FIFO, 5=Reset'}]}, {'name': 'CTRL', 'offset': 32, 'width': 32, 'access': 'rw', 'reset': 7936, 'category': 'control', 'description': 'Control Register', 'fields': [{'name': 'DataCnt', 'bits': [7, 0], 'access': 'rw', 'reset': 0, 'description': 'Data Byte Count (0=256)'}, {'name': 'Dir', 'bits': [8, 8], 'access': 'rw', 'reset': 0, 'description': 'Direction (0=TX, 1=RX)'}, {'name': 'Phase_stop', 'bits': [9, 9], 'access': 'rw', 'reset': 1, 'description': 'Enable Stop Phase'}, {'name': 'Phase_data', 'bits': [10, 10], 'access': 'rw', 'reset': 1, 'description': 'Enable Data Phase'}, {'name': 'Phase_addr', 'bits': [11, 11], 'access': 'rw', 'reset': 1, 'description': 'Enable Address Phase'}, {'name': 'Phase_start', 'bits': [12, 12], 'access': 'rw', 'reset': 1, 'description': 'Enable Start Phase'}]}, {'name': 'SETUP', 'offset': 36, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Setup Register', 'fields': [{'name': 'IICEn', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable Controller'}, {'name': 'Addressing', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': '0=7-bit, 1=10-bit'}, {'name': 'Master', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': '0=Slave, 1=Master'}, {'name': 'DMAEn', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Enable DMA'}, {'name': 'T_SCLHi', 'bits': [12, 4], 'access': 'rw', 'reset': 16, 'description': 'SCL High Count'}, {'name': 'T_SCLRatio', 'bits': [13, 13], 'access': 'rw', 'reset': 1, 'description': 'SCL Ratio'}, {'name': 'T_HDDAT', 'bits': [20, 16], 'access': 'rw', 'reset': 5, 'description': 'Hold Delay'}, {'name': 'T_SP', 'bits': [23, 21], 'access': 'rw', 'reset': 1, 'description': 'Spike Suppression'}, {'name': 'T_SUDAT', 'bits': [28, 24], 'access': 'rw', 'reset': 5, 'description': 'Setup Delay'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for atciic100_real.', 'state_variables': [{'name': 'cmd', 'source': 'registers.CMD', 'reset': 0, 'description': 'Current command'}, {'name': 'cfg', 'source': 'registers.CFG', 'reset': 0, 'description': 'Global config'}, {'name': 'int_en', 'source': 'registers.INT_EN', 'reset': 0, 'description': 'Interrupt enables'}, {'name': 'int_st', 'source': 'registers.INT_ST', 'reset': 1, 'description': 'Interrupt status (FIFOEmpty=1)'}, {'name': 'setup', 'source': 'registers.SETUP', 'reset': 0, 'description': 'Timing/Setup config'}, {'name': 'addr', 'source': 'registers.ADDR', 'reset': 0, 'description': 'Target/Own address'}, {'name': 'ctrl', 'source': 'registers.CTRL', 'reset': 7936, 'description': 'Phase/Direction/Count'}, {'name': 'phase', 'source': 'fsm.iic_phase', 'reset': 'IDLE', 'description': 'Current FSM phase'}, {'name': 'fifo_count', 'source': 'memory.instances[0].count', 'reset': 0, 'description': 'Current FIFO depth'}, {'name': 'master', 'source': 'setup.Master', 'reset': 0, 'description': 'Master/Slave mode flag'}, {'name': 'trans', 'source': 'ctrl.Dir', 'reset': 0, 'description': 'Transmitter/Receiver flag'}, {'name': 'arb_lost', 'source': 'int_st.ArbLose', 'reset': 0, 'description': 'Arbitration lost flag'}, {'name': 'datacnt', 'source': 'ctrl.DataCnt', 'reset': 0, 'description': 'Remaining byte count'}], 'transactions': [{'id': 'FM1', 'name': 'reset', 'preconditions': ['presetn == 0'], 'inputs': [], 'outputs': ['All registers reset to default', 'FIFO cleared', 'FSM=IDLE'], 'side_effects': ['i2c_int goes low', 'Bus lines released (open drain)'], 'error_cases': []}, {'id': 'FM2', 'name': 'csr_read', 'preconditions': ['psel==1 && penable==1 && pwrite==0'], 'inputs': ['paddr'], 'outputs': ['prdata = RegisterFile[paddr]'], 'side_effects': ['APB read completes in 2 cycles (setup then access phase)', 'INT_ST read does not clear W1C bits (only write-1 clears)'], 'error_cases': []}, {'id': 'FM3', 'name': 'csr_write', 'preconditions': ['psel==1 && penable==1 && pwrite==1'], 'inputs': ['paddr', 'pwdata'], 'outputs': ['RegisterFile[paddr] updated'], 'side_effects': ['CMD triggers action if valid', 'SETUP updates timing'], 'error_cases': []}, {'id': 'FM4', 'name': 'master_send', 'preconditions': ['master==1', 'trans==0', 'cmd==1', 'fifo_count > 0'], 'inputs': ['addr', 'data'], 'outputs': ['SCL/SDA signals driven for Start->Addr->Data->Stop', 'Target slave ACK/NACK'], 'side_effects': ['datacnt decrements', 'ByteTrans interrupt', 'Cmpl interrupt'], 'error_cases': [{'condition': 'No ACK from slave', 'result': 'int_st.ACK = 0, check NACK'}, {'condition': 'Arbitration Lost', 'result': 'arb_lost=1, STOP driving bus'}]}, {'id': 'FM5', 'name': 'master_recv', 'preconditions': ['master==1', 'trans==1', 'cmd==1'], 'inputs': ['addr'], 'outputs': ['SCL/SDA signals driven for Start->Addr->Data->Stop', 'Data pushed to FIFO'], 'side_effects': ['datacnt decrements', 'ByteRecv interrupt', 'FIFO status updates'], 'error_cases': [{'condition': 'Slave NACK on address', 'result': 'Transaction aborted, Stop sent, ACK status updated'}]}, {'id': 'FM6', 'name': 'slave_send', 'preconditions': ['master==0', 'trans==1', 'addr matched'], 'inputs': ['bus_clk', 'bus_data'], 'outputs': ['Data from FIFO shifted out'], 'side_effects': ['ByteTrans interrupt'], 'error_cases': [{'condition': 'FIFO Empty', 'result': 'Clock Stretching'}]}, {'id': 'FM7', 'name': 'slave_recv', 'preconditions': ['master==0', 'trans==0', 'addr matched'], 'inputs': ['bus_clk', 'bus_data'], 'outputs': ['Data pushed to FIFO'], 'side_effects': ['ByteRecv interrupt'], 'error_cases': [{'condition': 'FIFO Full', 'result': 'Clock Stretching or Overrun'}]}, {'id': 'FM8', 'name': 'general_call', 'preconditions': ['master==0', 'Address byte == 0x00'], 'inputs': ['bus_clk', 'bus_data'], 'outputs': ['ACK response', 'int_st.GenCall = 1'], 'side_effects': ['AddrHit interrupt'], 'error_cases': [{'condition': 'Controller disabled (IICEn=0)', 'result': 'No ACK, general call ignored'}]}, {'id': 'FM9', 'name': 'dma_request', 'preconditions': ['setup.DMAEn == 1', '(trans==1 && fifo_count > 0) || (trans==0 && fifo_count < FIFO_DEPTH)'], 'inputs': ['DMA Enable'], 'outputs': ['i2c_req = 1'], 'side_effects': ['DMA transfers data between FIFO and memory via external DMA controller'], 'error_cases': [{'condition': 'DMA acknowledge timeout', 'result': 'FIFO overrun or underrun may occur; DMA disabled until re-enabled'}]}], 'invariants': ['FIFO count never exceeds FIFO_DEPTH parameter.', 'Phase transitions follow IDLE->START->ADDR->DAT->STOP strictly, unless ArbLose occurs.', 'Arbitration Lost (ArbLose) terminates transmission immediately and releases bus.', 'i2c_int is asserted if and only if (int_st & int_en) != 0.', 'No destination write occurs before the corresponding source read completes in any transaction.', 'SCL/SDA outputs are open-drain: driven low or released high, never actively driven high.']}, 'cycle_model': {'purpose': 'Cycle/handshake contract for atciic100_real.', 'clock': 'pclk', 'reset': {'assertion': 'presetn low clears state', 'deassertion': 'State usable on next edge'}, 'latency': {'register_access': {'min_cycles': 2, 'max_cycles': 2, 'description': 'Setup/Access phases'}, 'i2c_byte': {'min_cycles': 9, 'max_cycles': None, 'description': '8 data bits + 1 ACK, scaled by T_SCLHi'}}, 'handshake_rules': [{'signal': 'psel/penable', 'rule': 'APB protocol requires setup then access phase.'}, {'signal': 'scl_o/sda_o', 'rule': 'Open drain; drive low or float high.'}, {'signal': 'i2c_req', 'rule': 'Hold high until i2c_ack received.'}, {'signal': 'scl_i filtering', 'rule': 'Ignore pulses < T_SP * t_pclk.'}, {'signal': 'scl_i/sda_i', 'rule': 'Sample filtered SCL/SDA on rising pclk edge after glitch filter latency.'}], 'pipeline': [{'stage': 'IDLE', 'cycle': 0, 'action': 'Wait for CMD or Address Match'}, {'stage': 'START', 'cycle': 1, 'action': 'Generate Start Condition (SDA H->L while SCL High)'}, {'stage': 'ADDR', 'cycle': '2..9', 'action': 'Shift out/in Address + R/W bit'}, {'stage': 'DAT', 'cycle': '10..N', 'action': 'Shift Data Bytes'}, {'stage': 'STOP', 'cycle': 'N+1', 'action': 'Generate Stop Condition (SDA L->H while SCL High)'}], 'ordering': ['Start must precede Addr.', 'Addr must precede Data.', 'Stop must follow Data or ArbLose.', 'A write response for beat i must complete before architectural completion of beat i.', 'Interrupt status updates occur on the same rising edge as the terminal status transition.'], 'arbitration': ['Sample SDA_I on SCL rising edge. If SDA_I=0 but SDA_O=1, ArbLose.'], 'backpressure': ['FIFO Full holds SCL Low (Clock Stretching).', 'FIFO Empty in slave TX holds SCL Low until data available.'], 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Reset'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'APB Read'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'APB Write'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Master TX'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'Master RX'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'Slave TX'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'Slave RX'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'Gen Call'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'Arb Lose'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'FIFO Full'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'DMA Flow'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'Glitch'}, {'id': 'function_reset', 'class': 'transaction_type', 'source': 'function_model.transactions[0]', 'description': 'reset'}, {'id': 'function_csr_read', 'class': 'transaction_type', 'source': 'function_model.transactions[1]', 'description': 'csr_read'}, {'id': 'function_csr_write', 'class': 'transaction_type', 'source': 'function_model.transactions[2]', 'description': 'csr_write'}, {'id': 'function_master_send', 'class': 'transaction_type', 'source': 'function_model.transactions[3]', 'description': 'master_send'}, {'id': 'function_master_recv', 'class': 'transaction_type', 'source': 'function_model.transactions[4]', 'description': 'master_recv'}, {'id': 'function_slave_send', 'class': 'transaction_type', 'source': 'function_model.transactions[5]', 'description': 'slave_send'}, {'id': 'function_slave_recv', 'class': 'transaction_type', 'source': 'function_model.transactions[6]', 'description': 'slave_recv'}, {'id': 'function_general_call', 'class': 'transaction_type', 'source': 'function_model.transactions[7]', 'description': 'general_call'}, {'id': 'function_dma_request', 'class': 'transaction_type', 'source': 'function_model.transactions[8]', 'description': 'dma_request'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'psel/penable', 'rule': 'APB protocol requires setup then access phase.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'scl_o/sda_o', 'rule': 'Open drain; drive low or float high.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'i2c_req', 'rule': 'Hold high until i2c_ack received.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'scl_i filtering', 'rule': 'Ignore pulses < T_SP * t_pclk.'}"}, {'id': 'cycle_handshake_4', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[4]', 'description': "{'signal': 'scl_i/sda_i', 'rule': 'Sample filtered SCL/SDA on rising pclk edge after glitch filter latency.'}"}, {'id': 'fsm_iic_phase_idle_to_start_0', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[0]', 'description': 'cmd==1 && master==1 && Phase_start'}, {'id': 'fsm_iic_phase_idle_to_addr_1', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[1]', 'description': 'cmd==1 && master==1 && !Phase_start && Phase_addr'}, {'id': 'fsm_iic_phase_idle_to_dat_2', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[2]', 'description': 'cmd==1 && master==1 && !Phase_start && !Phase_addr && Phase_data'}, {'id': 'fsm_iic_phase_start_to_addr_3', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[3]', 'description': 'Start sent'}, {'id': 'fsm_iic_phase_addr_to_dat_4', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[4]', 'description': 'Addr sent and ACK received'}, {'id': 'fsm_iic_phase_addr_to_stop_5', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[5]', 'description': 'Addr sent and NACK received'}, {'id': 'fsm_iic_phase_addr_to_arblost_6', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[6]', 'description': 'Arbitration Lost'}, {'id': 'fsm_iic_phase_dat_to_stop_7', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[7]', 'description': 'DataCnt==0'}, {'id': 'fsm_iic_phase_dat_to_dat_8', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[8]', 'description': 'DataCnt>0'}, {'id': 'fsm_iic_phase_dat_to_arblost_9', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[9]', 'description': 'Arbitration Lost'}, {'id': 'fsm_iic_phase_stop_to_idle_10', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[10]', 'description': 'Stop sent'}, {'id': 'fsm_iic_phase_arblost_to_idle_11', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[11]', 'description': 'Immediate'}, {'id': 'error_error_0', 'class': 'error', 'source': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_ACK', 'source': 'Slave NACK', 'effect': 'Transaction stops'}"}, {'id': 'error_error_1', 'class': 'error', 'source': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_ARB', 'source': 'Multi-Master Collision', 'effect': 'ArbLost Status'}"}, {'id': 'error_error_2', 'class': 'error', 'source': 'error_handling.error_sources[2]', 'description': "{'id': 'ERR_FIFO', 'source': 'Overrun/Underrun', 'effect': 'Data Loss/Clocking Stretching'}"}, {'id': 'error_error_3', 'class': 'error', 'source': 'error_handling.error_sources[3]', 'description': "{'id': 'ERR_DMA_TIMEOUT', 'source': 'DMA acknowledge not received', 'effect': 'FIFO overrun or underrun'}"}, {'id': 'error_error_4', 'class': 'error', 'source': 'error_handling.error_sources[4]', 'description': "{'id': 'ERR_GLITCH_INJECT', 'source': 'Injected glitch on SCL/SDA', 'effect': 'Filtered by GSF if within T_SP'}"}]}
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
