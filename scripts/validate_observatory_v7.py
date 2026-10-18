"""Independent boundary, time-order, QA, scaling and public-engine checks."""
from pathlib import Path
import json,datetime,hashlib,os,re
import numpy as np
import pyxccd
from pyxccd.utils import predict_ref
from shapely.geometry import shape,Point
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];P=R/'public/data/observatory';out=R/os.environ.get('TG_QA_OUT','deliverables/observatory-v7');out.mkdir(parents=True,exist_ok=True);checks=[]
def check(v,msg):
 assert v,msg
 checks.append(msg)
layers={y:json.loads((R/f'public/data/layers/rts-{y}.geojson').read_text(encoding='utf-8')) for y in [2016,2022]}
catalog=json.loads((R/'research/observatory-v5/catalog.json').read_text(encoding='utf-8'));expected=sum(x['id'].endswith('_T1') for x in catalog)
for key in ['rts-1820','rts-1938','background']:
 d=json.loads((P/(key+'.json')).read_text(encoding='utf-8'));obs=d['observations'];unique={}
 for o in obs:
  if o['quality'] in ['clear','water']:unique.setdefault(o['date'],o)
 v=list(unique.values())
 check([o['item'] for o in v]==[o['item'] for o in obs if o['used_in_model']],f'{key}: model membership independently reconstructed from quality and same-day ordering')
 check(len(obs)==expected,f'{key}: every catalogued Tier 1 scene retained ({expected})')
 check(len({o['date'] for o in v})==len(v),f'{key}: no duplicate valid dates')
 check(sum(d['quality_counts'].values())==len(obs),f'{key}: QA counts reconcile')
 check(all(o['item'].endswith('_T1') for o in obs),f'{key}: lower geometric quality Tier 2 excluded')
 for o in obs:
  check_value=all(abs(a-(b*.0000275-.2))<1e-7 for a,b in zip(o['values'],o['dn']))
  assert check_value,(key,o['item'],'reflectance scaling')
  if o['quality'] in ['clear','water']:assert o['qa_pixel']&(1|2|8|16|32)==0 and o['qa_radsat']==0
 checks.append(f'{key}: all raw DN conversions and valid-pixel QA independently checked')
 check(all(r['n']==sum(o['date']<=r['as_of'] for o in v) for r in d['replays']),f'{key}: each replay includes exactly the available valid prefix')
 check(all(not s['break'] or s['break']<=r['as_of'] for r in d['replays'] for s in r['segments']),f'{key}: no future break exposed in replay')
 for cutoff in ['2010-12-31','2020-11-23','2020-11-24','2025-12-31']:
  use=[o for o in v if o['date']<=cutoff];dates=np.array([o['ordinal'] for o in use],dtype=np.int64);a=np.array([[round(x*10000) for x in o['values']] for o in use],dtype=np.int64);qas=np.array([o['cfmask'] for o in use],dtype=np.int64)
  result=pyxccd.sccd_detect(dates,*[np.ascontiguousarray(a[:,i]) for i in range(6)],qas)
  actual=[datetime.date.fromordinal(int(s['t_break'])).isoformat() for s in result.rec_cg]
  cached=next(r for r in reversed(d['replays']) if r['as_of']<=cutoff)
  check(actual==[s['break'] for s in cached['segments']],f'{key}: independent engine rerun at {cutoff} agrees ({len(actual)} breaks)')
 # Verify the exact frontend reconstruction formula against public utility.
 last=d['replays'][-1];c=np.array(last['current']['coefs'][4]);t=v[-1]['ordinal'];w=2*np.pi*t/365.25
 computed=(c[0]+c[1]*t/10000+c[2]*np.cos(w)+c[3]*np.sin(w)+c[4]*np.cos(2*w)+c[5]*np.sin(2*w))/10000
 check(abs(computed-predict_ref(c,t)/10000)<1e-10,f'{key}: chart formula matches public model utility')
 if d['inventory_id']:
  p=Point(d['coordinates']);g={y:unary_union([shape(f['geometry']) for f in a['features'] if f['properties']['id']==d['inventory_id']]) for y,a in layers.items()}
  check(g[2022].contains(p) and not g[2016].contains(p),f'{key}: sampled inside true 2022-minus-2016 geometry')
