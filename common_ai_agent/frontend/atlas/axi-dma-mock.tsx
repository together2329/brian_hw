// axi-dma-mock.tsx - screenshot-test AXI DMA fetch interceptor.
// Loaded before data.jsx so test bypass state is installed before app boot.
// ── axi_dma mock pipeline state ─────────────────────────────────
// Intercept /api/pipeline/state and /api/orchestrator/workers for the
// axi_dma demo IP only when screenshot-test bypass is explicitly enabled.
// Live mode must always hit the backend, even for an IP named axi_dma.

// This file installs runtime window globals (ACTIVE_IP / ATLAS_USER_SESSION_ID /
// ACTIVE_SESSION) that are app-boot state owned by other files and are not (yet)
// declared on the ambient Window interface in types/atlas-window.d.ts. They are
// written via a local cast below to keep behavior identical without editing the
// shared .d.ts.
type AxiDmaTestWindow = Window & {
  ACTIVE_IP?: string;
  ATLAS_USER_SESSION_ID?: string;
  ACTIVE_SESSION?: string;
};

(function installAxiDmaMock() {
  'use strict';
  const AXI_DMA_PIPELINE_STATE = {
    ip: 'axi_dma',
    stages: {
      ssot:        { state: 'passed',  iter: 1,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/ssot/axi_dma.ssot.yaml'] },
      'fl-model':  { state: 'passed',  iter: 2,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/fl-model/fl_model.json'] },
      'cl-model':  { state: 'passed',  iter: 1,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/cl-model/cl_model.json'] },
      equivalence: { state: 'passed',  iter: 1,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/equivalence/equiv_report.json'] },
      rtl:         { state: 'running', iter: 14, model: 'gpt-5-codex',    progress: 0.6, live_tail: 'wrote axi_dma_ch_arb.sv (164 lines) — running lint pre-check', evidence_paths: [] },
      sim:         { state: 'running', iter: 3,  model: 'gpt-5.3-codex',  progress: 0.3, live_tail: 'sim driver scoreboarding test vector 84/256', evidence_paths: [] },
      lint:        { state: 'ready',   iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [] },
      tb:          { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for rtl' },
      'sim-debug': { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for sim' },
      coverage:    { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for sim' },
      'goal-audit':{ state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for coverage' },
      syn:         { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for rtl' },
      sta:         { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for syn' },
      pnr:         { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for sta' },
      'sta-post':  { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for pnr' },
    },
    orchestrator: { enabled: true, mode: 'multi-worker', model: 'gpt-4o', pending_handoffs: 0, claimed_handoffs: 0 },
    run_mode: 'engineering',
    exec_mode: 'orchestrator',
  };

  const AXI_DMA_WORKERS_STATE = {
    orchestrator: { enabled: true, mode: 'multi-worker', model: 'gpt-4o', active_target: 'rtl-gen', last_kind: 'http_send' },
    workers: [
      { workflow: 'ssot-gen',      running_count: 0, status: 'ok' },
      { workflow: 'fl-model-gen',  running_count: 0, status: 'ok' },
      { workflow: 'rtl-gen',       running_count: 1, status: 'ok' },
      { workflow: 'sim',           running_count: 1, status: 'ok' },
      { workflow: 'lint',          running_count: 0, status: 'ok' },
      { workflow: 'tb-gen',        running_count: 0, status: 'ok' },
      { workflow: 'coverage',      running_count: 0, status: 'ok' },
      { workflow: 'syn',           running_count: 0, status: 'ok' },
      { workflow: 'sta',           running_count: 0, status: 'ok' },
      { workflow: 'pnr',           running_count: 0, status: 'ok' },
      { workflow: 'sta-post',      running_count: 0, status: 'ok' },
    ],
  };

  function jsonResp(body: unknown): Response {
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  }

  // Screenshot-test bypass: when localStorage.atlasTestBypass === '1' (set by
  // frontend/atlas/_test_axi_dma.html), the interceptor also fakes
  // /api/auth/status and /api/users/me so the screenshot pipeline can render
  // the Pipeline screen without going through the real login UI. Real users
  // never set this flag — the gate is intentional, not a security hole.
  const isTestBypass = (() => {
    try {
      const liveBackend = new URLSearchParams(location.search || '').get('backend') === 'live';
      return !liveBackend && localStorage.getItem('atlasTestBypass') === '1';
    }
    catch (_) { return false; }
  })();
  if (isTestBypass && typeof window !== 'undefined') {
    // Pre-seed the active IP so pipelineInitialIp picks axi_dma instead of
    // falling back to the default IP. Runs before React mounts AtlasPipeline.
    (window as AxiDmaTestWindow).ACTIVE_IP = 'axi_dma';
    (window as AxiDmaTestWindow).ATLAS_USER_SESSION_ID = 'brian';
    (window as AxiDmaTestWindow).ACTIVE_SESSION = 'brian/axi_dma/orchestrator';
  }
  const TEST_USER = { username: 'brian', display_name: 'brian (test)', is_authenticated: true };
  const TEST_ME = { user: TEST_USER };  // app.jsx unwraps j.user
  const TEST_AUTH_STATUS = { authenticated: true, username: 'brian', user: TEST_USER, recovery_enabled: false, email_required: false };

  // In test bypass, hide the boot-progress dialog and force dark theme so
  // screenshots match the Pipeline Image mockup. WebSocket inevitably fails
  // against the static server, and app.jsx defaults theme to 'light' with no
  // localStorage persistence — so we keep-alive 'dark' via setInterval.
  if (isTestBypass && typeof document !== 'undefined') {
    const installHideStyle = () => {
      const s = document.createElement('style');
      s.setAttribute('data-test-bypass', '1');
      s.textContent = '[role="status"][aria-live="polite"]{display:none!important;}';
      if (document.head) document.head.appendChild(s);
    };
    if (document.head) installHideStyle();
    else document.addEventListener('DOMContentLoaded', installHideStyle, { once: true });
    // Override <html> setAttribute and a MutationObserver to force
    // data-theme="dark" on EVERY element that ever gets a data-theme
    // attribute (React sets it via JSX prop on the .app inner div, which
    // bypasses html.setAttribute monkey-patch).
    try {
      const html = document.documentElement;
      const origSetAttr = html.setAttribute.bind(html);
      html.setAttribute = function(name: string, value: string) {
        if (name === 'data-theme') return origSetAttr(name, 'dark');
        return origSetAttr(name, value);
      };
      origSetAttr('data-theme', 'dark');
    } catch (_) {}
    // After mount, drive the IP-picker <select> to axi_dma so the pipeline
    // state mock fires with ip=axi_dma instead of the default. Uses React's
    // native value setter + a bubbling change event so the React onChange
    // handler picks up the new value.
    const setAxiDma = () => {
      try {
        const select = document.querySelector('select.pipe-stage-rail-select') as HTMLSelectElement | null;
        if (!select) return false;
        if (select.value === 'axi_dma') return true;
        // Ensure the option exists in the dropdown
        let hasOpt = false;
        for (const opt of select.options) { if (opt.value === 'axi_dma') { hasOpt = true; break; } }
        if (!hasOpt) return false;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value')!.set!;
        setter.call(select, 'axi_dma');
        select.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
      } catch (_) { return false; }
    };
    const startClicker = () => {
      let ticks = 0;
      const id = setInterval(() => {
        if (setAxiDma() || ++ticks > 30) clearInterval(id);
      }, 200);
    };
    if (document.body) startClicker();
    else document.addEventListener('DOMContentLoaded', startClicker, { once: true });

    try {
      const enforceDark = (target: Element) => {
        if (target && target.getAttribute && target.getAttribute('data-theme') === 'light') {
          target.setAttribute('data-theme', 'dark');
        }
      };
      const mo = new MutationObserver((mutations) => {
        mutations.forEach((m) => {
          if (m.type === 'attributes' && m.attributeName === 'data-theme') {
            enforceDark(m.target as Element);
          }
          if (m.type === 'childList') {
            m.addedNodes.forEach((n) => {
              if (n && n.nodeType === 1) {
                const el = n as Element;
                enforceDark(el);
                if (el.querySelectorAll) {
                  el.querySelectorAll('[data-theme="light"]').forEach(enforceDark);
                }
              }
            });
          }
        });
      });
      const startObserving = () => {
        if (!document.body) return;
        mo.observe(document.body, { attributes: true, attributeFilter: ['data-theme'], subtree: true, childList: true });
        // Initial sweep
        document.querySelectorAll('[data-theme="light"]').forEach(enforceDark);
      };
      if (document.body) startObserving();
      else document.addEventListener('DOMContentLoaded', startObserving, { once: true });
    } catch (_) {}
  }

  const _origFetch = window.fetch.bind(window);
  window.fetch = function atlasAxiDmaMockFetch(input: RequestInfo | URL, init?: RequestInit) {
    let path = '';
    try {
      const url = typeof input === 'string' ? input : (input && (input as Request).url) || '';
      const parsed = new URL(url as string, location.href);
      path = parsed.pathname + parsed.search;
    } catch (_) {}
    if (isTestBypass) {
      if (/^\/api\/pipeline\/state/.test(path)) {
        const ipParam = (() => {
          try { return new URL(path, location.href).searchParams.get('ip') || ''; } catch (_) { return ''; }
        })();
        if (ipParam === 'axi_dma') {
          return Promise.resolve(jsonResp(AXI_DMA_PIPELINE_STATE));
        }
      }
      if (/^\/api\/orchestrator\/workers/.test(path)) {
        const ipParam = (() => {
          try { return new URL(path, location.href).searchParams.get('ip') || ''; } catch (_) { return ''; }
        })();
        if (ipParam === 'axi_dma') {
          return Promise.resolve(jsonResp(AXI_DMA_WORKERS_STATE));
        }
      }
      if (/^\/api\/auth\/status/.test(path)) {
        return Promise.resolve(jsonResp(TEST_AUTH_STATUS));
      }
      if (/^\/api\/users\/me/.test(path)) {
        return Promise.resolve(jsonResp(TEST_ME));
      }
      if (/^\/api\/ip\/list/.test(path)) {
        return Promise.resolve(jsonResp({
          items: [
            { ip: 'axi_dma', name: 'axi_dma', has_yaml: true, has_rtl: true, has_tb: true, has_sim: false },
            { ip: 'atcdmac100', name: 'atcdmac100', has_yaml: true, has_rtl: true, has_tb: true, has_sim: true },
            { ip: 'arm_m0_min', name: 'arm_m0_min', has_yaml: true, has_rtl: true, has_tb: true, has_sim: true },
          ],
        }));
      }
    }
    return _origFetch(input, init);
  };
})();

export {};
