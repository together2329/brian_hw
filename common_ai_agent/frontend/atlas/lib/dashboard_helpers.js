// dashboard_helpers.js — Dashboard openIp payload builder.
// Works as both an ES module (vitest/Node) and a plain <script> (browser UMD).

export function buildOpenIpPayload(row, workflowValue) {
  const wf = workflowValue(row);
  const payload = { id: row.session_id || '', ip: row.ip };
  if (wf) payload.workflow = wf;
  return payload;
}

if (typeof window !== 'undefined') {
  window.AtlasDashboardHelpers = { buildOpenIpPayload };
}
