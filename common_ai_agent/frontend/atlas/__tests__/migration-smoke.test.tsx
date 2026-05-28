// Runtime smoke test: prove migrated .tsx modules IMPORT + RENDER through the
// real React toolchain (not just type-check). Explicit .tsx extensions because
// during .jsx/.tsx coexistence the resolver may pick the stale .jsx; at the
// Vite cutover the .jsx are deleted and bare imports resolve to .tsx naturally.
import { render, screen } from '@testing-library/react';
import { CopyBtn, copyToClipboard } from '../ui-utils.tsx';
import { Pill, Kbd } from '../shared.tsx';

describe('TS migration runtime smoke', () => {
  it('ui-utils: CopyBtn renders its label', () => {
    render(<CopyBtn label="copy me" />);
    expect(screen.getByRole('button')).toHaveTextContent('copy me');
  });
  it('ui-utils: copyToClipboard is a callable export', () => {
    expect(typeof copyToClipboard).toBe('function');
    expect(() => copyToClipboard('x')).not.toThrow();
  });
  it('ui-utils: window bridge ran on import (legacy .jsx consumers)', () => {
    expect(typeof (window as unknown as { CopyBtn: unknown }).CopyBtn).toBe('function');
  });
  it('shared: Pill + Kbd render', () => {
    render(<Pill>hello</Pill>);
    expect(screen.getByText('hello')).toBeInTheDocument();
    render(<Kbd>esc</Kbd>);
    expect(screen.getByText('esc')).toBeInTheDocument();
  });
});
