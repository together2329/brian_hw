// Visual + assertion check for readable orchestrator tool-CALL rendering
// (read_pipeline_state summary + yield_run/wait_job/read_artifact/classify_failure
// compact args). Free (no LLM): fires the app's own atlas-conversation-loaded
// event with messages whose tool_call `arguments` are the SAME `key=val` strings
// the faux-stream persists (format_tool_call), so the real ToolCard path runs.
import { launch, login, gotoWorkspace, shoot, assert, failures, results, log } from './lib.mjs';

const ja = (o) => JSON.stringify(o);
// read_pipeline_state result, as record_tool_result persists it (└─ + compact json)
const rpsResult = '└─ ' + ja({
  ip: 'mctp_axi',
  passed: ['ssot', 'fl-model', 'rtl', 'lint', 'tb', 'syn', 'pnr'],
  failed: {
    coverage: 'mctp_axi/cov/coverage.json status=blocked',
    sim: 'mctp_axi/logs/stage_engine/sim.json status=fail [sim] FAIL',
    sta: 'mctp_axi/sta/out/wns.json clk setup WNS=-4.13 viol=5',
  },
  running: [],
});

// tool_call `arguments` passed as the faux-stream `key=val` string (NOT a JSON
// object) so onConvLoaded forwards it verbatim → matches the real action.text.
const messages = [
  { role: 'assistant', tool_calls: [{ function: { name: 'read_pipeline_state', arguments: 'ip="mctp_axi", include_jobs=true' } }] },
  { role: 'tool', name: 'read_pipeline_state', content: rpsResult },

  { role: 'assistant', tool_calls: [{ function: { name: 'yield_run', arguments: 'wake_on={"job_ids":["cd16478088c1"],"user_message":true,"after_seconds":600}, reason="SSOT generation is running for mctp_axi"' } }] },
  { role: 'tool', name: 'yield_run', content: '└─ woken: user_message' },

  { role: 'assistant', tool_calls: [{ function: { name: 'wait_job', arguments: 'job_id="cd16478088c1"' } }] },
  { role: 'assistant', tool_calls: [{ function: { name: 'read_artifact', arguments: 'ip="mctp_axi", stage="rtl"' } }] },
  { role: 'assistant', tool_calls: [{ function: { name: 'classify_failure', arguments: 'stage="rtl", evidence={"open_required_todos":123}' } }] },
];

const { browser, page } = await launch();
try {
  await login(page);
  await gotoWorkspace(page, { ip: 'mctp_axi', workflow: 'orchestrator' });
  // chat feed lives under the CHAT tab (orchestrator lands on the worker-status tab)
  await page.evaluate(() => {
    const el = [...document.querySelectorAll('button,span,div,[role="tab"]')]
      .find(x => (x.textContent || '').trim().toUpperCase() === 'CHAT' && x.offsetParent !== null);
    if (el) el.click();
  });
  await page.waitForTimeout(1000);

  const inject = () => page.evaluate((msgs) => {
    window.dispatchEvent(new CustomEvent('atlas-conversation-loaded', { detail: { messages: msgs } }));
  }, messages);
  await inject();
  await page.waitForTimeout(1200);
  if (await page.locator('.tool-card').count() === 0) { await inject(); await page.waitForTimeout(1200); }

  const cards = page.locator('.tool-card');
  const n = await cards.count();
  assert(n >= 5, `>=5 tool cards rendered (got ${n})`);
  const txt = (await cards.allInnerTexts()).join('\n');
  log('--- rendered tool-card text ---\n' + txt + '\n-------------------------------');

  // read_pipeline_state: compact summary, NOT raw JSON (collapsed by default)
  assert(/✓/.test(txt) && /ssot/.test(txt), 'read_pipeline_state shows ✓ passed summary');
  assert(/✗/.test(txt) && /coverage\(blocked\)/.test(txt), 'failed stage with reason shown (coverage blocked)');
  assert(/WNS -4\.13\/5/.test(txt), 'STA WNS/viol compacted');
  assert(!/\{"failed"|"passed":\s*\[/.test(txt), 'no raw read_pipeline_state JSON visible (collapsed)');

  // yield_run: readable wait summary, NOT raw wake_on JSON
  assert(/⏸/.test(txt), 'yield_run shows ⏸ pause glyph');
  assert(/job cd16478…?/.test(txt) && /your reply/.test(txt) && /600s timer/.test(txt), 'yield_run wait targets summarized');
  assert(/SSOT generation is running/.test(txt), 'yield_run reason shown');
  assert(!/wake_on=\{|"job_ids":|"user_message":/.test(txt), 'no raw wake_on JSON visible');

  // other tools: compact labels
  assert(/job cd16478/.test(txt), 'wait_job → job id short');
  assert(/rtl evidence/.test(txt), 'read_artifact → "<stage> evidence"');
  assert(/classify rtl/.test(txt), 'classify_failure → "classify <stage>"');

  await page.evaluate(() => { const f = document.querySelector('[class*="feed"]'); if (f) f.scrollTop = 0; });
  await shoot(page, 'orch_tool_readability.png');
} finally {
  await browser.close();
}
log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
process.exit(failures().length ? 1 : 0);
