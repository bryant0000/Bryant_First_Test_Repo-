/* Browser paths for the pinned candidate profile; not a visual equivalence test. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1360,height:960},reducedMotion:'reduce'}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 async function rollTurn(){if(await page.locator('#turn-dialog').isVisible()){if(await page.locator('#begin-turn').isVisible())await page.locator('#begin-turn').click();else await page.locator('[data-turn-dice="1"]').click()}else await page.locator('#roll').click()}
 async function openFinancials(){if(await page.locator('#finance-dialog').evaluate(e=>e.open))return;if(await page.locator('#statement-edge-tab').isVisible())await page.locator('#statement-edge-tab').click();else if(await page.locator('#event-dialog').isVisible())await page.locator('#event-finances').click();else await page.locator('#turn-finances').click()}
 await page.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3000');
 await page.evaluate(()=>localStorage.clear());await page.reload();await page.locator('#offline-mode').click();
 assert.equal(await page.locator('#job').inputValue(),'random');
 await page.locator('#job').selectOption('0');await page.locator('#start').click();
 assert.equal(await page.evaluate(()=>state.rulesProfile), 'reference-web-2026-10-23');
 assert.equal(await page.evaluate(()=>state.pos),16);
 assert.equal(await page.evaluate(()=>state.cash),400);
 assert.equal(await page.locator('[data-ui="accept-career"]').count(),0);
 await page.locator('[data-ui="dream-next"]').click();assert.equal(await page.evaluate(()=>state.dreamId),1);
 await page.locator('[data-ui="dream-prev"]').click();assert.equal(await page.evaluate(()=>state.dreamId),0);
 await page.reload();await page.locator('[data-ui="accept-dream"]').click();
 // A profitable saved game still has a notice to acknowledge before entry.
 await page.evaluate(()=>{state.cash=12345;state.assets.push({id:state.uid++,name:'测试住宅',key:'3/2HOUSE',type:'property',quantity:1,units:1,cost:2000,value:35000,debt:33000,income:2600});state.pending={kind:'notice',title:'交易完成'};game.rolled=true;E.check(state);save();render()});
 await page.locator('[data-action="dismiss"]').click();
 assert.equal(await page.locator('#event-dialog').getAttribute('data-kind'),'enterFast');
 await page.reload();await page.locator('[data-action="enterFast"]').click();
 assert.deepEqual(await page.evaluate(()=>({stage:state.stage,cash:state.cash,pos:state.pos})),{stage:'fast',cash:260000,pos:42});
 assert.deepEqual(await page.locator('#dice-count option').allTextContents(),['1 颗骰子']);await openFinancials();assert.equal(await page.locator('#fast-sheet-goal').textContent(),'$310,000');assert.equal(await page.locator('#fast-sheet-income').textContent(),'$260,000');assert.equal(await page.locator('#fast-sheet-cash').textContent(),'$260,000');await page.locator('#close-finance').click();
 assert.equal(await page.evaluate(()=>game.rolled),false);
 await page.keyboard.press('f');await page.locator('#finance-dialog').waitFor({state:'visible'});
 assert.match(await page.locator('#expense-table').textContent(),/保留工资.*3,300.*保留总支出.*2,130/);
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.matches(':modal')),false);
 await page.locator('#close-finance').click();
 async function landOnRisk(cash,rng){
  await page.evaluate(({cash})=>{state.cash=cash;state.fastGain=0;state.fastAssets=[];state.won=false;state.pending=null;state.pos=D.fast.findIndex(a=>a.rollmin===3)-1;game.rolled=false;Math.random=()=>0;save();render()},{cash});
  await rollTurn();await page.locator('[data-action="buy"]').waitFor({state:'visible'});
  await page.evaluate(rng=>Math.random=()=>rng,rng);
  await page.locator('[data-action="buy"]').click();
  assert.equal(await page.locator('#confirm-dialog').evaluate(e=>e.open),false);
  await page.locator('[data-action="resolveInvestment"]').waitFor({state:'visible'});
 }
 await landOnRisk(400000,.5);
 assert.equal(await page.evaluate(()=>state.cash),250000);
 assert.equal(await page.evaluate(()=>state.fastAssets.length),0);
 assert.match(await page.locator('#event').textContent(),/4.*成功/);
 await page.reload();await page.locator('[data-action="resolveInvestment"]').waitFor({state:'visible'});
 assert.equal(await page.evaluate(()=>state.pending.die),4);
 assert.equal(await page.locator('[data-action="dismiss"]').count(),0);
 await openFinancials();
 assert.equal(await page.locator('#event-dialog').evaluate(e=>e.open&&!e.matches(':modal')),true);
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open&&!e.matches(':modal')),true);
 await page.locator('#close-finance').click();
 await page.locator('[data-action="resolveInvestment"]').click();
 assert.deepEqual(await page.evaluate(()=>({cash:state.cash,income:state.fastGain,assets:state.fastAssets.length})),{cash:250000,income:25000,assets:1});
 await landOnRisk(400000,0);await page.locator('[data-action="resolveInvestment"]').click();
 assert.equal(await page.evaluate(()=>state.fastAssets.length),0);
 assert.equal(await page.evaluate(()=>state.cash),250000);
 // Loading an older save must preserve its original profile, start position and dice.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}]);state=T.current(game);state.stage='fast';state.cash=100000;save()});
 await page.reload();await page.locator('#begin-turn').click();
 assert.equal(await page.evaluate(()=>state.rulesProfile),null);
 assert.deepEqual(await page.locator('#dice-count option').allTextContents(),['2 颗骰子']);
 // A shared reverse split stays unapplied until each owner confirms their card.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0},{jobId:1,dreamId:1}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);for(const p of game.players)p.assets.push({id:p.uid++,name:'MYT4U',type:'stock',key:'MYT4U',symbol:'MYT4U',quantity:3,cost:15,value:15,debt:0,income:0,dividend:0});state.pos=23;game.decks.small=[D.small.findIndex(a=>a.type==='split'&&a.key==='MYT4U'&&a.factor===.5)];Math.random=()=>0;save();render()});
 await rollTurn();await page.locator('[data-action="small"]').click();
 assert.equal(await page.evaluate(()=>state.assets[0].quantity),3);
 assert.equal(await page.locator('[data-action="buy"]').count(),0);
 await page.locator('[data-action="acceptSplit"]').click();await page.locator('#end-turn').click();
 assert.equal(await page.evaluate(()=>game.active),1);
 assert.equal(await page.evaluate(()=>state.assets[0].quantity),3);
 await page.reload();await page.locator('[data-action="acceptSplit"]').click();
 assert.equal(await page.evaluate(()=>state.assets[0].quantity),1);
 assert.equal(await page.evaluate(()=>state.turn),0);
 assert.equal(await page.evaluate(()=>game.rolled),false);
 // A queued ordinary stock quote exposes sale only; new quotes retain valid defaults.
 await page.evaluate(()=>{state.pending={kind:'deal',title:'MYT4U',offer:D.small.find(a=>a.type==='stock'&&a.key==='MYT4U'),queued:true};save();render()});
 assert.equal(await page.locator('[data-action="buy"]').count(),0);
 assert.equal(await page.locator('#quantity').count(),0);
 assert.equal(await page.locator('[data-action="open-stock-sell"]').count(),1);
 await page.evaluate(()=>{state.pending.queued=false;render()});
 await page.locator('[data-action="open-stock-buy"]').click();
 assert.equal(await page.locator('#quantity').inputValue(),'1');
 await page.locator('[data-action="cancelStock"]').click();
 // Mandatory payment and suggested loan remain separate decisions across reloads.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.pos=0;state.cash=50;game.decks.doodads=[20];Math.random=()=>0;save();render()});
 await rollTurn();await page.locator('[data-action="payEvent"]').waitFor({state:'visible'});
 assert.equal(await page.evaluate(()=>state.cash),50);
 assert.equal(await page.locator('[data-action="dismiss"]').count(),0);
 await page.locator('[data-action="payEvent"]').click();
 assert.equal(await page.evaluate(()=>state.pending.loan),2000);
 await page.locator('[data-action="cancelLoan"]').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'payment');
 await page.locator('[data-action="payEvent"]').click();await page.reload();
 await page.locator('[data-action="acceptLoan"]').click();
 assert.equal(await page.locator('#receipt-dialog').evaluate(e=>e.open),false);
 assert.equal(await page.evaluate(()=>state.cash),2050);
 assert.equal(await page.evaluate(()=>state.pending.kind),'payment');
 await page.locator('[data-action="payEvent"]').click();
 assert.equal(await page.evaluate(()=>state.cash),50);
 assert.equal(await page.evaluate(()=>state.loans.find(l=>l.id==='bank').payment),200);
 await page.evaluate(()=>{state.stage='fast';state.pos=24;state.cash=10001;game.rolled=false;Math.random=()=>0;render()});
 await rollTurn();await page.locator('[data-action="payEvent"]').waitFor({state:'visible'});
 assert.equal(await page.evaluate(()=>state.cash),10001);
 await page.locator('[data-action="payEvent"]').click();
 assert.equal(await page.evaluate(()=>state.cash),0);
 // Shared mandatory market cards wait for each owner's confirmation.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0},{jobId:1,dreamId:1}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);for(const p of game.players)p.assets.push({id:p.uid++,name:'创业公司',key:'widget',type:'business',quantity:1,units:1,cost:1000,value:1000,debt:0,income:0});state.pos=6;game.decks.market=[D.market.findIndex(c=>c.mode==='startup'&&c.key==='250')];Math.random=()=>0;save();render()});
 await rollTurn();await page.locator('[data-action="payEvent"]').waitFor({state:'visible'});
 assert.equal(await page.evaluate(()=>state.assets[0].income),0);
 await page.locator('[data-action="payEvent"]').click();
 assert.equal(await page.evaluate(()=>state.assets[0].income),250);
 assert.equal(await page.evaluate(()=>game.players[1].assets[0].income),0);
 await page.locator('#end-turn').click();await page.reload();
 await page.locator('[data-action="payEvent"]').click();
 assert.equal(await page.evaluate(()=>state.assets[0].income),250);
 assert.equal(await page.evaluate(()=>game.players[0].cardQueue.length),0);
 assert.equal(await page.evaluate(()=>game.rolled),false);
 // A property card's buy button submits directly, without extra checkout dialogs.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.pos=23;state.cash=10000;game.decks.small=[D.small.findIndex(c=>c.type==='property'&&c.down===2000)];Math.random=()=>0;save();render()});
 await rollTurn();await page.locator('[data-action="small"]').click();
 await page.locator('[data-action="buy"]').click();
 assert.equal(await page.evaluate(()=>state.cash),8000);
 assert.equal(await page.evaluate(()=>state.assets.length),1);
 assert.equal(await page.locator('#confirm-dialog').evaluate(e=>e.open),false);
 assert.equal(await page.locator('#receipt-dialog').evaluate(e=>e.open),false);
 await page.evaluate(()=>{state.pending={kind:'deal',title:'MYT4U',offer:D.small.find(c=>c.type==='stock'&&c.key==='MYT4U')};render()});
 await page.screenshot({path:'/tmp/cashflow-candidate-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:'/tmp/cashflow-candidate-mobile.png',fullPage:true});
 // The separate sell card spans all lots, persists quantity and ends the quote.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.cash=1000;game.rolled=true;for(const [q,c] of [[3,15],[2,20]])state.assets.push({id:state.uid++,name:'MYT4U',key:'MYT4U',symbol:'MYT4U',type:'stock',quantity:q,cost:c,value:c,debt:0,income:0,dividend:0});state.pending={kind:'deal',title:'MYT4U',offer:{name:'MYT4U',key:'MYT4U',symbol:'MYT4U',type:'stock',price:40,dividend:0}};save();render()});
 await page.locator('[data-action="open-stock-sell"]').click();
 assert.equal(await page.locator('#quantity').inputValue(),'5');
 await page.locator('[data-action="stock-minus"]').click();
 assert.equal(await page.locator('#quantity').inputValue(),'4');
 assert.equal(await page.locator('#stock-total').textContent(),'$160');
 await page.reload();assert.equal(await page.locator('#quantity').inputValue(),'4');
 await page.locator('[data-action="confirm-stock"]').click();
 assert.equal(await page.evaluate(()=>state.cash),1160);
 assert.equal(await page.evaluate(()=>E.stockHeld(state,'MYT4U')),1);
 assert.equal(await page.evaluate(()=>state.pending),null);
 // Bankruptcy recovery can be completed through the financial sheet and reloaded.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.pos=4;state.cash=0;state.loans.push({id:'bank',name:'银行借款',balance:15000,payment:1500});state.assets.push({id:state.uid++,name:'亏损住宅',key:'3/2HOUSE',type:'property',quantity:1,units:1,cost:8001,value:35000,debt:26999,income:-500});Math.random=()=>0;save();render()});
 await rollTurn();await page.locator('[data-action="finances"]').first().waitFor({state:'visible'});
 assert.equal(await page.evaluate(()=>state.inBankruptcy),true);
 assert.equal(await page.evaluate(()=>state.cash),0);
 await openFinancials();
 assert.equal(await page.locator('#borrow').isDisabled(),true);
 await page.locator('#asset-table [data-sell]').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'assetSale');
 await page.locator('[data-action="cancelAssetSale"]').click();
 assert.equal(await page.evaluate(()=>state.cash),0);
 await openFinancials();await page.locator('#asset-table [data-sell]').click();
 await page.locator('[data-action="confirmAssetSale"]').click();
 assert.equal(await page.evaluate(()=>state.cash),4000.5);
 await openFinancials();await page.locator('[data-repay="bank"]').click();
 await page.locator('#debt-amount').fill('4000');await page.locator('[data-action="confirm-debt"]').click();
 await page.reload();
 await page.locator('[data-action="completeRecovery"]').click();
 assert.equal(await page.evaluate(()=>state.skip),3);
 await page.locator('#end-turn').click();
 for(let i=0;i<3;i++){
  await page.locator('[data-action="confirmSkip"]').waitFor({state:'visible'});
  if(i===1)await page.reload();
  await page.locator('[data-action="confirmSkip"]').click();
  assert.equal(await page.evaluate(()=>state.pos),5);
 }
 assert.equal(await page.evaluate(()=>state.skip),0);
 // A failed recovery acknowledges its result and moves on to the next player.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0},{jobId:1,dreamId:1}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.pos=4;state.cash=0;state.loans.push({id:'bank',name:'银行借款',balance:15000,payment:1500});Math.random=()=>0;save();render()});
 await rollTurn();await page.locator('[data-action="confirmRelief"]').click();
 await page.locator('[data-action="confirmBankruptLoss"]').click();
 assert.equal(await page.evaluate(()=>game.active),1);
 assert.equal(await page.evaluate(()=>game.players[0].bankrupt),true);
 await page.locator('#turn-dialog').waitFor({state:'visible'});
 // Baby changes the statement only after acknowledgement, including after reload.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.pos=2;Math.random=()=>0;save();render()});
 await rollTurn();await page.locator('[data-action="confirmChild"]').waitFor({state:'visible'});
 assert.equal(await page.evaluate(()=>state.kids),0);
 await page.reload();await page.locator('[data-action="confirmChild"]').click();
 assert.equal(await page.evaluate(()=>state.kids),1);
 // Property sales use a dedicated preview card and close after the final match.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.cash=10000;game.rolled=true;for(let i=0;i<2;i++)state.assets.push({id:state.uid++,name:'测试住宅',key:'3/2HOUSE',type:'property',quantity:1,units:1,cost:2000,value:35000,debt:33000,income:220});E.applyMarket(state,{mode:'sell',key:'3/2HOUSE',amount:70000,global:true});save();render()});
 await page.locator('#event [data-sell]').first().click();
 assert.match(await page.locator('#event').textContent(),/37,000/);
 assert.equal(await page.evaluate(()=>state.cash),10000);
 await page.reload();await page.locator('[data-action="cancelAssetSale"]').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'market');
 await page.locator('#event [data-sell]').first().click();await page.locator('[data-action="confirmAssetSale"]').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'market');
 await page.locator('#event [data-sell]').click();await page.locator('[data-action="confirmAssetSale"]').click();
 assert.equal(await page.evaluate(()=>state.cash),84000);
 assert.equal(await page.evaluate(()=>state.pending),null);
 await page.locator('[data-action="open-debt-picker"]').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'debtPicker');
 await page.locator('[data-debt-choice="car"]').click();
 await page.locator('[data-action="cancelDebtReview"]').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'debtPicker');
 assert.equal(await page.evaluate(()=>state.cash),84000);
 await page.locator('[data-debt-choice="car"]').click();await page.locator('[data-action="confirm-debt"]').click();
 assert.equal(await page.evaluate(()=>state.cash),79000);
 assert.equal(await page.evaluate(()=>state.loans.some(l=>l.id==='car')),false);
 // Compare the Doctor figures directly with the observed official financial sheet.
 await page.setViewportSize({width:1360,height:960});
 await page.waitForFunction(()=>innerWidth===1360);
 await page.evaluate(()=>{game=null;state=null;save();render()});
 await page.locator('#job').selectOption('8');await page.locator('#start').click();
 assert.match(await page.locator('#intro-content').textContent(),/医生/);
 assert.equal(await page.evaluate(()=>state.cash),400);
 await page.locator('[data-ui="accept-dream"]').click();await openFinancials();
 assert.deepEqual(await page.evaluate(()=>[state.cash,E.totals(state).expenses,E.totals(state).flow]),[400,8900,4300]);
 assert.equal(await page.locator('#finance-cash').textContent(),'可用现金 $400');
 assert.equal(await page.locator('#turn-dialog').evaluate(e=>e.open&&!e.matches(':modal')),true);
 assert.equal(await page.evaluate(()=>state.loans.some(l=>l.id==='school')),false);
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open&&!e.matches(':modal')),true);
 await page.screenshot({path:'/tmp/cashflow-doctor-finances-candidate.png',fullPage:true});
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open),true);
 await page.locator('#close-finance').click();
 // Normal start-turn borrowing does not consume the roll or change cash on cancel.
 await page.locator('#turn-borrow').click();assert.equal(await page.evaluate(()=>state.pending.kind),'borrowReview');
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open&&!e.matches(':modal')),true);
 await page.locator('[data-action="cancelBorrowReview"]').click();assert.equal(await page.evaluate(()=>state.cash),400);
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open),false);
 await page.locator('#turn-borrow').click();await page.locator('#borrow-review-amount').fill('1000');await page.locator('[data-action="confirm-borrow"]').click();
 assert.equal(await page.evaluate(()=>state.cash),1400);assert.equal(await page.evaluate(()=>game.rolled),false);
 // Charity dice remain selectable directly on the start-turn card.
 await page.evaluate(()=>{state.pending=null;state.pos=23;state.charity=3;game.rolled=false;state.cash=10000;game.decks.doodads=[0];Math.random=()=>0;render()});
 await page.locator('[data-turn-dice="2"]').click();
 assert.deepEqual(await page.evaluate(()=>state.lastDice),[1,1]);
 assert.equal(await page.evaluate(()=>state.charity),2);
 assert.equal(await page.evaluate(()=>state.pos),1);
 await page.locator('[data-action="payEvent"]').click();
 assert.equal(await page.locator('#event #end-turn').count(),1);
 await page.locator('[data-action="open-borrow"]').click();await page.locator('[data-action="cancelBorrowReview"]').click();
 assert.equal(await page.locator('#event #end-turn').count(),1);
 assert.equal(await page.evaluate(()=>game.rolled),true);
 // The official Nurse sequence uses a picker before confirmation, with no payment button on a shortfall.
 await page.evaluate(()=>{game=T.create([{jobId:1,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);save();render()});
 await page.locator('#turn-repay').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'debtPicker');
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open&&!e.matches(':modal')),true);
 assert.equal(await page.locator('.repay-selectable [data-repay]').count(),4);
 await page.locator('[data-repay="retail"]').click();
 assert.equal(await page.locator('[data-action="confirm-debt"]').count(),0);
 assert.match(await page.locator('#event').textContent(),/现金不足/);
 await page.locator('[data-action="cancelDebtReview"]').click();
 assert.equal(await page.evaluate(()=>state.pending.kind),'debtPicker');
 await page.locator('[data-action="cancelDebtPicker"]').click();
 assert.equal(await page.evaluate(()=>game.rolled),false);
 await page.locator('#turn-borrow').click();await page.locator('#borrow-review-amount').fill('2000');await page.locator('[data-action="confirm-borrow"]').click();
 assert.equal(await page.evaluate(()=>state.cash),2480);
 await page.locator('#turn-repay').click();await page.locator('[data-repay="retail"]').click();
 await page.reload();assert.equal(await page.evaluate(()=>state.pending.previous.kind),'debtPicker');
 await page.locator('[data-action="confirm-debt"]').click();
 assert.deepEqual(await page.evaluate(()=>[state.cash,E.totals(state).expenses,E.totals(state).flow,game.rolled]),[1480,2100,1000,false]);
 assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open),false);
 await page.locator('#turn-repay').click();await page.locator('[data-repay="bank"]').click();
 assert.equal(await page.locator('#debt-amount').inputValue(),'1000');
 await page.locator('[data-action="debt-plus"]').click();assert.equal(await page.locator('#debt-amount').inputValue(),'1480');
 await page.reload();assert.equal(await page.locator('#debt-amount').inputValue(),'1480');
 await page.locator('[data-action="confirm-debt"]').click();
 assert.deepEqual(await page.evaluate(()=>[state.cash,state.loans.find(l=>l.id==='bank').balance,E.totals(state).flow]),[480,1000,1100]);
 await page.evaluate(()=>{game.rolled=true;save();render()});
 await page.locator('[data-action="open-debt-picker"]').click();await page.locator('[data-action="cancelDebtPicker"]').click();
 assert.equal(await page.locator('#event #end-turn').count(),1);
 assert.equal(await page.evaluate(()=>game.rolled),true);
 // On phones, liability choices stay on the decision card rather than behind another modal.
 await page.setViewportSize({width:390,height:844});
 await page.evaluate(()=>{game=T.create([{jobId:1,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);E.borrow(state,2000);save();render()});
 await page.locator('#turn-repay').click();await page.locator('[data-debt-choice="bank"]').click();
 await page.locator('#debt-amount').fill('1499');await page.reload();assert.equal(await page.locator('#debt-amount').inputValue(),'1499');
 await page.locator('[data-action="confirm-debt"]').click();
 assert.deepEqual(await page.evaluate(()=>[state.cash,state.loans.find(l=>l.id==='bank').balance,game.rolled]),[1480,1000,false]);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 // Fast-track actions with insufficient cash or another owner cannot be submitted from the card.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0},{jobId:1,dreamId:1}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.stage='fast';state.cash=1;state.pos=0;state.pending={kind:'dream',title:'梦想',cost:125000};game.rolled=true;save();render()});
 assert.equal(await page.locator('[data-action="buy"]').count(),0);
 await page.evaluate(()=>{state.cash=1000000;state.pos=D.fast.findIndex(c=>c.type==='business');game.players[1].fastAssets=[{position:state.pos}];state.pending={kind:'fastDeal',title:'已被购入的事业',cost:100000,income:10000};save();render()});
 assert.equal(await page.locator('[data-action="buy"]').count(),0);
 await page.locator('[data-action="dismiss"]').click();assert.equal(await page.evaluate(()=>state.cash),1000000);
 // Official Mechanic stock-loan observation: cancelling or accepting returns to quantity one.
 await page.evaluate(()=>{game=T.create([{jobId:3,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);E.borrow(state,5000);state.cash=6330;game.rolled=true;const offer=D.small.find(c=>c.type==='stock'&&c.key==='OK4U'&&c.price===10);state.pending={kind:'deal',title:offer.name,offer};save();render()});
 await page.locator('[data-action="open-stock-buy"]').click();await page.locator('#quantity').fill('1633');await page.locator('[data-action="confirm-stock"]').click();assert.equal(await page.evaluate(()=>state.pending.loan),10000);await page.locator('[data-action="cancelLoan"]').click();assert.equal(await page.locator('#quantity').inputValue(),'1');assert.equal(await page.evaluate(()=>state.cash),6330);
 await page.locator('#quantity').fill('1633');await page.locator('[data-action="confirm-stock"]').click();await page.reload();await page.locator('[data-action="acceptLoan"]').click();assert.equal(await page.locator('#quantity').inputValue(),'1');assert.equal(await page.evaluate(()=>state.cash),16330);await page.locator('[data-action="confirm-stock"]').click();assert.deepEqual(await page.evaluate(()=>[state.cash,state.assets[0].quantity]),[16320,1]);
 // Stock text inputs use whole shares and clamp to the available position as the original cards do.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.cash=1000;game.rolled=true;state.pending={kind:'deal',title:'MYT4U',offer:{name:'MYT4U',key:'MYT4U',symbol:'MYT4U',type:'stock',price:40,dividend:0}};save();render()});
 await page.locator('[data-action="open-stock-buy"]').click();await page.locator('#quantity').fill('1.9');assert.equal(await page.locator('#stock-total').textContent(),'$40');await page.locator('[data-action="confirm-stock"]').click();assert.deepEqual(await page.evaluate(()=>[state.cash,state.assets[0].quantity]),[960,1]);
 await page.evaluate(()=>{state.pending={kind:'deal',title:'MYT4U',offer:{name:'MYT4U',key:'MYT4U',symbol:'MYT4U',type:'stock',price:40,dividend:0}};save();render()});await page.locator('[data-action="open-stock-sell"]').click();await page.locator('#quantity').fill('9999');assert.equal(await page.locator('#quantity').inputValue(),'1');await page.locator('[data-action="confirm-stock"]').click();assert.deepEqual(await page.evaluate(()=>[state.cash,state.assets.length]),[1000,0]);
 // Fast-track charity offers three direct roll buttons without a separate selection step.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.stage='fast';state.fastBase=100000;state.fastCharity=true;state.cash=1000000;state.pos=4;Math.random=()=>0;save();render()});
 assert.equal(await page.locator('[data-turn-dice]').count(),3);assert.equal(await page.locator('#begin-turn').isVisible(),false);await page.locator('[data-turn-dice="3"]').click();await page.waitForFunction(()=>!CashflowUI.moving());assert.deepEqual(await page.evaluate(()=>state.lastDice),[1,1,1]);assert.equal(await page.evaluate(()=>state.pos),7);
 // Payday lands directly on the end card; capped children still require the baby acknowledgement.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.pos=4;Math.random=()=>0;save();render()});
 await rollTurn();await page.waitForFunction(()=>!CashflowUI.moving());assert.equal(await page.evaluate(()=>state.pending),null);assert.equal(await page.locator('#event #end-turn').count(),1);assert.equal(await page.locator('[data-action="dismiss"]').count(),0);
 await page.evaluate(()=>{state.kids=3;state.pos=2;state.pending=null;game.rolled=false;save();render()});
 const cappedExpenses=await page.evaluate(()=>E.totals(state).expenses);await rollTurn();await page.locator('[data-action="confirmChild"]').waitFor({state:'visible'});await page.reload();await page.locator('[data-action="confirmChild"]').click();assert.deepEqual(await page.evaluate(()=>[state.kids,E.totals(state).expenses]),[3,cappedExpenses]);
 await page.evaluate(()=>{state.kids=0;state.cash=1;state.pos=18;state.pending=null;game.rolled=false;Math.random=()=>0;save();render()});await rollTurn();await page.locator('[data-action="dismiss"]').waitFor({state:'visible'});assert.equal(await page.locator('[data-action="donate"]').count(),0);await page.locator('[data-action="dismiss"]').click();
 // Cashflow and dream victories have distinct, persistent end cards.
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.stage='fast';state.fastGain=50000;E.check(state);save();render()});
 assert.equal(await page.locator('#event-dialog').getAttribute('data-kind'),'win-cashflow');assert.match(await page.locator('#event').textContent(),/新增现金流.*50,000/);assert.equal(await page.locator('#end-turn').isVisible(),false);await page.reload();assert.equal(await page.locator('#event-dialog').getAttribute('data-kind'),'win-cashflow');await openFinancials();await page.locator('#close-finance').click();
 await page.evaluate(()=>{game=T.create([{jobId:0,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.stage='fast';state.pos=E.dreams[0].position;state.cash=E.dreams[0].cost;state.pending={kind:'dream',title:E.dreams[0].name,cost:state.cash};game.rolled=true;save();render()});
 await page.locator('[data-action="buy"]').click();assert.equal(await page.locator('#event-dialog').getAttribute('data-kind'),'win-dream');assert.match(await page.locator('#event').textContent(),/已支付梦想费用/);assert.equal(await page.evaluate(()=>state.cash),0);await page.reload();assert.equal(await page.locator('#event-dialog').getAttribute('data-kind'),'win-dream');await page.setViewportSize({width:390,height:844});assert.equal(await page.locator('[data-terminal-exit]').isVisible(),true);await page.locator('[data-terminal-exit]').click();await page.locator('#confirm-yes').click();assert.equal(await page.evaluate(()=>game),null);await page.setViewportSize({width:1360,height:960});
 // Careers are assigned on start with replacement and persist through dream selection/reload.
 await page.evaluate(()=>{game=null;state=null;save();render();Math.random=()=>.999});
 await page.locator('#player-count').selectOption('2');await page.locator('#job').selectOption('0');await page.locator('#job-1').selectOption('1');
 await page.locator('#random-jobs').click();assert.equal(await page.locator('#job').inputValue(),'random');assert.equal(await page.locator('#job-1').inputValue(),'random');
 await page.locator('#player-name').fill('玩家甲');await page.locator('#name-1').fill('玩家乙');await page.locator('#start').click();
 assert.deepEqual(await page.evaluate(()=>game.players.map(p=>[p.jobId,p.cash,p.name])),[[11,560,'玩家甲'],[11,560,'玩家乙']]);
 await page.reload();assert.deepEqual(await page.evaluate(()=>game.players.map(p=>p.jobId)),[11,11]);
 await page.locator('[data-ui="accept-dream"]').click();
 assert.equal(await page.locator('#intro-dialog').evaluate(e=>e.open),false);
 assert.equal(await page.evaluate(()=>state.name),'玩家甲');
 await page.evaluate(()=>{game.rolled=true;state.pending=null;T.end(game);save();render()});
 assert.equal(await page.evaluate(()=>game.ui.introIndex),1);
 await page.reload();await page.locator('[data-ui="accept-dream"]').click();
 assert.equal(await page.evaluate(()=>state.name),'玩家乙');
 assert.deepEqual(errors,[]);
 console.log('PASS: new profile, entry acknowledgement/reload/confirmation, fast single die and statement, risk payment/result persistence/success/failure, legacy-save compatibility, multiplayer queued split/reload and stock quote controls, mandatory payment/loan/cancel/reload and divorce confirmation, shared mandatory market effects, direct card purchase, stock subcards/cancel/quantity/reload/sale, bankruptcy recovery/skips/loss/handoff, baby acknowledgement, asset sale/debt subcards, official Doctor financial values, docked panels, one-click turn and charity dice, mobile overflow, official Nurse repayment picker/shortfall/cancel/restore/rounding/mobile and automatic fast-track handoff; no browser errors');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
