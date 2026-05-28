// ui-utils.jsx — small frontend utilities extracted from workspace.jsx.
//
// Phase 13e of refactor/atlas-modular (first frontend extraction): isolate
// the cross-cutting copy-to-clipboard helper + the floating "copy" button.
// Both register on `window` so workspace.jsx (and any other jsx) can use
// them via window.<name>. index.html loads this BEFORE workspace.jsx.

// Copy that works over plain-HTTP LAN access too. navigator.clipboard only
// exists in secure contexts (https / localhost); when the app is opened via
// http://<lan-ip>:3000 it is undefined, so every copy button hit the catch
// and silently no-op'd. Fall back to a hidden-textarea execCommand('copy').
window._copyToClipboard = (value) => {
  const text = String(value == null ? '' : value);
  try {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text);
      return true;
    }
  } catch (_) {}
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
};

window.CopyBtn = ({ text, label = 'copy' }) => {
  const [copied, setCopied] = React.useState(false);
  const onClick = (e) => {
    e.stopPropagation();
    if (window._copyToClipboard(text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  };
  return (
    <button onClick={onClick} className="copy-btn" type="button"
      style={{
        position: 'absolute', top: 6, right: 6,
        opacity: 0, transition: 'opacity .15s',
        background: 'var(--bg-2)', border: '1px solid var(--line)',
        color: copied ? 'var(--ok)' : 'var(--fg-mute)',
        fontSize: 10, padding: '1px 6px', borderRadius: 2,
        cursor: 'pointer', fontFamily: 'var(--mono)',
      }}>
      {copied ? '✓ copied' : label}
    </button>
  );
};
