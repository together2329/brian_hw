// sim-debug-panels-side.tsx — the LEFT hierarchy panel and the SOURCE band
// extracted from sim-debug.tsx (strangler-fig split). Behavior-identical:
//   • HierarchyPanel = the SAME `eff.showHier && (...)` subtree — the RTL/TB
//     tab toggle, the backend label, the cocotb tree (TB) vs the RTL
//     HierarchyNode + the VCD signal list (RTL).
//   • SourceBand = the SAME `eff.showSource && (...)` subtree — the source
//     mini-header (path + loading/line badges + annot toggle + A/B/A+B axis
//     buttons) and the SourceViewer.
// The root SimDebug closure owns all the state; each panel receives the slice
// it renders + the handlers it fires as a typed props bundle (window-sourced
// values stay `any`, same permissive house style as sim-debug-helpers.tsx).
//
// Load order: imported by sim-debug.tsx. Owns no window bridge.
import type { ReactNode } from 'react';
import { CocotbTreeView, SourceViewer, HierarchyNode } from './sim-debug-panels';
import type { VcdData, VcdSignal } from './sim-debug-helpers';
import { waveSignalMatches } from './sim-debug-helpers';

interface HierarchyPanelProps {
  leftTab: string;
  setLeftTab: (v: string) => void;
  cocotbData: any;
  hierarchyBackendTitle: string;
  hierarchyBackendLabel: string;
  ipName: string;
  loadSourceFile: (path: string, cursorLine?: number) => void;
  hierarchy: any;
  onSelectModule: (moduleName?: string, instancePath?: string) => void;
  srcModule: string;
  hierarchyError: string;
  vcdData: VcdData | null;
  selectedSig: string;
  selectedSigScope: string;
  wavePinnedSignals: Array<{ name?: string; scope?: string }>;
  onSelectWaveSignal: (signalName: string, signalScope?: string) => void;
  showSignalHierarchy: boolean;
}

