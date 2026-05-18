# atcdmac100 Requirements Ledger

- Source: human-approved ATLAS Web Q&A state captured for `atcdmac100`.
- Authority: this file records requirement intent; the YAML SSOT remains the machine-readable source for downstream FL, RTL, DV, lint, simulation, and coverage stages.
- IP kind: open-decision marker.
- Generated: 2026-05-18T11:25:20.

## Approved Requirement Decisions
- `bus_interface`:  Compliant with AMBA™ 2 AHB protocol specification; Figure 1 shows the block diagram of ATCDMAC100, which contains one AHB master interface; for data transfer and one AHB slave interface for register programming.; AHB Bus; AHB Master AHB Slave
- `clock_reset`: the channel without asserting dma_ack. The error handling software should reset both the; hclk I System bus clock; hresetn I System bus reset; | hclk | | | I | | System bus clock; | hresetn | | | I | | System bus reset
- `interrupt`: 3.6. INTERRUPT STATUS REGISTER (OFFSET 0X30) ....................................................................................................... 14; 5.1.3. Interrupt Handling ........................................................................................................................................... 24; 5.2.3. Interrupt Handling ........................................................................................................................................... 25; TABLE 7. INTERRUPT STATUS REGISTER ..................................................................................................................................... 14; update the interrupt status register, IntStatus, and assert the dma_int interrupt signal if the
- `memory_map`: 4.2. FIFO SIZE ................................................................................................................................................................. 21; FIFO; FIFODepth 9:4 RO FIFO depth Configuration; 4.2. FIFO Size; Define ATCDMAC100_FIFO_DEPTH_n to specify the FIFO size as n entries (each entry is
- `parameters`: 1.1 2015-09-09 1.1 Describe the multiple address width support; 1.1 | 2015-09-09 | 1.1 | | | Describe the multiple address width support; 4.6. ADDRESS WIDTH....................................................................................................................................................... 22; FIFODepth 9:4 RO FIFO depth Configuration;  Unaligned transfer width
- `purpose`: ATCDMAC100 DS079 V1.2 Extracted Requirement Evidence; source: `/Users/brian/Desktop/andes/platform/AE210P_20161118/DOCS/AndeShape_ATCDMAC100_DS079_V1.2.pdf`; AndeShape™ ATCDMAC100 Data Sheet; 1.3. FUNCTION DESCRIPTION ............................................................................................................................................ 2
- `register_map`: AndeShape™ ATCDMAC100 Data Sheet; Revise the clear condition of channel abort register as; 1.1 2015-09-09 1.1 Describe the multiple address width support; 1.2 | 2016-01-27 | 3.8 | | | Revise the clear condition of channel abort register as write one clear; 1.1 | 2015-09-09 | 1.1 | | | Describe the multiple address width support
- `submodule_structure`: 1.2. BLOCK DIAGRAM ......................................................................................................................................................... 1; 4.2. FIFO SIZE ................................................................................................................................................................. 21; FIGURE 1. ATCDMAC100 BLOCK DIAGRAM ................................................................................................................................ 1; AndeShape™ ATCDMAC100 is a direct memory access controller which transfers regions of data; 1.2. Block Diagram
- `test_expectation`: 5.1.1. Scenario .............................................................................................................................................................. 23; 5.2.1. Scenario .............................................................................................................................................................. 25; update the interrupt status register, IntStatus, and assert the dma_int interrupt signal if the; channel, and assert dma_int if the corresponding interrupt is enabled.; device should assert dma_req only when it prepares enough data to transfer or when it has

## Behavioral Contract
- Top module `atcdmac100` must implement the approved function model and cycle model exactly as represented in `atcdmac100/yaml/atcdmac100.ssot.yaml`.
- Function model operations: ATCDMAC100 DS079 V1.2 Extracted Requirement Evidence; source: `/Users/brian/Desktop/andes/platform/AE210P_20161118/DOCS/AndeShape_ATCDMAC100_DS079_V1.2.pdf`; AndeShape™ ATCDMAC100 Data Sheet; 1.3. FUNCTION DESCRIPTION ............................................................................................................................................ 2.
- Cycle model obligation: latency, sampling, and output timing are defined by the SSOT cycle model.
- Any feature, port, state update, bus behavior, interrupt, memory, or coverage goal absent from the SSOT is outside this revision and requires a new approved requirement entry before implementation.
- RTL generation, test generation, sim-debug, and coverage are expected to read the SSOT and must not infer hidden behavior from chat history.

## Interface And Decomposition

## Decomposition Units
- `atcdmac100_figure` owns 1. ATCDMAC100  DIAGRAM ................................................................................................................................ 1.
- `atcdmac100` owns Top-level wrapper matching SSOT top_module and external interfaces.

## Verification And Coverage Intent
- Verification must prove FL-vs-RTL equivalence for every SSOT goal before final signoff.
- Functional coverage is the primary closure metric for this flow; structural metrics are required only when the SSOT explicitly requests tool evidence for them.
- DUT-only lint must pass before simulation evidence can be used for signoff.
- Scenario 1 `SC_RESET`: Assert and deassert reset using the approved clock/reset scheme.
- Scenario 2 `SC1`: 5.1.1. Scenario .............................................................................................................................................................. 23
- Scenario 3 `SC2`: 5.2.1. Scenario .............................................................................................................................................................. 25
- Scenario 4 `SC3`: update the interrupt status register
- Scenario 5 `SC4`: IntStatus
- Scenario 6 `SC5`: and assert the dma_int interrupt signal if the
- Scenario 7 `SC6`: channel
- Scenario 8 `SC7`: and assert dma_int if the corresponding interrupt is enabled
- Scenario 9 `SC8`: device should assert dma_req only when it prepares enough data to transfer or when it has

## Acceptance Criteria
- `atcdmac100/yaml/atcdmac100.ssot.yaml` parses and contains the functional model, cycle model, RTL contract, test requirements, quality gates, traceability, and downstream workflow action ledger.
- Generated RTL implements only SSOT-approved behavior and passes DUT-only lint with zero errors.
- Generated cocotb/pyuvm tests execute scoreboard comparisons against the functional model.
- Simulation produces machine-readable pass evidence, FL-vs-RTL comparison evidence, and coverage evidence.
- Final goal audit passes with fresh artifacts for requirements, SSOT, FL model, RTL, lint, DV, simulation, coverage, and equivalence.
