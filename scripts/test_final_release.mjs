// Additional release regressions: point state, causal exports, provenance, local file policy.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
const file=path.resolve(process.env.TG_HTML||'.verification/final-release/ThawGuard-AI/index.html');
const out=process.env.TG_QA_OUT||'.verification/final-qa/edge';
const channel=process.env.TG_BROWSER||'msedge';await fs.mkdir(out,{recursive:true});
const checks=[],errors=[],requests=[];
function ok(v,m){if(!v)throw Error(m);checks.push(m);}
const b=await chromium.launch({headless:true,channel});
const c=await b.newContext({offline:true,viewport:{width:1440,height:1000},acceptDownloads:true});
const p=await c.newPage();p.on('pageerror',e=>errors.push(String(e)));p.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
async function download(button,name){const pending=p.waitForEvent('download');await p.getByRole('button',{name:button,exact:true}).click();const d=await pending;const dest=path.join(out,name);await d.saveAs(dest);return {dest,suggested:d.suggestedFilename()};}
try{
 await p.goto(pathToFileURL(file).href);await p.getByRole('button',{name:'查看RTS 1938真实监测案例',exact:true}).waitFor();
 ok(p.url().startsWith('file:///'),'Actual extracted index.html opened with file://');
 ok((await p.locator('.hero .image-role-label').innerText()).includes('不是模型预测输出'),'Landing explicitly labels morphology image role');
 ok((await p.locator('#tg-third-party-notices').textContent()).includes('ISC License'),'Single-file forwarding preserves bundled library licenses');
 for(let i=0;i<6;i++){await p.locator('nav button').nth(i).click();ok(await p.locator('.observatory').getAttribute('data-page')===['story','overview','evidence','evolution','impact','science'][i],`Navigation ${i+1} renders intended page`);}
 await p.locator('nav button').nth(4).click();await p.getByLabel('地表覆盖年份').selectOption('2020');await p.locator('.exposure-tabs button').nth(1).click();
 ok((await p.locator('.cover-values').innerText()).includes('69.2%'),'1938 2020 cover starts at its real value');
 await p.locator('.impact-point-picker .point-picker button').nth(0).click();
 ok(await p.locator('.other-case-note').isVisible()&&await p.locator('.public-impact').count()===0,'1820 removes 1938 exclusive terrain, cover and infrastructure panels');
 ok(await p.locator('.exposure-map').count()===0&&await p.getByLabel('地表覆盖年份').count()===0,'1820 does not retain hidden 1938 map or cover controls');
 ok(!(await p.locator('.page-heading').innerText()).includes('查看 RTS 1938 已记录'),'Impact heading tracks selected comparison case');
 await p.locator('.impact-point-picker .point-picker button').nth(2).click();
 ok(await p.locator('.other-case-note').isVisible()&&await p.locator('.public-impact').count()===0,'Background also removes 1938 exclusive context');
 ok((await p.locator('.impact-values').innerText()).includes('不可计算'),'Background does not invent annual areas');
 await p.locator('.impact-point-picker .point-picker button').nth(1).click();
 ok((await p.locator('.cover-values').innerText()).includes('69.2%')&&(await p.getByLabel('地表覆盖年份').inputValue())==='2020','Returning to 1938 restores its matching selected-year values');
 ok((await p.locator('.exposure-tabs .active').innerText()).includes('铁路'),'Selected facility tab remains coherent after point round trip');
 ok((await p.locator('.exposure-results').innerText()).includes('24.23 km'),'Returning to 1938 restores actual rail distance');
 await p.getByLabel('地表覆盖年份').selectOption('2021');ok((await p.locator('.cover-values').innerText()).includes('74.5%'),'1938 alternate-year values remain switchable');
 await p.locator('nav button').nth(2).click();await p.getByLabel('回放截止日期').fill('2020-11-23');await p.locator('.stage-tabs button').nth(4).click();
 const before=await download('导出证据 JSON','before.json');let j=JSON.parse(await fs.readFile(before.dest,'utf8'));
 ok(j.as_of==='2020-11-23'&&j.sccd_snapshot.segments.filter(s=>s.break).length===0,'Pre-detection export contains no future break');
 ok(j.observations.every(o=>o.date<=j.as_of)&&j.image_references.every(i=>i.date<=j.as_of),'Exported observations and images respect selected cutoff');
 ok(j.auxiliary_prefix.residuals.length===0&&j.auxiliary_prefix.ndvi_flags.every(f=>f.date<=j.as_of),'Pre-detection assistance export does not expose future residuals');
 await p.getByLabel('回放截止日期').fill('2020-11-24');const after=await download('导出证据 JSON','after.json');j=JSON.parse(await fs.readFile(after.dest,'utf8'));
 ok(j.sccd_snapshot.segments.some(s=>s.break==='2020-09-29'),'Adding first-detection observation changes exported actual result');
 const report=await download('导出当前判读说明','case-report.html');
 ok(report.suggested.includes('RTS_1938')&&report.suggested.includes('2020-11-24'),'Report filename identifies RTS and as-of date');
 const rp=await c.newPage();await rp.goto(pathToFileURL(path.resolve(report.dest)).href);const text=await rp.locator('body').innerText();
 ok(text.includes('截至 2020-11-24')&&text.includes('RTS 1938'),'Report content identifies case and cutoff');
 ok(text.includes('分析假设')&&text.includes('Ye, Rogan, Zhu')&&text.includes('外部论文、数据源和产品链接需联网'),'Report includes assumptions, method attribution and offline-link boundary');
 ok(text.includes('统计单位不同')&&text.includes('不能据此计算准确率优势'),'Report prevents invalid baseline performance claims');
 ok(await rp.locator('img').count()===2&&await rp.locator('img').evaluateAll(a=>a.every(i=>i.complete&&i.naturalWidth>0)),'Exported report images decode in offline file:// context');
 await rp.close();
 for(const [idx,key] of [[0,'rts-1820'],[2,'background']]){
  await p.locator('.evidence-sidebar .point-picker button').nth(idx).click();const d=await download('导出证据 JSON',key+'.json');const q=JSON.parse(await fs.readFile(d.dest,'utf8'));
  ok(q.point.key===key&&q.posthoc_public_context===null&&q.cross_source_context===null,`${key} JSON never inherits 1938 public or cross-source context`);
  ok(key!=='background'||q.terrain_context===null,'Background does not inherit another point terrain');
 }
 await p.locator('.evidence-sidebar .point-picker button').nth(1).click();await p.locator('.stage-tabs button').nth(0).click();await p.getByRole('button',{name:'2020 断点前后影像',exact:true}).click();
 await p.locator('.case-workspace').screenshot({path:out+'/evidence-preview.png'});
 await p.locator('nav button').nth(0).click();await p.setViewportSize({width:1440,height:900});await p.screenshot({path:out+'/demo-preview.png'});
 await p.locator('.edition').click();const st=await p.getByRole('dialog').innerText();ok(st.includes('链接需联网')&&st.includes('Ye, Rogan, Zhu')&&st.includes('科研材料：'),'Sources dialog preserves scholarly credit and external-link notice');
 ok(errors.length===0,'No JavaScript errors on release regression route');ok(requests.length===0,'No external HTTP(S) requests across offline regressions');
 await fs.writeFile(out+'/RELEASE_BROWSER_QA.json',JSON.stringify({status:'passed',channel,browser_version:b.version(),os:process.platform,protocol:'file:',input_path:file,html_sha256:crypto.createHash('sha256').update(await fs.readFile(file)).digest('hex'),count:checks.length,checks,errors,requests,physical_devices:1,notes:'Same Windows host; not an independent second physical device. Browser offline context; OS adapter state was not changed.'},null,2));
 console.log(JSON.stringify({channel,version:b.version(),checks:checks.length,status:'passed'}));
}catch(e){await p.screenshot({path:out+'/failure.png',fullPage:true});console.log(JSON.stringify({checks,errors,requests}));throw e;}finally{await b.close();}