export const HierarchyPanel = ({
  leftTab, setLeftTab, cocotbData, hierarchyBackendTitle, hierarchyBackendLabel,
  ipName, loadSourceFile, hierarchy, onSelectModule, srcModule, hierarchyError,
  vcdData, selectedSig, selectedSigScope, wavePinnedSignals, onSelectWaveSignal,
  showSignalHierarchy,
}: HierarchyPanelProps): ReactNode => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--panel)', borderRight: '1px solid var(--line)' }}>
      <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
        <button
          onClick={() => setLeftTab('rtl')}
          style={{
            background: leftTab === 'rtl' ? 'var(--accent)' : 'transparent',
            color:      leftTab === 'rtl' ? 'var(--bg)'     : 'var(--fg-mute)',
            border: '1px solid var(--line)', borderRadius: 3,
            padding: '1px 8px', fontSize: 10, cursor: 'pointer',
            fontFamily: 'var(--mono)', fontWeight: 700,
            marginRight: 4,
          }}
          title="RTL hierarchy (verilator/pyslang elab)"
        >RTL</button>
        <button
          onClick={() => setLeftTab('tb')}
          style={{
            background: leftTab === 'tb' ? 'var(--accent)' : 'transparent',
            color:      leftTab === 'tb' ? 'var(--bg)'     : 'var(--fg-mute)',
            border: '1px solid var(--line)', borderRadius: 3,
            padding: '1px 8px', fontSize: 10, cursor: 'pointer',
            fontFamily: 'var(--mono)', fontWeight: 700,
          }}
          title="cocotb testbench environment"
        >TB{cocotbData && cocotbData.exists ? '' : ' ⊘'}</button>
        <span style={{ color: 'var(--fg-mute)', marginLeft: 8, fontSize: 10 }}>
          {leftTab === 'rtl'
            ? (
              <span title={hierarchyBackendTitle}>{hierarchyBackendLabel}</span>
            )
            : (cocotbData?.exists ? `cocotb · ${ipName}` : 'cocotb (none)')}
        </span>
        <span style={{ flex: 1 }} />
      </div>
      {leftTab === 'tb' ? (
        <CocotbTreeView
          data={cocotbData}
          ipName={ipName}
          onOpenFile={(p: string, line?: number) => loadSourceFile(p, line || 0)}
        />
      ) : (
      <div style={{ flex: 1, overflow: 'auto', padding: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
        {hierarchy ? (
          <HierarchyNode node={hierarchy} depth={0}
            onSelectModule={onSelectModule}
            activeModule={srcModule} />
        ) : (
          <div style={{ color: 'var(--fg-mute)', padding: 8 }}>
            No RTL hierarchy yet.<br />
            {hierarchyError ? (
              <span style={{ color: 'var(--err)' }}>{hierarchyError}</span>
            ) : (
              <span>Pick a workspace IP to elaborate.</span>
            )}
          </div>
        )}
        {vcdData && vcdData.signals && vcdData.signals.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4 }}>
              signals ({vcdData.signals.length})
            </div>
            {vcdData.signals.slice(0, 30).map((s: VcdSignal) => {
              const isSelected = selectedSig === s.name && (!selectedSigScope || selectedSigScope === s.scope);
              const isPinned = wavePinnedSignals.some(pin => waveSignalMatches(s, pin.name, pin.scope));
              return (
                <div
                  key={s.id}
                  onClick={() => onSelectWaveSignal(s.name!, s.scope)}
                  style={{
                    padding: '2px 4px', cursor: 'pointer',
                    color: isSelected ? 'var(--accent)' : 'var(--fg)',
                    background: isSelected ? 'var(--bg-2)' : 'transparent',
                    display: 'flex', gap: 4, alignItems: 'center',
                  }}
                  title="click to focus, Ctrl+W to add to waveform"
                >
                  <span style={{ color: isPinned ? 'var(--cyan)' : 'var(--fg-mute)' }}>{isPinned ? '◆' : '·'}</span>
                  <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {showSignalHierarchy && s.scope ? `${s.scope}.` : ''}{s.name}
                    {s.isBus && <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}> {s.range}</span>}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
      )}
    </div>
  );
};

interface SourceBandProps {
  eff: any;
  srcPath: string;
  srcLoading: boolean;
  srcCursor: number;
  showVcdAnnotations: boolean;
  setShowVcdAnnotations: (fn: (v: boolean) => boolean) => void;
  waveCursor: number;
  waveCursorB: number;
  vcdData: VcdData | null;
  vcdAnnotationAxis: string;
  setVcdAnnotationAxis: (mode: string) => void;
  srcLines: string[];
  sourceVcdAnnotations: any;
}

export const SourceBand = ({
  eff, srcPath, srcLoading, srcCursor, showVcdAnnotations, setShowVcdAnnotations,
  waveCursor, waveCursorB, vcdData, vcdAnnotationAxis, setVcdAnnotationAxis,
  srcLines, sourceVcdAnnotations,
}: SourceBandProps): ReactNode => {
  return (
    <div style={{
      flex: eff.showWave ? `${Math.round(eff.th * 100)} ${Math.round(eff.th * 100)} 0` : '1 1 0',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      background: 'var(--panel)',
    }}>
      <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
        <b>source</b>
        <span style={{ color: 'var(--cyan)', marginLeft: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
          {srcPath || `(click hierarchy module or wave signal)`}
        </span>
        <span style={{ flex: 1 }} />
        {srcLoading && <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>loading…</span>}
        {srcCursor > 0 && (
          <span style={{ color: 'var(--accent)', fontSize: 10 }}>L{srcCursor}</span>
        )}
        <button
          className="btn"
          onClick={() => setShowVcdAnnotations(v => !v)}
          title="toggle VCD values under the active source line"
          style={{
            padding: '1px 8px',
            fontSize: 10,
            fontWeight: 700,
            marginLeft: 8,
            background: showVcdAnnotations ? 'var(--accent)' : undefined,
            color: showVcdAnnotations ? '#000' : undefined,
          }}
        >
          annot {showVcdAnnotations ? 'on' : 'off'}
        </button>
        {showVcdAnnotations && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 2, marginLeft: 4 }}>
            {([
              ['both', 'A+B', `show VCD values at A (${waveCursor}${vcdData?.timescale || 'ns'}) and B (${waveCursorB}${vcdData?.timescale || 'ns'})`],
              ['a', 'A', `show VCD values at cursor A (${waveCursor}${vcdData?.timescale || 'ns'})`],
              ['b', 'B', `show VCD values at cursor B (${waveCursorB}${vcdData?.timescale || 'ns'})`],
            ] as Array<[string, string, string]>).map(([mode, label, title]) => (
              <button
                key={mode}
                className="btn"
                onClick={() => setVcdAnnotationAxis(mode)}
                title={title}
                style={{
                  padding: '1px 6px',
                  fontSize: 10,
                  fontWeight: 700,
                  minWidth: 26,
                  background: vcdAnnotationAxis === mode ? 'var(--cyan)' : undefined,
                  color: vcdAnnotationAxis === mode ? '#001018' : undefined,
                }}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>
      <SourceViewer
        lines={srcLines}
        cursor={srcCursor}
        path={srcPath}
        vcdAnnotations={sourceVcdAnnotations}
        vcdAnnotationAxis={vcdAnnotationAxis}
      />
    </div>
  );
};
