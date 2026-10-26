/* Independent control positions from original cardTemplate and per-card configurations.
   Covers the finite control variants; does not assert localized prose equality. */
const{chromium}=require('playwright'),assert=require('node:assert/strict');
const cases=[
 ['choose',['small','big'],[799,1016],'icon_popup_deal'],
 ['property',['buy','dismiss'],[799,1016],'icon_popup_smDeal'],
 ['stock',['open-stock-buy','dismiss'],[799,1016],'icon_popup_smDeal'],
 ['stock-held',['open-stock-buy','open-stock-sell','dismiss'],[799,907,1016],'icon_popup_smDeal'],
 ['stock-buy',['confirm-stock','cancelStock'],[799,1016],'icon_popup_smDeal'],
 ['stock-sell',['confirm-stock','cancelStock'],[799,1016],'icon_popup_smDeal'],
 ['split',['acceptSplit'],[1016],'icon_popup_smDeal'],
 ['baby',['confirmChild'],[799],'icon_popup_baby'],['baby-max',['confirmChild'],[799],'icon_popup_baby'],
 ['doodad',['payEvent'],[799],'icon_popup_dodad'],['doodad-pass',['dismiss'],[1016],'icon_popup_dodad'],
 ['credit',['pay-cash','pay-finance'],[799,1016],'icon_popup_dodad'],['credit-exact',['pay-finance'],[1016],'icon_popup_dodad'],
 ['downsize',['payEvent'],[799],'icon_popup_downsizing'],
 ['charity',['donate','dismiss'],[799,1016],'icon_popup_charity'],['charity-poor',['dismiss'],[1016],'icon_popup_charity'],
 ['market',['dismiss'],[1016],'icon_popup_mrkt'],['market-empty',['dismiss'],[1016],'icon_popup_mrkt'],['market-must',['payEvent'],[799],'icon_popup_mrkt'],
 ['borrow',['confirm-borrow','cancelBorrowReview'],[799,1016],'icon_popup_borrow'],['loan',['acceptLoan','cancelLoan'],[799,1016],'icon_popup_borrow'],
 ['repay-picker',['cancelDebtPicker'],[1016],'icon_popup_repay'],['repay',['confirm-debt','cancelDebtReview'],[799,1016],'icon_popup_repay'],['repay-poor',['cancelDebtReview'],[1016],'icon_popup_repay'],
 ['bank',['confirm-debt','cancelDebtReview'],[799,1016],'icon_popup_repay'],['bank-poor',['cancelDebtReview'],[1016],'icon_popup_repay'],
 ['asset-sale',['confirmAssetSale','cancelAssetSale'],[799,1016],'icon_popup_mrkt'],
 ['bankrupt',[],[],'icon_popup_bankrupt'],['bankrupt-sale',['confirmAssetSale','cancelAssetSale'],[799,1016],'icon_popup_bankrupt'],
 ['bankrupt-pay',['confirm-debt','cancelDebtReview'],[799,1016],'icon_popup_bankrupt'],
 ['halve',['confirmRelief'],[799],'icon_popup_bankrupt'],['recovery',['completeRecovery'],[799],'icon_popup_bankrupt'],['loss',['confirmBankruptLoss'],[799],'icon_popup_bankrupt'],
 ['skip',['confirmSkip'],[799],'icon_popup_skipturn'],['enter-fast',['enterFast'],[799],'icon_popup_fasttrack'],
 ['fast-deal',['buy','dismiss'],[799,1016],'heat_and_a_c_service'],['fast-poor',['dismiss'],[1016],'heat_and_a_c_service'],['fast-owned',['dismiss'],[1016],'heat_and_a_c_service'],
 ['dream',['buy','dismiss'],[799,1016],'stock_market_for_kids'],['dream-poor',['dismiss'],[1016],'stock_market_for_kids'],['dream-other',['dismiss'],[1016],'yacht_racing'],
 ['fast-charity',['donate','dismiss'],[799,1016],'icon_popup_charity'],
 ['tax',['payEvent'],[799],'icon_popup_tax_audit'],['divorce',['payEvent'],[799],'icon_popup_divorce'],['lawsuit',['payEvent'],[799],'icon_popup_lawsuit']
];
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{const p=await b.newPage({viewport:{width:1280,height:960}}),errors=[];p.on('pageerror',e=>errors.push(e.stack));await p.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3000');await p.evaluate(()=>{localStorage.clear();ClassicStage.enter();$('offline-mode').click()});await p.evaluate(()=>ReferenceArt.ready);
for(const[id,actions,xs,icon]of cases){await p.evaluate(id=>{game=T.create([{jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.cash=1000000;game.rolled=true;const property={id:1,name:'住宅',key:'3/2HOUSE',type:'property',quantity:1,units:1,cost:2000,value:45000,debt:43000,income:250};const stock={...D.small.find(c=>c.key==='MYT4U'&&c.type==='stock'),price:5};let e={title:'操作核对'};
 if(id==='choose')e.kind='choose';if(id==='property')e={kind:'deal',title:'房产',offer:D.small.find(c=>c.type==='property')};
 if(id.startsWith('stock')){e={kind:'deal',title:'股票',offer:stock};if(id==='stock-held'||id==='stock-sell')state.assets=[{...stock,id:1,quantity:2,cost:10,value:10,debt:0,income:0}];state.pending=e;if(id==='stock-buy'||id==='stock-sell'){E.openStock(state,id==='stock-buy'?'buy':'sell');e=state.pending}}
 if(id==='split')e={kind:'stockSplit',title:'拆股',offer:{...stock,factor:2}};
 if(id==='baby'||id==='baby-max'){e.kind='baby';e.atLimit=id==='baby-max'}
 if(id==='doodad')e={kind:'payment',effect:'doodad',title:'额外支出',cost:150};if(id==='doodad-pass')e={kind:'notice',title:'子女支出',sourceId:'doodad.1'};
 if(id==='credit'||id==='credit-exact'){e={kind:'doodadChoice',title:'购买电视',cost:4000,loan:4000,payment:120,down:0};if(id==='credit-exact')state.cash=4000}
 if(id==='downsize')e={kind:'payment',title:'失业',effect:'downsize',cost:1620};
 if(id.startsWith('charity')){e={kind:'charity',title:'慈善',cost:250};if(id==='charity-poor')state.cash=0}
 if(id==='market')e={kind:'market',title:'市场报价',card:D.market.find(c=>c.mode==='sell')};if(id==='market-empty')e={kind:'notice',title:'没有机会',sourceId:'market.1'};if(id==='market-must')e={kind:'marketMust',title:'强制市场',cost:200};
 if(id==='borrow')e={kind:'borrowReview',title:'借款',amount:1000};if(id==='loan')e={kind:'loanOffer',title:'贷款',loan:1000,previous:{kind:'payment',cost:1000}};
 if(id==='repay-picker')e={kind:'debtPicker',title:'选择负债'};
 if(['repay','repay-poor','bank','bank-poor','bankrupt-pay'].includes(id)){const bank=id.startsWith('bank')&&id!=='bankrupt-pay';if(bank)state.loans.push({id:'bank',name:'银行借款',balance:2000,payment:200});e={kind:'debtReview',title:'偿还',loanId:bank?'bank':'retail',amount:1000,previous:{kind:'debtPicker'}};if(id.endsWith('poor'))state.cash=0;if(id==='bankrupt-pay')state.inBankruptcy=true}
 if(id==='asset-sale'||id==='bankrupt-sale'){state.assets=[property];e={kind:'assetSale',title:'出售',assetId:1,gross:70000,debt:43000,net:27000,previous:{kind:'market'}};if(id==='bankrupt-sale')state.inBankruptcy=true}
 if(id==='bankrupt'){state.inBankruptcy=true;state.assets=[property];e.kind='insolvent'}
 if(['halve','recovery','loss'].includes(id)){state.inBankruptcy=true;e.kind=({halve:'debtHalved',recovery:'recovery',loss:'bankruptLost'})[id]}
 if(id==='skip'){state.skip=2;e.kind='skipTurn'}if(id==='enter-fast')e.kind='enterFast';
 if(['fast-deal','fast-poor','fast-owned'].includes(id)){state.stage='fast';state.pos=2;e={kind:'fastDeal',title:'事业',cost:200000,income:10000};if(id==='fast-poor')state.cash=0;if(id==='fast-owned')game.players.push({...E.create(0,0,E.REFERENCE_PROFILE),name:'其他玩家',color:'#a8b240',fastAssets:[{position:2}]})}
 if(['dream','dream-poor','dream-other'].includes(id)){state.stage='fast';state.pos=id==='dream-other'?3:0;e={kind:id==='dream-other'?'notice':'dream',title:'梦想',cost:125000};if(id==='dream-poor')state.cash=0}
 if(id==='fast-charity'){state.stage='fast';state.pos=1;e={kind:'charity',title:'慈善',cost:100000}}
 if(['tax','divorce','lawsuit'].includes(id)){state.stage='fast';state.pos=9;e={kind:'payment',effect:id,title:id,cost:500000}}
 state.pending=e;save();render()},id);
 const buttons=p.locator('#event .reference-card-actions button:visible');assert.deepEqual(await buttons.evaluateAll(es=>es.map(e=>e.dataset.action)),actions,id+' actions');const actual=[];for(const button of await buttons.all()){const r=await button.boundingBox();actual.push(Math.round(r.x));assert.equal(Math.round(r.width),110,id+' source width');assert.equal(Math.round(r.height),44,id+' source height');assert.equal(Math.round(r.y),459,id+' action row');assert.ok(await button.evaluate(e=>{const r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return h===e||e.contains(h)}),id+' hit target')}assert.deepEqual(actual,xs,id+' source slots');assert.equal(await p.locator('#card-symbol>svg').getAttribute('data-art-sprite'),icon,id+' icon');if(id==='bank-poor')assert.equal(await p.locator('#debt-amount').count(),0);if(id==='bankrupt'||id==='asset-sale'||id==='bankrupt-sale')assert.equal(await p.locator('#asset-table .classic-ledger-row b').first().textContent(),'$45,000');
}
for(const stage of ['rat','fast']){await p.evaluate(stage=>{game=T.create([{jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.stage=stage;state.charity=3;state.fastCharity=true;save();render()},stage);const options=p.locator('[data-turn-dice]:visible');const positions=[];for(const o of await options.all())positions.push(Math.round((await o.boundingBox()).x));assert.deepEqual(positions,stage==='rat'?[799,907]:[799,907,1016],stage+' charity dice slots');await p.evaluate(()=>{game.rolled=true;state.pending=null;save();render()});assert.equal(await p.locator('#card-symbol>svg').getAttribute('data-art-sprite'),'icon_popup_endturn');if(stage==='fast')assert.equal(await p.locator('#event .classic-end-banking button').count(),0)}
assert.deepEqual(errors,[]);console.log('PASS '+cases.length+' source card contracts plus rat/fast charity and end-card variants: actions, source slots, hit targets and icons. Full prose equivalence is outside this test.')}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
