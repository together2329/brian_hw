// Deep integration test rig for ATLAS frontend jsx files.
// Simulates the script-tag load order from index.html, runs each through
// the bundled babel transform, then checks that all expected globals exist.
const vm = require("vm");
const fs = require("fs");
const path = require("path");

const noop = () => {};
const React = {
  createElement: (...a) => ({_t:a[0]}),
  cloneElement: (...a) => ({_t:a[0]}),
  Fragment: "F", StrictMode: "Strict", Suspense: "Suspense",
  useState: (v) => [typeof v === "function" ? v() : v, () => {}],
  useEffect: noop, useLayoutEffect: noop,
  useCallback: (f) => f, useMemo: (f) => f(),
  useRef: (v) => ({current: v}),
  useReducer: (r, i) => [typeof i === "function" ? i() : i, () => {}],
  useContext: () => undefined,
  createContext: (v) => ({Provider:"P", Consumer:"C", _curr:v}),
  useImperativeHandle: noop, useDebugValue: noop, useId: () => "id",
  useTransition: () => [false, noop],
  useDeferredValue: (v) => v,
  useSyncExternalStore: (sub, get) => get(),
  memo: (c) => c, forwardRef: (f) => f, lazy: (f) => f,
  startTransition: noop, version: "18.0.0",
};

function mkEl() {
  return {
    appendChild: noop, removeChild: noop, insertBefore: noop, replaceChild: noop,
    setAttribute: noop, getAttribute: () => null, removeAttribute: noop, style: {},
    addEventListener: noop, removeEventListener: noop, dispatchEvent: noop,
    classList: {add: noop, remove: noop, toggle: noop, contains: () => false},
    querySelector: () => null, querySelectorAll: () => [],
    getBoundingClientRect: () => ({top:0,left:0,right:0,bottom:0,width:0,height:0}),
    innerHTML: "", textContent: "", value: "", focus: noop, blur: noop,
    scrollIntoView: noop, children: [], childNodes: [],
    parentNode: null, firstChild: null, lastChild: null,
    contains: () => false, cloneNode: () => mkEl(),
    select: noop, setSelectionRange: noop,
  };
}

