import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createRef, useState } from 'react';

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
