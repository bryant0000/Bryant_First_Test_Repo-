/* The room interface for a standalone file: all seats belong to this device. */
(function(root){
'use strict';
const E=typeof module!=='undefined'&&module.exports?require('./engine.js'):root.Cashflow,T=typeof module!=='undefined'&&module.exports?require('./table.js'):root.CashflowTable;
const base={perform:T.perform,end:T.end,chooseDream:T.chooseDream};
const copy=x=>JSON.parse(JSON.stringify(x)),key='cashflow-local-rooms-v1';
const actions=new Set(['roll','deal','buy','donate','dismiss','payDoodad','enterFast','resolveInvestment','acceptSplit','payEvent','acceptLoan','cancelLoan','confirmRelief','completeRecovery','confirmBankruptLoss','confirmChild','confirmSkip','openAssetSale','cancelAssetSale','confirmAssetSale','openDebtReview','cancelDebtReview','confirmDebtReview','openDebtPicker','cancelDebtPicker','changeDebtAmount','openBorrowReview','cancelBorrowReview','confirmBorrowReview','openStock','stockQuantity','cancelStock','confirmStock']);
function fail(message,status=400){throw Object.assign(Error(message),{status})}
class LocalRooms{
 constructor({storage=null,rng=Math.random}={}){this.storage=storage;this.rng=rng;this.rooms={};this.readStorage()}
 readStorage(){if(this.storage)try{const d=JSON.parse(this.storage.getItem(key)||'null');if(d?.version===1&&d.rooms)this.rooms=d.rooms}catch{}}
 save(){if(this.storage)try{this.storage.setItem(key,JSON.stringify({version:1,rooms:this.rooms}))}catch{this.storage=null}}
 log(r,author,message,kind='action'){r.chat.push({id:++r.chatRevision,author,message,kind});r.chat=r.chat.slice(-200)}
 view(r){const seat=r.game?r.game.active:0,g=r.game?copy(r.game):null;if(g)g.decks={};return {id:r.id,name:r.name,capacity:r.capacity,private:!!r.password,version:r.version,host:0,seat,local:true,players:r.seats.map((s,i)=>({seat:i,name:s.name,ready:s.ready,left:false,away:false})),game:g,chat:copy(r.chat),chatRevision:r.chatRevision}}
 async request(route,body,token){this.readStorage();const parts=route.split('/').filter(Boolean);
  if(!parts.length){if(body===undefined)return{rooms:Object.values(this.rooms).map(r=>({id:r.id,name:r.name,capacity:r.capacity,players:r.seats.length,private:!!r.password,started:!!r.game}))};const capacity=Number(body.capacity),name=String(body.name||'').trim().slice(0,8);if(!name)fail('请填写房间名称');if(!Number.isInteger(capacity)||capacity<1||capacity>6)fail('支持 1 至 6 人');if(Object.keys(this.rooms).length>=24)fail('本机房间已满');const id='local-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,9),r={id,name,capacity,password:String(body.password||'').slice(0,4),token:'device-'+id,version:1,seats:Array.from({length:capacity},(_,i)=>({name:i?'玩家 '+(i+1):String(body.playerName||'玩家 1').slice(0,8),jobId:E.randomCareer(this.rng),ready:true})),game:null,chat:[],chatRevision:0};this.rooms[id]=r;this.save();return{...this.view(r),token:r.token}}
  const existing=this.rooms[parts[0]];if(!existing)fail('房间不存在',404);
  if(parts[1]==='join'){if(existing.password!==String(body?.password||''))fail('房间密码不正确',403);return{...this.view(existing),token:existing.token}}
  if(token!==existing.token)fail('房间会话已失效',401);if(parts.length===1)return this.view(existing);
  const r=copy(existing),op=parts[1];if(op!=='chat'&&body?.version!==r.version)fail('房间状态已更新，请重试',409);
  if(op==='leave')return{left:true};
  if(op==='chat'){const message=String(body.message||'').trim();if(!r.game||!message||message.length>256)fail('请输入 1 至 256 字的消息');this.log(r,r.seats[r.game.active].name,message,'chat')}
  else if(op==='rename'){if(r.game)fail('开始后不能改名');r.seats[0].name=String(body.name||'玩家 1').slice(0,8)}
  else if(op==='ready'){if(r.game)fail('游戏已经开始');r.seats[0].ready=body.ready===true}
  else if(op==='start'){if(r.game)fail('游戏已经开始');if(r.seats.some(p=>!p.ready))fail('等待玩家准备');r.game=T.create(r.seats.map(s=>({name:s.name,jobId:s.jobId,dreamId:0})),{rulesProfile:E.REFERENCE_PROFILE,chooseDreamsOnTurn:true});this.log(r,'系统','游戏开始')}
  else if(op==='action'){
   const g=r.game;if(!g)fail('游戏尚未开始');if(g.over||g.players.some(p=>p.won))fail('本局已经结束');const action=body.action,args=Array.isArray(body.args)?body.args:[],p=g.players[g.active],n=p.history.length;if(args.length>3)fail('操作参数无效');
   if(action==='chooseDream')base.chooseDream(g,args[0]);else if(action==='cycleDream'){if(!g.ui||![-1,1].includes(args[0]))fail('当前不能切换梦想');p.dreamId=(p.dreamId+args[0]+E.dreams.length)%E.dreams.length}else if(action==='end')base.end(g);else{if(!actions.has(action))fail('未知游戏操作');if(action==='roll')base.perform(g,action,args[0],this.rng);else base.perform(g,action,...args)}
   for(const h of p.history.slice(0,Math.max(0,p.history.length-n)).reverse())this.log(r,p.name,h.text);if(action==='end')this.log(r,p.name,'结束回合');
  }else fail('未知房间操作',404);
  if(op!=='chat')r.version++;this.rooms[r.id]=r;this.save();return this.view(r);
 }
}
if(typeof module!=='undefined'&&module.exports)module.exports={LocalRooms};else root.CashflowLocalRooms=LocalRooms;
})(globalThis);
