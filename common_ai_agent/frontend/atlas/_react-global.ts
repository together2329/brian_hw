// _react-global.ts
//
// Exposes the BUNDLED React / ReactDOM on `window` BEFORE the app module
// self-mounts. main.tsx imports this FIRST so that app.tsx (which calls
// window.ReactDOM.createRoot) uses the SAME single React instance as every
// bundled component. Without this, the dynamically self-mounting app would
// otherwise pick up a second copy of React, producing the dual-instance
// "Invalid hook call" runtime error.
//
// This mirrors the legacy in-browser globals that the
// <script src="vendor/react.development.js"> / react-dom chain used to set,
// but sourced from the bundled npm packages instead.
import React from "react";
import * as ReactDOMClient from "react-dom/client";
import * as ReactDOM from "react-dom";

const w = window as any;
w.React = React;
// Merge the classic ReactDOM namespace with the react-dom/client API
// (createRoot, hydrateRoot) so window.ReactDOM.createRoot works in app.tsx.
w.ReactDOM = Object.assign({}, ReactDOM, ReactDOMClient);
