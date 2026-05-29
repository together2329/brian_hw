import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Vite config for the ATLAS frontend TypeScript migration.
// - `vite build` will bundle the migrated .tsx modules (no in-browser babel)
//   once the entry (app.tsx) is migrated. Until then this config powers the
//   vitest runtime smoke tests that prove each migrated .tsx imports + renders.
// - The Tauri shell will load `vite build`'s static output from outDir.
//
// resolve.extensions: CRITICAL during the .jsx→.tsx transition. Vite's default
// order lists .jsx BEFORE .tsx, so a bare `import '../foo'` would resolve to the
// stale legacy foo.jsx (window-global style, no ES exports) instead of the
// migrated foo.tsx. We put .tsx/.ts FIRST so migrated modules always win while
// both files coexist. (Removed once the .jsx are retired at the cutover.)
export default defineConfig({
  // @ts-expect-error vitest@1.6 bundles its own vite@5 whose Plugin type differs
  // from the top-level vite@7 that @vitejs/plugin-react targets (dual-version
  // type skew only — runtime is compatible; vitest loads this config fine).
  // Resolved by aligning vitest↔vite versions in a later toolchain pass.
  plugins: [react()],
  resolve: {
    extensions: ['.tsx', '.ts', '.jsx', '.js', '.json'],
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: '/Users/brian/Desktop/Project/brian_hw/common_ai_agent/frontend/atlas/index.vite.html',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['__tests__/**/*.test.{ts,tsx}'],
    setupFiles: ['./__tests__/setup.ts'],
  },
});
