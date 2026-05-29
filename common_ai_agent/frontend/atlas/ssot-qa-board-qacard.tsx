// ssot-qa-board-qacard.tsx — TypeScript migration + split of the QA-card render
// subtree extracted from ssot-qa-board.jsx (Phase 13f / TS-split).
//
// Holds:
//   - The PURE pending-answer helpers (pendingItemKey, optionRows, pendingKind,
//     pendingDraft, hasPendingAnswer, buildPendingInputText). These are also
//     consumed by the main component's global "submit all pending" bar, so they
//     are exported AND window-bridged.
//   - The <QaCard> component, which is the legacy `renderQa(item, status)`
//     (lines 880-958) plus its inline `renderPendingAnswerBox(item)` (802-879).
//     Closure state that those functions read (answerDrafts, closedCardKeys and
//     their setters, onSubmitPending, the resolved string table `t`, and `ip`)
//     is threaded in as explicit props — behavior is identical.
//
// Cross-file dep: AskUserQuestionBlock + atlasStatusMeta are owned by the
// (unmigrated) workspace.jsx. They are read through window at call time via the
// lambda forward-ref pattern, exactly like the legacy IIFE header did.
//
// Load order (index.html): BEFORE ssot-qa-board.tsx. The main component reads
// QaCard + the helpers through the transitional window bridges.
import { useRef, useState, type CSSProperties, type KeyboardEvent, type MouseEvent } from 'react';

import type { SsotQaStrings } from './ssot-qa-board-i18n';

// ── Cross-file globals owned by OTHER (unmigrated) files. Resolved at call
// time so module-eval ordering does not matter. ──
interface QaCardWindowGlobals {
  AskUserQuestionBlock: (...a: any[]) => any;
  atlasStatusMeta: (...a: any[]) => { color: string; [k: string]: unknown };
  // Optional connection-state getter exposed by backend.js. Returns a lowercase
  // string ('open' | 'connecting' | 'closed' | ...). Read defensively.
  backend?: { getConnectionState?: () => string };
  // This file's OWN public globals (set via the bridge below).
  SsotQaCard: (props: QaCardProps) => any;
  ssotPendingItemKey: typeof pendingItemKey;
  ssotOptionRows: typeof optionRows;
  ssotPendingKind: typeof pendingKind;
  ssotPendingDraft: typeof pendingDraft;
  ssotHasPendingAnswer: typeof hasPendingAnswer;
  ssotBuildPendingInputText: typeof buildPendingInputText;
}
const g = window as unknown as QaCardWindowGlobals;

// Forward-ref to workspace.jsx helpers (resolved at call time):
const AskUserQuestionBlock = (...a: any[]): any => g.AskUserQuestionBlock(...a);
const atlasStatusMeta = (...a: any[]): { color: string; [k: string]: unknown } => g.atlasStatusMeta(...a);

// ── Shared loose types for QA items / answer drafts ──────────────────
// QA items come straight from backend JSON — keep them permissive.
export interface QaItem {
  flow_id?: string;
  section?: string;
  section_id?: string;
  decision_key?: string;
  source?: string;
  question?: string;
  question_kind?: string;
  kind?: string;
  decision_label?: string;
  subtitle?: string;
  options?: unknown;
  answer?: unknown;
  answer_data?: unknown;
  [k: string]: unknown;
}
export interface QaOption {
  id: string;
  label: string;
  detail?: string;
  selected?: boolean;
  [k: string]: unknown;
}
export interface QaDraft {
  opts: QaOption[];
  custom: string;
}
export type AnswerDrafts = Record<string, QaDraft>;

// ── Pure helpers (legacy lines 699-786). No component-state closure. ─────
export function pendingItemKey(item: QaItem | null | undefined): string {
  return [
    item?.flow_id || '',
    item?.section || item?.section_id || '',
    item?.decision_key || item?.source || item?.question || '',
  ].join(':');
}

export function optionRows(item: QaItem | null | undefined): QaOption[] {
  return (
    Array.isArray(item?.options) ? item!.options : []
  ).map((option: any, idx: number) => {
    const raw = option && typeof option === 'object' ? option : { id: option, label: option };
    const id = String(raw.id ?? raw.value ?? raw.label ?? idx);
    const label = String(raw.label ?? raw.title ?? raw.value ?? raw.id ?? `Option ${idx + 1}`);
    const detail = raw.detail || raw.description || '';
    return { ...raw, id, label, detail } as QaOption;
  });
}

