/**
 * workspace-ssot-panels.tsx
 *
 * SSOT presentational cards + the SsotPanel container (strangler-fig mirror
 * of the matching slice of frontend/atlas/workspace.jsx).
 *
 * Owns the SSOT digest cards (FeatureCard / ModuleTree / SubmoduleCell and
 * their iface color/kind/width helpers), DigestSourceSections, chooseSsotFile,
 * and the SsotPanel pane. The interactive viewers (PipelineTraceDiagram,
 * SsotCommandPalette, RegisterBitMap / RegisterBitFieldView and
 * SsotScenarioPlayer) now live in workspace-ssotp-register-views.tsx and are
 * re-exported below so this module's public contract is unchanged.
 *
 * These .tsx files are INERT mirrors; the legacy workspace.jsx still serves
 * the live app. Window-sourced values are intentionally typed `any`.
 */
import { useState, useEffect, Fragment } from 'react';

import {
  linkifyReferences,
  trimSsotValue,
  ssotPathOf,
  ssotTitleFor,
  sourceSectionsForDigestView,
  ssotSectionStatus,
  ssotStatusColor,
  ssotStatusGlyph,
  ssotReviewMarkdown,
} from './workspace-ssot-extract';

// PipelineTraceDiagram, SsotCommandPalette, the register bit-map cluster
// (_parseBitRange / _accessColor / RegisterBitMap / RegisterBitFieldView) and
// SsotScenarioPlayer were relocated to workspace-ssotp-register-views.tsx for
// cohesion and to keep every file under 1000 lines. Re-export them here so the
// public contract of this module is unchanged.
export {
  PipelineTraceDiagram,
  SsotCommandPalette,
  _parseBitRange,
  _accessColor,
  RegisterBitMap,
  RegisterBitFieldView,
  SsotScenarioPlayer,
} from './workspace-ssotp-register-views';

// _markdownHtml lives in workspace-markdown-chips (outside this slice's import
// set); it is also registered on window by the live workspace.jsx, so read it
// from there. isSsotYamlPath / ssotIpFromSession live in
// workspace-session-routing (also outside this slice) and are likewise on
// window — none of these globals are declared in types/atlas-window.d.ts, so
// use the permissive (window as any) form.
const _markdownHtml = (text: unknown): string =>
  (window as any)._markdownHtml ? (window as any)._markdownHtml(text) : '';
const isSsotYamlPath = (path: any): boolean =>
  (window as any).isSsotYamlPath ? (window as any).isSsotYamlPath(path) : false;
const ssotIpFromSession = (session: any): string =>
  (window as any).ssotIpFromSession ? (window as any).ssotIpFromSession(session) : '';

export const _FeatureRow = ({ glyph, label, value, color }: any) => {
  if (value === '' || value == null) return null;
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '18px 78px minmax(0, 1fr)',
      gap: '4px 10px', alignItems: 'baseline',
      fontSize: 12, lineHeight: 1.45,
    }}>
      <span aria-hidden="true" style={{
        color, fontFamily: 'var(--mono)', fontWeight: 700, textAlign: 'center',
      }}>{glyph}</span>
      <span style={{
        color, fontFamily: 'var(--mono)', fontSize: 10,
        textTransform: 'uppercase', letterSpacing: '0.08em',
      }}>{label}</span>
      <span style={{ minWidth: 0, wordBreak: 'break-word' }}>{String(value)}</span>
    </div>
  );
};

