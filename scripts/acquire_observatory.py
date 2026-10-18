"""Acquire public Landsat C2 L2 observations at fixed, provenance-bound locations.

Run in project .venv. Uses public STAC + Planetary Computer pixel API, no key.
Sampling is retrospective and inventory-guided; not an independent accuracy test.
Individual responses are cached, making interruption and retry safe.
"""
from pathlib import Path
import json, time, datetime, concurrent.futures, threading, hashlib
import requests
from shapely.geometry import shape, Point
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/observatory-v5'; CACHE=OUT/'pixels'; CACHE.mkdir(parents=True,exist_ok=True)
PUB=ROOT/'public/data/observatory'; PUB.mkdir(parents=True,exist_ok=True)
STAC='https://planetarycomputer.microsoft.com/api/stac/v1'
API='https://planetarycomputer.microsoft.com/api/data/v1/item'
ASSETS=['blue','green','red','nir08','swir16','swir22','qa_pixel','qa_radsat']
local=threading.local()
def session():
 if not hasattr(local,'s'):local.s=requests.Session()
 return local.s
def get(url,params=None):
 for retry in range(4):
  try:
   r=session().get(url,params=params,timeout=60);r.raise_for_status();return r
  except Exception:
   if retry==3:raise
   time.sleep(1+retry*3)
layers={y:json.loads((ROOT/f'public/data/layers/rts-{y}.geojson').read_text()) for y in range(2016,2023)}
all_inventory=unary_union([shape(f['geometry']) for a in layers.values() for f in a['features']])
points=[]
for i in [1820,1938]:
 g=unary_union([shape(f['geometry']) for f in layers[2022]['features'] if f['properties']['id']==i])
 old=unary_union([shape(f['geometry']) for f in layers[2016]['features'] if f['properties']['id']==i])
 p=g.difference(old).representative_point()
 points.append({'key':f'rts-{i}','inventory_id':i,'coordinates':[p.x,p.y],'name':f'RTS {i} · 扩张区采样像元','role':'inventory_guided_expansion','selection':'2022边界减去2016边界后的内部代表点；按清单后验选点，不作盲测','bounds':[g.bounds[0]-.004,g.bounds[1]-.004,g.bounds[2]+.004,g.bounds[3]+.004]})
# Deterministic background candidate; outside all available boundaries, not ground truth.
for p in [Point(92.675+i*.004,35.09+j*.004) for j in range(15) for i in range(15)]:
 if all_inventory.distance(p)>.003:
  points.append({'key':'background','inventory_id':None,'coordinates':[p.x,p.y],'name':'邻近背景对照','role':'unlabelled_background','selection':'固定候选序列中首个距2016–2022全部清单边界>0.003度的点；不是实地确认阴性','bounds':[p.x-.007,p.y-.005,p.x+.007,p.y+.005]});break
assert len(points)==3
(PUB/'sampling.json').write_text(json.dumps(points,ensure_ascii=False,indent=2),encoding='utf-8')
cat=OUT/'catalog.json'
if cat.exists():items=json.loads(cat.read_text())
else:
 q={'collections':'landsat-c2-l2','bbox':'92.65,35.07,92.74,35.10','datetime':'1995-01-01T00:00:00Z/2025-12-31T23:59:59Z','limit':1000}
 d=get(STAC+'/search',q).json();items=d['features']
 while next((l for l in d.get('links',[]) if l['rel']=='next'),None):
  link=next(l for l in d['links'] if l['rel']=='next');d=get(link['href']).json();items.extend(d['features'])
 # One WRS path/row avoids using duplicate overlapping scene footprints as time gain.
 items=[x for x in items if str(x['properties'].get('landsat:wrs_path'))=='138' and str(x['properties'].get('landsat:wrs_row')).lstrip('0')=='36' and all(k in x['assets'] for k in ASSETS)]
 items.sort(key=lambda x:(x['properties']['datetime'],x['id']))
 cat.write_text(json.dumps(items),encoding='utf-8')
print('CATALOG',len(items),'POINTS',[(p['key'],p['coordinates']) for p in points],flush=True)
def one(job):
 x,p=job;dest=CACHE/(x['id']+'__'+p['key']+'.json')
 if dest.exists():return True
 q=[('collection','landsat-c2-l2'),('item',x['id'])]+[('assets',a) for a in ASSETS]
 try:
  r=get(API+'/point/'+','.join(map(str,p['coordinates'])),q)
  d=r.json();d.update(item=x['id'],date=x['properties']['datetime'][:10],point=p['key'],platform=x['properties']['platform'],source_url=next(l['href'] for l in x['links'] if l['rel']=='self'))
  dest.write_text(json.dumps(d),encoding='utf-8');return True
 except Exception as e:
  print('FAILED',x['id'],p['key'],str(e)[:100],flush=True);return False
jobs=[(x,p) for x in items for p in points]
done=0;failed=0
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for success in ex.map(one,jobs):
  done+=1;failed+=not success
  if done%100==0:print('PROGRESS',done,'/',len(jobs),'failed',failed,flush=True)
report={'catalog_items':len(items),'point_requests':len(jobs),'failed':failed,'catalog_sha256':hashlib.sha256(cat.read_bytes()).hexdigest(),'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'All indexed dates, one WRS 138/036, 1995–2025; no scene-cloud prefilter; QA_PIXEL and QA_RADSAT retained','selection_bias':'Inventory-guided case selection; background is unlabelled; no classification accuracy can be inferred'}
(OUT/'acquisition.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(report,flush=True)
