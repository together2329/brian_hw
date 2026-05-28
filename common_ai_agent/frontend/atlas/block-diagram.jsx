// block-diagram.jsx — Phase 18 refactor: BlockDiagram extracted from
// ssot-digest.jsx (which was 2123 lines, just over the 2000-line target).
// Same IIFE + lambda forward-ref pattern as preview-pane.jsx / ssot-digest.jsx.
// 6 workspace-scope deps; SubmoduleCell is one of them. All already on
// window from earlier phases (ssot-digest exposes them).

(() => {

// Forward-ref to workspace.jsx helpers (resolved at call time):
const SubmoduleCell = (...a) => window.SubmoduleCell(...a);
const _formatWidth = (...a) => window._formatWidth(...a);
const _ifaceColor = (...a) => window._ifaceColor(...a);
const _ifaceKind = (...a) => window._ifaceKind(...a);
const _maxNestingDepth = (...a) => window._maxNestingDepth(...a);
const sectionFact = (...a) => window.sectionFact(...a);


const BlockDiagram = ({ topName, modules, contractByModule = {}, interfaces = [], diagramPins = [], clockSection, parameters = [] }) => {
  const list = Array.isArray(modules) ? modules : [];
  if (!list.length) return null;
  // Multi-open: clicking a pin row toggles ITS drawer without closing
  // the others. The user wants to compare port lists side-by-side, so
  // restricting to one open drawer at a time would force back-and-forth
  // re-expansion. Persisted only for the lifetime of the component.
  const [openIfaces, setOpenIfaces] = React.useState(() => new Set());
  const toggleIface = (id) => setOpenIfaces(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });
  const [showAllSignals, setShowAllSignals] = React.useState(false);
  const [showParams, setShowParams] = React.useState(true);
  const maxDepth = _maxNestingDepth(list);
  // Default to 1 level so the diagram stays clean even when the SSOT
  // declares a deep hierarchy. User can raise to 2 / 3 / all from the
  // header. When SSOT has no nesting at all, the selector is hidden.
  const [depthLimit, setDepthLimit] = React.useState(1);
  const paramRows = Array.isArray(parameters) ? parameters.filter(p => p && p.name) : [];
  // Wiring-only wrappers (e.g. <ip>_wrapper) get pushed to the right so
  // the implementation submodules read first; rendering order doesn't
  // imply hardware ordering, just visual grouping.
  const ordered = [...list].sort((a, b) => Number(!!a.wiring_only) - Number(!!b.wiring_only));
  const accent = 'var(--accent)';
  // Bucket interfaces by kind so the chips can sit on the appropriate
  // edge of the frame (clock/reset → left, bus → right, irq → right,
  // data pads → bottom).
  const buckets = { clock: [], reset: [], bus: [], irq: [], data: [] };
  const pinRows = Array.isArray(diagramPins) ? diagramPins.filter(pin => pin && pin.name) : [];
  const ifaceRows = Array.isArray(interfaces) ? interfaces.filter(iface => iface && (iface.name || iface.description)) : [];
  const diagramRows = pinRows.length
    ? [
        ...pinRows,
        ...ifaceRows,
      ]
    : ifaceRows;
  diagramRows.forEach(iface => {
    const kind = _ifaceKind(iface.name, iface.type);
    (buckets[kind] || buckets.data).push({ ...iface, kind });
  });
  const hasPortDrawerOverflow = diagramRows.some(iface => (
    !iface.pin && Array.isArray(iface.ports) && iface.ports.length > 8
  ));
  // Synthesize default clock/reset chips from the clock_reset_domains
  // section if no explicit interface entries exist for them.
  if (!buckets.clock.length && clockSection) {
    const freq = sectionFact && sectionFact(clockSection, 'frequency_hz');
    buckets.clock.push({ name: 'clk', type: 'clock', kind: 'clock', description: freq ? `${freq} Hz` : '', ports: [] });
  }
  if (!buckets.reset.length && clockSection) {
    buckets.reset.push({ name: 'rst_n', type: 'reset', kind: 'reset', description: 'async reset', ports: [] });
  }

  // External pin row — used by the new left-column layout. Renders
  // `<name · type role>  ─── ●`, with the colored line + dot
  // visually "plugging into" the right-hand top-module frame.
  // Clicking the row toggles a port detail drawer underneath.
  const renderPinRow = (iface, idx) => {
    const color = _ifaceColor(iface.kind);
    // idx ("top0"/"bot1"…) is always appended so two interfaces sharing
    // kind+name — e.g. an `apb_slave` diagram pin and an `apb_slave` interface
    // both bucketed to "bus" — get distinct React keys (no "two children with
    // the same key" warning) and independent open/close drawer state.
    const id = `${iface.kind}:${iface.name || 'pin'}:${idx}`;
    const isOpen = openIfaces.has(id);
    const ports = Array.isArray(iface.ports) ? iface.ports
                : Array.isArray(iface.inputs) || Array.isArray(iface.outputs)
                  ? [...(iface.inputs || []).map(n => ({ name: n, dir: 'in' })),
                     ...(iface.outputs || []).map(n => ({ name: n, dir: 'out' }))]
                  : [];
    const hasDrawer = !iface.pin && ports.length;
    const visible = showAllSignals ? ports : ports.slice(0, 8);
    const typeStr = (iface.type || '').trim() || iface.kind || (iface.pin ? 'pin' : 'custom');
    const pinDir = iface.direction || iface.dir || (ports.length === 1 ? (ports[0].direction || ports[0].dir) : '');
    const pinWidth = iface.width || (ports.length === 1 ? ports[0].width : '');
    const pinWidthText = _formatWidth(pinWidth);
    const metaParts = [typeStr].filter(Boolean);
    if (iface.pin) {
      if (pinDir) metaParts.push(pinDir);
      if (pinWidthText) metaParts.push(pinWidthText);
    } else {
      const role = (iface.role || '').toLowerCase().startsWith('mast') ? 'M' : 'S';
      metaParts.push(role);
    }
    return (
      <div key={id} style={{ display: 'flex', flexDirection: 'column' }}>
        <div
          role={hasDrawer ? 'button' : undefined}
          tabIndex={hasDrawer ? 0 : undefined}
          onClick={() => { if (hasDrawer) toggleIface(id); }}
          onKeyDown={(e) => {
            if (!hasDrawer) return;
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleIface(id);
            }
          }}
          title={iface.description || iface.role || iface.type || iface.name}
          style={{
            display: 'flex', alignItems: 'center', gap: 0,
            cursor: hasDrawer ? 'pointer' : 'default', userSelect: 'none',
            padding: '2px 0',
          }}
        >
          <span style={{
            flex: 1, textAlign: 'right',
            paddingRight: 6,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            fontSize: 'var(--ui-control-font-size)',
          }}>
            <span style={{ color: 'var(--fg)', fontWeight: 600 }}>{iface.name || iface.type}</span>
            <span style={{ color: 'var(--fg-mute)' }}> · {metaParts.join(' ')}</span>
          </span>
          <span style={{ width: 22, height: 1.5, background: color, flexShrink: 0 }} />
          <span style={{
            width: 9, height: 9, borderRadius: '50%',
            background: color,
            flexShrink: 0,
            border: `1px solid ${color}`,
          }} />
          {hasDrawer ? (
            <span style={{
              marginLeft: 4, fontSize: 9,
              color: 'var(--fg-mute)',
            }}>
              {isOpen ? '▾' : '▸'}
            </span>
          ) : null}
        </div>
        {isOpen && hasDrawer ? (
          <div style={{
            margin: '4px 0 4px 8px',
            border: `1px solid ${color}`,
            borderRadius: 3,
            background: 'var(--bg-1)',
            padding: '5px 8px',
            display: 'grid',
            gridTemplateColumns: 'auto auto auto',
            gap: '2px 12px',
            fontSize: 10,
            alignItems: 'baseline',
            whiteSpace: 'nowrap',
          }}>
            {visible.map((p, i) => (
              <React.Fragment key={p.name || i}>
                <span style={{ color: 'var(--fg)', fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.dir || p.direction || ''}</span>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{_formatWidth(p.width)}</span>
              </React.Fragment>
            ))}
            {!showAllSignals && ports.length > 8 ? (
              <span style={{ gridColumn: '1 / -1', color: 'var(--fg-mute)', fontSize: 9 }}>
                +{ports.length - 8} more · click "show all" above
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  };

  // Legacy chip renderer — retained for any caller that still wants
  // the in-frame chip style. Kept inert until/unless wired back in.
  // eslint-disable-next-line no-unused-vars
  const renderIfaceChip = (iface, idx) => {
    const color = _ifaceColor(iface.kind);
    const id = `${iface.kind}:${iface.name || idx}`;
    const isOpen = openIfaces.has(id);
    const ports = Array.isArray(iface.ports) ? iface.ports : [];
    const visible = showAllSignals ? ports : ports.slice(0, 8);
    return (
      <div
        key={id}
        style={{
          display: 'flex', flexDirection: 'column', alignItems: 'stretch', minWidth: 0,
        }}
      >
        <div
          role="button"
          tabIndex={0}
          onClick={() => toggleIface(id)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleIface(id);
            }
          }}
          title={iface.description || iface.role || iface.type || iface.name}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '3px 8px',
            border: `1px solid ${color}`,
            background: `color-mix(in oklch, ${color} 8%, var(--bg-1))`,
            borderRadius: 4,
            color, fontSize: 10, fontWeight: 700,
            cursor: 'pointer', userSelect: 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <span style={{
            fontSize: 8, padding: '0 4px', borderRadius: 2,
            border: `1px solid ${color}`, opacity: 0.8,
            textTransform: 'uppercase',
          }}>{iface.kind}</span>
          <span style={{
            overflow: 'hidden', textOverflow: 'ellipsis',
            whiteSpace: 'nowrap', minWidth: 0,
            color: 'var(--fg)',
            fontWeight: 700,
          }}>{iface.name || iface.type}</span>
          {ports.length ? (
            <span style={{ color: 'var(--fg-mute)', fontWeight: 400, fontSize: 9 }}>
              {ports.length}
            </span>
          ) : null}
          <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}>{isOpen ? '▾' : '▸'}</span>
        </div>
        {isOpen && ports.length ? (
          <div style={{
            marginTop: 4,
            border: `1px solid ${color}`,
            borderRadius: 3,
            background: 'var(--bg-1)',
            padding: '5px 8px',
            display: 'grid',
            gridTemplateColumns: 'auto 1fr auto',
            gap: '2px 8px',
            fontSize: 10,
          }}>
            {visible.map((p, i) => (
              <React.Fragment key={p.name || i}>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.dir || p.direction || ''}</span>
                <span style={{ color: 'var(--fg)', fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.width ? `[${p.width}]` : ''}</span>
              </React.Fragment>
            ))}
            {!showAllSignals && ports.length > 8 ? (
              <span style={{ gridColumn: '1 / -1', color: 'var(--fg-mute)', fontSize: 9 }}>
                +{ports.length - 8} more · click "show all" above
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div style={{
      padding: '14px 12px 18px',
      fontFamily: 'var(--mono)',
      fontSize: 'var(--ui-control-font-size)',
    }}>
      {/* Detail toggle + depth selector. The depth chip group only
          appears when the SSOT declares any nesting (maxDepth > 1) —
          otherwise the buttons would be no-ops and just clutter the
          header. */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        {maxDepth > 1 ? (
          <>
            <span className="mute" style={{ fontSize: 10 }}>depth</span>
            {[1, 2, 3].filter(d => d <= maxDepth).map(d => (
              <button
                key={d}
                type="button"
                className="mini-btn"
                onClick={() => setDepthLimit(d)}
                title={`show ${d} level${d === 1 ? '' : 's'} of submodules`}
                style={depthLimit === d ? {
                  borderColor: 'var(--accent)',
                  color: 'var(--accent)',
                } : undefined}
              >
                {d}
              </button>
            ))}
            {maxDepth > 3 ? (
              <button
                type="button"
                className="mini-btn"
                onClick={() => setDepthLimit(maxDepth)}
                title="show every nested submodule level"
                style={depthLimit >= maxDepth ? {
                  borderColor: 'var(--accent)',
                  color: 'var(--accent)',
                } : undefined}
              >
                all
              </button>
            ) : null}
          </>
        ) : null}
        <span style={{ flex: 1 }} />
        {paramRows.length ? (
          <button
            type="button"
            className="mini-btn"
            onClick={() => setShowParams(v => !v)}
            title={`toggle parameter chips (${paramRows.length})`}
            style={showParams ? {
              borderColor: 'var(--accent)',
              color: 'var(--accent)',
            } : undefined}
          >
            {showParams ? '▾ params' : '▸ params'}
          </button>
        ) : null}
        {hasPortDrawerOverflow ? (
          <button
            type="button"
            className="mini-btn"
            onClick={() => setShowAllSignals(v => !v)}
            title="toggle full port list on every interface"
          >
            {showAllSignals ? '▾ collapse all' : '▸ show all'}
          </button>
        ) : null}
      </div>

      {/* Two-column layout: external pin labels (left) connect to the
          framed top module (right) via a short colored line + dot,
          mirroring the soc-architect block-card visual. Pin order:
          bus → data → irq grouped at top, clock → reset grouped at
          bottom (clock/reset are the conventional "ground reference"
          on most block diagrams).
          Left column is `auto`-sized so an expanded port drawer can
          push the column wider than the resting pin labels — without
          this, long widths like `[APB_ADDR_WIDTH-1:0]` got clipped
          inside the 220px cap. */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'auto 1fr',
        gap: 0,
        alignItems: 'stretch',
      }}>
        {/* LEFT — pin column. Each row: label · type role  ─── ● */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '36px 0 18px',
          gap: 4,
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {[...buckets.bus, ...buckets.data, ...buckets.irq].map((iface, i) =>
              renderPinRow(iface, `top${i}`)
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
            {[...buckets.clock, ...buckets.reset].map((iface, i) =>
              renderPinRow(iface, `bot${i}`)
            )}
          </div>
        </div>

        {/* RIGHT — framed top module. Title + category badges on the
            top edge, parameters + submodules inside. */}
        <div style={{
          position: 'relative',
          border: `2px solid ${accent}`,
          borderRadius: 8,
          background: 'color-mix(in oklch, var(--accent) 5%, var(--bg-2))',
          padding: '28px 16px 16px',
          marginLeft: -1,
        }}>
          {/* Top header strip — diamond + module name on the left,
              category badge on the right. Sits FULLY inside the frame
              so the outer border doesn't draw a strikethrough across
              the badge text. */}
          <div style={{
            position: 'absolute',
            top: 8,
            left: 14,
            right: 14,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 8,
            pointerEvents: 'none',
          }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              fontWeight: 700,
              color: 'var(--accent)',
              letterSpacing: '0.04em',
            }}>
              <span style={{ fontSize: 13, lineHeight: 1, color: accent }}>◇</span>
              <span>{topName || 'top'}</span>
            </div>
            <span style={{
              padding: '1px 8px',
              background: 'transparent',
              border: `1px solid color-mix(in oklch, ${accent} 50%, var(--line))`,
              borderRadius: 3,
              fontSize: 9,
              fontWeight: 700,
              color: 'var(--fg-mute)',
              letterSpacing: '0.08em',
              lineHeight: 1.4,
              whiteSpace: 'nowrap',
            }}>
              {(() => {
                const allChips = [...(buckets.bus || []), ...(buckets.irq || []), ...(buckets.data || [])];
                const text = allChips.map(c => `${c.name || ''} ${c.type || ''}`).join(' ').toLowerCase();
                if (/(apb|axi|ahb|wishbone|amba)/.test(text)) return 'PERIPH';
                if (/(cpu|core|fetch|decode|exec)/.test(text)) return 'CORE';
                if (/(dma|dmac)/.test(text)) return 'DMA';
                if (/(mem|cache|sram|dram)/.test(text)) return 'MEM';
                return 'TOP';
              })()}
            </span>
          </div>

          {/* Parameter chips (KEY=value) inside the frame, above
              submodules. Hidden when paramRows empty or user toggled
              off via the header `params` button. */}
          {showParams && paramRows.length ? (
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 6,
              marginBottom: 14,
            }}>
              {paramRows.map(p => (
                <span
                  key={p.name}
                  title={p.description || `${p.name}=${p.value}`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'baseline',
                    gap: 0,
                    padding: '3px 10px',
                    background: 'var(--bg-1)',
                    border: '1px solid var(--line)',
                    borderRadius: 14,
                    fontSize: 10,
                    color: 'var(--fg-mute)',
                    fontFamily: 'var(--mono)',
                  }}
                >
                  <span>{p.name}</span>
                  {p.value ? (
                    <>
                      <span style={{ color: 'var(--fg-mute)' }}>=</span>
                      <span style={{ color: 'var(--fg)', fontWeight: 700 }}>{p.value}</span>
                    </>
                  ) : null}
                </span>
              ))}
            </div>
          ) : null}

          {/* Inner grid of submodule blocks. */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: 10,
          }}>
            {ordered.map(m => (
              <SubmoduleCell
                key={m.name}
                module={m}
                contractByModule={contractByModule}
                depth={1}
                depthLimit={depthLimit}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

window.BlockDiagram = BlockDiagram;

})();
