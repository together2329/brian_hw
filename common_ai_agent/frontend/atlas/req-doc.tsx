// req-doc.tsx — ReqDocPane: the REQ tab.
//
// Renders the per-IP REQ bundle (requirements + obligations + contract +
// evidence + approval/lock) as one human-reviewable HTML document, served by
// GET /api/req/export and shown inside an iframe — the same render-in-iframe
// pattern as the DOC tab (SsotDocPane in ssot-doc.tsx).
//
// The server aggregates the locked-truth bundle read-only; this component only
// builds the export URL (with the chosen ?variant=) and frames the result. It
// registers on window.ReqDocPane so workspace-root.tsx can pick it up via its
// windowPanel() bridge (mirrors how SsotDocPane is consumed), and main.tsx
// side-effect-imports this module so the registration runs at boot.
import { useState, type ReactNode } from 'react';
import { appendActiveSessionParam } from './active-session-query';

// Cross-file window globals owned by the not-yet-migrated workspace.jsx; mirror
// the loose runtime shapes used by ssot-doc.tsx for the same IP fallback.
interface ReqDocWindow {
  ACTIVE_IP?: string;
  ssotIpFromSession?: (session: unknown) => string;
  ACTIVE_SESSION?: unknown;
}
const reqWin = window as unknown as ReqDocWindow;

type ReqVariant = 'full' | 'core4';

export interface ReqDocPaneProps {
  uiLang?: string;
  ip?: string;
  onBack?: () => void;
}

export const ReqDocPane = ({ uiLang = 'ko', ip = '', onBack }: ReqDocPaneProps): ReactNode => {
  const [reloadKey, setReloadKey] = useState(0);
  const [variant, setVariant] = useState<ReqVariant>('full');

  const effectiveIp = String(
    ip || reqWin.ACTIVE_IP || reqWin.ssotIpFromSession?.(reqWin.ACTIVE_SESSION) || '',
  ).trim();

  const inlineParams = effectiveIp
    ? appendActiveSessionParam(new URLSearchParams({
        ip: effectiveIp,
        format: 'html',
        variant,
        inline: '1',
        v: String(reloadKey),
      }))
    : null;
  const inlineUrl = inlineParams ? `/api/req/export?${inlineParams.toString()}` : '';
  const downloadParams = effectiveIp
    ? appendActiveSessionParam(new URLSearchParams({ ip: effectiveIp, format: 'html', variant }))
    : null;
  const downloadUrl = downloadParams ? `/api/req/export?${downloadParams.toString()}` : '';

  const title = uiLang === 'en' ? 'REQ Bundle' : 'REQ Bundle';
  const subtitle = uiLang === 'en'
    ? 'Requirements · obligations · contract · evidence in one reviewable view.'
    : 'requirements · obligations · contract · evidence를 한 화면에 모아 리뷰합니다.';

  if (!effectiveIp) {
    return (
      <div style={{ flex: 1, minHeight: 0, padding: 18, color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>
        No active IP for REQ rendering.
      </div>
    );
  }

  return (
    <div style={{
      flex: 1,
      minHeight: 0,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      background: 'var(--bg)',
    }}>
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid var(--line)',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'var(--bg-2)',
        fontFamily: 'var(--mono)',
      }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{
            color: 'var(--accent)',
            fontWeight: 800,
            fontSize: 12,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>{title}</div>
          <div className="mute trunc" style={{ marginTop: 3, fontSize: 'var(--ui-control-font-size)' }}>
            {effectiveIp} · {subtitle}
          </div>
        </div>
        <button type="button" className="btn" onClick={() => setReloadKey(k => k + 1)} style={{ fontSize: 10 }}>
          refresh
        </button>
        <div style={{ display: 'inline-flex', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
          {([
            ['full', uiLang === 'en' ? 'Full' : 'Full'],
            ['core4', uiLang === 'en' ? 'Compact' : 'Compact'],
          ] as Array<[ReqVariant, string]>).map(([mode, label], idx) => (
            <button
              key={mode}
              type="button"
              onClick={() => setVariant(mode)}
              style={{
                border: 0,
                borderRight: idx === 0 ? '1px solid var(--line)' : 0,
                background: variant === mode ? 'var(--accent)' : 'var(--bg)',
                color: variant === mode ? 'var(--bg)' : 'var(--fg-mute)',
                fontFamily: 'var(--mono)',
                fontSize: 10,
                fontWeight: 800,
                padding: '4px 8px',
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <button type="button" className="btn" onClick={() => { window.location.href = downloadUrl; }} style={{ fontSize: 10 }}>
          download
        </button>
        <button type="button" className="btn" onClick={onBack} style={{ fontSize: 10 }}>
          chat
        </button>
      </div>
      <div style={{
        flex: 1,
        minHeight: 0,
        padding: 12,
        background: 'var(--bg)',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <iframe
          key={inlineUrl}
          title={`${effectiveIp} REQ bundle`}
          data-testid="req-doc-frame"
          src={inlineUrl}
          style={{
            width: '100%',
            flex: 1,
            minHeight: 0,
            border: '1px solid var(--line)',
            background: '#fff',
          }}
        />
      </div>
    </div>
  );
};

// Transitional bridge: register on window so workspace-root.tsx's
// windowPanel('ReqDocPane', …) resolves the component (mirrors SsotDocPane).
(window as unknown as { ReqDocPane: typeof ReqDocPane }).ReqDocPane = ReqDocPane;
