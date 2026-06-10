import '@testing-library/jest-dom';

// ── React Flow (@xyflow/react) browser APIs jsdom lacks ──
// Without these, mounting <ReactFlow> throws. Added guarded (only if absent) so
// they don't disturb other suites.
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

if (typeof globalThis.DOMMatrixReadOnly === 'undefined') {
  globalThis.DOMMatrixReadOnly = class DOMMatrixReadOnly {
    m22 = 1;
    constructor(transform) {
      if (typeof transform === 'string') {
        const scale = transform.match(/scale\(([^)]+)\)/);
        if (scale) this.m22 = parseFloat(scale[1]) || 1;
      }
    }
  };
}

if (globalThis.SVGElement && typeof globalThis.SVGElement.prototype.getBBox !== 'function') {
  globalThis.SVGElement.prototype.getBBox = () => ({ x: 0, y: 0, width: 0, height: 0 });
}
