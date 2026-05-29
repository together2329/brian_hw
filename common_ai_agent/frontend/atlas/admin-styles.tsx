// admin-styles.tsx — TypeScript migration of the style objects extracted from
// admin.jsx (strangler-fig split, sub-1000 line refactor).
//
// These were all `const xStyle = {...}` declared INSIDE the AdminPage component
// in admin.jsx. They are pure presentation values (no component state), so they
// move out verbatim. The only exceptions are the two styles that closed over
// component state — `btnDangerStyle` (reads `deleting`) and `loginButtonStyle`
// (reads `loginSubmitting`) — which become factory functions taking that value
// as an argument so behavior is identical.
//
// Cross-file: this file owns no window globals; it only exports typed style
// values consumed by the admin-*.tsx family. Object literals are typed as
// React.CSSProperties so they slot into `style={...}` props with no behavior
// change.
import type { CSSProperties } from 'react';

export const pageStyle: CSSProperties = {
  width: '100%',
  height: '100%',
  background: '#11161c',
  color: '#d6dde6',
  fontFamily: "var(--mono, 'Inter', 'Noto Sans KR', system-ui, sans-serif)",
  fontSize: 14,
  lineHeight: 1.5,
  overflow: 'auto',
  display: 'flex',
  flexDirection: 'column',
};

export const headerStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '20px 32px',
  borderBottom: '1px solid #2a3540',
  background: '#141a21',
};

export const logoStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 12,
  fontSize: 22,
  fontWeight: 700,
  letterSpacing: '0.04em',
  color: '#f0c674',
};

export const badgeStyle: CSSProperties = {
  fontSize: 10,
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  padding: '3px 8px',
  borderRadius: 4,
  background: '#2a3a4a',
  color: '#f0c674',
  border: '1px solid #3a4756',
};

export const headerRightStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
};

export const headerButtonStyle: CSSProperties = {
  minHeight: 28,
  padding: '4px 9px',
  borderRadius: 4,
  border: '1px solid #3a4756',
  background: '#10161d',
  color: '#d6dde6',
  cursor: 'pointer',
  fontFamily: 'inherit',
  fontSize: 11,
};

export const mainStyle: CSSProperties = {
  flex: 1,
  padding: '24px 32px 40px',
  display: 'flex',
  flexDirection: 'column',
  gap: 24,
  maxWidth: 1200,
  margin: '0 auto',
  width: '100%',
};

export const tabRowStyle: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 4,
  background: '#161d25',
  borderRadius: 6,
  padding: 3,
  border: '1px solid #2a3540',
  width: 'fit-content',
};

export const tabStyle = (active: boolean): CSSProperties => ({
  padding: '6px 14px',
  fontSize: 12,
  fontWeight: 600,
  borderRadius: 4,
  border: 'none',
  cursor: 'pointer',
  fontFamily: "inherit",
  background: active ? '#2a3a4a' : 'transparent',
  color: active ? '#f0c674' : '#8893a3',
  transition: 'background 0.2s ease, color 0.2s ease',
});

export const filterBarStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
  gap: 10,
  padding: 12,
  background: '#161d25',
  border: '1px solid #2a3540',
  borderRadius: 10,
};

export const filterLabelStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 5,
  color: '#8893a3',
  fontSize: 11,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
};

export const selectStyle: CSSProperties = {
  minHeight: 32,
  background: '#10161d',
  color: '#d6dde6',
  border: '1px solid #2a3540',
  borderRadius: 5,
  padding: '5px 8px',
  fontFamily: 'inherit',
  fontSize: 12,
};

export const loginShellStyle: CSSProperties = {
  width: 'min(100%, 420px)',
  margin: '78px auto 0',
  padding: 24,
  background: '#161d25',
  border: '1px solid #2a3540',
  borderRadius: 8,
  boxShadow: '0 20px 50px rgba(0,0,0,0.35)',
};

export const loginTitleStyle: CSSProperties = {
  margin: '0 0 18px',
  color: '#f0c674',
  fontSize: 18,
  fontWeight: 700,
};

export const loginFieldStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 6,
  marginBottom: 12,
  color: '#8893a3',
  fontSize: 11,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
};

export const loginInputStyle: CSSProperties = {
  minHeight: 38,
  background: '#10161d',
  color: '#e6edf3',
  border: '1px solid #2a3540',
  borderRadius: 5,
  padding: '7px 10px',
  fontFamily: 'inherit',
  fontSize: 14,
};

// Factory: original `loginButtonStyle` closed over `loginSubmitting`.
export const loginButtonStyle = (loginSubmitting: boolean): CSSProperties => ({
  width: '100%',
  minHeight: 40,
  marginTop: 6,
  borderRadius: 5,
  border: '1px solid #4a5b6e',
  background: '#2a3a4a',
  color: '#f0c674',
  cursor: loginSubmitting ? 'wait' : 'pointer',
  fontFamily: 'inherit',
  fontSize: 13,
  fontWeight: 700,
});

