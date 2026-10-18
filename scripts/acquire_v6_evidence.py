"""Public corroborating inventories and dated 10m imagery; never private inputs."""
from pathlib import Path
import json,requests,hashlib,time
R=Path(__file__).resolve().parents[1];D=R/'research/observatory-v6';RAW=D/'raw';RAW.mkdir(parents=True,exist_ok=True)
P=R/'public/data/observatory-v6';P.mkdir(parents=True,exist_ok=True)
I=R/'public/images/observatory-v6';I.mkdir(parents=True,exist_ok=True)
s=requests.Session()
def get(url,params=None,timeout=90):
 for n in range(3):
  try:
   r=s.get(url,params=params,timeout=timeout);r.raise_for_status();return r
  except Exception:
   if n==2:raise
   time.sleep(1+n*2)
records=[]
for record in ['8103939','21693485']:
 try:
  q=get('https://zenodo.org/api/records/'+record).json();(D/f'zenodo-{record}.json').write_text(json.dumps(q),encoding='utf-8')
  print('RECORD',record,q['metadata'].get('license'),[(f['key'],f['size']) for f in q.get('files',[])],flush=True)
  if record=='21693485':
   for f in q['files']:
    if f['key']=='RTS-inventory.zip':
     dest=RAW/f['key']
     if not dest.exists():dest.write_bytes(get(f['links']['self'],timeout=180).content)
     md5=hashlib.md5(dest.read_bytes()).hexdigest();assert f['checksum']=='md5:'+md5
     print('DOWNLOADED',f['key'],dest.stat().st_size,'MD5 OK',flush=True)
  records.append({'id':record,'license':q['metadata'].get('license'),'title':q['metadata']['title'],'files':[{'name':f['key'],'checksum':f['checksum']} for f in q.get('files',[])]})
 except Exception as e:print('RECORD ERROR',record,str(e)[:200],flush=True)
point=json.loads((R/'public/data/observatory/rts-1938.json').read_text(encoding='utf-8'))
old_images=json.loads((R/'public/data/observatory/images.json').read_text(encoding='utf-8'))
catalog=json.loads((R/'research/observatory-v5/catalog.json').read_text(encoding='utf-8'))
images=[]
def crop(item,collection,assets,key,year,kind,res,stretch=None):
 bounds=point['bounds'];date=item['properties']['datetime'][:10];dest=I/f'{key}-{date}.png'
 args=[('collection',collection),('item',item['id']),*[( 'assets',a) for a in assets],('width',800),('height',800)]
 if stretch:args.append(('rescale',stretch))
 if not dest.exists():dest.write_bytes(get('https://planetarycomputer.microsoft.com/api/data/v1/item/bbox/'+','.join(map(str,bounds))+'.png',args).content)
 assert dest.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
 images.append({'key':'rts-1938','year':year,'date':date,'item':item['id'],'bounds':bounds,'path':'/images/observatory-v6/'+dest.name,'cloud_cover_scene_pct':item['properties'].get('eo:cloud_cover',0),'source_url':next(l['href'] for l in item['links'] if l['rel']=='self'),'sensor':kind,'resolution_m':res,'rendering':'True-color public image crop; scene cloud cover is not ROI quality','purpose':'reference_not_sccd_input' if res==10 else 'landsat_input_context'})
 print('IMAGE',kind,date,len(dest.read_bytes()),flush=True)
# Landsat images before and after 2020, chosen by summer OLI scene cloud ordering.
for year in [2019,2020,2021]:
 options=[x for x in catalog if x['id'].endswith('_T1') and x['properties']['platform'] in ['landsat-8','landsat-9'] and x['properties']['datetime'][:4]==str(year) and 6<=int(x['properties']['datetime'][5:7])<=9]
 options.sort(key=lambda x:(x['properties'].get('eo:cloud_cover',100),x['properties']['datetime']))
 for x in options[:3]:
  try:crop(x,'landsat-c2-l2',['red','green','blue'],'landsat-rts-1938',year,'Landsat',30,'7273,20000');break
  except Exception as e:print('IMAGE ERROR',str(e)[:130],flush=True)
# Exact retained input products around the model break; preserve SLC gaps.
for day in ['2020-09-05','2020-11-24']:
 o=next(o for o in point['observations'] if o['date']==day and o['used_in_model'])
 x=next(x for x in catalog if x['id']==o['item'])
 crop(x,'landsat-c2-l2',['red','green','blue'],'landsat-rts-1938',2020,'Landsat',30,'7273,20000')
for year in [2019,2020,2021]:
 try:
  d=get('https://planetarycomputer.microsoft.com/api/stac/v1/search',{'collections':'sentinel-2-l2a','bbox':','.join(map(str,point['bounds'])),'datetime':f'{year}-06-01T00:00:00Z/{year}-09-30T23:59:59Z','limit':1000}).json()
  (D/f'sentinel-catalog-{year}.json').write_text(json.dumps(d),encoding='utf-8')
  options=sorted(d['features'],key=lambda x:(x['properties'].get('eo:cloud_cover',100),x['properties']['datetime']))
  print('SENTINEL',year,len(options),flush=True)
  for x in options[:4]:
   try:crop(x,'sentinel-2-l2a',['visual'],'sentinel-rts-1938',year,'Sentinel-2',10);break
   except Exception as e:print('SENTINEL ERROR',str(e)[:170],flush=True)
 except Exception as e:print('SENTINEL CATALOG ERROR',str(e)[:200],flush=True)
(P/'extra-images.json').write_text(json.dumps(images,ensure_ascii=False,indent=2),encoding='utf-8')
(D/'public-acquisition.json').write_text(json.dumps({'records':records,'images':len(images)},ensure_ascii=False,indent=2),encoding='utf-8')
