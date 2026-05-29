#!/usr/bin/env bash
# atlas_model_smoke.sh — verify the ATLAS worker/orchestrator LLM model after a
# model switch (e.g. glm -> gpt-5.5 via Codex OAuth). READ-ONLY + free: it only
# hits GET probes and the free orchestrator status fast-path, never spends an LLM
# call. The decisive "does gpt answer without HTTP 400" check is a manual run
# documented in doc/wiki/worker-model-gpt-switch.md.
#
# Usage:
#   scripts/atlas_model_smoke.sh                 # defaults: localhost:3000, /tmp/atlas_cookie, expect gpt-5.5
#   HOST=http://127.0.0.1:3000 EXPECT=gpt-5.5 scripts/atlas_model_smoke.sh
#
# Exit codes:
#   0  orchestrator.model == EXPECT  (boot picked up the switch — PASS)
#   2  orchestrator.model != EXPECT  (server still on old model — restart pending)
#   1  server unreachable / probe error
set -euo pipefail

HOST="${HOST:-http://127.0.0.1:3000}"
COOKIE_FILE="${COOKIE_FILE:-/tmp/atlas_cookie}"
EXPECT="${EXPECT:-gpt-5.5}"

if [[ ! -f "$COOKIE_FILE" ]]; then
  echo "✗ cookie file not found: $COOKIE_FILE" >&2
  exit 1
fi
CK="$(cat "$COOKIE_FILE")"

echo "== ATLAS model smoke =="
echo "host=$HOST  expect=$EXPECT"
echo

# 1) health
if ! curl -fsS -m 5 -b "atlas_session=$CK" "$HOST/healthz" >/dev/null 2>&1; then
  echo "✗ /healthz unreachable — is the server running on $HOST ?" >&2
  exit 1
fi
echo "✓ /healthz ok"
echo

# 2) orchestrator + worker model state (authoritative)
WORKERS_JSON="$(curl -fsS -m 8 -b "atlas_session=$CK" "$HOST/api/orchestrator/workers")"

echo "$WORKERS_JSON" | EXPECT="$EXPECT" python3 -c '
import sys, json, os
expect = os.environ["EXPECT"]
d = json.load(sys.stdin)
o = d.get("orchestrator", {}) or {}
orch_model = o.get("model")
print("orchestrator.model :", orch_model, "(profile:", o.get("profile"), ")")
print()
print("%-14s %-10s %-12s %-9s %-5s %s" % ("workflow","model","configured","mismatch","runs","running"))
bad_cfg = []
for w in d.get("workers", []):
    cfg = w.get("configured_model")
    if cfg != expect:
        bad_cfg.append(w.get("workflow"))
    print("%-14s %-10s %-12s %-9s %-5s %s" % (
        w.get("workflow"), w.get("model"), cfg,
        w.get("model_mismatch"), w.get("total_runs"), w.get("worker_running_models")))
print()
if bad_cfg:
    print("⚠ workers whose configured_model != %s: %s" % (expect, ", ".join(bad_cfg)))
else:
    print("✓ all workers configured_model == %s (.env is correct)" % expect)

# exit signal via marker line parsed by the shell wrapper
print("ORCH_MODEL=%s" % (orch_model or ""))
' | tee /tmp/.atlas_smoke_out

echo
ORCH_MODEL="$(grep '^ORCH_MODEL=' /tmp/.atlas_smoke_out | tail -1 | cut -d= -f2)"
rm -f /tmp/.atlas_smoke_out

if [[ "$ORCH_MODEL" == "$EXPECT" ]]; then
  echo "✓ PASS: orchestrator.model == $EXPECT (boot picked up the switch)."
  echo "  Next (manual, decisive): run ONE workflow from the UI, then check its job log"
  echo "  has no 'HTTP 400' / 'no reply' — see doc/wiki/worker-model-gpt-switch.md."
  exit 0
else
  echo "✗ PENDING: orchestrator.model is '$ORCH_MODEL', expected '$EXPECT'."
  echo "  The running server still holds the OLD boot model. To activate the switch:"
  echo "    1) set USE_OPENCODE_OAUTH=true in .config"
  echo "    2) restart the server with:  --model $EXPECT"
  echo "  Rollback if gpt errors (z.ai 400): cp /tmp/atlas_env_backup_glm_20260529 .env  (then restart without --model)"
  exit 2
fi
