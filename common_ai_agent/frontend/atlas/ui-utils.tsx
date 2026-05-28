// ui-utils.tsx — TypeScript migration of ui-utils.jsx (Phase TS-1, the first
// file migrated off the in-browser-babel + window-global pattern).
//
// What changed vs ui-utils.jsx:
//   - Proper ES module: `import { useState } from 'react'` instead of the
//     ambient global `React` + `<script type="text/babel">` in-browser compile.
//   - Real typed exports (`CopyBtn`, `copyToClipboard`) — consumers will
//     `import` these once they migrate.
//   - Strict types: the `window._copyToClipboard` call is checked against the
//     ambient Window declaration in types/atlas-window.d.ts, so a typo in the
//     global name is a COMPILE error (the exact `window.X is not a function`
//     bug class that broke boot repeatedly during the .jsx refactor).
//
// Transitional: still bridges to `window.*` at the bottom so not-yet-migrated
// .jsx files keep resolving `window.CopyBtn` / `window._copyToClipboard`.
import { useState, type MouseEvent } from 'react';

// Copy that works over plain-HTTP LAN access too. navigator.clipboard only
// exists in secure contexts (https / localhost); when opened via
// http://<lan-ip>:3000 it is undefined, so fall back to a hidden-textarea
// execCommand('copy').
export function copyToClipboard(value: unknown): boolean {
  const text = String(value == null ? '' : value);
  try {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text);
      return true;
    }
  } catch (_) {
    /* fall through to execCommand */
  }
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, text.length);
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
  } catch (_) {
    return false;
  }
}

export interface CopyBtnProps {
  text?: string;
  label?: string;
}

export function CopyBtn({ text, label = 'copy' }: CopyBtnProps) {
  const [copied, setCopied] = useState(false);
  const onClick = (e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (copyToClipboard(text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  };
  return (
    <button
      onClick={onClick}
      className="copy-btn"
      type="button"
      style={{
        position: 'absolute',
        top: 6,
        right: 6,
        opacity: 0,
        transition: 'opacity .15s',
        background: 'var(--bg-2)',
        border: '1px solid var(--line)',
        color: copied ? 'var(--ok)' : 'var(--fg-mute)',
        fontSize: 10,
        padding: '1px 6px',
        borderRadius: 2,
        cursor: 'pointer',
        fontFamily: 'var(--mono)',
      }}
    >
      {copied ? '✓ copied' : label}
    </button>
  );
}

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Type-checked against types/atlas-window.d.ts. Remove once all consumers
// import { CopyBtn, copyToClipboard } directly.
window._copyToClipboard = copyToClipboard;
window.CopyBtn = CopyBtn;
