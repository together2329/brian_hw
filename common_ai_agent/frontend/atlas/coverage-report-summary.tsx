import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';

import type { LintDiagnostic } from './lint-diagnostics';
import { ToolOutputPre } from './workspace-markdown-chips';
import { AtlasStatusBadge } from './workspace-report-status';
import { CoverageToolCard } from './coverage-report-card';
import {
  normalizeCoverageReport,
  preferredCoveragePath,
  type CoverageReportData,
} from './coverage-report-model';

export { CoverageMetricCell, CoverageToolCard, coverageMetricText } from './coverage-report-card';

interface CoverageReportSummaryProps {
  readonly ip: string;
  readonly onSelectPath?: (path: string) => void;
  readonly onOpenDiagnostic?: (diagnostic: LintDiagnostic) => void;
}

const errorMessage = (value: unknown): string => {
  if (value instanceof Error) return value.message;
  return String(value || 'unknown error');
};

const valueCard = (label: string, value: string | number): ReactNode => (
  <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--panel)', borderRadius: 3, padding: '6px 8px', minWidth: 0 }}>
    <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
    <div className="trunc" title={String(value)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>{value}</div>
  </div>
);

const reportFetchError = (body: CoverageReportData, status: number): Error => {
  const message = body.errors[0] || `HTTP ${status}`;
  return new Error(message);
};