const sb = {};
sb.self = sb; sb.window = sb; sb.global = sb; sb.globalThis = sb;
sb.navigator = {userAgent: "node", clipboard: undefined};
sb.React = React;
sb.ReactDOM = {createRoot: () => ({render: noop, unmount: noop}), render: noop, flushSync: (f) => f()};
sb.console = console;
sb.setTimeout = setTimeout; sb.clearTimeout = clearTimeout;
sb.setInterval = setInterval; sb.clearInterval = clearInterval;
sb.queueMicrotask = queueMicrotask;
sb.document = Object.assign(mkEl(), {
  createElement: () => mkEl(), createElementNS: () => mkEl(),
  createTextNode: () => mkEl(), createDocumentFragment: () => mkEl(),
  createRange: () => ({selectNodeContents: noop, collapse: noop, getBoundingClientRect: () => ({})}),
  body: mkEl(), head: mkEl(), documentElement: mkEl(),
  addEventListener: noop, removeEventListener: noop, dispatchEvent: noop,
  getElementById: () => mkEl(), getElementsByClassName: () => [], getElementsByTagName: () => [],
  execCommand: () => true, hasFocus: () => false, activeElement: mkEl(),
  visibilityState: "visible", hidden: false, title: "", readyState: "complete",
});
sb.requestIdleCallback = (f) => setTimeout(f, 0); sb.cancelIdleCallback = clearTimeout;
sb.requestAnimationFrame = (f) => setTimeout(f, 0); sb.cancelAnimationFrame = clearTimeout;
sb.fetch = () => Promise.resolve({
  ok: true, status: 200, json: async () => ({}), text: async () => "",
  arrayBuffer: async () => new ArrayBuffer(0), blob: async () => ({}),
});
sb.URL = function URL(u, base) { this.href = u; this.pathname = ""; this.searchParams = new Map(); };
sb.URL.createObjectURL = () => "blob:fake";
sb.URL.revokeObjectURL = noop;
sb.URLSearchParams = function(s) { this.get = () => null; this.set = noop; this.has = () => false; this.toString = () => ""; };
sb.atob = (s) => Buffer.from(s, "base64").toString("binary");
sb.btoa = (s) => Buffer.from(s, "binary").toString("base64");
sb.matchMedia = () => ({matches: false, addEventListener: noop, removeEventListener: noop, addListener: noop, removeListener: noop});
sb.localStorage = {getItem: () => null, setItem: noop, removeItem: noop, clear: noop, key: () => null, length: 0};
sb.sessionStorage = {getItem: () => null, setItem: noop, removeItem: noop, clear: noop, key: () => null, length: 0};
sb.location = {href: "http://t/", origin: "http://t", pathname: "/", search: "", hash: "", host: "t", hostname: "t", protocol: "http:", port: "", reload: noop, assign: noop, replace: noop};
sb.history = {pushState: noop, replaceState: noop, back: noop, forward: noop, go: noop, length: 0, state: null};
sb.crypto = {randomUUID: () => "a".repeat(36), getRandomValues: (a) => a, subtle: {}};
sb.performance = {now: () => Date.now(), mark: noop, measure: noop, clearMarks: noop, clearMeasures: noop, getEntriesByType: () => [], getEntriesByName: () => []};
sb.WebSocket = function() {}; sb.EventSource = function() {};
sb.IntersectionObserver = function() { this.observe = noop; this.unobserve = noop; this.disconnect = noop; };
sb.ResizeObserver = function() { this.observe = noop; this.unobserve = noop; this.disconnect = noop; };
sb.MutationObserver = function() { this.observe = noop; this.disconnect = noop; this.takeRecords = () => []; };
sb.Event = function(t, o) { this.type = t; Object.assign(this, o || {}); };
sb.CustomEvent = function(t, o) { this.type = t; this.detail = (o && o.detail) || null; Object.assign(this, o || {}); };
sb.MessageChannel = function() { this.port1 = {postMessage: noop, onmessage: null, addEventListener: noop, removeEventListener: noop, start: noop, close: noop}; this.port2 = this.port1; };
sb.alert = noop; sb.confirm = () => false; sb.prompt = () => null;
sb.HTMLElement = function() {};
sb.Element = function() {};
sb.Node = function() {};
sb.getComputedStyle = () => ({getPropertyValue: () => "", fontSize: "16px"});

vm.createContext(sb);
const repoRoot = process.argv[2] || ".";
vm.runInContext(fs.readFileSync(path.join(repoRoot, "frontend/atlas/vendor/babel.min.js"), "utf8"), sb);

const files = [
  ["axi-dma-mock.jsx", "frontend/atlas/axi-dma-mock.jsx"],
  ["shared.jsx", "frontend/atlas/shared.jsx"],
  ["ui-utils.jsx", "frontend/atlas/ui-utils.jsx"],
  ["preview-pane.jsx", "frontend/atlas/preview-pane.jsx"],
  ["block-diagram.jsx", "frontend/atlas/block-diagram.jsx"],
  ["ssot-digest.jsx", "frontend/atlas/ssot-digest.jsx"],
  ["ssot-digest-content.jsx", "frontend/atlas/ssot-digest-content.jsx"],
  ["ssot-review.jsx", "frontend/atlas/ssot-review.jsx"],
  ["ssot-qa-board.jsx", "frontend/atlas/ssot-qa-board.jsx"],
  ["agent-status-panel.jsx", "frontend/atlas/agent-status-panel.jsx"],
  ["workspace-panels.jsx", "frontend/atlas/workspace-panels.jsx"],
  ["progress-todo-panels.jsx", "frontend/atlas/progress-todo-panels.jsx"],
  ["workspace.jsx", "frontend/atlas/workspace.jsx"],
];
const failed = [];
for (const [n, p] of files) {
  try {
    const out = sb.Babel.transform(fs.readFileSync(path.join(repoRoot, p), "utf8"), {presets: ["react"]}).code;
    vm.runInContext(out, sb);
    console.log(`  ${n}: loaded`);
  } catch (e) {
    console.log(`  ${n}: FAIL — ${String(e.message).split("\n")[0]}`);
    failed.push(n);
  }
}

