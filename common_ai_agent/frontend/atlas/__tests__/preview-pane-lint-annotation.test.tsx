import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';

type TestWindow = typeof window & Record<string, unknown>;

function escapeHtml(value: unknown): string {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function installPreviewGlobals(): void {
  const w = window as TestWindow;
  w._buildFoldTree = () => ({ children: [], line_start: 0, line_end: 1e9 });
  w._copyToClipboard = vi.fn();
  w._escHtml = escapeHtml;
  w._highlightYamlLine = escapeHtml;
  w._markdownHtml = vi.fn(() => '');
  w._normalizeMarkdownImageSrc = vi.fn((src: unknown) => String(src || ''));
  w._postProcessMarkdownNode = vi.fn();
  w.atlasFileTreeMetaForPath = vi.fn(() => ({}));
  w.atlasFormatBytes = vi.fn(() => '');
  w.atlasImageMimeForExt = vi.fn(() => 'image/png');
  w.scheduleAtlasPreviewWork = (work: () => void) => {
    work();
    return undefined;
  };
  w.useAtlasAsyncResource = vi.fn(() => [{}, vi.fn()]);
  w.AtlasStatusBadge = () => null;
  w.DocxFallbackPane = () => null;
  w._FOLD_KIND_COLOR = {};
  w.PRISM_LANG_MAP = { sv: 'systemverilog' };
  w.Prism = undefined;
  Object.assign(globalThis, {
    fetch: vi.fn(async () =>
      new Response(JSON.stringify({ ranges: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  });
}

describe('PreviewPane lint diagnostic annotations', () => {
  beforeEach(() => {
    vi.resetModules();
    installPreviewGlobals();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders the lint diagnostic explanation under the selected source line', async () => {
    const { FoldablePane } = await import('../preview-pane.tsx');

    render(
      <FoldablePane
        path="demo_ip/rtl/demo.sv"
        body={'module demo;\nassign out = in[7:0];\nendmodule'}
        lang="systemverilog"
        lineCount={3}
        focusLine={2}
        lintDiagnostic={{
          severity: 'error',
          rule: 'WIDTH',
          path: 'demo_ip/rtl/demo.sv',
          file: 'rtl/demo.sv',
          line: 2,
          column: 12,
          message: 'Output port connection width mismatch: left 32 bits, right 8 bits',
          source: 'assign out = in[7:0];',
        }}
      />,
    );

    const annotation = await screen.findByTestId('lint-diagnostic-annotation');
    expect(annotation).toHaveTextContent('WIDTH');
    expect(annotation).toHaveTextContent('Output port connection width mismatch: left 32 bits, right 8 bits');
    expect(annotation).toHaveTextContent('assign out = in[7:0];');
  });
});
