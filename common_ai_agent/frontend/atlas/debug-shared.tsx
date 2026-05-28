// debug-shared.tsx — primitives shared across all 3 debug variations
// Wave canvas, signal data, source code, agent transcript scaffolding.
//
// TypeScript migration of debug-shared.jsx (strangler-fig): proper ES module
// with typed exports, JSX automatic runtime, and a transitional window.* bridge
// at the bottom so not-yet-migrated .jsx consumers keep resolving the globals.
import { Fragment, type ReactNode, type MouseEvent } from 'react';

// ── Mock signal data ──────────────────────────────────────────
// One trace = array of [time, value]. Time in ns. Single-bit
// values are 0/1/'x'/'z'. Buses are uppercase hex strings or 'x'.
//
// The bug: bit_cnt is 4 bits (0..F) but the FSM expects 8-cycle
// transfers. Wraparound at 7→0 leaves stale shift_reg state for
// one cycle, which bleeds X through to mosi via a missing reset.
type TraceSample = [number, number | string];
type Trace = TraceSample[];

export const MOCK_TRACES: Record<string, Trace> = {
  clk:        [[0,0],[5,1],[10,0],[15,1],[20,0],[25,1],[30,0],[35,1],[40,0],[45,1],[50,0],[55,1],[60,0],[65,1],[70,0],[75,1],[80,0],[85,1],[90,0],[95,1],[100,0],[105,1],[110,0],[115,1],[120,0],[125,1],[130,0],[135,1],[140,0],[145,1],[150,0],[155,1],[160,0],[165,1],[170,0],[175,1],[180,0],[185,1],[190,0],[195,1],[200,0]],
  rst_n:      [[0,0],[15,1]],
  cs_n:       [[0,1],[20,0],[180,1]],
  state:      [[0,'IDLE'],[20,'LOAD'],[30,'SHIFT'],[160,'COMPLETE'],[180,'IDLE']],
  bit_cnt:    [[0,'0'],[30,'0'],[40,'1'],[50,'2'],[60,'3'],[70,'4'],[80,'5'],[90,'6'],[100,'7'],[110,'8'],[120,'9'],[130,'A'],[140,'B'],[150,'C'],[160,'D']],
  shift_reg:  [[0,'00'],[20,'A5'],[40,'4A'],[60,'94'],[80,'29'],[100,'52'],[120,'A4'],[140,'48']],
  // mosi goes X at t=110 because bit_cnt rolled past 7 without reload
  mosi:       [[0,0],[40,1],[60,0],[80,1],[100,0],[110,'x'],[160,0]],
  miso:       [[0,'z'],[20,1],[40,0],[60,1],[80,1],[100,0],[120,1],[140,0],[160,'z']],
  sclk:       [[0,0],[40,1],[50,0],[60,1],[70,0],[80,1],[90,0],[100,1],[110,0],[120,1],[130,0],[140,1],[150,0],[160,0]],
  done:       [[0,0],[160,1],[180,0]],
};

// ── Source code (mock SystemVerilog) ──────────────────────────
// Line numbers correspond to typical SPI master FSM. The bug is at L34: bit_cnt[3:0] should be reset at the COMPLETE→IDLE edge.
type SourceToken = [string, number, number];
interface SourceLine {
  ln: number;
  txt: string;
  tok?: SourceToken[];
}

