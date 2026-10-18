"""Separate ERA5-Land temperature from ERA5 precipitation; native grids."""
from pathlib import Path
import requests,json,datetime
R=Path(__file__).resolve().parents[1];D=R/'data/raw/observatory-v7';D.mkdir(parents=True,exist_ok=True)
for model,variable,name in [('era5_land','temperature_2m_mean','era5-land-native-daily.json'),('era5','precipitation_sum','era5-precip-native-daily.json')]:
 if (D/name).exists():continue
 params={'latitude':35.07607472715217,'longitude':92.72564269377199,'start_date':'2019-01-01','end_date':'2021-12-31','daily':variable,'models':model,'timezone':'UTC','elevation':'nan','cell_selection':'nearest'}
 url='https://archive-api.open-meteo.com/v1/archive';r=requests.get(url,params=params,timeout=60);r.raise_for_status();q=r.json();assert len(q['daily']['time'])==1096 and all(v is not None for v in q['daily'][variable])
 (D/name).write_text(json.dumps(q,ensure_ascii=False),encoding='utf-8');(D/(name+'.query.json')).write_text(json.dumps({'url':url,'params':params,'download_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False),encoding='utf-8')
 print(model,len(q['daily']['time']))
