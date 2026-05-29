// app-mobile.tsx — TypeScript migration of the mobile (< 900px) header and
// its bottom-sheet sub-components, extracted from app.jsx (strangler-fig).
//
// These four components (MobileIpPicker, MobileWorkflowPicker, MobileKebabMenu,
// MobileHeader) are a self-contained, least-coupled seam: they take only
// plain props/callbacks from the App root and own no shared App state. Moving
// them out keeps the main app.tsx focused on the App root component.
//
// Behavior is identical to the original app.jsx — same markup, same event
// wiring, same props.
import { useState, useEffect, useRef } from 'react';

// ── MobileIpPicker ────────────────────────────────────────────────────────
// Bottom-sheet IP picker for mobile. Slides up from the bottom, dismissible
// by tap-outside or swipe-down. Each row is 56px tall (touch target).
export interface MobileIpPickerProps {
  open: boolean;
  activeIp: string;
  ipOptions: string[];
  onSelect: (ip: string) => void;
  onCreateIp: () => void;
  onClose: () => void;
}
export const MobileIpPicker = ({
  open, activeIp, ipOptions, onSelect, onCreateIp, onClose,
}: MobileIpPickerProps) => {
  const [filter, setFilter] = useState('');
  const inputRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    if (open) {
      setFilter('');
      setTimeout(() => { try { inputRef.current && inputRef.current.focus(); } catch (_) {} }, 80);
    }
  }, [open]);
  if (!open) return null;
  const query = filter.trim().toLowerCase();
  const visible = (ipOptions || []).filter(ip =>
    !query || ip.toLowerCase().includes(query)
  );
  return (
    <div className="mob-sheet-backdrop" onClick={onClose}>
      <div
        className="mob-sheet"
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Select IP"
      >
        <div className="mob-sheet-handle" />
        <div className="mob-sheet-title">Select IP</div>
        <div className="mob-sheet-search-wrap">
          <input
            ref={inputRef}
            className="mob-sheet-search"
            placeholder="Filter IPs…"
            value={filter}
            onChange={e => setFilter(e.currentTarget.value)}
            aria-label="Filter IP list"
          />
        </div>
        <div className="mob-sheet-list">
          {/* Create new IP row always at top */}
          <button
            className="mob-sheet-row mob-sheet-create"
            onClick={() => { onClose(); onCreateIp(); }}
          >
            <span className="mob-sheet-row-icon">+</span>
            <span className="mob-sheet-row-label">Create new IP</span>
          </button>
          {visible.length === 0 && (
            <div className="mob-sheet-empty">No IPs match "{filter}"</div>
          )}
          {visible.map(ip => (
            <button
              key={ip}
              className={'mob-sheet-row' + (ip === activeIp ? ' active' : '')}
              onClick={() => { onSelect(ip); onClose(); }}
            >
              <span className="mob-sheet-row-icon">
                {ip === activeIp ? '✓' : ' '}
              </span>
              <span className="mob-sheet-row-label">{ip}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// ── MobileWorkflowPicker ──────────────────────────────────────────────────
export interface MobileWorkflowPickerProps {
  open: boolean;
  workflow: string;
  workflowOptions: string[];
  onSelect: (wf: string) => void;
  onClose: () => void;
}
export const MobileWorkflowPicker = ({
  open, workflow, workflowOptions, onSelect, onClose,
}: MobileWorkflowPickerProps) => {
  if (!open) return null;
  return (
    <div className="mob-sheet-backdrop" onClick={onClose}>
      <div
        className="mob-sheet"
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Select Workflow"
      >
        <div className="mob-sheet-handle" />
        <div className="mob-sheet-title">Select Workflow</div>
        <div className="mob-sheet-list">
          {(workflowOptions || []).map(wf => (
            <button
              key={wf}
              className={'mob-sheet-row' + (wf === workflow ? ' active' : '')}
              onClick={() => { onSelect(wf); onClose(); }}
            >
              <span className="mob-sheet-row-icon">
                {wf === workflow ? '✓' : ' '}
              </span>
              <span className="mob-sheet-row-label">{wf}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// ── MobileKebabMenu ───────────────────────────────────────────────────────
export interface MobileKebabMenuProps {
  open: boolean;
  onClose: () => void;
  stopAgent: () => void;
  exitAll: () => void;
}
export const MobileKebabMenu = ({ open, onClose, stopAgent, exitAll }: MobileKebabMenuProps) => {
  if (!open) return null;
  return (
    <div className="mob-sheet-backdrop" onClick={onClose}>
      <div
        className="mob-sheet mob-sheet-sm"
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="More options"
      >
        <div className="mob-sheet-handle" />
        <div className="mob-sheet-title">Options</div>
        <div className="mob-sheet-list">
          <button className="mob-sheet-row mob-sheet-danger"
                  onClick={() => { stopAgent(); onClose(); }}>
            <span className="mob-sheet-row-icon">■</span>
            <span className="mob-sheet-row-label">Stop agent</span>
          </button>
          <button className="mob-sheet-row mob-sheet-danger"
                  onClick={() => { exitAll(); onClose(); }}>
            <span className="mob-sheet-row-icon">✕</span>
            <span className="mob-sheet-row-label">Exit</span>
          </button>
        </div>
      </div>
    </div>
  );
};

// ── MobileHeader ──────────────────────────────────────────────────────────
// Compact 52px sticky header shown only on mobile (< 900px). Renders:
//   ☰  [IP: <name> ▾]  ORCH  ⋮
// The IP pill is the focal element; ORCH opens workflow picker; ⋮ opens
// a kebab menu with stop/exit. ☰ fires a CustomEvent caught by workspace.jsx
// drawer logic.
export interface MobileHeaderProps {
  activeIp: string;
  ipOptions: string[];
  onSelectIp: (ip: string) => void;
  onCreateIp: () => void;
  workflow: string;
  workflowOptions?: string[];
  onSelectWorkflow?: (wf: string) => void;
  onOpenLeftDrawer: () => void;
  onOpenRightDrawer: () => void;
  stopAgent: () => void;
  exitAll: () => void;
}
export const MobileHeader = ({
  activeIp, ipOptions, onSelectIp, onCreateIp,
  workflow,
  onOpenLeftDrawer, onOpenRightDrawer,
  stopAgent, exitAll,
}: MobileHeaderProps) => {
  const [ipPickerOpen,       setIpPickerOpen]       = useState(false);
  const [kebabOpen,          setKebabOpen]           = useState(false);

  // Wire workspace.jsx's existing drawer state through CustomEvents so the
  // MobileHeader doesn't need to own that state.
  useEffect(() => {
    const onLeft  = () => onOpenLeftDrawer();
    const onRight = () => onOpenRightDrawer();
    window.addEventListener('atlas:mobile-left-drawer-request',  onLeft);
    window.addEventListener('atlas:mobile-right-drawer-request', onRight);
    return () => {
      window.removeEventListener('atlas:mobile-left-drawer-request',  onLeft);
      window.removeEventListener('atlas:mobile-right-drawer-request', onRight);
    };
  }, [onOpenLeftDrawer, onOpenRightDrawer]);

  const ipLabel = (!activeIp || activeIp === 'default') ? 'default' : activeIp;
  const wfLabel = (!workflow || workflow === 'default') ? 'orch' : workflow;

  return (
    <div className="mob-header atlas-mobile-only">
      {/* ── Hamburger ── */}
      <button
        className="mob-header-btn mob-header-ham"
        aria-label="Open sidebar"
        onClick={onOpenLeftDrawer}
      >☰</button>

      {/* ── IP pill ── */}
      <button
        className="mob-ip-pill"
        aria-label={`Current IP: ${ipLabel}. Tap to change.`}
        onClick={() => setIpPickerOpen(true)}
      >
        <span className="mob-ip-pill-label">IP: {ipLabel}</span>
        <span className="mob-ip-pill-chevron">▾</span>
      </button>

      {/* ── Workflow chip ── */}
      <button
        className="mob-header-wf"
        aria-label={`Workflow: ${wfLabel}. Open sidebar to change.`}
        onClick={onOpenLeftDrawer}
      >{wfLabel.toUpperCase().slice(0, 6)}</button>

      {/* ── Kebab ── */}
      <button
        className="mob-header-btn mob-header-kebab"
        aria-label="More options"
        onClick={() => setKebabOpen(true)}
      >⋮</button>

      {/* ── Sheets ── */}
      <MobileIpPicker
        open={ipPickerOpen}
        activeIp={activeIp}
        ipOptions={ipOptions}
        onSelect={onSelectIp}
        onCreateIp={onCreateIp}
        onClose={() => setIpPickerOpen(false)}
      />
      <MobileKebabMenu
        open={kebabOpen}
        onClose={() => setKebabOpen(false)}
        stopAgent={stopAgent}
        exitAll={exitAll}
      />
    </div>
  );
};
