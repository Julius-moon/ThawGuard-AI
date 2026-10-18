from pathlib import Path
import json,zipfile,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'deliverables/observatory-v7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
artifact=O/'ThawGuard_连续观测与事件证据_v7.html';manifest=json.loads((O/'MANIFEST.json').read_text(encoding='utf-8'));assert sha(artifact)==manifest['sha256']
for n in ['BROWSER_QA.json','SCIENCE_QA.json','LIVE_PREVIEW_QA.json']:assert json.loads((O/n).read_text(encoding='utf-8'))['status']=='passed'
docs=['AUDIT.md','DATA_AUDIT.md','MODEL_CARD.md','COPY_REVIEW.md','THREE_MINUTE_GUIDE.md','README_运行与边界.md','source_registry.csv','MODEL_RUN.json','model_run.log','BROWSER_QA.json','SCIENCE_QA.json','LIVE_PREVIEW_QA.json','MANIFEST.json']
entry='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ThawGuard V7 · 交付入口</title><style>body{max-width:1100px;margin:40px auto;padding:24px;font:17px/1.85 'Segoe UI','Microsoft YaHei',sans-serif;background:#f5f7f3;color:#244751}h1{font-size:33px;line-height:1.5}p{color:#5a737b}a{color:#246e77}a.main{display:inline-block;background:#236e77;color:white;border-radius:8px;padding:14px 22px;text-decoration:none;margin:15px 0}section{padding:25px;background:white;border:1px solid #d3e1d7;border-radius:12px;margin-top:24px}img{width:100%;border-radius:8px}nav{display:flex;flex-wrap:wrap;gap:17px;font-size:15px}</style><h1>ThawGuard V7<br>RTS 1938 公开数据与科学判读</h1><p>基于现有V6继续迭代。公开卫星观测、变化检测回放、地形、地表分类与设施距离在同一案例中核查。</p><a class="main" href="ThawGuard_连续观测与事件证据_v7.html">打开完整离线 Demo →</a><nav><a href="THREE_MINUTE_GUIDE.md">三分钟路线</a><a href="README_运行与边界.md">使用说明</a><a href="DATA_AUDIT.md">数据审计</a><a href="MODEL_CARD.md">方法卡与训练门槛</a><a href="source_registry.csv">来源登记表</a></nav><section><h2>先看真实的检测与影像</h2><p>30m Landsat用于公开S-CCD，10m Sentinel用于形态参照。断点与两期边界不能自动确认滑塌起始时间或未来风险。</p><img src="screenshots/16-断点前后联合证据.png" alt="实际浏览器中的2020断点前后影像与模型"></section><section><h2>再看真实设施关系</h2><p>最近OSM记录路径约9.77km、铁路约24.23km。虚线是几何测距，不是灾害运移路径；不将间距转成失效概率。</p><img src="screenshots/18-真实设施与测距.png" alt="真实OSM设施与几何测距"></section><p>78项浏览器回归、116项数据/方法完整性检查通过，不等于分类准确率或现场效益已验证。459条现有标签均为RTS，核实负类为0；本版采用可审计规则辅助，未训练伪二分类器。猫咪未在干净浏览器复现，外部来源尚未确认。</p></html>'''
(O/'打开这里_交付入口.html').write_text(entry,encoding='utf-8')
shots=['13-运行首页.png','16-断点前后联合证据.png','17-地表覆盖与光谱统计.png','18-真实设施与测距.png','390-项目导览.png','390-地表扰动与设施.png']
share=R/'deliverables/ThawGuard_v7_协作展示包.zip'
with zipfile.ZipFile(share,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in [artifact,O/'打开这里_交付入口.html',*[O/n for n in docs],*[O/'screenshots'/n for n in shots],*list((O/'baseline').glob('*.png'))]:z.write(p,p.relative_to(O).as_posix())
 q=O/'SOURCE_REBUILD_QA.json'
 if q.exists() and json.loads(q.read_text(encoding='utf-8')).get('sha256')==sha(artifact):z.write(q,q.name)
files=[R/n for n in ['package-lock.json','tsconfig.json','vite.config.ts','index.html','requirements-observatory.txt','requirements-observatory-v6.txt','requirements-observatory-v7.txt','README.md','STATUS.md','data/source_registry.csv']]
files+=list((R/'src/observatory-v7').glob('*'))
scripts=['audit_v7.mjs','public_range_reader.py','acquire_v7_public.py','acquire_v7_sentinel.py','acquire_v7_climate.py','process_v7_public.py','register_v7_sources.py','experiment_v7.py','validate_observatory_v7.py','test_observatory_v7.mjs','vite.observatory-v7.config.ts','package_observatory_v7.py','build_observatory_v7_site.py','serve_observatory_v7.mjs','verify_observatory_v7_preview.mjs','release_observatory_v7.py','acquire_v6_evidence.py','match_v6_inventory.py','acquire_observatory.py','process_observatory.py']
files += [R/'scripts'/n for n in scripts]
files += [R/'public/data'/n for n in ['summary.json','sites.geojson','workflow-terrain.json']]
for folder,pattern in [('public/data/layers','rts-*.geojson'),('public/data/observatory','*.json'),('public/data/observatory-v6','*'),('public/data/observatory-v7','*'),('data/raw/observatory-v7','*'),('data/processed/observatory-v7','*')]:files+=list((R/folder).glob(pattern))
images=[]
for f in ['public/data/observatory/images.json','public/data/observatory-v6/extra-images.json','public/data/observatory-v7/extra-images.json']:images+=json.loads((R/f).read_text(encoding='utf-8'))
files += [R/'public'/i['path'].lstrip('/') for i in images]+[R/'public/images/beiluhe-nasa.jpg']
files += list((R/'data/raw').glob('QTP_RTS_*'))+[R/'data/raw/10928346_metadata.json',R/'data/raw/2008-2021RTSs.shp.zip',R/'research/observatory-v6/raw/RTS-inventory.zip',R/'research/observatory-v5/catalog.json']+list((R/'research/observatory-v6').glob('zenodo-*.json'))
files += [R/'deliverables/observatory-v5/SCIENCE_QA.json',R/'deliverables/observatory-v5/ThawGuard_连续观测与事件证据_v5.html',R/'deliverables/observatory-v6/ThawGuard_连续观测与事件证据_v6.html']+[O/n for n in docs]
package=json.loads((R/'package.json').read_text(encoding='utf-8'));package['scripts']={k:v for k,v in package['scripts'].items() if k in ['dev','build','preview','preview:observatory','test:observatory','test:science','data:experiment']}
source=R/'deliverables/ThawGuard_v7_源码与公开数据.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('package.json',json.dumps(package,ensure_ascii=False,indent=2)+'\n')
 for p in sorted(set(files)):
  assert p.is_file(),p
  z.write(p,p.relative_to(R).as_posix())
for p in [share,source]:
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
release={'version':'v7','date':'2026-10-18','artifact':{'file':artifact.name,'bytes':artifact.stat().st_size,'sha256':sha(artifact)},'browser_checks':json.loads((O/'BROWSER_QA.json').read_text(encoding='utf-8'))['count'],'data_method_checks':json.loads((O/'SCIENCE_QA.json').read_text(encoding='utf-8'))['count'],'packages':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in [share,source]],'raw_public_data_in_source_package':True,'private_ppt_parameters_or_samples_included':False,'trained_classifier':False,'reason':'459 positive RTS records, zero verified non-RTS labels. Public S-CCD and baseline actually run.','independent_accuracy_or_user_benefit_established':False}
(O/'RELEASE.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(release,ensure_ascii=True))