export const MOCK_SOURCE: SourceLine[] = [
  { ln: 1,  txt: 'module spi_master #(', tok: [['kw',0,6],['fn',7,17]] },
  { ln: 2,  txt: '  parameter CPOL = 0,', tok: [['kw',2,11]] },
  { ln: 3,  txt: '  parameter CPHA = 0', tok: [['kw',2,11]] },
  { ln: 4,  txt: ')(' },
  { ln: 5,  txt: '  input  logic        clk,', tok: [['kw',2,7],['type',10,15]] },
  { ln: 6,  txt: '  input  logic        rst_n,', tok: [['kw',2,7],['type',10,15]] },
  { ln: 7,  txt: '  input  logic [7:0]  data_in,', tok: [['kw',2,7],['type',10,15]] },
  { ln: 8,  txt: '  output logic        mosi,', tok: [['kw',2,8],['type',10,15]] },
  { ln: 9,  txt: '  input  logic        miso,', tok: [['kw',2,7],['type',10,15]] },
  { ln: 10, txt: '  output logic        sclk', tok: [['kw',2,8],['type',10,15]] },
  { ln: 11, txt: ');' },
  { ln: 12, txt: '' },
  { ln: 13, txt: '  typedef enum { IDLE, LOAD, SHIFT, COMPLETE } st_t;', tok: [['kw',2,9],['kw',10,14],['type',49,53]] },
  { ln: 14, txt: '  st_t state, next_state;', tok: [['type',2,6]] },
  { ln: 15, txt: '  logic [3:0] bit_cnt;', tok: [['type',2,7]] },
  { ln: 16, txt: '  logic [7:0] shift_reg;', tok: [['type',2,7]] },
  { ln: 17, txt: '' },
  { ln: 18, txt: '  always_ff @(posedge clk or negedge rst_n) begin', tok: [['kw',2,11],['kw',13,14],['kw',15,22],['kw',27,29],['kw',30,37],['kw',43,48]] },
  { ln: 19, txt: '    if (!rst_n) begin', tok: [['kw',4,6],['kw',16,21]] },
  { ln: 20, txt: '      state     <= IDLE;', tok: [['kw',18,22]] },
  { ln: 21, txt: '      bit_cnt   <= 4\'h0;', tok: [['num',18,23]] },
  { ln: 22, txt: '      shift_reg <= 8\'h00;', tok: [['num',18,24]] },
  { ln: 23, txt: '    end else begin', tok: [['kw',4,7],['kw',8,12],['kw',13,18]] },
  { ln: 24, txt: '      state <= next_state;', tok: [] },
  { ln: 25, txt: '      case (state)', tok: [['kw',6,10]] },
  { ln: 26, txt: '        LOAD:     shift_reg <= data_in;' },
  { ln: 27, txt: '        SHIFT: begin', tok: [['kw',15,20]] },
  { ln: 28, txt: '          shift_reg <= {shift_reg[6:0], miso};' },
  { ln: 29, txt: '          bit_cnt   <= bit_cnt + 1;' },
  { ln: 30, txt: '        end', tok: [['kw',8,11]] },
  { ln: 31, txt: '        COMPLETE: ;' },
  { ln: 32, txt: '        // BUG: missing bit_cnt <= 0 here', tok: [['cm',8,42]] },
  { ln: 33, txt: '        default: ;', tok: [['kw',8,15]] },
  { ln: 34, txt: '      endcase', tok: [['kw',6,13]] },
  { ln: 35, txt: '    end', tok: [['kw',4,7]] },
  { ln: 36, txt: '  end', tok: [['kw',2,5]] },
  { ln: 37, txt: '' },
  { ln: 38, txt: '  assign mosi = shift_reg[7];', tok: [['kw',2,8]] },
  { ln: 39, txt: 'endmodule', tok: [['kw',0,9]] },
];

// ── Render a token-highlighted source line ────────────────────
export function renderSourceLine(line: SourceLine): ReactNode {
  if (!line.tok || line.tok.length === 0) return line.txt;
  const out: ReactNode[] = [];
  let i = 0;
  for (const [tok, start, end] of line.tok) {
    if (start > i) out.push(<span key={`p${i}`}>{line.txt.slice(i, start)}</span>);
    out.push(<span key={`t${start}`} className={`tok-${tok}`}>{line.txt.slice(start, end)}</span>);
    i = end;
  }
  if (i < line.txt.length) out.push(<span key={`pe${i}`}>{line.txt.slice(i)}</span>);
  return out;
}

// ── SourceCode component ──────────────────────────────────────
export interface SourceCodeProps {
  highlight?: number[];
  breakpoints?: number[];
  cursor?: number | null;
  fromLine?: number;
  toLine?: number;
}

