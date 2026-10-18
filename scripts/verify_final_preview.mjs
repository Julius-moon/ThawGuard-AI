import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const out='deliverables/ThawGuard-AI',url='http://127.0.0.1:8000/';
const checks=[],errors=[],external=[];function ok(v,m){if(!v)throw Error(m);checks.push(m);}
const bytes=await fs.readFile(out+'/index.html'),hash=crypto.createHash('sha256').update(bytes).digest('hex');
const r=await fetch(url);ok(r.status===200,'Bundled one-command Node fallback returns HTTP 200');ok(crypto.createHash('sha256').update(Buffer.from(await r.arrayBuffer())).digest('hex')===hash,'Fallback serves byte-identical frozen HTML');
ok((await fetch(url+'../package.json')).status===404&&(await fetch(url+'docs/DATA_AND_AI.md')).status===404,'Fallback exposes only index.html, not workspace files');
const b=await chromium.launch({headless:true,channel:'msedge'});
try{
 const c=await b.newContext({viewport:{width:1440,height:900}});await c.route('**/*',route=>{if(/^https?:/.test(route.request().url())&&!route.request().url().startsWith(url)){external.push(route.request().url());return route.abort();}return route.continue();});
 const p=await c.newPage();p.on('pageerror',e=>errors.push(String(e)));await p.goto(url);await p.getByRole('button',{name:'查看RTS 1938真实监测案例',exact:true}).waitFor();
 await p.screenshot({path:out+'/media/demo-preview.png'});ok(await p.locator('.notice').count()===0,'Fresh landing screenshot contains no leftover export notification');
 await p.getByRole('button',{name:'查看RTS 1938真实监测案例',exact:true}).click();await p.getByRole('button',{name:'回到首次检出前',exact:true}).click();ok((await p.locator('.time-evidence').innerText()).includes('未形成结构断点'),'Live prefix route has no break before first-detection observation');
 await p.getByRole('button',{name:'加入首次检出观测',exact:true}).click();await p.getByRole('button',{name:'2020 断点前后影像',exact:true}).click();ok((await p.locator('.time-evidence').innerText()).includes('2020-11-24'),'Live route shows actual first detectable observation');
 await p.locator('.linked-grid').screenshot({path:out+'/media/evidence-preview.png'});
 await p.locator('nav button').nth(4).click();await p.locator('.exposure-grid').screenshot({path:out+'/media/impact-preview.png'});ok((await p.locator('.exposure-results').innerText()).includes('9.77 km'),'Live route shows actual OSM proximity');
 ok(errors.length===0&&external.length===0,'Local preview route has no external requests or script errors');
 await fs.writeFile(out+'/qa/LIVE_PREVIEW_QA.json',JSON.stringify({status:'passed',url,html_sha256:hash,count:checks.length,checks,errors,external,notes:'Screenshots captured from fresh real Edge context. Local-only server, no public deployment.'},null,2));console.log(JSON.stringify({status:'passed',checks:checks.length,sha256:hash}));
}finally{await b.close();}
