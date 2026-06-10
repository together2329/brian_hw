# Address-map validation rules

`addrmap_check` runs after **every** edit that touches `addrMap` or any
instance's `addr`. The architect must halt and report on any failure
below.

## Hard errors (block the edit)

1. **Overlap.** Any two entries `[base_a, base_a + range_a)` and
   `[base_b, base_b + range_b)` intersecting.
2. **Zero base.** `base: 0x0000_0000` is reserved for the SoC vector
   table or the boot ROM — never assign it to a peripheral.
3. **Range = 0.** Every entry must have a positive range.
4. **Misaligned base.** `base` must be a multiple of `range` (so the
   region is power-of-two-aligned and the decoder is cheap).
5. **Range not power-of-two.** `range` must be in {0x1000, 0x2000,
   0x4000, …, 4 GiB}. Non-power-of-two ranges break standard AXI
   decoders.

## Soft warnings (proceed but flag)

1. **Gap > 1 GiB.** A huge unused gap between two regions probably
   means the user forgot an IP — surface it.
2. **Region > 4 GiB.** Past 4 GiB the SoC needs 64-bit AXI; double-check
   that all masters support it.
3. **Region < 4 KiB.** Most decoders bottom out at 4 KiB pages; sub-page
   regions waste decoder bits.
4. **Non-monotonic order.** `addrMap[]` should be sorted by `base`. If
   not, the architect re-sorts on the next write (and warns).

## Output format

When validation runs, emit a one-line per check:

```
✓ overlap        — clean
✓ zero base      — clean
✓ range > 0      — clean
✗ alignment      — spi_master_0 base 0x4000_2A00 not multiple of range 0x1000
⚠ gap            — gap of 0x4000_0000 between spi_master_0 and ddr_phy
```

A single ✗ blocks the edit. ⚠ does not block but the architect
acknowledges it before continuing.
