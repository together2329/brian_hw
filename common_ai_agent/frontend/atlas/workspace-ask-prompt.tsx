// workspace-ask-prompt.tsx — AskUserPrompt (chat-input ask_user prompt block).
//
// Extracted from workspace-panels.tsx (Phase 13g cluster split) to keep every
// file under 1000 lines. Shared types + the cross-file `w` cast + the
// AskUserQuestionBlock / Kbd forward-refs live in workspace-panel-shared.tsx.
// Still bridges window.AskUserPrompt at the bottom for not-yet-migrated .jsx
// consumers (workspace.jsx aliases it back).
import { type KeyboardEvent } from 'react';
import {
  w,
  AskUserQuestionBlock,
  Kbd,
  type AskOption,
  type AskTabState,
  type AskFlowQuestion,
  type AskFlow,
  type AskFlowState,
} from './workspace-panel-shared';

export interface AskUserPromptProps {
  flowId: string;
  state?: AskFlowState | null;
  sel: number;
  intent?: string;
  fullHeight?: boolean;
  onToggle: (flowId: string, optionId: string) => void;
  onCustom: (flowId: string, value: string) => void;
  onSubmit: (flowId: string) => void;
  onChat: (flowId: string) => void;
  onSel: (index: number) => void;
  onSetTab?: (flowId: string, index: number) => void;
  onAdvance?: (flowId: string) => void;
}

