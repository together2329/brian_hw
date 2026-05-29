/* workspace-ssotx-status.tsx — strangler-fig sibling of workspace-ssot-extract.tsx.
 *
 * Owns the SSOT status + reviewer-markdown helper family:
 *   - ssotProgressStatusMap   (window.ATLAS_PROGRESS → key→status map)
 *   - ssotSectionStatus       (per-section status inference)
 *   - ssotStatusKey / ssotNeedsAttentionStatus / ssotStatusColor /
 *     ssotStatusGlyph         (status normalization + presentation)
 *   - ssotReviewMarkdown      (per-section reviewer markdown render)
 *
 * NO React components — pure functions. INERT mirror: legacy workspace.jsx
 * still serves the live app. These symbols are re-exported from
 * workspace-ssot-extract.tsx so the public contract is unchanged.
 *
 * Cross-module deps are imported from their canonical homes:
 *   - normalizeAtlasStatus            ← workspace-report-status
 *   - SSOT_REVIEW_FOCUS               ← workspace-ssotx-labels
 *   - ssotTitleFor / mdCell /
 *     summarizeSsotSection            ← workspace-ssot-extract
 * The extract↔status cycle is call-time only (these helpers invoke their
 * deps when called, not at module eval), so the ES-module cycle is safe.
 */
import { normalizeAtlasStatus } from './workspace-report-status';
import { SSOT_REVIEW_FOCUS } from './workspace-ssotx-labels';
import { ssotTitleFor, mdCell, summarizeSsotSection } from './workspace-ssot-extract';

export const ssotProgressStatusMap = (): Record<string, any> => {
  const data = window.ATLAS_PROGRESS || {};
  const selected = data.selected || (Array.isArray(data.modules) ? data.modules[0] : null) || {};
  const ssot = (((selected.progress || {}).ssot) || {});
  const rows = Array.isArray(ssot.sections) ? ssot.sections : [];
  return rows.reduce((acc: Record<string, any>, row: any) => {
    const key = row.key || row.id || row.section || row.name;
    if (key) acc[key] = row.status || row.state || row.approval || '';
    return acc;
  }, {});
};

export const ssotSectionStatus = (section: any, statusByKey: any): string => {
  const fromProgress = statusByKey[section.key];
  if (fromProgress) return String(fromProgress).toLowerCase();
  const body = section.text || '';
  if (/(approved|approval|status|state)\s*:\s*['"]?(approved|done|pass|ok|true)/i.test(body)) return 'approved';
  if (section.summary.gaps.length) return 'needs review';
  if (/(pending|blocked|draft|partial|todo|tbd)/i.test(body)) return 'pending';
  return 'review';
};

export const ssotStatusKey = (status: any): string => normalizeAtlasStatus(status);

export const ssotNeedsAttentionStatus = (status: any): boolean => {
  const s = ssotStatusKey(status);
  return ['pending', 'needs_review', 'draft', 'partial', 'todo', 'tbd', 'blocked', 'error', 'rejected', 'failed', 'fail']
    .includes(s);
};

export const ssotStatusColor = (status: any): string => {
  const s = ssotStatusKey(status);
  if (['approved', 'done', 'pass', 'ok'].includes(s)) return 'var(--ok)';
  if (['fail', 'failed', 'error', 'rejected', 'blocked'].includes(s)) return 'var(--err)';
  if (['pending', 'needs_review', 'draft', 'partial', 'todo', 'tbd'].includes(s)) return 'var(--warn)';
  return 'var(--fg-mute)';
};

export const ssotStatusGlyph = (status: any): string => {
  const s = ssotStatusKey(status);
  if (['approved', 'done', 'pass', 'ok'].includes(s)) return 'OK';
  if (ssotNeedsAttentionStatus(status)) return '!';
  return '·';
};

export const ssotReviewMarkdown = (section: any, status: any): string => {
  const title = ssotTitleFor(section.key);
  const summary = section.summary || summarizeSsotSection(section);
  const focus = SSOT_REVIEW_FOCUS[section.key] || [
    'Review that this section is specific enough for downstream generation.',
    'Check for missing constraints, ambiguous wording, and stale assumptions.',
  ];
  const rows: [string, any][] = [
    ['Status', status || 'review'],
    ['Source line', section.startLine],
    ['YAML lines', summary.lineCount],
    ['List items', summary.listItems],
    ['Nested groups', summary.groups.length ? summary.groups.join(', ') : '-'],
  ];

  const facts = summary.facts.length
    ? summary.facts.map((f: any) => `| \`${mdCell(f.key)}\` | ${mdCell(f.value)} |`).join('\n')
    : '| - | No compact key facts detected. Review raw section below. |';
  const listItems = summary.listPreview.length
    ? summary.listPreview.map((x: any) => `- ${x}`).join('\n')
    : '- No top-level list preview detected.';
  const gaps = summary.gaps.length
    ? summary.gaps.map((g: any) => `- Line ${g.line}: ${g.text}`).join('\n')
    : '- No obvious TBD, null, pending, or placeholder text detected.';

  return [
    `### ${title}`,
    '',
    `\`${section.key}\``,
    '',
    '| Review item | Value |',
    '| --- | --- |',
    rows.map(([k, v]) => `| ${mdCell(k)} | ${mdCell(v)} |`).join('\n'),
    '',
    '#### Reviewer Focus',
    focus.map((x: any) => `- ${x}`).join('\n'),
    '',
    '#### Key Facts',
    '| Field | Value |',
    '| --- | --- |',
    facts,
    '',
    '#### List Preview',
    listItems,
    '',
    '#### Review Flags',
    gaps,
  ].join('\n');
};
