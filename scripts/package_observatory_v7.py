from pathlib import Path
import json,base64,hashlib,re,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--out-dir',default='deliverables/observatory-v7')
parser.add_argument('--filename',default='ThawGuard_连续观测与事件证据_v7.html')
parser.add_argument('--title',default='ThawGuard AI · 连续观测与事件证据 v7')
args=parser.parse_args()
R=Path(__file__).resolve().parents[1];build=R/'.build/observatory-v7';out=R/args.out_dir;out.mkdir(parents=True,exist_ok=True)
paths=['summary.json','sites.geojson','workflow-terrain.json']+[f'layers/rts-{y}.geojson' for y in range(2016,2023)]
paths += ['observatory/'+f.name for f in (R/'public/data/observatory').glob('*.json') if f.name!='sampling.json']
resources={'/data/'+p:json.loads((R/'public/data'/p).read_text(encoding='utf-8')) for p in paths}
resources.update({'/data/observatory-v6/'+f.name:json.loads(f.read_text(encoding='utf-8')) for f in (R/'public/data/observatory-v6').glob('*.json')});resources['/data/observatory-v6/corroboration.geojson']=json.loads((R/'public/data/observatory-v6/corroboration.geojson').read_text(encoding='utf-8'));resources.update({'/data/observatory-v7/'+f.name:json.loads(f.read_text(encoding='utf-8')) for f in (R/'public/data/observatory-v7').glob('*') if f.suffix in ['.json','.geojson']});images={}
used={i['path'].lstrip('/') for i in resources['/data/observatory/images.json']+resources['/data/observatory-v6/extra-images.json']+resources['/data/observatory-v7/extra-images.json']}
for f in [R/'public/images/beiluhe-nasa.jpg',*[R/'public'/n for n in sorted(used)]]:images['/images/'+f.relative_to(R/'public/images').as_posix()]='data:image/'+('jpeg' if f.suffix=='.jpg' else 'png')+';base64,'+base64.b64encode(f.read_bytes()).decode()
payload=json.dumps({'resources':resources,'images':images},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
js=(build/'app.js').read_text(encoding='utf-8').replace('</script','<\\/script');css='\n'.join(p.read_text(encoding='utf-8') for p in build.glob('*.css'))
bootstrap="const embedded=JSON.parse(document.getElementById('tg-data').textContent);window.__TG_IMAGES=embedded.images;window.fetch=async(input)=>{const key=typeof input==='string'?input:input.url;if(Object.prototype.hasOwnProperty.call(embedded.resources,key))return new Response(JSON.stringify(embedded.resources[key]),{status:200,headers:{'Content-Type':'application/json'}});throw new Error('离线包中没有此资源：'+key)};"
html='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="从卫星观测到热融滑塌事件证据的科研原型"><title>ThawGuard AI · 连续观测与事件证据 v7</title><style>'+css+'</style></head><body><div id="root"></div><script type="application/json" id="tg-data">'+payload+'</script><script>'+bootstrap+'\n'+js+'</script></body></html>'
notices=R/'public/data/observatory-v7/third-party-notices.txt'
if notices.exists():html=html.replace('</body>', '<script type="text/plain" id="tg-third-party-notices">'+notices.read_text(encoding='utf-8').replace('</script','<\\/script')+'</script></body>')
html=html.replace('<title>ThawGuard AI · 连续观测与事件证据 v7</title>','<title>'+args.title+'</title>')
dest=out/args.filename;dest.write_text(html,encoding='utf-8')
manifest={'artifact':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'data_resources':len(resources),'images':len(images),'observations':sum(len(resources[f'/data/observatory/{k}.json']['observations']) for k in ['rts-1820','rts-1938','background']),'offline':True,'algorithm':'S-CCD public defaults / pyxccd 1.1.0','scientific_claims':'Spectral-change retrospective reproduction only; not independent RTS accuracy, nowcasting, or future forecast.'}
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False))
