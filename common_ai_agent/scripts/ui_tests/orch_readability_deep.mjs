// DEEP test of orchestrator tool-call readability via the REAL hydration path
// (onConvLoaded / conversation.json), which is where the live bug lived — the
// faux-stream/injection path looked fine while this one dumped raw role='tool'
// lines. Messages mirror the persisted conversation.json shape:
//   - tool CALL  → role:'tool',  content: '⏺ <tool>(<key=val…>)'  (format_tool_call)
//   - tool RESULT→ role:'tool',  content: '└─ <json|text>'        (record_tool_result)
//   - agent/thought → role:'assistant' / 'thought'
import { launch, login, gotoWorkspace, shoot, assert, failures, results, log } from './lib.mjs';

const ja = (o) => JSON.stringify(o);
const call = (tool, args) => ({ role: 'tool', content: `⏺ ${tool}(${args})` });
const result = (text) => ({ role: 'tool', content: `└─ ${text}` });

const messages = [
  { role: 'assistant', content: "Got it — I'll drive mctp_axi to green." },
  { role: 'thought', content: 'No stages run yet; read state first.' },

  // read_pipeline_state (passed + failed-with-reasons + running)
  call('read_pipeline_state', 'ip="mctp_axi", include_jobs=true'),
  result(ja({ ip: 'mctp_axi', passed: ['ssot', 'fl-model', 'rtl', 'lint'], failed: { sim: 'mctp_axi/logs/sim.json status=fail [sim] FAIL', sta: 'mctp_axi/sta/wns.json clk setup WNS=-4.13 viol=5' }, running: ['tb'] })),

  // dispatch_workflow single + running result
  call('dispatch_workflow', 'workflow="ssot-gen", ip="mctp_axi", prompt="Create the SSOT requirements/specification for an AXI slave processing MCTP packets with full register map and verification goals.", reason="kickoff"'),
  result(ja({ ok: true, workflow: 'ssot-gen', status: 'running', worker: 'http://127.0.0.1:6911', job_ids: ['cd16478088c1'], model: 'deepseek-v4-pro' })),

  // dispatch_workflow fan-out (stages) + per-stage jobs result
  call('dispatch_workflow', 'ip="mctp_axi", stages=["lint","tb","syn"], schedule="dag", prompt="Verify RTL in parallel"'),
  result(ja({ ok: true, jobs: [{ workflow: 'lint', status: 'running' }, { workflow: 'tb', status: 'running' }, { workflow: 'syn', status: 'queued' }] })),

  // dispatch_workflow with ERROR result
  call('dispatch_workflow', 'workflow="sim", ip="mctp_axi", reason="run cocotb"'),
  result(ja({ ok: false, workflow: 'sim', status: 'error', error: 'sim timed out after 600s' })),

  // write_handoff
  call('write_handoff', 'workflow="rtl-gen", ip="mctp_axi", payload={"task":"Implement RTL from approved SSOT"}, reason="fl/cl models passed"'),

  // yield_run variants
  call('yield_run', 'wake_on={"job_ids":["cd16478088c1"],"user_message":true,"after_seconds":600}, reason="SSOT generation is running"'),
  call('yield_run', 'wake_on={"after_seconds":120}, reason="cooldown"'),
  call('yield_run', 'wake_on={"user_message":true}, reason="awaiting decision"'),

  // wait_job / read_artifact / classify_failure / mark_downstream_stale
  call('wait_job', 'job_id="cd16478088c1"'),
  call('read_artifact', 'ip="mctp_axi", stage="rtl"'),
  call('classify_failure', 'stage="sim", evidence={"open_required_todos":3}'),
  call('mark_downstream_stale', 'ip="mctp_axi", from_stage="ssot"'),

  // web_search / ask_user / import_document
  call('web_search', 'query="UVM scoreboard cocotb best practices", limit=5'),
  call('ask_user', 'question="Increase sim-debug budget or stop as blocked?"'),
  call('import_document', 'ip="mctp_axi", path="/Users/brian/docs/mctp_spec.pdf"'),

  // EDGE: malformed / truncated read_pipeline_state result must degrade gracefully
  call('read_pipeline_state', 'ip="mctp_axi"'),
  result('{"passed":["ssot","rtl"],"failed":{"sim":"status=fa…[truncated]'),

  // __final__ terminal dispatch
  call('dispatch_workflow', 'workflow="__final__", ip="mctp_axi", payload={"state":"blocked","reason":"manual review"}'),
];