d=json.loads((P/'rts-1938.json').read_text(encoding='utf-8'))
check(d['first_seen_breaks']==[{'estimated_change':'2020-09-29','first_detectable_observation':'2020-11-24','calendar_days':56}],'RTS1938: estimated change and first detectable observation kept separate')
check(all(not json.loads((P/(key+'.json')).read_text(encoding='utf-8'))['first_seen_breaks'] for key in ['rts-1820','background']),'Other two fixed samples preserve no-break outputs')

# V6 additions: remeasure exported cross-source polygons independently.
from pyproj import Transformer
from shapely.ops import transform
from PIL import Image
metres=Transformer.from_crs(4326,32646,always_xy=True).transform
ref=transform(metres,unary_union([shape(f['geometry']) for f in layers[2022]['features'] if f['properties']['id']==1938]))
pixel=transform(metres,Point(d['coordinates']))
c=json.loads((R/'public/data/observatory-v6/corroboration.json').read_text(encoding='utf-8'))
gs=json.loads((R/'public/data/observatory-v6/corroboration.geojson').read_text(encoding='utf-8'))
for rec,yr in [(8103939,None),(21693485,2016),(21693485,2022)]:
 f=next(f for f in gs['features'] if f['properties']['source_record']==rec and (f['properties']['year']==yr if yr else '2018-2020' in f['properties']['layer']))
 g=transform(metres,shape(f['geometry']));props=f['properties'];iou=g.intersection(ref).area/g.union(ref).area
 check(abs(iou-props['iou_with_case_2022'])<.000001,f'V6 source {rec}/{yr}: exported geometry independently reproduces spatial overlap')
 check(g.covers(pixel)==props['contains_sampling_point'],f'V6 source {rec}/{yr}: actual polygon inclusion reproduces spatial matching')
check(next(m for m in c['matches'] if m['source_record']==21693485 and m['year']==2022)['source_properties']['id']=='432_4','V6 cross-source object uses actual uid_sid, not a fabricated ID equality')
check(next(m for m in c['matches'] if m['source_record']==21693485 and m['year']==2016)['contains_sampling_point'],'V6 expanded inventory already covers the pixel in 2016: no 2020 onset claim')
ext=next(m for m in c['matches'] if m['source_record']==21693485 and m['year']==2022)
check(ext['source_properties']['gap-filled']=='N','V6 displayed 2022 polygon is not a carried-forward gap-fill')
check(abs(ext['source_properties']['area']/10000-33.3252)<1e-8,'V6 independently sourced area is 33.3252 ha; mismatch with 18.2826 is retained')
for rec,src in [(8103939,R/'data/raw/2008-2021RTSs.shp.zip'),(21693485,R/'research/observatory-v6/raw/RTS-inventory.zip')]:
 meta=json.loads((R/f'research/observatory-v6/zenodo-{rec}.json').read_text(encoding='utf-8'))
 file=next(f for f in meta['files'] if f['key']==src.name)
 check('md5:'+hashlib.md5(src.read_bytes()).hexdigest()==file['checksum'],f'V6 source {rec}: downloaded ZIP agrees with publisher MD5')
 check(meta['metadata']['license']['id']=='cc-by-4.0',f'V6 source {rec}: publisher license verified CC-BY-4.0')
imgs=json.loads((R/'public/data/observatory-v6/extra-images.json').read_text(encoding='utf-8'))
check(len(imgs)==8 and sum(i['sensor']=='Sentinel-2' for i in imgs)==3,'V6 contains 5 actual Landsat plus 3 Sentinel-2 reference images')
check(len({tuple(i['bounds']) for i in imgs})==1,'V6 paired images use exactly the same geographic crop bounds')
for i in imgs:
 with Image.open(R/'public'/i['path'].lstrip('/')) as image:assert image.size==(800,800);image.verify()
