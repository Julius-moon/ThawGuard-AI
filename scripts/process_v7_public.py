"""Metric terrain, fixed-footprint land cover, OSM distances and dated context."""
from pathlib import Path
import json,datetime,hashlib,csv,collections
import numpy as np,rasterio
from rasterio.warp import calculate_default_transform,reproject,Resampling
from rasterio.features import geometry_mask
from shapely.geometry import shape,mapping,LineString,Point
from shapely.ops import unary_union,transform,nearest_points
from pyproj import Transformer
R=Path(__file__).resolve().parents[1];D=R/'data/raw/observatory-v7';P=R/'public/data/observatory-v7';P.mkdir(parents=True,exist_ok=True);C=R/'data/processed/observatory-v7';C.mkdir(parents=True,exist_ok=True)
tm=Transformer.from_crs(4326,32646,always_xy=True).transform;tl=Transformer.from_crs(32646,4326,always_xy=True).transform
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,q):p.write_text(json.dumps(q,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
layers={y:load(R/f'public/data/layers/rts-{y}.geojson') for y in range(2016,2023)}
g={y:transform(tm,unary_union([shape(f['geometry']) for f in a['features'] if f['properties']['id']==1938])) for y,a in layers.items()};ref=g[2022]
point=load(R/'public/data/observatory/rts-1938.json');pixel=transform(tm,Point(point['coordinates']))
def projected(file,res,method):
 with rasterio.open(file) as ds:
  tr,w,h=calculate_default_transform(ds.crs,32646,ds.width,ds.height,*ds.bounds,resolution=res)
  a=np.zeros((h,w),dtype='float32' if method==Resampling.bilinear else 'uint8')
  reproject(rasterio.band(ds,1),a,src_transform=ds.transform,src_crs=ds.crs,dst_transform=tr,dst_crs=32646,resampling=method)
  return a,tr
z,tr=projected(D/'cop-dem-glo30-native.tif',30,Resampling.bilinear)
dy,dx=np.gradient(z,30.,30.);slope=np.degrees(np.arctan(np.hypot(dx,dy)));aspect=np.degrees(np.arctan2(-dx,dy))%360
mask=geometry_mask([mapping(ref)],z.shape,tr,invert=True);near=geometry_mask([mapping(ref.buffer(250))],z.shape,tr,invert=True)
angles=np.deg2rad(aspect[mask&(slope>=1)]);s=np.sin(angles).mean();co=np.cos(angles).mean();concentration=float(np.hypot(s,co));direction=float(np.degrees(np.arctan2(s,co))%360)
old=load(R/'public/data/workflow-terrain.json')['sites']['1938']
terrain={'source_id':'cop-dem-glo30-aws-2022','method_id':'utm30-bilinear-central-gradient-v1','observation_date':'2010–2015 acquisition; AWS object 2022-05-09','resolution':'nominal 30 m DSM; native 1 arc-second; computation grid 30 m','crs':'EPSG:32646','vertical_datum':'EGM2008 orthometric heights (m)','geometry_reference':'original inventory ID 1938 / 2022 polygon','n_cells':int(mask.sum()),'elevation_median_m':round(float(np.median(z[mask])),2),'slope_median_deg':round(float(np.median(slope[mask])),3),'slope_p90_deg':round(float(np.quantile(slope[mask],.9)),3),'aspect_circular_mean_deg':round(direction,2),'aspect_concentration':round(concentration,4),'aspect_n_cells':int(len(angles)),'local_relief_p95_p05_m':round(float(np.quantile(z[near],.95)-np.quantile(z[near],.05)),2),'local_relief_scope':'2022 polygon buffered by 250 m','sampling_buffer22m_mean_elevation_m':round(float(z[~geometry_mask([mapping(pixel.buffer(22))],z.shape,tr)].mean()),2),'comparison_mapzen':{'elevation_median_m':old['elevation_m'],'slope_median_deg':old['slope_deg'],'steepest_cell_aspect_deg':old['aspect_deg'],'elevation_delta_m':round(float(np.median(z[mask]))-old['elevation_m'],2),'note':'Different vertical datum/source, grid and sampling; old steepest-cell aspect is not the new circular mean.'},'limitations':'Static edited radar DSM, not current field survey or bare-earth DTM. Resampling creates no extra spatial detail. Flat cells below 1 degree excluded from aspect mean. No DEM differencing or erosion volume.'}
for name,a in [('dem',z),('slope',slope.astype('float32')),('aspect',aspect.astype('float32'))]:
 with rasterio.open(C/(name+'-utm30.tif'),'w',driver='GTiff',height=a.shape[0],width=a.shape[1],count=1,dtype=a.dtype,crs=32646,transform=tr,compress='deflate') as ds:ds.write(a,1)
classes={10:('乔木','#006400'),20:('灌丛','#ffbb22'),30:('草地','#c4c663'),40:('耕地','#f096ff'),50:('建设用地','#ed645b'),60:('裸地／稀疏植被','#a99d88'),70:('冰雪','#edf5ef'),80:('永久水体','#387fb2'),90:('草本湿地','#409a8f'),95:('红树林','#00cf75'),100:('苔藓与地衣','#d7cda3')}
cover={}
for year in [2020,2021]:
 a,t=projected(D/f'worldcover-{year}-native.tif',10,Resampling.nearest);m=geometry_mask([mapping(ref)],a.shape,t,invert=True);v=a[m];valid=v[v>0];values,counts=np.unique(valid,return_counts=True)
 cover[str(year)]={'source_id':f'worldcover-{year}','method_id':'utm10-nearest-fixed-2022-mask-v1','observation_date':str(year),'resolution':'nominal 10 m; native 0.3 arc-second; reporting grid 10 m','reference':'fixed original 2022 polygon (post-hoc context)','valid_cells':int(len(valid)),'masked_cells':int(m.sum()),'classified_area_ha':round(len(valid)*.01,4),'classes':[{'code':int(k),'name':classes.get(int(k),('未知','#999'))[0],'color':classes.get(int(k),('未知','#999'))[1],'count':int(n),'area_ha':round(int(n)*.01,4),'percent':round(float(n/len(valid)*100),3)} for k,n in zip(values,counts)],'limitations':'Pixel-center raster area estimate, not original vector area. 2020 v100 and 2021 v200 use different algorithm versions. Class differences are not attributed to thaw slump or carbon loss.'}
osm=load(D/'osm-25000m.json');features=[]
for e in osm['elements']:
 coords=[[v['lon'],v['lat']] for v in e.get('geometry',[]) if v.get('lon') is not None]
 if len(coords)<2:continue
 line=LineString(coords);metric=transform(tm,line);tags=e.get('tags',{});kind='道路' if 'highway' in tags else '铁路' if 'railway' in tags else '水系';dist=metric.distance(ref);p1,p2=nearest_points(ref,metric)
 features.append({'type':'Feature','geometry':mapping(line),'properties':{'osm_id':e['id'],'osm_version':e.get('version'),'osm_timestamp':e.get('timestamp'),'kind':kind,'name':tags.get('name') or tags.get('ref') or tags.get('highway') or tags.get('waterway') or tags.get('railway'),'tags':tags,'distance_to_boundary_m':round(dist,2),'nearest_connector':mapping(transform(tl,LineString([p1,p2]))),'source_id':'osm-beiluhe-20261018','method_id':'utm46-polygon-to-way-distance-v1','observation_date':osm['osm3s']['timestamp_osm_base'],'resolution':'OSM vector; positional precision and completeness not guaranteed','limitations':'OSM way records are not counts of independent facilities. Geometric separation is not a failure probability or runout path.'}})
features.sort(key=lambda f:f['properties']['distance_to_boundary_m']);dump(P/'infrastructure.geojson',{'type':'FeatureCollection','features':features})
nearest=[]
for kind in ['道路','铁路','水系']:
 rows=[f['properties'] for f in features if f['properties']['kind']==kind];within=[f for f in features if f['properties']['kind']==kind and transform(tm,shape(f['geometry'])).distance(pixel)<=25000]
 nearest.append({'kind':kind,'way_records_25km':len(within),'nearest':rows[0] if rows else None})
infra={'source_id':'osm-beiluhe-20261018','method_id':'utm46-polygon-to-way-distance-v1','observation_date':osm['osm3s']['timestamp_osm_base'],'resolution':'vector; variable mapping detail','query_radius_m':25000,'query_center':point['coordinates'],'counts_basis':'unique OSM way records intersecting radius from sampling point; not unique roads/facilities','categories':nearest,'g109_nearest':next((f['properties'] for f in features if f['properties']['tags'].get('ref')=='G109'),None),'limitations':'Current OSM snapshot is post-hoc spatial context, not a historical 2020 facility survey. Missing OSM records do not imply no infrastructure. Euclidean distances do not establish exposure by flow paths or engineering risk.'}
cl=load(D/'era5-land-native-daily.json');rain=load(D/'era5-precip-native-daily.json');daily={**cl['daily'],**rain['daily']};months=collections.defaultdict(list)
for i,day in enumerate(daily['time']):months[day[:7]].append(i)
monthly=[]
for m,ix in sorted(months.items()):
 ts=[daily['temperature_2m_mean'][i] for i in ix];ps=[daily['precipitation_sum'][i] for i in ix]
 monthly.append({'month':m,'days':len(ix),'temperature_c':round(float(np.mean(ts)),2) if all(v is not None for v in ts) else None,'precipitation_mm':round(float(np.sum(ps)),2) if all(v is not None for v in ps) else None})
climate={'source_id':'openmeteo-era5land-native-temperature+era5-precipitation','method_id':'complete-daily-to-calendar-month-v1','observation_date':'2019-01-01/2021-12-31','resolution':'ERA5-Land temperature 0.1 degree; ERA5 precipitation 0.25 degree; elevation downscaling disabled','grid_coordinates':[cl['longitude'],cl['latitude']],'precipitation_grid_coordinates':[rain['longitude'],rain['latitude']],'api_elevation_m':None,'months':monthly,'limitations':'Open-Meteo daily aggregation, not direct GEE monthly asset. ERA5-Land does not provide precipitation in this API: precipitation is explicitly from ERA5, at coarser resolution. No station validation or event-cause attribution.'}
indices=[]
for year in [2019,2020,2021]:
 rows=[o for o in point['observations'] if o['used_in_model'] and o['platform']=='landsat-8' and o['date'][:4]==str(year) and '06-01'<=o['date'][5:]<='09-30']
 def index(o,a,b):return (o['values'][a]-o['values'][b])/(o['values'][a]+o['values'][b])
 indices.append({'year':year,'n':len(rows),'dates':[o['date'] for o in rows],'ndvi_median':round(float(np.median([o['ndvi'] for o in rows])),4),'nbr_median':round(float(np.median([index(o,3,5) for o in rows])),4),'ndwi_median':round(float(np.median([index(o,1,3) for o in rows])),4),'swir1_median':round(float(np.median([o['values'][4] for o in rows])),4)})
spectral={'source_id':'landsat-c2l2-fixed-pixel','method_id':'landsat8-jun-sep-valid-median-v1','observation_date':'2019/2020/2021 June–September','resolution':'single Landsat 30 m pixel','years':indices,'limitations':'Same sensor and seasonal window, variable dates and sample counts. Pixel index differences are not polygon vegetation loss or proof of causation.'}
areas={str(y):{'attribute_ha':sum(f['properties']['area_m2']/10000 for f in a['features'] if f['properties']['id']==1938),'projected_geometry_ha':g[y].area/10000} for y,a in layers.items()}
summary={'schema':'thawguard-public-context-v7','case_key':'rts-1938','terrain':terrain,'landcover':cover,'infrastructure':infra,'climate':climate,'spectral_context':spectral,'areas':{'source_id':'xia-annual-10928346','method_id':'source-area-plus-utm46-geometry-v1','observation_date':'2016–2022','resolution':'third-party vector interpretation','years':areas,'net_attribute_ha_2016_2022':areas['2022']['attribute_ha']-areas['2016']['attribute_ha'],'geometry_added_2016_2022_ha':g[2022].difference(g[2016]).area/10000,'geometry_removed_2016_2022_ha':g[2016].difference(g[2022]).area/10000,'limitations':'Attribute areas and projected geometry areas differ slightly due to source area processing. Net area is not erosion volume, vegetation loss or carbon flux.'}}
dump(P/'context.json',summary)
print(json.dumps({'terrain':terrain,'landcover':cover,'infrastructure':nearest,'indices':indices},ensure_ascii=True)[:11000])
