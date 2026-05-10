// debug-tab.jsx — top-level Debug tab pane mounted by workspace.jsx
// when mainTab === 'debug'. Reads /api/debug/scenarios for the active
// IP, plus auxiliary sim artifacts (scoreboard_events.jsonl, fl_rtl_
// compare.json, VCD files), and renders a 3-pane layout:
//
//   ┌────────────────┬──────────────────────────────┐
//   │ Scenarios list │  Selected scenario detail    │
//   │                │  + scoreboard rows           │
//   ├────────────────┴──────────────────────────────┤
//   │ Sim artifacts  · click to open in preview     │
//   └───────────────────────────────────────────────┘
//
// onOpenSource(path) is wired by workspace.jsx to the preview pane
// so clicking a VCD/source row pivots the preview to that file.

(function () {
  'use strict';

  const STATUS_COLOR = {
    pass: 'var(--green, #22c55e)',
    fail: 'var(--red, #ef4444)',
    pending: 'var(--fg-mute, #888)',
  };

  const fmtRel = (path) => {
    if (!path) return '';
    const root = (window.PROJECT_ROOT_NAME || '').replace(/\/$/, '');
    return root && path.startsWith(root + '/') ? path.slice(root.length + 1) : path;
  };

  const StatusPill = ({ status }) => (
    <span style={{
      display: 'inline-block',
      padding: '1px 7px',
      borderRadius: 999,
      fontSize: 10,
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: 0.5,
      border: '1px solid ' + (STATUS_COLOR[status] || STATUS_COLOR.pending),
      color: STATUS_COLOR[status] || STATUS_COLOR.pending,
      background: 'transparent',
    }}>{status || 'pending'}</span>
  );

  const Section = ({ title, count, children, action }) => (
    <div style={{
      border: '1px solid var(--line)',
      borderRadius: 6,
      marginBottom: 12,
      background: 'var(--bg-1, #14171c)',
    }}>
      <div style={{
        padding: '8px 12px',
        borderBottom: '1px solid var(--line)',
        fontSize: 11,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: 1,
        color: 'var(--fg-mute)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span>{title}</span>
        {count != null && <span style={{ fontSize: 10, opacity: 0.7 }}>{count}</span>}
        <span style={{ flex: 1 }} />
        {action}
      </div>
      <div style={{ padding: '4px 0' }}>{children}</div>
    </div>
  );

  window.DebugTab = function DebugTab({ ip, onOpenSource }) {
    const [scenarios, setScenarios] = React.useState({ tests: [], summary: { pass: 0, fail: 0, pending: 0 }, ssot_path: '', sb_path: '' });
    const [selectedSid, setSelectedSid] = React.useState(null);
    const [artifacts, setArtifacts] = React.useState({ vcd: [], rtl: [], compare: null });
    const [loading, setLoading] = React.useState(false);
    const [err, setErr] = React.useState('');

    const refresh = React.useCallback(async () => {
      if (!ip) {
        setScenarios({ tests: [], summary: { pass: 0, fail: 0, pending: 0 } });
        setArtifacts({ vcd: [], rtl: [], compare: null });
        return;
      }
      setLoading(true);
      setErr('');
      try {
        const [scResp, lsResp] = await Promise.all([
          fetch(`/api/debug/scenarios?ip=${encodeURIComponent(ip)}`, { cache: 'no-store' }),
          fetch(`/api/files?path=${encodeURIComponent(ip + '/sim')}`, { cache: 'no-store' }).catch(() => null),
        ]);
        if (scResp && scResp.ok) {
          setScenarios(await scResp.json());
        } else if (scResp) {
          setErr(`scenarios: HTTP ${scResp.status}`);
        }
        // Best-effort artifact discovery via /api/files. Skips silently
        // if the endpoint shape doesn't match.
        let simEntries = [];
        try {
          const j = lsResp && lsResp.ok ? await lsResp.json() : null;
          simEntries = Array.isArray(j?.entries) ? j.entries : Array.isArray(j) ? j : [];
        } catch (_) {}
        const vcd = simEntries
          .filter(e => /\.vcd$/i.test(e.name || e.path || ''))
          .map(e => ({ name: e.name, path: e.path || `${ip}/sim/${e.name}` }));
        // RTL listing — same idea but rooted at <ip>/rtl.
        let rtl = [];
        try {
          const r = await fetch(`/api/files?path=${encodeURIComponent(ip + '/rtl')}`, { cache: 'no-store' });
          if (r.ok) {
            const j = await r.json();
            const ents = Array.isArray(j?.entries) ? j.entries : Array.isArray(j) ? j : [];
            rtl = ents
              .filter(e => /\.(sv|v)$/i.test(e.name || ''))
              .map(e => ({ name: e.name, path: e.path || `${ip}/rtl/${e.name}` }));
          }
        } catch (_) {}
        // fl_rtl_compare.json (closure summary)
        let compare = null;
        try {
          const r = await fetch(`/api/ssot?file=${encodeURIComponent(ip + '/sim/fl_rtl_compare.json')}`, { cache: 'no-store' });
          if (r.ok) {
            const j = await r.json();
            try { compare = JSON.parse(j.content || '{}'); } catch (_) { compare = null; }
          }
        } catch (_) {}
        setArtifacts({ vcd, rtl, compare });
      } catch (e) {
        setErr(String(e && e.message || e));
      } finally {
        setLoading(false);
      }
    }, [ip]);

    React.useEffect(() => { refresh(); }, [refresh]);

    // Subscribe to backend signals so the panel auto-refreshes when
    // a sim run finishes or scoreboard rows are appended.
    React.useEffect(() => {
      if (!window.backend?.subscribe) return undefined;
      const subs = [];
      ['sim_done', 'scoreboard_appended', 'fl_rtl_compare_done'].forEach(ev => {
        try { subs.push(window.backend.subscribe(ev, () => refresh())); } catch (_) {}
      });
      return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
    }, [refresh]);

    const selectedScenario = (scenarios.tests || []).find(t => t.scenario_id === selectedSid) || null;

    if (!ip) {
      return (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)', fontSize: 12 }}>
          No IP selected — pick one from <code>IP_ID</code> to see scenarios.
        </div>
      );
    }

    const summary = scenarios.summary || { pass: 0, fail: 0, pending: 0 };
    const compare = artifacts.compare;

    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{
          padding: '8px 14px',
          borderBottom: '1px solid var(--line)',
          fontSize: 11,
          color: 'var(--fg-mute)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <strong style={{ color: 'var(--fg)' }}>Debug · {ip}</strong>
          <span>· {(scenarios.tests || []).length} scenarios</span>
          <span style={{ color: STATUS_COLOR.pass }}>{summary.pass} pass</span>
          <span style={{ color: STATUS_COLOR.fail }}>{summary.fail} fail</span>
          <span>{summary.pending} pending</span>
          {compare && (
            <span>· FL/RTL: <span style={{ color: STATUS_COLOR[compare.status] || STATUS_COLOR.pending }}>{compare.status || '?'}</span></span>
          )}
          <span style={{ flex: 1 }} />
          {loading && <span>refreshing…</span>}
          <button className="mini-btn" type="button" onClick={refresh}>refresh</button>
        </div>

        {err && (
          <div style={{ padding: '8px 14px', color: STATUS_COLOR.fail, fontSize: 11 }}>
            {err}
          </div>
        )}

        <div style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '320px 1fr',
          minHeight: 0,
        }}>
          {/* Scenarios list */}
          <div style={{ borderRight: '1px solid var(--line)', overflow: 'auto', padding: '8px 10px' }}>
            <Section title="Scenarios" count={(scenarios.tests || []).length}>
              {(scenarios.tests || []).length === 0 && (
                <div style={{ padding: '8px 12px', fontSize: 11, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                  no test_requirements.scenarios in <code>{fmtRel(scenarios.ssot_path) || `${ip}/yaml/${ip}.ssot.yaml`}</code>
                </div>
              )}
              {(scenarios.tests || []).map(t => (
                <div
                  key={t.scenario_id}
                  onClick={() => setSelectedSid(t.scenario_id)}
                  style={{
                    padding: '6px 12px',
                    cursor: 'pointer',
                    borderLeft: '3px solid ' + (selectedSid === t.scenario_id ? STATUS_COLOR[t.status] || STATUS_COLOR.pending : 'transparent'),
                    background: selectedSid === t.scenario_id ? 'color-mix(in oklch, var(--accent) 8%, transparent)' : 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    fontSize: 11,
                  }}>
                  <StatusPill status={t.status} />
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan)' }}>{t.scenario_id}</span>
                  <span style={{ flex: 1 }} />
                  <span style={{ opacity: 0.65 }}>{t.pass_rows + t.fail_rows} rows</span>
                </div>
              ))}
            </Section>
          </div>

          {/* Detail pane */}
          <div style={{ overflow: 'auto', padding: '12px 14px' }}>
            {selectedScenario ? (
              <Section title={`${selectedScenario.scenario_id} · ${selectedScenario.name || ''}`}>
                <div style={{ padding: '8px 12px', display: 'grid', gridTemplateColumns: '110px 1fr', columnGap: 12, rowGap: 6, fontSize: 11 }}>
                  <span style={{ color: 'var(--fg-mute)' }}>status</span><span><StatusPill status={selectedScenario.status} /></span>
                  <span style={{ color: 'var(--fg-mute)' }}>pass / fail</span><span>{selectedScenario.pass_rows} / {selectedScenario.fail_rows}</span>
                  <span style={{ color: 'var(--fg-mute)' }}>stimulus</span><pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 11 }}>{String(selectedScenario.stimulus || '')}</pre>
                  <span style={{ color: 'var(--fg-mute)' }}>expected</span><pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 11 }}>{String(selectedScenario.expected || '')}</pre>
                  <span style={{ color: 'var(--fg-mute)' }}>checker</span><pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 11 }}>{String(selectedScenario.checker || '')}</pre>
                  <span style={{ color: 'var(--fg-mute)' }}>coverage</span><span style={{ fontFamily: 'var(--font-mono)' }}>{(selectedScenario.coverage || []).join(', ') || '—'}</span>
                </div>
              </Section>
            ) : (
              <div style={{ padding: '12px', color: 'var(--fg-mute)', fontSize: 11, fontStyle: 'italic' }}>
                Select a scenario from the list to view its stimulus / expected / checker.
              </div>
            )}

            {compare && (
              <Section title="FL / RTL closure" action={
                <span style={{ color: STATUS_COLOR[compare.status] || STATUS_COLOR.pending, fontSize: 10 }}>{compare.status || '?'}</span>
              }>
                <pre style={{ margin: 0, padding: '8px 12px', whiteSpace: 'pre-wrap', fontSize: 11 }}>
                  {JSON.stringify(compare, null, 2).slice(0, 1200)}
                </pre>
              </Section>
            )}

            <Section title="Sim artifacts (VCD)" count={artifacts.vcd.length}>
              {artifacts.vcd.length === 0 && (
                <div style={{ padding: '8px 12px', fontSize: 11, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                  no .vcd in <code>{ip}/sim</code>
                </div>
              )}
              {artifacts.vcd.map(f => (
                <div key={f.path}
                  onClick={() => onOpenSource && onOpenSource(f.path)}
                  style={{ padding: '4px 12px', cursor: 'pointer', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                  📊 {f.name}
                </div>
              ))}
            </Section>

            <Section title="RTL sources" count={artifacts.rtl.length}>
              {artifacts.rtl.length === 0 && (
                <div style={{ padding: '8px 12px', fontSize: 11, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                  no .sv / .v in <code>{ip}/rtl</code>
                </div>
              )}
              {artifacts.rtl.map(f => (
                <div key={f.path}
                  onClick={() => onOpenSource && onOpenSource(f.path)}
                  style={{ padding: '4px 12px', cursor: 'pointer', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                  📄 {f.name}
                </div>
              ))}
            </Section>
          </div>
        </div>
      </div>
    );
  };
})();
