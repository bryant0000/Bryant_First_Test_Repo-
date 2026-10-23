/* Original rules engine; numeric facts and evidence notes are in SOURCES.md. */
(function(root){
'use strict';
const D=typeof module!=='undefined'&&module.exports?require('./reference-data.js'):root.ClassicData;
const {jobs,track,dreams}=D;
const labels={opportunity:'机会',doodad:'额外支出',payday:'发薪日',market:'市场',baby:'添丁',charity:'慈善',downsized:'失业'};
function create(jobId,dreamId=0){
 const p=jobs[jobId];if(!p||!dreams[dreamId])throw Error('请选择有效职业和梦想');
 const s={version:3,ruleset:D.revision,jobId,dreamId,turn:0,pos:0,stage:'rat',cash:0,kids:0,assets:[],fastAssets:[],loans:[
  ['home','住房抵押贷款',p.homeDebt,p.homePayment],['school','教育贷款',p.schoolDebt,p.schoolPayment],['car','汽车贷款',p.carDebt,p.carPayment],['credit','信用卡债务',p.creditDebt,p.creditPayment],['retail','零售债务',p.retailDebt,p.retailPayment]
 ].filter(x=>x[2]>0).map(([id,name,balance,payment])=>({id,name,balance,payment})),charity:0,fastCharity:false,skip:0,pending:null,suspended:null,restructuring:false,lastDice:[],history:[],fastBase:0,fastGain:0,won:false,bankrupt:false,uid:1,decks:{}};
 s.cash=p.savings+totals(s).flow;log(s,`领取职业：${p.name}；储蓄 ${p.savings} + 月现金流 ${totals(s).flow} = 开局现金 ${s.cash}。`);return s;
}
function ratTotals(s){const p=jobs[s.jobId],passive=s.assets.reduce((n,a)=>n+a.income,0),payments=s.loans.reduce((n,l)=>n+l.payment,0),expenses=p.tax+p.other+payments+s.kids*p.childCost;return {salary:p.salary,passive,payments,expenses,flow:p.salary+passive-expenses,net:s.cash+s.assets.reduce((n,a)=>n+a.value-a.debt,0)-s.loans.reduce((n,l)=>n+l.balance,0),progress:expenses?Math.min(100,Math.max(0,passive/expenses*100)):100}}
function totals(s){const t=ratTotals(s);return s.stage==='rat'?t:{...t,salary:0,passive:s.fastBase+s.fastGain,expenses:0,payments:0,flow:s.fastBase+s.fastGain,net:s.cash+s.fastAssets.reduce((n,a)=>n+a.cost,0),progress:Math.min(100,Math.max(0,s.fastGain/50000*100))}}
function log(s,text){s.history.unshift({turn:s.turn,text})}
function available(s){if(s.won||s.bankrupt)throw Error('本局已结束')}
function draw(s,name,rng=Math.random){if(!s.decks[name]?.length){const indices=D[name].map((_,i)=>i);for(let i=indices.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[indices[i],indices[j]]=[indices[j],indices[i]]}s.decks[name]=indices}return {...D[name][s.decks[name].pop()]}}
function notice(s,title,text){s.pending={kind:'notice',title,text}}
function check(s){
 if(s.won||s.bankrupt)return;
 if(s.cash<0||(s.restructuring&&ratTotals(s).flow<0)){
  if(s.pending?.kind!=='insolvent'){s.suspended=s.pending;s.restructuring=s.restructuring||ratTotals(s).flow<0}
  s.pending={kind:'insolvent',title:s.restructuring?'资不抵债 · 调整财务':'现金不足',text:s.restructuring?'补足负现金，并将月现金流恢复为非负后才能继续。可按首付的一半清算资产、偿还债务或申请债务减免。':'通过贷款补足现金后可继续原事件。清算仅在现金危机时开放，按首付的一半回收，不是按房产总价打折。'};return;
 }
 if(s.pending?.kind==='insolvent'){s.pending=s.suspended;s.suspended=null;s.restructuring=false}
 if(s.stage==='rat'&&ratTotals(s).passive>ratTotals(s).expenses){
  const passive=ratTotals(s).passive;s.stage='fast';s.pos=0;s.fastBase=Math.round(passive/1000)*100000;s.cash+=s.fastBase;s.charity=0;s.skip=0;
  notice(s,'走出老鼠赛跑！',`被动收入 ${passive} 超过月支出，按最近的千元取整后乘 100，快车道基础收入为 ${s.fastBase}。已领取一次入场收入；此项为兼容规则，来源差异见说明。`);log(s,`进入快车道，基础收入 ${s.fastBase}，已领取入场收入。`);
 }
 if(s.stage==='fast'&&s.fastGain>=50000){s.won=true;notice(s,'赢得财务自由！','快车道现金流比入场基准增加了至少 50,000。');log(s,'达成新增现金流 50,000 的胜利条件。')}
}
function charityEvent(s){s.pending={kind:'charity',title:'慈善捐赠',cost:s.stage==='fast'?100000:Math.ceil((jobs[s.jobId].salary+ratTotals(s).passive)*.1),text:s.stage==='fast'?'捐出 100,000，之后可选择 1、2 或 3 颗骰子。这是所查在线版采用的规则。':'捐出总收入的 10%，接下来 3 个自己的回合可选择 1 或 2 颗骰子。'} }
function roll(s,count=s.stage==='fast'?2:1,rng=Math.random){
 available(s);if(s.pending)throw Error('请先完成当前事件');
 const allowed=s.stage==='fast'?(s.fastCharity?[1,2,3]:[2]):(s.charity>0?[1,2]:[1]);if(!allowed.includes(count))throw Error('当前不能使用这个骰子数量');
 s.turn++;if(s.skip>0){s.skip--;if(s.charity>0)s.charity--;notice(s,'失业休整',`跳过本回合。还需等待 ${s.skip} 回合。`);log(s,`失业休整，剩余 ${s.skip} 回合。`);return}
 s.lastDice=Array.from({length:count},()=>1+Math.floor(rng()*6));const steps=s.lastDice.reduce((a,b)=>a+b,0),len=s.stage==='rat'?track.length:D.fast.length;
 for(let i=0;i<steps;i++){s.pos=(s.pos+1)%len;if((s.stage==='rat'?track[s.pos]:D.fast[s.pos].type)==='payday'){const amount=totals(s).flow;s.cash+=amount;log(s,`经过${s.stage==='rat'?'发薪日':'现金流日'}，结算 ${amount>=0?'+':''}${amount}。`)}}
 if(s.charity>0)s.charity--;log(s,`掷出 ${s.lastDice.join(' + ')}，停在第 ${s.pos+1} 格。`);
 if(s.stage==='fast'){fastEvent(s);check(s);return}
 switch(track[s.pos]){
 case 'opportunity':s.pending={kind:'choose',title:'投资机会',text:'选择小买卖或大买卖牌堆。读完卡牌后可购买或放弃。'};break;
 case 'doodad':doodad(s,draw(s,'doodads',rng));break;
 case 'baby':if(s.kids<3){s.kids++;notice(s,'家庭添丁',`增加一名孩子，月支出增加 ${jobs[s.jobId].childCost}。目前 ${s.kids} 名孩子。`);log(s,`家庭添丁，子女数 ${s.kids}。`)}else notice(s,'子女数量已达上限','已有 3 名孩子，本次不再增加支出。');break;
 case 'charity':charityEvent(s);break;
 case 'downsized':{const cost=ratTotals(s).expenses;s.cash-=cost;s.skip=2;s.charity=0;notice(s,'遭遇失业',`支付月总支出 ${cost}，跳过接下来 2 回合，慈善资格清零。`);log(s,`失业，支付 ${cost}，休整 2 回合。`);break}
 case 'market':applyMarket(s,draw(s,'market',rng));break;
 default:notice(s,'发薪日','经过该格的净现金流已经结算，请查看现金和回合记录。');
 }
 check(s);
}
function doodad(s,c){if(c.child&&!s.kids){notice(s,c.name,'此卡只对有孩子的玩家生效，你无需支付。');return}const cost=c.child==='per'?c.cost*s.kids:c.cost;if(c.payment){s.pending={kind:'doodadChoice',title:c.name,cost,loan:c.name==='购买新游艇'?17000:4000,down:c.name==='购买新游艇'?1000:0,payment:c.payment,text:'此支出必须支付。可付全款，也可按卡面约定使用分期，增加对应贷款和月供。',sourceId:c.sourceId};return}s.cash-=cost;log(s,`${c.name}，支付 ${cost}。`);notice(s,c.name,`强制支出 ${cost}。${c.child==='per'?'已按孩子人数计算。':''}`)}
function payDoodad(s,finance){available(s);const e=s.pending;if(e?.kind!=='doodadChoice')throw Error('当前没有分期支出');if(finance){s.cash-=e.down;s.loans.push({id:'doodad-'+s.uid++,name:e.title+'分期',balance:e.loan,payment:e.payment});log(s,`${e.title}分期，首付 ${e.down}，负债 ${e.loan}，月供 ${e.payment}。`)}else{s.cash-=e.cost;log(s,`${e.title}全额支付 ${e.cost}。`)}s.pending=null;check(s)}
function deal(s,size,rng=Math.random){available(s);if(s.pending?.kind!=='choose')throw Error('当前没有投资机会');if(!['small','big'].includes(size))throw Error('无效牌堆');const a=draw(s,size,rng);if(a.type==='split'){for(const asset of s.assets.filter(x=>x.symbol===a.key)){asset.quantity*=a.factor;asset.dividend/=a.factor;asset.income=asset.quantity*asset.dividend}notice(s,a.factor===2?'股票拆分':'股票合并',`${a.key} 持股数乘 ${a.factor}，总成本不变。本次不可交易；允许保留半股以避免无依据的取整。`);s.pending.sourceId=a.sourceId;log(s,`${a.key} ${a.factor===2?'拆股':'并股'}，股数乘 ${a.factor}。`);s.lastGlobal={kind:'split',offer:a};return}
 s.pending={kind:'deal',title:a.name,text:a.type==='stock'?'按当前报价买入，已有同代码证券也可按本次报价出售。':'首付从现金扣除；资产附带贷款单列，净月收入已扣除运营与该资产融资成本。',offer:a};
}
function buy(s,quantity=1,rng=Math.random){
 available(s);const e=s.pending;if(!e||!['deal','fastDeal','dream'].includes(e.kind))throw Error('当前没有购买机会');
 if(e.kind==='dream'){if(D.dreams[s.dreamId].position!==s.pos)throw Error('这里不是你选定的梦想');if(s.cash<e.cost)throw Error('现金不足');s.cash-=e.cost;s.won=true;log(s,`实现梦想：${dreams[s.dreamId].name}。`);notice(s,'梦想成真！','你实现了开局选择的梦想，赢得了游戏。');return}
 if(e.kind==='fastDeal'){if(s.fastAssets.some(a=>a.position===s.pos))throw Error('你已购买这个项目');if(s.cash<e.cost)throw Error('现金不足');s.cash-=e.cost;let income=e.income||0,reward=0;if(e.rollmin){const n=1+Math.floor(rng()*6);const success=n>=e.rollmin;if(!success)income=0;if(success)reward=e.reward||0;log(s,`项目检定掷出 ${n}，${success?'成功':'失败'}。`)}s.cash+=reward;s.fastGain+=income;s.fastAssets.push({id:s.uid++,position:s.pos,name:e.title,cost:e.cost,income});log(s,`快车道购买${e.title}，投入 ${e.cost}，新增现金流 ${income}，现金奖励 ${reward}。`);s.pending=null;check(s);return}
 const a=e.offer;let cost;if(a.type==='stock'){if(!Number.isInteger(quantity)||quantity<1||quantity>1000000)throw Error('请输入 1 至 1,000,000 的整数份数');cost=a.price*quantity}else{cost=a.down;quantity=1}if(s.cash<cost)throw Error('现金不足，可以先贷款补足首付或放弃');
 s.cash-=cost;s.assets.push({id:s.uid++,name:a.name,key:a.key,type:a.type,symbol:a.symbol||null,quantity,units:a.units||1,dividend:a.dividend||0,cost,value:a.type==='stock'?cost:a.value,debt:a.debt||0,income:a.type==='stock'?a.dividend*quantity:a.income});log(s,`买入${a.name}${a.type==='stock'?' '+quantity+' 份':''}，现金投入 ${cost}。`);s.pending=null;check(s);
}
function matching(a,c){return c.key==='rental'?a.type==='property':c.key==='8PLEX'?a.key==='PLEX'&&a.units===8:a.key===c.key&&(a.units||1)>=(c.minUnits||1)}
function applyMarket(s,c){
 const assets=s.assets.filter(a=>matching(a,c));s.lastGlobal={kind:'market',card:c};
 const title={sell:'市场收购报价',selladd:'房产增值报价',sellmultiply:'有限合伙被收购',fee:'物业维修支出',lose:'房产被银行收回',startup:'创业公司成长',brother:'亲属赊购提议'}[c.mode];
 if(c.mode==='fee'){const cost=assets.length?c.amount:0;s.cash-=cost;notice(s,title,assets.length?`你有符合条件的资产，支付 ${cost}。`:'没有符合条件的资产，无需支付。');log(s,`市场维修事件，支付 ${cost}。`)}
 else if(c.mode==='lose'){s.assets=s.assets.filter(a=>!matching(a,c));notice(s,title,`移除 ${assets.length} 项对应资产、附带抵押和现金流。`);log(s,`银行收回 ${assets.length} 套三卧室住宅。`)}
 else if(c.mode==='startup'){const amount=Number(c.key);const startups=s.assets.filter(a=>['widget','software'].includes(a.key));startups.forEach(a=>a.income+=amount);notice(s,title,`${startups.length} 家创业公司每家月现金流增加 ${amount}。`);log(s,`创业公司收入改善 ${startups.length} × ${amount}。`)}
 else if(c.mode==='sellmultiply'){let receipt=0;for(const a of assets){receipt+=a.value*c.amount-a.debt;s.assets=s.assets.filter(x=>x.id!==a.id)}s.cash+=receipt;notice(s,title,`按原投入的 ${c.amount} 倍强制收购 ${assets.length} 项合伙投资，净收款 ${receipt}。`);log(s,`合伙被收购，收入 ${receipt}。`)}
 else if(c.mode==='brother'){notice(s,title,'此卡的四年期应收款如何对应棋盘回合尚无核验资料。为避免伪造回款规则，本次只展示提议，不自动成交。');s.pending.unverified=true}
 else{s.pending={kind:'market',title,card:c,text:c.mode==='selladd'?`符合条件的房产按原价加 ${c.amount} 收购。`:`按卡面 ${c.amount} 报价收购符合条件的资产；多户房产按每户计算。`}}
 if(s.pending)s.pending.sourceId=c.sourceId;
}
function quote(s,a){
 const e=s.pending;if(e?.kind==='insolvent')return {gross:Math.round(a.cost*.5)+a.debt,net:Math.round(a.cost*.5),kind:'清算'};
 if(e?.kind==='deal'&&e.offer.type==='stock'&&a.symbol===e.offer.symbol)return {gross:e.offer.price*a.quantity,net:e.offer.price*a.quantity,price:e.offer.price,kind:'证券报价'};
 if(e?.kind==='market'&&matching(a,e.card)){const c=e.card,gross=c.mode==='selladd'?a.value+c.amount:c.amount*(['PLEX','APTHOUSE'].includes(a.key)?a.units:a.key==='gold'?10:1);return {gross,net:gross-a.debt,kind:'市场报价'}}return null;
}
function sell(s,id,quantity){available(s);const i=s.assets.findIndex(a=>a.id===id);if(i<0)throw Error('找不到资产');const a=s.assets[i],q=quote(s,a);if(!q)throw Error('需有匹配的市场或证券报价；仅现金危机时允许银行清算');
 if(a.type==='stock'&&quantity!==undefined){if(!Number.isFinite(quantity)||quantity<=0||quantity>a.quantity||quantity*2%1!==0)throw Error('出售份数无效');const fraction=quantity/a.quantity,receipt=q.net*fraction;s.cash+=receipt;a.value*=1-fraction;a.cost*=1-fraction;a.quantity-=quantity;a.income=a.quantity*a.dividend;if(!a.quantity)s.assets.splice(i,1);log(s,`出售${a.name} ${quantity} 份，收入 ${receipt}。`)}else{s.cash+=q.net;s.assets.splice(i,1);log(s,`${q.kind}：出售${a.name}，成交 ${q.gross}，结清贷款 ${a.debt}，净收款 ${q.net}。`)}check(s);
}
function borrow(s,amount){available(s);if(s.stage!=='rat')throw Error('快车道不提供银行借款');if(!Number.isInteger(amount)||amount<=0||amount%1000||amount>1000000)throw Error('借款须为 1,000 的正整数倍，单次不超过 1,000,000');s.cash+=amount;let l=s.loans.find(x=>x.id==='bank');if(!l){l={id:'bank',name:'银行借款',balance:0,payment:0};s.loans.push(l)}l.balance+=amount;l.payment=l.balance*.1;log(s,`借款 ${amount}，银行总借款 ${l.balance}，月还款 ${l.payment}。`);check(s)}
function repay(s,id,amount){available(s);const i=s.loans.findIndex(l=>l.id===id);if(i<0)throw Error('找不到贷款');const l=s.loans[i];amount=amount===undefined?l.balance:amount;if(amount<=0||amount>l.balance||!Number.isInteger(amount))throw Error('偿还金额无效');if(id!=='bank'&&amount!==l.balance)throw Error('此类债务需全额偿还');if(id==='bank'&&amount%1000)throw Error('银行还款须为 1,000 的倍数');if(s.cash<amount)throw Error('现金不足');s.cash-=amount;l.balance-=amount;if(id==='bank')l.payment=l.balance*.1;if(!l.balance)s.loans.splice(i,1);log(s,`偿还${l.name} ${amount}。`);check(s)}
function donate(s){available(s);const e=s.pending;if(e?.kind!=='charity')throw Error('当前不在慈善格');if(s.cash<e.cost)throw Error('现金不足');s.cash-=e.cost;if(s.stage==='fast')s.fastCharity=true;else s.charity=3;s.pending=null;log(s,`慈善捐赠 ${e.cost}。`);check(s)}
function dismiss(s){available(s);if(['insolvent','doodadChoice'].includes(s.pending?.kind))throw Error('必须先解决当前强制事件');s.pending=null;check(s)}
function debtRelief(s){available(s);if(s.pending?.kind!=='insolvent'||s.assets.length||s.reliefUsed)throw Error('须先清算全部资产，债务减免每局仅一次');s.reliefUsed=true;for(const l of s.loans.filter(l=>['car','credit','retail'].includes(l.id))){l.balance=Math.ceil(l.balance/2);l.payment=Math.ceil(l.payment/2)}log(s,'汽车、信用卡及零售债务与月供减半。');check(s)}
function fastEvent(s){const a=D.fast[s.pos];if(a.type==='payday'){notice(s,'现金流日','经过本格的收入已入账。');return}if(a.type==='charity'){charityEvent(s);return}if(a.type==='dream'){const selected=dreams[s.dreamId].position===s.pos;s.pending=selected?{kind:'dream',title:a.name,cost:a.cost,text:'这是你开局选择的梦想，支付费用即可获胜。'}:{kind:'notice',title:a.name,text:'这不是你开局选择的梦想，继续寻找属于你的目标。'};return}if(['tax','divorce','lawsuit'].includes(a.type)){const loss=Math.floor(s.cash/2);s.cash-=loss;log(s,`${a.name}，失去一半现金 ${loss}。`);notice(s,a.name,`支付一半现金 ${loss}。`);return}if(s.fastAssets.some(x=>x.position===s.pos)){notice(s,a.name,'你已持有此事业，本次无需重复购买。');return}s.pending={kind:'fastDeal',title:a.name,cost:a.cost,income:a.income,rollmin:a.rollmin,reward:a.reward,text:a.rollmin?`投资后掷一颗骰子，至少 ${a.rollmin} 点才成功。成功${a.reward?'获得现金奖励 '+a.reward:'获得月现金流 '+a.income}；失败会损失投入。`:'支付投资款，增加快车道现金流。'}}
const api={data:D,jobs,track,labels,dreams,create,totals,ratTotals,roll,deal,buy,sell,borrow,repay,donate,dismiss,check,quote,matching,applyMarket,payDoodad,debtRelief,draw};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Cashflow=api;
})(globalThis);
