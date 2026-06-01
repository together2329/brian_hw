import { buildSsotDocChatPrefillText } from './ssot-doc-feedback-api';
import type {
  SsotDocChatPrefillContext,
  SsotDocCommentEventDetail,
  SsotDocSelectedTarget,
} from './ssot-doc-feedback-types';

type ClosestCapableTarget = EventTarget & {
  readonly closest?: (selector: string) => Element | null;
  readonly parentElement?: Element | null;
};

function hasClosest(value: object): value is { closest: (selector: string) => Element | null } {
  const candidate = value as { closest?: unknown };
  return typeof candidate.closest === 'function';
}

function hasParentElement(value: object): value is { readonly parentElement?: Element | null } {
  return 'parentElement' in value;
}

export function findSsotDocSelectableElement(node: EventTarget | null): Element | null {
  if (!node || typeof node !== 'object') return null;
  if (hasClosest(node)) {
    return node.closest('[data-ssot-path]');
  }
  if (hasParentElement(node)) {
    return node.parentElement?.closest('[data-ssot-path]') || null;
  }
  return null;
}

export function buildSsotDocTargetFromElement(node: ClosestCapableTarget | null): SsotDocSelectedTarget | null {
  const el = findSsotDocSelectableElement(node);
  if (!el) return null;
  const path = String(el.getAttribute('data-ssot-path') || '').trim();
  if (!path) return null;
  const section = String(el.getAttribute('data-ssot-section') || path.split('.')[0] || 'custom').trim();
  return {
    section,
    path,
    label: String(el.getAttribute('data-ssot-label') || el.textContent || path).trim() || path,
    kind: String(el.getAttribute('data-ssot-kind') || 'component').trim() || 'component',
  };
}

export function dispatchSsotDocComment(context: SsotDocChatPrefillContext): void {
  const detail: SsotDocCommentEventDetail = {
    ...context,
    text: buildSsotDocChatPrefillText(context),
  };
  window.dispatchEvent(new CustomEvent<SsotDocCommentEventDetail>('atlas-ssot-doc-comment', { detail }));
}

export function clearSsotDocSelection(doc: Document): void {
  doc.querySelectorAll('[data-atlas-doc-feedback-selected="1"]').forEach(el => {
    el.removeAttribute('data-atlas-doc-feedback-selected');
  });
}

export function markSsotDocSelection(el: Element): void {
  const doc = el.ownerDocument;
  if (doc) clearSsotDocSelection(doc);
  el.setAttribute('data-atlas-doc-feedback-selected', '1');
  if (typeof el.scrollIntoView === 'function') {
    el.scrollIntoView({ block: 'center', inline: 'nearest' });
  }
}