export const AskUserPrompt = ({ flowId, state, sel, intent, fullHeight = false, onToggle, onCustom, onSubmit, onChat, onSel, onSetTab, onAdvance }: AskUserPromptProps) => {
  const flow = w.QA_FLOWS[flowId];
  if (!flow || !state) return null;

  // Batched flow virtualization — derive the "view" for the active tab
  // and reuse all the existing single-question rendering below.
  const isBatched = !!state.batched;
  const tabCount = isBatched ? (flow.questions || []).length : 0;
  const active = isBatched ? (state.active || 0) : 0;
  const isSubmitTab = isBatched && active === tabCount;
  // Active tab view (used by the option/custom widgets below)
  const tabState: AskTabState = isBatched
    ? (state.states && state.states[active]) || { opts: [], custom: '' }
    : state;
  const tabFlowKind = isBatched && !isSubmitTab ? flow.questions![active].kind : flow.kind;
  const tabFlowMultiline = !!(isBatched && !isSubmitTab ? flow.questions![active].multiline : flow.multiline);
  const tabAnswered = (i: number): boolean => {
    const ts = state.states && state.states[i];
    if (!ts) return false;
    return (ts.opts || []).some(o => o.selected) || (ts.custom || '').trim().length > 0;
  };
  const allAnswered = isBatched
    ? (state.states || []).every((_, i) => tabAnswered(i))
    : true;

  const goNextBatchedStep = (): boolean => {
    if (!isBatched) return false;
    if (isSubmitTab) {
      if (allAnswered) onSubmit(flowId);
      return true;
    }
    if (active < tabCount - 1) {
      onAdvance ? onAdvance(flowId) : onSetTab && onSetTab(flowId, active + 1);
      return true;
    }
    if (allAnswered) {
      onSubmit(flowId);
    } else {
      onSetTab && onSetTab(flowId, tabCount);
    }
    return true;
  };

  const opts = tabState.opts || [];
  const customIdx = opts.length;       // row index for custom-text line
  const submitIdx = opts.length + 1;   // Submit menu line
  const chatIdx   = opts.length + 2;   // "Chat about this" menu line
  const lastIdx   = chatIdx;

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    // Batched flow: ⌘/⌃ + ←/→ moves the keyboard cursor between
    // question blocks (each Q renders its own block; the active block
    // is highlighted and owns the option/custom cursor).
    if (isBatched) {
      if (e.key === 'ArrowLeft' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.max(0, active - 1)); return;
      }
      if (e.key === 'ArrowRight' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.min(tabCount - 1, active + 1)); return;
      }
    }
    if (e.key === 'ArrowDown' || (e.key === 'j' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.min(sel + 1, lastIdx)); return;
    }
    if (e.key === 'ArrowUp' || (e.key === 'k' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.max(sel - 1, 0)); return;
    }
    if (e.key === ' ' && sel < opts.length) {
      // When focus is in the custom-answer input/textarea, space must
      // pass through to the field. Without this guard the parent
      // div's keydown intercepts and toggles the selected option
      // instead, swallowing every space the user types.
      const ae = document.activeElement;
      const aeTag = ae && ae.tagName;
      if (aeTag === 'INPUT' || aeTag === 'TEXTAREA' || (ae && (ae as HTMLElement).isContentEditable)) return;
      e.preventDefault(); onToggle(flowId, opts[sel].id); return;
    }
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      const activeEl = document.activeElement;
      const isCustomInput = activeEl && activeEl.classList && activeEl.classList.contains('askcustom');
      if (isCustomInput && tabFlowMultiline && !e.metaKey && !e.ctrlKey) return;
      e.preventDefault();
      // Custom-input Enter: in batched, advance to next question (or
      // submit-all on the last); in single, submit immediately when the
      // text isn't empty so a one-shot QA can be answered with Enter.
      if (isCustomInput) {
        if (isBatched) { goNextBatchedStep(); return; }
        if ((tabState.custom || '').trim() || opts.some(o => o.selected)) {
          onSubmit(flowId);
        }
        return;
      }
      if (sel < opts.length) {
        onToggle(flowId, opts[sel].id);
        // Batched + single-kind: advance to next question (or submit
        // when on the last one and everything else is answered).
        if (isBatched && tabFlowKind !== 'multi') { goNextBatchedStep(); return; }
        // Non-batched + single-kind (one-question flow): Enter
        // immediately submits — the user just picked their answer.
        if (!isBatched && tabFlowKind === 'single') { onSubmit(flowId); return; }
        return;
      }
      if (sel === customIdx) {
        if (isBatched && (tabState.custom || '').trim()) { goNextBatchedStep(); return; }
        const el = e.currentTarget.querySelector('input.askcustom, textarea.askcustom') as HTMLElement | null; el?.focus(); return;
      }
      if (sel === submitIdx) {
        if (isBatched) { if (allAnswered) onSubmit(flowId); return; }
        onSubmit(flowId);
        return;
      }
      if (sel === chatIdx)   { onChat(flowId); return; }
    }
    if (e.key === 'Escape') { e.preventDefault(); onSel(0); }
  };

  const renderQuestionBlock = (i: number, block: AskFlow | AskFlowQuestion, bs: AskTabState, kind: string | undefined) => (
    <AskUserQuestionBlock
      key={i}
      index={i}
      block={block}
      blockState={bs}
      kind={kind}
      isBatched={isBatched}
      isActive={!isBatched || i === active}
      answered={tabAnswered(i)}
      selectedIndex={sel}
      onEnsureActive={(idx: number) => {
        if (isBatched && idx !== active && onSetTab) onSetTab(flowId, idx);
      }}
      onSelectIndex={onSel}
      onToggleOption={(optionId: string) => onToggle(flowId, optionId)}
      onCustom={(value: string) => onCustom(flowId, value)}
      onSelectAll={(blockOpts: AskOption[]) => {
        blockOpts.forEach(o => { if (!o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
      onClearAll={(blockOpts: AskOption[]) => {
        blockOpts.forEach(o => { if (o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
    />
  );

  return (
    <div
      className="ask-prompt fade-in"
      tabIndex={0}
      onKeyDown={onKey}
      style={{
        border: `1px solid var(--accent)`,
        borderLeftWidth: 3,
        background: 'var(--bg-2)',
        padding: '10px 14px 8px',
        outline: 'none',
        boxShadow: '0 -2px 0 0 color-mix(in oklch, var(--accent) 25%, transparent)',
        height: fullHeight ? '100%' : undefined,
        minHeight: fullHeight ? 0 : undefined,
        overflow: fullHeight ? 'auto' : undefined,
      }}
    >
      {/* header — mimics the screenshot: "▸ ask_user · ✓ Submit" */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8,
        fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ ask_user</span>
        <span className="mute">·</span>
        <span className="ok" style={{ fontWeight: 600, opacity: sel === submitIdx ? 1 : 0.6 }}>✓ Submit</span>
        <span className="mute">·</span>
        <span className="mute">{flow.stage} · step {flow.step}/{flow.total}</span>
        <span style={{ flex: 1 }} />
        {intent === 'plan' && (
          <span className="warn" style={{ fontSize: 10, fontWeight: 700 }}>◐ plan mode · still asks</span>
        )}
        <span className="mute" style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10 }}>
          {tabFlowKind === 'multi' ? 'multi-select' : tabFlowKind === 'input' ? 'text' : 'single-select'}
        </span>
        {isBatched && (
          <span
            className={allAnswered ? 'ok' : 'mute'}
            style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10, marginLeft: 6, fontWeight: 600 }}
          >
            · {(state.states || []).filter((_, i) => tabAnswered(i)).length}/{tabCount} answered
          </span>
        )}
      </div>

      {/* questions — single block when not batched, stacked blocks when batched */}
      {isBatched
        ? (flow.questions || []).map((q, i) => {
            const ts = (state.states || [])[i] || { opts: [], custom: '' };
            const k = q.kind === 'multi' ? 'multi' : q.kind === 'input' ? 'input' : 'single';
            return renderQuestionBlock(i, q, ts, k);
          })
        : renderQuestionBlock(0, flow, state, tabFlowKind)}

      {/* submit row — for batched, gates on allAnswered and submits all */}
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 0 }}>
        <div
          onClick={() => {
            if (isBatched) { if (allAnswered) onSubmit(flowId); }
            else onSubmit(flowId);
          }}
          style={{
            padding: '4px 8px',
            background: sel === submitIdx ? 'color-mix(in oklch, var(--ok) 18%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === submitIdx ? 'var(--ok)' : 'transparent'}`,
            cursor: (isBatched && !allAnswered) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
            color: sel === submitIdx ? 'var(--ok)' : 'var(--fg)',
            fontWeight: sel === submitIdx ? 600 : 400,
            opacity: (isBatched && !allAnswered) ? 0.6 : 1,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>
          {isBatched ? `Submit all (${(state.states || []).filter((_, i) => tabAnswered(i)).length}/${tabCount})` : 'Submit'}
          {!isBatched && (
            <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>
              ({(opts.filter(o => o.selected) || []).length}{tabState.custom ? '+1' : ''} reply)
            </span>
          )}
        </div>
        <div
          onClick={() => { onSel(chatIdx); onChat(flowId); }}
          style={{
            padding: '4px 8px',
            background: sel === chatIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === chatIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>Chat about this
          <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(send a free-form message instead)</span>
        </div>
      </div>

      {/* hint footer — terminal-style */}
      <div className="mute" style={{
        marginTop: 8, paddingTop: 6, borderTop: '1px dashed var(--line)',
        fontSize: 'var(--ui-control-font-size)', display: 'flex', gap: 14, flexWrap: 'wrap',
      }}>
        <span><Kbd>↵</Kbd> {isBatched ? 'select & next' : 'select & submit'}</span>
        <span><Kbd>↑↓</Kbd>/<Kbd>j k</Kbd> navigate</span>
        <span><Kbd>Space</Kbd> toggle</span>
        <span><Kbd>Tab</Kbd> next field</span>
        {isBatched && <span><Kbd>⌘/⌃ ←→</Kbd> switch question</span>}
        <span><Kbd>Esc</Kbd> top</span>
      </div>
    </div>
  );
};

(window as unknown as { AskUserPrompt: typeof AskUserPrompt }).AskUserPrompt = AskUserPrompt;
