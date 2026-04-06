# TDISP RTL — PCIe TDISP (Tee Device Interface Security Protocol) Controller

## Overview

This repository implements a synthesizable RTL controller for the **PCIe TDISP** protocol
(Tee Device Interface Security Protocol), conforming to the PCI-SIG TDISP specification.
TDISP provides hardware-rooted security for PCIe devices participating in Confidential
Computing architectures (TDX, SEV-SNP, CCA).

The controller manages per-TDI (Tee Device Interface) state machines, DOE mailbox
message handling, TLP access control, IDE session validation, P2P stream binding,
and MMIO attribute management.

## Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │                    tdisp_top                         │
                    │                                                     │
  DOE RX ──────────►│  ┌──────────────┐   ┌─────────┐   ┌──────────────┐ │
  (AXI-Stream)      │  │ tdisp_transport│──►│tdisp_msg│──►│  tdisp_fsm   │ │
                    │  │              │   │ parser  │   │  (per-TDI)   │ │
  DOE TX ◄──────────│  │  Framing /   │◄──│         │◄──│              │ │
  (AXI-Stream)      │  │  Error Detect│   │tdisp_msg│   │  State:      │ │
                    │  └──────────────┘   │formatter│   │  UNLOCKED →  │ │
                    │                     └─────────┘   │  LOCKED →    │ │
  TLP Req ─────────►│  ┌──────────────┐                 │  RUN →       │ │
                    │  │ tdisp_tlp_   │                 │  ERROR       │ │
  TLP Allow ◄───────│  │ rules        │◄────────────────│              │ │
  TLP Block ◄───────│  │ (Access Ctrl)│   ┌──────────┐ └──────────────┘ │
                    │  └──────────────┘   │tdisp_lock│                   │
  Dev Config ──────►│  ┌──────────────┐   │  ctrl    │                   │
  (IDE, BAR, ...)   │  │ tdisp_tdi_   │◄──│          │                   │
                    │  │ mgr          │   └──────────┘                   │
                    │  │ (Context)    │                                   │
                    │  └──────────────┘   ┌──────────────┐               │
                    │                     │ tdisp_nonce_ │               │
                    │                     │ gen          │               │
                    │                     └──────────────┘               │
                    └─────────────────────────────────────────────────────┘
