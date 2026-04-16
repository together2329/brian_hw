# DMA 512-bit Data Width Update Plan

## 1. Goals
- Increase `DATA_WIDTH` parameter for the DMA subsystem from 32 bits to 512 bits.
- Ensure all address calculations, buffer sizes, and memory interfaces remain consistent with the wider datapath.
- Update verification collateral (testbenches, RAM model) and documentation accordingly.

## 2. RTL Updates (rtl/dma.sv)
1. **Parameter Defaults**
   - Change `parameter int DATA_WIDTH = 32;` to `512`.
2. **Byte Increment Logic**
   - Everywhere `DATA_WIDTH/8` is used (source/destination address increments), confirm arithmetic width is sufficient (ADDR_WIDTH should accommodate 64-byte increments).
   - Validate `length` semantics (number of DATA_WIDTH words) remain correct; update comments if needed.
3. **Data Buffer/Register Widths**
   - Ensure `data_buf_*` and `mem_wdata_*` signals already tied to `DATA_WIDTH` remain correctly sized; no extra changes expected.
4. **State Machine Timing**
   - Re-evaluate handshake assumptions: a 512-bit transfer implies 64-byte payload per transaction; confirm memory interface can deliver/consume 512-bit data in one cycle (`mem_ready` semantics unchanged).
5. **Reset/Done Logic**
   - Confirm `done` pulse logic (`remaining_q == 1`) unaffected; no width-dependent arithmetic aside from address increments.

## 3. Memory/Testbench Updates
1. **tb/dma_tb.sv**
   - Update localparam `DATA_WIDTH = 512`.
   - Adjust memory initialization/check helpers if they assume 32-bit words (e.g., literal assignments like `32'h1000_0000 + i`; expand to `512'h...` pattern or pack smaller sequences).
   - Ensure `prepare_regions` and `check_regions` operate on 512-bit words before writing/reading `mem.mem[]` entries.
2. **tb/ram_model.sv**
   - Update default `DATA_WIDTH = 512`.
   - Confirm `$clog2(DATA_WIDTH/8)` still works (DATA_WIDTH multiple of 8, so fine).
   - Ensure any literals or assignments match wider width (`wdata`, `rdata`).
3. **Memory Array Size**
   - For DEPTH=1024, total storage becomes 1024 × 512 bits (64 KB). Confirm this is acceptable for simulations.

## 4. Verification Strategy
1. **Smoke Tests**: Re-run existing dma_tb scenarios with updated widths.
2. **Stress Tests**: Add a test that transfers multiple 512-bit words (e.g., length=16) ensuring address increments step 64 bytes.
3. **Overlap/Edge Cases**: Re-validate overlapping region test with larger word size.
4. **Assertions**: Optionally add assertions checking address alignment (`src_addr`, `dst_addr` multiples of 64 bytes) if required.

## 5. Documentation & Follow-up
- Update `dma_enhancement_notes.md` with summary of the width change.
- Record in requirements doc that throughput target is now 512-bit words per cycle.
- After RTL/testbench updates, capture simulation logs demonstrating success and attach to change review.
