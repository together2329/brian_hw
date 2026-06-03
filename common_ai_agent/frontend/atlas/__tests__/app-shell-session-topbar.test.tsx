import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AppShell } from '../app-shell';

const noop = () => {};

describe('AppShell session topbar', () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders user, session, and IP as separate context controls', () => {
    (window as any).ATLAS_USER = { username: 'alice' };

    render(
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
        bootDisplayDone={false}
        nameEntry={null}
        setNameEntry={noop}
        nameEntryBusy={false}
        nameEntryInputRef={{ current: null }}
        commitNameEntry={noop}
        newIpInitialWorkflow={() => 'default'}
        normalizeSession={(value: unknown) => String(value || '').trim()}
        activeNamespace="alice/default/NEWIP_MCTP/default"
        ownerEditable={false}
        activeSessionId="alice"
        activeWorkspaceSession="default"
        sessionIdOptions={['default', 's1']}
        selectSessionId={noop}
        newSessionId={noop}
        activeIp="NEWIP_MCTP"
        WORKFLOW_DEFAULT="default"
        selectIp={noop}
        ipOptions={['default', 'NEWIP_MCTP']}
        authState="authed"
        beginNameEntry={noop}
        execMode="single-worker"
        currentWorkflow={() => 'default'}
        fontMode="mono"
        setFontMode={noop}
        fontScale="compact"
        setFontScale={noop}
        resolution="1920x1080"
        setResolution={noop}
        uiLang="en"
        chooseUiLang={noop}
        stopAgent={noop}
        exitAll={noop}
        screen="workspace"
        setScreen={noop}
        runMode="starter"
        saveRunPolicy={noop}
        WORKFLOW_OPTIONS={['default']}
        selectWorkflow={noop}
        activateDashboardSession={noop}
      />,
    );

    expect(screen.getByLabelText('User owner')).toHaveValue('alice');
    expect(screen.getByLabelText('Workspace session')).toHaveValue('default');
    expect(screen.getByLabelText('IP ID')).toHaveValue('NEWIP_MCTP');
  });
});
