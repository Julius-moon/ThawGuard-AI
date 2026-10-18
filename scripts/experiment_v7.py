"""Label audit, causal NDVI baseline, public S-CCD reruns, no fabricated classifier."""
from pathlib import Path
import json,sys,io,zipfile,collections,datetime,hashlib
import numpy as np,pyxccd
from shapely.geometry import shape,Point
from shapely.ops import transform,unary_union
from pyproj import Transformer
R=Path(__file__).resolve().parents[1];P=R/'public/data/observatory-v7';O=R/'deliverables/observatory-v7'
sys.path.insert(0,str(R/'.python-deps'));import shapefile;sys.path.pop(0)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,q):p.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
z=zipfile.ZipFile(R/'data/raw/2008-2021RTSs.shp.zip');n=next(n for n in z.namelist() if '2018-2020' in n and n.endswith('.shp'));r=shapefile.Reader(**{k:io.BytesIO(z.read(n[:-3]+k)) for k in ['shp','shx','dbf']})
counts=collections.Counter(rec.as_dict().get('TYPE') for rec in r.records())
tm=Transformer.from_crs(4326,32646,always_xy=True).transform
ref=transform(tm,unary_union([shape(f['geometry']) for f in load(R/'public/data/layers/rts-2022.geojson')['features'] if f['properties']['id']==1938]))
spatial=[]
for sr in r.iterShapeRecords():
 g=shape(sr.shape.__geo_interface__)
 if not g.is_valid:g=g.buffer(0)
 area=g.intersection(ref).area
 if area>0:spatial.append({'source_id':sr.record.as_dict()['ID'],'TYPE':sr.record.as_dict()['TYPE'],'intersection_m2':round(area,3),'iou':round(area/g.union(ref).area,6),'ref_covered_fraction':round(area/ref.area,6)})
