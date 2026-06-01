import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';

const baseUrl = 'http://127.0.0.1:5179/coverage-qa.html';
const evidenceDir = '/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.omo/ulw-loop/019e7e69-3956-76b0-89df-6acc580185bd/evidence';

const requireText = async (page, text) => {
  await page.getByText(text, { exact: true }).waitFor({ timeout: 10000 });
};

const bodyText = async page => page.locator('body').innerText();

const assertIncludes = (haystack, needle, label) => {
  if (!haystack.includes(needle)) {
    throw new Error(`${label}: missing ${needle}`);
  }
};

const assertNotIncludes = (haystack, needle, label) => {
  if (haystack.includes(needle)) {
    throw new Error(`${label}: unexpected ${needle}`);
  }
};

const writeScenario = async (name, lines) => {
  await writeFile(`${evidenceDir}/${name}.txt`, `${lines.join('\n')}\n`, 'utf8');
};

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });

try {
  await page.goto(`${baseUrl}?scenario=coverage`, { waitUntil: 'networkidle' });
  for (const label of [
    'Verilator code coverage',
    'pyslang static/elab coverage',
    'Simulation VCD toggle coverage',
    'FL function coverage',
    'CL cycle coverage',
  ]) {
    await requireText(page, label);
  }
  for (const detail of [
    'Reset path never deasserted',
    '1/8 bits',
    'rtl/missing.sv',
    'idle/read transaction not observed',
    'ready latency transition not observed',
  ]) {
    await requireText(page, detail);
  }
  await page.getByRole('button', { name: /Reset path never deasserted/ }).click();
  await page.getByText('toggle gap: only 1/8 bits toggled in tb.demo_ip.u_dut').waitFor({ timeout: 10000 });
  await page.getByText("always_ff @(posedge clk) if (reset_n) out <= {24'h0, state};").waitFor({ timeout: 10000 });
  const c001Body = await bodyText(page);
  assertIncludes(c001Body, 'modules 1 / always 1 / assigns 2 / lines 42', 'C001 static RTL row');
  await page.screenshot({ path: `${evidenceDir}/C001-browser-coverage-kinds.png`, fullPage: true });
  await writeScenario('C001-browser-coverage-kinds', [
    'PASS C001 coverage browser QA',
    'Observed Verilator, pyslang static/elab, Simulation VCD toggle, FL, and CL coverage labels.',
    'Observed unmet reasons/details: Reset path never deasserted, 1/8 bits, rtl/missing.sv, FL/CL missing bin descriptions.',
    'Clicked VCD toggle unmet scope and observed RTL source plus diagnostic: toggle gap: only 1/8 bits toggled in tb.demo_ip.u_dut.',
  ]);

  await page.goto(`${baseUrl}?scenario=empty`, { waitUntil: 'networkidle' });
  await page.getByText(/No coverage artifacts found yet/).waitFor({ timeout: 10000 });
  const c002Body = await bodyText(page);
  assertNotIncludes(c002Body, 'toggle gap: only 1/8 bits toggled', 'C002 empty coverage');
  assertNotIncludes(c002Body, 'Reset path never deasserted', 'C002 empty coverage');
  await page.screenshot({ path: `${evidenceDir}/C002-browser-coverage-empty.png`, fullPage: true });
  await writeScenario('C002-browser-coverage-empty', [
    'PASS C002 empty/malformed coverage browser QA',
    'Observed empty coverage guidance without crash.',
    'Confirmed no VCD diagnostic/source focus text appears for malformed tools/artifacts/vcd_paths.',
  ]);

  await page.goto(`${baseUrl}?workflow=lint`, { waitUntil: 'networkidle' });
  await requireText(page, 'WIDTH');
  await page.getByRole('button', { name: /Output port connection width mismatch/ }).click();
  await page.getByTestId('lint-diagnostic-annotation').getByText('Output port connection width mismatch: left 32 bits, right 8 bits').waitFor({ timeout: 10000 });
  await page.locator('.line').filter({ hasText: 'assign out = in[7:0];' }).first().waitFor({ timeout: 10000 });
  const calls = await page.evaluate(() => window.__readCalls || []);
  const lintCall = JSON.stringify(calls);
  assertIncludes(lintCall, 'demo_ip/rtl/demo.sv', 'C003 lint readAtlasAsyncResource call');
  await page.screenshot({ path: `${evidenceDir}/C003-browser-lint-regression.png`, fullPage: true });
  await writeScenario('C003-browser-lint-regression', [
    'PASS C003 lint browser regression QA',
    'Observed lint WIDTH diagnostic and clicked it.',
    'Observed RTL source line assign out = in[7:0]; and readAtlasAsyncResource path demo_ip/rtl/demo.sv.',
  ]);
} finally {
  await browser.close();
}
