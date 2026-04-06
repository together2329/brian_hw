# TDISP Design Specification

## Document Information

| Field        | Value                                      |
|--------------|--------------------------------------------|
| Project      | PCIe TDISP Controller RTL                  |
| Version      | 1.0                                        |
| Spec Reference | PCI-SIG TDISP Specification              |
| Status       | Implementation Complete                    |

---

## 1. Introduction

### 1.1 Purpose

This document captures the detailed design decisions for the TDISP (Tee Device Interface
Security Protocol) RTL controller. It maps each design module to the relevant sections of
the PCI-SIG TDISP specification and explains the architectural choices made during
implementation.

### 1.2 TDISP Overview

TDISP is a PCIe-based protocol that enables a Trusted Execution Environment (TEE) to
securely manage PCIe device interfaces (TDIs). The protocol provides:

- **Device attestation** via interface identity reporting
- **Secure configuration** through a controlled state machine lifecycle
- **Runtime access control** for TLP traffic based on TEE originator status
- **P2P stream binding** for secure peer-to-peer DMA
- **MMIO attribute management** for TEE/non-TEE memory classification

### 1.3 Confidential Computing Context

TDISP operates within the broader PCIe IDE (Integrity and Data Encryption) framework:

```
┌─────────────────────────────────────────────┐
│              Confidential Computing          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   TEE    │  │  SPDM    │  │  TDISP   │  │
│  │  Guest   │──│  Session │──│  Policy  │  │
│  │  VM      │  │  Mgmt    │  │  Engine  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│       │              │              │        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  PCIe    │  │  IDE     │  │  TDISP   │  │
│  │  Core    │──│  Stream  │──│  RTL     │  │
│  │  (TLP)   │  │  Engine  │  │  (This)  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

---

## 2. Architecture Design Decisions

### 2.1 Top-Level Integration (`tdisp_top`)

**Decision:** Monolithic top-level wiring module (no intermediate bus hierarchy).

**Rationale:**
- With 8 submodules and moderate signal count (~60 ports), a flat hierarchy avoids
  unnecessary multiplexing latency.
- All submodule interconnect is combinational or single-register pipelines.
- Parameterization propagates cleanly through a single level of hierarchy.

**Spec Mapping:** N/A (implementation choice, not spec-mandated).

### 2.2 Transport Layer (`tdisp_transport`)

**Spec Reference:** TDISP Spec Chapter 5 — TDISP Message Protocol

**Design Decisions:**

| Decision                    | Choice               | Rationale                                    |
|-----------------------------|----------------------|----------------------------------------------|
| Framing detection           | TLAST-based          | DOE mailbox uses TLAST to delimit messages   |
| Version filtering           | Major/minor compare  | Reject unsupported TDISP versions early      |
| Error handling              | Per-message CRC      | Spec mandates message integrity checking      |
| Backpressure                | AXI-Stream ready/valid | Standard PCIe DOE handshake protocol        |

**Message Framing:**
```
┌──────────┬───────────┬──────────┬──────────┬──────────────┬─────────┐
│ Version  │ Msg Type  │ Reserved | Reserved | Interface ID │Payload  │
│ (1 byte) │ (1 byte)  │ (1 byte) │ (1 byte) │ (12 bytes)   │(var.)   │
└──────────┴───────────┴──────────┴──────────┴──────────────┴─────────┘
```

### 2.3 Message Parser (`tdisp_msg_parser`)

**Spec Reference:** TDISP Spec Chapter 6 — Message Definitions

**Design Decisions:**

| Decision                    | Choice               | Rationale                                    |
|-----------------------------|----------------------|----------------------------------------------|
| Byte-level parsing          | Shift register based | Supports variable DATA_WIDTH (32/64/128)     |
| Header extraction           | Word-aligned         | 16-byte TDISP header always fits in ≤5 beats |
| Payload buffering           | BRAM-backed FIFO     | MAX_MSG_BYTES=1024 requires memory backing   |
| Malformed message handling  | ERROR response       | Spec requires error response for bad format  |

**Parsed Output Fields:**
- TDISP version (major/minor)
- Message type (request code)
- Interface ID (96-bit)
- Message-specific payload

### 2.4 Message Formatter (`tdisp_msg_formatter`)

**Spec Reference:** TDISP Spec Chapter 6 — Response Formats

**Design Decisions:**

| Decision                    | Choice               | Rationale                                    |
|-----------------------------|----------------------|----------------------------------------------|
| Response assembly           | State machine        | Multi-beat AXI-Stream generation             |
| Error response format       | Standard TDISP_ERROR | 0x7F message type with error code            |
| Header pre-pending          | Automatic            | Version + type + interface ID always first    |

### 2.5 FSM (`tdisp_fsm`)

**Spec Reference:** TDISP Spec Chapter 8 — Device Interface Lifecycle

**State Encoding:**

```
TDI_CONFIG_UNLOCKED = 2'b00   // Initial/configurable state
TDI_CONFIG_LOCKED   = 2'b01   // Locked, awaiting START
TDI_RUN             = 2'b10   // Operational state
TDI_ERROR           = 2'b11   // Error recovery state
```

**Design Decisions:**

| Decision                    | Choice               | Rationale                                    |
|-----------------------------|----------------------|----------------------------------------------|
| Per-TDI FSM replication     | Generate loop        | NUM_TDI parameter controls replication       |
| State encoding              | One-hot equivalent   | 2-bit encoded for area efficiency            |
| Transition validation       | Combinational check  | Zero-cycle latency for state guard checks    |
| Error state entry           | Automatic            | Invalid transitions force ERROR state         |

**Transition Table:**

| From      | To        | Trigger                          | Spec Section |
|-----------|-----------|----------------------------------|--------------|
| UNLOCKED  | LOCKED    | LOCK_INTERFACE (valid)           | Ch. 9        |
| LOCKED    | RUN       | START_INTERFACE (valid)          | Ch. 10       |
| LOCKED    | UNLOCKED  | STOP_INTERFACE                   | Ch. 10       |
| LOCKED    | ERROR     | Invalid message / protocol error | Ch. 8        |
| RUN       | UNLOCKED  | STOP_INTERFACE                   | Ch. 10       |
| RUN       | ERROR     | TLP violation / protocol error   | Ch. 8        |
| ERROR     | UNLOCKED  | STOP_INTERFACE                   | Ch. 8        |

### 2.6 Lock Controller (`tdisp_lock_ctrl`)

**Spec Reference:** TDISP Spec Chapter 9 — Lock Interface Protocol

**Pre-condition Checks (all must pass for LOCK to succeed):**

| Check                         | Signal                    | Spec Basis                   |
|-------------------------------|---------------------------|------------------------------|
| IDE stream valid              | `ide_stream_valid_i`      | IDE must be established      |
| IDE keys programmed           | `ide_keys_programmed_i`   | Keys must be provisioned     |
| SPDM session match            | `ide_spdm_session_match_i`| Session binding required     |
| IDE TC0 enabled               | `ide_tc0_enabled_i`       | Traffic class 0 IDE active   |
| Phantom functions disabled    | `phantom_fn_disabled_i`   | Security requirement         |
| No BAR overlap                | `no_bar_overlap_i`        | Address space isolation      |
| Valid page size               | `valid_page_size_i`       | MMU alignment requirement    |

**Lock Flags Structure:**

```
┌───────┬──────────┬─────────┬───────────┐
│ bit 0 │ bit 1    │ bit 2   │ bits 15:3 │
│lock   │ bind_p2p │ mmio    │ reserved  │
└───────┴──────────┴─────────┴───────────┘
```

- `bind_p2p` (bit 1): Enables BIND_P2P_STREAM in RUN state
- `mmio` (bit 2): Enables SET_MMIO_ATTRIBUTE in RUN state

**Design Decision:** All pre-conditions are checked combinationally in a single cycle.
This provides deterministic LOCK timing for security verification.

### 2.7 Nonce Generator (`tdisp_nonce_gen`)

**Spec Reference:** TDISP Spec Chapter 10 — Start Interface Protocol

**Design Decisions:**

| Decision                    | Choice               | Rationale                                    |
|-----------------------------|----------------------|----------------------------------------------|
| Nonce width                 | 256-bit              | Spec-mandated                                |
| LFSR polynomial             | Galois XOR-feedback  | Maximal period, low area                     |
| Per-TDI tracking            | Generate loop        | Each TDI has independent nonce state         |
| START validation            | Compare-then-accept  | Host nonce echoed back with device nonce     |

**Nonce Exchange Flow:**
```
Host                           Device
  │                              │
  │── START_INTERFACE ──────────►│  (host_nonce)
  │                              │  Validate host_nonce
  │                              │  Generate device_nonce
  │◄── START_INTERFACE_RSP ─────│  (host_nonce + device_nonce)
  │                              │