export function pendingKind(item: QaItem | null | undefined): 'multi' | 'input' | 'single' {
  const kind = String(item?.question_kind || item?.kind || '').toLowerCase();
  if (kind === 'multi' || kind === 'multiple' || kind === 'checkbox') return 'multi';
  if (kind === 'input' || kind === 'text' || kind === 'freeform') return 'input';
  return optionRows(item).length ? 'single' : 'input';
}

export function pendingDraft(item: QaItem | null | undefined, answerDrafts: AnswerDrafts): QaDraft {
  const key = pendingItemKey(item);
  const stored = answerDrafts[key];
  const rows = optionRows(item);
  if (stored) {
    const selected = new Set((stored.opts || []).filter(o => o.selected).map(o => String(o.id)));
    return {
      opts: rows.map(option => ({ ...option, selected: selected.has(option.id) })),
      custom: stored.custom || '',
    };
  }
  // No in-memory edit yet → seed from the saved answer so approved/answered
  // cards open with their previous selection pre-checked. The seed is
  // matched by option id, label, or value (whichever is in the answer
  // payload). If we cannot match an option, fall back to dropping the
  // entire saved blob into the custom note.
  const ans: any = item?.answer_data || item?.answer || '';
  const seedSelected = new Set<string>();
  let seedCustom = '';
  if (ans && typeof ans === 'object') {
    const sel = Array.isArray(ans.selected) ? ans.selected : [];
    sel.forEach((s: unknown) => {
      const tok = String(s || '').trim();
      if (!tok) return;
      const match = rows.find(o => String(o.id) === tok || String(o.label) === tok);
      if (match) seedSelected.add(String(match.id));
    });
    seedCustom = String(ans.answer || ans.note || ans.custom || '').trim();
  } else if (typeof ans === 'string' && ans.trim()) {
    const txt = ans.trim();
    const match = rows.find(o => String(o.label) === txt || String(o.id) === txt);
    if (match) seedSelected.add(String(match.id));
    else seedCustom = txt;
  }
  return {
    opts: rows.map(option => ({ ...option, selected: seedSelected.has(option.id) })),
    custom: seedCustom,
  };
}

export function hasPendingAnswer(draft: QaDraft | null | undefined): boolean {
  return (
    (draft?.opts || []).some(o => o.selected)
  ) || String(draft?.custom || '').trim().length > 0;
}

export function buildPendingInputText(
  item: QaItem,
  draft: QaDraft,
  ip: string,
): string {
  const selectedRows = (draft?.opts || []).filter(option => option.selected);
  const selectedLines = selectedRows.map(option => (
    option.detail ? `  - ${option.label} (${option.id}): ${option.detail}` : `  - ${option.label} (${option.id})`
  ));
  const custom = String(draft?.custom || '').trim();
  const lines: string[] = [];
  const headerKey = item.decision_key ? ` · ${item.decision_key}` : '';
  lines.push(`### Answer pending QA — ${ip}${headerKey}`);
  if (item.decision_label && item.decision_label !== item.question) {
    lines.push(`Decision: ${item.decision_label}`);
  }
  lines.push(`Question: ${item.question || item.decision_label || 'Untitled question'}`);
  if (item.subtitle) lines.push(`Context : ${item.subtitle}`);
  if (selectedLines.length) {
    lines.push('Selected:');
    lines.push(...selectedLines);
  }
  if (custom) lines.push(`Note    : ${custom}`);
  if (!selectedLines.length && !custom) {
    lines.push('Answer  : <choose option or type note>');
  }
  lines.push('Apply this answer to SSOT-GEN QA and continue the current workflow.');
  return lines.join('\n');
}

// ── <QaCard> — legacy renderQa + renderPendingAnswerBox (lines 802-958) ──
// onSubmitPending mirrors the legacy parent callback:
//   onSubmitPending(bundle, combinedText) where bundle = [{ item, draft }].
export interface QaCardProps {
  item: QaItem;
  status: string;
  t: SsotQaStrings;
  ip: string;
  answerDrafts: AnswerDrafts;
  closedCardKeys: Set<string>;
  setClosedCardKeys: (updater: (prev: Set<string>) => Set<string>) => void;
  updatePendingDraft: (item: QaItem, draft: QaDraft) => void;
  onSubmitPending?: (bundle: Array<{ item: QaItem; draft: QaDraft }>, text: string) => void;
}

