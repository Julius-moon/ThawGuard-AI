"""Reproducible public S-CCD execution and strict observation-prefix replay.

No unpublished team parameters. S-CCD public package defaults, not the team's
thaw-slump classifier, and not an implementation of the full 2014 CCDC chain.
"""
from pathlib import Path
import json,datetime,hashlib,collections,warnings
import numpy as np
import pyxccd

R=Path(__file__).resolve().parents[1];D=R/'research/observatory-v5';P=R/'public/data/observatory'
points=json.loads((P/'sampling.json').read_text(encoding='utf-8'))
def iso(n):return datetime.date.fromordinal(int(n)).isoformat() if int(n)>0 else None
def rounded(a):return np.round(a,6).tolist()
def encode(pack):
 segments=[{'start':iso(s['t_start']),'break':iso(s['t_break']),'n':int(s['num_obs']),'coefs':rounded(s['coefs']),'rmse':rounded(s['rmse'])} for s in pack.rec_cg]
 nrt=None
 if pack.nrt_model.dtype.names:
  m=pack.nrt_model if pack.nrt_model.shape==() else pack.nrt_model[0];names=m.dtype.names
  nrt={'start':iso(int(m['t_start_since1982'])+723742),'coefs':rounded(m['nrt_coefs']),'consecutive_anomalies':int(m['anomaly_conse'])}
 return {'segments':segments,'current':nrt,'mode':int(pack.nrt_mode)}
outputs=[]
for p in points:
 rows=[]
 for f in (D/'pixels').glob('*__'+p['key']+'.json'):
  d=json.loads(f.read_text(encoding='utf-8'))
  # Tier 2 has looser geometric quality; fixed-pixel chronology uses Tier 1 only.
  if not d['item'].endswith('_T1'):continue
  v=d['values'];qa=int(v[6] or 0);sat=int(v[7] or 0)
  old=d['platform'] in ['landsat-4','landsat-5','landsat-7']
  values=[round(float(n)*.0000275-.2,7) if n is not None else None for n in v[:6]]
  if qa&1 or any(n is None or n==0 for n in v[:6]):status='nodata';cf=255
  elif sat:status='saturated';cf=255
  elif qa&8 or qa&2 or (not old and qa&4):status='cloud';cf=4
  elif qa&16:status='shadow';cf=2
  elif qa&32:status='snow';cf=3
  elif any(n<0 or n>1 for n in values):status='range';cf=255
  elif qa&128:status='water';cf=1
  else:status='clear';cf=0
  red,nir=values[2:4];ndvi=round((nir-red)/(nir+red),6) if red is not None and nir is not None and nir+red>0 else None
  rows.append({'date':d['date'],'ordinal':datetime.date.fromisoformat(d['date']).toordinal(),'item':d['item'],'platform':d['platform'],'values':values,'dn':v[:6],'qa_pixel':qa,'qa_radsat':sat,'quality':status,'cfmask':cf,'ndvi':ndvi,'source_url':d['source_url']})
 rows.sort(key=lambda d:(d['date'],d['item']))
 valid=[d for d in rows if d['cfmask'] in [0,1]]
 # Deterministic one acquisition per date; this choice does not inspect change outputs.
 good={}
 for d in rows:d['used_in_model']=False
 for d in valid:
  if d['date'] not in good:good[d['date']]=d;d['used_in_model']=True
 valid=list(good.values());dates=np.array([d['ordinal'] for d in valid],dtype=np.int64)
 vals=np.array([[round(v*10000) for v in d['values']] for d in valid],dtype=np.int64)
 qa=np.array([d['cfmask'] for d in valid],dtype=np.int64)
 replays=[];first_seen={};errors=[]
 for n in range(60,len(valid)+1):
  try:
   with warnings.catch_warnings():
    warnings.simplefilter('ignore');pack=pyxccd.sccd_detect(dates[:n],*[np.ascontiguousarray(vals[:n,k]) for k in range(6)],qa[:n])
   snap={'as_of':valid[n-1]['date'],'n':n,**encode(pack)}
   for seg in snap['segments']:
    if seg['break']:first_seen.setdefault(seg['break'],snap['as_of'])
   replays.append(snap)
  except Exception as e:errors.append({'as_of':valid[n-1]['date'],'error':str(e)[:200]})
 result={**p,'observations':rows,'valid_count':len(valid),'quality_counts':dict(collections.Counter(x['quality'] for x in rows)),'replays':replays,'first_seen_breaks':[{'estimated_change':b,'first_detectable_observation':t,'calendar_days':(datetime.date.fromisoformat(t)-datetime.date.fromisoformat(b)).days} for b,t in sorted(first_seen.items())],'errors':errors}
 (P/(p['key']+'.json')).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print(p['key'],'total',len(rows),'valid',len(valid),'snapshots',len(replays),'breaks',result['first_seen_breaks'],'errors',errors[:2],flush=True)
 outputs.append({k:result[k] for k in ['key','inventory_id','coordinates','name','role','selection','bounds','valid_count','quality_counts','first_seen_breaks']})
meta={'algorithm':'S-CCD','implementation':'pyxccd','version':pyxccd.__version__,'configuration':'unmodified public defaults','data':'USGS Landsat Collection 2 Level 2 Tier 1 only; public Planetary Computer STAC + point API','period':'1995–2025','bands':['blue','green','red','nir08','swir16','swir22'],'scaling':'reflectance = DN × 0.0000275 − 0.2; algorithm input reflectance × 10000 rounded','qa':'Tier 1 only. Exclude fill, saturation/terrain occlusion, cloud, dilated cloud, L8/9 cirrus, shadow, snow and reflectance outside [0,1]; retain clear/water and label separately','replay':'Re-run on each valid-observation prefix after first 60 valid dates; no observations after as_of supplied','identification':'Spectral changes only; inventory-guided sampling is not independent thaw-slump identification or validation','timeliness':'Historical observation-time replay; actual catalog publication/processing latency unavailable, so not operational lead-time evidence','cross_sensor':'TM/ETM+/OLI C2 common-band values; no additional cross-sensor harmonization, sensor transitions may produce apparent changes','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'points':outputs}
(P/'index.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
(D/'processed_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.glob('*.json')},indent=2),encoding='utf-8')