export const CoverageReportSummary = ({
  ip,
  onSelectPath,
  onOpenDiagnostic,
}: CoverageReportSummaryProps): ReactNode => {
  const [data, setData] = useState<CoverageReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [running, setRunning] = useState('');
  const [tick, setTick] = useState(0);
  const [selectedVcdPath, setSelectedVcdPath] = useState('');
  const selectedVcdPathRef = useRef('');
  selectedVcdPathRef.current = selectedVcdPath;

  const load = useCallback(async (mode = ''): Promise<void> => {
    if (!ip) return;
    setLoading(true);
    setErr('');
    setRunning(mode);
    const params = new URLSearchParams({ ip });
    if (mode === 'summary' || mode === 'all') params.set('refresh', '1');
    if (mode === 'vcd' || mode === 'all') params.set('vcd', '1');
    if ((mode === 'vcd' || mode === 'all') && selectedVcdPathRef.current) {
      params.set('vcd_path', selectedVcdPathRef.current);
    }
    try {
      const response = await fetch(`/reports/cov?${params.toString()}`, { cache: 'no-store' });
      const body = normalizeCoverageReport(await response.json().catch(() => ({})));
      if (!response.ok) throw reportFetchError(body, response.status);
      setData(body);
      const paths = body.vcd_paths;
      if (paths.length > 0 && !paths.includes(selectedVcdPathRef.current)) {
        setSelectedVcdPath(paths[0]);
      }
      const preferred = preferredCoveragePath(body);
      if (preferred) onSelectPath?.(preferred);
    } catch (error) {
      setErr(errorMessage(error));
    } finally {
      setLoading(false);
      setRunning('');
    }
  }, [ip, onSelectPath]);

  useEffect(() => {
    void load('');
  }, [load, tick]);

  const tools = data?.tools || [];
  const artifacts = data?.artifacts || [];
  const vcdPaths = data?.vcd_paths || [];
  const selectedVcd = selectedVcdPath && vcdPaths.includes(selectedVcdPath)
    ? selectedVcdPath
    : vcdPaths[0] || '';
  const missingTools = tools.filter(tool => !tool.available).length;

  return (
    <div style={{ borderBottom: '1px solid var(--line)', background: 'var(--bg-2)', padding: 12, display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <div style={{ minWidth: 0 }}>
          <div className="trunc" title="coverage report" style={{ fontWeight: 900, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 12 }}>
            coverage report
          </div>
          <div className="trunc" title={`${data?.resolved_ip || ip} / Verilator + pyslang + VCD + FL/CL`} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, marginTop: 2 }}>
            {data?.resolved_ip || ip} / Verilator + pyslang + VCD + FL/CL
          </div>
        </div>
        <span style={{ flex: 1, minWidth: 0 }} />
        {data?.status && data.status !== 'unknown' && <AtlasStatusBadge status={data.status} label={data.status} compact />}
        <button className="btn" onClick={() => setTick(value => value + 1)} disabled={loading} style={{ padding: '2px 8px', fontSize: 10, flex: '0 0 auto' }}>
          refresh
        </button>
        <button className="btn" onClick={() => void load('summary')} disabled={!!running || loading} style={{ padding: '2px 8px', fontSize: 10, flex: '0 0 auto' }}>
          run summary
        </button>
        <button className="btn" onClick={() => void load('vcd')} disabled={!!running || loading} style={{ padding: '2px 8px', fontSize: 10, flex: '0 0 auto' }}>
          run vcd
        </button>
      </div>

      {vcdPaths.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'auto minmax(0, 1fr) auto', gap: 8, alignItems: 'center' }}>
          <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>vcd</span>
          <select
            aria-label="VCD file"
            value={selectedVcd}
            onChange={event => {
              selectedVcdPathRef.current = event.currentTarget.value;
              setSelectedVcdPath(event.currentTarget.value);
            }}
            style={{
              minWidth: 0,
              background: 'var(--panel)',
              color: 'var(--fg)',
              border: '1px solid var(--line)',
              borderRadius: 3,
              padding: '3px 6px',
              fontFamily: 'var(--mono)',
              fontSize: 10,
            }}
          >
            {vcdPaths.map(path => (
              <option key={path} value={path}>{path}</option>
            ))}
          </select>
          <button className="btn" onClick={() => selectedVcd && onSelectPath?.(selectedVcd)} disabled={!selectedVcd} style={{ padding: '2px 8px', fontSize: 10 }}>
            open vcd
          </button>
        </div>
      )}

      {err && <div style={{ color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 11 }}>{err}</div>}
      {loading && (
        <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          {running === 'summary' ? 'Running SSOT coverage summary...' : running === 'vcd' ? 'Running VCD toggle coverage...' : 'Loading coverage report...'}
        </div>
      )}
      {!err && data && !data.exists && !loading && (
        <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          No coverage artifacts found yet. Static RTL scan still needs a DUT filelist or rtl/ sources.
        </div>
      )}

      {data && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8 }}>
            {[
              valueCard('tools', tools.length),
              valueCard('missing', missingTools),
              valueCard('artifacts', artifacts.length),
              valueCard('vcd files', vcdPaths.length),
            ]}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(270px, 1fr))', gap: 10, minWidth: 0 }}>
            {tools.map((tool, idx) => (
              <CoverageToolCard
                key={`${tool.id || tool.label || 'coverage-tool'}-${idx}`}
                tool={tool}
                onSelectPath={onSelectPath}
                onOpenDiagnostic={onOpenDiagnostic}
              />
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <button className="btn" onClick={() => data.report_path && onSelectPath?.(data.report_path)} disabled={!data.report_exists} style={{ padding: '2px 8px', fontSize: 10 }}>open json</button>
            <button className="btn" onClick={() => data.lcov_path && onSelectPath?.(data.lcov_path)} disabled={!data.lcov_exists} style={{ padding: '2px 8px', fontSize: 10 }}>open lcov</button>
            <button className="btn" onClick={() => data.toggle_path && onSelectPath?.(data.toggle_path)} disabled={!data.toggle_exists} style={{ padding: '2px 8px', fontSize: 10 }}>open toggle</button>
            <button className="btn" onClick={() => data.markdown_path && onSelectPath?.(data.markdown_path)} disabled={!data.markdown_exists} style={{ padding: '2px 8px', fontSize: 10 }}>open md</button>
          </div>
          {data.errors.length > 0 && (
            <div style={{ color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              {data.errors.join(' / ')}
            </div>
          )}
          {data.run_entries.map(info => (
            <ToolOutputPre key={info.name} text={`${info.name}: rc ${String(info.returncode ?? '')}\n${info.output}`} tool="bash" />
          ))}
        </>
      )}
    </div>
  );
};
