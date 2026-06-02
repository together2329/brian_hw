import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  _chipKindFor,
  _normalizeDisplayedToolPaths,
  _postProcessMarkdownNode,
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

describe('workspace markdown mermaid rendering', () => {
  beforeEach(() => {
    delete (window as any).__ATLAS_MERMAID_INITIALIZED;
  });

  it('renders mermaid code fences into sanitized svg blocks', async () => {
    const mermaid = {
      initialize: vi.fn(),
      render: vi.fn(async () => ({
        svg: '<svg xmlns="http://www.w3.org/2000/svg"><g></g><script>bad()</script></svg>',
      })),
    };
    const purify = {
      sanitize: vi.fn((html: string) => html.replace(/<script[\s\S]*?<\/script>/g, '')),
    };
    (window as any).mermaid = mermaid;
    (window as any).DOMPurify = purify;

    const host = document.createElement('div');
    host.innerHTML = '<pre><code class="language-mermaid">flowchart TD\nA-->B</code></pre>';

    _postProcessMarkdownNode(host);
    await Promise.resolve();
    await Promise.resolve();

    expect(mermaid.initialize).toHaveBeenCalledWith(expect.objectContaining({ startOnLoad: false }));
    expect(mermaid.render).toHaveBeenCalledWith(expect.stringMatching(/^atlas-mermaid-md-/), 'flowchart TD\nA-->B');
    expect(purify.sanitize).toHaveBeenCalled();
    expect(host.querySelector('.atlas-mermaid-block')).not.toBeNull();
    expect(host.querySelector('pre')).toBeNull();
    expect(host.querySelector('script')).toBeNull();
  });
});
