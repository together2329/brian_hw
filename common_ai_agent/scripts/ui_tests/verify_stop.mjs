import { chromium } from 'playwright';
const BASE='http://127.0.0.1:3001';
const b=await chromium.launch({channel:'chrome',headless:true});
const p=await (await b.newContext()).newPage();
await p.goto(BASE,{waitUntil:'domcontentloaded'});
await p.evaluate(async()=>{await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'admin',password:'1151'}),credentials:'include'});});
await p.waitForTimeout(8000);
for(const ip of ['shot_ctr2','shot_counter','confirmation']){
  const d=await p.evaluate(async(ip)=>{
    const out={};
    try{const r=await fetch(`/api/orchestrator/workers?ip=${ip}`,{credentials:'include'});const j=await r.json();const ws=(j.workers||[]);out.active=ws.filter(w=>Number(w.running_count||0)>0||Number(w.pending_count||0)>0).map(w=>w.workflow);}catch(e){out.werr=String(e);}
    try{const r=await fetch(`/api/orchestrator/active_run?ip=${ip}`,{credentials:'include'});out.run=await r.json();}catch(e){}
    return out;
  },ip);
  console.log('[verify]',ip,JSON.stringify(d).slice(0,200));
}
await b.close();
