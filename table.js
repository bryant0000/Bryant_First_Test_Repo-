/* Same-device turn order and shared market responses. */
(function(root){
'use strict';
const E=typeof module!=='undefined'&&module.exports?require('./engine.js'):root.Cashflow;
function create(configs,options={}){
 if(!Array.isArray(configs)||configs.length<1||configs.length>6)throw Error('支持 1 至 6 人');
 const g={version:3,ruleset:E.data.revision,players:configs.map((c,i)=>({...E.create(c.jobId==='random'?E.randomCareer(options.rng||Math.random):c.jobId,c.dreamId,options.rulesProfile||null),name:String(c.name||'玩家 '+(i+1)).slice(0,options.rulesProfile===E.REFERENCE_PROFILE?8:16),color:(options.rulesProfile===E.REFERENCE_PROFILE?E.REFERENCE_COLORS:['#f1bd4f','#86b993','#a8abff','#f39a8a','#71c5df','#de94ca'])[i]})),active:0,rolled:false,decks:{},round:1};
 if(options.chooseDreamsOnTurn&&options.rulesProfile===E.REFERENCE_PROFILE){g.dreamSelection='per-turn';for(const p of g.players)p.dreamConfirmed=false;prepareTurn(g)}
 return g;
}
const current=g=>g.players[g.active];
function prepareTurn(g){const s=current(g);if(g.rolled||g.ui||g.over||s.pending)return;if(g.dreamSelection==='per-turn'&&!s.dreamConfirmed){g.ui={introIndex:g.active,step:'dream'};return}advanceQueue(s)}
function chooseDream(g,id){const s=current(g);if(g.dreamSelection!=='per-turn'||g.ui?.introIndex!==g.active||s.dreamConfirmed||!Number.isInteger(id)||!E.dreams[id])throw Error('当前不能选择梦想');s.dreamId=id;s.dreamConfirmed=true;s.history.unshift({turn:s.turn,text:'选定梦想：'+E.dreams[id].name+'。'});g.ui=null;prepareTurn(g)}
function perform(g,action,...args){const s=current(g);if(g.dreamSelection==='per-turn'&&g.ui)throw Error('请先选择自己的梦想');if(action==='roll'&&g.rolled)throw Error('本回合已移动，请先结束回合');if(!E[action])throw Error('未知操作');
 if(action==='buy'&&s.pending?.kind==='fastDeal'&&g.players.some(p=>p!==s&&p.fastAssets.some(a=>a.position===s.pos)))throw Error('该事业已被其他玩家购入');
 const dreamPosition=E.isReference(s)&&s.stage==='fast'&&['buy','dismiss'].includes(action)&&E.data.fast[s.pos].type==='dream'?s.pos:null;
 s.lastGlobal=null;s.decks=g.decks;E[action](s,...args);g.decks=s.decks;if(dreamPosition!==null){for(const p of g.players){if(p!==s&&E.data.dreams[p.dreamId].position===dreamPosition){p.dreamMultiplier=(p.dreamMultiplier||1)+1;p.history.unshift({turn:p.turn,text:`其他玩家经过你的梦想，价格倍数增加到 ${p.dreamMultiplier}。`})}}}if(action==='roll')g.rolled=true;
 const event=s.lastGlobal;if(event&&E.isReference(s)){for(const p of g.players){if(p===s)continue;if(event.kind==='split'||event.kind==='stockQuote'||event.kind==='market'&&event.card.global)(p.cardQueue||(p.cardQueue=[])).push(JSON.parse(JSON.stringify(event)))}s.lastGlobal=null}else if(event){for(const p of g.players){if(p===s||p.stage!=='rat'||p.won||p.bankrupt)continue;if(event.kind==='split'){const a=event.offer;E.splitShares(p,a.key,a.factor);p.history.unshift({turn:p.turn,text:`共享事件：${a.key} 股数乘 ${a.factor}。`})}else if(event.card.global&&['startup','sellmultiply'].includes(event.card.mode)){const pending=p.pending;E.applyMarket(p,event.card);p.pending=pending;E.check(p)}}s.lastGlobal=null}
 if(action==='confirmBankruptLoss'){g.rolled=true;end(g)}
 if(action==='enterFast'&&E.isReference(s)){g.rolled=true;end(g)}
 if(action==='confirmSkip'&&E.isReference(s)){g.rolled=true;end(g)}
 if(E.isReference(s)&&s.processingQueue&&!s.pending)advanceQueue(s);
 return s;
}
function advanceQueue(s){
 s.processingQueue=false;
 if(!E.isReference(s))return;
 s.cardQueue=s.cardQueue||[];
 if(s.stage!=='rat'||s.bankrupt){s.cardQueue=[];return}
 if(s.skip>0){s.cardQueue=[];s.pending={kind:'skipTurn',title:s.skipReason==='bankruptcy'?'破产重整休整':'失业休整',text:`本回合暂停行动，还需休整 ${s.skip} 回合。确认后轮到下一位玩家。`};return}
 while(s.cardQueue.length){
  const event=s.cardQueue.shift(),a=event.offer,c=event.card;
  if(event.kind==='split'||event.kind==='stockQuote'){
   if(!a.anyoneBuy&&!s.assets.some(x=>x.type==='stock'&&x.key===a.key&&x.quantity>0))continue;
   s.pending=event.kind==='split'?{kind:'stockSplit',title:a.factor===2?'股票拆分':'股票合并',text:`${a.key} 股数乘 ${a.factor}。本次不能交易。`,offer:a,queued:true}:{kind:'deal',title:a.name,text:a.anyoneBuy?'所有玩家均可按本张报价购买或出售。':'这是之前抽出的共享报价，可出售持有证券。',offer:a,queued:true};
  }else if(event.kind==='market'){
   const usable=c.mode==='startup'?s.assets.some(x=>['widget','software'].includes(x.key)):s.assets.some(x=>E.matching(x,c));
   if(!usable)continue;E.applyMarket(s,c);if(s.pending)s.pending.queued=true;s.lastGlobal=null;E.check(s);
  }else continue;
  s.processingQueue=true;return;
 }
}
function end(g){const s=current(g);if(s.won)throw Error('已有玩家获胜');if(!g.rolled&&!s.bankrupt)throw Error('请先完成本回合行动');if(s.pending&&!s.bankrupt)throw Error('请先处理当前事件');if(!g.players.some(p=>!p.bankrupt&&!p.inactive)){g.over=true;return}let next=g.active;for(let i=0;i<g.players.length;i++){next=(next+1)%g.players.length;if(next===0)g.round++;if(!g.players[next].bankrupt&&!g.players[next].inactive)break}g.active=next;g.rolled=false;prepareTurn(g)}
function response(g,index,action,id,quantity){const s=current(g);if(E.isReference(s))throw Error('共享卡将在对应玩家回合开始时处理');const p=g.players[index],e=s.pending;if(!p||p===s||p.stage!=='rat'||p.bankrupt||p.won||p.pending?.kind==='insolvent')throw Error('该玩家当前不能响应');if(!e||!(e.kind==='deal'&&e.offer.type==='stock'||e.kind==='market'&&e.card.global))throw Error('当前报价不对其他玩家开放');if(action==='buy'&&!(e.kind==='deal'&&e.offer.anyoneBuy))throw Error('该卡只允许抽卡者买入，其他玩家只能出售');const old=p.pending,copy=JSON.parse(JSON.stringify(e));p.pending=copy;try{if(action==='sell')E.sell(p,id,quantity);else if(action==='buy')E.buy(p,quantity);else throw Error('无效响应');if(p.pending===copy||p.pending===null)p.pending=old}catch(error){p.pending=old;throw error}}
function trade(g,buyerIndex,assetId,price){const seller=current(g),buyer=g.players[buyerIndex];if(!buyer||buyer===seller||seller.stage!=='rat'||buyer.stage!=='rat'||seller.won||seller.bankrupt||seller.inBankruptcy||buyer.won||buyer.bankrupt||buyer.inBankruptcy)throw Error('交易双方必须仍在老鼠赛跑');if(!Number.isInteger(price)||price<0)throw Error('交易价须为非负整数');if(buyer.cash<price)throw Error('买方现金不足');const i=seller.assets.findIndex(a=>a.id===assetId);if(i<0)throw Error('找不到资产');const a=seller.assets.splice(i,1)[0];seller.cash+=price;buyer.cash-=price;buyer.assets.push({...a,id:buyer.uid++});seller.history.unshift({turn:seller.turn,text:`将${a.name}及附带贷款转给${buyer.name}，收款 ${price}。`});buyer.history.unshift({turn:buyer.turn,text:`向${seller.name}购买${a.name}及附带贷款，支付 ${price}。`});E.check(seller);E.check(buyer)}
const api={create,current,prepareTurn,chooseDream,perform,end,response,trade};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.CashflowTable=api;
})(globalThis);
