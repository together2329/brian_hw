import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  _grepOutputRows,
  GrepOutputPre,
} from '../workspace-markdown-chips';

describe('workspace grep output display', () => {
  it('preserves source indentation from formatted grep_file rows', () => {
    const rows = _grepOutputRows([
      '=== Matches in rtl/top.sv ===',
      '  12:     if (enable) begin',
      '  13:         next_state = RUN;',
    ].join('\n'));

    expect(rows[1]).toMatchObject({
      kind: 'context',
      lineNumber: '12',
      code: '    if (enable) begin',
    });
    expect(rows[2]).toMatchObject({
      kind: 'context',
      lineNumber: '13',
      code: '        next_state = RUN;',
    });
  });

  it('does not strip the first source indent from raw system grep rows', () => {
    const rows = _grepOutputRows('rtl/top.sv:12:    if (enable) begin');

    expect(rows[0]).toMatchObject({
      kind: 'match',
      file: 'rtl/top.sv',
      lineNumber: '12',
      code: '    if (enable) begin',
    });
  });

  it('renders grep source text in a separate code cell from the gutter', () => {
    const view = render(
      <GrepOutputPre
        text={[
          '=== Matches in rtl/top.sv ===',
          '  12:     if (enable) begin',
        ].join('\n')}
      />,
    );

    const codeCells = Array.from(view.container.querySelectorAll('[data-grep-code="true"]'));
    expect(codeCells).toHaveLength(1);
    expect(codeCells[0]?.textContent).toBe('    if (enable) begin');
  });
});
