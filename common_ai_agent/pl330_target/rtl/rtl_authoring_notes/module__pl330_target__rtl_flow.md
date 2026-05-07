# module__pl330_target__rtl_flow

Authored `rtl/pl330_target.sv` for packet RTL-0002.

Implemented evidence:
- Module declaration matches SSOT top module `pl330_target`.
- All 11 SSOT top IO contracts are present with the requested directions and parameterized widths.
- Both reset/clock pairs are consumed by active reset-domain logic.
- `req_ready`, `rsp_valid`, `rsp_data`, and `error` are driven from nonconstant request/response state, reset-domain state, and protocol flow state.
- The packet remains draft-only because global pass/signoff is blocked by locked-truth and later authoring packets.
