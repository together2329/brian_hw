#!/bin/bash
# post_session.sh — Save spec review session summary on session end

RESULTS_DIR="${BENCHMARK_LOG}/sessions"
mkdir -p "${RESULTS_DIR}"

SUMMARY_FILE="${RESULTS_DIR}/session_$(date +%Y%m%d_%H%M%S).txt"

echo "=== Spec Review Session ===" > "${SUMMARY_FILE}"
echo "Workspace : ${HOOK_WORKSPACE}" >> "${SUMMARY_FILE}"
echo "Date      : $(date)" >> "${SUMMARY_FILE}"
echo "Todo      : ${HOOK_TODO_INDEX} — ${HOOK_TODO_CONTENT}" >> "${SUMMARY_FILE}"
echo "" >> "${SUMMARY_FILE}"
echo "Session log saved to: ${SUMMARY_FILE}"