export const SourceCode = ({ highlight = [], breakpoints = [], cursor = null, fromLine = 1, toLine = 39 }: SourceCodeProps) => {
  return (
    <div className="src">
      {MOCK_SOURCE.filter(l => l.ln >= fromLine && l.ln <= toLine).map(line => {
        const cls: string[] = [];
        if (highlight.includes(line.ln)) cls.push('hl');
        if (breakpoints.includes(line.ln)) cls.push('bp');
        if (cursor === line.ln) cls.push('cur');
        return (
          <div key={line.ln} className={`src-line ${cls.join(' ')}`}>
            <span className="ln">{line.ln}</span>
            <span>{renderSourceLine(line)}</span>
          </div>
        );
      })}
    </div>
  );
};

// ── Wave time→x conversion. ───────────────────────────────────
// Time range visible in the wave area.
// Time range is now pulled from the active VCD whenever possible. The
// constants below are only used as fallback when no VCD has been
// loaded (mock data window). window.WAVE_TIME_START / END can be set
// externally (sim-debug.jsx does this on VCD parse) to override.
const TIME_START = 0;
const TIME_END = 200;
const WAVE_HEIGHT = 26;
const WAVE_PAD_Y = 4;

function tToX(t: number, width: number): number {
  const w = window as unknown as { WAVE_TIME_START?: number | null; WAVE_TIME_END?: number | null };
  const start = (typeof window !== 'undefined' && w.WAVE_TIME_START != null) ? w.WAVE_TIME_START : TIME_START;
  const end   = (typeof window !== 'undefined' && w.WAVE_TIME_END   != null) ? w.WAVE_TIME_END   : TIME_END;
  const span = (end - start) || 1;
  return ((t - start) / span) * width;
}

function nearestWaveEdgeTime(trace: Trace | unknown, x: number | string, width: number, thresholdPx = 8): number | null {
  if (!Array.isArray(trace) || trace.length < 2) return null;
  const clickX = Number(x);
  if (!Number.isFinite(clickX)) return null;
  let bestTime: number | null = null;
  let bestDist = Infinity;
  for (let i = 1; i < trace.length; i++) {
    const prev = trace[i - 1];
    const curr = trace[i];
    if (!Array.isArray(prev) || !Array.isArray(curr)) continue;
    if (String(prev[1]) === String(curr[1])) continue;
    const t = Number(curr[0]);
    if (!Number.isFinite(t)) continue;
    const edgeX = tToX(t, width);
    if (edgeX < -thresholdPx || edgeX > width + thresholdPx) continue;
    const dist = Math.abs(edgeX - clickX);
    if (dist <= thresholdPx && dist < bestDist) {
      bestDist = dist;
      bestTime = t;
    }
  }
  return bestTime;
}

// Convert a binary or named bus value to a display string per radix.
// VCD parser hands us bus values as binary strings (e.g. "10110011"); the
// previous WaveRow rendered them verbatim with a "0x" prefix so a 32-bit
// signal showed up as "0x1111111111111111111111111111111111" — illegible
// at a glance.
function fmtBusValue(v: number | string | null | undefined, radix?: string): string {
  if (v == null) return '?';
  const s = String(v);
  if (s.includes('x') || s.includes('X')) return 'x';
  if (s.includes('z') || s.includes('Z')) return 'z';
  if (radix === 'BIN') return '0b' + s;
  if (radix === 'DEC') {
    // Big-int safe parse for wide buses.
    try {
      const bi = BigInt('0b' + s);
      return bi.toString(10);
    } catch (_) { return s; }
  }
  // HEX (default) — chunk binary in groups of 4 from the right.
  if (/^[01]+$/.test(s)) {
    const pad = (4 - (s.length % 4)) % 4;
    const padded = '0'.repeat(pad) + s;
    let hex = '';
    for (let i = 0; i < padded.length; i += 4) {
      hex += parseInt(padded.slice(i, i + 4), 2).toString(16);
    }
    return '0x' + (hex.replace(/^0+/, '') || '0').toUpperCase();
  }
  return s;
}

// Treat numeric (0/1) and string ('0'/'1') hi/lo identically so traces
// from both MOCK_TRACES and the VCD parser render the same way.
function bitOf(v: number | string): number | string {
  if (v === 1 || v === '1') return 1;
  if (v === 0 || v === '0') return 0;
  return 'x';
}

