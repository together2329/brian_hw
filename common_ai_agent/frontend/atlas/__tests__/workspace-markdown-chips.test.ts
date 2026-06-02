import { describe, expect, it } from 'vitest';

import {
  _chipKindFor,
  _normalizeDisplayedToolPaths,
} from '../workspace-markdown-chips';

describe('workspace markdown chips path display', () => {
  it('normalizes backslash paths in tool output text', () => {
    const text = [
      'root: C:\\repo',
      'cwd: C:\\repo\\common_ai_agent\\uart_core',
      'file: uart_core\\rtl\\top.sv',
      'same: uart_core/rtl/top.sv',
      'escape: \\n',
    ].join('\n');

    const normalized = _normalizeDisplayedToolPaths(text);

    expect(normalized).toContain('C:/repo');
    expect(normalized).toContain('C:/repo/common_ai_agent/uart_core');
    expect(normalized).toContain('uart_core/rtl/top.sv');
    expect(normalized).toContain('same: uart_core/rtl/top.sv');
    expect(normalized).toContain('escape: \\n');
    expect(normalized).not.toContain('uart_core\\rtl\\top.sv');
  });

  it('classifies backslash file paths as path chips', () => {
    expect(_chipKindFor('uart_core\\rtl\\top.sv')).toBe('path');
  });
});
