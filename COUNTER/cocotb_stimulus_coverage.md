# Cocotb Stimulus and Coverage Strategy for DMA

## Directed Stimulus Plan
1. **Reset Sequence**: common coroutine to assert `rst_n=0` for 5 cycles, release, and wait for DUT ready.
2. **Test1 (No-op)**:
   - Set `length=0`, random but aligned addresses, ensure `done` pulses quickly and no memory activity.
3. **Test2 (Single word)**:
   - Prepare 1-word source/dest, run DMA, verify mem copy and latency.
4. **Test3 (Back-to-back)**:
   - Issue two consecutive transfers (2 words each) without extra idle, verifying `busy/done` handshake stability.
5. **Test4 (Medium burst)**:
   - 8-word transfer verifying sustained handshake.
6. **Test5 (Overlap dst>src)**:
   - Source base 200, dest 204, length 4; ensure correct copy despite overlap.
7. **Test6 (Reverse overlap dst<src)**:
   - Source 300, dest 296, length 6; check reverse overlap correctness.
8. **Test7 (Long burst)**:
   - 64-word transfer to stress throughput.
9. **Test8 (Near boundary)**:
   - Transfer near RAM end (DEPTH-96 → DEPTH-32) for boundary handling.

## Randomized Stimulus
- After directed suite, run `NUM_RANDOM=20` trials:
  - Random `src_word`, `dst_word`, `length` (1–32 words).
  - Random pattern selection.
  - 20% chance to create overlaps by forcing `dst_word = src_word + delta` where `delta` can be negative.
  - Ensure addresses stay within bounds.
  - Track seeds for reproducibility; log parameters of each trial.

## Memory Pattern Strategy
- Use helper functions to generate 512-bit payloads for each lane pattern (zero, word-index, lane-sweep, alt-toggle).
- For random tests, choose pattern randomly per trial.

## Coverage Strategy
1. **Functional Coverage Metrics (tracked in scoreboard/config):**
   - Transfer length categories: {1, 2-7, 8-15, 16-63, 64}.
   - Overlap type bins: {none, dst>src, dst<src}.
   - Address region bins: {low (<128 words), mid, high (>DEPTH-128)}.
   - Pattern usage counts.
   - Random trials executed vs requested.

2. **Assertions/Checks:**
   - Each directed/random test verifies destination matches source (or expected mismatch when configured).
   - Optional: assert `mem_req` deasserts when `busy=0` (via simple monitors).

3. **Reporting:**
   - After run, print coverage summary (counts per bin) and random trial results.
   - Optionally emit JSON/CSV for integration into CI dashboards.

## Reusability Considerations
- Parameterize number of random trials and coverage bins via config file/ENV.
- Provide ability to skip long tests for smoke mode.
- Include seed override for deterministic reruns.
