import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';
const file=path.resolve('deliverables/observatory-v7/ThawGuard_连续观测与事件证据_v7.html');
http.createServer(async(req,res)=>{if(req.url==='/'||req.url?.startsWith('/?')){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(await fs.readFile(file))}else{res.writeHead(404);res.end('Not found')}}).listen(4197,'127.0.0.1',()=>console.log('ThawGuard v7: http://127.0.0.1:4197/'));