// Render a single-bit (0/1/x/z) wave as SVG path.
function bitWavePath(trace: Trace | null | undefined, width: number): string {
  if (!trace || trace.length === 0) return '';
  const yHi = WAVE_PAD_Y;
  const yLo = WAVE_HEIGHT - WAVE_PAD_Y;
  const yMid = (yHi + yLo) / 2;
  let d = '';
  for (let i = 0; i < trace.length; i++) {
    const [t, v] = trace[i];
    const x = tToX(t, width);
    const nx = i + 1 < trace.length ? tToX(trace[i + 1][0], width) : width;
    const b = bitOf(v);
    const y = b === 1 ? yHi : b === 0 ? yLo : yMid;
    if (i === 0) d += `M ${x} ${y}`;
    else d += ` L ${x} ${y}`;
    d += ` L ${nx} ${y}`;
  }
  return d;
}

// Render a bus wave (hex/named values) as a "flag" shape.
interface BusWaveProps {
  trace?: Trace | null;
  width: number;
  radix?: string;
}

function BusWave({ trace, width, radix = 'HEX' }: BusWaveProps): ReactNode {
  if (!trace || trace.length === 0) return null;
  const yTop = WAVE_PAD_Y;
  const yBot = WAVE_HEIGHT - WAVE_PAD_Y;
  const slope = 2;
  const segs: ReactNode[] = [];
  for (let i = 0; i < trace.length; i++) {
    const [t, v] = trace[i];
    const x = tToX(t, width);
    const nx = i + 1 < trace.length ? tToX(trace[i + 1][0], width) : width;
    const segW = Math.max(0, nx - x);
    const isX = String(v).includes('x') || String(v).includes('X');
    // Verdi-style: bright cyan outline + transparent fill, red for X.
    const fill = isX ? 'rgba(255, 82, 82, 0.18)' : 'rgba(77, 208, 225, 0.10)';
    const stroke = isX ? '#ff5252' : '#4dd0e1';
    // Pretty-print the segment value: HEX preferred, drop the 0x for
    // segment labels (visually crowded) but keep it in tooltip.
    const pretty = fmtBusValue(v, radix);
    const labelInline = pretty.replace(/^0x/, '');
    // Hide label when segment is too narrow to fit any text.
    const showLabel = segW > 18;
    segs.push(
      <g key={i}>
        <polygon
          points={`${x + slope},${yTop} ${nx - slope},${yTop} ${nx},${(yTop + yBot) / 2} ${nx - slope},${yBot} ${x + slope},${yBot} ${x},${(yTop + yBot) / 2}`}
          fill={fill}
          stroke={stroke}
          strokeWidth={1}
        >
          <title>{`${pretty} @ t=${t}ns`}</title>
        </polygon>
        {showLabel && (
          <text x={(x + nx) / 2} y={(yTop + yBot) / 2 + 3.5}
                textAnchor="middle"
                className={`bus-flag-text ${isX ? 'x' : ''}`}>
            {labelInline.length > Math.floor(segW / 7)
              ? labelInline.slice(0, Math.max(1, Math.floor(segW / 7) - 1)) + '…'
              : labelInline}
          </text>
        )}
      </g>
    );
  }
  return <g>{segs}</g>;
}

// Render a single signal row.
export interface WaveRowProps {
  name: string;
  scope?: string;
  trace?: Trace | null;
  width: number;
  isBus?: boolean;
  radix?: string;
  selected?: boolean;
  onClick?: (e: MouseEvent<HTMLDivElement>) => void;
  onEdgeClick?: (edgeTime: number, e: MouseEvent<HTMLDivElement>) => void;
  colorHint?: string;
}

