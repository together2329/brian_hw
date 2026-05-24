import React from 'react';
import { render } from '@testing-library/react';
import { beforeAll, describe, expect, it } from 'vitest';

describe('debug ToolCard rendering', () => {
  beforeAll(async () => {
    globalThis.React = React;
    await import('../debug-shared.jsx?tool-card-object-test');
  });

  it('renders object args/results as text instead of React children', () => {
    let view;
    expect(() => {
      view = render(React.createElement(window.ToolCard, {
        name: 'probe_tool',
        args: { static: true, internal: { source: 'worker' } },
        result: { static: 'ok', internal: ['trace', 'obs'] },
        status: 'done',
      }));
    }).not.toThrow();

    expect(view.container.textContent).toContain('probe_tool');
    expect(view.container.textContent).toContain('{"static":true');
    expect(view.container.textContent).toContain('"static": "ok"');
    expect(view.container.textContent).toContain('"internal": [');
  });
});
