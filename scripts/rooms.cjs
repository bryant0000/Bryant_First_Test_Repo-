'use strict';
const crypto=require('node:crypto'),fs=require('node:fs/promises'),path=require('node:path');
const E=require('../engine.js'),T=require('../table.js');
const clone=x=>JSON.parse(JSON.stringify(x));
const actions=new Set(['roll','deal','buy','sell','borrow','repay','donate','dismiss','payDoodad','enterFast','resolveInvestment','acceptSplit','payEvent','acceptLoan','cancelLoan','confirmRelief','completeRecovery','confirmBankruptLoss','confirmChild','confirmSkip','openAssetSale','cancelAssetSale','confirmAssetSale','openDebtReview','cancelDebtReview','confirmDebtReview','openDebtPicker','cancelDebtPicker','changeDebtAmount','openBorrowReview','cancelBorrowReview','confirmBorrowReview','openStock','stockQuantity','cancelStock','confirmStock']);
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const passwordHash=(value,salt)=>crypto.scryptSync(value,salt,32).toString('hex');
function fail(message,status=400){throw Object.assign(new Error(message),{status})}
function text(value,max,fallback=''){return String(value??fallback).trim().slice(0,max)||fallback}
function same(a,b){return typeof a==='string'&&a.length===b.length&&crypto.timingSafeEqual(Buffer.from(a),Buffer.from(b))}
class Rooms{
 constructor({file=null,rng=Math.random,now=Date.now,presenceTimeout=90000}={}){this.file=file;this.rng=rng;this.now=now;this.presenceTimeout=presenceTimeout;this.presenceDirty=false;this.rooms=new Map();this.writing=Promise.resolve()}
 async load(){if(!this.file)return;try{const data=JSON.parse(await fs.readFile(this.file,'utf8'));if(data.version!==1||!Array.isArray(data.rooms))throw Error('Invalid room store');for(const room of data.rooms)if(room.id&&Array.isArray(room.seats)&&room.capacity>=1&&room.capacity<=6){for(const seat of room.seats)seat.lastSeen=this.now();this.rooms.set(room.id,room)}}catch(e){if(e.code!=='ENOENT')throw e}}
 async persist(){if(!this.file)return;const data=JSON.stringify({version:1,rooms:[...this.rooms.values()]});this.writing=this.writing.catch(()=>{}).then(async()=>{await fs.mkdir(path.dirname(this.file),{recursive:true});await fs.writeFile(this.file+'.tmp',data,{mode:0o600});await fs.rename(this.file+'.tmp',this.file)});await this.writing}
 list(){return [...this.rooms.values()].filter(r=>!r.game&&r.seats.some(s=>!s.left)).map(r=>({id:r.id,name:r.name,capacity:r.capacity,players:r.seats.filter(s=>!s.left&&!s.away).length,private:!!r.passwordHash,version:r.version}))}
 find(id){const r=this.rooms.get(id);if(!r)fail('房间不存在或已关闭',404);return r}
 member(r,token){if(!token)fail('请先加入房间',401);const tokenHash=hash(token);const index=r.seats.findIndex(s=>!s.left&&same(s.tokenHash,tokenHash));if(index<0)fail('房间会话已失效',401);const seat=r.seats[index];seat.lastSeen=this.now();if(seat.away){seat.away=false;if(r.game){r.game.players[index].inactive=false;this.appendLog(r,seat.name,'重新连接','action')}r.version++;this.presenceDirty=true}return index}
 view(r,seat){const game=r.game?clone(r.game):null;if(game)game.decks={};return {id:r.id,name:r.name,capacity:r.capacity,version:r.version,chatRevision:r.chatRevision||0,chat:clone(r.chat||[]),seat,host:r.host,players:r.seats.map((s,i)=>({seat:i,name:s.name,ready:s.ready,left:!!s.left,away:!!s.away})),game}}
 newSeat(name,token){return {name:text(name,8,'玩家'),ready:false,left:false,away:false,lastSeen:this.now(),tokenHash:hash(token),jobId:E.randomCareer(this.rng)}}
 async create(body){const capacity=Number(body.capacity);if(!Number.isInteger(capacity)||capacity<1||capacity>6)fail('房间支持 1 至 6 人');if(this.rooms.size>=200)fail('房间数量已满，请稍后再试',503);const token=crypto.randomBytes(24).toString('hex'),id=crypto.randomBytes(6).toString('hex'),salt=crypto.randomBytes(16).toString('hex'),password=String(body.password||'');if(password.length>128)fail('房间密码过长');const r={id,name:text(body.name,32,'现金流房间'),capacity,host:0,seats:[this.newSeat(body.playerName,token)],salt,passwordHash:password?passwordHash(password,salt):null,version:1,chatRevision:0,chat:[],game:null};r.seats[0].ready=true;this.rooms.set(id,r);await this.persist();return {...this.view(r,0),token}}
 async join(id,body){const r=this.find(id);if(r.game)fail('游戏已经开始');const password=String(body.password||'');if(password.length>128)fail('房间密码不正确',403);if(r.passwordHash&&!same(r.passwordHash,passwordHash(password,r.salt)))fail('房间密码不正确',403);let seat=r.seats.findIndex(s=>s.left||s.away);if(seat<0)seat=r.seats.length;if(seat>=r.capacity)fail('房间人数已满');const token=crypto.randomBytes(24).toString('hex');r.seats[seat]=this.newSeat(body.playerName,token);if(seat===r.host)r.seats[seat].ready=true;r.version++;await this.persist();return {...this.view(r,seat),token}}
 read(id,token){const r=this.find(id);return this.view(r,this.member(r,token))}
 async expireAbsent(){let changed=this.presenceDirty;this.presenceDirty=false;const now=this.now();for(const r of this.rooms.values()){let dirty=false;r.seats.forEach((seat,index)=>{if(!seat.left&&!seat.away&&now-seat.lastSeen>=this.presenceTimeout){seat.away=true;seat.ready=false;if(r.game){r.game.players[index].inactive=true;this.appendLog(r,seat.name,'暂时离线，未结算的事件已保留','action')}dirty=true}});if(dirty){r.version++;changed=true}}if(changed)await this.persist()}
 appendLog(r,author,message,kind){r.chatRevision=(r.chatRevision||0)+1;(r.chat||(r.chat=[])).push({id:r.chatRevision,author,message,kind});if(r.chat.length>200)r.chat.splice(0,r.chat.length-200)}
 async command(id,token,operation,body={}){
  const r=this.find(id),seat=this.member(r,token);if(operation!=='chat'&&(!Number.isInteger(body.version)||body.version!==r.version))fail('房间状态已更新，请重试本次操作',409);
  if(operation==='chat'){if(!r.game)fail('游戏尚未开始');const message=String(body.message||'').trim();if(!message||message.length>256)fail('聊天内容需要 1 至 256 个字符');this.appendLog(r,r.seats[seat].name,message,'chat');await this.persist();return this.view(r,seat)}
  else if(operation==='rename'){if(r.game)fail('游戏开始后不能修改名字');r.seats[seat].name=text(body.name,8,'玩家')}
  else if(operation==='ready'){if(r.game)fail('游戏已经开始');r.seats[seat].ready=body.ready===true}
  else if(operation==='start'){
   if(seat!==r.host)fail('只有房主可以开始游戏',403);if(r.game)fail('游戏已经开始');const present=r.seats.filter(s=>!s.left&&!s.away);if(present.length!==r.capacity||present.some(s=>!s.ready))fail('等待所有玩家加入并准备');
   r.seats=present;r.host=r.seats.findIndex(s=>same(s.tokenHash,hash(token)));r.game=T.create(r.seats.map(s=>({name:s.name,jobId:s.jobId,dreamId:0})),{rulesProfile:E.REFERENCE_PROFILE,chooseDreamsOnTurn:true});this.appendLog(r,'系统','游戏开始','action');
  }else if(operation==='leave'){
   if(!r.game&&seat===r.host){this.rooms.delete(id);await this.persist();return {left:true}}
   r.seats[seat].left=true;if(r.game)this.appendLog(r,r.seats[seat].name,'离开房间','action');if(!r.seats.some(s=>!s.left)){this.rooms.delete(id);await this.persist();return {left:true}}
   if(r.host===seat)r.host=r.seats.findIndex(s=>!s.left);
   if(r.game){r.game.players[seat].inactive=true;if(r.game.active===seat&&!r.game.over&&!r.game.players.some(p=>p.won)){r.game.ui=null;r.game.players[seat].pending=null;r.game.rolled=true;if(r.seats.some(s=>!s.left&&!s.away))T.end(r.game);else{r.game.active=r.seats.findIndex(s=>!s.left);r.game.rolled=false;T.prepareTurn(r.game)}}}
  }else if(operation==='action'){
   if(!r.game)fail('游戏尚未开始');if(r.game.active!==seat)fail('还没有轮到你',403);if(r.game.over||r.game.players.some(p=>p.won))fail('本局已经结束');
   const previousHistoryLength=r.game.players[seat].history.length;const g=clone(r.game),args=Array.isArray(body.args)?body.args:[];if(args.length>3)fail('操作参数无效');
   if(body.action==='chooseDream')T.chooseDream(g,args[0]);else if(body.action==='cycleDream'){
    if(g.ui?.introIndex!==seat||![-1,1].includes(args[0]))fail('当前不能切换梦想');g.players[seat].dreamId=(g.players[seat].dreamId+args[0]+E.dreams.length)%E.dreams.length;
   }else if(body.action==='end')T.end(g);else{
    if(!actions.has(body.action)||['borrow','repay','sell'].includes(body.action))fail('未知游戏操作');if(body.action==='openDebtReview'&&!['debtPicker','insolvent','debtReview'].includes(g.players[seat].pending?.kind))fail('请先选择偿还负债');if(body.action==='roll'&&(args.length!==1||![1,2,3].includes(args[0])))fail('骰子参数无效');
    if(['deal','buy','sell','donate','dismiss','payDoodad','enterFast','resolveInvestment','acceptSplit','payEvent','acceptLoan','cancelLoan','confirmRelief','completeRecovery','confirmBankruptLoss','confirmChild','confirmSkip','openAssetSale','cancelAssetSale','confirmAssetSale','cancelDebtReview','confirmDebtReview','cancelDebtPicker','changeDebtAmount','cancelBorrowReview','confirmBorrowReview','openStock','stockQuantity','cancelStock','confirmStock'].includes(body.action)&&!g.players[seat].pending)fail('当前没有待处理的事件');
    T.perform(g,body.action,...args);
   }
   r.game=g;const added=g.players[seat].history.length-previousHistoryLength;for(const h of g.players[seat].history.slice(0,Math.max(0,added)).reverse())this.appendLog(r,r.seats[seat].name,h.text,'action');if(body.action==='end')this.appendLog(r,r.seats[seat].name,'结束回合','action');
  }else fail('未知房间操作',404);
  r.version++;await this.persist();return operation==='leave'?{left:true}:this.view(r,seat);
 }
}
async function body(req){const chunks=[];let bytes=0;for await(const chunk of req){bytes+=chunk.length;if(bytes>8192)fail('请求内容过长',413);chunks.push(chunk)}try{const text=Buffer.concat(chunks).toString('utf8');return text?JSON.parse(text):{}}catch{fail('请求格式无效')}}
function json(res,status,data){const encoded=JSON.stringify(data);res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(encoded)}
function handler(rooms){return async(req,res)=>{let url;try{url=new URL(req.url,'http://local')}catch{return false}if(!url.pathname.startsWith('/api/'))return false;
 try{
  if(req.method==='POST'&&req.headers.origin){const origin=new URL(req.headers.origin);if(![req.headers.host,...String(req.headers['x-forwarded-host']||'').split(',').map(x=>x.trim())].includes(origin.host))fail('请求来源不匹配',403)}
  const token=(req.headers.authorization||'').replace(/^Bearer /,'');const parts=url.pathname.split('/').filter(Boolean);if(parts[1]!=='rooms')fail('接口不存在',404);
  let result,status=200;if(parts.length===2&&req.method==='GET')result={rooms:rooms.list()};else if(parts.length===2&&req.method==='POST'){result=await rooms.create(await body(req));status=201}
  else if(parts.length===3&&req.method==='GET')result=rooms.read(parts[2],token);
  else if(parts.length===4&&req.method==='POST')result=parts[3]==='join'?await rooms.join(parts[2],await body(req)):await rooms.command(parts[2],token,parts[3],await body(req));else fail('接口不存在',404);
  json(res,status,result);
 }catch(error){json(res,error.status||400,{error:error.message||'无法完成操作'})}return true;
}}
module.exports={Rooms,handler};
