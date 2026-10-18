"""Public, credential-free input acquisition. Retain native raster clips and metadata."""
from pathlib import Path
import json,datetime,hashlib,os,traceback,concurrent.futures
import requests
R=Path(__file__).resolve().parents[1];D=R/'data/raw/observatory-v7';D.mkdir(parents=True,exist_ok=True)
def save(n,x):(D/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def get(url,params=None,timeout=65):
 r=requests.get(url,params=params,timeout=timeout);r.raise_for_status();return r
point=json.loads((R/'public/data/observatory/rts-1938.json').read_text(encoding='utf-8'));bounds=point['bounds']
def raster_clip(name,url,bbox):
 import rasterio
 from rasterio.windows import from_bounds,Window
 f=D/(name+'.tif')
 if f.exists():return str(f)
 with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_CONNECTTIMEOUT='20',GDAL_HTTP_TIMEOUT='45',GDAL_HTTP_MAX_RETRY='0'):
  from public_range_reader import HTTPRangeFile
  with rasterio.open(name+'.tif',opener=lambda path,mode='rb':HTTPRangeFile(url)) as ds:
   win=from_bounds(*bbox,ds.transform).round_offsets().round_lengths()
   win=Window(win.col_off-4,win.row_off-4,win.width+8,win.height+8).intersection(Window(0,0,ds.width,ds.height))
   a=ds.read(window=win);profile=ds.profile.copy();profile.update(width=a.shape[2],height=a.shape[1],transform=ds.window_transform(win),driver='GTiff',compress='deflate')
   with rasterio.open(f,'w',**profile) as out:out.write(a)
   save(name+'-metadata.json',{'source_url':url,'download_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_crs':str(ds.crs),'source_shape':[ds.height,ds.width],'source_transform':list(ds.transform),'window':[win.col_off,win.row_off,win.width,win.height],'clip_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'clip_bounds':list(rasterio.transform.array_bounds(a.shape[1],a.shape[2],profile['transform'])),'method':'native-grid window read; no resampling in raw clip'})
 return str(f)
def dem():
 url='https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N35_00_E092_00_DEM/Copernicus_DSM_COG_10_N35_00_E092_00_DEM.tif'
 # Covers the existing three sample positions and enough slope context.
 return raster_clip('cop-dem-glo30-native',url,[92.65,35.065,92.74,35.105])
def cover(year,version):
 url=f'https://esa-worldcover.s3.eu-central-1.amazonaws.com/{version}/{year}/map/ESA_WorldCover_10m_{year}_{version}_N33E090_Map.tif'
 return raster_clip(f'worldcover-{year}-native',url,bounds)
def osm():
 query='[out:json][timeout:50];(way(around:25000,35.07607472715217,92.72564269377199)[highway];way(around:25000,35.07607472715217,92.72564269377199)[railway];way(around:25000,35.07607472715217,92.72564269377199)[waterway];);out meta geom;'
 f=D/'osm-25000m.json'
 if f.exists():return 'cached '+str(f)
 for endpoint in ['https://overpass.private.coffee/api/interpreter','https://overpass-api.de/api/interpreter','https://overpass.nchc.org.tw/api/interpreter']:
  try:
   response=requests.get(endpoint,params={'data':query},headers={'User-Agent':'ThawGuard-public-data-audit/7.0 (noncommercial scientific research; one Beiluhe case)'},timeout=65);response.raise_for_status();q=response.json();assert 'elements' in q
   save(f.name,q);save('osm-query.json',{'endpoint':endpoint,'query':query,'download_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'license':'ODbL-1.0','copyright':'© OpenStreetMap contributors','data_osm_base':q.get('osm3s',{}).get('timestamp_osm_base')});return len(q['elements'])
  except Exception as e:print('OSM endpoint',endpoint,type(e).__name__,flush=True)
 raise RuntimeError('No Overpass endpoint returned valid data')
def climate():
 f=D/'era5-land-daily-2019-2021.json'
 if f.exists():return 'cached climate'
 params={'latitude':35.07607472715217,'longitude':92.72564269377199,'start_date':'2019-01-01','end_date':'2021-12-31','daily':'temperature_2m_mean,precipitation_sum','models':'era5_land','timezone':'UTC'}
 url='https://archive-api.open-meteo.com/v1/archive';q=get(url,params).json();assert len(q['daily']['time'])>1000
 save(f.name,q);save('climate-query.json',{'url':url,'params':params,'download_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'license':'CC-BY-4.0','note':'Open-Meteo Historical Weather API requesting ERA5-Land; daily values aggregated locally, not the GEE MONTHLY_AGGR asset.'});return len(q['daily']['time'])
def s2_metadata():
 imgs=json.loads((R/'public/data/observatory-v6/extra-images.json').read_text(encoding='utf-8'))
 for im in imgs:
  if im['sensor']=='Sentinel-2':
   f=D/(im['item']+'.json')
   if not f.exists():save(f.name,get(im['source_url']).json())
 return '3 existing Sentinel metadata retained'
jobs={'dem':dem,'cover2020':lambda:cover(2020,'v100'),'cover2021':lambda:cover(2021,'v200'),'osm':osm,'climate':climate,'s2_metadata':s2_metadata};report={}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 tasks={pool.submit(fn):name for name,fn in jobs.items()}
 for f in concurrent.futures.as_completed(tasks):
  name=tasks[f]
  try:report[name]={'status':'ok','result':f.result()}
  except Exception as e:report[name]={'status':'failed','error':str(e)[:700]}
  print(name,report[name],flush=True);save('acquisition-log.json',report)