export const WaveRow = ({ name, scope, trace, width, isBus, radix = 'HEX', selected, onClick, onEdgeClick, colorHint }: WaveRowProps) => {
  const lastVal = trace && trace.length > 0 ? trace[trace.length - 1][1] : '?';
  const valStr = isBus
    ? fmtBusValue(lastVal, radix)
    : String(bitOf(lastVal));
  const valCls = String(lastVal).match(/[xX]/) ? 'x' : (String(lastVal).match(/[zZ]/) ? 'z' : '');
  const handleTrackClick = (e: MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    if (onClick) onClick(e);
    if (!onEdgeClick) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const edgeTime = nearestWaveEdgeTime(trace, e.clientX - rect.left, width);
    if (edgeTime != null) onEdgeClick(edgeTime, e);
  };
  return (
    <div className={`wave-row ${selected ? 'sel' : ''}`} onClick={onClick}
         title={name + (scope ? ' · ' + scope : '')}>
      <div className="wave-name">
        <span className="scope-glyph">{isBus ? '═' : '─'}</span>
        <span>{name}</span>
        {isBus && <span className="radix">{radix}</span>}
      </div>
      <div className={`wave-val ${valCls}`}>{valStr}</div>
      <div className="wave-track wave-area" onClick={handleTrackClick} title="click a transition edge to move cursor B">
        <svg className="wave-svg" width={width} height={WAVE_HEIGHT}>
          {isBus ? (
            <BusWave trace={trace} width={width} radix={radix} />
          ) : (
            <path d={bitWavePath(trace, width)}
                  stroke={colorHint || '#7CFC4D'}
                  strokeWidth={1.4} fill="none" shapeRendering="crispEdges" />
          )}
        </svg>
      </div>
    </div>
  );
};

// Time ruler with tick marks. Accepts an optional [tMin, tMax] range
// + signal count so the labels reflect the actual VCD instead of the
// hard-coded 0-200 mock window.
export interface TimeRulerProps {
  width: number;
  tMin?: number;
  tMax?: number;
  signals?: number;
  scope?: string;
  timescale?: string;
}

export const TimeRuler = ({ width, tMin = 0, tMax = 200, signals = 0, scope = 'scope', timescale = 'ns' }: TimeRulerProps) => {
  // Pick a tick stride that yields ~10 labeled ticks across the axis.
  const span = Math.max(1, tMax - tMin);
  const rawStep = span / 10;
  // Snap to a "nice" 1/2/5 × 10^n step.
  const mag = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const norm = rawStep / mag;
  const niceStep = norm < 1.5 ? 1 : (norm < 3.5 ? 2 : (norm < 7.5 ? 5 : 10));
  const step = niceStep * mag;
  const start = Math.ceil(tMin / step) * step;
  const ticks: ReactNode[] = [];
  for (let t = start; t <= tMax; t += step) {
    const x = ((t - tMin) / span) * width;
    ticks.push(
      <span key={t} className="tr-tick" style={{ left: x }}>
        {Number.isInteger(t) ? t : t.toFixed(1)}
      </span>
    );
  }
  return (
    <div className="time-ruler">
      <div className="tr-corner">{scope} · {signals} sig</div>
      <div className="tr-vcorner">value @ A</div>
      <div className="tr-axis">{ticks}</div>
    </div>
  );
};

// Cursor + delta marker overlay. Position passed as time (ns).
export interface WaveCursorProps {
  time: number;
  label?: ReactNode;
  kind?: string;
  width: number;
}

export const WaveCursor = ({ time, label, kind = 'a', width }: WaveCursorProps) => {
  const x = tToX(time, width);
  return (
    <>
      <div className={`wave-cursor ${kind === 'b' ? 'b' : kind === 'marker' ? 'marker' : ''}`} style={{ left: x + 'px' }} />
      {label && (
        <div className={`wave-cursor-label ${kind === 'b' ? 'b' : kind === 'marker' ? 'marker' : ''}`} style={{ left: x + 'px' }}>
          {label}
        </div>
      )}
    </>
  );
};

// X-prop hatch overlay
export interface XPropOverlayProps {
  from: number;
  to: number;
  width: number;
}

export const XPropOverlay = ({ from, to, width }: XPropOverlayProps) => {
  const x1 = tToX(from, width);
  const x2 = tToX(to, width);
  return <div className="wave-xprop" style={{ left: x1 + 'px', width: (x2 - x1) + 'px' }} />;
};

