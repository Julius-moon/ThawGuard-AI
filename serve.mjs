// Local read-only fallback: run `node serve.mjs` from this release directory.
import http from 'node:http';
import fs from 'node:fs/promises';
const file=new URL('./index.html',import.meta.url);
http.createServer(async(req,res)=>{
 if(req.method!=='GET'&&req.method!=='HEAD'){res.writeHead(405);res.end();return;}
 if(!['/','/index.html'].includes((req.url||'').split('?')[0])){res.writeHead(404);res.end('Not found');return;}
 try{const content=await fs.readFile(file);res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Length':content.length});res.end(req.method==='HEAD'?undefined:content);}
 catch{res.writeHead(500);res.end('index.html is missing');}
}).listen(8000,'127.0.0.1',()=>console.log('ThawGuard V7 final: http://127.0.0.1:8000/'));
