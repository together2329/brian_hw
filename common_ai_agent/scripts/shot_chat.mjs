import { chromium } from 'playwright';
const BASE='http://127.0.0.1:3000', USER='admin', PASS='1151', IP=process.env.IP||'cnt8_en_v1';
const b=await chromium.launch({headless:true});
const ctx=await b.newContext({viewport:{width:1680,height:1000}});
const errs=[];
try{
 await ctx.request.post(BASE+'/api/auth/login',{data:{username:USER,password:PASS}});
 const p=await ctx.newPage();
 p.on('pageerror',e=>errs.push('PAGEERR: '+(e.stack||e.message).slice(0,300)));
 await p.goto(BASE+'/',{waitUntil:'domcontentloaded'});
 if(await p.$('input[type=password]')){try{await p.fill('input[type=text],input[name=username]',USER);await p.fill('input[type=password]',PASS);await p.click('button[type=submit],button:has-text("Login")');}catch(_){}}
 await p.waitForTimeout(3500);
 for(const s of await p.$$('select')){const ok=await s.selectOption({label:IP}).then(()=>1).catch(()=>0);if(ok){console.log('ip set');break;}}
 await p.waitForTimeout(2000);
 // WORKSPACE screen, CHAT tab
 {const ws=await p.$('text=WORKSPACE'); if(ws){await ws.click().catch(()=>{});await p.waitForTimeout(1500);}}
 {const chat=await p.$('text=CHAT'); if(chat){await chat.click().catch(()=>{});await p.waitForTimeout(3000);}}
 const bodyTxt=(await p.evaluate(()=>document.body.innerText||'')).slice(0,400);
 const hasOrch=/dispatch|classify|read_pipeline|assistant|orchestrator run/i.test(bodyTxt);
 console.log('chat shows orchestrator activity:',hasOrch);
 await p.screenshot({path:'/tmp/chat_shot.png'});
 console.log('shot saved');
}catch(e){errs.push('SCRIPT: '+(e.message||e));}finally{if(errs.length){console.log('ERRORS:');errs.slice(0,4).forEach(e=>console.log(e));}await b.close();}