const expected = [
  // Phase 13d components + 12 deps
  "PreviewPane", "FoldablePane", "DeferredMarkdownPreview",
  "_buildFoldTree", "_copyToClipboard", "_escHtml", "_highlightYamlLine",
  "_markdownHtml", "_normalizeMarkdownImageSrc", "_postProcessMarkdownNode",
  "atlasFileTreeMetaForPath", "atlasFormatBytes", "atlasImageMimeForExt",
  "scheduleAtlasPreviewWork", "useAtlasAsyncResource",
  // Phase 13c components + sample of the 57 deps
  "DigestCard", "BlockDiagram", "SsotDigestContent", "SsotReviewPane",
  "AtlasStatusBadge", "DigestEmpty", "DigestKV", "DigestList", "FeatureCard",
  "FsmTransitionDiagram", "GatesPanel", "ModuleTree", "PipelineTraceDiagram",
  "RegisterBitFieldView", "SsotCommandPalette", "SubmoduleCell",
  "_formatWidth", "_ifaceColor", "_ifaceKind", "blockField", "blockListValues",
  "compactDigestItems", "extractFeatures", "extractFsms", "extractRegisters",
  "extractScenarios", "fieldFromText", "listBlocksFromSection",
  "sectionByKey", "sectionFact", "ssotTitleFor", "ssotStatusColor",
  "chooseSsotFile", "splitSsotSections", "ssotPathOf",
  // Phase 13f component + 4 newly-exposed deps (AtlasStatusBadge already counted above)
  "SsotQaBoard",
  "AskUserQuestionBlock", "atlasStatusMeta", "normalizeUiSession", "ssotIpFromSession",
  // Phase 13g — 6 panel components + 8 newly-exposed deps (the other 5
  // panel deps — AskUserQuestionBlock/AtlasStatusBadge/atlasStatusMeta/
  // normalizeUiSession — are already counted above from earlier phases)
  "AskUserPrompt", "ProgressPanel", "TodoPanel", "OrchestratorChatPanel", "GitPanel", "AgentStatusPanel",
  "TodoGraph", "_limitAtlasLines", "_statusGlyph", "atlasUiExecMode",
  "healthMatchesCurrentUser", "uiEffectiveHealthSession",
  "uiHealthCountersMatchBrowserRoute", "uiSessionRoute", "workspaceFetchWorkerSnapshot",
];
console.log("\nwindow registration:");
let ok = 0;
for (const k of expected) {
  const t = typeof sb[k];
  if (t === "function") ok++;
  console.log(`  window.${k}: ${t}`);
}
console.log(`\n${ok}/${expected.length} window globals present, ${failed.length} files failed`);

// ── Render-time forward-ref check: call helpers through window to verify
//    they reach the real workspace.jsx implementations after both files loaded.
console.log("\nforward-ref smoke:");
try {
  console.log(`  atlasFormatBytes(1536) → "${sb.atlasFormatBytes(1536)}"`);
  console.log(`  atlasFileTreeMetaForPath("foo.md") → ${JSON.stringify(sb.atlasFileTreeMetaForPath("foo.md")).slice(0,90)}`);
  console.log(`  atlasImageMimeForExt("png") → "${sb.atlasImageMimeForExt("png")}"`);
  console.log(`  _escHtml("<b>x</b>") → "${sb._escHtml("<b>x</b>")}"`);
} catch (e) {
  console.log(`  FAIL: ${String(e.message).split("\n")[0]}`);
  process.exit(1);
}
process.exit(failed.length === 0 && ok === expected.length ? 0 : 1);
