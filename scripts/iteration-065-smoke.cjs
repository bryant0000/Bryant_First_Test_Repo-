/* Real browser inputs for the two evidence-backed v0.6.5 fixes. Fixture injection is local only. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
 const page=await browser.newPage({viewport:{width:1280,height:960}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3215');
 await page.waitForFunction(()=>document.body.classList.contains('native-scene-ready'));
 await page.evaluate(()=>{localStorage.clear();ClassicStage.enter();$('offline-mode').click();game=T.create([{jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);game.rolled=true;state.cash=1000000000;const offer=D.small.find(c=>c.type==='stock'&&c.price===5);state.pending={kind:'deal',title:offer.name,offer};render()});
 await page.locator('[data-action="open-stock-buy"]').click();
 assert.equal(await page.locator('#quantity').getAttribute('max'),'99999');
 await page.locator('#quantity').fill('100000');assert.equal(await page.locator('#quantity').inputValue(),'99999');
 await page.locator('[data-action="confirm-stock"]').click();assert.equal(await page.evaluate(()=>state.assets[0].quantity),99999);
 assert.equal(await page.evaluate(()=>state.cash),1000000000-99999*5);
 await page.evaluate(()=>{game=T.create([{jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);game.rolled=true;state.cash=310400;const offer=D.small.find(c=>c.key==='gold');state.assets=[{...offer,id:state.uid++,quantity:1}];E.applyMarket(state,{mode:'sell',key:'gold',amount:600});render()});
 assert.match(await page.locator('#event').textContent(),/600/);
 if(!await page.locator('#finance-dialog').evaluate(e=>e.open))await page.locator('#statement-edge-tab').click();
 await page.locator('#asset-table [data-sell]').click();assert.equal(await page.evaluate(()=>state.pending.kind),'assetSale');
 assert.equal(await page.evaluate(()=>state.pending.net),600);
 await page.screenshot({path:'/tmp/cashflow-v065-gold-confirmation.png'});
 await page.locator('[data-action="cancelAssetSale"]').click();assert.equal(await page.evaluate(()=>state.cash),310400);
 if(!await page.locator('#finance-dialog').evaluate(e=>e.open))await page.locator('#statement-edge-tab').click();
 await page.locator('#asset-table [data-sell]').click();await page.locator('[data-action="confirmAssetSale"]').click();
 assert.equal(await page.evaluate(()=>state.cash),311000);assert.equal(await page.evaluate(()=>state.assets.length),0);
 assert.deepEqual(errors,[]);console.log('PASS v0.6.5 real UI: 99,999 input bound and purchase; gold sale shows 600, cancellation preserves cash and confirmed sale credits 600 once; no page errors.');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