```

### 2.8 TDI Context Manager (`tdisp_tdi_mgr`)

**Spec Reference:** TDISP Spec Chapters 8-11

**Managed Context per TDI:**

| Field                | Width              | Description                         |
|----------------------|--------------------|-------------------------------------|
| `interface_id`       | INTERFACE_ID_WIDTH | 96-bit TDI identifier              |
| `state`              | 2                  | Current FSM state                   |
| `lock_flags`         | 16                 | Lock-time configuration flags       |
| `stream_id`          | 8                  | Bound P2P stream                    |
| `p2p_bound`          | 1                  | P2P stream binding active           |
| `mmio_attrs[BUS_WIDTH]` | var.            | MMIO range attributes               |
| `mmio_count`         | clog2(BUS_WIDTH+1) | Number of MMIO ranges configured    |
| `start_nonce`        | NONCE_WIDTH        | Last START nonce                    |
| `report_valid`       | 1                  | Interface report available          |

**Design Decision:** Register-based storage (not BRAM) for single-cycle context access.
With NUM_TDI=4 and BUS_WIDTH=8, total context is ~2KB — fits comfortably in registers.

### 2.9 TLP Access Rules (`tdisp_tlp_rules`)

**Spec Reference:** TDISP Spec Chapter 12 — TLP Access Control

**Access Control Policy:**

| TDI State   | TEE Originator | Non-TEE Originator | Action         |
|-------------|----------------|--------------------|----------------|
| UNLOCKED    | Any            | Any                | ALLOW          |
| LOCKED      | Any            | Any                | ALLOW          |
| RUN         | Yes            | —                  | ALLOW          |
| RUN         | —              | Yes                | BLOCK + IRQ    |
| ERROR       | Any            | Any                | BLOCK          |

**Additional Checks in RUN State:**
1. Requester ID must match IDE session endpoint
2. Address must fall within configured MMIO ranges
3. AT (Address Translation) type must be valid
4. P2P TLPs must have bound stream ID

**Design Decision:** Rule evaluation is fully combinational for single-cycle
allow/block decision, meeting PCIe transaction latency requirements.

---

## 3. P2P Stream Binding Design

**Spec Reference:** TDISP Spec Chapter 11.2-11.3

### 3.1 BIND_P2P_STREAM Protocol

```
Pre-conditions:
  - TDI must be in RUN state
  - LOCK_INTERFACE must have been called with bind_p2p flag set
  - stream_id must not already be bound

