'use strict';
const http=require('node:http');
const fs=require('node:fs/promises');
const path=require('node:path');
const {Rooms,handler}=require('./rooms.cjs');
const rooms=new Rooms({file:process.env.CASHFLOW_ROOMS_FILE||path.join(__dirname,'../.cashflow/rooms.json')}),handleRooms=handler(rooms);
const root=path.resolve(__dirname,'..');
const args=process.argv.slice(2);
function option(name,fallback){const i=args.indexOf('--'+name);return i<0?fallback:args[i+1]}
const port=Number(option('port',process.env.PORT||3000));
const host=option('host','0.0.0.0');
if(!Number.isInteger(port)||port<1||port>65535){console.error('Invalid port');process.exit(1)}
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.cjs':'text/plain; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8','.zip':'application/zip','.svg':'image/svg+xml','.png':'image/png','.mp3':'audio/mpeg','.otf':'font/otf'};
const server=http.createServer(async(req,res)=>{
 if(await handleRooms(req,res))return;
 if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{'Allow':'GET, HEAD'});res.end();return}
 let pathname;try{pathname=decodeURIComponent(new URL(req.url,'http://local').pathname)}catch{res.writeHead(400);res.end('Bad request');return}
 if(pathname==='/healthz'){res.writeHead(200,{'Content-Type':'application/json'});res.end(req.method==='HEAD'?'':'{"status":"ok"}');return}
 if(pathname.endsWith('/'))pathname+='index.html';
 const filename=path.resolve(root,'.'+pathname);
 if(!filename.startsWith(root+path.sep)||pathname.split('/').some(p=>p.startsWith('.'))){res.writeHead(403);res.end('Forbidden');return}
 try{
  const real=await fs.realpath(filename);if(!real.startsWith(root+path.sep)){res.writeHead(403);res.end('Forbidden');return}
  const stat=await fs.stat(real);if(!stat.isFile()){res.writeHead(404);res.end('Not found');return}
  const data=await fs.readFile(real);res.writeHead(200,{'Content-Type':types[path.extname(real)]||'application/octet-stream','Content-Length':data.length,'Cache-Control':'no-cache','X-Content-Type-Options':'nosniff'});res.end(req.method==='HEAD'?undefined:data);
 }catch(error){res.writeHead(['ENOENT','ENOTDIR'].includes(error.code)?404:500);res.end(error.code==='ENOENT'?'Not found':'Cannot serve file')}
});
server.on('error',error=>{console.error(error.code==='EADDRINUSE'?`Port ${port} is already in use. Choose another port with --port.`:error.message);process.exit(1)});
const presenceTimer=setInterval(()=>rooms.expireAbsent().catch(error=>console.error('Cannot save room presence:',error.message)),5000);presenceTimer.unref();
rooms.load().then(()=>server.listen(port,host,()=>console.log(`CASHFLOW server listening on ${host}:${port}`))).catch(error=>{console.error('Cannot load saved game rooms:',error.message);process.exitCode=1});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)));
