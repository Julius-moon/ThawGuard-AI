"""Package only curated final files; never upload or overwrite the V7 candidate."""
from pathlib import Path
import argparse,hashlib,json,zipfile,re
R=Path(__file__).resolve().parents[1]
O=R/'deliverables/ThawGuard-AI'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');args=parser.parse_args()
assert sha(R/'deliverables/observatory-v7/ThawGuard_连续观测与事件证据_v7.html')=='62c58ada54357c9848571276de2d5cdddeaffb6b3096536381245b9452f4bad9','V7 candidate changed'
assert sha(O/'index.html')==json.loads((O/'MANIFEST.json').read_text(encoding='utf-8'))['sha256'],'Final HTML does not match manifest'
secret=re.compile(r'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{30,}|sk-proj-[A-Za-z0-9_-]{25,}|[?&](?:sig|access_token|refresh_token)=[A-Za-z0-9%_+/.=-]{15,}',re.I)
def check_entry(name,b):
 assert not any(x in Path(name).parts for x in ['node_modules','.venv','.git','.aws']),name
 assert Path(name).suffix.lower() not in ['.pptx','.ppt','.pfx','.pem','.key'],name
 assert not Path(name).name.startswith('.env'),name
 if Path(name).suffix in ['.json','.geojson','.csv','.md','.html','.py','.mjs','.ts','.tsx','.txt']:
  s=b.decode('utf-8',errors='ignore')
  # Binary image payloads can coincidentally contain token-shaped characters.
  # Keep metadata, URLs, source and every other text field in the scan.
  s=re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+','[embedded binary image]',s)
  assert not secret.search(s),f'Potential credential in {name}'
files=sorted(p for p in O.rglob('*') if p.is_file())
for p in files:check_entry(p.relative_to(O).as_posix(),p.read_bytes())
manifest=json.loads((O/'MANIFEST.json').read_text(encoding='utf-8'))
manifest.update({'version':'v7-final','date':'2026-10-18','html_frozen':True,'physical_devices_tested':1,'second_physical_device':'not tested; manual checklist in docs/VALIDATION_REPORT.md','remote_repository_created':False,'files':{p.relative_to(O).as_posix():sha(p) for p in files if p.name!='MANIFEST.json'}})
(O/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
release=R/'deliverables/ThawGuard_v7_final_release.zip'
with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,'ThawGuard-AI/'+p.relative_to(O).as_posix())
packages=[release]
if args.source:
 base=R/'deliverables/ThawGuard_v7_源码与公开数据.zip'
 overrides={}
 for folder in ['src/observatory-v7','public/data/observatory-v7']:
  for p in (R/folder).glob('*'):
   if p.is_file():overrides[p.relative_to(R).as_posix()]=p.read_bytes()
 for name in ['scripts/package_observatory_v7.py','scripts/test_observatory_v7.mjs','scripts/validate_observatory_v7.py','scripts/release_final.py','scripts/test_final_release.mjs','scripts/verify_final_preview.mjs','public/data/observatory/content.json','README.md','STATUS.md']:
  p=R/name;overrides[name]=p.read_bytes()
 for p in O.rglob('*'):
  if p.is_file():overrides[p.relative_to(R).as_posix()]=p.read_bytes()
 package=json.loads((R/'package.json').read_text(encoding='utf-8'))
 package['scripts']={k:v for k,v in package['scripts'].items() if k in ['dev','build','preview','preview:observatory','test:observatory','test:science','data:experiment','build:final','preview:final']}
 overrides['package.json']=(json.dumps(package,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 source=R/'deliverables/ThawGuard_v7_final_source.zip'
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in old.namelist():
   if name in overrides:continue
   b=old.read(name);check_entry(name,b);z.writestr(name,b)
  for name,b in sorted(overrides.items()):check_entry(name,b);z.writestr(name,b)
 packages.append(source)
for p in packages:
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
report={'version':'v7-final','date':'2026-10-18','html_sha256':sha(O/'index.html'),'packages':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in packages],'secret_scan':'curated file whitelist plus credential-pattern scan passed; not a substitute for rights review','html_frozen':True,'second_physical_device_tested':False,'published':False}
(R/'deliverables/ThawGuard_v7_final_RELEASE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