spatial.sort(key=lambda x:-x['iou'])
audit={'source_id':'yang-8103939','method_id':'source-label-and-overlap-audit-v1','observation_date':'2018–2020 inventory; downloaded 2026-10-18','resolution':'interpreted vector polygons','rts_positive_records':len(r),'activity_codes':dict(counts),'verified_negative_records':0,'independent_event_onset_labels':0,'original_inventory_2022_ids_in_window':437,'fixed_pixel_time_series':3,'overlap_candidates_for_1938':spatial,'classification_training_permitted':False,'reason':'All 459 features are thaw-slump records. N means inactive RTS, not non-RTS. Unlisted background is unlabelled. Shared input inventories and inconsistent object boundaries prevent independent event/onset validation. A binary classifier has no verified negative class; fitting pseudo-negatives would not validate RTS identification.','limitations':'Counts audit the available local public sources, not all possible labels worldwide. No accuracy/PR-AUC/confusion matrix claimed.'}
checks=[];cases={}
for key in ['rts-1820','rts-1938','background']:
 d=load(R/f'public/data/observatory/{key}.json');obs=[o for o in d['observations'] if o['used_in_model']];flags=[]
 # Intentionally simple public baseline: previous 20 valid NDVI samples only.
 # Analysts specified the baseline here; not a private laboratory parameter.
 for i,o in enumerate(obs):
  if i<20 or o['ndvi'] is None:continue
  history=np.array([v['ndvi'] for v in obs[i-20:i]],dtype=float);med=float(np.median(history));mad=float(np.median(np.abs(history-med)));scale=max(1.4826*mad,1e-4);score=abs(o['ndvi']-med)/scale
  if score>3:flags.append({'date':o['date'],'ndvi':o['ndvi'],'past_median':med,'past_mad':mad,'standardized_deviation':round(score,5),'history_last_date':obs[i-1]['date']})
 for cutoff in ['2010-12-31','2020-11-23','2020-11-24','2025-12-31']:
  v=[o for o in obs if o['date']<=cutoff];dates=np.asarray([o['ordinal'] for o in v],dtype=np.int64);a=np.asarray([[round(x*10000) for x in o['values']] for o in v],dtype=np.int64);qas=np.asarray([o['cfmask'] for o in v],dtype=np.int64)
  result=pyxccd.sccd_detect(dates,*[np.ascontiguousarray(a[:,i]) for i in range(6)],qas)
  actual=[datetime.date.fromordinal(int(s['t_break'])).isoformat() for s in result.rec_cg];cached=next(s for s in reversed(d['replays']) if s['as_of']<=cutoff)
  assert actual==[s['break'] for s in cached['segments']];checks.append({'case':key,'as_of':cutoff,'valid_n':len(v),'breaks':actual,'status':'reproduced'})
 first=d['first_seen_breaks'][0] if d['first_seen_breaks'] else None;residuals=[]
 if first:
  snap=next(s for s in d['replays'] if s['as_of']==first['first_detectable_observation']);segment=next(s for s in snap['segments'] if s['break']==first['estimated_change']);coefs=np.array(segment['coefs']);rmse=np.array(segment['rmse'])/10000
  for o in obs:
   if first['estimated_change']<=o['date']<=first['first_detectable_observation']:
    n=o['ordinal'];w=2*np.pi*n/365.25;prediction=(coefs[:,0]+coefs[:,1]*n/10000+coefs[:,2]*np.cos(w)+coefs[:,3]*np.sin(w)+coefs[:,4]*np.cos(2*w)+coefs[:,5]*np.sin(2*w))/10000
    residual=(np.array(o['values'])-prediction)/np.maximum(rmse,1e-8)
    residuals.append({'date':o['date'],'item':o['item'],'normalized_residuals':np.round(residual,4).tolist(),'bands_abs_z_ge_3':int((np.abs(residual)>=3).sum()),'available_as_of':snap['as_of']})
 cases[key]={'source_id':'landsat-c2l2-fixed-pixel','method_id':'public-sccd-prefix-plus-ndvi-mad-baseline-v1','observation_date':'1995–2025; each prefix dated separately','resolution':'30 m pixel','valid_n':len(obs),'ndvi_mad_flags':flags,'sccd_final_breaks':[s['break'] for s in d['replays'][-1]['segments'] if s['break']],'first_detection_residuals':residuals,'limitations':'NDVI flags count isolated deviations, whereas S-CCD segments identify sustained multiband structural changes; counts are not directly comparable accuracy measures. No true-negative labels or independent onset truth. Residuals use the segment available at first detection, never shown earlier.'}
dump(P/'assistance.json',{'schema':'thawguard-transparent-assistance-v7','label_audit':audit,'cases':cases,'public_rules':{'baseline':'previous 20 valid NDVI samples; abs(current-median) > 3 * max(1.4826*MAD, 0.0001)','candidate':'Use only S-CCD segments available at selected cutoff. Terrain, maps and land cover are separately dated context, not inputs to past replay.','classification':'No trained binary classifier: public sources contain zero independently verified non-RTS labels.'},'type':'可审计规则辅助判读，非训练分类模型'})
dump(O/'MODEL_RUN.json',{'status':'completed','engine':'pyxccd 1.1.0 public defaults','independent_prefix_reruns':checks,'baseline_flag_counts':{k:len(v['ndvi_mad_flags']) for k,v in cases.items()},'trained_classifier':False,'label_gate':audit,'no_ml_metrics_claimed':True})
(O/'model_run.log').write_text('\n'.join([f"{x['case']} {x['as_of']} n={x['valid_n']} breaks={x['breaks']} {x['status']}" for x in checks])+ '\nClassifier training stopped at verified-label gate: 459 RTS records, 0 verified non-RTS records. Inactive N is not a negative class. No fabricated accuracy.\n',encoding='utf-8')
print('Model audit',len(r),dict(counts),'negative labels',0,'prefix reruns',len(checks),'NDVI flags',{k:len(v['ndvi_mad_flags']) for k,v in cases.items()},'overlap candidates',spatial)
