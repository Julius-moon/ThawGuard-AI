"""Validate Sentinel native scene classification and render a clear 2020 pair."""
from pathlib import Path
import json,hashlib,datetime,concurrent.futures
import requests,numpy as np,rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds,reproject,Resampling
from rasterio.transform import from_bounds as transform_from_bounds
from rasterio.features import geometry_mask
from shapely.geometry import shape,mapping
from shapely.ops import unary_union
from pyproj import Transformer
from shapely.ops import transform
from PIL import Image
from public_range_reader import HTTPRangeFile,UA
R=Path(__file__).resolve().parents[1];D=R/'data/raw/observatory-v7';P=R/'public/data/observatory-v7';I=R/'public/images/observatory-v7';I.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,q):p.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
session=requests.Session();session.headers['User-Agent']=UA
point=load(R/'public/data/observatory/rts-1938.json');bounds=point['bounds']
ref=unary_union([shape(f['geometry']) for f in load(R/'public/data/layers/rts-2022.geojson')['features'] if f['properties']['id']==1938]);metric=transform(Transformer.from_crs(4326,32646,always_xy=True).transform,ref)
def request(url,params=None):r=session.get(url,params=params,timeout=60);r.raise_for_status();return r
def clip(item,band):
 f=D/f"{item['id']}-{band}.tif"
 if not f.exists():
  href=item['assets'][band]['href'];signed=request('https://planetarycomputer.microsoft.com/api/sas/v1/sign',{'href':href}).json()['href']
  with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
   with rasterio.open(item['id']+'-'+band+'.tif',opener=lambda path,mode='rb':HTTPRangeFile(signed)) as ds:
    b=transform_bounds(4326,ds.crs,*bounds);w=from_bounds(*b,ds.transform).round_offsets().round_lengths();a=ds.read(1,window=w);pr=ds.profile.copy();pr.update(driver='GTiff',width=a.shape[1],height=a.shape[0],transform=ds.window_transform(w),compress='deflate')
    with rasterio.open(f,'w',**pr) as dst:dst.write(a,1)
 with rasterio.open(f) as ds:return ds.read(1),ds.transform,ds.crs
def quality(item):
 a,t,crs=clip(item,'SCL');assert crs.to_epsg()==32646
 m=geometry_mask([mapping(metric)],a.shape,t,invert=True);v=a[m];keys,counts=np.unique(v,return_counts=True)
 row={'source_id':'sentinel2-l2a-'+item['id'],'method_id':'native-scl20-fixed-2022-mask-v1','item':item['id'],'observation_date':item['properties']['datetime'][:10],'resolution':'RGB 10 m native; SCL 20 m native; 2022 polygon fixed-mask context','processing_baseline':item['properties'].get('s2:processing_baseline'),'scene_cloud_pct':item['properties'].get('eo:cloud_cover'),'roi_scl_counts':{str(k):int(n) for k,n in zip(keys,counts)},'roi_clear_land_water_pct':round(float(np.isin(v,[4,5,6]).mean()*100),3),'roi_cells':int(len(v)),'scl_mask_path':str((D/f"{item['id']}-SCL.tif").relative_to(R)).replace('\\','/'),'source_url':next(l['href'] for l in item['links'] if l['rel']=='self'),'limitations':'SCL is a modelled 20m quality classification, not independent field truth; ROI quality differs from scene cloud percentage. Post-hoc fixed polygon statistics do not enter Landsat S-CCD.'}
 print('SCL',row['observation_date'],row['roi_clear_land_water_pct'],flush=True);return row
existing=[load(f) for f in D.glob('S2*.json') if '-candidate' not in f.name]
quality_rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for row in pool.map(quality,existing):quality_rows.append(row)
# Exact 2020 pre/post reference: evaluate SCL instead of trusting scene cloud.
cat=request('https://planetarycomputer.microsoft.com/api/stac/v1/search',{'collections':'sentinel-2-l2a','bbox':','.join(map(str,bounds)),'datetime':'2020-09-01T00:00:00Z/2020-11-24T23:59:59Z','limit':1000}).json();dump(D/'sentinel-candidates-2020.json',cat)
selected=[]
for before in [True,False]:
 options=[f for f in cat['features'] if (f['properties']['datetime'][:10]<'2020-09-29')==before and f['properties'].get('eo:cloud_cover',100)<40]
 options.sort(key=lambda f:f['properties']['datetime'],reverse=before)
 for item in options[:6]:
  try:
   q=quality(item);quality_rows.append(q);dump(D/(item['id']+'-candidate.json'),item)
   if q['roi_clear_land_water_pct']<90:continue
   selected.append(item);break
  except Exception as e:print('S2 candidate failure',type(e).__name__,str(e)[:100],flush=True)
selected=[i for i in existing if i['properties']['datetime'][:4] in ['2019','2021']]+selected
images=[]
for item in selected:
 bands={b:clip(item,b) for b in ['B04','B03','B02']};rgb=np.stack([bands[b][0] for b in ['B04','B03','B02']],axis=2).astype(float)/10000
 # These pre-2022 products have processing baseline below 04.00; offset=0.
 assert float(item['properties']['s2:processing_baseline'])<4
 rgb=(np.clip((rgb-.04)/.40,0,1)**(1/1.2)*255).astype('uint8');f=I/(item['id']+'.png');Image.fromarray(rgb).resize((800,800),Image.Resampling.NEAREST).save(f)
 # Native crop is rectangular projected UTM, but renderer rectangle must use
 # the same WGS84 bbox as other comparison images. Use public bbox renderer
 # with the identical fixed RGB DN stretch instead of stretching raw cells.
 params=[('collection','sentinel-2-l2a'),('item',item['id']),('assets','B04'),('assets','B03'),('assets','B02'),('rescale','400,4400'),('width',800),('height',800)]
 f.write_bytes(request('https://planetarycomputer.microsoft.com/api/data/v1/item/bbox/'+','.join(map(str,bounds))+'.png',params).content);assert f.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
 scl,st,sc=clip(item,'SCL');mask=np.zeros((800,800),dtype='uint8');reproject(scl,mask,src_transform=st,src_crs=sc,dst_transform=transform_from_bounds(*bounds,800,800),dst_crs=4326,resampling=Resampling.nearest);im=Image.open(f).convert('RGBA');im.putalpha(Image.fromarray(np.where(np.isin(mask,[4,5,6]),255,0).astype('uint8')));im.save(f)
 images.append({'key':'rts-1938','year':int(item['properties']['datetime'][:4]),'date':item['properties']['datetime'][:10],'item':item['id'],'bounds':bounds,'path':'/images/observatory-v7/'+f.name,'source_url':next(l['href'] for l in item['links'] if l['rel']=='self'),'sensor':'Sentinel-2','resolution_m':10,'cloud_cover_scene_pct':item['properties'].get('eo:cloud_cover',0),'rendering':'B04/B03/B02 fixed common DN stretch 400..4400; native SCL 20m nearest-mask classes 4/5/6; bbox 800px rendering adds no detail','purpose':'reference_not_sccd_input'})
dump(P/'sentinel-quality.json',quality_rows);dump(P/'extra-images.json',images);print('S2 complete',len(quality_rows),'quality records',len(images),'new images',flush=True)
