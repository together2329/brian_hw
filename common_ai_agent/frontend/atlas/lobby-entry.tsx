// lobby-entry.tsx — Vite ES-module entry for the ATLAS lobby page.
//
// Mirrors main.tsx's entry pattern: import the react-global shim FIRST so that
// window.React / window.ReactDOM are populated with the single bundled React
// instance BEFORE the lobby module runs, then import the lobby module as a
// side effect. lobby.tsx self-mounts onto #root via createRoot() at the end of
// the file (and registers window.LobbyPage for the transitional bridge), so —
// exactly like main.tsx — there is NO explicit createRoot() call here.

import "./_react-global";

import "./lobby";
