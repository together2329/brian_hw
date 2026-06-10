# Headless Stage Validation Phase 2 — pulse_counter_hx (2026-06-10)

Phase-2 follow-up to [[stage-validation-pulse-counter-20260610]] and
[[stage-validation-reflections-20260610]]: run the SAME workflow headlessly on
a fresh IP (`pulse_counter_hx`, APB pulse counter authored from a new
requirement md) with a real LLM worker, and fix every machinery gap the run
exposes. Operator role = repair loop only (route gate rejections to the owning
artifact, never bypass).

**Result: full pipeline pass.** req → ssot-gen → fl-model-gen → cl-model-gen →
dual-fcov → equiv-goals → rtl-gen → lint → tb-gen → sim, scoreboard **57/57**,
sim stage PASS, 13 runs total (each run = one repair round).

## Model note

User asked for gpt-5.3-codex; the ChatGPT/Codex OAuth route rejects it
(HTTP 400 "The 'gpt-5.3-codex' model is not supported when using Codex with a
ChatGPT account" — gpt-5.3 also rejected). Substituted **gpt-5.5**; an OpenAI
API-key route would be needed for gpt-5.3-codex.

## Run ledger (what blocked, who owned it, what fixed it)

| # | Stage blocked | Cause | Repair (owner) |
|---|---|---|---|
| 1 | cl-model-gen | SSOT handshake_rules used undeclared `csr_*_accept` | rename to declared `pready` (SSOT) |
| 2 | rtl-gen | no locked req bundle (headless has no req-authoring stage) | adapt pc1 VCM bundle + `lock_requirement_set` (req) |
| 3 | cl-model-gen | re-authored SSOT invented `psel_pen_pwrite`/`pulse_rise`/`clear_req` | declare them as `derived_signals` (SSOT) |
| 4 | rtl-gen | headless req stage clobbered the locked approval_manifest | **machinery**: preserve `requirements_locked` manifest (`headless_workflow._copy_requirement`) |
| 5 | rtl-gen | behavioral contracts not projected into SSOT (`orphans=3`) | add `function_model.transactions[].contract_refs` (SSOT) |
| 6 | rtl-gen | packet `work_allowed=false` deadlock: contract-implementation gate draft-blocked a fresh IP | **machinery**: drop `locked_truth_contract_implementation` from `_DRAFT_BLOCKING_GATE_KINDS` (PASS still locked) |
| 7 | rtl-gen | verilator UNUSEDSIGNAL | LLM repair round (RTL) |
| 8 | rtl-gen | `.irq(irq_q)` port-map vs SSOT term `irq`; LLM answered with comments 2 rounds | **machinery**: connection checker follows continuous-assign chains (depth 2, both directions) |
| 9 | tb-gen | behavioral contracts not projected into cycle_model rows | add `cycle_model.handshake_rules[].contract_refs` (SSOT) |
| 10 | sim 40/57 | SSOT had **zero stimulus_machine_spec** (known stimulus-contract P0, headless reproduction) | author 8 timelines (SSOT) |
| 11 | sim 42/57 | FL got index-derived stimulus (pwdata=14) while timeline drove data=5; park killed level-holds; FL modeled clear strobe as persistent | **machinery**: mirror timeline final CSR access + assigns into FL stimulus; park honors timeline-final assigns. SSOT: clear_req_q post-tx = 0 |
| 12 | — | — | **57/57 PASS** |

## Machinery changes (general, regression-verified)

1. `src/headless_workflow.py` — `_copy_requirement` no longer overwrites a
   `requirements_locked` approval manifest; the markdown-copy proof moves to
   `headless_req_copy_manifest.json`. (Two writers, one filename, two schemas
   was the bug.)
2. `workflow/rtl-gen/scripts/derive_rtl_todos.py` —
   `locked_truth_contract_implementation` is no longer draft-blocking: it is
   closable only BY authoring RTL, so blocking drafts on it deadlocked every
   fresh IP that carries a locked req bundle (gpt-5.5 honestly refused to work
   under `work_allowed=false`). It stays in `_LOCKED_TRUTH_GATE_KINDS`, so
   rtl-gen PASS/signoff is still forbidden until implemented. Matches the
   pinned expectation draft=True/pass=False for fresh IPs (19/19 tests pass).
3. `workflow/rtl-gen/scripts/derive_rtl_todos.py` — connection-contract
   matching follows continuous-assign chains (`_assign_chain_links`, depth 2,
   both directions): `.irq(irq_q)` + `assign irq = irq_q;` is the same signal;
   an unrelated net still never reaches the expected term. mctp stash-compare:
   baseline open=4 (pre-existing), with fix open=3 — one contract honestly
   closed, none loosened.
4. `workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py` — two machine-spec
   runner fixes: (a) the timeline's last written DATA and the EVENT value of
   each assigned input are mirrored into the FL stimulus (CL already had csr
   mirroring; FL didn't — so FL applied pwdata=14 while the DUT saw 1, a
   silent expected-vs-driven desync); (b) the post-spec idle park no longer
   overrides inputs the timeline explicitly left assigned (a level-hold like
   `pulse_in=1` must survive to the sample or synchronizer-state goals fail
   by construction).
   Two regression-caught refinements shaped (a): mirroring `op`/`addr` from a
   trailing `csr_read` made the FL re-resolve the goal to a READ transaction
   (pc1 EQ_TIMING_ORDERING 31/31→29/31) — only write DATA is mirrored, kind
   resolution stays pinned to the donor; and FL needs the EVENT value of a
   pulse assign (the non-idle 1), not the resting value the park uses (the
   trailing 0). Final state: pc1 31/31 AND hx 57/57 on the same template.

## Worker-design findings (feed into orchestrator/worker)

1. **Headless needs a req-authoring/lock stage.** The req stage only copies
   markdown; nothing authors/locks the VCM bundle (`/draft-req`+`/finalize-req`
   territory), so the pipeline dies late at rtl-gen's authority gate.
2. **ssot-gen prompt must carry the locked-truth projection contract.** Three
   separate stalls (run 1, 3 symbol contract; run 5 function_model projection;
   run 9 cycle_model projection; run 10 stimulus specs) are all "the model
   didn't know SSOT must project locked truth". Inject: contract-ID list +
   projection rules (`transactions[].contract_refs`, cycle rows
   `contract_refs`, `stimulus_machine_spec` per transaction, symbol
   declaration channels).
3. **The runner needs an outer retry loop.** Each invocation does bounded
   repair rounds then exits FAIL with "queued rtl-gen repair"; something must
   re-invoke the failed stage (this session: me, 13 times).
4. **Repair prompts need action semantics.** gpt-5.5 answered a port-map
   diagnostic with comments two rounds running; the diagnostic never said
   "change the port-map expression or rename the net".
5. **Gate-as-work-queue held.** Every one of the 13 stalls was an actionable
   gate message; zero silent passes observed in the headless path; the model
   itself refused to fabricate under a no-work policy (run 6) — the honesty
   machinery works on a real LLM worker.

Related: [[stage-validation-pulse-counter-20260610]],
[[stage-validation-reflections-20260610]],
[[workflow-improvement-candidates]],
[[orchestrator-headless-worker-feedback]], [[verification-contract-model]].