```

## Module Hierarchy

| Module              | File                         | Description                                        |
|---------------------|------------------------------|----------------------------------------------------|
| `tdisp_top`         | `rtl/tdisp_top.sv`           | Top-level integration, wires all submodules        |
| `tdisp_types`       | `rtl/tdisp_types.sv`         | Package: enums, structs, constants                 |
| `tdisp_transport`   | `rtl/tdisp_transport.sv`     | DOE framing, version detect, error/CRC checking    |
| `tdisp_msg_parser`  | `rtl/tdisp_msg_parser.sv`    | AXI-Stream → parsed TDISP message fields           |
| `tdisp_msg_formatter` | `rtl/tdisp_msg_formatter.sv` | Response message assembly → AXI-Stream            |
| `tdisp_fsm`         | `rtl/tdisp_fsm.sv`           | Per-TDI state machine (UNLOCKED/LOCKED/RUN/ERROR)  |
| `tdisp_lock_ctrl`   | `rtl/tdisp_lock_ctrl.sv`     | LOCK validation, device readiness checks           |
| `tdisp_nonce_gen`   | `rtl/tdisp_nonce_gen.sv`     | START_INTERFACE nonce validation & echo            |
| `tdisp_tdi_mgr`     | `rtl/tdisp_tdi_mgr.sv`       | Per-TDI context: interface IDs, P2P, MMIO attrs   |
| `tdisp_tlp_rules`   | `rtl/tdisp_tlp_rules.sv`     | Runtime TLP access control (TEE originator check)  |

## Parameters

| Parameter            | Default | Description                               |
|----------------------|---------|-------------------------------------------|
| `DATA_WIDTH`         | 32      | DOE AXI-Stream data width (bits)          |
| `NUM_TDI`            | 4       | Number of TDI contexts                    |
| `ADDR_WIDTH`         | 64      | PCIe address width                        |
| `BUS_WIDTH`          | 8       | Max MMIO attribute ranges per TDI         |
| `MAX_OUTSTANDING`    | 255     | Max concurrent pending TDISP messages     |
| `MAX_MSG_BYTES`      | 1024    | Max TDISP message payload (bytes)         |
| `MAC_WIDTH`          | 32      | MAC tag width (bytes)                     |
| `SESSION_ID_WIDTH`   | 32      | SPDM session ID width                     |
| `NONCE_WIDTH`        | 256     | START_INTERFACE nonce width               |
| `INTERFACE_ID_WIDTH` | 96      | Interface ID width (PCI-SIG defined)      |
| `MAX_PAYLOAD_BYTES`  | 256     | Max PCIe TLP payload                      |
| `PAGE_SIZE`          | 4096    | System page size for MMIO validation      |
| `NONCE_SEED`         | 0xDEADBEEF | LFSR seed for nonce generation         |

## Interface Ports

### DOE Mailbox (AXI-Stream)
| Port            | Dir  | Width          | Description                    |
|-----------------|------|----------------|--------------------------------|
| `doe_rx_tdata`  | in   | DATA_WIDTH     | RX data from DOE mailbox       |
| `doe_rx_tkeep`  | in   | DATA_WIDTH/8   | RX byte enables                |
| `doe_rx_tlast`  | in   | 1              | RX last beat                   |
| `doe_rx_tvalid` | in   | 1              | RX valid                       |
| `doe_rx_tready` | out  | 1              | RX ready (backpressure)        |
| `doe_tx_tdata`  | out  | DATA_WIDTH     | TX data to DOE mailbox         |
| `doe_tx_tkeep`  | out  | DATA_WIDTH/8   | TX byte enables                |
| `doe_tx_tlast`  | out  | 1              | TX last beat                   |
| `doe_tx_tvalid` | out  | 1              | TX valid                       |
| `doe_tx_tready` | in   | 1              | TX ready (backpressure)        |

### TLP Access Control
| Port                  | Dir  | Width     | Description                          |
|-----------------------|------|-----------|--------------------------------------|
| `tlp_valid_i`         | in   | 1         | TLP request valid                    |
| `tlp_header_dw0_i`    | in   | 32        | TLP header DWORD 0                   |
| `tlp_header_dw2_i`    | in   | 32        | TLP header DWORD 2                   |
| `tlp_header_dw3_i`    | in   | 32        | TLP header DWORD 3 (4DW only)        |
| `tlp_is_4dw_i`        | in   | 1         | TLP is 4-DWORD header                |
| `tlp_requester_id_i`  | in   | 16        | Requester Bus/Dev/Func               |
| `tlp_at_i`            | in   | 2         | Address Translation type             |
| `tlp_tee_originator_i`| in   | 1         | Request from TEE originator          |
| `tlp_xt_enabled_i`    | in   | 1         | PCIe Ext. Tagging enabled            |
| `tlp_allow_o`         | out  | 1         | Allow TLP access                     |
| `tlp_blocked_o`       | out  | 1         | Block TLP (violation)                |
| `tlp_tdi_index_o`     | out  | clog2(NUM_TDI) | Target TDI index                |
| `tlp_violation_irq_o` | out  | 1         | Access violation interrupt           |

### Device Configuration
| Port                      | Dir  | Width     | Description                        |
|---------------------------|------|-----------|------------------------------------|
| `ide_stream_valid_i`      | in   | 1         | IDE stream is valid                |
| `ide_keys_programmed_i`   | in   | 1         | IDE keys have been programmed      |
| `ide_spdm_session_match_i`| in   | 1         | SPDM session matches               |
| `ide_tc0_enabled_i`       | in   | 1         | Traffic Class 0 IDE enabled        |
| `phantom_fn_disabled_i`   | in   | 1         | Phantom functions disabled         |
| `no_bar_overlap_i`        | in   | 1         | No BAR address overlap detected    |
| `valid_page_size_i`       | in   | 1         | System page size matches           |
| `dev_cache_line_size_i`   | in   | 7         | Device cache line size (bytes)     |
| `fw_update_supported_i`   | in   | 1         | Firmware update supported          |

### Interface ID Initialization
| Port                  | Dir  | Width              | Description                     |
|-----------------------|------|--------------------|---------------------------------|
| `iface_id_update_i`   | in   | 1                  | Interface ID write strobe       |
| `iface_id_tdi_index_i`| in   | clog2(NUM_TDI)     | Target TDI for ID update        |
| `iface_id_value_i`    | in   | INTERFACE_ID_WIDTH | Interface ID value              |

### Status Outputs
| Port                   | Dir  | Width     | Description                       |
|------------------------|------|-----------|-----------------------------------|
| `tdi_state_out`        | out  | 2×NUM_TDI | Per-TDI state (enum array)        |
| `total_outstanding_o`  | out  | 8         | Total outstanding messages        |
| `transport_error_o`    | out  | 1         | Transport layer error detected    |
| `transport_error_code_o`| out | (enum)    | Error code                        |
| `entropy_warn_o`       | out  | 1         | Low entropy warning               |

## TDI State Machine

```
              LOCK_INTERFACE
  UNLOCKED ──────────────────► LOCKED
      ▲                         │
      │                         │ START_INTERFACE
      │ STOP_INTERFACE          ▼
      │                       RUN
      │                         │
      └─────────────────────────┘
            (or error → ERROR)
