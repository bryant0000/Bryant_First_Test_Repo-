/* Presentation of the observed classic web cards. Financial commands stay in the existing engine. */
(function(){
'use strict';
document.body.classList.add('classic-shell');
const labels={small:'小买卖',big:'大买卖','open-stock-buy':'买入','open-stock-sell':'卖出',buy:'买入',dismiss:'跳过','confirm-stock':'买入',cancelStock:'取消',payEvent:'支付',acceptLoan:'是',cancelLoan:'否',enterFast:'确定',resolveInvestment:'确定','pay-cash':'全款','pay-finance':'分期',donate:'捐赠',confirmChild:'确定',confirmSkip:'确定',acceptSplit:'确定',confirmRelief:'确定',completeRecovery:'确定',confirmBankruptLoss:'确定','confirm-borrow':'借款',cancelBorrowReview:'取消',cancelDebtPicker:'取消','confirm-debt':'支付',cancelDebtReview:'取消',cancelAssetSale:'返回',confirmAssetSale:'出售'};
const paths={home:'M8 29 32 8l24 21M15 25v30h34V25M27 55V37h12v18M20 28h7v7h-7M39 28h7v7h-7',money:'M45 18c-5-8-27-7-27 6 0 14 29 7 29 21 0 13-24 16-32 5M32 6v52',dice:'M12 16h36v36H12zM20 24h1M39 24h1M29 34h1M20 44h1M39 44h1',heart:'M32 54 9 32C-5 13 20 0 32 19 44 0 69 13 55 32Z',family:'M20 12a7 7 0 1 0 0 .1M44 12a7 7 0 1 0 0 .1M8 49V29h21v20M35 49V29h21v20M26 53V42h12v11',market:'M10 22h44M14 22v32h36V22M8 13h48v9H8zM26 54V38h12v16',briefcase:'M8 22h48v32H8zM22 22V12h20v10M8 34h48M29 30h6v9h-6',chart:'M10 10v44h46M17 43l12-15 12 7 14-23'};
function symbolPath(){const e=state.pending;if(!e)return'dice';if(e.kind==='choose'||e.kind==='deal'||e.kind==='stockTrade')return'home';if(e.kind==='baby')return'family';if(e.kind==='charity')return'heart';if(e.kind==='market'||e.kind==='marketMust'||e.kind==='assetSale')return'market';if(e.kind==='fastDeal'||e.kind==='investmentRoll')return'chart';if(e.kind==='skipTurn')return'briefcase';return'money'}
function icon(key){return `<svg viewBox="0 0 64 64" aria-hidden="true"><path d="${paths[key]}"/></svg>`}
function sheet(){
 if(!CashflowUI.docked()){finances();return}const p=window.OnlineGame?.player()||state;if(p.stage!=='rat')return;
 const t=E.ratTotals(p),job=E.jobs[p.jobId],stocks=p.assets.filter(a=>a.type==='stock'),properties=p.assets.filter(a=>a.type!=='stock');
 const blank=n=>Array.from({length:Math.max(0,n)},()=>'<div class="classic-ledger-blank" aria-hidden="true"></div>').join('');
 const lines=(items,label,value)=>items.map(a=>row(esc(label(a)),value(a))).join('');
 $('income-table').innerHTML=row(esc(job.name)+'工资',job.salary)+'<h4>利息 / 分红</h4>'+lines(stocks,a=>a.symbol||a.name,a=>a.income)+blank(1-stocks.length)+'<h4>房地产 / 事业</h4>'+lines(properties,a=>a.name,a=>a.income)+blank(2-properties.length);
 const labels={home:'住房抵押贷款月供',car:'汽车贷款月供',credit:'信用卡月供',retail:'零售债务月供',bank:'银行借款月供'};
 const ordered=['home','car','credit','retail'];$('expense-table').innerHTML=row('税金',job.tax)+ordered.flatMap(id=>p.loans.filter(l=>l.id===id).map(l=>row(labels[id]||esc(l.name),l.payment))).join('')+row('其他生活支出',job.other)+p.loans.filter(l=>!ordered.includes(l.id)).map(l=>row(labels[l.id]||esc(l.name)+'月供',l.payment)).join('')+(p.kids?row('子女支出 · '+p.kids+' 人',p.kids*job.childCost):'')+blank(7-(2+p.loans.length+(p.kids?1:0)));
 const assetRow=a=>{const q=E.quote(p,a),tag=q?'button':'div',attrs=q?` type="button" data-sell="${a.id}"`:'';return `<${tag}${attrs} class="classic-ledger-row ${q?'classic-ledger-selectable':''}"><span>${esc(a.symbol||a.name)}${a.type==='stock'?' · '+a.quantity+' 份':''}</span><b>${money(a.type==='stock'?a.cost/a.quantity:a.value)}</b></${tag}>`};
 $('asset-table').innerHTML='<h4>股票 / 基金 / 存单 <span>每份成本</span></h4>'+stocks.map(assetRow).join('')+blank(3-stocks.length)+'<h4>房地产 / 事业 <span>成本</span></h4>'+properties.map(assetRow).join('')+blank(3-properties.length);
 const selecting=['debtPicker','insolvent'].includes(p.pending?.kind);$('loan-table').innerHTML=p.loans.map(l=>{const tag=selecting?'button':'div';return `<${tag}${selecting?` type="button" data-repay="${l.id}"`:''} class="classic-ledger-row ${selecting?'classic-ledger-selectable':''}"><span>${esc(l.name)}</span><b>${money(l.balance)}</b></${tag}>`}).join('');
 $('ref-property-debts').innerHTML='<h4>房地产 / 事业 <span>贷款余额</span></h4>'+lines(properties,a=>a.name,a=>a.debt)+blank(3-properties.length);
}
function present(){if(!game||!state||!E.isReference(state))return;sheet();const e=state.pending,dialog=$('event-dialog');
 $('card-symbol').innerHTML=icon(symbolPath());
 $('turn-marker').innerHTML=icon('dice');$('turn-marker').setAttribute('aria-hidden','true');
 const actions=Array.from($('event').children).filter(n=>n.classList.contains('event-buttons')&&!n.classList.contains('reference-amount-arrows'));
 if(e||state.won||game.over){const group=actions.at(-1);if(group)group.classList.add('reference-card-actions');}
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
 if(e?.kind==='deal'&&e.offer.type!=='stock'){const a=e.offer,facts=$('event').querySelector('.deal-numbers');if(facts)facts.innerHTML=`<div><span>价格</span><b>${money(a.value)}</b></div><div><span>现金流</span><b>${money(a.income)}</b></div><div><span>首付</span><b>${money(a.down)}</b></div>`;}
 if(e?.kind==='investmentRoll'){const success=e.die>=e.rollmin,facts=$('event').querySelector('.deal-numbers');for(const p of $('event').querySelectorAll(':scope>p'))p.remove();if(facts)facts.innerHTML=`<div><span>掷骰结果</span><b>${e.die}</b></div><div><span>${e.reward?'现金奖励':'新增现金流'}</span><b>${money(success?(e.reward||e.income||0):0)}</b></div>`;}
 if(e?.kind==='payment'&&e.effect==='doodad'){const p=$('event').querySelector(':scope>p');if(p)p.textContent='支付 '+money(e.cost);$('event').querySelector('.deal-numbers')?.remove();}
 if(e?.kind==='doodadChoice'){const p=$('event').querySelector(':scope>p');if(p)p.textContent='支付 '+money(e.cost);const facts=$('event').querySelector('.deal-numbers');if(facts)facts.textContent=e.down?'使用借款支付时，首付 '+money(e.down)+'，增加贷款 '+money(e.loan)+'，每月增加支出 '+money(e.payment)+'。':'使用信用卡支付时，增加信用卡债务 '+money(e.loan)+'，每月增加支出 '+money(e.payment)+'。';const credit=$('event').querySelector('[data-action="pay-finance"]');if(credit)credit.textContent=e.down?'借款':'信用卡';}
 if(e?.kind==='debtReview'){const p=$('event').querySelector(':scope>p'),facts=$('event').querySelector('.deal-numbers'),loan=state.loans.find(l=>l.id===e.loanId);if(e.loanId==='bank'){if(state.cash>=1000){if(p)p.textContent='输入要偿还的银行贷款金额。';if(facts)facts.textContent='还款金额必须是 1,000 的整数倍。'}else{p?.remove();facts?.remove();$('debt-amount')?.closest('label')?.remove();$('event').querySelector('.reference-amount-arrows')?.remove();$('event').querySelector('.repay-shortfall')?.remove();}}else{if(p)p.textContent='贷款金额：'+money(loan?.balance||0);if(facts)facts.textContent=state.cash>=(loan?.balance||0)?'确认偿还这项贷款。':'现金不足，当前无法偿还这项负债。';$('event').querySelector('.repay-shortfall')?.remove();}}
 if(e?.kind==='payment'&&['tax','lawsuit','divorce'].includes(e.effect)){$('event').querySelector('.deal-numbers')?.remove();const button=$('event').querySelector('[data-action="payEvent"]');if(button)button.textContent='确定';}
 if(e?.kind==='payment'&&e.effect==='downsize'){const facts=$('event').querySelector('.deal-numbers');if(facts)facts.textContent='支付 '+money(e.cost);}
 if(e?.kind==='assetSale'){const p=$('event').querySelector(':scope>p'),facts=$('event').querySelector('.deal-numbers');if(state.inBankruptcy){if(p)p.textContent='出售所得：'+money(e.net);facts?.remove();const title=$('event').querySelector('h3');if(title)title.textContent='出售资产';}else{if(p)p.innerHTML='出售报价扣除抵押贷款后，得到净收入。<br>'+money(e.gross)+' - '+money(e.debt)+' = '+money(e.net);if(facts)facts.textContent='出售所得：'+money(e.net);}}
 if(e?.kind==='baby'&&!e.atLimit){const p=$('event').querySelector(':scope>p');if(p)p.textContent='家庭迎来新的孩子。';const facts=document.createElement('div');facts.className='deal-numbers';facts.textContent='每个孩子的月支出：'+money(E.jobs[state.jobId].childCost);p?.after(facts);}
 if(e?.kind==='charity'&&state.stage==='rat'&&state.cash<e.cost){const facts=$('event').querySelector('.deal-numbers');if(facts)facts.textContent='现金不足，无法捐赠。';}
 if(e?.kind==='debtHalved'||e?.kind==='recovery'){const p=$('event').querySelector(':scope>p');if(p)p.textContent=e.kind==='debtHalved'?'已无可出售资产，且现金流仍不为正。':'月现金流已经恢复为正。';const facts=document.createElement('div');facts.className='deal-numbers';facts.textContent=e.kind==='debtHalved'?'汽车贷款、信用卡和零售债务及其月供减半。':'接下来休整三个回合。';p?.after(facts);}
 if(e?.kind==='insolvent'&&state.inBankruptcy){const p=$('event').querySelector(':scope>p');if(p)p.innerHTML='当前现金流：'+money(E.ratTotals(state).flow)+'。<br>恢复正现金流后才能完成重整。';const facts=document.createElement('div');facts.className='deal-numbers';facts.innerHTML='1. 以首付的一半清算资产。<br>2. 偿还个人债务。<br>3. 偿还银行借款。';p?.after(facts);}
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
