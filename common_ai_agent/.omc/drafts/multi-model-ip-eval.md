# Plan — Multi-Model HW-IP Generation Benchmark

> **Status**: DRAFT v2 — Q1 (model slugs) confirmed via `.env`. Q2/Q3 still open.

## Confirmed via `.env`

The repo already has 3 LLM profiles with full BASE_URL+API_KEY+MODEL trios.
Profile switching is via `--model <name>` CLI flag (`src/main.py:2500-2522`)
which atomically swaps the trio in-place — far cleaner than per-task env vars.

| Profile | Model slug | Endpoint |
|---|---|---|
| `deepseek` | `deepseek-v4-pro` | `https://api.deepseek.com` |
| `glm` | `glm-5.1` | `https://api.z.ai/api/coding/paas/v4` (Z.ai direct, not OpenRouter) |
| `kimi` | `kimi-2.6` | `https://inference.canopywave.io/v1` |

**Worker dispatch becomes**:
```bash
python3 src/main.py --model deepseek -w <workflow> "/<command> <ip>"
python3 src/main.py --model glm      -w <workflow> "/<command> <ip>"
python3 src/main.py --model kimi     -w <workflow> "/<command> <ip>"
```

So **no env-var jugglery, no openrouter slugs needed**. The earlier
`PRIMARY_MODEL=...` recipe in this draft is obsolete — replaced below.

## Requirements Summary

Evaluate the `common_ai_agent` system's hardware-IP generation chain
(`/ssot-gen` → `/rtl-gen` → `/sim`) by running it across **3-5 IPs** with
**3 different LLMs** (deepseek, glm-x.x, kimi). Produce a comparison matrix:
per-IP × per-model × per-stage outcomes (success/fail, time, cost, quality
score).

The system already supports per-task model selection via env vars
(`PRIMARY_MODEL`, `SUBAGENT_LOW_MODEL`, `SUBAGENT_HIGH_MODEL`,
`MODEL_NAME`) all using the OpenRouter slug format
(`openrouter/<vendor>/<model>`). `core/agent_config.py:295-297` reads them
at agent boot. No code changes required to swap models — just env override
per worker.

## Acceptance Criteria

A successful run must produce:

1. `.benchmark/multi_model/<model>/<ip>/{ssot.yaml,rtl/*.sv,sim/<ip>.vcd,report.md}`
   for every (model, ip) cell in the matrix that completed.
2. `.benchmark/multi_model/SUMMARY.md` — single table with rows = IPs,
   columns = models, cells = `pass | fail` + headline metric (RTL LoC,
   sim outcome, wall-clock minutes, $-cost).
3. Each "pass" cell must satisfy:
   - SSOT: ≥ 100 lines AND `validate-yaml.sh` rc=0
   - RTL: ≥ 1 .sv file, `verilator --lint-only` 0 errors
   - SIM: at least one tb_*.sv compiled and `vvp` exit 0
4. Verifiable artifacts via the existing `/lint` and `/sim` workflows
   (no custom validation).

## Implementation Steps

### Stage 0 — Pre-flight (one-time, ~10 min)

| Step | File / Command | Verifiable |
|---|---|---|
| 0.1 Confirm OpenRouter API key is set | `grep -E "OPENROUTER_API_KEY" ~/.zshrc ~/.bashrc; printenv OPENROUTER_API_KEY \| head -c 10` | non-empty |
| 0.2 Pin exact OpenRouter slugs for the 3 models | manual edit of `.benchmark/multi_model/models.txt` | 3 lines, each `openrouter/...` |
| 0.3 Pick 3-5 IPs (mix mature + stub recommended) | edit `.benchmark/multi_model/ips.txt` | 3-5 lines, IP names |
| 0.4 Smoke test each model with one trivial /sim run on `counter` | `python3 src/main.py --model <profile> -w sim "/sim counter"` for `<profile> ∈ {deepseek, glm, kimi}` | each model: rc=0 |

### Stage 1 — Per-(model, IP) generation runs

For each `(model, ip)` cell, with `model ∈ {deepseek, glm, kimi}`:

```bash
OUTDIR=".benchmark/multi_model/${model}/${ip}"
mkdir -p "$OUTDIR"

# Stage 1a — SSOT (only when stub ≤ 50 lines; mature IPs skip if Q3=α)
python3 src/main.py --model "$model" -w ssot-gen "/new-ip $ip" 2>&1 \
  | tee "$OUTDIR/ssot.log"

# Stage 1b — RTL gen
python3 src/main.py --model "$model" -w rtl-gen "/ssot-rtl $ip" 2>&1 \
  | tee "$OUTDIR/rtl.log"

# Stage 1c — sim
python3 src/main.py --model "$model" -w sim "/sim $ip" 2>&1 \
  | tee "$OUTDIR/sim.log"

# Snapshot artifacts and metrics
cp "$ip/yaml/$ip.ssot.yaml" "$OUTDIR/ssot.yaml" 2>/dev/null
cp -r "$ip/rtl"             "$OUTDIR/rtl"        2>/dev/null
cp "$ip/sim/"*.vcd          "$OUTDIR/"           2>/dev/null
```

**Important**: each IP's `yaml/`, `rtl/`, `sim/` directories must be
**reset between models** so the next model starts from the same baseline.
Use `git stash` per IP per model, or copy the IP dir into the per-model
output area first and run from there.

### Stage 2 — Parallel orchestration via OMC team mode

Two viable team-mode strategies (pick at user-confirm step):

**Option A — `/omc-teams 3:claude` per IP** (sequential model sweep):
- Each worker takes one IP, sweeps all 3 models inside it.
- 3 IPs × 1 worker = 3 tmux panes, each does 3 model runs serially.
- Pro: minimal contention, clear pane → IP mapping.
- Con: serial within worker; total time ~3× one (model, IP) run.

**Option B — `/omc-teams 3:claude` per MODEL** (parallel model sweep):
- Each worker pins one model and does all IPs.
- 3 workers × 3-5 IPs serial within each.
- Pro: clean per-model time/cost accounting.
- Con: workers compete for filesystem (per-IP `yaml/rtl/sim` dirs).
  Mitigation: each worker writes to `.benchmark/multi_model/<model>/<ip>/`
  isolated tree, never to the shared `<ip>/` source-of-truth.

→ **Recommended: Option B with isolated per-model worktrees.**

### Stage 3 — Metrics aggregation (~15 min)

Single bash + python script `.benchmark/multi_model/aggregate.sh` walks
each `<model>/<ip>/` and emits:

- `ssot_lines`: `wc -l ssot.yaml`
- `rtl_files`: count of `.sv` files
- `rtl_loc`: sum of lines
- `lint_errors`: `verilator --lint-only` count
- `sim_pass`: `grep -c PASS sim.log`
- `wall_clock_sec`: parsed from log timestamps
- `usd_cost`: parsed from `[cost]` lines emitted by `core/llm_client.py`

Writes `SUMMARY.md` with one big markdown table.

### Stage 4 — Qualitative diff (optional, ~30 min)