export function QaCard({
  item,
  status,
  t,
  ip,
  answerDrafts,
  closedCardKeys,
  setClosedCardKeys,
  updatePendingDraft,
  onSubmitPending,
}: QaCardProps) {
  const draftOf = (it: QaItem): QaDraft => pendingDraft(it, answerDrafts);

  // Transient in-board confirmation after a send/re-answer click, so the action
  // is never perceived as a no-op (the parent immediately switches to the chat
  // tab, so any feedback rendered here is short-lived but proves the click
  // landed). Holds the i18n message to show, or '' when idle.
  const [sentFeedback, setSentFeedback] = useState('');
  const sentTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flashSent = (message: string): void => {
    setSentFeedback(message);
    if (sentTimerRef.current) clearTimeout(sentTimerRef.current);
    sentTimerRef.current = setTimeout(() => setSentFeedback(''), 4000);
  };
  // Read the optional backend connection-state getter defensively. Returns
  // 'open' (lowercase) when the websocket is live; anything else means the
  // submit will be queued/retried rather than delivered immediately.
  const isBackendOpen = (): boolean => {
    try {
      const getState = g.backend?.getConnectionState;
      if (typeof getState !== 'function') return true; // no getter → assume OK
      return String(getState() || '').toLowerCase() === 'open';
    } catch {
      return true;
    }
  };

  const togglePendingOption = (it: QaItem, optionId: string): void => {
    const draft = draftOf(it);
    const kind = pendingKind(it);
    const opts = (draft.opts || []).map(option => {
      if (kind === 'multi') {
        return option.id === optionId ? { ...option, selected: !option.selected } : option;
      }
      return { ...option, selected: option.id === optionId };
    });
    updatePendingDraft(it, { ...draft, opts });
  };

  const renderPendingAnswerBox = (it: QaItem, resolved: boolean) => {
    const draft = draftOf(it);
    const kind = pendingKind(it);
    const hasAnswer = hasPendingAnswer(draft);
    // When the card is already resolved (approved), the send button is a
    // re-submit. Relabel it ("re-answer") + use a secondary (outlined) style so
    // the user is not surprised that a 0-pending card still accepts input.
    const sendLabel = resolved ? (t.reAnswer || t.send) : t.send;
    const sendActiveBg = resolved ? 'transparent' : 'var(--cyan)';
    const sendActiveColor = resolved ? 'var(--cyan)' : 'var(--bg-0)';
    const sendActiveBorder = resolved ? '1px solid var(--cyan)' : undefined;
    return (
      <div
        onClick={(ev) => ev.stopPropagation()}
        onKeyDown={(ev) => ev.stopPropagation()}
        style={{
          marginTop: 8,
          paddingTop: 8,
          borderTop: '1px solid var(--line)',
      }}>
        <div style={{ color: 'var(--fg-mute)', fontSize: 10, marginBottom: 6 }}>
          {kind === 'multi' ? t.selectMany : (kind === 'single' ? t.selectOne : t.typedAnswer)}
        </div>
        {!draft.opts.length ? (
          <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 6 }}>{t.noOptions}</div>
        ) : null}
        <AskUserQuestionBlock
          index={0}
          block={{
            question: it.question || it.decision_label || '',
            subtitle: it.subtitle || '',
            placeholder: kind === 'input' ? t.typedAnswer : t.customNote,
            multiline: kind === 'input',
          }}
          blockState={draft}
          kind={kind}
          isBatched={false}
          isActive={true}
          selectedIndex={-1}
          showQuestion={false}
          onToggleOption={(optionId: string) => togglePendingOption(it, optionId)}
          onCustom={(value: string) => updatePendingDraft(it, { ...draftOf(it), custom: value })}
          onSelectAll={() => updatePendingDraft(it, {
            ...draft,
            opts: (draft.opts || []).map(option => ({ ...option, selected: true })),
          })}
          onClearAll={() => updatePendingDraft(it, {
            ...draft,
            opts: (draft.opts || []).map(option => ({ ...option, selected: false })),
          })}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
          <span
            style={{
              color: sentFeedback ? 'var(--ok)' : (hasAnswer ? 'var(--cyan)' : 'var(--fg-mute)'),
              fontSize: 10,
            }}
          >
            {sentFeedback || (hasAnswer ? t.inputUpdated : t.autoInputHint)}
          </span>
          <span style={{ flex: 1 }} />
          {onSubmitPending ? (
            <button
              type="button"
              className="mini-btn"
              disabled={!hasAnswer}
              title={
                !hasAnswer
                  ? t.sendNeedAnswer
                  : (resolved ? t.reAnswerHint : '')
              }
              onClick={(ev: MouseEvent<HTMLButtonElement>) => {
                ev.stopPropagation();
                if (!hasAnswer) return;
                // Immediate in-board confirmation BEFORE the parent flips to the
                // chat tab, so the click is never perceived as a no-op. Surface a
                // retry hint when the backend socket is not open.
                flashSent(isBackendOpen() ? t.sent : t.notConnectedRetry);
                onSubmitPending(
                  [{ item: it, draft }],
                  buildPendingInputText(it, draft, ip),
                );
              }}
              style={{
                background: hasAnswer ? sendActiveBg : undefined,
                color: hasAnswer ? sendActiveColor : undefined,
                border: hasAnswer ? sendActiveBorder : undefined,
                fontWeight: hasAnswer ? 600 : undefined,
                opacity: hasAnswer ? 1 : 0.45,
                cursor: hasAnswer ? 'pointer' : 'not-allowed',
              }}
            >
              {sendLabel}
            </button>
          ) : null}
        </div>
      </div>
    );
  };

  const key = pendingItemKey(item);
  const isPending = status === 'pending';
  const isApproved = status === 'approved';
  // All QA cards (pending and approved) default OPEN. Approved cards
  // can be re-opened to amend the saved answer (re-select / re-submit).
  const isOpen = (isPending || isApproved) && !closedCardKeys.has(key);
  const statusColor = atlasStatusMeta(status).color;
  const cardToggleable = isPending || isApproved;
  const togglePendingCard = (): void => {
    if (!cardToggleable) return;
    setClosedCardKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };
  const handleCardKey = (ev: KeyboardEvent<HTMLDivElement>): void => {
    if (!cardToggleable) return;
    if (ev.key === 'Enter' || ev.key === ' ') {
      ev.preventDefault();
      togglePendingCard();
    }
  };
  return (
    <div
      key={key}
      role={cardToggleable ? 'button' : undefined}
      tabIndex={cardToggleable ? 0 : undefined}
      onClick={cardToggleable ? togglePendingCard : undefined}
      onKeyDown={cardToggleable ? handleCardKey : undefined}
      title={cardToggleable ? (isOpen ? 'Click to collapse' : 'Click to expand') : undefined}
      style={{
        padding: '8px 10px',
        border: '1px solid var(--line)',
        borderLeft: `3px solid ${statusColor}`,
        background: status === 'approved'
          ? 'color-mix(in oklch, var(--ok) 7%, transparent)'
          : 'color-mix(in oklch, var(--warn) 8%, transparent)',
        marginBottom: 8,
        fontFamily: 'var(--mono)',
        cursor: cardToggleable ? 'pointer' : 'default',
      } as CSSProperties}
    >
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
        <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
          {item.decision_key || item.source || 'qa'}
        </span>
        <span style={{ flex: 1 }} />
        {cardToggleable ? (
          <span
            aria-hidden="true"
            style={{
              color: 'var(--fg-mute)',
              fontSize: 10,
              fontFamily: 'var(--mono)',
              userSelect: 'none',
            }}
          >
            {isOpen ? '▾' : '▸'}
          </span>
        ) : null}
      </div>
      <div style={{ color: 'var(--fg)', fontSize: 12, lineHeight: 1.45 }}>
        {item.question || item.decision_label || 'Untitled question'}
      </div>
      {item.subtitle ? (
        <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginTop: 3 }}>
          {item.subtitle}
        </div>
      ) : null}
      {isOpen ? renderPendingAnswerBox(item, isApproved) : null}
      <div style={{ color: item.answer ? 'var(--fg)' : 'var(--fg-mute)', fontSize: 12, marginTop: 7, lineHeight: 1.45 }}>
        {(item.answer as any) || t.noAnswer}
      </div>
    </div>
  );
}

// ── Transitional bridge: register on window for call-time resolution. ──
g.SsotQaCard = QaCard;
g.ssotPendingItemKey = pendingItemKey;
g.ssotOptionRows = optionRows;
g.ssotPendingKind = pendingKind;
g.ssotPendingDraft = pendingDraft;
g.ssotHasPendingAnswer = hasPendingAnswer;
g.ssotBuildPendingInputText = buildPendingInputText;
