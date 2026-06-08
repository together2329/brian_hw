import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const appRootSource = readFileSync(resolve(here, '../app.tsx'), 'utf8');
const appSource = readFileSync(resolve(here, '../app-session-hook.tsx'), 'utf8');
const appShellSource = readFileSync(resolve(here, '../app-shell.tsx'), 'utf8');
const pipelineSource = readFileSync(resolve(here, '../pipeline-rail.tsx'), 'utf8');
const gitTabSource = readFileSync(resolve(here, '../git-tab.tsx'), 'utf8');

describe('Atlas IP roster source', () => {
  it('does not seed authenticated IP_ID options from browser-local stale state', () => {
    expect(appSource).toContain("const ownerScopedRoster = authState === 'authed' && !!currentUserSession;");
    expect(appSource).toContain("const browserLocalRosterAllowed = !ownerScopedRoster && authState !== 'checking';");
    expect(appSource).toContain('if (browserLocalRosterAllowed && acceptIp(rememberedIp)) nextIps.add(rememberedIp);');
    expect(appSource).toContain('if (browserLocalRosterAllowed && acceptIp(activeIp)) nextIps.add(activeIp);');
  });

  it('does not seed authenticated SESSION options from another owner browser-local state', () => {
    expect(appSource).toContain('const rememberedBelongsToCurrentUser = !!(');
    expect(appSource).toContain('(browserLocalRosterAllowed || rememberedBelongsToCurrentUser) && rememberedParts.workspaceSession');
    expect(appSource).toContain("|| (browserLocalRosterAllowed ? (window as any).ATLAS_WORKSPACE_SESSION_ID : '')");
    expect(appSource).toContain('liveParts.sessionId && liveParts.sessionId !== currentUserSession');
    expect(appSource).toContain('namespaceFor(\n          currentUserSession,\n          WORKFLOW_DEFAULT,');
  });

  it('does not preserve a previous user IP list when the owner-scoped roster probe fails', () => {
    expect(appSource).toContain('if (!ipListOk && !ownerScopedRoster) (prev || []).forEach');
  });

  it('hides detached active IP options in authenticated mode', () => {
    expect(appShellSource).toContain(
      "authState !== 'authed' && activeIp && activeIp !== WORKFLOW_DEFAULT && !ipOptions.includes(activeIp)"
    );
  });

  it('keeps secondary IP rosters from falling back to stale active IPs for logged-in users', () => {
    expect(pipelineSource).toContain('if (!dead && !ownerScoped && activeIp) setIps([activeIp]);');
    expect(gitTabSource).toContain('const nextNames = !ownerScoped && initialIp && !names.includes(initialIp)');
  });

  it('resets IP and workflow when switching workspace sessions', () => {
    const start = appRootSource.indexOf('const selectSessionId =');
    const body = appRootSource.slice(start, appRootSource.indexOf('const selectIp =', start));

    expect(body).toContain('activateNamespace(owner, WORKFLOW_DEFAULT, WORKFLOW_DEFAULT, true);');
  });
});
