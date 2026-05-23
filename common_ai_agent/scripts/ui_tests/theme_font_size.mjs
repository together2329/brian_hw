// Gap 3: theme / font / size actually applied to the DOM (computed CSS).
import { launch, login, shoot, assert, assertEq, failures, exitCode, log } from './lib.mjs';

// Set a React-controlled <select> by matching an option, fire change.
const setSelect = (page, kind, value) => page.evaluate(({ kind, value }) => {
  const selects = [...document.querySelectorAll('select.dir-select.mini, select.dir-select')];
  const isSize = (s) => [...s.options].some(o => /\d+px/.test(o.textContent));
  const isFont = (s) => [...s.options].some(o => /^(mono|sans|system|windows)$/i.test(o.value));
  const sel = selects.find(kind === 'size' ? isSize : isFont);
  if (!sel) return false;
  sel.value = value;
  sel.dispatchEvent(new Event('input', { bubbles: true }));
  sel.dispatchEvent(new Event('change', { bubbles: true }));
  return sel.value === value;
}, { kind, value });

const readHtml = (page) => page.evaluate(() => {
  const h = document.documentElement;
  return {
    scale: h.getAttribute('data-font-scale'),
    font: h.getAttribute('data-font'),
    theme: h.getAttribute('data-theme'),
    uiFont: getComputedStyle(h).getPropertyValue('--ui-font-size').trim(),
  };
});

const clickBtn = (page, text) => page.evaluate((t) => {
  const b = [...document.querySelectorAll('button,.dir-btn')].find(x => (x.textContent || '').trim() === t && x.offsetParent !== null);
  if (b) { b.click(); return true; }
  return false;
}, text);

const { browser, page } = await launch();
try {
  await login(page);

  // SIZE: each scale maps to a px in styles.css
  for (const [key, px] of [['compact', '13px'], ['normal', '14px'], ['large', '15px'], ['xl', '16px']]) {
    const ok = await setSelect(page, 'size', key);
    assert(ok, `size select accepts "${key}"`);
    await page.waitForTimeout(400);
    const s = await readHtml(page);
    assertEq(s.scale, key, `data-font-scale = ${key}`);
    assertEq(s.uiFont, px, `--ui-font-size = ${px} at scale ${key}`);
  }

  // FONT family
  for (const f of ['sans', 'mono']) {
    const ok = await setSelect(page, 'font', f);
    assert(ok, `font select accepts "${f}"`);
    await page.waitForTimeout(400);
    const s = await readHtml(page);
    assertEq(s.font, f, `data-font = ${f}`);
  }
  await setSelect(page, 'size', 'compact'); // back to default for the shot
  await setSelect(page, 'font', 'mono');

  // THEME
  for (const [label, attr] of [['Light', 'light'], ['Dark', 'dark']]) {
    const ok = await clickBtn(page, label);
    assert(ok, `theme button "${label}" clickable`);
    await page.waitForTimeout(400);
    const s = await readHtml(page);
    assertEq(s.theme, attr, `data-theme = ${attr}`);
    await shoot(page, `tf-${attr}.png`, { x: 0, y: 0, width: 1600, height: 90 });
  }
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await browser.close();
}
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
