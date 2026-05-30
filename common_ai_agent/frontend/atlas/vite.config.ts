import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Vite config for the ATLAS frontend TypeScript migration.
// - `vite build` will bundle the migrated .tsx modules (no in-browser babel)
//   once the entry (app.tsx) is migrated. Until then this config powers the
//   vitest runtime smoke tests that prove each migrated .tsx imports + renders.
// - The Tauri shell will load `vite build`'s static output from outDir.
//
// resolve.extensions: the legacy .jsx modules are retired (0 .jsx remain), so
// only .tsx/.ts/.js/.json are resolved.
export default defineConfig({
  // @ts-expect-error vitest@1.6 bundles its own vite@5 whose Plugin type differs
  // from the top-level vite@7 that @vitejs/plugin-react targets (dual-version
  // type skew only — runtime is compatible; vitest loads this config fine).
  // Resolved by aligning vitest↔vite versions in a later toolchain pass.
  plugins: [react()],
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.json'],
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      // Relative to Vite root (the config dir, frontend/atlas — where the build
      // runs). PORTABLE: no machine-absolute paths, no node-types dependency.
      input: {
        index: 'index.vite.html',
        lobby: 'lobby.vite.html',
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['__tests__/**/*.test.{ts,tsx}'],
    setupFiles: ['./__tests__/setup.ts'],
  },
});
