import { describe, it, expect } from 'vitest';
import {
  cleanTerminalControlText,
  compactThoughtText,
  coalesceFeedEntries,
  feedEntryFromChatMessage,
  feedEntryFromWorkerLogEntry,
  isThinkingPlaceholderText,
  toolEntryFromDisplayLine,
  visibleThoughtLines,
  workerLocalTodosFromFeed,
} from '../lib/orchestrator_chat_logic.mjs';

describe('orchestrator chat poll mapping', () => {
  it('renders assistant rows as agent feed entries', () => {
    const entry = feedEntryFromChatMessage({
      id: 'm1',
      created_at: 1716400000,
      payload: { role: 'assistant', content: '작업을 시작했어요' },
    });

    expect(entry).toEqual({
      kind: 'agent',
      text: '작업을 시작했어요',
      createdAt: 1716400000000,
    });
  });

  it('streams assistant delta rows into one agent feed entry', () => {
    const first = feedEntryFromChatMessage({
      id: 'd1',
      created_at: 1716400000,
      payload: { role: 'assistant_delta', content: 'Hello ', stream_id: 's1' },
    });
    const second = feedEntryFromChatMessage({
      id: 'd2',
      created_at: 1716400001,
      payload: { role: 'assistant_delta', content: 'world', stream_id: 's1' },
    });

    expect(first).toMatchObject({
      kind: 'agent_delta',
      text: 'Hello ',
      streamId: 's1',
    });

    const entries = coalesceFeedEntries([], [first, second]);
    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      kind: 'agent',
      text: 'Hello world',
      streamId: 's1',
    });
  });

  it('renders DB-restored raw tool rows as real tool-card action entries', () => {
    const entry = feedEntryFromChatMessage({
      id: 'm2',
      created_at: 1716400001,
      payload: {
        role: 'tool',
        display_name: 'read_artifact',
        content: '⏺ read_artifact(ip="new_axi", stage="ssot")',
      },
    });

    expect(entry).toEqual({
      kind: 'action',
      text: '⏺ read_artifact(ip="new_axi", stage="ssot")',
      tool: 'read_artifact',
      args: '(ip="new_axi", stage="ssot")',
      createdAt: 1716400001000,
    });
  });

  it('parses raw orchestrator call lines without translated status mapping', () => {
    expect(toolEntryFromDisplayLine('⏺ dispatch_workflow(workflow="pnr", ip="new_axi")')).toEqual({
      tool: 'dispatch_workflow',
      args: '(workflow="pnr", ip="new_axi")',
      text: '⏺ dispatch_workflow(workflow="pnr", ip="new_axi")',
    });
    expect(toolEntryFromDisplayLine('read_artifact(ip="new_axi", stage="sta")')).toEqual({
      tool: 'read_artifact',
      args: '(ip="new_axi", stage="sta")',
      text: 'read_artifact(ip="new_axi", stage="sta")',
    });
    expect(toolEntryFromDisplayLine('🔎 파이프라인 상태 조회: new_axi')).toBeNull();
  });

  it('renders DB-restored tool result rows as obs entries', () => {
    expect(feedEntryFromChatMessage({
      id: 'm4',
      created_at: 1716400002,
      payload: {
        role: 'tool_result',
        display_name: 'read_artifact',
        content: '└─ {"ok":true}',
      },
    })).toEqual({
      kind: 'obs',
      text: '└─ {"ok":true}',
      tool: 'read_artifact',
      createdAt: 1716400002000,
    });
  });

  it('renders DB-restored reasoning rows as thought entries', () => {
    expect(feedEntryFromChatMessage({
      id: 'm5',
      created_at: 1716400003,
      payload: { role: 'thought', content: 'checking state' },
    })).toEqual({
      kind: 'thought',
      text: 'checking state',
      createdAt: 1716400003000,
    });
  });

  it('ignores user rows because the submit path already mirrors them', () => {
    expect(feedEntryFromChatMessage({
      id: 'm3',
      payload: { role: 'user', content: 'Hi' },
    })).toBeNull();
  });

  it('maps worker log action/result rows as live raw feed entries', () => {
    const job = { job_id: 'j1', run_id: 'r1', workflow: 'sim_debug', status: 'running', worker: 'http://127.0.0.1:7000' };
    expect(feedEntryFromWorkerLogEntry({
      index: 6,
      type: 'action',
      role: 'assistant',
      content: 'slash:/sim-debug mctp_axi',
      timestamp: 1716400004,
    }, job)).toMatchObject({
      kind: 'action',
      text: 'slash:/sim-debug mctp_axi',
      tool: 'sim_debug',
      live: true,
      worker: { job_id: 'j1', workflow: 'sim_debug' },
    });
    expect(feedEntryFromWorkerLogEntry({
      index: 7,
      type: 'observation',
      role: 'tool',
      content: '[sim-debug] FL-vs-RTL compare',
      timestamp: 1716400005,
    }, job)).toMatchObject({
      kind: 'obs',
      text: '[sim-debug] FL-vs-RTL compare',
      tool: 'sim_debug',
      live: true,
    });
  });

  it('does not dump the huge worker context prompt into live chat', () => {
    expect(feedEntryFromWorkerLogEntry({
      type: 'task',
      role: 'user',
      content: '[ATLAS ARCHITECT WORKFLOW CONTEXT]\n- ip: mctp_axi',
    }, { workflow: 'rtl-gen' })).toBeNull();
  });

  it('maps IPC stdout log lines while the worker is still running', () => {
    expect(feedEntryFromWorkerLogEntry({
      index: 3,
      type: 'log',
      role: 'stdout',
      content: '[worker] reading mctp/yaml/mctp.ssot.yaml',
      timestamp: 1716400006,
    }, { job_id: 'j2', run_id: 'ipc-j2', workflow: 'ssot-gen', status: 'running' })).toMatchObject({
      kind: 'thought',
      text: '[worker] reading mctp/yaml/mctp.ssot.yaml',
      live: true,
      worker: { job_id: 'j2', workflow: 'ssot-gen' },
    });
  });

  it('hides runtime wait bookkeeping from the chat feed', () => {
    expect(feedEntryFromChatMessage({
      id: 'm-runtime-tool',
      payload: {
        role: 'tool',
        content: 'read_pipeline_state(ip="NEW_MCTP")',
      },
    })).toBeNull();

    expect(feedEntryFromChatMessage({
      id: 'm-runtime-result',
      payload: {
        role: 'tool_result',
        display_name: 'yield_run',
        content: '└ parked',
      },
    })).toBeNull();

    expect(feedEntryFromWorkerLogEntry({
      type: 'log',
      role: 'stdout',
      content: '⏳ streaming… 110s? idle (limit 1200s?)',
    }, { workflow: 'ssot-gen' })).toBeNull();
  });

  it('cleans terminal title control text without losing worker todo status', () => {
    expect(cleanTerminalControlText('\x1b]0;[1/6] ▶ in_progress | Check rtl\x07')).toBe('[1/6] ▶ in_progress | Check rtl');
    expect(cleanTerminalControlText('☒]0;[1/6] ▶ in_progress | Check rtl☒')).toBe('[1/6] ▶ in_progress | Check rtl');
  });

  it('derives worker-local todos from the live worker feed', () => {
    const todos = workerLocalTodosFromFeed([
      { kind: 'action', text: '▶ Todo (6 tasks)', worker: { workflow: 'ssot-gen' } },
      { kind: 'action', text: '▶ ssot-gen running' },
      { kind: 'obs', text: '☒]0;[1/6] ▶ in_progress | Check for rtl_blocked.json and existing SSOT state☒' },
      { kind: 'thought', text: 'THOUGHT (2)\nChecking existing artifacts' },
    ], 'ssot-gen');

    expect(todos).toEqual([expect.objectContaining({
      id: expect.stringContaining('worker-ssot-gen-'),
      state: 'in_progress',
      section: 'worker-local',
      title: 'Check for rtl_blocked.json and existing SSOT state',
    })]);
  });

  it('maps raw IPC stdout tool prefixes into action and observation entries', () => {
    const job = { job_id: 'j2', run_id: 'ipc-j2', workflow: 'ssot-gen', status: 'running' };

    expect(feedEntryFromWorkerLogEntry({
      index: 4,
      type: 'log',
      role: 'stdout',
      content: '⏺ Read(path="counter/yaml/counter.ssot.yaml")',
      timestamp: 1716400007,
    }, job)).toMatchObject({
      kind: 'action',
      tool: 'Read',
      args: '(path="counter/yaml/counter.ssot.yaml")',
      live: true,
      worker: { job_id: 'j2', workflow: 'ssot-gen' },
    });

    expect(feedEntryFromWorkerLogEntry({
      index: 5,
      type: 'log',
      role: 'stdout',
      content: '⎿  2 lines',
      timestamp: 1716400008,
    }, job)).toMatchObject({
      kind: 'obs',
      text: '⎿  2 lines',
      live: true,
      worker: { job_id: 'j2', workflow: 'ssot-gen' },
    });
  });

  it('coalesces adjacent live observation fragments from the same worker', () => {
    const worker = { job_id: 'j2', run_id: 'ipc-j2', workflow: 'ssot-gen' };
    const entries = coalesceFeedEntries([], [
      { kind: 'action', text: '⏺ Read(path="counter/yaml/counter.ssot.yaml")', tool: 'Read', live: true, worker },
      { kind: 'obs', text: '⎿  2 lines', tool: 'ssot-gen', live: true, worker },
      { kind: 'obs', text: '│ 1 top_module:', tool: 'ssot-gen', live: true, worker },
      { kind: 'obs', text: '│ 2   name: counter', tool: 'ssot-gen', live: true, worker },
    ]);

    expect(entries.map(e => e.kind)).toEqual(['action', 'obs']);
    expect(entries[1].text).toBe('⎿  2 lines\n│ 1 top_module:\n│ 2   name: counter');
  });

  it('keeps raw list continuation lines inside the observation card', () => {
    const job = { job_id: 'j-list', run_id: 'ipc-list', workflow: 'ssot-gen', status: 'running' };
    const entries = coalesceFeedEntries([], [
      feedEntryFromWorkerLogEntry({
        type: 'log',
        role: 'stdout',
        content: '⏺ List(path="/Users/brian/Desktop/Project/ROOT_IP/NEW_MCTP")',
      }, job),
      feedEntryFromWorkerLogEntry({
        type: 'log',
        role: 'stdout',
        content: '└ 14 entries',
      }, job),
      feedEntryFromWorkerLogEntry({
        type: 'log',
        role: 'stdout',
        content: '.git/',
      }, job),
      feedEntryFromWorkerLogEntry({
        type: 'log',
        role: 'stdout',
        content: 'rtl/',
      }, job),
      feedEntryFromWorkerLogEntry({
        type: 'log',
        role: 'stdout',
        content: '└ Total: 13 directories, 1 files',
      }, job),
    ]);

    expect(entries.map(e => e.kind)).toEqual(['action', 'obs']);
    expect(entries[1].text).toBe('└ 14 entries\n.git/\nrtl/\n└ Total: 13 directories, 1 files');
  });

  it('does not merge a real thought header into the previous observation card', () => {
    const worker = { job_id: 'j2', run_id: 'ipc-j2', workflow: 'ssot-gen' };
    const entries = coalesceFeedEntries([], [
      { kind: 'obs', text: '└ 14 entries', tool: 'ssot-gen', live: true, worker },
      { kind: 'thought', text: 'THOUGHT (2)\nLet me check yaml/', live: true, worker },
    ]);

    expect(entries.map(e => e.kind)).toEqual(['obs', 'thought']);
    expect(entries[1].text).toBe('THOUGHT (2)\nLet me check yaml/');
  });

  it('coalesces repeated live Thinking placeholders instead of stacking rows', () => {
    expect(isThinkingPlaceholderText('* Thinking...')).toBe(true);
    expect(isThinkingPlaceholderText('✣ Thinking…')).toBe(true);
    expect(isThinkingPlaceholderText('THOUGHT * Thinking...')).toBe(true);
    expect(isThinkingPlaceholderText('reading mctp/yaml/mctp.ssot.yaml')).toBe(false);
    expect(visibleThoughtLines('✣ Thinking…\n✦ Thinking…')).toEqual([]);

    const entries = coalesceFeedEntries([], [
      { kind: 'thought', text: '* Thinking...', live: true, createdAt: 1 },
      { kind: 'thought', text: '✣ Thinking…\n✦ Thinking…', live: true, createdAt: 2 },
      { kind: 'thought', text: 'reading mctp/yaml/mctp.ssot.yaml', live: true, createdAt: 3 },
      { kind: 'action', text: '▶ read_artifact stage="ssot"', tool: 'read_artifact', live: true, createdAt: 4 },
      { kind: 'thought', text: 'Answering RTL blockers\n✣ Thinking…\n✦ Thinking…', live: true, createdAt: 5 },
      { kind: 'obs', text: '{"ok":true}', tool: 'read_artifact', live: true, createdAt: 6 },
    ]);

    expect(entries.map(e => e.kind)).toEqual(['thought', 'action', 'thought', 'obs']);
    expect(entries[0].text).toBe('reading mctp/yaml/mctp.ssot.yaml');
    expect(entries[2].text).toBe('Answering RTL blockers');
  });

  it('caps coalesced thought logs so live worker chat stays responsive', () => {
    const longThought = Array.from({ length: 120 }, (_, i) => `line ${i + 1}`).join('\n');

    expect(compactThoughtText(longThought).split('\n')).toHaveLength(81);

    const entries = coalesceFeedEntries([{ kind: 'thought', text: longThought, live: true }], [
      { kind: 'thought', text: 'line 121', live: true },
    ]);

    expect(entries).toHaveLength(1);
    expect(entries[0].text).toContain('older thought lines hidden for speed');
    expect(entries[0].text).toContain('line 121');
    expect(entries[0].text).not.toContain('line 1\n');
  });
});
