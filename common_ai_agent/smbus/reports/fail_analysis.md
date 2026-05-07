# Fail analysis — smbus

> Auto-generated skeleton. The LLM is expected to fill in `[LLM TODO]` slots
> with specific patch proposals. **Cardinal rule**: do NOT modify FL/spec/coverage
> to make the test pass — only RTL/TB/vectors are LLM-editable.

## Summary
- Total failing rows: **3**
- Owner-on-fail `rtl`: 1
- Owner-on-fail `rtl|tb`: 1
- Owner-on-fail `tb`: 1
- Failing test: `TC_smbus_writeread`

## Detail
### EQ_TRANSACTION_FM_PRIMARY
- **Owner-on-fail (heuristic, LLM can override)**: `rtl`
- **Expected**: `{"packet_ok": 1, "resp": 0, "result": 42}`
- **Actual**:   `{"packet_ok": 0, "resp": 0, "result": 42}`
- **Context**: smbus 1-byte write/read; FL says packet_ok=1, RTL drove 0
- **Likely cause**: [LLM TODO] inspect FL trace + RTL waveform around this goal
- **Suggested RTL patch**: [LLM TODO] propose minimal RTL patch in the owning module
- **Trace excerpt**:
  ```
  {"event": "start", "t": 0}
  {"event": "ack_seen", "t": 7}
  ```

### EQ_PROTOCOL_HANDSHAKE_0
- **Owner-on-fail (heuristic, LLM can override)**: `rtl|tb`
- **Expected**: `{"awready": 1, "awvalid": 1}`
- **Actual**:   `{"awready": 0, "awvalid": 1}`
- **Context**: AXI handshake stalled
- **Likely cause**: awready never asserted in slave model
- **Suggested RTL patch**: [LLM TODO] propose minimal RTL patch in the owning module

### EQ_COVERAGE_burst_64beat
- **Owner-on-fail (heuristic, LLM can override)**: `tb`
- **Expected**: `{"hit": true}`
- **Actual**:   `{"hit": false}`
- **Context**: coverage bin not exercised by current testlist
- **Likely cause**: [LLM TODO] inspect FL trace + RTL waveform around this goal
- **Suggested RTL patch**: [LLM TODO] propose minimal RTL patch in the owning module

## Next steps (LLM owned)
1. Pick the highest-priority owner-on-fail entry (rtl > rtl|tb > tb).
2. Look at the corresponding RTL module + the FL trace around the failing transaction.
3. Propose the smallest RTL patch that closes the diff. Do NOT touch FL.
4. Re-run cocotb harness (`make fl_cl_rtl` in `<ip>/verify/`).
5. If still failing, run `emit_regression_min.py` to bisect the seed first.
