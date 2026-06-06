---
title: MCTP Contract Slice Trial And Error 2026-06-06
type: reference
tags: [trial-and-error, formal, sby, yosys, verilator, mutation, mctp, contract, equivalence-check, process]
updated: 2026-06-06
related: [mctp-assembler-contract-breakdown, formal-verification-evidence, llm-contract-repair-loop, spec-loop-and-equivalence-check, req-obligation-contract-evidence-validation]
---

# MCTP Contract Slice Trial And Error 2026-06-06

The dated process record for building `examples/mctp_contract_slice/` — taking the
contract-closure methodology from concept to a runnable, open-source, three-lane
(iverilog + verilator `--assert` + SymbiYosys/z3) worked example, slice by slice,
up to a full-assembler integration. This page is the "if you repeat this, here are
the traps" log; the design itself is in [[mctp-assembler-contract-breakdown]].

The single recurring lesson, stated once:

```text
If a planted mutant does NOT die, the verification (or its model) is wrong,
not the RTL. Every gotcha below was caught by that rule.
```

## 0. Toolchain bring-up

- **No prover was installed.** `sby` (SymbiYosys) absent, no SMT solver. Fix:
  `brew install z3`; `git clone github.com/YosysHQ/sby && make install PREFIX=~/.local`.
  yosys + `yosys-smtbmc` were already present (Homebrew). The earlier wiki claim
  "no prover wired" was about the repo *pipeline*, not feasibility — the OSS prover
  installs and runs fine.
- **sby `[files]` flattens to `src/` by basename.** The `[script]` must
  `read_verilog mctp_x.sv` (basename), not `rtl/mctp_x.sv` — else "File not found".
- **`equiv`/`smtbmc` need `proc` first** ("module contains memories or processes"),
  and **async reset (`$adff`) needs `async2sync`** ("No SAT model for async FF").

## 1. yosys-native SVA gotchas (no Verific)

- **`bind` is ignored** → the checker module is dropped as "unused" →
  **vacuous pass** (both the correct prove and the mutant BMC passed because there
  were *zero* assertions). Caught only because the mutant didn't fail. Fix: embed
  assertions in the RTL under `` `ifdef FORMAL `` (they see internal signals
  natively), or instantiate the checker via an explicit wrapper module.
- **`property … endproperty` named blocks are unsupported** ("unexpected
  TOK_PROPERTY").
- **Standalone `assert property (@(posedge clk) …)` also choked** ("unexpected
  '@'"). Portable form: immediate `assert(...)` inside a clocked `always` using
  `$past` — the open-source-friendly style.
- **Anti-vacuity guard, always:** after `prep`, require `select -count t:$assert`
  > 0, and pair every `assert` with a reachable `cover`.

## 2. Mutation-design gotchas

- **Identity mutation is optimized away.** `drop_count <= drop_count` is a no-op
  to yosys → the STATUS mutant survived. Use an unambiguous change.
- **NBA precedence differs from Verilog last-wins.** A later unconditional
  override vs an earlier conditional `+1` — yosys formal kept the `+1`, so formal
  *missed* the STATUS bug while verilator caught it. Fix: express the mutation as a
  single assignment (a `` `DROP_INC `` macro). Lesson: run **both** lanes.
