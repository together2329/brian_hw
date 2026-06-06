import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { AskUserQuestionBlock } from '../workspace-feed-askuser';

describe('AskUserQuestionBlock', () => {
  it('highlights only the selected single-select answer even when keyboard focus is elsewhere', () => {
    const { getByText } = render(
      <AskUserQuestionBlock
        block={{ question: 'Pick one?' }}
        blockState={{
          opts: [
            { id: 'a', label: 'Focused answer', selected: false },
            { id: 'b', label: 'Selected answer', selected: true },
          ],
          custom: '',
        }}
        kind="single"
        isActive={true}
        selectedIndex={0}
        onEnsureActive={vi.fn()}
        onSelectIndex={vi.fn()}
        onToggleOption={vi.fn()}
        onCustom={vi.fn()}
      />,
    );

    const selectedLabel = getByText('Selected answer');
    const selectedRow = selectedLabel.parentElement?.parentElement;
    const focusedLabel = getByText('Focused answer');
    const focusedRow = focusedLabel.parentElement?.parentElement;

    expect(selectedRow?.style.background).toContain('var(--accent)');
    expect(selectedRow?.style.borderLeft).toContain('var(--accent)');
    expect(focusedRow?.style.background).toBe('transparent');
    expect(focusedRow?.style.borderLeft).toContain('transparent');
  });
});
