#!/usr/bin/env bash
# benchmark_tick.sh — Record iteration timestamp to benchmark log
# Triggered: before_llm (every iteration)

LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
ITER="${HOOK_ITERATION:-?}"

echo "${TS} iter=${ITER}" >> "${LOG}"