export const overviewGridStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 170px), 1fr))',
  gap: 12,
};

export const metricCardStyle = (tone: string = 'default'): CSSProperties => ({
  background: tone === 'danger' ? 'rgba(224,108,117,0.10)' : '#161d25',
  border: tone === 'danger' ? '1px solid rgba(224,108,117,0.45)' : '1px solid #2a3540',
  borderRadius: 8,
  padding: '14px 15px',
  minHeight: 82,
});

export const metricLabelStyle: CSSProperties = {
  color: '#8893a3',
  fontSize: 11,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: 7,
};

export const metricValueStyle: CSSProperties = {
  color: '#f0c674',
  fontSize: 24,
  fontWeight: 750,
  lineHeight: 1.1,
};

export const panelTitleStyle: CSSProperties = {
  padding: '12px 14px',
  borderBottom: '1px solid #2a3540',
  background: '#1c252f',
  color: '#f0c674',
  fontSize: 12,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
};

export const tableWrapStyle: CSSProperties = {
  background: '#161d25',
  border: '1px solid #2a3540',
  borderRadius: 10,
  overflow: 'hidden',
  overflowX: 'auto',
};

export const dashboardGridStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))',
  gap: 14,
};

export const dashboardWideStyle: CSSProperties = {
  gridColumn: '1 / -1',
};

export const widgetHeaderStyle: CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: 12,
  padding: '11px 14px',
  borderBottom: '1px solid #2a3540',
  background: '#1c252f',
};

export const widgetTitleStyle: CSSProperties = {
  color: '#f0c674',
  fontSize: 12,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
};

export const widgetMetaStyle: CSSProperties = {
  color: '#8893a3',
  fontSize: 11,
  whiteSpace: 'nowrap',
};

export const barTrackStyle: CSSProperties = {
  height: 8,
  borderRadius: 4,
  background: '#0f151b',
  border: '1px solid #2a3540',
  overflow: 'hidden',
};

export const barFillStyle = (width: string, tone: string = 'default'): CSSProperties => ({
  height: '100%',
  width,
  minWidth: width === '0%' ? 0 : 4,
  background: tone === 'cost' ? '#f0c674' : '#7dc9a0',
});

export const mutedSmallStyle: CSSProperties = {
  color: '#8893a3',
  fontSize: 11,
};

export const tableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: 13,
};

export const thStyle: CSSProperties = {
  textAlign: 'left',
  padding: '10px 14px',
  background: '#1c252f',
  color: '#a3aebb',
  fontWeight: 600,
  fontSize: 11,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  borderBottom: '1px solid #2a3540',
};

export const tdStyle: CSSProperties = {
  padding: '10px 14px',
  borderBottom: '1px solid #2a3540',
  color: '#d6dde6',
};

// Factory: original `btnDangerStyle` closed over `deleting`.
export const btnDangerStyle = (deleting: unknown): CSSProperties => ({
  background: 'transparent',
  color: '#e06c75',
  border: '1px solid #e06c75',
  borderRadius: 4,
  padding: '5px 10px',
  fontSize: 11,
  fontWeight: 600,
  fontFamily: "inherit",
  cursor: 'pointer',
  opacity: deleting ? 0.6 : 1,
  pointerEvents: deleting ? 'none' : 'auto',
});

export const emptyStateStyle: CSSProperties = {
  color: '#8893a3',
  fontSize: 13,
  textAlign: 'center',
  padding: '32px 0',
};

export const errorStateStyle: CSSProperties = {
  color: '#e06c75',
  fontSize: 14,
  textAlign: 'center',
  padding: '40px 0',
  border: '1px dashed #e06c75',
  borderRadius: 10,
  background: 'rgba(224,108,117,0.08)',
};

export const statusPillStyle = (status: unknown): CSSProperties => {
  const value = String(status || '').toLowerCase();
  const tone = (
    value === 'passed' || value === 'completed' || value === 'success' ? 'ok'
      : value === 'failed' || value === 'error' ? 'bad'
        : value === 'running' ? 'run'
          : value === 'blocked' ? 'warn'
            : 'idle'
  );
  const palette = ({
    ok: ['#1c2f25', '#7dc9a0'],
    bad: ['#3a1f24', '#e06c75'],
    run: ['#1f2a3a', '#82aaff'],
    warn: ['#3a3120', '#f0c674'],
    idle: ['#1c252f', '#a3aebb'],
  } as Record<string, string[]>)[tone];
  return {
    fontSize: 10,
    fontWeight: 600,
    textTransform: 'uppercase',
    padding: '2px 6px',
    borderRadius: 3,
    background: palette[0],
    color: palette[1],
    border: '1px solid #2a3540',
  };
};
