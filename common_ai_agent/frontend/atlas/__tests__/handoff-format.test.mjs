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

  it('surfaces an error result and leaves result null when obs has no signal', () => {
    const errObs = { text: '{"workflow":"sim","status":"error","result":{"error":"timeout after 600s"}}' };
    const { result } = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'sim' } }, errObs);
    expect(result.status).toBe('error');
    expect(result.error).toBe('timeout after 600s');

    const noResult = handoffFields({ tool: 'dispatch_workflow', argsRaw: { ip: 'x', workflow: 'sim' } }, { text: 'not json' });
    expect(noResult.result).toBeNull();
  });

  it('maps status to colors', () => {
    expect(handoffStatusColor('running')).toBe('#58a6ff');
    expect(handoffStatusColor('completed')).toBe('#3fb950');
    expect(handoffStatusColor('blocked')).toBe('#f85149');
    expect(handoffStatusColor('queued')).toBe('#8b949e');
  });
});
