import { describe, it, expect } from 'vitest';
import { handoffFields, handoffStatusColor } from '../lib/orchestrator_chat_logic.mjs';

describe('handoffFields — dispatch / write_handoff labeled rendering', () => {
  it('parses a structured (argsRaw object) dispatch + result obs', () => {
    const action = {
      tool: 'dispatch_workflow',
      argsRaw: { ip: 'uart_tx', workflow: 'ssot-gen', prompt: 'Generate SSOT for UART TX', reason: 'kickoff', schedule: 'auto' },
    };
    const obs = { text: '{"workflow":"ssot-gen","status":"running","worker":"admin/uart_tx/ssot-gen","job_id":"j_8f2a","model":"deepseek-v4-pro"}' };
    const { sent, result } = handoffFields(action, obs);
    expect(sent).toMatchObject({
      target: 'ssot-gen', ip: 'uart_tx', task: 'Generate SSOT for UART TX', reason: 'kickoff', schedule: 'auto', fanout: false,
    });
    expect(result).toMatchObject({
      workflow: 'ssot-gen', status: 'running', worker: 'admin/uart_tx/ssot-gen', job: 'j_8f2a', model: 'deepseek-v4-pro',
    });
  });

  it('parses the flattened "key=value" args text form (hydration string)', () => {
    const action = {
      tool: 'dispatch_workflow',
      args: 'ip="uart_tx", workflow="ssot-gen", prompt="Generate SSOT for UART TX", reason="kickoff", schedule="auto"',
    };
    const { sent } = handoffFields(action, null);
    expect(sent.target).toBe('ssot-gen');
    expect(sent.ip).toBe('uart_tx');
    expect(sent.task).toBe('Generate SSOT for UART TX');
    expect(sent.reason).toBe('kickoff');
  });

  it('joins fan-out stages and flags fanout', () => {
    const action = { tool: 'dispatch_workflow', argsRaw: { ip: 'uart_tx', stages: ['lint', 'tb', 'syn'], schedule: 'dag', prompt: 'Verify RTL' } };
    const obs = { text: '{"jobs":[{"workflow":"lint","status":"running"},{"workflow":"tb","status":"running"},{"workflow":"syn","status":"queued"}]}' };
    const { sent, result } = handoffFields(action, obs);
    expect(sent.target).toBe('lint, tb, syn');
    expect(sent.fanout).toBe(true);
    expect(sent.schedule).toBe('dag');
    // per-stage result for fan-out rendering
    expect(result.jobs).toEqual([
      { workflow: 'lint', status: 'running' },
      { workflow: 'tb', status: 'running' },
      { workflow: 'syn', status: 'queued' },
    ]);
  });

  it('does not set jobs[] for a single-worker dispatch', () => {
    const { result } = handoffFields(
      { tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'ssot-gen' } },
      { text: '{"workflow":"ssot-gen","status":"running","job_id":"j1"}' });
    expect(result.jobs).toBeUndefined();
  });

  it('write_handoff pulls task/reason from payload when prompt is absent', () => {
    const action = { tool: 'write_handoff', argsRaw: { ip: 'uart_tx', workflow: 'rtl-gen', payload: { task: 'Implement RTL' }, reason: 'fl passed' } };
    const { sent } = handoffFields(action, null);
    expect(sent.target).toBe('rtl-gen');
    expect(sent.task).toBe('Implement RTL');
    expect(sent.reason).toBe('fl passed');
  });

  it('recovers payload fields embedded inside flattened args text', () => {
    const action = {
      tool: 'write_handoff',
      args: 'ip="mctp_axi", workflow="rtl-gen", payload={"task":"Implement AXI packet RTL","reason":"SSOT passed"}, schedule="serial"',
    };
    const { sent } = handoffFields(action, null);
    expect(sent.target).toBe('rtl-gen');
    expect(sent.ip).toBe('mctp_axi');
    expect(sent.task).toBe('Implement AXI packet RTL');
    expect(sent.reason).toBe('SSOT passed');
    expect(sent.schedule).toBe('serial');
  });

  it('surfaces an error result and leaves result null when obs has no signal', () => {
    const errObs = { text: '{"workflow":"sim","status":"error","result":{"error":"timeout after 600s"}}' };
    const { result } = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'sim' } }, errObs);
    expect(result.status).toBe('error');
    expect(result.error).toBe('timeout after 600s');

    const noResult = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'sim' } }, { text: 'not json' });
    expect(noResult.result).toBeNull();
  });

  it('surfaces a dispatch result with status=blocked + a reason/error (Task 6 feed visibility)', () => {
    // The orchestrator handoff feed must show a blocked dispatch distinctly: the
    // status comes through as "blocked" (colored red by handoffStatusColor) and
    // the reason/error is preserved for the HandoffCard error row.
    const obs = { text: '{"workflow":"rtl-gen","status":"blocked","result":{"error":"upstream SSOT changed; blocked on owner"}}' };
    const { result } = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'uart_tx', workflow: 'rtl-gen' } }, obs);
    expect(result.workflow).toBe('rtl-gen');
    expect(result.status).toBe('blocked');
    expect(result.error).toBe('upstream SSOT changed; blocked on owner');
    expect(handoffStatusColor(result.status)).toBe('#f85149');
  });

  it('maps status to colors', () => {
    expect(handoffStatusColor('running')).toBe('#58a6ff');
    expect(handoffStatusColor('completed')).toBe('#3fb950');
    expect(handoffStatusColor('blocked')).toBe('#f85149');
    expect(handoffStatusColor('queued')).toBe('#8b949e');
    // case-insensitive + variants
    expect(handoffStatusColor('PASSED')).toBe('#3fb950');
    expect(handoffStatusColor('in_progress')).toBe('#58a6ff');
    expect(handoffStatusColor('')).toBe('#8b949e');
    expect(handoffStatusColor(undefined)).toBe('#8b949e');
  });

  // ── Robustness / edge cases ────────────────────────────────────────────
  it('never throws on null/empty inputs', () => {
    expect(() => handoffFields(null, null)).not.toThrow();
    expect(handoffFields(null, null)).toEqual({ sent: { target: '', fanout: false, ip: '', task: '', reason: '', schedule: '' }, result: null });
    expect(handoffFields({}, {})).toMatchObject({ result: null });
  });

  it('strips a leading "└─ " before parsing the result JSON', () => {
    const obs = { text: '└─ {"workflow":"sim","status":"completed","job_id":"j9"}' };
    const { result } = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'sim' } }, obs);
    expect(result).toMatchObject({ workflow: 'sim', status: 'completed', job: 'j9' });
  });

  it('handles single-quoted values in the flattened text form', () => {
    const action = { tool: 'dispatch_workflow', args: "ip='uart_tx', workflow='rtl-gen', reason='go'" };
    const { sent } = handoffFields(action, null);
    expect(sent.target).toBe('rtl-gen');
    expect(sent.ip).toBe('uart_tx');
    expect(sent.reason).toBe('go');
  });

  it('reads worker from a workers[] array and survives non-JSON obs', () => {
    const wk = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'lint' } },
      { text: '{"status":"running","workers":["admin/x/lint"]}' });
    expect(wk.result.worker).toBe('admin/x/lint');
    const nan = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'lint' } }, { text: 'some plain log line' });
    expect(nan.result).toBeNull();
  });

  it('stringifies object metadata before it reaches React rendering', () => {
    const { sent, result } = handoffFields({
      tool: 'dispatch_workflow',
      argsRaw: {
        ip: 'x',
        workflow: { static: 'ssot-gen', internal: 'debug' },
        prompt: { static: 'make IP', internal: { source: 'test' } },
      },
    }, {
      text: JSON.stringify({
        status: { static: 'running', internal: 'queued' },
        jobs: [
          { workflow: { static: 'ssot-gen', internal: 'debug' }, status: { static: 'running', internal: 'queued' } },
          { workflow: 'rtl-gen', status: 'queued' },
        ],
      }),
    });

    expect(sent.target).toBe('{"static":"ssot-gen","internal":"debug"}');
    expect(sent.task).toBe('{"static":"make IP","internal":{"source":"test"}}');
    expect(result.status).toBe('{"static":"running","internal":"queued"}');
    expect(result.jobs).toEqual([
      { workflow: '{"static":"ssot-gen","internal":"debug"}', status: '{"static":"running","internal":"queued"}' },
      { workflow: 'rtl-gen', status: 'queued' },
    ]);
  });

  it('a single job in jobs[] does not trigger per-stage rendering', () => {
    const { result } = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'sim' } },
      { text: '{"jobs":[{"workflow":"sim","status":"running","job_id":"j1"}]}' });
    expect(result.jobs).toBeUndefined();
    expect(result.status).toBe('running');
  });
});
