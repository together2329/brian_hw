import { describe, expect, it } from 'vitest';

import {
  activeIpForRouting,
  healthCountersMatchRoute,
  isRealIp,
  scopeIp,
  sessionRoute,
  sessionIpFromSession,
  sessionsShareOwnerIp,
  shouldUseBrowserSession,
} from '../lib/session_routing.mjs';

describe('Atlas session routing', () => {
  it('routes chat to the IP embedded in the active orchestrator session before stale scope', () => {
    expect(activeIpForRouting({
      sessions: ['happy2/mctp/orchestrator'],
      activeIp: 'new_axi',
      scopePath: 'new_axi',
    })).toBe('mctp');
  });

  it('keeps worker views scoped to their own IP', () => {
    expect(sessionIpFromSession('happy2/mctp/ssot-gen')).toBe('mctp');
    expect(sessionIpFromSession('happy2/session-a/mctp/ssot-gen')).toBe('mctp');
    expect(activeIpForRouting({
      sessions: ['happy2/mctp/ssot-gen'],
      activeIp: 'old_ip',
      scopePath: 'old_ip',
    })).toBe('mctp');
  });

  it('falls back to active IP then scope only when no session IP exists', () => {
    expect(activeIpForRouting({
      sessions: ['happy2/default/orchestrator'],
      activeIp: 'uart_axi',
      scopePath: 'stale_axi',
    })).toBe('uart_axi');
    expect(activeIpForRouting({
      sessions: ['happy2/default/orchestrator'],
      activeIp: '',
      scopePath: 'stale_axi',
    })).toBe('stale_axi');
  });

  it('does not treat workflow names as IP names', () => {
    expect(isRealIp('orchestrator')).toBe(false);
    expect(isRealIp('ssot-gen')).toBe(false);
    expect(scopeIp('happy2/ssot-gen')).toBe('');
  });

  it('rejects health context from another IP while preserving same-IP workers', () => {
    expect(sessionRoute('happy2/mctp/orchestrator')).toEqual({
      owner: 'happy2',
      ip: 'mctp',
      workflow: 'orchestrator',
    });
    expect(sessionsShareOwnerIp('happy2/mctp/orchestrator', 'happy2/mctp/ssot-gen')).toBe(true);
    expect(healthCountersMatchRoute({
      browserSession: 'happy2/mctp/orchestrator',
      payloadSession: 'happy2/mctp/ssot-gen',
    })).toBe(true);
    expect(healthCountersMatchRoute({
      browserSession: 'happy2/mctp/orchestrator',
      payloadSession: 'happy2/NEW_MCTP/ssot-gen',
    })).toBe(false);
    expect(shouldUseBrowserSession({
      browserSession: 'happy2/mctp/orchestrator',
      payloadSession: 'happy2/NEW_MCTP/ssot-gen',
    })).toBe(true);
  });

  it('treats v2 user sessions as separate routing owners even for the same IP', () => {
    expect(sessionRoute('happy2/s1/mctp/orchestrator')).toEqual({
      owner: 'happy2/s1',
      ip: 'mctp',
      workflow: 'orchestrator',
    });
    expect(sessionsShareOwnerIp('happy2/s1/mctp/orchestrator', 'happy2/s1/mctp/ssot-gen')).toBe(true);
    expect(sessionsShareOwnerIp('happy2/s1/mctp/orchestrator', 'happy2/s2/mctp/ssot-gen')).toBe(false);
    expect(healthCountersMatchRoute({
      browserSession: 'happy2/s1/mctp/orchestrator',
      payloadSession: 'happy2/s2/mctp/ssot-gen',
    })).toBe(false);
    expect(shouldUseBrowserSession({
      browserSession: 'happy2/s1/mctp/orchestrator',
      payloadSession: 'happy2/s2/mctp/ssot-gen',
    })).toBe(true);
  });
});
