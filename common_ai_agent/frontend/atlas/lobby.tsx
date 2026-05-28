// lobby.tsx — TypeScript migration of lobby.jsx.
//
// What changed vs lobby.jsx:
//   - Proper ES module: `import { useState, ... } from 'react'` instead of the
//     ambient global `React` + in-browser babel compile. Call sites rewritten
//     from `React.useState(` to `useState(` etc.
//   - `ReactDOM.createRoot` replaced with the typed `createRoot` from
//     'react-dom/client' (same React 18 root API, behavior identical).
//   - Real typed export (`LobbyPage`) — consumers will `import` it once they
//     migrate.
//
// Transitional: still bridges to `window.LobbyPage` at the bottom so the
// not-yet-migrated boot HTML keeps resolving it, and still mounts itself onto
// #root exactly as the .jsx did.
import {
  useState,
  useEffect,
  useMemo,
  type CSSProperties,
  type ChangeEvent,
  type KeyboardEvent,
  type MouseEvent,
} from 'react';
import { createRoot } from 'react-dom/client';

interface ProjectOption {
  value: string;
  label: string;
}

const PROJECT_OPTIONS: ProjectOption[] = [
  { value: 'gpio', label: 'GPIO' },
  { value: 'uart', label: 'UART' },
  { value: 'soc', label: 'SoC' },
  { value: 'i2c', label: 'I2C' },
  { value: 'spi', label: 'SPI' },
];

interface StatusMetaEntry {
  label: string;
  dot: string;
}

const STATUS_META: Record<string, StatusMetaEntry> = {
  active:   { label: 'Active',   dot: '#7dc9a0' },
  archived: { label: 'Archived', dot: '#8893a3' },
};

interface SessionInfo {
  id: string;
  title: string;
  status: string;
  project?: string;
  progress?: number;
  lastActive?: string;
  updated_at?: string;
  created_at?: string;
}

