// workers_panel_logic.mjs — ES module twin of workers_panel_logic.js for vitest.

export function summarizeWorkers(list) {
  const total = list.length;
  const upCount = list.filter(w => String(w.status || '') === 'ok').length;
  return { total, upCount };
}

export function workerTone(w) {
  const s = String(w.status || '');
  if (s === 'ok' && Number(w.running_count || 0) > 0) return 'active';
  if (s === 'ok') return 'done';
  if (s === 'mismatch') return 'err';
  return 'pending';
}

export function portFromUrl(url) {
  const m = String(url || '').match(/:(\d+)(?:\/|$)/);
  return m ? m[1] : '';
}
