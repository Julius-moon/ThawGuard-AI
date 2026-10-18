"""Small read-only HTTPS Range opener for GDAL when Windows curl TLS fails."""
import io,requests,re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
UA='ThawGuard-public-data-audit/7.0 (noncommercial scientific research; one Beiluhe case)'
class HTTPRangeFile(io.RawIOBase):
 def __init__(self,url):
  super().__init__();self.url=url;self.pos=0;self.block=262144;self.cache={};self.session=requests.Session();self.session.headers['User-Agent']=UA;self.session.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,status_forcelist=[500,502,503,504])))
  r=self.session.get(url,headers={'Range':'bytes=0-0'},timeout=45);r.raise_for_status()
  if r.status_code!=206:raise OSError('Public server did not support HTTP Range; refusing whole-tile download')
  self.length=int(r.headers['Content-Range'].split('/')[-1])
 def readable(self):return True
 def seekable(self):return True
 def writable(self):return False
 def tell(self):return self.pos
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.length+offset
  return self.pos
 def read(self,size=-1):
  if size<0:size=self.length-self.pos
  if size>16000000:raise OSError('Refusing unexpected full raster read')
  end=min(self.length,self.pos+size);parts=[]
  while self.pos<end:
   start=self.pos//self.block*self.block
   if start not in self.cache:
    stop=min(self.length-1,start+self.block-1)
    r=self.session.get(self.url,headers={'Range':f'bytes={start}-{stop}'},timeout=55);r.raise_for_status()
    if r.status_code!=206 or not r.headers.get('Content-Range','').startswith(f'bytes {start}-'):raise OSError('Range mismatch: '+str(r.headers.get('Content-Range')))
    self.cache[start]=r.content
   block=self.cache[start];offset=self.pos-start;n=min(end-self.pos,len(block)-offset)
   if n<=0:raise OSError('Unexpected truncated Range response')
   parts.append(block[offset:offset+n]);self.pos+=n
  return b''.join(parts)
 def readinto(self,buffer):
  b=self.read(len(buffer));buffer[:len(b)]=b;return len(b)
