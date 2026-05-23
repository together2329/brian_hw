import { describe, it, expect } from 'vitest';
import { feedEntryFromChatMessage } from '../lib/orchestrator_chat_logic.mjs';

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

  it('renders tool rows as visible action feed entries', () => {
    const entry = feedEntryFromChatMessage({
      id: 'm2',
      created_at: 1716400001,
      payload: { role: 'tool', content: '🔎 파이프라인 상태 조회: new_axi' },
    });

    expect(entry).toEqual({
      kind: 'action',
      text: '▶ 🔎 파이프라인 상태 조회: new_axi',
      createdAt: 1716400001000,
    });
  });

  it('ignores user rows because the submit path already mirrors them', () => {
    expect(feedEntryFromChatMessage({
      id: 'm3',
      payload: { role: 'user', content: 'Hi' },
    })).toBeNull();
  });
});