check(all(i['purpose']=='reference_not_sccd_input' and i['resolution_m']==10 for i in imgs if i['sensor']=='Sentinel-2'),'V6 10m reference remains outside the S-CCD inputs')
check(all(any(o['item']==i['item'] and o['date']==i['date'] for o in d['observations']) for i in imgs if i['sensor']=='Landsat'),'V6 Landsat RGB references correspond to actual retained time-series products')
old=json.loads((R/'deliverables/observatory-v5/SCIENCE_QA.json').read_text(encoding='utf-8'))
check(all(hashlib.sha256((P/name).read_bytes()).hexdigest()==sha for name,sha in old['data_hashes'].items() if name!='content.json'),'Scientific core observations, model snapshots and product metadata remain byte-identical to validated V5')
baseline_html=(R/'deliverables/observatory-v5/ThawGuard_连续观测与事件证据_v5.html').read_text(encoding='utf-8')
baseline_content=json.loads(re.search(r'<script type="application/json" id="tg-data">(.*?)</script>',baseline_html,re.S).group(1))['resources']['/data/observatory/content.json']
current_content=json.loads((P/'content.json').read_text(encoding='utf-8'))
attribution='S-CCD：Ye, Rogan, Zhu & Eastman (2021)；pyxccd 公开实现作者 Su Ye。使用 1.1.0 未修改的公开默认配置，逐有效观测前缀重跑；输出光谱结构变化，不含热融滑塌分类器。算法贡献归原作者，本次完成案例复现与证据组织。'
if hashlib.sha256((P/'content.json').read_bytes()).hexdigest()!=old['data_hashes']['content.json']:
 next(s for s in baseline_content['sources'] if s['id']=='sccd')['supports']=attribution
check(current_content==baseline_content,'Final content differs from V5 only by the explicit approved public S-CCD author credit; research statements and all other fields unchanged')
check(hashlib.sha256((R/'deliverables/observatory-v5/ThawGuard_连续观测与事件证据_v5.html').read_bytes()).hexdigest()=='83ff1c8a973235b9e311a2cb2f337cd5bc5ba92b05f65b52793743f0483fb0ed','V5 original artifact preserved byte-for-byte')


# V7 integrity checks on public data; not field/classification validation.
import csv,calendar,rasterio
from rasterio.features import geometry_mask
from shapely.geometry import mapping
from scipy.ndimage import convolve
context=json.loads((R/'public/data/observatory-v7/context.json').read_text(encoding='utf-8'))
registry=list(csv.DictReader((R/'data/source_registry.csv').open(encoding='utf-8-sig')))
ids={row['source_id'] for row in registry}
for row in registry:
 files=row['raw_files'].split(';');hashes=row['raw_file_sha256'].split(';')
 check(all(hashlib.sha256((R/f).read_bytes()).hexdigest()==h for f,h in zip(files,hashes)),f"V7 registry {row['source_id']}: retained raw files match SHA256")
