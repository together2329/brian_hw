// Batch-export the interactive_ui SVG diagrams to standalone .svg/.png by
// driving each page headless and clicking its in-page export buttons.
// Doubles as an E2E test that the export buttons actually work.
//   node scripts/wavespec/export_svg.mjs
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'interactive_ui', 'img');
fs.mkdirSync(OUT, { recursive: true });
const FILES = ['timing-diagram', 'timing-compare', 'architecture-diagram', 'fsm-diagram'];

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ctx = await browser.newContext({ acceptDownloads: true });
let fail = 0;
for (const name of FILES) {
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  await page.goto('file://' + path.join(ROOT, 'interactive_ui', name + '.html'));
  await page.waitForTimeout(300); // let render() run
  const nSvg = await page.locator('svg').count();
  for (const [label, ext] of [['⬇ SVG', 'svg'], ['⬇ PNG', 'png']]) {
    const dlp = page.waitForEvent('download');
    await page.getByRole('button', { name: label }).click();
    const dl = await dlp;
    const dest = path.join(OUT, name + '.' + ext);
    await dl.saveAs(dest);
  }
  // validate the SVG output
  const svg = fs.readFileSync(path.join(OUT, name + '.svg'), 'utf8');
  const pngBytes = fs.statSync(path.join(OUT, name + '.png')).size;
  const okSvg = svg.includes('<svg') && /rgb\(|#[0-9a-f]{3,6}/i.test(svg) && /<(path|rect|line|text)/.test(svg);
  const ok = okSvg && pngBytes > 1000 && errs.length === 0;
  if (!ok) fail++;
  console.log(
    (ok ? 'PASS ' : 'FAIL ') + name.padEnd(22),
    'svgs=' + nSvg, 'svg=' + svg.length + 'B', 'png=' + pngBytes + 'B',
    errs.length ? ('ERR:' + errs[0]) : ''
  );
  await page.close();
}
await browser.close();
console.log(fail ? ('\n' + fail + ' FAILED') : '\nAll exports OK');
process.exit(fail ? 1 : 0);