// Wave pin (annotation marker)
export interface WavePinProps {
  time: number;
  kind?: string;
  top?: number;
  width: number;
  onClick?: (e: MouseEvent<HTMLDivElement>) => void;
  title?: string;
}

export const WavePin = ({ time, kind = 'mag', top = 50, width, onClick, title }: WavePinProps) => (
  <div className={`wave-pin ${kind}`} style={{ left: tToX(time, width) + 'px', top: top + '%' }} onClick={onClick} title={title} />
);

// Scope tree
interface ScopeItem {
  kind: string;
  name: string;
  depth: number;
  badge?: string;
}

export interface ScopeTreeProps {
  selected?: string;
  onSelect?: (name: string) => void;
}

export const ScopeTree = ({ selected, onSelect }: ScopeTreeProps) => {
  const items: ScopeItem[] = [
    { kind: 'module', name: 'tb_top',          depth: 0, badge: 'tb' },
    { kind: 'module', name: 'dut',             depth: 1, badge: 'dut' },
    { kind: 'module', name: 'spi_master_inst', depth: 2, badge: 'spi' },
    { kind: 'signal', name: 'clk',             depth: 3 },
    { kind: 'signal', name: 'rst_n',           depth: 3 },
    { kind: 'signal', name: 'state',           depth: 3, badge: 'enum' },
    { kind: 'signal', name: 'bit_cnt[3:0]',    depth: 3, badge: '4b' },
    { kind: 'signal', name: 'shift_reg[7:0]',  depth: 3, badge: '8b' },
    { kind: 'signal', name: 'mosi',            depth: 3 },
    { kind: 'signal', name: 'miso',            depth: 3 },
    { kind: 'signal', name: 'sclk',            depth: 3 },
    { kind: 'signal', name: 'cs_n',            depth: 3 },
    { kind: 'signal', name: 'done',            depth: 3 },
    { kind: 'module', name: 'monitor',         depth: 2, badge: 'mon' },
    { kind: 'module', name: 'driver',          depth: 1, badge: 'drv' },
  ];
  return (
    <div className="scope-tree">
      {items.map(it => (
        <div
          key={it.name + it.depth}
          className={`scope-row ${it.kind} ${selected === it.name ? 'sel' : ''}`}
          style={{ paddingLeft: 12 + it.depth * 14 + 'px' }}
          onClick={() => onSelect && onSelect(it.name)}
        >
          <span className="glyph">{it.kind === 'module' ? '▸' : '·'}</span>
          <span style={{ flex: 1, fontFamily: 'var(--mono)' }}>{it.name}</span>
          {it.badge && <span className="badge">{it.badge}</span>}
        </div>
      ))}
    </div>
  );
};

// Title bar reused across variants. `workspace` prop overrides the
// fallback "spi_master/" placeholder so the live IP shows up here
// when the panel is mounted against a real workspace (e.g. gpio).
export interface AtlasTitleProps {
  subtitle?: ReactNode;
  right?: ReactNode;
  workspace?: string;
}

export const AtlasTitle = ({ subtitle, right, workspace }: AtlasTitleProps) => {
  const ws = (workspace && String(workspace).trim()) || 'spi_master';
  return (
    <div className="vt-title">
      <span className="dot" />
      <span><b>ATLAS</b> · common_ai_agent</span>
      <span className="pipe">│</span>
      <span><b>workspace</b> · {ws}/</span>
      {subtitle && (
        <>
          <span className="pipe">│</span>
          <span style={{ color: 'var(--accent)' }}>{subtitle}</span>
        </>
      )}
      <span className="spacer" />
      {right}
    </div>
  );
};

// Status bar
interface StatusItem {
  kind?: string;
  text: ReactNode;
  color?: string;
}

export interface AtlasStatusProps {
  items?: StatusItem[];
  right?: ReactNode;
}