const { browser, page } = await launch();
try {
  await login(page);
  await gotoWorkspace(page, { ip: 'mctp_axi', workflow: 'orchestrator' });
  await page.evaluate(() => { const e=[...document.querySelectorAll('button,span,div,[role="tab"]')].find(x=>(x.textContent||'').trim().toUpperCase()==='CHAT'&&x.offsetParent);if(e)e.click(); });
  await page.waitForTimeout(900);
  const inject = () => page.evaluate((m)=>window.dispatchEvent(new CustomEvent('atlas-conversation-loaded',{detail:{messages:m}})), messages);
  await inject();
  await page.waitForTimeout(1400);
  if (await page.locator('.tool-card').count() === 0) { await inject(); await page.waitForTimeout(1400); }

  const handoffs = await page.locator('.handoff-card').count();
  const toolCards = await page.locator('.tool-card').count();
  const allText = (await page.locator('.feed-entry, .tool-card, .react-block').allInnerTexts()).join('\n');
  log('--- DEEP rendered text ---\n' + allText.slice(0, 1600) + '\n--------------------------');

  // dispatch_workflow(×4: ssot, fan-out, sim, __final__) + write_handoff = 5 handoff cards
  assert(handoffs >= 5, `>=5 HandoffCards (dispatch/handoff) rendered (got ${handoffs})`);
  assert(toolCards >= 12, `tool cards rendered for all calls (got ${toolCards})`);

  // NO raw JSON / raw arg blobs leaking anywhere in the feed
  assert(!/wake_on=\{|"job_ids":|"user_message":|"after_seconds":/.test(allText), 'no raw yield_run wake_on JSON');
  assert(!/\{"failed"|"passed":\s*\[|status=fail \[sim\]/.test(allText), 'no raw read_pipeline_state JSON');
  assert(!/prompt="Create the SSOT|payload=\{/.test(allText), 'no raw dispatch prompt/payload blob');

  // HandoffCard fields
  assert(/⇢/.test(allText), 'handoff ⇢ glyph present');
  assert(/Dispatch/.test(allText) && /Handoff/.test(allText), 'both Dispatch + Handoff verbs');
  assert(/Implement RTL from approved SSOT/.test(allText), 'write_handoff task shown');
  assert(/lint|tb|syn/.test(allText), 'fan-out stages shown');
  assert(/timed out after 600s/.test(allText), 'dispatch error surfaced');

  // read_pipeline_state summary (✓/✗ + compact reasons)
  assert(/✓/.test(allText) && /✗/.test(allText), 'read_pipeline_state ✓/✗ summary');
  assert(/sim\(fail\)|sim\(FAIL\)/i.test(allText), 'failed sim with reason');
  assert(/WNS -4\.13\/5/.test(allText), 'STA WNS/viol compacted');

  // yield_run variants
  assert(/⏸ until job cd\w+… \/ your reply \/ 600s timer/.test(allText), 'yield_run combo summarized');
  assert(/⏸ until 120s timer/.test(allText), 'yield_run timer-only summarized');
  assert(/⏸ until your reply/.test(allText), 'yield_run user-only summarized');

  // compact labels
  assert(/job cd16478/.test(allText), 'wait_job short id');
  assert(/rtl evidence/.test(allText), 'read_artifact label');
  assert(/classify sim/.test(allText), 'classify_failure label');
  assert(/stale from ssot/.test(allText), 'mark_downstream_stale label');
  assert(/“UVM scoreboard cocotb best practices”/.test(allText), 'web_search query');
  assert(/Increase sim-debug budget or stop as blocked\?/.test(allText), 'ask_user question');
  assert(/mctp_spec\.pdf/.test(allText), 'import_document filename');

  // EDGE: malformed read_pipeline_state must NOT crash the feed (still many cards)
  assert(toolCards >= 12, 'malformed read_pipeline_state did not break rendering');

  // agent + thought still render
  assert(/Got it — I'll drive mctp_axi/.test(allText), 'agent prose rendered');

  await shoot(page, 'orch-deep.png');
} finally {
  await browser.close();
}
log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
process.exit(failures().length ? 1 : 0);
