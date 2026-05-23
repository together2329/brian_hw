// Visual + assertion check for the orchestrator HandoffCard (dispatch_workflow
// / write_handoff) labeled-card rendering. Free (no LLM): drives the real
// hydration path by firing the app's own `atlas-conversation-loaded` event
// with a realistic conversation, then asserts the rendered DOM + screenshots.
import { launch, login, gotoWorkspace, shoot, assert, failures, results, log } from './lib.mjs';

const ja = (o) => JSON.stringify(o);

// Authentic payload shapes (schema: prompts.py dispatch_workflow/write_handoff,
// result summary: orchestrator/tools.py).
const messages = [
  { role: 'assistant', content: '', tool_calls: [{ function: { name: 'dispatch_workflow', arguments: ja({
    ip: 'uart_tx', workflow: 'ssot-gen', prompt: 'Generate the SSOT for the UART TX datapath', reason: 'kickoff', schedule: 'auto' }) } }] },
  { role: 'tool', name: 'dispatch_workflow', content: ja({
    workflow: 'ssot-gen', status: 'running', worker: 'admin/uart_tx/ssot-gen', job_id: 'j_8f2a', model: 'deepseek-v4-pro' }) },

  { role: 'assistant', content: '', tool_calls: [{ function: { name: 'dispatch_workflow', arguments: ja({
    ip: 'uart_tx', stages: ['lint', 'tb', 'syn'], schedule: 'dag', prompt: 'Verify RTL in parallel' }) } }] },
  { role: 'tool', name: 'dispatch_workflow', content: ja({ jobs: [
    { workflow: 'lint', status: 'running', worker: 'admin/uart_tx/lint', job_id: 'j1', model: 'deepseek-v4-pro' },
    { workflow: 'tb', status: 'running' }, { workflow: 'syn', status: 'queued' } ] }) },

  { role: 'assistant', content: '', tool_calls: [{ function: { name: 'write_handoff', arguments: ja({
    ip: 'uart_tx', workflow: 'rtl-gen', payload: { task: 'Implement the RTL from the approved SSOT' }, reason: 'fl/cl models passed' }) } }] },

  { role: 'assistant', content: '', tool_calls: [{ function: { name: 'dispatch_workflow', arguments: ja({
    ip: 'uart_tx', workflow: 'sim', reason: 'run cocotb' }) } }] },
  { role: 'tool', name: 'dispatch_workflow', content: ja({ workflow: 'sim', status: 'error', result: { error: 'sim timed out after 600s' } }) },
];

const main = async () => {
  const { browser, page } = await launch();
  try {
    await login(page);
    await gotoWorkspace(page, { ip: 'uart_tx', workflow: 'orchestrator' });

    // The chat feed (where ToolCard/HandoffCard render) lives under the center
    // CHAT tab; orchestrator workflow lands on the worker-status tab. Click the
    // first visible center tab whose text is exactly "CHAT".
    await page.evaluate(() => {
      const el = [...document.querySelectorAll('button,span,div,[role="tab"]')]
        .find(x => (x.textContent || '').trim().toUpperCase() === 'CHAT' && x.offsetParent !== null);
      if (el) el.click();
    });
    await page.waitForTimeout(1200);

    // Fire the real hydration event the app listens on. No session => the
    // guard in onConvLoaded is skipped, so it hydrates our feed verbatim.
    const inject = () => page.evaluate((msgs) => {
      window.dispatchEvent(new CustomEvent('atlas-conversation-loaded', { detail: { messages: msgs } }));
    }, messages);
    await inject();
    await page.waitForTimeout(1200);
    // Re-fire once in case an app-driven empty snapshot raced us.
    if (await page.locator('.handoff-card').count() === 0) { await inject(); await page.waitForTimeout(1200); }

    const cards = page.locator('.handoff-card');
    const n = await cards.count();
    assert(n >= 4, `>=4 handoff cards rendered (got ${n})`);

    const allText = (await cards.allInnerTexts()).join('\n');
    log('--- rendered handoff text ---\n' + allText + '\n-----------------------------');

    // No raw JSON leaking
    assert(!/\{"|":"/.test(allText), 'no raw JSON in rendered cards');
    // Labels present
    for (const label of ['task', 'reason', 'schedule', 'worker', 'job']) {
      assert(allText.includes(label), `label "${label}" present`);
    }
    // Field values
    assert(allText.includes('Generate the SSOT for the UART TX datapath'), 'single-dispatch task text shown');
    assert(allText.includes('ssot-gen') && allText.includes('uart_tx'), 'workflow + ip shown');
    assert(allText.includes('lint, tb, syn'), 'fan-out stages joined');
    assert(allText.includes('admin/uart_tx/ssot-gen'), 'worker shown');
    assert(/j_8f2a.*deepseek-v4-pro/s.test(allText), 'job · model shown');
    assert(/Handoff/.test(allText), 'write_handoff verb shown');
    assert(/error|timed out/i.test(allText), 'error result surfaced');

    // status dot color check (running=blue, error=red)
    const dotColors = await page.locator('.handoff-dot').evaluateAll(els =>
      els.map(e => getComputedStyle(e).color));
    log('dot colors:', ja(dotColors));
    assert(dotColors.some(c => /(88|85|86),\s*166|rgb\(88/.test(c) || c.includes('88, 166, 255')), 'has a blue (running) dot');

    await page.evaluate(() => { const f = document.querySelector('.feed, .chat-feed, [class*="feed"]'); if (f) f.scrollTop = 0; });
    await shoot(page, 'handoff_card_render.png');
  } finally {
    await browser.close();
  }
  log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
  process.exit(failures().length ? 1 : 0);
};
main().catch(e => { log('FATAL', e); process.exit(2); });
