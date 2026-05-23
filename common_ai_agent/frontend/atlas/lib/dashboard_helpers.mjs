// dashboard_helpers.mjs — ES module twin of dashboard_helpers.js for vitest.

export function buildOpenIpPayload(row, workflowValue) {
  const wf = workflowValue(row);
  const payload = { id: row.session_id || '', ip: row.ip };
  if (wf) payload.workflow = wf;
  return payload;
}
