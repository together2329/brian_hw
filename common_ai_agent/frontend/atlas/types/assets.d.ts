// Ambient declarations for non-code side-effect imports (e.g. React Flow's
// `import '@xyflow/react/dist/style.css'`). Vite handles these at build time;
// this keeps the TS server / tsc from flagging the bare import.
declare module '*.css';