For 1 hand-picked IP (suggest `gpio_pad` since we already have a known-good
baseline), diff the generated RTL across models with
`diff -u <model_a>/rtl/ <model_b>/rtl/`. Capture style, naming,
parameter handling differences.

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| OpenRouter rate-limit on 3-way concurrent | Medium | Stagger workers by 30s startup. Per-model retry on 429 (already in `src/llm_client.py:1480` retry logic). |
| Model slug mismatch (e.g. "glm 5.1" doesn't exist) | High | Open Question Q1 below — confirm exact slugs before any run. |
| Stub IPs (cci550, ddr_phy etc.) are too vague — model can't generate meaningful RTL | Medium | Mix mature + stub: include `gpio_pad` (361L, known-good) as anchor; treat stubs as "stretch" cases that may legitimately fail across all models. |
| Per-IP source-of-truth corruption between runs | High | Write to `.benchmark/multi_model/<model>/<ip>/` only; never let workers mutate `<ip>/yaml/`. **Wrap each workflow call in a per-worker IP-copy shim.** |
| Cost overrun ($X to >$50) | Low | Set per-run hard cap via `.config` `MAX_COST_USD`. Total estimate: 3 models × 5 IPs × ~$0.50/run ≈ **$7.50** if no retry storms. |
| `/sim` requires synthesizable RTL — model A passes lint but RTL is unsynthesizable, sim fails | High | Acceptance criterion explicitly separates lint and sim — partial pass is recorded. |

## Verification Steps

```bash
# 1. Smoke test on counter (smallest IP) across all 3 profiles
for m in deepseek glm kimi; do
  python3 src/main.py --model "$m" -w sim "/sim counter"
done
# Expect: each profile completes with rc=0

# 2. Full matrix run via /omc-teams Option B
/oh-my-claudecode:omc-teams 3:claude "$(cat .benchmark/multi_model/run_per_model.sh)"

# 3. Aggregate
bash .benchmark/multi_model/aggregate.sh

# 4. Verify summary
cat .benchmark/multi_model/SUMMARY.md
# Expect: 3-5 IP rows × 3 model columns, each cell pass/fail + headline metric
```

## Open Questions (block plan promotion until answered)

### Q1 — Model slugs ✓ RESOLVED via `.env`

`.env` defines 3 LLM profiles: `deepseek` (`deepseek-v4-pro`),
`glm` (`glm-5.1`, Z.ai direct), `kimi` (`kimi-2.6`). Switch via
`--model <profile>` CLI flag at `src/main.py:2500-2522`. No OpenRouter
needed.

### Q2 — Which 3-5 IPs?

Available locally:

| IP | SSOT lines | Has RTL | Has sim | Suitable for |
|---|---:|---|---|---|
| `counter` | 20 | ✓ | ✓ | smoke test, baseline |
| `gpio_pad` | 361 | ✓ | ✓ | known-good anchor (Phase A validated) |
| `uart` | 228 | ✓ | ✓ | mid-complexity anchor |
| `spi_master` | 8 | ✗ | ✓ | from-scratch eval |
| `cci550` | 7 | ✗ | ✗ | from-scratch eval (cache coherent interconnect, hard) |
| `cortexa15_0` | 7 | ✗ | ✗ | from-scratch eval (CPU core, very hard) |
| `ddr_phy` | 6 | ✗ | ✗ | from-scratch eval (high-speed PHY, analog, very hard) |
| `gic_400` | 7 | ✗ | ✗ | from-scratch eval (interrupt controller, medium) |

**Recommended set (5)**: `counter`, `gpio_pad`, `uart`, `spi_master`,
`gic_400` — covers smoke + 2 known-goods + 2 from-scratch.

**Recommended set (3)**: `counter`, `gpio_pad`, `gic_400` — minimum viable.

### Q3 — Source-of-truth handling

When evaluating mature IPs (`counter`, `gpio_pad`, `uart`), should the
model:

- **(α) Re-generate from existing SSOT** — input is the 100-360L SSOT, output is fresh RTL. Compares model's RTL synthesis quality against existing baseline.
- **(β) Re-generate from stub** — wipe SSOT down to bare `top_module` line, ask model to expand. Compares model's spec-elaboration ability.
- **(γ) Both per IP** — α and β separately, double the runs.

**Recommended**: **(α)** for mature IPs, default behavior for stubs (no
SSOT to wipe). Doubles runs only if user explicitly wants spec-elaboration
quality measurement.

## Estimated Cost & Time (with recommended set)

| | Time | Cost |
|---|---|---|
| Pre-flight | 10 min | $0.05 |
| Stage 1 — 5 IPs × 3 models, sequential per worker, 3 workers parallel | ~90 min | ~$7.50 |
| Stage 3 aggregation | 15 min | $0 |
| Stage 4 qualitative diff (optional) | 30 min | $0 |
| **Total** | **~2 h** | **< $10** |

## Plan Promotion Checklist

Before moving from `.omc/drafts/` to `.omc/plans/`:

- [ ] Q1 model slugs confirmed
- [ ] Q2 IP set confirmed (3 vs 5)
- [ ] Q3 SOT handling confirmed (α / β / γ)
- [ ] User chooses team-mode strategy: A (per-IP) or B (per-MODEL)
- [ ] Cost cap set (default $10) and per-run timeout set (default 30 min)