export const FeatureCard = ({ index, feature, tokenMap, onJump }: any) => {
  const [hover, setHover] = useState(false);
  const hasAny = feature && (feature.datapath || feature.control || feature.output);
  const description = feature && feature.description;
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        border: '1px solid ' + (hover ? 'var(--accent)' : 'var(--line)'),
        borderRadius: 6,
        background: 'var(--bg-2)',
        padding: '12px 14px',
        minWidth: 0,
        display: 'flex', flexDirection: 'column', gap: 8,
        transition: 'border-color 120ms ease, transform 120ms ease',
        transform: hover ? 'translateY(-1px)' : 'translateY(0)',
      }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <span style={{
          fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)',
          color: 'var(--fg-mute)', minWidth: 28,
        }}>F{index}.</span>
        <span style={{
          color: 'var(--accent)', fontWeight: 800, fontSize: 14,
          letterSpacing: '0.01em',
        }}>{feature.name || '(unnamed feature)'}</span>
        {feature.trigger ? (
          <span style={{
            fontSize: 10, fontFamily: 'var(--mono)',
            padding: '2px 8px', borderRadius: 999,
            background: 'color-mix(in oklch, var(--magenta) 14%, transparent)',
            color: 'var(--magenta)',
            border: '1px solid color-mix(in oklch, var(--magenta) 35%, transparent)',
          }}>trigger · {feature.trigger}</span>
        ) : null}
      </div>
      {description ? (
        <div className="mute" style={{ lineHeight: 1.55, fontSize: 'var(--ui-control-font-size)' }}>
          {tokenMap ? linkifyReferences(description, tokenMap, onJump) : description}
        </div>
      ) : null}
      {hasAny ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingTop: 2 }}>
          <_FeatureRow glyph="➜" label="datapath" value={feature.datapath}
                       color="var(--accent)" />
          <_FeatureRow glyph="⊳" label="control"  value={feature.control}
                       color="var(--magenta)" />
          <_FeatureRow glyph="⊙" label="output"   value={feature.output}
                       color="var(--green, #22c55e)" />
        </div>
      ) : (
        <div className="mute" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>
          — no datapath / control / output captured yet —
        </div>
      )}
    </div>
  );
};

export const ModuleTree = ({ topName, modules }: any) => (
  <div className="code" style={{
    margin: 0, padding: '10px 12px', fontSize: 12, lineHeight: 1.55,
    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  }}>
    <div><span style={{ color: 'var(--magenta)', fontWeight: 800 }}>{topName || 'top'}</span></div>
    {(modules || []).map((m: any, idx: number) => {
      const last = idx === modules.length - 1;
      const branch = last ? '└─ ' : '├─ ';
      const pad = last ? '   ' : '│  ';
      const meta = m.file ? `  ${m.file}` : '';
      const desc = m.description ? `${pad}   ${trimSsotValue(m.description, 140)}` : '';
      return (
        <div key={`${idx}-${m.name || 'mod'}`}>
          <div>{branch}<span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{m.name || 'module'}</span><span className="mute">{meta}</span></div>
          {desc ? <div className="mute">{desc}</div> : null}
        </div>
      );
    })}
  </div>
);

// Categorize an interface name + type into one of: clock | reset | bus
// | irq | data. Drives which side of the BlockDiagram frame the chip
// is rendered on, and which color it uses.
export const _ifaceKind = (name: any, type: any): string => {
  const t = `${name || ''} ${type || ''}`.toLowerCase();
  if (/(^|[^a-z])(clk|clock|cks)([^a-z]|$)/.test(t)) return 'clock';
  if (/(^|[^a-z])(rst|reset|aresetn)([^a-z]|$)/.test(t)) return 'reset';
  if (/(apb|axi|ahb|wishbone|tilelink|amba|bus|register|reg_if|reg-if|paddr|psel|penable|pwrite|pwdata|prdata|pready|pslverr|pstrb|pprot)/.test(t)) return 'bus';
  if (/(irq|interrupt|nmi)/.test(t)) return 'irq';
  return 'data';
};

// Pin connector colors. Clock/reset use a green family (the "ground
// reference" convention from most SoC schematic tools); bus/data/irq
// share a deep navy so the user can tell signal-domain pins from
// timing-domain pins at a glance. Matches the soc-architect ModuleCard
// palette so the two views feel consistent.
// Format a port width hint into SystemVerilog range notation.
// • "" / "1" / 1 → ""        (single-bit, no range)
// • numeric "8"  → "[7:0]"     (concrete range)
// • symbolic "NUM_PINS" → "[NUM_PINS-1:0]" (parametric range)
// • already-shaped "NUM_PINS-1:0" or "[7:0]" → preserved
export const _formatWidth = (w: any): string => {
  if (w === undefined || w === null || w === '') return '';
  const s = String(w).trim();
  if (!s || s === '1') return '';
  if (s.startsWith('[') && s.endsWith(']')) return s;
  if (/[:]/.test(s)) return `[${s}]`;
  if (/^\d+$/.test(s)) {
    const n = parseInt(s, 10);
    if (n <= 1) return '';
    return `[${n - 1}:0]`;
  }
  return `[${s}-1:0]`;
};

