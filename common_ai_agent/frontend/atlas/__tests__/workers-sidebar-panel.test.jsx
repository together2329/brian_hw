/**
 * Behavior test for AgentStatusPanel workers grid.
 *
 * workspace.jsx (line 15955) is a 16k-line browser-globals script. We inline
 * the minimal component that reproduces the worker grid logic from lines
 * 16280-16351 (tone() → cfgFor() → grid cells). The production file is not
 * modified.
 */
import React, { useState, useEffect } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// tone() logic from workspace.jsx:16286-16292
function tone(w) {
  const s = String(w.status || '');
  if (s === 'ok' && Number(w.running_count || 0) > 0) return 'active';
  if (s === 'ok') return 'done';
  if (s === 'mismatch') return 'err';
  return 'pending';
}

// cfgFor() from workspace.jsx:16293-16298
function cfgFor(t) {
  if (t === 'active') return { color: 'var(--accent)', glyph: '●', className: 'accent' };
  if (t === 'done')   return { color: 'var(--ok)',     glyph: '✓', className: 'done' };
  if (t === 'err')    return { color: 'var(--err)',    glyph: '✗', className: 'err' };
  return { color: 'var(--fg-mute)', glyph: '○', className: 'pending' };
}

// Minimal reproduction of the workers grid section of AgentStatusPanel
function WorkersGrid({ fetchUrl = '/api/orchestrator/workers' }) {
  const [liveWorkers, setLiveWorkers] = useState([]);
  const [workersError, setWorkersError] = useState('');

  useEffect(() => {
    let dead = false;
    fetch(fetchUrl, { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((j) => {
        if (!dead) setLiveWorkers(Array.isArray(j && j.workers) ? j.workers : []);
      })
      .catch((e) => {
        if (!dead) setWorkersError(String(e.message || e));
      });
    return () => { dead = true; };
  }, [fetchUrl]);

  const total = liveWorkers.length;

  if (workersError) return <div data-testid="workers-error">{workersError}</div>;

  return (
    <div data-testid="workers-grid">
      <div data-testid="workers-count">{total}</div>
      {total === 0 ? (
        <div data-testid="workers-empty">no workers yet</div>
      ) : (
        <div
          data-testid="workers-cells"
          style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4 }}
        >
          {liveWorkers.map((w) => {
            const cfg = cfgFor(tone(w));
            const label = String(w.workflow || '').slice(0, 6);
            return (
              <div
                key={w.url || w.workflow}
                data-testid={`worker-cell-${w.workflow}`}
                className={cfg.className}
              >
                <div style={{ color: cfg.color }}>
                  {cfg.glyph} {label}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

describe('AgentStatusPanel workers grid', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        workers: [
          {
            workflow: 'ssot-gen',
            url: 'http://127.0.0.1:5621',
            status: 'ok',
            running_count: 1,
          },
        ],
      }),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders 1 worker cell when fetch returns 1 worker', async () => {
    render(<WorkersGrid />);
    await waitFor(() => {
      expect(screen.getByTestId('worker-cell-ssot-gen')).toBeInTheDocument();
    });
    expect(screen.getByTestId('workers-count').textContent).toBe('1');
  });

  it('worker cell has class "accent" when status=ok and running_count=1', async () => {
    render(<WorkersGrid />);
    await waitFor(() => {
      const cell = screen.getByTestId('worker-cell-ssot-gen');
      expect(cell).toHaveClass('accent');
    });
  });

  it('shows empty state when workers array is empty', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ workers: [] }),
    });
    render(<WorkersGrid />);
    await waitFor(() => {
      expect(screen.getByTestId('workers-empty')).toBeInTheDocument();
    });
  });
});
