#!/usr/bin/env bash
# Fast-forward merge feat_ssot_preview into main and push.
# User-authorized via the wrapping script invocation — see PR/discussion.

set -e

echo "[ff-merge] stashing local WIP (if any)..."
git stash push -u -m "wip before ff merge ssot_preview" 2>/dev/null || true

echo "[ff-merge] checking out main..."
git checkout main

echo "[ff-merge] fast-forward merging feat_ssot_preview..."
git merge --ff-only feat_ssot_preview

echo "[ff-merge] pushing to origin/main..."
git push origin main

echo "[ff-merge] restoring stash (if any)..."
git stash pop 2>/dev/null || echo "[ff-merge] no stash to pop"

echo "[ff-merge] done. recent history:"
git log --oneline -5