export function LobbyPage() {
  const [username, setUsername] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('active');
  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newProject, setNewProject] = useState(PROJECT_OPTIONS[0].value);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        await fetch('/api/auth/guest', { method: 'POST' });
        const resp = await fetch('/api/sessions');
        const data = await resp.json();
        setSessions(data.sessions || []);
        setError(null);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const filteredSessions = useMemo(() => {
    return sessions.filter((s) => {
      const matchesTab = s.status === activeTab;
      const matchesSearch = s.title.toLowerCase().includes(searchQuery.trim().toLowerCase());
      return matchesTab && matchesSearch;
    });
  }, [sessions, activeTab, searchQuery]);

  const onOpenSession = (session: SessionInfo) => {
    window.location.href = '/?session_id=' + encodeURIComponent(session.id);
  };

  const onCreateSession = async () => {
    if (!newTitle.trim()) return;
    try {
      const resp = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle.trim(), project_id: newProject }),
      });
      if (!resp.ok) throw new Error('Create failed');
      setNewTitle('');
      setNewProject(PROJECT_OPTIONS[0].value);
      setShowModal(false);
      const listResp = await fetch('/api/sessions');
      const data = await listResp.json();
      setSessions(data.sessions || []);
    } catch (e) {
      alert('Failed to create session: ' + e);
    }
  };

  const onContinueGuest = async () => {
    try {
      await fetch('/api/auth/guest', { method: 'POST' });
      alert('Continuing as guest');
    } catch (e) {
      alert('Guest auth failed: ' + e);
    }
  };

  const onLogin = () => {
    alert('Login flow not wired yet.');
  };

  const pageStyle: CSSProperties = {
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

  const headerStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 32px',
    borderBottom: '1px solid #2a3540',
    background: '#141a21',
  };

  const logoStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    fontSize: 22,
    fontWeight: 700,
    letterSpacing: '0.04em',
    color: '#f0c674',
  };

  const badgeStyle: CSSProperties = {
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

  const mainStyle: CSSProperties = {
    flex: 1,
    padding: '24px 32px 40px',
    display: 'flex',
    flexDirection: 'column',
    gap: 28,
    maxWidth: 1200,
    margin: '0 auto',
    width: '100%',
  };

  const loginWrapStyle: CSSProperties = {
    background: '#161d25',
    border: '1px solid #2a3540',
    borderRadius: 10,
    padding: '24px 28px',
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 16,
  };

  const inputStyle: CSSProperties = {
    background: '#11161c',
    color: '#d6dde6',
    border: '1px solid #2a3540',
    borderRadius: 6,
    padding: '9px 14px',
    fontSize: 13,
    fontFamily: "inherit",
    outline: 'none',
    minWidth: 260,
    flex: 1,
  };

  const btnPrimaryStyle: CSSProperties = {
    background: '#f0c674',
    color: '#171108',
    border: 'none',
    borderRadius: 6,
    padding: '9px 18px',
    fontSize: 13,
    fontWeight: 600,
    fontFamily: "inherit",
    cursor: 'pointer',
    transition: 'filter 0.2s ease, transform 0.2s ease',
  };

  const btnSecondaryStyle: CSSProperties = {
    background: 'transparent',
    color: '#a3aebb',
    border: '1px solid #3a4756',
    borderRadius: 6,
    padding: '9px 18px',
    fontSize: 13,
    fontWeight: 500,
    fontFamily: "inherit",
    cursor: 'pointer',
    transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease',
  };

  const sectionTitleStyle: CSSProperties = {
    fontSize: 16,
    fontWeight: 700,
    color: '#d6dde6',
    margin: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  };

  const toolbarStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
  };

  const searchStyle: CSSProperties = {
    background: '#161d25',
    color: '#d6dde6',
    border: '1px solid #2a3540',
    borderRadius: 6,
    padding: '8px 12px',
    fontSize: 13,
    fontFamily: "inherit",
    outline: 'none',
    width: 240,
  };

  const tabRowStyle: CSSProperties = {
    display: 'flex',
    gap: 4,
    background: '#161d25',
    borderRadius: 6,
    padding: 3,
    border: '1px solid #2a3540',
  };

  const tabStyle = (active: boolean): CSSProperties => ({
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

  const gridStyle: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: 16,
  };

  const cardStyle: CSSProperties = {
    background: '#161d25',
    border: '1px solid #2a3540',
    borderRadius: 10,
    padding: '18px 20px',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    position: 'relative',
    overflow: 'hidden',
  };

  const cardTitleStyle: CSSProperties = {
    fontSize: 15,
    fontWeight: 700,
    color: '#d6dde6',
    margin: 0,
  };

  const cardMetaStyle: CSSProperties = {
    fontSize: 12,
    color: '#8893a3',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  };

  const statusBadgeStyle = (): CSSProperties => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 11,
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: 4,
    background: '#1c252f',
    color: '#a3aebb',
    border: '1px solid #2a3540',
  });

  const progressTrackStyle: CSSProperties = {
    height: 6,
    background: '#2a3540',
    borderRadius: 3,
    overflow: 'hidden',
    marginTop: 4,
  };

  const progressFillStyle = (pct: number, color?: string): CSSProperties => ({
    width: pct + '%',
    height: '100%',
    background: color || '#f0c674',
    borderRadius: 3,
    transition: 'width 0.4s ease',
  });

  const fabStyle: CSSProperties = {
    position: 'fixed',
    bottom: 28,
    right: 32,
    width: 52,
    height: 52,
    borderRadius: '50%',
    background: '#f0c674',
    color: '#171108',
    border: 'none',
    fontSize: 24,
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    zIndex: 50,
  };

  const overlayStyle: CSSProperties = {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.55)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
    backdropFilter: 'blur(2px)',
  };

  const modalStyle: CSSProperties = {
    background: '#161d25',
    border: '1px solid #2a3540',
    borderRadius: 12,
    padding: '24px 28px',
    width: 'min(90vw, 420px)',
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  };

  const modalTitleStyle: CSSProperties = {
    fontSize: 16,
    fontWeight: 700,
    color: '#d6dde6',
    margin: 0,
  };

  const labelStyle: CSSProperties = {
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    color: '#8893a3',
    marginBottom: 4,
  };

  const selectStyle: CSSProperties = {
    background: '#11161c',
    color: '#d6dde6',
    border: '1px solid #2a3540',
    borderRadius: 6,
    padding: '9px 12px',
    fontSize: 13,
    fontFamily: "inherit",
    outline: 'none',
    width: '100%',
  };

  const emptyStateStyle: CSSProperties = {
    color: '#8893a3',
    fontSize: 13,
    textAlign: 'center',
    padding: '32px 0',
    border: '1px dashed #2a3540',
    borderRadius: 10,
    background: '#141a21',
  };

  return (
    <div style={pageStyle}>
      <style>{`
        .lobby-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 12px 36px rgba(0,0,0,0.35);
          border-color: #3a4756;
        }
        .lobby-fab:hover {
          transform: scale(1.06);
          box-shadow: 0 12px 40px rgba(0,0,0,0.55);
        }
        .lobby-btn-primary:hover {
          filter: brightness(1.08);
        }
        .lobby-btn-secondary:hover {
          background: rgba(214, 221, 230, 0.06);
          color: #d6dde6;
          border-color: #4a5868;
        }
        .lobby-input:focus {
          border-color: #f0c674;
          box-shadow: 0 0 0 2px rgba(240, 198, 116, 0.15);
        }
        .lobby-search:focus {
          border-color: #f0c674;
          box-shadow: 0 0 0 2px rgba(240, 198, 116, 0.15);
        }
        @media (max-width: 640px) {
          .lobby-main { padding: 16px !important; }
          .lobby-header { padding: 14px 16px !important; }
          .lobby-grid { grid-template-columns: 1fr !important; }
          .lobby-login-wrap { flex-direction: column; align-items: stretch !important; }
        }
      `}</style>

      <header className="lobby-header" style={headerStyle}>
        <div style={logoStyle}>
          <span style={{ fontSize: 26 }}>◈</span>
          <span>ATLAS</span>
        </div>
        <span style={badgeStyle}>Multi-User</span>
      </header>

      <main className="lobby-main" style={mainStyle}>
        <section className="lobby-login-wrap" style={loginWrapStyle}>
          <input
            className="lobby-input"
            style={inputStyle}
            placeholder="Enter username or continue as guest"
            value={username}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
          />
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="lobby-btn-primary"
              style={btnPrimaryStyle}
              onClick={onContinueGuest}
            >
              Continue as Guest
            </button>
            <button
              className="lobby-btn-secondary"
              style={btnSecondaryStyle}
              onClick={onLogin}
            >
              Login
            </button>
          </div>
        </section>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <h2 style={sectionTitleStyle}>
            Your Sessions
            <span style={{ fontSize: 12, fontWeight: 500, color: '#8893a3', marginLeft: 10 }}>
              {filteredSessions.length}
            </span>
          </h2>
          <div style={toolbarStyle}>
            <input
              className="lobby-search"
              style={searchStyle}
              placeholder="Search sessions…"
              value={searchQuery}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            />
            <div style={tabRowStyle}>
              <button style={tabStyle(activeTab === 'active')} onClick={() => setActiveTab('active')}>
                Active
              </button>
              <button style={tabStyle(activeTab === 'archived')} onClick={() => setActiveTab('archived')}>
                Archived
              </button>
            </div>
          </div>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#8893a3' }}>
            Loading sessions…
          </div>
        )}

        {!loading && error && (
          <div style={{ ...emptyStateStyle, color: '#e06c75', borderColor: '#e06c75', background: 'rgba(224,108,117,0.08)' }}>
            {error}
          </div>
        )}

        {!loading && !error && filteredSessions.length === 0 ? (
          <div style={emptyStateStyle}>
            No {activeTab} sessions match your search.
          </div>
        ) : (
          !loading && !error && (
            <div className="lobby-grid" style={gridStyle}>
              {filteredSessions.map((s) => {
                const meta = STATUS_META[s.status] || STATUS_META.active;
                const progress = s.progress ?? 0;
                const progressColor = progress === 100 ? '#7dc9a0' : progress > 50 ? '#f0c674' : '#d9a94a';
                return (
                  <div
                    key={s.id}
                    className="lobby-card"
                    style={cardStyle}
                    onClick={() => onOpenSession(s)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e: KeyboardEvent<HTMLDivElement>) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onOpenSession(s);
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                      <h3 style={cardTitleStyle}>{s.title}</h3>
                      <span style={statusBadgeStyle()}>
                        <span style={{ width: 7, height: 7, borderRadius: '50%', background: meta.dot, display: 'inline-block' }} />
                        {meta.label}
                      </span>
                    </div>
                    <div style={cardMetaStyle}>
                      <span style={{ fontWeight: 500, color: '#a3aebb' }}>{s.project}</span>
                      {s.lastActive && (
                        <>
                          <span style={{ color: '#3a4756' }}>·</span>
                          <span>Last active: {s.lastActive}</span>
                        </>
                      )}
                      {!s.lastActive && (s.updated_at || s.created_at) && (
                        <>
                          <span style={{ color: '#3a4756' }}>·</span>
                          <span>Last active: {new Date((s.updated_at || s.created_at) as string).toLocaleString()}</span>
                        </>
                      )}
                    </div>
                    <div style={{ marginTop: 'auto', paddingTop: 6 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#8893a3', marginBottom: 4 }}>
                        <span>{progress}% complete</span>
                        <span>{Math.round((progress / 100) * 12)}/12 tasks</span>
                      </div>
                      <div style={progressTrackStyle}>
                        <div style={progressFillStyle(progress, progressColor)} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )
        )}
      </main>

      <button
        className="lobby-fab"
        style={fabStyle}
        onClick={() => setShowModal(true)}
        title="New Session"
        aria-label="New Session"
      >
        +
      </button>

      {showModal && (
        <div
          style={overlayStyle}
          onClick={(e: MouseEvent<HTMLDivElement>) => {
            if (e.target === e.currentTarget) setShowModal(false);
          }}
          role="dialog"
          aria-modal="true"
        >
          <div style={modalStyle}>
            <h3 style={modalTitleStyle}>New Session</h3>
            <div>
              <div style={labelStyle}>Session Title</div>
              <input
                className="lobby-input"
                style={{ ...inputStyle, width: '100%', minWidth: 'unset' }}
                placeholder="e.g., AXI DMA Controller"
                value={newTitle}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setNewTitle(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <div style={labelStyle}>Project</div>
              <select
                className="lobby-input"
                style={selectStyle}
                value={newProject}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => setNewProject(e.target.value)}
              >
                {PROJECT_OPTIONS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 4 }}>
              <button
                className="lobby-btn-secondary"
                style={btnSecondaryStyle}
                onClick={() => setShowModal(false)}
              >
                Cancel
              </button>
              <button
                className="lobby-btn-primary"
                style={btnPrimaryStyle}
                onClick={onCreateSession}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Remove once all consumers import { LobbyPage } directly. `LobbyPage` is not
// (yet) declared on the ambient Window in types/atlas-window.d.ts, so we widen
// the type locally; the runtime assignment is identical to the .jsx original.
(window as Window & { LobbyPage?: typeof LobbyPage }).LobbyPage = LobbyPage;

if (typeof document !== 'undefined' && document.getElementById('root')) {
  createRoot(document.getElementById('root')!).render(<LobbyPage />);
}
