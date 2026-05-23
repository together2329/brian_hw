import { describe, it, expect } from 'vitest';
import {
  feedEntryFromChatMessage,
  toolEntryFromDisplayLine,
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

  it('renders DB-restored raw tool rows as real tool-card action entries', () => {
    const entry = feedEntryFromChatMessage({
      id: 'm2',
      created_at: 1716400001,
      payload: {
        role: 'tool',
        display_name: 'read_pipeline_state',
        content: '⏺ read_pipeline_state(ip="new_axi", include_jobs=true)',
      },
    });

    expect(entry).toEqual({
      kind: 'action',
      text: '⏺ read_pipeline_state(ip="new_axi", include_jobs=true)',
      tool: 'read_pipeline_state',
      args: '(ip="new_axi", include_jobs=true)',
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
        display_name: 'read_pipeline_state',
        content: '└─ {"ok":true}',
      },
    })).toEqual({
      kind: 'obs',
      text: '└─ {"ok":true}',
      tool: 'read_pipeline_state',
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
});
