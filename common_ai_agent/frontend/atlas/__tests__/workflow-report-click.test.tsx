import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';

vi.mock('../preview-pane.tsx', () => ({
  PreviewPane: ({
    path,
    focusLine = 0,
    lintDiagnostic,
  }: {
    readonly path?: string;
    readonly focusLine?: number;
    readonly lintDiagnostic?: { readonly message?: string } | null;
  }) => (
    <div data-testid="preview-pane">
      {path || 'no preview'}|L{focusLine}|{lintDiagnostic?.message || 'no lint diagnostic'}
    </div>
  ),
}));

type TestWindow = typeof window & Record<string, unknown>;

function installWorkflowReportGlobals(responseBody: Record<string, unknown>): void {
  const w = window as TestWindow;
  w.WORKFLOW_REPORT_TABS = {
    lint: {
      label: 'lint report',
      title: 'Lint Report',
      folders: ['lint'],
      paths: (ip: string) => [`${ip}/lint/dut_lint.json`],
    },
    coverage: {
      label: 'coverage report',
      title: 'Coverage Report',
      folders: ['cov', 'sim'],
      paths: (ip: string) => [`${ip}/cov/coverage.json`],
    },
  };
  w.PreviewPane = ({ path }: { readonly path?: string }) => (
    <div data-testid="window-preview-pane">{path || 'no preview'}</div>
  );
  w.readAtlasAsyncResource = vi.fn(async () => ({}));
  w.atlasData = { refreshFileTree: vi.fn() };
  w.FILE_TREE = [];
  w.SCOPE_PATH = 'demo_ip';
  w.ACTIVE_SESSION = 'default/demo_ip/lint';

  Object.assign(globalThis, {
    fetch: vi.fn(async () =>
      new Response(JSON.stringify(responseBody), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  });
}

describe('Workflow report click surfaces', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders lint report summary when the report endpoint returns an empty state', async () => {
    installWorkflowReportGlobals({
      exists: false,
      resolved_ip: 'demo_ip',
      report_path: '',
      tool_results: [],
    });
    const { WorkflowReportPane } = await import('../workflow-report.tsx');

    expect(() => render(<WorkflowReportPane workflow="lint" activeIp="demo_ip" />)).not.toThrow();

    expect(await screen.findByText('No dut_lint.json found yet.')).toBeInTheDocument();
  });

  it('keeps long lint commands constrained inside report rows', async () => {
    const longCommand = [
      'pyslang rtl/demo_ip.sv rtl/demo_ip_axi_slave_ingress.sv rtl/demo_ip_packet_engine.sv',
      'verilator --lint-only -Wall -Irtl -f list/demo_ip.f --top-module demo_ip',
    ].join(' && ');
    installWorkflowReportGlobals({
      exists: true,
      resolved_ip: 'demo_ip',
      tool: 'pyslang+verilator',
      passed: true,
      errors: 0,
      warnings: 0,
      suppression_violations: 0,
      style_violations: 0,
      command: longCommand,
      report_path: 'demo_ip/lint/dut_lint.json',
      log_path: 'demo_ip/lint/dut_lint.log',
      log_exists: true,
      tool_results: [
        { tool: 'pyslang', passed: true, returncode: 0, errors: 0, warnings: 0, command: longCommand, diagnostics: [] },
        { tool: 'verilator', passed: true, returncode: 0, errors: 0, warnings: 0, command: longCommand, diagnostics: [] },
      ],
    });
    const { WorkflowReportPane } = await import('../workflow-report.tsx');

    render(<WorkflowReportPane workflow="lint" activeIp="demo_ip" />);

    const commandRows = await screen.findAllByTitle(longCommand);
    expect(commandRows.length).toBeGreaterThanOrEqual(2);
    for (const row of commandRows) {
      expect(row).toHaveStyle({ minWidth: '0' });
    }
  });

  it('groups lint diagnostics by rule with foldable counts', async () => {
    installWorkflowReportGlobals({
      exists: true,
      resolved_ip: 'demo_ip',
      tool: 'pyslang+verilator',
      passed: false,
      errors: 3,
      warnings: 0,
      suppression_violations: 0,
      style_violations: 0,
      command: 'pyslang rtl/demo.sv && verilator --lint-only rtl/demo.sv',
      report_path: 'demo_ip/lint/dut_lint.json',
      tool_results: [
        {
          tool: 'verilator',
          passed: false,
          returncode: 1,
          errors: 3,
          warnings: 0,
          command: 'verilator --lint-only rtl/demo.sv',
          diagnostics: [
            { severity: 'error', rule: 'WIDTH', path: 'demo_ip/rtl/demo.sv', file: 'rtl/demo.sv', line: 7, message: 'Output port connection width mismatch: left 32 bits, right 8 bits' },
            { severity: 'error', rule: 'WIDTH', path: 'demo_ip/rtl/demo.sv', file: 'rtl/demo.sv', line: 8, message: 'Assignment width mismatch: left 16 bits, right 1 bit' },
            { severity: 'error', rule: 'UNUSED', path: 'demo_ip/rtl/demo.sv', file: 'rtl/demo.sv', line: 10, message: 'Signal is not used: tmp' },
          ],
        },
      ],
    });
    const { WorkflowReportPane } = await import('../workflow-report.tsx');

    render(<WorkflowReportPane workflow="lint" activeIp="demo_ip" />);

    const widthGroup = await screen.findByTestId('lint-diagnostic-group-WIDTH');
    expect(within(widthGroup).getByText('WIDTH')).toBeInTheDocument();
    expect(within(widthGroup).getByText('2')).toBeInTheDocument();
    const unusedGroup = screen.getByTestId('lint-diagnostic-group-UNUSED');
    expect(within(unusedGroup).getByText('UNUSED')).toBeInTheDocument();
    expect(within(unusedGroup).getByText('1')).toBeInTheDocument();
  });

  it('passes the selected lint diagnostic into the source preview', async () => {
    installWorkflowReportGlobals({
      exists: true,
      resolved_ip: 'demo_ip',
      tool: 'pyslang+verilator',
      passed: false,
      errors: 1,
      warnings: 0,
      suppression_violations: 0,
      style_violations: 0,
      command: 'verilator --lint-only rtl/demo.sv',
      report_path: 'demo_ip/lint/dut_lint.json',
      tool_results: [
        {
          tool: 'verilator',
          passed: false,
          returncode: 1,
          errors: 1,
          warnings: 0,
          command: 'verilator --lint-only rtl/demo.sv',
          diagnostics: [
            {
              severity: 'error',
              rule: 'WIDTH',
              path: 'demo_ip/rtl/demo.sv',
              file: 'rtl/demo.sv',
              line: 7,
              column: 12,
              message: 'Output port connection width mismatch: left 32 bits, right 8 bits',
              source: 'assign out = in[7:0];',
            },
          ],
        },
      ],
    });
    const { WorkflowReportPane } = await import('../workflow-report.tsx');

    render(<WorkflowReportPane workflow="lint" activeIp="demo_ip" />);
    fireEvent.click(await screen.findByRole('button', { name: /Output port connection width mismatch/ }));

    expect(await screen.findByTestId('preview-pane')).toHaveTextContent(
      'demo_ip/rtl/demo.sv|L7|Output port connection width mismatch: left 32 bits, right 8 bits',
    );
    expect((window as TestWindow).readAtlasAsyncResource).toHaveBeenCalledWith('file', 'demo_ip/rtl/demo.sv', true);
  });

  it('renders coverage report summary when the report endpoint returns malformed empty data', async () => {
    installWorkflowReportGlobals({
      exists: false,
      resolved_ip: 'demo_ip',
      tools: 'not-an-array',
      artifacts: null,
      vcd_paths: null,
      run: null,
    });
    const { WorkflowReportPane } = await import('../workflow-report.tsx');

    expect(() => render(<WorkflowReportPane workflow="coverage" activeIp="demo_ip" />)).not.toThrow();

    expect(await screen.findByText(/No coverage artifacts found yet/)).toBeInTheDocument();
  });
});