- **A mutation can hide its own trigger.** The ALLOC mutant forced every
  allocation to slot 0, so the "table full" state never occurred and the only
  alloc contract never fired → mutant survived. The real gap was a **missing
  contract**, not a weak test → added `C-ALLOC-NEW` ("a new allocation must land on
  a free slot"). A surviving mutant means the contract *set* has a hole.

## 3. Formal-modeling gotchas (false failures = verification bugs, not RTL bugs)

- **No reset constraint → coincidental pass.** With a free initial state the
  solver chose an 8-bit `drop_count = 255` so `255 + 1 = 0` masked a frozen-counter
  bug. Fix: a power-on `assume(!rst_n)` (first cycle).
- **Unbounded data wraps.** The byte-exact payload symbolic proof failed because a
  message longer than the SRAM wrapped the 3-bit address and overwrote addr 0. Fix
  reflected the spec: v3 §10.2 MAX_MESSAGE_BYTES overflow → drop (a `room` guard).
- **True-but-not-k-inductive → UNKNOWN.** The byte-exact invariant needed
  strengthening: aux invariants `cnt <= DEPTH`, `wp == cnt` so k-induction closes.
- **Single-packet reset of a pointer broke an aux invariant.** A single-packet
  message resets `wp = 0`, so `f_k < f_cwp` (0<0) failed; fix: `!active || f_k<f_cwp`.
- **Assertion width overflow.** A region-bound assert `wr_addr < base + REGION`
  overflowed 3-bit arithmetic (`4 + 4 = 0`) → always false. Fix: `<= base+(REGION-1)`.
- **`$past`-based asserts fire across reset→run.** Combinational `hdr_upd` was true
  during reset (the packet was swallowed), so `$past(hdr_upd)` at the next cycle
  wrongly expected state. Fix: guard `$past`-based asserts with `$past(rst_n)`.

## 4. Simulation / testbench gotchas

- **verilator pragma trap.** A TB comment that *starts with the word* "verilator"
  is parsed as a pragma → `BADVLTPRAGMA`. Reword the comment.
- **NBA-read-after-`@(posedge)`.** Reading a registered output immediately after
  `@(posedge clk)` reads the pre-latch value → false scoreboard failure. Add `#1`.
- **Descriptor scoreboard off-by-one under interleaving.** A TB reference-FIFO
  ordering bug (got[N] == exp[N+1]) — not an RTL bug. Since formal proves the
  descriptor/header contracts, the sim lane was simplified to the robustly
  observable payload/gate/seq checks.
- **Random sim leaves coverage holes formal fills.** The `ANY` drop mutant only
  fires when exactly the timeout bit is set alone (~1/16384), so random sim missed
  it; formal caught it. (And vice-versa: NBA-precedence STATUS was sim-only.)

## 5. Shell / git / repo process gotchas

- **zsh `nomatch` aborts the whole command.** `rm -rf mc_* obj_*` fails entirely if
  any glob has no match → use `find . -maxdepth 1 \( -name 'mc_*' … \) -exec rm -rf`.
- **zsh does not word-split unquoted vars** (unlike bash) → `$CMD "$arg"` ran the
  whole `$CMD` string as one program name. Inline the command or use an array.
- **The wiki direction pages were committed by the user directly to `main`**
  (predating the sby work), so `formal-verification-evidence` still said "no prover
  wired" — stale and had to be corrected after the prover was demonstrated.
- **`.git/info/exclude` globally ignores `README.md` and `.gitignore`** in this
  repo → the example's README didn't stage; renamed to `OVERVIEW.md` and put build
  patterns in the local exclude.
- **`main` is the default branch** → branch first, commit, fast-forward merge.
  `main` also advanced (other work) and was already pushed — verify with
  `git ls-remote origin refs/heads/main` rather than trusting a stale tracking ref.

## 6. What integration exposed that slices could not

- A **fixed write base** (`INJECT_BASE_BUG`) is invisible with one context but
  corrupts the other once two contexts interleave — pure coupling, only visible
  after fusing multi-context + payload.
- The two worst false-failures (`$past` across reset, sim FIFO off-by-one) only
  appeared at full-integration scale. Integration tests the **harness** as much as
  the design.

## Meta

```text
- Multi-lane is not redundancy: sim and formal each caught bugs the other missed.
- Most "formal failures" on a correct design are verification bugs (assert width,
  aux invariant, reset guard, capture timing) — formal forces the spec to be exact.
- Slices prove contracts in isolation; integration proves they compose AND that the
  verification harness itself is sound.
- The mutant-must-die rule turned every silent vacuity into a visible failure.
```

한 줄 요약: 오픈소스 formal로 contract를 닫는 과정에서 진짜로 부딪힌 함정 모음 —
yosys SVA(bind 무시/named property 미지원/async2sync), mutation 설계(identity
최적화·NBA 우선순위·자기 트리거 은폐·contract 구멍), formal 모델링(reset assume·
오버플로·비귀납·width·$past 가드), sim/TB(verilator pragma·NBA 읽기·scoreboard
off-by-one), 그리고 shell/git. 핵심 규칙: "심은 버그가 안 죽으면 RTL이 아니라
검증이 틀린 것."
