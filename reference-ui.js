/* Presentation of the observed classic web cards. Financial commands stay in the existing engine. */
(function(){
'use strict';
document.body.classList.add('classic-shell');
const labels={small:'小买卖',big:'大买卖','open-stock-buy':'买入','open-stock-sell':'卖出',buy:'买入',dismiss:'跳过','confirm-stock':'买入',cancelStock:'取消',payEvent:'支付',acceptLoan:'是',cancelLoan:'否',enterFast:'确定',resolveInvestment:'确定','pay-cash':'全款','pay-finance':'分期',donate:'捐赠',confirmChild:'确定',confirmSkip:'确定',acceptSplit:'确定',confirmRelief:'确定',completeRecovery:'确定',confirmBankruptLoss:'确定','confirm-borrow':'借款',cancelBorrowReview:'取消',cancelDebtPicker:'取消','confirm-debt':'支付',cancelDebtReview:'取消',cancelAssetSale:'取消',confirmAssetSale:'出售'};
const paths={home:'M8 29 32 8l24 21M15 25v30h34V25M27 55V37h12v18M20 28h7v7h-7M39 28h7v7h-7',money:'M45 18c-5-8-27-7-27 6 0 14 29 7 29 21 0 13-24 16-32 5M32 6v52',dice:'M12 16h36v36H12zM20 24h1M39 24h1M29 34h1M20 44h1M39 44h1',heart:'M32 54 9 32C-5 13 20 0 32 19 44 0 69 13 55 32Z',family:'M20 12a7 7 0 1 0 0 .1M44 12a7 7 0 1 0 0 .1M8 49V29h21v20M35 49V29h21v20M26 53V42h12v11',market:'M10 22h44M14 22v32h36V22M8 13h48v9H8zM26 54V38h12v16',briefcase:'M8 22h48v32H8zM22 22V12h20v10M8 34h48M29 30h6v9h-6',chart:'M10 10v44h46M17 43l12-15 12 7 14-23'};
function symbolPath(){const e=state.pending;if(!e)return'dice';if(e.kind==='choose'||e.kind==='deal'||e.kind==='stockTrade')return'home';if(e.kind==='baby')return'family';if(e.kind==='charity')return'heart';if(e.kind==='market'||e.kind==='marketMust'||e.kind==='assetSale')return'market';if(e.kind==='fastDeal'||e.kind==='investmentRoll')return'chart';if(e.kind==='skipTurn')return'briefcase';return'money'}
function icon(key){return `<svg viewBox="0 0 64 64" aria-hidden="true"><path d="${paths[key]}"/></svg>`}
function sheet(){
 if(!CashflowUI.docked()){finances();return}const p=window.OnlineGame?.player()||state;if(p.stage!=='rat')return;
 const t=E.ratTotals(p),job=E.jobs[p.jobId],stocks=p.assets.filter(a=>a.type==='stock'),properties=p.assets.filter(a=>a.type!=='stock');
 const blank=n=>Array.from({length:Math.max(0,n)},()=>'<div class="classic-ledger-blank" aria-hidden="true"></div>').join('');
 const lines=(items,label,value)=>items.map(a=>row(esc(label(a)),value(a))).join('');
 $('income-table').innerHTML=row(esc(job.name)+'工资',job.salary)+'<h4>利息 / 分红</h4>'+lines(stocks,a=>a.symbol||a.name,a=>a.income)+blank(2-stocks.length)+'<h4>房地产 / 事业</h4>'+lines(properties,a=>a.name,a=>a.income)+blank(3-properties.length);
 const labels={home:'住房抵押贷款月供',car:'汽车贷款月供',credit:'信用卡月供',retail:'零售债务月供',bank:'银行借款月供'};
 const ordered=['home','car','credit','retail'];$('expense-table').innerHTML=row('税金',job.tax)+ordered.flatMap(id=>p.loans.filter(l=>l.id===id).map(l=>row(labels[id]||esc(l.name),l.payment))).join('')+row('其他生活支出',job.other)+p.loans.filter(l=>!ordered.includes(l.id)).map(l=>row(labels[l.id]||esc(l.name)+'月供',l.payment)).join('')+(p.kids?row('子女支出 · '+p.kids+' 人',p.kids*job.childCost):'');
 const assetRow=a=>{const q=E.quote(p,a),tag=q?'button':'div',attrs=q?` type="button" data-sell="${a.id}"`:'';return `<${tag}${attrs} class="classic-ledger-row ${q?'classic-ledger-selectable':''}"><span>${esc(a.symbol||a.name)}${a.type==='stock'?' · '+a.quantity+' 份':''}</span><b>${money(a.type==='stock'?a.cost/a.quantity:a.cost)}</b></${tag}>`};
 $('asset-table').innerHTML='<h4>股票 / 基金 / 存单 <span>每份成本</span></h4>'+stocks.map(assetRow).join('')+blank(4-stocks.length)+'<h4>房地产 / 事业 <span>成本</span></h4>'+properties.map(assetRow).join('')+blank(3-properties.length);
 const selecting=['debtPicker','insolvent'].includes(p.pending?.kind);$('loan-table').innerHTML=p.loans.map(l=>{const tag=selecting?'button':'div';return `<${tag}${selecting?` type="button" data-repay="${l.id}"`:''} class="classic-ledger-row ${selecting?'classic-ledger-selectable':''}"><span>${esc(l.name)}</span><b>${money(l.balance)}</b></${tag}>`}).join('');
 $('ref-property-debts').innerHTML='<h4>房地产 / 事业 <span>贷款余额</span></h4>'+lines(properties,a=>a.name,a=>a.debt)+blank(3-properties.length);
}
function present(){if(!game||!state||!E.isReference(state))return;sheet();const e=state.pending,dialog=$('event-dialog');
 $('card-symbol').innerHTML=icon(symbolPath());
 $('turn-marker').innerHTML=icon('dice');$('turn-marker').setAttribute('aria-hidden','true');
 const actions=Array.from($('event').children).filter(n=>n.classList.contains('event-buttons')&&!n.classList.contains('reference-amount-arrows'));
 if(e||state.won){const group=actions.at(-1);if(group)group.classList.add('reference-card-actions');}
 if(e?.kind==='stockTrade'||e?.kind==='debtReview'){
  const adjust=actions.find(n=>n.querySelector('[data-action="stock-plus"],[data-action="debt-plus"]'));if(adjust)adjust.classList.add('reference-amount-arrows');
  const input=$('quantity')||$('debt-amount');if(input){input.closest('label').classList.add('reference-amount-input');input.setAttribute('inputmode','numeric')}
 }
 let queued=dialog.querySelector('.reference-queue');if(!queued){queued=document.createElement('div');queued.className='reference-queue';dialog.append(queued)}queued.classList.toggle('hidden',!e?.queued);queued.textContent='共享机会';
 dialog.dataset.cardKind=e?.kind||'end';if($('event').querySelector('.asset-row')&&!$('event').querySelector('.reference-asset-hint')){const hint=document.createElement('p');hint.className='reference-asset-hint';hint.textContent='在财务表中点选高亮资产，查看出售金额。';$('event').append(hint)}
 for(const b of $('event').querySelectorAll('[data-action]')){const a=b.dataset.action;if(labels[a]){b.setAttribute('aria-label',b.textContent);b.textContent=a==='confirm-stock'&&e?.mode==='sell'?'卖出':a==='buy'&&e?.kind==='dream'?'购买梦想':labels[a]}}
 if(e?.kind==='stockTrade'||e?.kind==='deal'&&e.offer.type==='stock'){
  const offer=e.offer,range=offer.rangeMin!==undefined?offer:D.small.find(a=>a.key===offer.key&&a.rangeMin!==undefined);const facts=$('event').querySelector('.deal-numbers');
  facts.innerHTML=`<div><span>每份价格</span><b>${money(offer.price)}</b></div><div><span>每份现金流</span><b>${money(offer.dividend||0)}</b></div>${range?`<div><span>常见交易区间</span><b>${money(range.rangeMin)} 至 ${money(range.rangeMax)}</b></div>`:''}<div><span>持有份数</span><b>${E.stockHeld(state,offer.key)}</b></div>`;
 }
 if($('stock-total'))$('stock-total').closest('.deal-numbers').classList.add('reference-stock-total');
 if(e?.kind==='borrowReview'&&!$('event').querySelector('[data-reference-step]')){
  const input=$('borrow-review-amount');input.closest('label').classList.add('reference-amount-input');input.setAttribute('inputmode','numeric');
  const arrows=document.createElement('div');arrows.className='event-buttons reference-amount-arrows';arrows.innerHTML='<button class="secondary" data-reference-step="-1000" aria-label="减少借款">▼</button><button class="secondary" data-reference-step="1000" aria-label="增加借款">▲</button>';$('event').append(arrows);
 }
 for(const input of $('event').querySelectorAll('input'))input.disabled=!!window.OnlineGame?.active&&!OnlineGame.isMyTurn();
 const failedRisk=e?.kind==='investmentRoll'&&e.die<e.rollmin;dialog.classList.toggle('reference-right-action',failedRisk);
 for(const [action,text] of [['stock-plus','▲'],['stock-minus','▼'],['debt-plus','▲'],['debt-minus','▼']]){const b=$('event').querySelector(`[data-action="${action}"]`);if(b){b.setAttribute('aria-label',action.endsWith('plus')?'增加':'减少');b.textContent=text}}
 $('minimize-event').textContent='−';$('minimize-event').title='收起当前卡片';
 $('begin-turn').textContent=state.skip?'确定':'掷骰';$('end-turn').textContent='结束回合';
 if(state.stage==='rat'){$('turn-repay').textContent='偿还';$('turn-borrow').textContent='借款'}
}
document.addEventListener('click',event=>{const b=event.target.closest('[data-reference-step]');if(!b||!game||window.OnlineGame?.active&&!OnlineGame.isMyTurn())return;const input=$('borrow-review-amount'),amount=Math.max(1000,Math.min(E.borrowLimit(state),(parseInt(input.value,10)||1000)+Number(b.dataset.referenceStep)));input.value=amount;input.dispatchEvent(new Event('input',{bubbles:true}));});
window.addEventListener('resize',()=>{if(game&&innerWidth>=100)present()});
const previous=render;render=function(){previous();present()};window.ReferenceUI={refresh:present};present();
})();
