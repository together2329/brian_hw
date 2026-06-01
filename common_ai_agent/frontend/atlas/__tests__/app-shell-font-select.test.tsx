import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createRef, useState } from 'react';
import { readFileSync } from 'node:fs';

import { AppShell } from '../app-shell';

type RenderResult = {
  calls: string[];
};

function renderShell(initialFontMode = 'mono'): RenderResult {
  const calls: string[] = [];
  const noop = vi.fn();

  function Harness() {
    const [fontMode, setFontModeState] = useState(initialFontMode);
    const setFontMode = (value: string) => {
      calls.push(value);
      setFontModeState(value);
    };

    return (
      <AppShell
        dir="B"
        theme="dark"
        setTheme={noop}
        topNotice=""
        setTopNotice={noop}
        wfSwitching={null}
        bootHidden={true}
        setBootHidden={noop}
        bootSteps={{}}
        bootFailed={false}
        bootDisplayDone={true}
        nameEntry={null}
        setNameEntry={noop}
        nameEntryBusy={false}
        nameEntryInputRef={createRef<HTMLInputElement>()}
        commitNameEntry={noop}
        newIpInitialWorkflow={() => 'default'}
        normalizeSession={(value: unknown) => String(value || '')}
        activeNamespace="tester/default/default"
        ownerEditable={true}
        activeSessionId="tester"
        sessionIdOptions={['tester']}
        selectSessionId={noop}
        newSessionId={noop}
        activeIp="default"
        WORKFLOW_DEFAULT="default"
        selectIp={noop}
        ipOptions={['default']}
        authState="authed"
        beginNameEntry={noop}
        execMode="single-worker"
        currentWorkflow={() => 'default'}
        fontMode={fontMode}
        setFontMode={setFontMode}
        fontScale="compact"
        setFontScale={noop}
        resolution="auto"
        setResolution={noop}
        uiLang="en"
        chooseUiLang={noop}
        stopAgent={noop}
        exitAll={noop}
        screen="workspace"
        setScreen={noop}
        runMode="engineering"
        saveRunPolicy={noop}
        WORKFLOW_OPTIONS={['default']}
        selectWorkflow={noop}
        activateDashboardSession={noop}
      />
    );
  }

  render(<Harness />);
  return { calls };
}

describe('AppShell font selector', () => {
  beforeEach(() => {
    localStorage.clear();
    (window as any).Workspace = () => null;
    (window as any).ATLAS_USER = undefined;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('selects a font mode through the normal change event', () => {
    const { calls } = renderShell('mono');
    const select = screen.getByLabelText('Font family') as HTMLSelectElement;

    expect(select).toHaveValue('mono');
    fireEvent.change(select, { target: { value: 'sans' } });

    expect(calls).toContain('sans');
    expect(select).toHaveValue('sans');
    expect(localStorage.getItem('atlasFontModeUserSet')).toBe('1');
  });

  it('also accepts input events from native pickers', () => {
    const { calls } = renderShell('mono');
    const select = screen.getByLabelText('Font family') as HTMLSelectElement;

    fireEvent.input(select, { target: { value: 'windows' } });

    expect(calls).toContain('windows');
    expect(select).toHaveValue('windows');
  });

  it('falls back to mono when persisted state is invalid', () => {
    renderShell('missing-font');

    expect(screen.getByLabelText('Font family')).toHaveValue('mono');
  });
});

describe('Atlas font CSS cascade', () => {
  it('lets font mode selectors override Windows platform defaults', () => {
    const css = readFileSync('styles.css', 'utf8');
    const platformIndex = css.indexOf('html[data-platform="windows"]');

    expect(platformIndex).toBeGreaterThan(-1);
    for (const mode of ['mono', 'sans', 'windows', 'system']) {
      const selector = `html[data-font="${mode}"]`;
      const selectorIndex = css.indexOf(selector);

      expect(selectorIndex).toBeGreaterThan(platformIndex);
    }
  });

  it('keeps Windows text on the native hinting path instead of fuzzy geometric rendering', () => {
    const css = readFileSync('styles.css', 'utf8');

    expect(css).not.toMatch(/text-rendering:\s*(?:geometricPrecision|optimizeLegibility)\b/);
    expect(css).toMatch(/html\[data-platform="windows"\]\s+\.app\s*\{[^}]*text-rendering:\s*auto\b/s);
    expect(css).toMatch(/--windows-mono:\s*Consolas,/);
  });

  it('applies font mode changes to UI, code, and enhanced panel font tokens', () => {
    const css = readFileSync('styles.css', 'utf8');
    const blockFor = (mode: string): string => {
      const match = css.match(new RegExp(`html\\[data-font="${mode}"\\],[\\s\\S]*?\\[data-font="${mode}"\\]\\s*\\{([\\s\\S]*?)\\n\\}`));
      return match ? match[1] : '';
    };

    for (const mode of ['mono', 'sans', 'windows', 'system']) {
      const block = blockFor(mode);

      expect(block).toContain('--mono:');
      expect(block).toContain('--code-font:');
      expect(block).toContain('--enh-mono:');
    }
  });

  it('keeps source previews on one fixed monospace size independent of UI font mode', () => {
    const css = readFileSync('styles.css', 'utf8');

    expect(css).toContain('--source-code-font: var(--mono-base);');
    expect(css).toContain('--preview-code-font-size: 12px;');
    expect(css).toContain('--preview-code-line-height: 1.55;');
    expect(css).toMatch(/\.foldable-pane\s*\{[^}]*font-family:\s*var\(--source-code-font/s);
    expect(css).toMatch(/\.foldable-pane\s*\{[^}]*font-size:\s*var\(--preview-code-font-size/s);
    expect(css).toMatch(/\.foldable-pane\s+\.lineno,[\s\S]*\.foldable-pane\s+\.line,[\s\S]*\.foldable-pane\s+\.line\s+\.token\s*\{[^}]*font-size:\s*inherit\s*!important/s);
    expect(css).toMatch(/\.code-pane,[\s\S]*\.code-pane\s+code\[class\*="language-"\]\s*\{[^}]*font-size:\s*var\(--preview-code-font-size/s);
  });

  it('maps SystemVerilog extensions to the Prism SystemVerilog grammar', () => {
    const html = readFileSync('index.vite.html', 'utf8');

    expect(html).toMatch(/sv:\s*'systemverilog'/);
    expect(html).toMatch(/svh:\s*'systemverilog'/);
    expect(html).toMatch(/v:\s*'verilog'/);
    expect(html).toMatch(/vh:\s*'verilog'/);
  });
});

describe('Atlas sharp resolution defaults', () => {
  it('migrates saved fixed canvas presets back to auto to avoid startup scaling blur', () => {
    const html = readFileSync('index.vite.html', 'utf8');

    expect(html).toContain('atlasResolutionMigratedSharpText2');
    expect(html).toMatch(/saved\s+&&\s+saved\s+!==\s+'auto'/);
    expect(html).toContain("localStorage.setItem('atlasResolution', 'auto')");
    expect(html).toContain("res.key === 'auto'");
  });
});
