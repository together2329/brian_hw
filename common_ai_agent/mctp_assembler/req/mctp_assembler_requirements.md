# MCTP Assembler Requirements

## Purpose

`mctp_assembler` receives raw PCIe VDM TLP packets over an AXI write-slave ingress. Each AXI write burst carries one PCIe VDM TLP in `WDATA`, including the PCIe TLP/VDM header, MCTP transport header, and MCTP payload. The IP validates MCTP-over-PCIe-VDM packets, assembles fragmented MCTP messages, writes completed message payloads to an SRAM write port, exposes control/status/debug through an APB slave interface, and raises a single interrupt.

## External Interfaces

- AXI write slave ingress in `axi_aclk` domain.
- APB slave control/debug register interface in `pclk` domain.
- AXI and APB clocks are asynchronous.
- SRAM write port is in the AXI clock domain.
- One top-level interrupt output `intr`.

## Protocol Assumptions

- One AXI write burst equals exactly one PCIe VDM TLP.
- Byte lane 0 of the first accepted `WDATA` beat contains TLP byte 0.
- `WSTRB` marks valid bytes; partial valid bytes are expected on the final beat.
- `WLAST` marks TLP end.
- `AWADDR` selects an ingress window and is not interpreted as a payload address.
- The upstream PCIe block provides raw TLP bytes; ECRC/TD handling is configurable and may be treated as already checked/stripped or ignored.

## MCTP Requirements

- Accept MCTP over PCIe VDM packets matching the DMTF binding:
  - Type 1 VDM with data.
  - Message Code `0x7F`.
  - DMTF Vendor ID `0x1AB4`.
  - MCTP VDM code `0000b`.
- Parse the MCTP transport header.
- Assemble fragmented messages using `{source_eid, tag_owner, message_tag}`.
- Use `SOM`, `EOM`, and 2-bit packet sequence increment modulo 4 to determine message start, continuation, completion, and sequence errors.
- Strip PCIe/VDM header, MCTP transport header, and final packet pad bytes before writing assembled message payload to SRAM.
- Record descriptor metadata in APB-readable internal registers/FIFO.

## Control And Debug

- APB registers configure enable, soft reset, local EID, destination EID filtering policy, MTU, timeout, SRAM base/limit, interrupt enables, and debug controls.
- APB reads expose status, interrupt status, descriptor words, error status, counters, and debug state.
- Interrupt is level-style active-high, generated in the APB/system domain from synchronized AXI events, and cleared through APB write-one-to-clear registers.

## Required Error Handling

- Malformed/short TLP.
- Unsupported VDM, vendor ID, message code, or MCTP VDM code.
- Bad MCTP header version.
- Unsupported destination EID based on configuration.
- Unexpected middle/end packet without active context.
- Duplicate SOM for an active context.
- Packet sequence mismatch.
- Context table full.
- Message size overflow.
- SRAM allocation/write overflow.
- Descriptor FIFO/mailbox full.
- Assembly timeout.

## Drop Classification

`mctp_assembler` distinguishes packet drops from assembly drops.

### Packet Drop

Packet drop applies before a packet starts, appends, completes, or terminates an assembly context. A packet drop never allocates a new context, never releases an existing context, never writes payload bytes to SRAM, and never publishes a successful descriptor.

Packet drop conditions include:

- Disabled ingress when `drop_when_disabled` is set.
- Malformed or short AXI/TLP packet, inconsistent `WLAST`/length/`WSTRB`, or unsupported AXI burst policy.
- Unsupported PCIe VDM format/routing for this IP.
- Unsupported PCIe VDM message code, DMTF vendor ID, or MCTP VDM code.
- Bad MCTP transport header version or insufficient MCTP header bytes.
- Unsupported destination EID based on APB configuration.
- Unexpected middle/end packet without an active context.
- Bad, unexpected, or expired tag-owner/message-tag policy when the packet is not allowed to affect assembly state.
- Unsupported pad length, non-EOM pad, or dword alignment violation.

### Assembly Drop

Assembly drop applies after a packet has been accepted into, or would update, an active assembly context. An assembly drop aborts the affected context, releases that context slot, suppresses any successful descriptor for that message, and records the drop reason.

Assembly drop conditions include:

- Duplicate `SOM` for an active `{source_eid, tag_owner, message_tag}` key.
- Packet sequence mismatch for an active context.
- Message size overflow.
- SRAM allocation/write overflow.
- Descriptor FIFO/mailbox full when a completed message cannot publish metadata.
- Assembly timeout.
- Protocol violation that makes an active context unrecoverable.

## Initial Approved Assumptions

- IP name and top module: `mctp_assembler`.
- AXI data width default: 128 bits.
- APB data width: 32 bits.
- Assembly context queue count: 15, allowing up to 15 simultaneous interleaved MCTP message assemblies.
- Maximum assembled message size default: 4096 bytes.
- Baseline/default MTU: 64 bytes.
- Destination EID filtering is configurable and initially enabled for `cfg_local_eid`.
- Message payload types are opaque to hardware; the IP records the first MCTP message type byte but does not parse PLDM/SPDM/NVMe-MI semantics.

## Open Human Review Items

- Confirm AXI ID support requirements. The first SSOT uses no top-level AXI ID pins and allows only one outstanding ingress burst.
- Confirm whether upstream strips/checks ECRC or whether this IP must account for TLP digest bytes.
- Confirm descriptor pop policy: explicit APB pop command versus pop-on-read.
- Confirm exact SRAM address allocation/wrap policy.
- Confirm timeout cycle units and default value for the target system.