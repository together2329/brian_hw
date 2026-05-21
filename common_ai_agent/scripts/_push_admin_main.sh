#!/usr/bin/env bash
# Push the admin Raw DB + permissions commit to origin/main.
# User-authorized via the wrapping script invocation.

set -e

echo "[push-admin] verifying local main is ahead of origin/main..."
git fetch origin main
git log --oneline origin/main..main | head -5

echo "[push-admin] pushing to origin/main..."
git push origin main

echo "[push-admin] done. recent history:"
git log --oneline -3
