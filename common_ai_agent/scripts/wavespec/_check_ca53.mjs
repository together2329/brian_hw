import { chromium } from 'playwright';
import path from 'path';
const ROOT=process.cwd();
const b=await chromium.launch({channel:'chrome',headless:true});
const page=await b.newPage();
const errs=[]; page.on('pageerror',e=>errs.push(String(e)));
await page.goto('file://'+path.join(ROOT,'interactive_ui','ca53-trm.html'));
await page.waitForTimeout(400);
const counts=await page.evaluate(()=>({
  regRows: document.querySelectorAll('table tr').length,
  featureText: document.body.innerText.includes('Implementation options'),
  hasMAIR: document.body.innerText.includes('MAIR_EL1'),
  hasCCSIDR: document.body.innerText.includes('CCSIDR_EL1'),
  hasCTRfields: document.body.innerText.includes('IminLine'),
}));
await page.screenshot({path:path.join(ROOT,'interactive_ui','img','ca53-trm.png'),fullPage:true});
console.log('pageerrors:', errs.length, errs[0]||'');
console.log('table rows:', counts.regRows, '| Implementation options:', counts.featureText,
            '| MAIR_EL1:', counts.hasMAIR, '| CCSIDR_EL1:', counts.hasCCSIDR, '| CTR IminLine field:', counts.hasCTRfields);
await b.close();
