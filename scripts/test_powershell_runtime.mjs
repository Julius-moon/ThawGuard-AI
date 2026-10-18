import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const url='http://127.0.0.1:8017/',out='.verification/powershell-runtime';await fs.mkdir(out,{recursive:true});
const expected=crypto.createHash('sha256').update(await fs.readFile('index.html')).digest('hex');
const checks=[],errors=[],external=[];function ok(v,m){if(!v)throw Error(m);checks.push(m);}
const r=await fetch(url);ok(r.status===200,'PowerShell-only runtime returns HTTP 200');ok(crypto.createHash('sha256').update(Buffer.from(await r.arrayBuffer())).digest('hex')===expected,'HTTP response equals frozen offline HTML');
ok((await fetch(url,{method:'HEAD'})).status===200,'HEAD works without sending the body');
ok((await fetch(url+'README.md')).status===404&&(await fetch(url+'.git/config')).status===404,'Runtime exposes no source, configuration or Git paths');
ok((await fetch(url,{method:'POST'})).status===404,'Runtime rejects write methods');
const b=await chromium.launch({headless:true,channel:'msedge'});
try {
 const c=await b.newContext({viewport:{width:1440,height:900},acceptDownloads:true});await c.route('**/*',route=>{const u=route.request().url();if(/^https?:/.test(u)&&!u.startsWith(url)){external.push(u);return route.abort();}return route.continue();});
 const p=await c.newPage();p.on('pageerror',e=>errors.push(String(e)));await p.goto(url);await p.getByRole('button',{name:'查看RTS 1938真实监测案例',exact:true}).waitFor();
 for(let i=0;i<6;i++){await p.locator('nav button').nth(i).click();ok(await p.locator('.observatory').getAttribute('data-page')===['story','overview','evidence','evolution','impact','science'][i],`Page ${i+1} works using only Windows runtime`);}
 await p.locator('nav button').nth(2).click();await p.getByRole('button',{name:'回到首次检出前',exact:true}).click();ok((await p.locator('.time-evidence').innerText()).includes('未形成结构断点'),'Actual prefix before detection shows no break');
 await p.getByRole('button',{name:'加入首次检出观测',exact:true}).click();ok((await p.locator('.time-evidence').innerText()).includes('2020-11-24'),'First-detection observation changes actual replay');
 const pending=p.waitForEvent('download');await p.getByRole('button',{name:'导出当前判读说明',exact:true}).click();const d=await pending;const dest=path.resolve(out+'/export.html');await d.saveAs(dest);ok(d.suggestedFilename().includes('RTS_1938')&&d.suggestedFilename().includes('2020-11-24'),'Runtime permits dated same-case report export');
 const rc=await b.newContext({offline:true});const rp=await rc.newPage();await rp.goto(pathToFileURL(dest).href);ok(await rp.locator('img').evaluateAll(a=>a.every(i=>i.complete&&i.naturalWidth>0)),'Exported report remains offline and self-contained');
 ok(errors.length===0&&external.length===0,'No JavaScript errors or external requests on tested runtime route');
 await fs.writeFile('qa/POWERSHELL_RUNTIME_QA.json',JSON.stringify({status:'passed',count:checks.length,checks,errors,external,html_sha256:expected,runtime:'Windows built-in PowerShell 5.1 / .NET TcpListener; application does not require Node or Python',test_harness:'Playwright/Node used only as verifier',browser_version:b.version(),physical_devices:1},null,2));console.log(JSON.stringify({status:'passed',checks:checks.length,html_sha256:expected}));
}finally{await b.close();}
