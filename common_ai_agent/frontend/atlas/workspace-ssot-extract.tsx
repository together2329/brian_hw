/* workspace-ssot-extract.tsx — strangler-fig migration slice of workspace.jsx.
 *
 * Owns the pure SSOT YAML parsing/extraction layer:
 *   - SSOT_SECTION_LABELS / SSOT_REVIEW_FOCUS / SSOT_DIGEST_VIEWS constants.
 *   - Scenario, reference-token, and linkify builders.
 *   - The YAML block/section/field parser family (splitSsotSections,
 *     listBlocksFrom*, mapBlocksFrom*, fieldFromText, blockField, …).
 *   - IO / interface / feature / submodule / module-contract / register /
 *     FSM extractors.
 *   - Digest-view source mapping + SSOT status helpers.
 *
 * NO React components — all pure data functions + label constants (one helper,
 * linkifyReferences, returns JSX chips). INERT mirror: legacy workspace.jsx
 * still serves the live app; public exports are consumed by sibling
 * workspace-*.tsx modules and the root composer.
 */
// Reference-token + linkify layer (the only JSX-bearing group) moved to
// workspace-ssotx-references.tsx. Re-exported here so the public contract is
// unchanged; this module is now JSX-free (no react import needed).
export {
  buildReferenceTokens,
  _refKindColor,
  _viewIdForRefKind,
  linkifyReferences,
} from './workspace-ssotx-references';

// Constant tables moved to workspace-ssotx-labels.tsx (window.SSOT_SECTION_LABELS
// bridge executes there). Re-exported here so the public contract is unchanged.
// SSOT_DIGEST_VIEWS is also re-exported below, next to its original position.
export { SSOT_SECTION_LABELS, SSOT_REVIEW_FOCUS, SSOT_DIGEST_VIEWS } from './workspace-ssotx-labels';
import { SSOT_SECTION_LABELS, SSOT_DIGEST_VIEWS } from './workspace-ssotx-labels';

// Status + reviewer-markdown helpers moved to workspace-ssotx-status.tsx.
// Re-exported here so the public contract is unchanged.
export {
  ssotProgressStatusMap,
  ssotSectionStatus,
  ssotStatusKey,
  ssotNeedsAttentionStatus,
  ssotStatusColor,
  ssotStatusGlyph,
  ssotReviewMarkdown,
} from './workspace-ssotx-status';

