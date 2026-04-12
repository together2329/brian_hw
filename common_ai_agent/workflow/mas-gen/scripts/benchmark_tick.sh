#!/usr/bin/env bash
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
echo "${TS} iter=${HOOK_ITERATION:-?}" >> "${LOG}"
