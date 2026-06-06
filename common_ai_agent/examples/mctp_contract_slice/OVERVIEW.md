# MCTP Contract Slice — worked example

A small, fully reproducible worked example of the contract-closure direction in
the wiki: [[req-obligation-contract-evidence-validation]] →
[[locked-truth-concept]] → [[mctp-assembler-contract-breakdown]] →
[[llm-contract-repair-loop]] → [[formal-verification-evidence]].

It proves the methodology end-to-end on a tiny RX MCTP assembler: every contract
is closed across **three independent lanes** (iverilog compile, verilator
`--assert` random sim, SymbiYosys+z3 formal), and **a deliberately planted bug
per contract is caught** (mutation kill) so closure is non-vacuous.

## Toolchain

```
iverilog 12, verilator 5.x, yosys + yosys-smtbmc, SymbiYosys (sby), z3
# macOS: brew install z3 ; sby from github.com/YosysHQ/sby (make install PREFIX=~/.local)
```

## Two parts

### 1. `rtl/mctp_rx_assembler.sv` — 12-contract single-context skeleton
Run: `./run_all.sh`
Contracts: gate / key / start / single / cont / seq / payload / end / drop /
out / reset / status. Assertions are embedded under `` `ifdef FORMAL `` (they see
internal `len_q` natively — no debug ports, no `bind`). Each `INJECT_*_BUG`
breaks exactly one contract.
Result: `signoff/validation_closure_12.json` — correct PASS on all 3 lanes;
all 11 mutants killed (verilator + formal).

### 2. `rtl/mctp_rx_mc.sv` — multi-context + 3-field key + interleaving deep-dive
Run: `./run_mc.sh`
Reflects v3 spec §9.1/§9.2/§9.3: key `{source_eid, tag_owner, message_tag}`,
2 independent contexts, interleaved arrival. Proves cross-context **isolation**
(a packet for one key never corrupts another context), allocation, duplicate-SOM
abort, and per-context sequence. Formal `cover` proves two contexts are live with
different keys simultaneously (interleaving is actually reachable).
Result: `signoff/validation_closure_mc.json`.

## What this example is / isn't

- **Is**: a teaching skeleton that proves the contract→evidence→mutation-kill
  loop runs on real RTL with real tools.
- **Isn't**: the production IP. The full IP lives at `mctp_assembler_v3/`. Payload
  is a byte count (not SRAM byte-exact packing), key is small-width, payload
  ordering / descriptor / header-snapshot queue / timeout are separate stages
  (see the v3 reflection map in [[mctp-assembler-contract-breakdown]]).

## Gotchas this example documents (real, hit during bring-up)

1. yosys-native frontend ignores SVA `bind` → checker dropped as unused → vacuous
   pass. Fix: embed assertions under `` `ifdef FORMAL `` (or an explicit wrapper).
2. An identity mutation (`x <= x`) is optimized to a no-op by yosys → looks like a
   pass. Use an unambiguous mutation.
3. yosys formal NBA precedence can differ from Verilog last-wins on overlapping
   assignments → a sim lane caught what formal modeled away. Run both lanes.
4. Formal with no reset constraint starts from a free state → coincidental passes.
   Add a power-on `assume(!rst_n)`.
5. A `proven` assert is meaningless if its antecedent is unreachable → pair every
   assert with a `cover`, and require an assert-count > 0 anti-vacuity guard.