// ── Multi-cycle scenarios ────────────────────────────────────────
// Pull named scenarios from cycle_model.scenarios / function_model.scenarios.
// Each scenario is { name, summary, steps:[{cycle, action, fl_state, cl_state, signals:{key:value}}] }.
// When the SSOT lacks explicit scenarios, synthesize one from
// function_model.transactions + cycle_model.pipeline so the user still
// gets a "what does this IP do, cycle by cycle" view.
export const _scenarioStepsFromBlocks = (blocks: any[]): any[] => blocks.map((b: any, idx: number) => {
  const cycle = Number(blockField(b, 'cycle') || blockField(b, 't') || idx);
  const signals: Record<string, any> = {};
  const sigBlocks = listBlocksFromText(b.text, 'signals');
  for (const s of sigBlocks) {
    const name = blockField(s, 'name');
    const value = blockField(s, 'value');
    if (name) signals[name] = value;
  }
  // Inline "signals: { ... }" mapping fallback
  const sigMap = fieldFromText(b.text, 'signals', 1200);
  if (sigMap && !sigBlocks.length) {
    const re = /([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*([^,;\n]+)/g;
    let m: RegExpExecArray | null;
    while ((m = re.exec(sigMap)) !== null) {
      signals[m[1].trim()] = m[2].trim();
    }
  }
  return {
    cycle: Number.isFinite(cycle) ? cycle : idx,
    action: blockField(b, 'action', 320) || blockField(b, 'description', 320) || blockField(b, 'event', 320) || '',
    fl_state: blockField(b, 'fl_state') || blockField(b, 'function_state') || blockField(b, 'fl') || '',
    cl_state: blockField(b, 'cl_state') || blockField(b, 'cycle_state') || blockField(b, 'cl') || blockField(b, 'stage') || '',
    signals,
    notes: blockField(b, 'notes', 200),
  };
});

export const _scenarioFromBlock = (block: any): any => ({
  name: blockField(block, 'name') || blockField(block, 'id') || 'scenario',
  summary: blockField(block, 'summary', 400) || blockField(block, 'description', 400) || '',
  steps: _scenarioStepsFromBlocks(listBlocksFromText(block.text, 'steps')),
});

export const extractScenarios = (sections: any[]): any[] => {
  const cycleSection = sectionByKey(sections, 'cycle_model');
  const fnSection = sectionByKey(sections, 'function_model');
  const testSection = sectionByKey(sections, 'test_requirements');
  const declared = [
    ...listBlocksFromSection(cycleSection, 'scenarios'),
    ...listBlocksFromSection(fnSection, 'scenarios'),
    ...listBlocksFromSection(testSection, 'scenarios'),
  ].map(_scenarioFromBlock).filter((s: any) => s.steps.length);
  if (declared.length) return declared;
  // Auto-synthesize: one scenario per transaction, walking the pipeline.
  const transactions = listBlocksFromSection(fnSection, 'transactions');
  const pipeline = listBlocksFromSection(cycleSection, 'pipeline');
  if (!transactions.length || !pipeline.length) return [];
  return transactions.slice(0, 8).map((tx: any, ti: number) => {
    const txName = blockField(tx, 'id') || blockField(tx, 'name') || `tx_${ti + 1}`;
    const summary = blockField(tx, 'description', 360) || blockField(tx, 'purpose', 360) || '';
    const steps = pipeline.map((stage: any, si: number) => ({
      cycle: si,
      action: `${blockField(stage, 'stage') || blockField(stage, 'name') || `stage_${si}`}: ${blockField(stage, 'action', 240) || ''}`,
      fl_state: txName,
      cl_state: blockField(stage, 'stage') || blockField(stage, 'name') || `stage_${si}`,
      signals: {},
      notes: blockField(stage, 'notes', 160) || '',
    }));
    return { name: txName, summary, steps, synthesized: true };
  });
};

// ── reference tokens + linkify ───────────────────────────────────
// buildReferenceTokens / _refKindColor / _viewIdForRefKind / linkifyReferences
// moved to workspace-ssotx-references.tsx and re-exported from the head of
// this file (kept the JSX out of this otherwise pure-data module).

export const ssotPathOf = (entry: any): string => typeof entry === 'string' ? entry : (entry && entry.path) || '';

export const ssotTitleFor = (key: any): string => {
  const raw = String(key || '').trim();
  if (!raw) return 'Untitled Section';
  if (SSOT_SECTION_LABELS[raw]) return SSOT_SECTION_LABELS[raw];
  return raw.split(/[_\-.]+/).filter(Boolean)
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ');
};
(window as any).ssotTitleFor = ssotTitleFor;  // Phase 13a: consumed by ssot-doc.jsx

export const trimSsotValue = (value: any, max = 130): string => {
  const text = String(value ?? '').replace(/^['"]|['"]$/g, '').replace(/\s+/g, ' ').trim();
  if (!text) return '';
  return text.length > max ? text.slice(0, max - 1) + '...' : text;
};

export const mdCell = (value: any): string => {
  const text = trimSsotValue(value, 220).replace(/\|/g, '\\|');
  return text || '-';
};

export const stripSsotYamlComment = (line: any): string => {
  const text = String(line ?? '');
  let single = false;
  let double = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const prev = i > 0 ? text[i - 1] : '';
    if (ch === "'" && !double) {
      single = !single;
      continue;
    }
    if (ch === '"' && !single && prev !== '\\') {
      double = !double;
      continue;
    }
    if (ch === '#' && !single && !double && (i === 0 || /\s/.test(prev))) {
      return text.slice(0, i).trimEnd();
    }
  }
  return text;
};

export const ssotPreviewLines = (text: any): string[] => String(text || '').split(/\r?\n/).map(stripSsotYamlComment);

export const splitSsotSections = (content: any): any[] => {
  const lines = ssotPreviewLines(content);
  const sections: any[] = [];
  let current: any = null;
  const push = () => {
    if (!current) return;
    const text = current.lines.join('\n').trimEnd();
    if (text.trim()) {
      const section: any = { ...current, text, lineCount: current.lines.length };
      section.summary = summarizeSsotSection(section);
      sections.push(section);
    }
  };

  lines.forEach((line: string, idx: number) => {
    const m = line.match(/^([A-Za-z_][A-Za-z0-9_.-]*):(?:\s*(.*))?$/);
    if (m) {
      push();
      current = { key: m[1], value: (m[2] || '').trim(), startLine: idx + 1, lines: [line] };
    } else if (current) {
      current.lines.push(line);
    }
  });
  push();
  return sections;
};

export const summarizeSsotSection = (section: any): any => {
  const lines = ssotPreviewLines(section.text);
  const facts: any[] = [];
  const groups: string[] = [];
  const listPreview: string[] = [];
  const gaps: any[] = [];
  let listItems = 0;

  lines.forEach((line: string, idx: number) => {
    const list = line.match(/^\s*-\s+(.+)/);
    if (list) {
      listItems += 1;
      if (listPreview.length < 8) listPreview.push(trimSsotValue(list[1], 180));
    }

    const group = line.match(/^\s{2}([A-Za-z0-9_.-]+):\s*(?:#.*)?$/);
    if (group && !groups.includes(group[1]) && groups.length < 12) groups.push(group[1]);

    const fact = line.match(/^\s{2,}([A-Za-z0-9_.-]+):\s*(.+?)\s*$/);
    if (fact && facts.length < 12) {
      const value = trimSsotValue(fact[2]);
      if (value && !['|', '>', '{}', '[]'].includes(value)) facts.push({ key: fact[1], value });
    }

    if (/\b(TBD|TODO|FIXME|unknown|placeholder|pending|null|assumption|unspecified)\b/i.test(line)) {
      const cleaned = trimSsotValue(line, 220);
      if (cleaned && gaps.length < 10) gaps.push({ line: section.startLine + idx, text: cleaned });
    }
  });

  if (section.value && facts.length < 12) facts.unshift({ key: section.key, value: section.value });
  return { facts, groups, listItems, listPreview, gaps, lineCount: lines.length };
};

export const rxEscape = (text: any): string => String(text || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export const indentOf = (line: any): number => (String(line || '').match(/^\s*/) || [''])[0].length;

export const stripYamlScalar = (value: any): string => {
  let text = stripSsotYamlComment(value).trim();
  text = text.replace(/^['"]|['"]$/g, '');
  return text.replace(/\s+/g, ' ').trim();
};

export const ssotValuePresent = (value: any): boolean => {
  const text = stripYamlScalar(value);
  return !!text && !/^(false|none|n\/a|na|tbd|todo|unknown|placeholder|null|\[\]|\{\})$/i.test(text);
};

export const formatBitRange = (value: any): string => {
  const text = stripYamlScalar(value);
  if (!text) return '';
  const pair = text.match(/^\[?\s*(\d+)\s*(?:,|:|-|\s+)\s*(\d+)\s*\]?$/);
  if (pair) return pair[1] === pair[2] ? pair[1] : `${pair[1]}:${pair[2]}`;
  const single = text.match(/^\[?\s*(\d+)\s*\]?$/);
  return single ? single[1] : text;
};

export const fieldFromText = (text: any, key: any, max = 260): string => {
  const lines = ssotPreviewLines(text);
  const rx = new RegExp(`^\\s*(?:-\\s*)?${rxEscape(key)}:\\s*(.*)$`);
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(rx);
    if (!m) continue;
    const base = indentOf(lines[i]);
    const parts: string[] = [];
    if (m[1] && !['|', '>'].includes(m[1].trim())) parts.push(m[1].trim());
    for (let j = i + 1; j < lines.length; j++) {
      const line = lines[j];
      const trimmed = line.trim();
      if (!trimmed) continue;
      const ind = indentOf(line);
      if (ind <= base) break;
      if (ind === base + 2 && /^[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
      if (/^-\s+[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
      parts.push(trimmed.replace(/^-\s+/, ''));
    }
    return trimSsotValue(stripYamlScalar(parts.join(' ')), max);
  }
  return '';
};

export const sectionByKey = (sections: any, key: any): any => (sections || []).find((s: any) => s.key === key) || null;
export const sectionsForKeys = (sections: any, keys: any): any[] => (keys || []).map((k: any) => sectionByKey(sections, k)).filter(Boolean);

export const sectionFact = (section: any, key: any, fallback = ''): string => {
  if (!section) return fallback;
  const fromText = fieldFromText(section.text, key);
  if (fromText) return fromText;
  const fact = ((section.summary && section.summary.facts) || []).find((f: any) => f.key === key);
  return fact ? fact.value : fallback;
};

export const listBlocksFromText = (text: any, parentKey = ''): any[] => {
  const lines = ssotPreviewLines(text);
  let start = 0;
  let parentIndent = -1;
  if (parentKey) {
    const parentRx = new RegExp(`^\\s*${rxEscape(parentKey)}:\\s*(?:#.*)?$`);
    const idx = lines.findIndex((line: string) => parentRx.test(line));
    if (idx < 0) return [];
    start = idx + 1;
    parentIndent = indentOf(lines[idx]);
  }

  let listIndent = -1;
  for (let i = start; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (!trimmed) continue;
    const ind = indentOf(lines[i]);
    if (parentKey && ind < parentIndent) break;
    if (parentKey && ind === parentIndent && !trimmed.startsWith('- ') && /^[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
    if (trimmed.startsWith('- ')) {
      listIndent = ind;
      start = i;
      break;
    }
  }
  if (listIndent < 0) return [];

  const blocks: any[] = [];
  let cur: any = null;
  for (let i = start; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    const ind = indentOf(line);
    if (parentKey && trimmed && ind < parentIndent) break;
    if (parentKey && trimmed && ind === parentIndent && !trimmed.startsWith('- ') && /^[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
    if (trimmed.startsWith('- ') && ind === listIndent) {
      if (cur) blocks.push(cur);
      cur = { startLineOffset: i, lines: [line] };
    } else if (cur) {
      cur.lines.push(line);
    }
  }
  if (cur) blocks.push(cur);
  return blocks.map((b: any) => ({ text: b.lines.join('\n'), startLineOffset: b.startLineOffset }));
};

export const listBlocksFromSection = (section: any, parentKey = ''): any[] =>
  section ? listBlocksFromText(section.text, parentKey).map((b: any) => ({
    ...b,
    startLine: section.startLine + b.startLineOffset,
  })) : [];

export const childBlockFromText = (text: any, parentKey = ''): any => {
  if (!parentKey) return null;
  const lines = ssotPreviewLines(text);
  const parentRx = new RegExp(`^\\s*${rxEscape(parentKey)}:\\s*(.*)$`);
  const idx = lines.findIndex((line: string) => parentRx.test(line));
  if (idx < 0) return null;
  const parentIndent = indentOf(lines[idx]);
  const blockLines = [lines[idx]];
  for (let i = idx + 1; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed && indentOf(line) <= parentIndent) break;
    blockLines.push(line);
  }
  return { text: blockLines.join('\n'), startLineOffset: idx };
};

export const nestedFieldFromText = (text: any, parentKey: any, childKey: any, max = 240): string => {
  const child = childBlockFromText(text, parentKey);
  if (!child) return '';
  const firstLine = String(child.text || '').split(/\r?\n/)[0] || '';
  const inline = inlineYamlObjectFromLine(firstLine);
  if (inline && inline[childKey]) return trimSsotValue(inline[childKey], max);
  return fieldFromText(child.text, childKey, max);
};

export const mapBlocksFromText = (text: any, parentKey = ''): any[] => {
  const lines = ssotPreviewLines(text);
  let start = 0;
  let parentIndent = -1;
  if (parentKey) {
    const parentRx = new RegExp(`^\\s*${rxEscape(parentKey)}:\\s*(?:#.*)?$`);
    const idx = lines.findIndex((line: string) => parentRx.test(line));
    if (idx < 0) return [];
    start = idx + 1;
    parentIndent = indentOf(lines[idx]);
  }

  const baseIndent = parentKey ? parentIndent + 2 : (lines[0] ? indentOf(lines[0]) + 2 : 0);
  const blocks: any[] = [];
  let cur: any = null;
  for (let i = start; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) continue;
    const ind = indentOf(line);
    if (parentKey && ind <= parentIndent) break;
    const m = line.match(/^\s*([A-Za-z0-9_.-]+):\s*(.*)$/);
    if (m && ind === baseIndent && !trimmed.startsWith('- ')) {
      if (cur) blocks.push(cur);
      cur = { mapKey: m[1], startLineOffset: i, lines: [line] };
    } else if (cur) {
      cur.lines.push(line);
    }
  }
  if (cur) blocks.push(cur);
  return blocks.map((b: any) => ({ mapKey: b.mapKey, text: b.lines.join('\n'), startLineOffset: b.startLineOffset }));
};

export const mapBlocksFromSection = (section: any, parentKey = ''): any[] =>
  section ? mapBlocksFromText(section.text, parentKey).map((b: any) => ({
    ...b,
    startLine: section.startLine + b.startLineOffset,
  })) : [];

export const inlineYamlObjectFromLine = (line: any): Record<string, any> => {
  const raw = String(line || '').match(/\{(.+)\}/);
  if (!raw) return {};
  return raw[1].split(/,(?=(?:[^'"]*['"][^'"]*['"])*[^'"]*$)/).reduce((acc: Record<string, any>, part: string) => {
    const m = part.match(/^\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$/);
    if (m) acc[m[1]] = stripYamlScalar(m[2]);
    return acc;
  }, {});
};

export const blockField = (block: any, key: any, max = 240): string => {
  const direct = fieldFromText(block && block.text, key, max);
  if (direct) return direct;
  const firstLine = String((block && block.text) || '').split(/\r?\n/)[0] || '';
  return trimSsotValue(inlineYamlObjectFromLine(firstLine)[key], max);
};

export const blockListValues = (block: any, parentKey: any, max = 8): string[] =>
  listBlocksFromText(block && block.text, parentKey)
    .map((b: any) => stripYamlScalar(b.text.split(/\r?\n/)[0].replace(/^\s*-\s*/, '')))
    .filter(Boolean)
    .slice(0, max);

export const mapGroupsFromSection = (section: any, parentKey = ''): any[] => {
  if (!section) return [];
  const lines = ssotPreviewLines(section.text);
  let start = 0;
  let parentIndent = indentOf(lines[0] || '');
  if (parentKey) {
    const rx = new RegExp(`^\\s*${rxEscape(parentKey)}:\\s*(?:#.*)?$`);
    const idx = lines.findIndex((line: string) => rx.test(line));
    if (idx < 0) return [];
    start = idx + 1;
    parentIndent = indentOf(lines[idx]);
  }
  const groups: any[] = [];
  let cur: any = null;
  const wantedIndent = parentKey ? parentIndent + 2 : 2;
  for (let i = start; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) continue;
    const ind = indentOf(line);
    if (parentKey && ind <= parentIndent) break;
    const m = line.match(/^\s*([A-Za-z0-9_.-]+):\s*(.*)$/);
    if (m && ind === wantedIndent && !trimmed.startsWith('- ')) {
      if (cur) groups.push(cur);
      cur = { key: m[1], startLine: section.startLine + i, lines: [line] };
    } else if (cur) {
      cur.lines.push(line);
    }
  }
  if (cur) groups.push(cur);
  return groups.map((g: any) => ({ ...g, text: g.lines.join('\n') }));
};

export const interfaceFromBlock = (block: any, fallbackName = 'interface', fallbackType = 'custom'): any => ({
  name: block?.mapKey || blockField(block, 'name') || blockField(block, 'id') || blockField(block, 'bus') || fallbackName,
  type: blockField(block, 'type')
    || blockField(block, 'proto')
    || blockField(block, 'protocol')
    || blockField(block, 'bus_type')
    || nestedFieldFromText(block?.text, 'busType', 'name')
    || nestedFieldFromText(block?.text, 'bus_type', 'name')
    || fallbackType,
  role: blockField(block, 'role'),
  description: blockField(block, 'description', 360) || blockField(block, 'displayName', 220),
  ports: [
    ...listBlocksFromText(block.text, 'ports'),
    ...mapBlocksFromText(block.text, 'ports'),
    ...listBlocksFromText(block.text, 'signals'),
    ...mapBlocksFromText(block.text, 'signals'),
  ].map((port: any) => ({
    name: blockField(port, 'name') || port?.mapKey || stripYamlScalar(port.text.replace(/^\s*-\s*/, '').split(':')[0]),
    direction: blockField(port, 'direction') || blockField(port, 'dir') || blockField(port, 'mode'),
    width: blockField(port, 'width') || blockField(port, 'bits') || blockField(port, 'range'),
    description: blockField(port, 'description', 220),
  })),
});

export const scalarInterfaceFromSection = (section: any, key: any, fallbackName = 'bus_interface'): any[] => {
  const value = section ? fieldFromText(section.text, key, 260) : '';
  if (!value || /^(?:\[\]|\{\}|\[|\{)$/.test(value)) return [];
  const inline = inlineYamlObjectFromLine(`${key}: ${value}`);
  const type = inline.type || inline.proto || inline.protocol || inline.bus_type || value;
  const name = inline.name || inline.id || fallbackName;
  return [{
    name,
    type,
    role: inline.role || '',
    description: inline.description || value,
    ports: [],
  }];
};

export const extractInterfaces = (section: any): any[] => {
  const keys: [string, string, string][] = [
    ['interfaces', 'interface', 'custom'],
    ['bus_interfaces', 'bus_interface', 'bus'],
    ['bus_interface', 'bus_interface', 'bus'],
    ['busInterfaces', 'bus_interface', 'bus'],
    ['buses', 'bus', 'bus'],
  ];
  const rows: any[] = [];
  keys.forEach(([key, fallbackName, fallbackType]) => {
    rows.push(
      ...listBlocksFromSection(section, key).map((block: any) => interfaceFromBlock(block, fallbackName, fallbackType)),
      ...mapBlocksFromSection(section, key).map((block: any) => interfaceFromBlock(block, block.mapKey || fallbackName, fallbackType)),
    );
    rows.push(...scalarInterfaceFromSection(section, key, fallbackName));
  });
  return rows;
};

export const extractSignalPorts = (section: any): any[] => [
  ...listBlocksFromSection(section, 'signals'),
  ...mapBlocksFromSection(section, 'signals'),
  ...listBlocksFromSection(section, 'ports'),
  ...mapBlocksFromSection(section, 'ports'),
].map((block: any) => ({
  name: blockField(block, 'name') || block?.mapKey || 'signal',
  direction: blockField(block, 'direction') || blockField(block, 'dir') || blockField(block, 'mode'),
  width: blockField(block, 'width') || blockField(block, 'bits') || blockField(block, 'range') || '1',
  description: blockField(block, 'description', 220),
}));

export const _pinTypeFromPort = (port: any, fallbackType = 'signal'): string => {
  const text = `${port?.name || ''} ${port?.description || ''} ${port?.protocol || ''} ${fallbackType || ''}`.toLowerCase();
  if (/(^|[^a-z])(clk|clock|pclk|hclk|aclk|sclk)([^a-z]|$)/.test(text)) return 'clock';
  if (/(^|[^a-z])(rst|reset|resetn|aresetn|presetn|preset_n)([^a-z]|$)/.test(text)) return 'reset';
  if (/(apb|paddr|psel|penable|pwrite|pwdata|prdata|pready|pslverr|pstrb|pprot)/.test(text)) {
    return port?.protocol || 'apb';
  }
  if (/(axi|ahb|wishbone|tilelink|amba|bus)/.test(text)) {
    return port?.protocol || (fallbackType && fallbackType !== 'signal' ? fallbackType : 'bus');
  }
  if (/(irq|interrupt|nmi)/.test(text)) return 'irq';
  return fallbackType || port?.protocol || 'signal';
};

export const _portFromBlock = (block: any, defaults: any = {}): any => {
  const name = blockField(block, 'name') || block?.mapKey || defaults.name || '';
  const direction = blockField(block, 'direction') || blockField(block, 'dir') || blockField(block, 'mode') || defaults.direction || '';
  const width = blockField(block, 'width') || blockField(block, 'bits') || blockField(block, 'range') || defaults.width || '';
  const description = blockField(block, 'description', 220) || defaults.description || '';
  const protocol = blockField(block, 'protocol') || defaults.protocol || '';
  const type = blockField(block, 'type') || _pinTypeFromPort({ name, description, protocol }, defaults.type || protocol || 'signal');
  return {
    name,
    direction,
    width,
    description,
    protocol,
    type,
    role: blockField(block, 'role') || defaults.role || direction,
    clock_domain: blockField(block, 'clock_domain') || defaults.clock_domain || '',
    reset_domain: blockField(block, 'reset_domain') || defaults.reset_domain || '',
  };
};

export const _dedupePins = (pins: any[]): any[] => {
  const seen = new Set<string>();
  return (pins || []).filter((pin: any) => {
    const name = String(pin?.name || '').trim();
    if (!name) return false;
    const key = name.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

export const listRootIoItems = (section: any): any[] => {
  if (!section) return [];
  const lines = ssotPreviewLines(section.text);
  const rootIndent = lines[0] ? indentOf(lines[0]) : 0;
  const itemIndent = rootIndent + 2;
  const blocks: any[] = [];
  let cur: any = null;
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) continue;
    const ind = indentOf(line);
    if (ind <= rootIndent) break;
    if (trimmed.startsWith('- ') && ind === itemIndent) {
      if (cur) blocks.push(cur);
      cur = { startLineOffset: i, lines: [line] };
      continue;
    }
    if (!cur) continue;
    if (ind <= itemIndent) {
      blocks.push(cur);
      cur = null;
      continue;
    }
    cur.lines.push(line);
  }
  if (cur) blocks.push(cur);
  return blocks.map((block: any) => ({
    text: block.lines.join('\n'),
    startLineOffset: block.startLineOffset,
    startLine: section.startLine + block.startLineOffset,
  }));
};

export const extractFlatIoPorts = (ioSection: any): any[] => {
  return listRootIoItems(ioSection)
    .map((block: any) => _portFromBlock(block))
    .filter((port: any) => port.name && (port.direction || port.width));
};

export const extractIoDiagramPins = (ioSection: any): any[] => {
  const flatPins = extractFlatIoPorts(ioSection).map((port: any) => ({
    ...port,
    pin: true,
    ports: [],
  }));
  return _dedupePins(flatPins);
};

export const extractReviewPins = (ioSection: any): any[] => extractIoDiagramPins(ioSection);

export const extractReviewInterfaces = (sections: any, ioSection: any): any[] => {
  const canonical = extractInterfaces(ioSection);
  const generic = (sections || [])
    .filter((section: any) => section !== ioSection && /(interfaces?|bus_?interfaces?|busInterfaces|interrupts?)$/i.test(section.key || ''))
    .flatMap((section: any) => {
      const busItems = [
        ...listBlocksFromSection(section),
        ...mapBlocksFromSection(section),
      ];
      if (busItems.length && /^bus_?interfaces?$/i.test(section.key || '')) {
        return busItems.map((block: any) => interfaceFromBlock(block, ssotTitleFor(section.key), 'bus'));
      }
      if (/^bus_?interface$/i.test(section.key || '') && section.value) {
        return [{
          name: ssotTitleFor(section.key),
          type: stripYamlScalar(section.value) || 'bus',
          role: sectionFact(section, 'role'),
          description: sectionFact(section, 'description', stripYamlScalar(section.value)),
          ports: extractSignalPorts(section),
        }];
      }
      return [{
        name: ssotTitleFor(section.key),
        type: sectionFact(section, 'type') || sectionFact(section, 'proto') || 'interface',
        role: sectionFact(section, 'role'),
        description: sectionFact(section, 'description', ''),
        ports: extractSignalPorts(section),
      }];
    });
  const seen = new Set<string>();
  return [...canonical, ...generic].filter((iface: any) => {
    const key = `${iface.name}:${iface.type}:${iface.role}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return iface.name || iface.description || (iface.ports || []).length;
  });
};

export const extractFeatures = (section: any): any[] => listBlocksFromSection(section).map((block: any) => ({
  name: blockField(block, 'name') || 'Feature',
  description: blockField(block, 'description', 480) || blockField(block, 'summary', 480),
  trigger: blockField(block, 'trigger', 360),
  datapath: blockField(block, 'datapath', 520),
  control: blockField(block, 'control', 300),
  output: blockField(block, 'output', 360),
}));

// Recursively parse a sub-module block, descending into any nested
// `sub_modules: …` lists declared on the block. Without recursion, the
// BlockDiagram could only ever render one level — adding nested support
// lets a top module wrap its mid-level modules, which themselves wrap
// leaf modules. Only depth-aware code paths use the `children` field;
// existing flat-list consumers ignore it.
export const _parseSubmoduleBlock = (block: any): any => ({
  name: blockField(block, 'name') || 'module',
  file: blockField(block, 'file'),
  description: blockField(block, 'description', 360),
  implements: blockListValues(block, 'implements', 6),
  sourceSections: blockListValues(block, 'source_sections', 6),
  interfaces: listBlocksFromText(block.text, 'interfaces').map((iface: any) => ({
    name: blockField(iface, 'name') || 'interface',
    type: blockField(iface, 'type') || 'local',
    inputs: blockListValues(iface, 'inputs', 8),
    outputs: blockListValues(iface, 'outputs', 8),
  })),
  children: listBlocksFromText(block.text, 'sub_modules').map(_parseSubmoduleBlock),
});

export const extractSubmodules = (section: any): any[] => listBlocksFromSection(section).map(_parseSubmoduleBlock);

export const extractModuleContracts = (section: any): any[] => listBlocksFromSection(section, 'module_contracts').map((block: any) => ({
  module: blockField(block, 'module') || blockField(block, 'name') || 'module',
  owns: blockListValues(block, 'owns', 10),
  inputs: blockListValues(block, 'inputs', 12),
  outputs: blockListValues(block, 'outputs', 12),
  implementation: blockField(block, 'implementation_direction', 520)
    || blockField(block, 'implementation', 520)
    || blockField(block, 'approach', 520),
  interfaces: listBlocksFromText(block.text, 'interfaces').map((iface: any) => ({
    name: blockField(iface, 'name') || 'interface',
    type: blockField(iface, 'type') || 'local',
    role: blockField(iface, 'role'),
    inputs: blockListValues(iface, 'inputs', 8),
    outputs: blockListValues(iface, 'outputs', 8),
    description: blockField(iface, 'description', 260),
  })),
}));

export const extractRegisters = (section: any): any[] => {
  const blocks = [
    ...listBlocksFromSection(section, 'register_list'),
    ...mapBlocksFromSection(section, 'register_list'),
    ...listBlocksFromSection(section, 'map'),
    ...mapBlocksFromSection(section, 'map'),
  ];
  const rootMap = mapBlocksFromSection(section).filter((block: any) => {
    const key = String(block.mapKey || '').toLowerCase();
    if (['config', 'register_width', 'addr_width', 'byte_addressable', 'no_registers', 'no_csr', 'no_register_map'].includes(key)) return false;
    return blockField(block, 'offset')
      || blockField(block, 'access')
      || blockField(block, 'width')
      || listBlocksFromText(block.text, 'fields').length
      || mapBlocksFromText(block.text, 'fields').length;
  });
  const source = blocks.length ? blocks : (listBlocksFromSection(section).length ? listBlocksFromSection(section) : rootMap);
  return source.map((block: any) => ({
    name: blockField(block, 'name') || block?.mapKey || 'REG',
    offset: blockField(block, 'offset'),
    width: blockField(block, 'width'),
    access: blockField(block, 'access'),
    reset: blockField(block, 'reset'),
    description: blockField(block, 'description', 300),
    fields: [
      ...listBlocksFromText(block.text, 'fields'),
      ...mapBlocksFromText(block.text, 'fields'),
    ].map((field: any) => ({
      bits: formatBitRange(blockField(field, 'bits')
        || blockField(field, 'bit')
        || blockField(field, 'range')
        || blockField(field, 'position')),
      name: blockField(field, 'name') || field?.mapKey || 'field',
      access: blockField(field, 'access'),
      reset: blockField(field, 'reset'),
      description: blockField(field, 'description', 240),
    })),
  }));
};

export const _isRegisterPlaceholderValue = (value: any): boolean => {
  const text = stripYamlScalar(value).trim();
  return !text || /^(-|--|tbd|todo|unknown|placeholder|null|none|n\/a|na)$/i.test(text);
};

export const _hasRegisterDetail = (value: any): boolean => !_isRegisterPlaceholderValue(value);

export const _hasMeaningfulRegisterField = (field: any): boolean => !!field && (
  _hasRegisterDetail(field.bits)
  || _hasRegisterDetail(field.name)
  || _hasRegisterDetail(field.access)
  || _hasRegisterDetail(field.reset)
  || _hasRegisterDetail(field.description)
);

export const _stateNameFromBlock = (block: any): string => {
  const first = String((block && block.text) || '').split(/\r?\n/)[0] || '';
  return blockField(block, 'name')
    || blockField(block, 'state')
    || stripYamlScalar(first.replace(/^\s*-\s*/, ''));
};

export const _parseFsmTransition = (block: any): any => {
  const first = String((block && block.text) || '').split(/\r?\n/)[0] || '';
  const scalar = stripYamlScalar(first.replace(/^\s*-\s*/, ''));
  let from = blockField(block, 'from');
  let to = blockField(block, 'to');
  let condition = blockField(block, 'condition', 280)
    || blockField(block, 'guard', 280)
    || blockField(block, 'when', 280)
    || blockField(block, 'on', 280);
  const action = blockField(block, 'action', 240) || blockField(block, 'output', 240);
  if ((!from || !to) && scalar) {
    const m = scalar.match(/^(.+?)\s*(?:->|=>|to)\s*(.+?)(?:\s+(?:when|if|on)\s+(.+))?$/i);
    if (m) {
      from = from || stripYamlScalar(m[1]);
      to = to || stripYamlScalar(m[2]);
      condition = condition || stripYamlScalar(m[3] || '');
    }
  }
  return { from, to, condition, action, raw: scalar };
};

export const _fsmFromText = (name: any, text: any, sourceKey = ''): any => {
  const stateBlocks = listBlocksFromText(text, 'states');
  const transitionBlocks = listBlocksFromText(text, 'transitions');
  const states = stateBlocks.map(_stateNameFromBlock).filter(Boolean);
  const transitions = transitionBlocks.map(_parseFsmTransition).filter((t: any) => (
    t.from || t.to || t.condition || t.raw
  ));
  return {
    name,
    sourceKey,
    states,
    transitions,
    resetState: fieldFromText(text, 'reset_state')
      || fieldFromText(text, 'initial_state')
      || fieldFromText(text, 'reset')
      || states[0]
      || '',
    illegalRecovery: fieldFromText(text, 'illegal_state_recovery', 360)
      || fieldFromText(text, 'default_recovery', 360)
      || fieldFromText(text, 'safe_state', 240),
    outputs: blockListValues({ text }, 'outputs', 8),
    actions: blockListValues({ text }, 'actions', 8),
    note: fieldFromText(text, 'note', 360) || fieldFromText(text, 'description', 360),
  };
};

export const extractFsms = (section: any): any[] => {
  if (!section) return [];
  const groups = mapGroupsFromSection(section)
    .filter((group: any) => !/^(states|transitions|outputs|actions)$/i.test(group.key || ''));
  if (groups.length) {
    return groups
      .map((group: any) => _fsmFromText(ssotTitleFor(group.key), group.text, section.key))
      .filter((machine: any) => machine.states.length || machine.transitions.length || machine.note);
  }
  const direct = _fsmFromText(ssotTitleFor(section.key), section.text, section.key);
  if (direct.states.length || direct.transitions.length) return [direct];
  return [];
};

export const sourceSectionsForDigestView = (view: any, sections: any): any[] => {
  const source = sectionsForKeys(sections, view && view.keys);
  const addMatching = (rx: RegExp) => {
    (sections || []).forEach((section: any) => {
      if (rx.test(section.key || '') && !source.includes(section)) source.push(section);
    });
  };
  switch (view && view.id) {
    case 'interfaces':
      addMatching(/interface|businterfaces|interrupts?/i);
      break;
    case 'registers':
      addMatching(/register|memory_?map/i);
      break;
    case 'clocking':
      addMatching(/clock|reset|cdc|rdc/i);
      break;
    case 'function_model':
      addMatching(/function|fsm|state|logic|arbitration|ack|interrupt/i);
      break;
    case 'fsm':
      addMatching(/fsm|state|transition/i);
      break;
    case 'cycle_model':
      addMatching(/cycle|timing|latency|handshake|pipeline|scl/i);
      break;
    case 'rtl_contract':
      addMatching(/rtl_?contract|error_?handling|debug_?observability|filelist|coding_?rules/i);
      break;
    case 'dataflow':
      addMatching(/dataflow|flow|fifo|buffer|bit_control|start_stop|open_drain|access/i);
      break;
    case 'architecture':
      addMatching(/sub_?modules|decomposition|module|build/i);
      break;
    case 'feature_map':
      addMatching(/feature|fifo|fsm|arbitration|ack|interrupt|start_stop|open_drain|scl|bit_control|access/i);
      break;
    case 'verification':
      addMatching(/test_?requirements|quality_?gates|traceability|workflow_?todos|coverage/i);
      break;
    case 'implementation':
      addMatching(/integration|dft|synthesis|pnr|filelist|coding_?rules|reuse_?modules/i);
      break;
    case 'review_gaps':
    case 'raw_yaml':
      return sections || [];
    default:
      break;
  }
  return source;
};

export const digestViewsForSections = (sections: any): any[] => {
  if (!(sections || []).length) return [];
  return SSOT_DIGEST_VIEWS.filter((view: any) => (
    view.id === 'overview'
    || view.id === 'scenarios'
    || view.id === 'review_gaps'
    || view.id === 'raw_yaml'
    || sourceSectionsForDigestView(view, sections).length > 0
  ));
};

// ── ssot status + reviewer-markdown helpers ──────────────────────
// Moved to workspace-ssotx-status.tsx and re-exported from the head of this
// file. Definitions intentionally live there to keep this module < 1000 lines.