export const AtlasStatus = ({ items, right }: AtlasStatusProps) => (
  <div className="vt-status">
    {items && items.map((it, i) => (
      <Fragment key={i}>
        {it.kind === 'tag' ? (
          <span className="tag">{it.text}</span>
        ) : (
          <span style={{ color: it.color || 'inherit' }}>{it.text}</span>
        )}
        {i < items.length - 1 && <span style={{ color: 'var(--line-2)' }}>│</span>}
      </Fragment>
    ))}
    <span style={{ flex: 1 }} />
    {right}
  </div>
);

// Agent transcript block
export interface TraceBlockProps {
  kind: string;
  tag?: ReactNode;
  children?: ReactNode;
}

export const TraceBlock = ({ kind, tag, children }: TraceBlockProps) => (
  <div className={`trace-block ${kind}`}>
    <span className="trace-tag">{tag || kind}</span>
    <span style={{ color: 'var(--fg)' }}>{children}</span>
  </div>
);

const _debugCardText = (value: unknown, pretty = false): string => {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') return String(value);
  try {
    return JSON.stringify(value, null, pretty ? 2 : 0);
  } catch (_) {
    return String(value);
  }
};

// Tool call card
export interface ToolCardProps {
  name?: unknown;
  args?: unknown;
  result?: unknown;
  status?: string;
}

export const ToolCard = ({ name, args, result, status = 'done' }: ToolCardProps) => {
  const argsText = _debugCardText(args);
  const resultText = _debugCardText(result, true);
  return (
    <div className="tool-card">
      <div className="tc-h">
        <span style={{ color: status === 'running' ? 'var(--cyan)' : 'var(--ok)' }}>
          {status === 'running' ? '◌' : '✓'}
        </span>
        <span className="name">{_debugCardText(name) || 'tool'}</span>
        <span className="args">({argsText})</span>
        <span style={{ marginLeft: 'auto', color: 'var(--fg-mute)', fontSize: 10 }}>{_debugCardText(status)}</span>
      </div>
      {resultText && <div className="tc-body">{resultText}</div>}
    </div>
  );
};

// Mini "wavelet" preview SVG used in scope tree previews
export interface MiniWaveProps {
  trace?: Trace | null;
  width?: number;
  height?: number;
}

export const MiniWave = ({ trace, width = 38, height = 8 }: MiniWaveProps) => {
  if (!trace || trace.length === 0) return null;
  const yHi = 1, yLo = height - 1;
  const xMax = 200;
  let d = '';
  for (let i = 0; i < trace.length; i++) {
    const [t, v] = trace[i];
    const x = (t / xMax) * width;
    const nx = i + 1 < trace.length ? (trace[i + 1][0] / xMax) * width : width;
    const y = v === 1 ? yHi : v === 0 ? yLo : (yHi + yLo) / 2;
    if (i === 0) d += `M ${x} ${y}`;
    else d += ` L ${x} ${y}`;
    d += ` L ${nx} ${y}`;
  }
  return (
    <svg width={width} height={height} className="scope-spark">
      <path d={d} stroke="var(--accent)" strokeWidth={1} fill="none" />
    </svg>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// These globals are owned by THIS file. They are not yet declared in
// types/atlas-window.d.ts (that file only carries already-fully-cut-over
// globals), so the assignments go through a single `Record` view of
// `window` to register them without changing any runtime behavior. Remove
// once all consumers import the named exports directly.
const _w = window as unknown as Record<string, unknown>;
_w.MOCK_TRACES = MOCK_TRACES;
_w.MOCK_SOURCE = MOCK_SOURCE;
_w.renderSourceLine = renderSourceLine;
_w.SourceCode = SourceCode;
_w.waveTimeToX = tToX;
_w.nearestWaveEdgeTime = nearestWaveEdgeTime;
_w.WaveRow = WaveRow;
_w.TimeRuler = TimeRuler;
_w.WaveCursor = WaveCursor;
_w.XPropOverlay = XPropOverlay;
_w.WavePin = WavePin;
_w.ScopeTree = ScopeTree;
_w.AtlasTitle = AtlasTitle;
_w.AtlasStatus = AtlasStatus;
_w.TraceBlock = TraceBlock;
_w.ToolCard = ToolCard;
_w.MiniWave = MiniWave;