BIND_P2P_STREAM_REQUEST:
  ┌──────────┬────────┬─────────────────────┐
  │ stream_id│reserved│                     │
  │ (1 byte) │(3 bytes)│                    │
  └──────────┴────────┴─────────────────────┘

BIND_P2P_STREAM_RESPONSE:
  (empty payload on success, or ERROR with code)
```

### 3.2 UNBIND_P2P_STREAM Protocol

```
Pre-conditions:
  - TDI must be in RUN state
  - stream_id must be currently bound

UNBIND_P2P_STREAM_REQUEST:
  ┌──────────┬────────┐
  │ stream_id│reserved│
  │ (1 byte) │(3 bytes)│
  └──────────┴────────┘
```

### 3.3 Design Decision

P2P stream binding state is stored in `tdisp_tdi_mgr` per-TDI context. The `bind_p2p`
lock flag is checked at BIND_P2P_STREAM time (not at LOCK time), allowing the host to
use different policies per TDI.

---

## 4. MMIO Attribute Management Design

**Spec Reference:** TDISP Spec Chapter 11.4-11.5

### 4.1 SET_MMIO_ATTRIBUTE Protocol

```
Pre-conditions:
  - TDI must be in RUN state

SET_MMIO_ATTRIBUTE_REQUEST:
  ┌──────────────────┬────────────┬─────────────────┐
  │ start_page_addr  │ num_pages  │    attributes    │
  │   (8 bytes)      │ (4 bytes)  │    (1 byte)      │
  └──────────────────┴────────────┴─────────────────┘

Attributes byte:
  bit 0: IS_NON_TEE_MEM
  bits 7:1: reserved