```

| State             | Code | Description                                  |
|-------------------|------|----------------------------------------------|
| `TDI_CONFIG_UNLOCKED` | 00 | Default state; configuration allowed        |
| `TDI_CONFIG_LOCKED`   | 01 | Locked; awaiting START_INTERFACE            |
| `TDI_RUN`             | 10 | Operational; TLP filtering + P2P/MMIO active|
| `TDI_ERROR`           | 11 | Error state; requires STOP to recover       |

## Supported TDISP Messages

### Request Messages (Host → Device)
| Message                          | Code  | Valid States              |
|----------------------------------|-------|---------------------------|
| `GET_TDISP_VERSION`              | 0x81  | Any                       |
| `GET_TDISP_CAPABILITIES`         | 0x82  | Any                       |
| `LOCK_INTERFACE`                 | 0x83  | UNLOCKED                  |
| `GET_DEVICE_INTERFACE_REPORT`    | 0x84  | LOCKED, RUN               |
| `GET_DEVICE_INTERFACE_STATE`     | 0x85  | Any                       |
| `START_INTERFACE`                | 0x86  | LOCKED                    |
| `STOP_INTERFACE`                 | 0x87  | LOCKED, RUN, ERROR        |
| `BIND_P2P_STREAM`                | 0x88  | RUN (with bind_p2p flag)  |
| `UNBIND_P2P_STREAM`              | 0x89  | RUN                       |
| `SET_MMIO_ATTRIBUTE`             | 0x8A  | RUN                       |
| `VDM`                            | 0x8B  | RUN                       |
| `SET_TDISP_CONFIG`               | 0x8C  | UNLOCKED                  |

### Response Messages (Device → Host)
| Message                          | Code  |
|----------------------------------|-------|
| `TDISP_VERSION`                  | 0x01  |
| `TDISP_CAPABILITIES`             | 0x02  |
| `LOCK_INTERFACE`                 | 0x03  |
| `DEVICE_INTERFACE_REPORT`        | 0x04  |
| `DEVICE_INTERFACE_STATE`         | 0x05  |
| `START_INTERFACE`                | 0x06  |
| `STOP_INTERFACE`                 | 0x07  |
| `BIND_P2P_STREAM`                | 0x08  |
| `UNBIND_P2P_STREAM`             | 0x09  |
| `SET_MMIO_ATTRIBUTE`             | 0x0A  |
| `VDM`                            | 0x0B  |
| `SET_TDISP_CONFIG`               | 0x0C  |
| `TDISP_ERROR`                    | 0x7F  |

## Test Plan

| Test File                                    | Coverage Area                           |
|----------------------------------------------|-----------------------------------------|
| `tb/tests/test_tdisp_lock_validation.sv`     | LOCK validation, pre-condition checks   |
| `tb/tests/test_tdisp_p2p_mmio.sv`            | P2P bind/unbind, MMIO attributes        |
| `tb/sv/test_tdisp_tlp_rules.sv`              | TLP access control rule evaluation      |
| `tb/sv/test_tdisp_state_transitions.sv`      | FSM state transition coverage           |
| `tb/sv/test_tdisp_error_cases.sv`            | Error injection and recovery            |
| `tb/sv/test_tdisp_multi_tdi.sv`              | Multi-TDI concurrent operations         |
| `tb/sv/test_tdisp_basic_seq.sv`              | Basic message sequence verification     |
| `tb/tdisp_tb_top.sv`                         | Full integration testbench              |

## Simulation

### Prerequisites
- Synopsys VCS (primary simulator)
- Verilator (lint checks)
- Make

### Quick Start

```bash
# Run all simulations
make -C sim sim_all

