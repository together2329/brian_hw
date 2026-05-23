import { chromium } from 'playwright';
import path from 'path';
const ROOT=process.cwd();
const b=await chromium.launch({channel:'chrome',headless:true});
let fail=0;
for(const name of ['ca53-trm','timing-diagram','ssot-explorer','architecture-diagram']){
  const ctx=await b.newContext();
  await ctx.addInitScript(()=>localStorage.setItem('iui-theme','light'));
  const page=await ctx.newPage();
  const errs=[]; page.on('pageerror',e=>errs.push(String(e)));
  await page.goto('file://'+path.join(ROOT,'interactive_ui',name+'.html'));
  await page.waitForTimeout(400);
  const bg=await page.evaluate(()=>getComputedStyle(document.body).backgroundColor);
  const theme=await page.evaluate(()=>document.documentElement.dataset.theme);
  await page.screenshot({path:path.join(ROOT,'interactive_ui','img','light',name+'.png'),fullPage:true});
  const white = bg==='rgb(255, 255, 255)';
  if(!(white&&!errs.length)) fail++;
  console.log((white&&!errs.length?'PASS ':'FAIL ')+name.padEnd(22),'theme='+theme,'bodyBg='+bg, errs.length?('ERR:'+errs[0]):'');
  await ctx.close();
}
await b.close();
process.exit(fail?1:0);
