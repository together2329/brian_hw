# module__timer_regs__registers

Updated `timer_regs` to make the LOAD.value field explicit as live RTL behavior rather than comment-only evidence.

- Added `load_value_next` for the full-width writable LOAD.value datapath from `pwdata`.
- Added `load_value_read_data` for LOAD.value readback from `load_q`.
- Preserved existing APB decode, CTRL.ENABLE, CTRL.RESERVED read-as-zero masking, STATUS.count readback, STATUS write ignore, and unmapped-address `pslverr` behavior.
- No SSOT semantics were invented; this only names and wires the already-required LOAD.value full-field behavior from the locked register contract.

PASS/signoff remains blocked by the broader authoring plan until all remaining required packets and gates close.