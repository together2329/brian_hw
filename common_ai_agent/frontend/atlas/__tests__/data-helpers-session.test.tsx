import { beforeEach, describe, expect, it } from 'vitest';

import {
  activeIpFromSession,
  normalizeSessionName,
} from '../data-helpers';
import {
  resolveActiveSession,
} from '../workspace-session-routing';

describe('workspace session normalization', () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.replaceState({}, '', '/');
    const w = window as any;
    w.normalizeAtlasSessionName = normalizeSessionName;
    w.atlasData = { normalizeSessionName };
    w.ATLAS_USER = { username: 'webalice' };
    w.ATLAS_USER_SESSION_ID = 'webalice';
    w.ATLAS_WORKSPACE_SESSION_ID = 'default';
  });

  it('preserves user/workspace/ip/workflow namespaces instead of truncating to ip/workflow', () => {
    expect(normalizeSessionName('webalice/s1/NEWIP_MCTP/default'))
      .toBe('webalice/s1/NEWIP_MCTP/default');
    expect(activeIpFromSession('webalice/s1/NEWIP_MCTP/default'))
      .toBe('NEWIP_MCTP');
  });

  it('preserves v2 namespaces under explicit .session paths', () => {
    expect(normalizeSessionName('/tmp/root/.session/webalice/s1/NEWIP_MCTP/default/conversation.json'))
      .toBe('webalice/s1/NEWIP_MCTP/default');
    expect(normalizeSessionName('/tmp/root/webalice/s1/NEWIP_MCTP/default'))
      .toBe('NEWIP_MCTP/default');
  });

  it('uses URL session and workspace_session before stale local storage', () => {
    localStorage.setItem('atlasActiveSession', 'webalice/default/default/default');
    localStorage.setItem('atlasWorkspaceSessionId', 'default');
    window.history.replaceState(
      {},
      '',
      '/?session=webalice%2Fs1%2FNEWIP_MCTP%2Fdefault&workspace_session=s1&ip=NEWIP_MCTP&workflow=default',
    );
    expect(resolveActiveSession()).toBe('webalice/s1/NEWIP_MCTP/default');
  });
});