# Run individual tests
make -C sim sim_lock_val      # Lock validation test
make -C sim sim_tlp_rules     # TLP rules test
make -C sim sim_p2p_mmio      # P2P and MMIO attribute test
make -C sim sim_integration   # Full integration test

# Run regression with coverage
make -C sim regression

# Verilator lint
make -C sim verilator_lint

# View waveforms
make -C sim waves_p2p_mmio

# Clean
make -C sim clean
```

### Alternative: Regression Script

```bash
cd sim
./regression.sh          # Run all tests
./regression.sh --cov    # With coverage
./regression.sh --quick  # Re-run existing binaries
```

## Directory Structure

```
├── rtl/                    # RTL source files
│   ├── tdisp_types.sv      # Package: types, enums, constants
│   ├── tdisp_top.sv        # Top-level integration module
│   ├── tdisp_transport.sv  # DOE transport layer
│   ├── tdisp_msg_parser.sv # Message parser (RX path)
│   ├── tdisp_msg_formatter.sv # Message formatter (TX path)
│   ├── tdisp_fsm.sv        # Per-TDI state machine
│   ├── tdisp_lock_ctrl.sv  # Lock validation controller
│   ├── tdisp_nonce_gen.sv  # Nonce generator/validator
│   ├── tdisp_tdi_mgr.sv    # TDI context manager
│   └── tdisp_tlp_rules.sv  # TLP access control rules
├── tb/                     # Testbench files
│   ├── tdisp_tb_top.sv     # Integration testbench top
│   ├── agents/             # UVM-like agents (TSM agent)
│   ├── sequences/          # Test sequences
│   ├── sv/                 # Shared testbench infrastructure
│   └── tests/              # Standalone unit tests
│       ├── test_tdisp_lock_validation.sv
│       └── test_tdisp_p2p_mmio.sv
├── sim/                    # Simulation infrastructure
│   ├── Makefile            # VCS/Verilator build targets
│   ├── regression.sh       # Regression runner script
│   ├── vcs_compile.tcl     # VCS compile script
│   ├── vcs_run.tcl         # VCS simulation script
│   ├── verilator_lint.sh   # Verilator lint script
│   └── tdisp_waves*.do     # Waveform viewer scripts
├── docs/                   # Documentation
│   └── tdisp_design_spec.md
└── README.md               # This file
```

## Specification Compliance

This implementation targets the PCI-SIG **TDISP** specification:
- Chapter 5: TDISP Message Protocol (transport layer framing)
- Chapter 7: TDISP Capability Reporting
- Chapter 8: Device Interface Lifecycle (state machine)
- Chapter 9: Lock Interface Protocol (pre-condition validation)
- Chapter 10: Start/Stop Interface Protocol
- Chapter 11: P2P Stream Binding and MMIO Attributes
- Chapter 12: TLP Access Control Rules

## License

Proprietary — All rights reserved.
