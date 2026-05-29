# Worker / Orchestrator LLM model switch (glm → gpt-5.5 via Codex OAuth)

Runbook for switching ATLAS off the cost-optimized glm/deepseek worker models
onto `gpt-5.5` (≈8× faster per call in measured comparison), and verifying it
end-to-end without breaking the running pipeline.

> **Why this is delicate.** The model name and the *auth route* are coupled.
> With `LLM_PROFILE=glm`, Codex OAuth is **deactivated at boot**, so any `gpt-*`
> selection routes to the z.ai endpoint → **HTTP 400 / no reply**. The switch is
> therefore *model variables + auth activation together*, not just renaming models.

## What changed (already done in `.env`)

`.env` (gitignored — never committed) had these 17 model variables flipped to
`gpt-5.5`:

- `PRIMARY_MODEL`, `SECONDARY_MODEL`, `SUBAGENT_LOW_MODEL`, `SUBAGENT_HIGH_MODEL`
- `ATLAS_ORCHESTRATOR_MODEL`
- `ATLAS_WORKER_MODEL_*` (all 12: ssot_gen, fl_model_gen, rtl_gen, lint, tb_gen,
  sim, coverage, sim_debug, syn, sta, pnr, sta_post)

`LLM_PROFILE=glm` and all `PROFILE_*_API_KEY` lines were **left untouched**.
Resolution path: `_worker_model_for()` in `src/atlas_api_jobs.py:435` reads
`ATLAS_WORKER_MODEL_<SUFFIX>` first, so these `.env` values are authoritative.

Backup of the pre-switch `.env`: `/tmp/atlas_env_backup_glm_20260529`.

## Activation (requires your environment — restart + OAuth)

The running server holds the **boot-time** model in memory, so the `.env` edit
takes effect only on restart, and only if Codex OAuth is activated:

1. Set in `.config`:  `USE_OPENCODE_OAUTH=true`
2. Restart the server with the model flag (this overrides the `glm` profile and
   makes config fall through to Codex OAuth — the documented recipe in `.env`):

   ```
   python atlas_ui.py ... --model gpt-5.5
   ```

> Without **both** steps, restarting will route every worker's `gpt-5.5` to z.ai
> → HTTP 400 (worse than slow). Do both, or roll back.

## Verify

Read-only + free probe (exits 0 on success, 2 if restart still pending):

```bash
scripts/atlas_model_smoke.sh
# HOST=http://127.0.0.1:3000 EXPECT=gpt-5.5 scripts/atlas_model_smoke.sh
```

- **PASS signal (automated):** `orchestrator.model == gpt-5.5` and every worker
  `configured_model == gpt-5.5`, no `model_mismatch`.
- **Decisive signal (manual):** run ONE workflow from the UI (e.g. `ssot-gen`),
  then confirm its job log has **no `HTTP 400` / `no reply`** and `total_runs`
  increments on `/api/orchestrator/workers`. `worker_running_models` should show
  `gpt-5.5` once a call lands.

## Rollback

```bash
cp /tmp/atlas_env_backup_glm_20260529 .env
# then restart WITHOUT --model gpt-5.5  → back to glm/deepseek
```

## Cost / rate note

Codex OAuth bills against your ChatGPT plan. All 12 workers on `gpt-5.5` in
parallel can hit rate limits. If so, keep interactive workflows
(`ssot_gen`, orchestrator, chat) on `gpt-5.5` and move the heavy batch EDA
workers (`rtl_gen`, `sim`, `lint`, `syn`, `sta`, `pnr`, `sta_post`) back to a
cheaper model (`deepseek-v4-pro`) — a surgical split that keeps ~90% of the
felt speed-up at a fraction of the cost.