```

### 4.2 IS_NON_TEE_MEM Attribute

When set, the MMIO range is classified as non-TEE memory. This affects TLP access
control: non-TEE originators may access IS_NON_TEE_MEM ranges even when the TDI is
in RUN state.

### 4.3 Design Decision

MMIO attributes are stored as an array of `BUS_WIDTH` entries per TDI. Each entry
contains:
- `start_addr` (64-bit)
- `num_pages` (32-bit)
- `is_non_tee_mem` (1-bit flag)

Range lookup in `tdisp_tlp_rules` uses a priority-encoded comparator chain for
deterministic timing.

---

## 5. Error Handling

### 5.1 Error Codes

| Error Code | Name                  | Description                           |
|------------|-----------------------|---------------------------------------|
| 0x0001     | INVALID_STATE         | Message received in wrong TDI state   |
| 0x0002     | INVALID_INTERFACE_ID  | Interface ID not recognized           |
| 0x0003     | INVALID_VERSION       | Unsupported TDISP version             |
| 0x0004     | LOCK_PRECOND_FAIL     | LOCK pre-condition not met            |
| 0x0005     | NONCE_MISMATCH        | START nonce validation failed         |
| 0x0006     | P2P_NOT_BOUND         | P2P operation without bind_p2p flag   |
| 0x0007     | MMIO_INVALID_RANGE    | Invalid MMIO range parameters         |
| 0x0008     | TLP_VIOLATION         | Runtime TLP access violation          |
| 0x0009     | MSG_FORMAT_ERROR      | Malformed message                     |
| 0x000A     | UNSUPPORTED_MESSAGE   | Unknown message type                  |

### 5.2 Error Recovery

- TDISP_ERROR responses include the error code for host-side diagnostics
- TDI enters ERROR state on protocol violations
- STOP_INTERFACE is the only valid message in ERROR state
- STOP_INTERFACE from ERROR returns TDI to UNLOCKED (full reset)

---

## 6. Verification Strategy

### 6.1 Unit Tests

| Test                         | What's Verified                                    |
|------------------------------|----------------------------------------------------|
| `test_tdisp_lock_validation` | All 7 LOCK pre-conditions, error paths, flag handling |
| `test_tdisp_p2p_mmio`        | BIND/UNBIND P2P, SET_MMIO, state guards, multi-TDI |
| `test_tdisp_tlp_rules`       | TEE/non-TEE originator, address range, state filtering |

### 6.2 Integration Tests

| Test                         | What's Verified                                    |
|------------------------------|----------------------------------------------------|
| `test_tdisp_state_transitions` | Full FSM lifecycle: UNLOCKED→LOCKED→RUN→UNLOCKED |
| `test_tdisp_error_cases`     | Error injection, recovery via STOP                 |
| `test_tdisp_multi_tdi`       | Concurrent operations on multiple TDIs             |
| `test_tdisp_basic_seq`       | Standard message sequence compliance               |
| `tdisp_tb_top`               | Full system-level integration                      |

### 6.3 Coverage Targets

| Metric          | Target   |
|-----------------|----------|
| Line coverage   | ≥ 90%    |
| FSM state       | 100%     |
| FSM transition  | ≥ 95%    |
| Toggle coverage | ≥ 85%    |
| Assertion       | ≥ 90%    |

---

## 7. Implementation Notes

### 7.1 Clocking

Single clock domain (`clk`/`rst_n`). All modules use synchronous active-low reset.
No clock domain crossing is required as DOE transport is expected to be in the same
clock domain as the PCIe core.

### 7.2 Reset Strategy

Active-low synchronous reset (`rst_n`). Reset clears:
- All TDI states to UNLOCKED
- All P2P bindings
- All MMIO attributes
- Interface ID registers (must be re-programmed after reset)
- Transport layer state machines
- Nonce generator seeds

### 7.3 Parameterization

All design parameters are exposed at `tdisp_top` level and propagated down.
Key trade-offs:

| Parameter      | Small Value         | Large Value              |
|----------------|---------------------|--------------------------|
| `NUM_TDI`      | Lower area          | More concurrent TDI ctx  |
| `BUS_WIDTH`    | Fewer MMIO ranges   | More MMIO range entries  |
| `DATA_WIDTH`   | Lower throughput    | Higher DOE throughput    |
| `MAX_MSG_BYTES`| Lower BRAM usage    | Larger message support   |

### 7.4 Synthesis Considerations

- All modules are purely RTL (no hard IP dependencies)
- `tdisp_nonce_gen` LFSR uses XOR-based feedback (no multipliers)
- `tdisp_tlp_rules` address comparison is the critical timing path
- BRAM inference hints included in `tdisp_msg_parser` for payload FIFO

---

## 8. Revision History

| Version | Date       | Changes                              |
|---------|------------|--------------------------------------|
| 1.0     | 2024-12    | Initial implementation complete      |
