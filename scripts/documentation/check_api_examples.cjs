/* In-memory own-room traffic for document contract review; no publisher or persistent state. */
const http=require('node:http'),fs=require('node:fs');
const {Rooms,handler}=require('../rooms.cjs');
(async()=>{
 const store=new Rooms({rng:()=>0}),route=handler(store),server=http.createServer((req,res)=>route(req,res));
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const base='http://127.0.0.1:'+server.address().port,rows=[];
 async function call(method,path,body,token,expected,raw){
  const headers={};if(token)headers.Authorization='Bearer '+token;if(body!==undefined||raw!==undefined)headers['Content-Type']='application/json';
  const response=await fetch(base+path,{method,headers,body:raw===undefined?(body===undefined?undefined:JSON.stringify(body)):raw});const data=await response.json();
  if(response.status!==expected)throw Error(method+' '+path+' expected '+expected+' got '+response.status+' '+JSON.stringify(data));
  rows.push({method:method.toLowerCase(),path:path.replace(/\/api\/rooms\/[^/]+/,'/api/rooms/{id}'),status:String(response.status),requestBody:body,data});return data;
 }
 try{
  await call('GET','/api/rooms',undefined,null,200);
  const host=await call('POST','/api/rooms',{name:'文档契约验证',capacity:2,playerName:'甲',password:'1234'},null,201);
  await call('GET','/api/rooms/'+host.id,undefined,null,401);
  await call('POST','/api/rooms/'+host.id+'/join',{playerName:'乙',password:'bad'},null,403);
  const guest=await call('POST','/api/rooms/'+host.id+'/join',{playerName:'乙',password:'1234'},null,200);
  let view=await call('POST','/api/rooms/'+host.id+'/ready',{version:guest.version,ready:true},guest.token,200);
  view=await call('POST','/api/rooms/'+host.id+'/rename',{version:view.version,name:'甲2'},host.token,200);
  view=await call('POST','/api/rooms/'+host.id+'/start',{version:view.version},host.token,200);
  await call('POST','/api/rooms/'+host.id+'/action',{version:view.version,action:'chooseDream',args:[0]},guest.token,403);
  view=await call('POST','/api/rooms/'+host.id+'/action',{version:view.version,action:'chooseDream',args:[0]},host.token,200);
  view=await call('POST','/api/rooms/'+host.id+'/chat',{message:'文档契约验证消息'},guest.token,200);
  await call('POST','/api/rooms/'+host.id+'/action',{version:view.version-1,action:'roll',args:[1]},host.token,409);
  view=await call('POST','/api/rooms/'+host.id+'/action',{version:view.version,action:'roll',args:[1]},host.token,200);
  await call('GET','/api/rooms/'+host.id,undefined,guest.token,200);
  await call('POST','/api/rooms/'+host.id+'/leave',{version:view.version},guest.token,200);
  const latest=await call('GET','/api/rooms/'+host.id,undefined,host.token,200);
  await call('POST','/api/rooms/'+host.id+'/leave',{version:latest.version},host.token,200);
  await call('GET','/api/rooms/missing',undefined,host.token,404);
  await call('POST','/api/rooms',undefined,null,400,'{');
  await call('POST','/api/rooms',{capacity:1,name:'a'.repeat(9000)},null,413);
  // Tokens only exist in this ephemeral validation file; never copied into the deliverables.
  fs.writeFileSync('/tmp/cashflow-contract-responses.json',JSON.stringify(rows));console.log('Validated HTTP statuses for '+rows.length+' isolated API exchanges.');
 }finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve))}
})().catch(e=>{console.error(e);process.exitCode=1});