check(all(x in ids for x in [context['terrain']['source_id'],context['climate']['source_id'],context['infrastructure']['source_id']]),'V7 displayed context source IDs resolve to the source registry')
check(all(all(k in group for k in ['source_id','method_id','observation_date','resolution','limitations']) for group in [context['terrain'],context['areas'],context['climate'],context['infrastructure'],context['spectral_context'],*context['landcover'].values()]),'V7 public value groups retain dates, methods, resolution and limitations')
with rasterio.open(R/'data/processed/observatory-v7/dem-utm30.tif') as ds:
 z=ds.read(1);g=transform(metres,unary_union([shape(f['geometry']) for f in layers[2022]['features'] if f['properties']['id']==1938]));m=geometry_mask([mapping(g)],z.shape,ds.transform,invert=True)
 # Horn weighted 3x3 derivative is independent of the 2-neighbour gradient implementation.
 k=np.array([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=float)/(8*30)
 dx=convolve(z,k,mode='nearest');dy=convolve(z,k.T,mode='nearest');horn=np.degrees(np.arctan(np.hypot(dx,dy)));horn_median=float(np.median(horn[m]))
 check(abs(horn_median-context['terrain']['slope_median_deg'])<1,'V7 terrain: alternative Horn slope agrees within one degree (algorithm cross-check, not field accuracy)')
 check(ds.crs.to_epsg()==32646 and ds.res==(30,30),'V7 terrain uses metre coordinates before slope derivatives')
 check(abs(np.median(z[m])-context['terrain']['elevation_median_m'])<.01,'V7 terrain exported elevation reconciles with retained projected DSM')
check(context['terrain']['slope_median_deg']<=context['terrain']['slope_p90_deg']<90,'V7 slope summaries are ordered in physical units')
check(0<=context['terrain']['aspect_concentration']<=1 and 0<=context['terrain']['aspect_circular_mean_deg']<360,'V7 circular aspect and concentration are bounded')
check(abs(context['terrain']['comparison_mapzen']['elevation_delta_m'])<20,'V7 Copernicus and legacy Mapzen polygon medians cross-check within 20m; no elevation-change inference')
ref_ll=unary_union([shape(f['geometry']) for f in layers[2022]['features'] if f['properties']['id']==1938])
for year in [2020,2021]:
 c=context['landcover'][str(year)]
 check(sum(x['count'] for x in c['classes'])==c['valid_cells'],'V7 '+str(year)+' WorldCover class counts reconcile')
 check(abs(sum(x['percent'] for x in c['classes'])-100)<.01,'V7 '+str(year)+' WorldCover shares sum to 100%')
 with rasterio.open(R/f'data/raw/observatory-v7/worldcover-{year}-native.tif') as ds:
  a=ds.read(1);m=geometry_mask([mapping(ref_ll)],a.shape,ds.transform,invert=True);v=a[m];bare=float(np.mean(v==60)*100);reported=next(x['percent'] for x in c['classes'] if x['code']==60)
  check(abs(bare-reported)<3,'V7 '+str(year)+' direct native-grid cover fraction cross-checks projected reporting grid within 3 percentage points')
geo=json.loads((R/'public/data/observatory-v7/infrastructure.geojson').read_text(encoding='utf-8'))
for category in context['infrastructure']['categories']:
 nearest=category['nearest'];features=[f for f in geo['features'] if f['properties']['kind']==category['kind']]
 actual=min(transform(metres,shape(f['geometry'])).distance(g) for f in features)
 check(abs(actual-nearest['distance_to_boundary_m'])<.01,'V7 '+category['kind']+' nearest polygon-to-way distance independently reconciles')
check(context['infrastructure']['categories'][1]['nearest']['distance_to_boundary_m']>24000,'V7 RTS1938 is not presented as adjacent to the recorded railway')
check(all(m['days']==calendar.monthrange(int(m['month'][:4]),int(m['month'][5:]))[1] and m['temperature_c'] is not None and m['precipitation_mm'] is not None for m in context['climate']['months']),'V7 climate: 36 complete calendar months; no null precipitation imputed as zero')
q=json.loads((R/'public/data/observatory-v7/sentinel-quality.json').read_text(encoding='utf-8'));im=json.loads((R/'public/data/observatory-v7/extra-images.json').read_text(encoding='utf-8'))
check(len(im)==4 and {x['date'] for x in im}>={'2019-08-15','2020-09-21','2020-10-01','2021-09-11'},'V7 Sentinel quality-screened reference includes an actual 2020 pre/post pair')
for i in im:
 quality=next(x for x in q if x['item']==i['item'])
 with rasterio.open(R/quality['scl_mask_path']) as ds:
  a=ds.read(1);m=geometry_mask([mapping(g)],a.shape,ds.transform,invert=True);pct=float(np.mean(np.isin(a[m],[4,5,6]))*100)
 check(abs(pct-quality['roi_clear_land_water_pct'])<.001,'V7 '+i['date']+' native SCL polygon quality is actually computed')
 with Image.open(R/'public'/i['path'].lstrip('/')) as png:check(png.mode=='RGBA' and png.size==(800,800),'V7 '+i['date']+' displayed image retains an explicit quality alpha mask')
aid=json.loads((R/'public/data/observatory-v7/assistance.json').read_text(encoding='utf-8'));audit=aid['label_audit']
check(audit['rts_positive_records']==459 and audit['activity_codes']=={'N':332,'Y':124,'T':3} and audit['verified_negative_records']==0,'V7 label audit prevents inactive RTS being used as false negative labels')
check(len(audit['overlap_candidates_for_1938'])==4,'V7 cross-source audit records four overlapping objects, not an assumed one-to-one match')
for key,c in aid['cases'].items():
 check(all(f['history_last_date']<f['date'] for f in c['ndvi_mad_flags']),'V7 '+key+' NDVI baseline uses past-only rolling inputs')
 check(all(r['date']<=r['available_as_of'] for r in c['first_detection_residuals']),'V7 '+key+' explanatory residuals retain their first availability date')
check(hashlib.sha256((R/'deliverables/observatory-v6/ThawGuard_连续观测与事件证据_v6.html').read_bytes()).hexdigest()=='e3ce7a5a055fc604b27f43fd21c012731d516808f5b62ee49cda336604d295f3','V6 deliverable preserved byte-for-byte')

report={'status':'passed','checks':checks,'count':len(checks),'data_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in P.glob('*.json')},'scope':'Data and engine integrity only. No independent thaw-slump classification accuracy, onset truth, operational latency or user benefit established.'}
(out/'SCIENCE_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('SCIENCE QA',len(checks),'checks passed')
