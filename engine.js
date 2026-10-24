/* Original rules engine; numeric facts and evidence notes are in SOURCES.md. */
(function(root){
'use strict';
const D=typeof module!=='undefined'&&module.exports?require('./reference-data.js'):root.ClassicData;
const {jobs,track,dreams}=D;
const REFERENCE_PROFILE='reference-web-2026-10-23';
const REFERENCE_COLORS=['#775478','#a8b240','#db753c','#769ba3','#ee4136','#81888f'];
const isReference=s=>s.rulesProfile===REFERENCE_PROFILE;
const labels={opportunity:'机会',doodad:'额外支出',payday:'发薪日',market:'市场',baby:'添丁',charity:'慈善',downsized:'失业'};
function randomCareer(rng=Math.random){const id=Math.floor(rng()*jobs.length);if(!jobs[id])throw Error('随机职业结果无效');return id}
function create(jobId,dreamId=0,rulesProfile=null){
 const p=jobs[jobId];if(!p||!dreams[dreamId])throw Error('请选择有效职业和梦想');
 const s={version:3,ruleset:D.revision,rulesProfile,jobId,dreamId,dreamMultiplier:1,cardQueue:[],processingQueue:false,turn:0,pos:rulesProfile===REFERENCE_PROFILE?16:0,stage:'rat',cash:0,kids:0,assets:[],fastAssets:[],loans:[
  ['home','住房抵押贷款',p.homeDebt,p.homePayment],['school','教育贷款',p.schoolDebt,p.schoolPayment],['car','汽车贷款',p.carDebt,p.carPayment],['credit','信用卡债务',p.creditDebt,p.creditPayment],['retail','零售债务',p.retailDebt,p.retailPayment]
 ].filter(x=>x[2]>0&&!(rulesProfile===REFERENCE_PROFILE&&x[0]==='school')).map(([id,name,balance,payment])=>({id,name,balance,payment})),charity:0,fastCharity:false,skip:0,pending:null,suspended:null,restructuring:false,lastDice:[],history:[],fastBase:0,fastGain:0,won:false,bankrupt:false,uid:1,decks:{}};
 s.cash=isReference(s)?p.savings:p.savings+totals(s).flow;if(isReference(s))s.referenceInitVersion=2;log(s,isReference(s)?`领取职业：${p.name}；开局现金为储蓄 ${s.cash}。`:`领取职业：${p.name}；储蓄 ${p.savings} + 月现金流 ${totals(s).flow} = 开局现金 ${s.cash}。`);return s;
}
function ratTotals(s){const p=jobs[s.jobId],passive=s.assets.reduce((n,a)=>n+a.income,0),payments=s.loans.reduce((n,l)=>n+l.payment,0),expenses=p.tax+p.other+payments+s.kids*p.childCost;return {salary:p.salary,passive,payments,expenses,flow:p.salary+passive-expenses,net:s.cash+s.assets.reduce((n,a)=>n+a.value-a.debt,0)-s.loans.reduce((n,l)=>n+l.balance,0),progress:expenses?Math.min(100,Math.max(0,passive/expenses*100)):100}}
function totals(s){const t=ratTotals(s);if(s.stage==='rat')return t;const income=s.fastBase+s.fastGain;return {...t,salary:isReference(s)?t.salary:0,passive:income,expenses:isReference(s)?t.expenses:0,payments:isReference(s)?t.payments:0,flow:income+(isReference(s)?t.salary-t.expenses:0),net:s.cash+s.fastAssets.reduce((n,a)=>n+a.cost,0),progress:Math.min(100,Math.max(0,s.fastGain/50000*100))}}
function log(s,text){s.history.unshift({turn:s.turn,text})}
function available(s){if(s.won||s.bankrupt)throw Error('本局已结束')}
function draw(s,name,rng=Math.random){if(!s.decks[name]?.length){const indices=D[name].map((_,i)=>i);for(let i=indices.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[indices[i],indices[j]]=[indices[j],indices[i]]}s.decks[name]=indices}return {...D[name][s.decks[name].pop()]}}
function notice(s,title,text){s.pending={kind:'notice',title,text}}
function check(s){
 if(s.won||s.bankrupt)return;
 if(isReference(s)&&s.inBankruptcy){updateBankruptcy(s);return}
 if(!isReference(s)&&(s.cash<0||(s.restructuring&&ratTotals(s).flow<0))){
  if(s.pending?.kind!=='insolvent'){s.suspended=s.pending;s.restructuring=s.restructuring||ratTotals(s).flow<0}
  s.pending={kind:'insolvent',title:s.restructuring?'资不抵债 · 调整财务':'现金不足',text:s.restructuring?'补足负现金，并将月现金流恢复为非负后才能继续。可按首付的一半清算资产、偿还债务或申请债务减免。':'通过贷款补足现金后可继续原事件。清算仅在现金危机时开放，按首付的一半回收，不是按房产总价打折。'};return;
 }
 if(s.pending?.kind==='insolvent'){s.pending=s.suspended;s.suspended=null;s.restructuring=false}
 if(s.stage==='rat'&&ratTotals(s).passive>ratTotals(s).expenses){
  if(isReference(s)){if(s.pending)return;s.pending={kind:'enterFast',title:'准备进入快车道',text:'被动收入已经超过支出。确认后进入快车道，基础现金流为当前被动收入的 100 倍。'};return}
  const passive=ratTotals(s).passive;s.stage='fast';s.pos=0;s.fastBase=Math.round(passive/1000)*100000;s.cash+=s.fastBase;s.charity=0;s.skip=0;
  notice(s,'走出老鼠赛跑！',`被动收入 ${passive} 超过月支出，按最近的千元取整后乘 100，快车道基础收入为 ${s.fastBase}。已领取一次入场收入；此项为兼容规则，来源差异见说明。`);log(s,`进入快车道，基础收入 ${s.fastBase}，已领取入场收入。`);
 }
 if(s.stage==='fast'&&s.fastGain>=50000){s.won=true;s.winReason='cashflow';notice(s,'赢得财务自由！','快车道现金流比入场基准增加了至少 50,000。');log(s,'达成新增现金流 50,000 的胜利条件。')}
}
function charityEvent(s){s.pending={kind:'charity',title:'慈善捐赠',cost:s.stage==='fast'?100000:isReference(s)?Math.max(1,(jobs[s.jobId].salary+ratTotals(s).passive)*.1):Math.ceil((jobs[s.jobId].salary+ratTotals(s).passive)*.1),text:s.stage==='fast'?'捐出 100,000，之后可选择 1、2 或 3 颗骰子。':'捐出总收入的 10%，接下来 3 个自己的回合可选择 1 或 2 颗骰子。'} }
function roll(s,count=s.stage==='fast'&&!isReference(s)?2:1,rng=Math.random){
 available(s);if(s.pending)throw Error('请先完成当前事件');
 const allowed=s.stage==='fast'?(s.fastCharity?[1,2,3]:isReference(s)?[1]:[2]):(s.charity>0?[1,2]:[1]);if(!allowed.includes(count))throw Error('当前不能使用这个骰子数量');
 s.turn++;if(s.skip>0){s.skip--;if(!isReference(s)&&s.charity>0)s.charity--;notice(s,s.skipReason==='bankruptcy'?'破产重整休整':'失业休整',`跳过本回合。还需等待 ${s.skip} 回合。`);log(s,`失业休整，剩余 ${s.skip} 回合。`);return}
 s.lastDice=Array.from({length:count},()=>1+Math.floor(rng()*6));const steps=s.lastDice.reduce((a,b)=>a+b,0),len=s.stage==='rat'?track.length:D.fast.length;
 for(let i=0;i<steps;i++){s.pos=(s.pos+1)%len;if((s.stage==='rat'?track[s.pos]:D.fast[s.pos].type)==='payday'){const amount=totals(s).flow;s.cash+=amount;log(s,`经过${s.stage==='rat'?'发薪日':'现金流日'}，结算 ${amount>=0?'+':''}${amount}。`)}}
 if(s.charity>0)s.charity--;
 if(isReference(s)&&s.cash<0){s.cash=0;s.inBankruptcy=true;s.pending=null;s.cardQueue=[];s.processingQueue=false;log(s,'发薪结算不足，现金归零，进入破产重整。');updateBankruptcy(s);return}
 log(s,`掷出 ${s.lastDice.join(' + ')}，停在第 ${s.pos+1} 格。`);
 if(s.stage==='fast'){fastEvent(s);check(s);return}
 switch(track[s.pos]){
 case 'opportunity':s.pending={kind:'choose',title:'投资机会',text:'选择小买卖或大买卖牌堆。读完卡牌后可购买或放弃。'};break;
 case 'doodad':doodad(s,draw(s,'doodads',rng));break;
 case 'baby':if(s.kids<3){if(isReference(s)){s.pending={kind:'baby',title:'家庭添丁',text:`确认后增加一名孩子，月支出增加 ${jobs[s.jobId].childCost}。`};break}s.kids++;notice(s,'家庭添丁',`增加一名孩子，月支出增加 ${jobs[s.jobId].childCost}。目前 ${s.kids} 名孩子。`);log(s,`家庭添丁，子女数 ${s.kids}。`)}else if(isReference(s))s.pending={kind:'baby',title:'子女数量已达上限',atLimit:true,text:'已有 3 名孩子，本次不再增加子女支出。确认后继续本回合。'};else notice(s,'子女数量已达上限','已有 3 名孩子，本次不再增加支出。');break;
 case 'charity':charityEvent(s);break;
 case 'downsized':{const cost=ratTotals(s).expenses;if(isReference(s)){s.pending={kind:'payment',effect:'downsize',title:'遭遇失业',cost,text:'支付本次卡片列出的月总支出，之后休整两回合。'};break}s.cash-=cost;s.skip=2;s.charity=0;notice(s,'遭遇失业',`支付月总支出 ${cost}，跳过接下来 2 回合，慈善资格清零。`);log(s,`失业，支付 ${cost}，休整 2 回合。`);break}
 case 'market':applyMarket(s,draw(s,'market',rng));break;
 default:if(!isReference(s))notice(s,'发薪日','经过该格的净现金流已经结算，请查看现金和回合记录。');
 }
 check(s);
}
function doodad(s,c){if(c.child&&!s.kids){notice(s,c.name,'此卡只对有孩子的玩家生效，你无需支付。');return}const cost=c.child==='per'?c.cost*s.kids:c.cost;if(c.payment){s.pending={kind:'doodadChoice',title:c.name,cost,loan:c.name==='购买新游艇'?17000:4000,down:c.name==='购买新游艇'?1000:0,payment:c.payment,text:'此支出必须支付。可付全款，也可按卡面约定使用分期，增加对应贷款和月供。',sourceId:c.sourceId};return}if(isReference(s)){s.pending={kind:'payment',effect:'doodad',title:c.name,cost,sourceId:c.sourceId,text:'本次支出必须支付。现金不足时可查看所需银行贷款。'};return}s.cash-=cost;log(s,`${c.name}，支付 ${cost}。`);notice(s,c.name,`强制支出 ${cost}。${c.child==='per'?'已按孩子人数计算。':''}`)}
function payDoodad(s,finance){available(s);const e=s.pending;if(e?.kind!=='doodadChoice')throw Error('当前没有分期支出');if(isReference(s)&&s.cash<(finance?e.down:e.cost)){offerLoan(s,(finance?e.down:e.cost)-s.cash);return}if(finance){s.cash-=e.down;if(isReference(s)){const id=e.title==='购买新游艇'?'boat':'credit';let l=s.loans.find(x=>x.id===id);if(!l){l={id,name:e.title==='购买新游艇'?'游艇贷款':'信用卡债务',balance:0,payment:0};s.loans.push(l)}l.balance+=e.loan;l.payment+=e.payment}else s.loans.push({id:'doodad-'+s.uid++,name:e.title+'分期',balance:e.loan,payment:e.payment});log(s,`${e.title}分期，首付 ${e.down}，负债 ${e.loan}，月供 ${e.payment}。`)}else{s.cash-=e.cost;log(s,`${e.title}全额支付 ${e.cost}。`)}s.pending=null;check(s)}
function deal(s,size,rng=Math.random){available(s);if(s.pending?.kind!=='choose')throw Error('当前没有投资机会');if(!['small','big'].includes(size))throw Error('无效牌堆');const a=draw(s,size,rng);if(a.type==='split'){if(isReference(s)){s.pending={kind:'stockSplit',title:a.factor===2?'股票拆分':'股票合并',text:`${a.key} 股数乘 ${a.factor}。本次不能交易。`,offer:a};s.lastGlobal={kind:'split',offer:a};return}splitShares(s,a.key,a.factor);notice(s,a.factor===2?'股票拆分':'股票合并',`${a.key} 持股数乘 ${a.factor}，总成本不变。本次不可交易；${isReference(s)?'参考站反向拆股将股数向下取整。':'兼容模式保留半股。'}`);s.pending.sourceId=a.sourceId;log(s,`${a.key} ${a.factor===2?'拆股':'并股'}，股数乘 ${a.factor}。`);s.lastGlobal={kind:'split',offer:a};return}
 s.pending={kind:'deal',title:a.name,text:a.type==='stock'?'按当前报价买入，已有同代码证券也可按本次报价出售。':'首付从现金扣除；资产附带贷款单列，净月收入已扣除运营与该资产融资成本。',offer:a};if(isReference(s)&&a.type==='stock')s.lastGlobal={kind:'stockQuote',offer:a};
}
function buy(s,quantity=1,rng=Math.random){
 available(s);const e=s.pending;if(!e||!['deal','fastDeal','dream'].includes(e.kind))throw Error('当前没有购买机会');
 if(e.kind==='dream'){if(D.dreams[s.dreamId].position!==s.pos)throw Error('这里不是你选定的梦想');if(s.cash<e.cost)throw Error('现金不足');s.cash-=e.cost;s.won=true;s.winReason='dream';log(s,`实现梦想：${dreams[s.dreamId].name}。`);notice(s,'梦想成真！','你实现了开局选择的梦想，赢得了游戏。');return}
 if(e.kind==='fastDeal'){if(s.fastAssets.some(a=>a.position===s.pos))throw Error('你已购买这个项目');if(s.cash<e.cost)throw Error('现金不足');s.cash-=e.cost;if(isReference(s)&&e.rollmin){const die=1+Math.floor(rng()*6);s.pending={...e,kind:'investmentRoll',paid:e.cost,cost:0,die,position:s.pos};log(s,`风险投资${e.title}已支付 ${e.cost}，等待确认检定结果。`);return}let income=e.income||0,reward=0;if(e.rollmin){const n=1+Math.floor(rng()*6);const success=n>=e.rollmin;if(!success)income=0;if(success)reward=e.reward||0;log(s,`项目检定掷出 ${n}，${success?'成功':'失败'}。`)}s.cash+=reward;s.fastGain+=income;s.fastAssets.push({id:s.uid++,position:s.pos,name:e.title,cost:e.cost,income});log(s,`快车道购买${e.title}，投入 ${e.cost}，新增现金流 ${income}，现金奖励 ${reward}。`);s.pending=null;check(s);return}
 const a=e.offer;if(e.queued&&!a.anyoneBuy)throw Error('该排队报价只允许出售持有证券');let cost;if(a.type==='stock'){if(!Number.isInteger(quantity)||quantity<1||quantity>1000000)throw Error('请输入 1 至 1,000,000 的整数份数');cost=a.price*quantity}else{cost=a.down;quantity=1}if(s.cash<cost){if(isReference(s)){offerLoan(s,cost-s.cash);return}throw Error('现金不足，可以先贷款补足首付或放弃')};
 s.cash-=cost;s.assets.push({id:s.uid++,name:a.name,key:a.key,type:a.type,symbol:a.symbol||null,quantity,units:a.units||1,dividend:a.dividend||0,cost,value:a.type==='stock'?cost:a.value,debt:a.debt||0,income:a.type==='stock'?a.dividend*quantity:a.income});log(s,`买入${a.name}${a.type==='stock'?' '+quantity+' 份':''}，现金投入 ${cost}。`);s.pending=null;check(s);
}
function matching(a,c){return c.key==='rental'?a.type==='property':c.key==='8PLEX'?a.key==='PLEX'&&a.units===8:a.key===c.key&&(a.units||1)>=(c.minUnits||1)}
function applyMarket(s,c,confirmed=false){
 const assets=s.assets.filter(a=>matching(a,c));s.lastGlobal=confirmed?null:{kind:'market',card:c};
 const title={sell:'市场收购报价',selladd:'房产增值报价',sellmultiply:'有限合伙被收购',fee:'物业维修支出',lose:'房产被银行收回',startup:'创业公司成长',brother:'亲属赊购提议'}[c.mode];
 if(isReference(s)&&!confirmed&&['fee','lose','startup','sellmultiply'].includes(c.mode)){
  const eligible=c.mode==='startup'?s.assets.some(a=>['widget','software'].includes(a.key)):assets.length>0;
  if(eligible)s.pending={kind:'marketMust',title,card:c,cost:c.mode==='fee'?c.amount:0,sourceId:c.sourceId,text:({fee:'确认支付本次物业费用。多项符合条件的物业只收取一次。',lose:'确认后移除匹配物业、贷款和现金流。',startup:`确认后每家对应创业公司的月现金流增加 ${Number(c.key)}。`,sellmultiply:`确认后按 ${c.amount} 倍价格完成合伙收购。`})[c.mode]};
  else notice(s,title,'没有符合条件的资产，本次无需处理。');
  return;
 }
 if(c.mode==='fee'){const cost=assets.length?c.amount:0;s.cash-=cost;notice(s,title,assets.length?`你有符合条件的资产，支付 ${cost}。`:'没有符合条件的资产，无需支付。');log(s,`市场维修事件，支付 ${cost}。`)}
 else if(c.mode==='lose'){s.assets=s.assets.filter(a=>!matching(a,c));notice(s,title,`移除 ${assets.length} 项对应资产、附带抵押和现金流。`);log(s,`银行收回 ${assets.length} 套三卧室住宅。`)}
 else if(c.mode==='startup'){const amount=Number(c.key);const startups=s.assets.filter(a=>['widget','software'].includes(a.key));startups.forEach(a=>a.income+=amount);notice(s,title,`${startups.length} 家创业公司每家月现金流增加 ${amount}。`);log(s,`创业公司收入改善 ${startups.length} × ${amount}。`)}
 else if(c.mode==='sellmultiply'){let receipt=0;for(const a of assets){receipt+=a.value*c.amount-a.debt;s.assets=s.assets.filter(x=>x.id!==a.id)}s.cash+=receipt;notice(s,title,`按原投入的 ${c.amount} 倍强制收购 ${assets.length} 项合伙投资，净收款 ${receipt}。`);log(s,`合伙被收购，收入 ${receipt}。`)}
 else if(isReference(s)&&!assets.length){notice(s,title,'没有符合条件的资产，本次没有出售机会。')}
 else if(c.mode==='brother'){if(isReference(s))s.pending={kind:'market',title,card:c,text:'接受后移除这项住宅及其抵押贷款。本次出售不会立即收到现金。'};else{notice(s,title,'此卡的四年期应收款如何对应棋盘回合尚无核验资料。为避免伪造回款规则，本次只展示提议，不自动成交。');s.pending.unverified=true}}
 else{s.pending={kind:'market',title,card:c,text:c.mode==='selladd'?`符合条件的房产按原价加 ${c.amount} 收购。`:`按卡面 ${c.amount} 报价收购符合条件的资产；多户房产按每户计算。`}}
 if(s.pending)s.pending.sourceId=c.sourceId;
}
function quote(s,a){
 const e=s.pending;if(e?.kind==='insolvent'){if(isReference(s)&&s.inBankruptcy&&a.type==='stock')return null;const value=isReference(s)?a.cost*.5:Math.round(a.cost*.5);return {gross:value+a.debt,net:value,kind:'清算'}};
 if(e?.kind==='deal'&&e.offer.type==='stock'&&a.symbol===e.offer.symbol)return {gross:e.offer.price*a.quantity,net:e.offer.price*a.quantity,price:e.offer.price,kind:'证券报价'};
 if(e?.kind==='market'&&matching(a,e.card)){const c=e.card;if(c.mode==='brother')return {gross:a.debt,net:0,kind:'亲属赊购'};const gross=c.mode==='selladd'?a.value+c.amount:c.amount*((['PLEX','APTHOUSE'].includes(a.key)||isReference(s)&&a.key==='coin')?a.units:a.key==='gold'?10:1);return {gross,net:gross-a.debt,kind:'市场报价'}}return null;
}
function sell(s,id,quantity){available(s);const i=s.assets.findIndex(a=>a.id===id);if(i<0)throw Error('找不到资产');const a=s.assets[i],q=quote(s,a);if(!q)throw Error('需有匹配的市场或证券报价；仅现金危机时允许银行清算');
 if(a.type==='stock'&&quantity!==undefined){if(!Number.isFinite(quantity)||quantity<=0||quantity>a.quantity||quantity*2%1!==0)throw Error('出售份数无效');const fraction=quantity/a.quantity,receipt=q.net*fraction;s.cash+=receipt;a.value*=1-fraction;a.cost*=1-fraction;a.quantity-=quantity;a.income=a.quantity*a.dividend;if(!a.quantity)s.assets.splice(i,1);log(s,`出售${a.name} ${quantity} 份，收入 ${receipt}。`)}else{s.cash+=q.net;s.assets.splice(i,1);log(s,`${q.kind}：出售${a.name}，成交 ${q.gross}，结清贷款 ${a.debt}，净收款 ${q.net}。`)}check(s);
}
function borrowLimit(s){return isReference(s)?9999000:1000000}
function creditBankLoan(s,amount){available(s);if(s.stage!=='rat')throw Error('快车道不提供银行借款');if(s.inBankruptcy)throw Error('破产重整期间请清算资产或偿还债务');if(!Number.isSafeInteger(amount)||amount<=0||amount%1000)throw Error('借款须为 1,000 的正整数倍');s.cash+=amount;let l=s.loans.find(x=>x.id==='bank');if(!l){l={id:'bank',name:'银行借款',balance:0,payment:0};s.loans.push(l)}l.balance+=amount;l.payment=l.balance*.1;log(s,`借款 ${amount}，银行总借款 ${l.balance}，月还款 ${l.payment}。`)}
function borrow(s,amount){available(s);if(!Number.isInteger(amount)||amount<=0||amount%1000||amount>borrowLimit(s))throw Error(`借款须为 1,000 的正整数倍，单次不超过 ${borrowLimit(s).toLocaleString('en-US')}`);creditBankLoan(s,amount);check(s)}
function repay(s,id,amount){available(s);const i=s.loans.findIndex(l=>l.id===id);if(i<0)throw Error('找不到贷款');const l=s.loans[i];amount=amount===undefined?l.balance:amount;if(amount<=0||amount>l.balance||!Number.isFinite(amount)||((id==='bank'||!isReference(s))&&!Number.isInteger(amount)))throw Error('偿还金额无效');if(id!=='bank'&&amount!==l.balance)throw Error('此类债务需全额偿还');if(id==='bank'&&amount%1000)throw Error('银行还款须为 1,000 的倍数');if(s.cash<amount)throw Error('现金不足');s.cash-=amount;l.balance-=amount;if(id==='bank')l.payment=l.balance*.1;if(!l.balance)s.loans.splice(i,1);log(s,`偿还${l.name} ${amount}。`);check(s)}
function donate(s){available(s);const e=s.pending;if(e?.kind!=='charity')throw Error('当前不在慈善格');if(s.cash<e.cost)throw Error('现金不足');s.cash-=e.cost;if(s.stage==='fast')s.fastCharity=true;else s.charity=3;s.pending=null;log(s,`慈善捐赠 ${e.cost}。`);check(s)}
function dismiss(s){available(s);if(['insolvent','doodadChoice','enterFast','investmentRoll','stockSplit','payment','loanOffer','marketMust','stockTrade','debtHalved','recovery','bankruptLost','baby','assetSale','debtReview','debtPicker','borrowReview','skipTurn'].includes(s.pending?.kind))throw Error('必须先解决当前强制事件');s.pending=null;check(s)}
function debtRelief(s){available(s);if(s.pending?.kind!=='insolvent'||s.assets.length||s.reliefUsed)throw Error('须先清算全部资产，债务减免每局仅一次');s.reliefUsed=true;for(const l of s.loans.filter(l=>['car','credit','retail'].includes(l.id))){l.balance=isReference(s)?l.balance/2:Math.ceil(l.balance/2);l.payment=isReference(s)?l.payment/2:Math.ceil(l.payment/2)}log(s,'汽车、信用卡及零售债务与月供减半。');check(s)}
function fastEvent(s){const a=D.fast[s.pos];if(a.type==='payday'){if(isReference(s))s.pending=null;else notice(s,'现金流日','经过本格的收入已入账。');return}if(a.type==='charity'){charityEvent(s);return}if(a.type==='dream'){const selected=dreams[s.dreamId].position===s.pos;s.pending=selected?{kind:'dream',title:a.name,cost:a.cost*(isReference(s)?s.dreamMultiplier||1:1),text:'这是你开局选择的梦想，支付费用即可获胜。'}:{kind:'notice',title:a.name,text:'这不是你开局选择的梦想，继续寻找属于你的目标。'};return}if(['tax','divorce','lawsuit'].includes(a.type)){const loss=isReference(s)?(a.type==='divorce'?s.cash:s.cash*.5):Math.floor(s.cash/2);if(isReference(s)){s.pending={kind:'payment',effect:a.type,title:a.name,cost:loss,text:a.type==='divorce'?'确认后清空可用现金。':'确认后支付可用现金的一半。'};return}s.cash-=loss;log(s,`${a.name}，支付 ${loss}。`);notice(s,a.name,`支付 ${loss}。`);return}if(s.fastAssets.some(x=>x.position===s.pos)){notice(s,a.name,'你已持有此事业，本次无需重复购买。');return}s.pending={kind:'fastDeal',title:a.name,cost:a.cost,income:a.income,rollmin:a.rollmin,reward:a.reward,text:a.rollmin?`投资后掷一颗骰子，至少 ${a.rollmin} 点才成功。成功${a.reward?'获得现金奖励 '+a.reward:'获得月现金流 '+a.income}；失败会损失投入。`:'支付投资款，增加快车道现金流。'}}

function splitShares(s,key,factor){for(const a of s.assets.filter(x=>x.symbol===key)){const old=a.quantity;if(isReference(s)){a.quantity=factor===.5?Math.floor(old/2):old*2;a.cost*=a.quantity/old;a.value*=a.quantity/old}else{a.quantity*=factor;a.dividend/=factor}a.income=a.quantity*a.dividend}s.assets=s.assets.filter(a=>a.quantity>0)}
function offerLoan(s,shortfall){
 if(!isReference(s)||s.stage!=='rat'||!(shortfall>0))throw Error('当前不能提供贷款');
 s.pending={kind:'loanOffer',title:'现金不足 · 银行贷款',loan:Math.ceil(shortfall/1000)*1000,previous:s.pending,text:'借款按 1,000 向上取整，每月支出增加借款的 10%。借款后返回原卡片，再确认付款。'};
}
function acceptLoan(s){
 available(s);const e=s.pending;if(e?.kind!=='loanOffer')throw Error('当前没有贷款提议');
 if(isReference(s))creditBankLoan(s,e.loan);else borrow(s,e.loan);restoreLoanCard(s,e);
}
function restoreLoanCard(s,e){s.pending=e.previous;if(isReference(s)&&s.pending?.kind==='stockTrade'&&s.pending.mode==='buy')s.pending.quantity=1}
function cancelLoan(s){available(s);const e=s.pending;if(e?.kind!=='loanOffer')throw Error('当前没有贷款提议');restoreLoanCard(s,e)}
function payEvent(s){
 available(s);const e=s.pending;if(!isReference(s)||!['payment','marketMust'].includes(e?.kind))throw Error('当前没有待付事件');
 if(s.cash<e.cost){offerLoan(s,e.cost-s.cash);return}
 if(e.kind==='marketMust'){applyMarket(s,e.card,true);s.pending=null;check(s);return}
 s.cash-=e.cost;if(e.effect==='downsize'){s.skip=2;s.charity=0}
 log(s,`支付${e.title} ${e.cost}。`);s.pending=null;check(s);
}
function updateBankruptcy(s){
 if(['debtHalved','recovery','bankruptLost'].includes(s.pending?.kind))return;
 if(ratTotals(s).flow>0){s.pending={kind:'recovery',title:'重整完成',text:'月现金流已恢复为正。确认后休整三回合。'};return}
 const assets=s.assets.some(a=>a.type!=='stock'&&a.quantity>0),canRepay=s.loans.some(l=>l.balance>0&&(s.cash>=l.balance||l.id==='bank'&&s.cash>=1000));
 if(assets||canRepay){s.pending={kind:'insolvent',title:'破产重整',text:'通过财务表清算资产、偿还负债，直到月现金流恢复为正。物业按首付的一半清算。'};return}
 for(const l of s.loans.filter(l=>['car','credit','retail'].includes(l.id))){l.balance/=2;l.payment/=2}
 log(s,'破产重整：汽车、信用卡和零售债务及月供减半。');s.pending={kind:'debtHalved',title:'债务减半',text:'汽车、信用卡和零售债务及月供已减半。确认后检查是否能够恢复。'};
}
function confirmRelief(s){available(s);if(!s.inBankruptcy||s.pending?.kind!=='debtHalved')throw Error('当前没有债务减半结果');s.pending=ratTotals(s).flow>0?{kind:'recovery',title:'重整完成',text:'月现金流恢复为正，确认后休整三回合。'}:{kind:'bankruptLost',title:'重整失败',text:'减免后月现金流仍未恢复为正，确认后退出本局。'}}
function completeRecovery(s){available(s);if(!s.inBankruptcy||s.pending?.kind!=='recovery')throw Error('尚未完成破产重整');s.inBankruptcy=false;s.pending=null;s.skip=3;s.skipReason='bankruptcy';s.cardQueue=[];s.processingQueue=false;log(s,'完成破产重整，休整三回合。');check(s)}
function confirmBankruptLoss(s){available(s);if(s.pending?.kind!=='bankruptLost')throw Error('当前没有重整失败结果');s.inBankruptcy=false;s.bankrupt=true;s.pending=null;s.cardQueue=[];s.processingQueue=false;log(s,'重整失败，退出本局。')}
function confirmChild(s){available(s);if(!isReference(s)||s.pending?.kind!=='baby')throw Error('当前没有添丁事件');if(s.kids<3){s.kids++;log(s,`家庭添丁，子女数 ${s.kids}。`)}else log(s,'已有 3 名孩子，本次不增加子女支出。');s.pending=null;check(s)}
function confirmSkip(s){available(s);if(!isReference(s)||s.pending?.kind!=='skipTurn'||s.skip<1)throw Error('当前没有休整回合');s.skip--;s.turn++;s.pending=null;log(s,`本回合休整，剩余 ${s.skip} 回合。`)}
function openAssetSale(s,id){
 available(s);const a=s.assets.find(x=>x.id===id),previous=s.pending;
 if(!isReference(s)||!a||a.type==='stock'||!['market','insolvent'].includes(previous?.kind))throw Error('当前不能出售这项资产');
 const q=quote(s,a);if(!q)throw Error('没有适用的资产报价');s.pending={kind:'assetSale',title:'出售 '+a.name,assetId:id,previous,gross:q.gross,net:q.net,debt:a.debt,text:previous.kind==='insolvent'?'确认后按当前清算价出售，移除资产和相关贷款。':'核对售价、结清贷款和净收款后确认出售。'};
}
function cancelAssetSale(s){available(s);if(s.pending?.kind!=='assetSale')throw Error('当前没有资产出售确认');s.pending=s.pending.previous}
function confirmAssetSale(s){
 available(s);const e=s.pending;if(e?.kind!=='assetSale')throw Error('当前没有资产出售确认');
 s.pending=e.previous;try{sell(s,e.assetId)}catch(error){s.pending=e;throw error}
 if(e.previous.kind==='market'&&s.pending?.kind==='market'&&(e.previous.card.mode==='brother'||!s.assets.some(a=>matching(a,e.previous.card)))){s.pending=null;check(s)}
}
function openDebtReview(s,id){
 available(s);const l=s.loans.find(x=>x.id===id);if(!isReference(s)||s.stage!=='rat'||!l||l.balance<=0)throw Error('请选择有效负债');
 const previous=s.pending?.kind==='debtReview'?s.pending.previous:s.pending;s.pending={kind:'debtReview',title:'偿还 '+l.name,loanId:id,amount:id==='bank'?1000:l.balance,payment:l.payment,previous,text:id==='bank'?'选择按整千偿还的金额，或结清全部银行贷款。':'此项负债需要全额结清。'};
}
function cancelDebtReview(s){available(s);if(s.pending?.kind!=='debtReview')throw Error('当前没有还款确认');s.pending=s.pending.previous}
function confirmDebtReview(s,amount){
 available(s);const e=s.pending;if(e?.kind!=='debtReview')throw Error('当前没有还款确认');
 const l=s.loans.find(x=>x.id===e.loanId);if(!l)throw Error('找不到贷款');
 let payment=amount===undefined?e.amount:amount;
 if(e.loanId==='bank'){
  if(!Number.isFinite(payment)||s.cash<1000)throw Error('请输入有效还款金额，现金至少需要 1,000');
  payment=Math.max(1000,Math.min(Math.round(payment/1000)*1000,l.balance,Math.floor(s.cash/1000)*1000));
 }
 s.pending=e.previous?.kind==='debtPicker'?e.previous.previous:e.previous;
 try{repay(s,e.loanId,payment)}catch(error){s.pending=e;throw error}
}
function openDebtPicker(s){available(s);if(!isReference(s)||s.stage!=='rat'||s.inBankruptcy||s.pending)throw Error('当前不能选择还款负债');s.pending={kind:'debtPicker',title:'偿还负债',previous:null,text:'点击财务表中高亮的个人负债，再确认偿还金额。'}}
function cancelDebtPicker(s){available(s);if(s.pending?.kind!=='debtPicker')throw Error('当前没有负债选择卡');s.pending=s.pending.previous}
function changeDebtAmount(s,direction){
 available(s);const e=s.pending;if(e?.kind!=='debtReview'||e.loanId!=='bank'||![-1,1].includes(direction))throw Error('当前不能调整还款金额');
 const l=s.loans.find(x=>x.id==='bank');if(!l)throw Error('找不到贷款');
 const rounded=Math.round(e.amount/1000)*1000;
 e.amount=direction>0?Math.min(l.balance,s.cash,Math.max(1000,rounded+1000)):Math.max(1000,rounded-1000);
}
function openBorrowReview(s){available(s);if(!isReference(s)||s.stage!=='rat'||s.inBankruptcy||s.pending)throw Error('当前不能打开银行借款');s.pending={kind:'borrowReview',title:'银行借款',amount:1000,text:'借款以 1,000 为单位，每月支出增加借款的 10%。'}}
function cancelBorrowReview(s){available(s);if(s.pending?.kind!=='borrowReview')throw Error('当前没有借款表单');s.pending=null}
function confirmBorrowReview(s,amount){available(s);const e=s.pending;if(e?.kind!=='borrowReview')throw Error('当前没有借款表单');s.pending=null;try{borrow(s,Math.round(amount/1000)*1000)}catch(error){s.pending=e;throw error}}
function stockHeld(s,key){return s.assets.filter(a=>a.type==='stock'&&a.key===key).reduce((n,a)=>n+a.quantity,0)}
function openStock(s,mode){
 available(s);const e=s.pending;if(!isReference(s)||e?.kind!=='deal'||e.offer.type!=='stock'||!['buy','sell'].includes(mode))throw Error('当前没有证券报价');
 const held=stockHeld(s,e.offer.key);if(mode==='buy'&&e.queued&&!e.offer.anyoneBuy)throw Error('该排队报价只允许出售持有证券');if(mode==='sell'&&!held)throw Error('没有可出售的证券');
 s.pending={kind:'stockTrade',title:e.title,offer:e.offer,mode,quantity:mode==='buy'?1:held,previous:e,text:mode==='buy'?'选择购买份数，再提交买入。':'选择出售份数，再提交卖出。'};
}
function stockQuantity(s,quantity){const e=s.pending;if(e?.kind!=='stockTrade')throw Error('当前没有证券交易');if(!Number.isInteger(quantity))throw Error('份数必须为整数');e.quantity=Math.max(1,Math.min(quantity,e.mode==='buy'?99999:stockHeld(s,e.offer.key)))}
function cancelStock(s){available(s);if(s.pending?.kind!=='stockTrade')throw Error('当前没有证券交易');s.pending=s.pending.previous}
function confirmStock(s,quantity){
 available(s);const e=s.pending;if(!isReference(s)||e?.kind!=='stockTrade')throw Error('当前没有证券交易');
 const max=e.mode==='buy'?99999:stockHeld(s,e.offer.key);if(!Number.isInteger(quantity)||quantity<1||quantity>max)throw Error(`请输入 1 至 ${max} 的整数份数`);e.quantity=quantity;
 if(e.mode==='buy'){s.pending=e.previous;try{buy(s,quantity);if(s.pending?.kind==='loanOffer')s.pending.previous=e}catch(error){s.pending=e;throw error}return}
 const lots=s.assets.filter(a=>a.type==='stock'&&a.key===e.offer.key).sort((a,b)=>a.cost/a.quantity-b.cost/b.quantity);let remaining=quantity;
 for(const a of lots){const count=Math.min(remaining,a.quantity),ratio=(a.quantity-count)/a.quantity;a.cost*=ratio;a.value*=ratio;a.quantity-=count;a.income=a.quantity*a.dividend;remaining-=count;if(!remaining)break}
 s.assets=s.assets.filter(a=>a.quantity>0);s.cash+=e.offer.price*quantity;log(s,`出售${e.title} ${quantity} 份，收入 ${e.offer.price*quantity}。`);s.pending=null;check(s);
}
function acceptSplit(s){available(s);const e=s.pending;if(!isReference(s)||e?.kind!=='stockSplit')throw Error('当前没有拆股事件');splitShares(s,e.offer.key,e.offer.factor);log(s,`${e.offer.key} 股数乘 ${e.offer.factor}。`);s.pending=null;check(s)}
function resolveInvestment(s){
 available(s);const e=s.pending;if(!isReference(s)||e?.kind!=='investmentRoll')throw Error('当前没有投资检定结果');
 const success=e.die>=e.rollmin;let reward=0,income=0;
 if(success){reward=e.reward||0;income=e.income||0;s.cash+=reward;s.fastGain+=income;s.fastAssets.push({id:s.uid++,position:e.position,name:e.title,cost:0,income})}
 log(s,`风险投资${e.title}掷出 ${e.die}，${success?'成功':'失败'}；新增现金流 ${income}，现金奖励 ${reward}。`);s.pending=null;check(s);
}
function enterFast(s){available(s);if(!isReference(s)||s.pending?.kind!=='enterFast')throw Error('尚未进入快车道确认阶段');s.fastBase=ratTotals(s).passive*100;s.stage='fast';s.cash=s.fastBase;s.pos=42;s.charity=0;s.skip=0;s.pending=null;log(s,`确认进入快车道，现金与基础收入设为 ${s.fastBase}，入场位置 42。`)}
const api={REFERENCE_COLORS,randomCareer,confirmSkip,changeDebtAmount,openDebtPicker,cancelDebtPicker,REFERENCE_PROFILE,isReference,enterFast,resolveInvestment,acceptSplit,payEvent,acceptLoan,cancelLoan,confirmRelief,completeRecovery,confirmBankruptLoss,confirmChild,openAssetSale,cancelAssetSale,confirmAssetSale,openDebtReview,cancelDebtReview,confirmDebtReview,openBorrowReview,cancelBorrowReview,confirmBorrowReview,stockHeld,openStock,stockQuantity,cancelStock,confirmStock,splitShares,data:D,jobs,track,labels,dreams,create,totals,ratTotals,roll,deal,buy,sell,borrowLimit,borrow,repay,donate,dismiss,check,quote,matching,applyMarket,payDoodad,debtRelief,draw};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Cashflow=api;
})(globalThis);
