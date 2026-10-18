from pathlib import Path
import sys,json,zipfile,io,re,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'.python-deps'))
import shapefile
sys.path.pop(0)
from shapely.geometry import shape,Point,mapping
from shapely.ops import transform,unary_union
from pyproj import Transformer,CRS
to_m=Transformer.from_crs(4326,32646,always_xy=True).transform
to_ll=Transformer.from_crs(32646,4326,always_xy=True).transform
def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
p=json.loads((R/'public/data/observatory/rts-1938.json').read_text(encoding='utf-8'))
point=transform(to_m,Point(p['coordinates']))
targets={y:unary_union([transform(to_m,shape(f['geometry'])) for f in json.loads((R/f'public/data/layers/rts-{y}.geojson').read_text(encoding='utf-8'))['features'] if f['properties']['id']==1938]) for y in range(2016,2023)}
out=[];geo=[]
for record,src in [(8103939,R/'data/raw/2008-2021RTSs.shp.zip'),(21693485,R/'research/observatory-v6/raw/RTS-inventory.zip')]:
 z=zipfile.ZipFile(src)
 for n in sorted(n for n in z.namelist() if n.endswith('.shp') and not n.startswith('__MACOSX')):
  year=int(re.search(r'RTSs-(\d{4})',n)[1]) if record==21693485 else None
  crs=CRS.from_wkt(z.read(n[:-3]+'prj').decode())
  assert crs.to_epsg()==32646
  r=shapefile.Reader(**{k:io.BytesIO(z.read(n[:-3]+k)) for k in ['shp','shx','dbf']})
  # Match the fixed 2022 case footprint, not the old inventory ID string.
  best=None
  for sr in r.iterShapeRecords():
   g=shape(sr.shape.__geo_interface__)
   if not g.is_valid:g=g.buffer(0)
   intersection=g.intersection(targets[2022]).area
   if not intersection:continue
   iou=intersection/g.union(targets[2022]).area
   if best is None or iou>best[0]:best=(iou,g,sr.record.as_dict())
  if best:
   iou,g,props=best
   rec={'source_record':record,'layer':n,'year':year,'source_properties':props,'area_geometry_ha':round(g.area/10000,6),'iou_with_case_2022':round(iou,6),'case_2022_covered_fraction':round(g.intersection(targets[2022]).area/targets[2022].area,6),'contains_sampling_point':g.covers(point),'distance_to_sampling_point_m':round(g.distance(point),3),'match_rule':'maximum polygon intersection-over-union with fixed 2022 ID 1938 geometry in EPSG:32646'}
   if year in targets:rec['iou_with_same_year_case']=round(g.intersection(targets[year]).area/g.union(targets[year]).area,6)
   out.append(rec)
   if record==8103939 or year in [2016,2019,2020,2021,2022,2024]:geo.append({'type':'Feature','geometry':mapping(transform(to_ll,g)),'properties':rec})
result={'schema':'thawguard-spatial-corroboration-v6','case_key':'rts-1938','coordinates':p['coordinates'],'reference_source':'https://zenodo.org/records/10928346','reference_year':2022,'metric_crs':'EPSG:32646','sources':[{'record':8103939,'url':'https://zenodo.org/records/8103939','license':'CC-BY-4.0','md5':hashlib.md5((R/'data/raw/2008-2021RTSs.shp.zip').read_bytes()).hexdigest(),'note':'Yang et al. inventory explicitly cites earlier Luo and Xia inventories. This is cross-source spatial corroboration, not fully independent ground truth.'},{'record':21693485,'url':'https://zenodo.org/records/21693485','license':'CC-BY-4.0','md5':hashlib.md5((R/'research/observatory-v6/raw/RTS-inventory.zip').read_bytes()).hexdigest(),'note':'Xia et al. extended inventory. IDs use uid_sid, not original ID 1938. Gap-filled entries carry an earlier polygon and are not a fresh observation.'}],'matches':out,'limitations':['Matching uses spatial overlap, never equality of IDs across inventories.','Shared literature and authorship mean independence is not established.','A polygon match corroborates location and footprint, not exact onset, S-CCD accuracy, or future risk.','Gap-filled polygons must not be interpreted as newly observed annual boundaries.']}
dump(R/'public/data/observatory-v6/corroboration.json',result)
dump(R/'public/data/observatory-v6/corroboration.geojson',{'type':'FeatureCollection','features':geo})
for rec in out:
 if rec['source_record']==8103939 or rec['year'] in [2016,2019,2020,2021,2022,2024]:print(rec['source_record'],rec['year'] or rec['layer'],rec['source_properties'],rec['iou_with_case_2022'],rec['contains_sampling_point'])