export const _ifaceColor = (kind: any): string => (({
  clock: '#3a8f4f',
  reset: '#3a8f4f',
  bus:   '#1f3552',
  irq:   '#1f3552',
  data:  '#1f3552',
} as Record<string, string>)[kind] || 'var(--fg-mute)');

// Pure HTML/CSS block diagram for the Architecture section.
// Hierarchical layout: the top module is rendered as the OUTER frame,
// and each submodule sits visually contained inside it as a child box.
// Major interfaces (clock, reset, bus, irq, data pads) are rendered as
// chips around the outer frame edges so the user sees the IP's
// "shape" (what plugs in where) at a glance. Each interface chip
// expands to show its full port list when clicked.
// Recursive submodule cell. When the module has `children`, it renders
// as a mini-frame containing nested cells (capped by `depthLimit` —
// any nesting deeper than the limit collapses into a "+N hidden" hint
// so the user can dial up the level via the BlockDiagram header).
export const SubmoduleCell = ({ module: m, contractByModule, depth, depthLimit }: any) => {
  // Submodule pin/interface display — surfaces the per-module local
  // interfaces (apb_slave, gpio_pad, …) as small chips inside the cell
  // so the user can see what each submodule plugs into without leaving
  // the diagram. Contract data (richer: includes role/description)
  // wins over the raw sub_modules[].interfaces list.
  const localIfaces = (contractByModule[m.name]?.interfaces && contractByModule[m.name].interfaces.length
    ? contractByModule[m.name].interfaces
    : (Array.isArray(m.interfaces) ? m.interfaces : []));
  const wiringOnly = !!m.wiring_only;
  const blockColor = wiringOnly ? 'var(--magenta)' : 'var(--cyan)';
  // Per-cell expand state — clicking a chip toggles its drawer
  // independent of the top-level pin-row state.
  const [openLocal, setOpenLocal] = useState<Set<string>>(() => new Set());
  const toggleLocal = (id: string) => setOpenLocal(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });
  const childList = Array.isArray(m.children) ? m.children : [];
  const showChildren = childList.length > 0 && depth < depthLimit;
  const hiddenChildren = childList.length > 0 && depth >= depthLimit ? childList.length : 0;
  const orderedChildren = [...childList].sort((a: any, b: any) => Number(!!a.wiring_only) - Number(!!b.wiring_only));
  return (
    <div
      style={{
        border: `${wiringOnly ? '1.5px dashed' : '1.5px solid'} ${blockColor}`,
        background: 'var(--bg-1)',
        borderRadius: 5,
        padding: '7px 10px 8px',
        minWidth: 0,
      }}
    >
      <div
        title={m.name}
        style={{
          color: blockColor, fontWeight: 700, fontSize: 12,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}
      >
        {m.name}
      </div>
      {m.file ? (
        <div
          className="mute"
          title={m.file}
          style={{
            fontSize: 9, marginTop: 2,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}
        >
          {m.file}
        </div>
      ) : null}
      {localIfaces.length ? (
        <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
          {localIfaces.map((iface: any, ifIdx: number) => {
            const kind = _ifaceKind(iface.name, iface.type);
            const color = _ifaceColor(kind);
            const id = `${m.name}:${iface.name || ifIdx}`;
            const isOpen = openLocal.has(id);
            const allPorts = Array.isArray(iface.ports) && iface.ports.length
              ? iface.ports
              : [
                  ...(Array.isArray(iface.inputs) ? iface.inputs : []).map((n: any) =>
                    typeof n === 'string' ? { name: n, dir: 'input' } : ({ ...n, dir: n.dir || 'input' })
                  ),
                  ...(Array.isArray(iface.outputs) ? iface.outputs : []).map((n: any) =>
                    typeof n === 'string' ? { name: n, dir: 'output' } : ({ ...n, dir: n.dir || 'output' })
                  ),
                ];
            return (
              <div key={id}>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => { e.stopPropagation(); toggleLocal(id); }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      e.stopPropagation();
                      toggleLocal(id);
                    }
                  }}
                  title={iface.description || iface.role || iface.type || iface.name}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                    padding: '1px 6px',
                    border: `1px solid ${color}`,
                    background: `color-mix(in oklch, ${color} 6%, transparent)`,
                    borderRadius: 10,
                    fontSize: 9,
                    cursor: 'pointer', userSelect: 'none',
                    fontFamily: 'var(--mono)',
                  }}
                >
                  <span style={{
                    width: 6, height: 6, borderRadius: '50%', background: color,
                  }} />
                  <span style={{ color: 'var(--fg)', fontWeight: 600 }}>{iface.name || iface.type}</span>
                  {allPorts.length ? (
                    <span style={{ color: 'var(--fg-mute)' }}>{allPorts.length}</span>
                  ) : null}
                  <span style={{ color: 'var(--fg-mute)' }}>{isOpen ? '▾' : '▸'}</span>
                </span>
                {isOpen && allPorts.length ? (
                  <div style={{
                    marginTop: 3,
                    border: `1px solid ${color}`,
                    borderRadius: 3,
                    background: 'var(--bg-1)',
                    padding: '4px 6px',
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1fr) auto auto',
                    gap: '1px 8px',
                    fontSize: 9,
                  }}>
                    {allPorts.slice(0, 12).map((p: any, i: number) => (
                      <Fragment key={p.name || i}>
                        <span style={{ color: 'var(--fg)', fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
                        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.dir || p.direction || ''}</span>
                        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{_formatWidth(p.width)}</span>
                      </Fragment>
                    ))}
                    {allPorts.length > 12 ? (
                      <span style={{ gridColumn: '1 / -1', color: 'var(--fg-mute)', fontSize: 8 }}>
                        +{allPorts.length - 12} more
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}
      {wiringOnly ? (
        <div
          style={{
            marginTop: 4,
            fontSize: 9, color: 'var(--fg-mute)',
            textTransform: 'uppercase', letterSpacing: '0.06em',
          }}
        >
          wiring only
        </div>
      ) : null}
      {showChildren ? (
        <div style={{
          marginTop: 6,
          padding: '6px',
          border: `1px dashed color-mix(in oklch, ${blockColor} 40%, var(--line))`,
          borderRadius: 4,
          background: `color-mix(in oklch, ${blockColor} 3%, transparent)`,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 6,
        }}>
          {orderedChildren.map((child: any) => (
            <SubmoduleCell
              key={child.name}
              module={child}
              contractByModule={contractByModule}
              depth={depth + 1}
              depthLimit={depthLimit}
            />
          ))}
        </div>
      ) : null}
      {hiddenChildren ? (
        <div className="mute" style={{
          marginTop: 4, fontSize: 9, color: 'var(--fg-mute)',
          fontStyle: 'italic',
        }}>
          ↳ +{hiddenChildren} nested submodule{hiddenChildren === 1 ? '' : 's'} (raise depth to view)
        </div>
      ) : null}
    </div>
  );
};

// Walk a module tree to find the deepest level present so the depth
// selector can offer just-enough options (no "5" button when the data
// only goes 2 deep).
export const _maxNestingDepth = (modules: any): number => {
  if (!Array.isArray(modules) || !modules.length) return 1;
  let best = 1;
  for (const m of modules) {
    const childDepth = m && Array.isArray(m.children) && m.children.length
      ? 1 + _maxNestingDepth(m.children)
      : 1;
    if (childDepth > best) best = childDepth;
  }
  return best;
};


export const DigestSourceSections = ({ view, sections, statusByKey, t }: any) => {
  const source = sourceSectionsForDigestView(view, sections);
  if (!source.length) return null;
  return (
    <details style={{
      marginTop: 12, border: '1px solid var(--line)', borderRadius: 4,
      background: 'var(--bg-2)',
    }}>
      <summary style={{
        cursor: 'pointer', padding: '8px 12px',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)',
      }}>{t.sourceSections}</summary>
      <div style={{ borderTop: '1px solid var(--line)', padding: '10px 12px', display: 'grid', gap: 10 }}>
        {source.map((section: any) => {
          const status = ssotSectionStatus(section, statusByKey);
          const glyph = ssotStatusGlyph(status);
          return (
            <div key={section.key} style={{ borderLeft: `2px solid ${ssotStatusColor(status)}`, paddingLeft: 10 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', marginBottom: 4 }}>
                <span style={{ color: ssotStatusColor(status), fontFamily: 'var(--mono)', fontWeight: 900, minWidth: 18 }}>
                  {glyph}
                </span>
                <span style={{ color: 'var(--fg)', fontWeight: 700 }}>{ssotTitleFor(section.key)}</span>
                <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{section.key} · line {section.startLine}</span>
              </div>
              <div className="md-agent"
                dangerouslySetInnerHTML={{ __html: _markdownHtml(ssotReviewMarkdown(section, status)) }} />
            </div>
          );
        })}
      </div>
    </details>
  );
};


export const chooseSsotFile = (files: any, preferredPath = ''): string => {
  const paths = (Array.isArray(files) ? files : []).map(ssotPathOf).filter(Boolean);
  if (preferredPath && (paths.includes(preferredPath) || isSsotYamlPath(preferredPath))) return preferredPath;
  const scope = String(window.SCOPE_PATH || '').split('/').filter(Boolean).pop() || '';
  const sessionIp = ssotIpFromSession(window.ACTIVE_SESSION || '');
  const explicitIp = String(window.ACTIVE_IP || '').trim();
  // When IP context is the literal `default` placeholder (or empty),
  // do NOT auto-pick the first SSOT in the workspace — that misleads
  // the user into thinking the current session owns that IP. Show the
  // empty/default-workspace state instead and let them pick an IP.
  const ipFromContext = sessionIp || (explicitIp && explicitIp !== 'default' ? explicitIp : '') || scope;
  const isDefault = !ipFromContext || ipFromContext === 'default';
  if (isDefault) return '';
  return paths.find((p: string) => p === `${ipFromContext}.ssot.yaml` || p.includes(`${ipFromContext}/`) || p.includes(`/${ipFromContext}.`))
    || '';
};

// Phase 13a refactor: SsotDocPane moved to frontend/atlas/ssot-doc.jsx.
export const SsotDocPane = window.SsotDocPane;

// agent writes a new SSOT (data.jsx subscribes to tool_result).
export const SsotPanel = () => {
  const files = (window as any).SSOT_FILES || [];
  const [selected, setSelected] = useState<any>(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  // Default to the first file once the list is populated.
  useEffect(() => {
    if (!selected && files.length > 0) setSelected(files[0].path);
  }, [files.length, selected]);

  // Fetch content whenever the selected file changes (or the file list
  // refreshes — the user may want to see updated content for an SSOT
  // the agent just wrote).
  useEffect(() => {
    if (!selected) { setContent(''); return; }
    let cancelled = false;
    setLoading(true);
    window.atlasData.fetchSsot(selected).then((d: any) => {
      if (cancelled) return;
      setContent(d?.content || `# (could not read ${selected})`);
      setLoading(false);
    }).catch(() => { if (!cancelled) { setContent(''); setLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length]);

  if (files.length === 0) {
    return (
      <div className="code" style={{ flex: 1, overflow: 'auto',
        padding: '14px 16px', fontSize: 12, color: 'var(--fg-mute)' }}>
        # No *.ssot.yaml files in the project yet.<br />
        # Use <span className="acc">/grill-me</span> to gather the spec
        and <span className="acc">/to-ssot &lt;ip&gt;</span> to write the YAML.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* file picker */}
      <div style={{
        borderBottom: '1px solid var(--line)', padding: '4px 6px',
        display: 'flex', flexWrap: 'wrap', gap: 4,
        background: 'var(--bg-2)',
      }}>
        {files.map((f: any) => (
          <span key={f.path}
            onClick={() => setSelected(f.path)}
            title={f.path}
            style={{
              cursor: 'pointer',
              padding: '2px 8px', fontSize: 10,
              fontFamily: 'var(--mono)',
              border: `1px solid ${selected === f.path ? 'var(--accent)' : 'var(--line)'}`,
              color: selected === f.path ? 'var(--accent)' : 'var(--fg-mute)',
              background: selected === f.path ? 'var(--bg-3, var(--bg-2))' : 'transparent',
              borderRadius: 2,
            }}>
            {f.path.split('/').pop()}
          </span>
        ))}
      </div>
      {/* content viewer */}
      <pre className="code" style={{
        flex: 1, overflow: 'auto', margin: 0,
        padding: '12px 14px', fontSize: 12, lineHeight: 1.55,
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {loading ? '# loading…' : content}
      </pre>
    </div>
  );
};
