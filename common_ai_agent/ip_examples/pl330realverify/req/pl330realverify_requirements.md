# pl330realverify Requirements Seed

Pipeline-provided context only; no external requirements document was present at ssot-gen start.

Assumption policy for this engineering draft:
- Target is a PL330/DMA-330-like DMA controller verification IP contract.
- Single-clock APB4 control interface plus AXI4 read/write master data interfaces.
- Eight channels, 32 peripheral event inputs, 64-bit AXI datapath, 32-bit register/data address fields.
- Behavioral scope is a production-oriented, SSOT-owned contract for downstream RTL/TB generation and verification; it is not a verbatim ARM TRM implementation.
- Open human decisions are captured as SSOT QA cards and custom.assumptions in the YAML.
