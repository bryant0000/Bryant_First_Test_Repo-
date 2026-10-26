/* Reproduce the three screenshots using real inputs, drawer close events and board inspection. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs');
const diceFixture=require('../audit/dice-layout-fixtures.json');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync(require('node:path').join(__dirname,'../assets/reference/dice.png'))).digest('hex'),diceFixture.image_sha256);
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  for(const scale of [1,2]){
   const context=await browser.newContext({viewport:{width:1280,height:960},deviceScaleFactor:scale});
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3041');
   await page.waitForFunction(()=>document.body.classList.contains('native-scene-ready'));
   await page.evaluate(()=>{localStorage.clear();ClassicStage.enter();$('offline-mode').click()});
   assert.deepEqual(await page.evaluate(()=>ClassicArt.sprites.dice),diceFixture.frames);
   assert.deepEqual(await page.evaluate(()=>{const {x,y,width,height}=ClassicLayout.dice;return{x,y,width,height}}),diceFixture.anchor);
   for(const mode of ['buy','sell']){
    await page.evaluate(mode=>{
     game=T.create([{jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.cash=999999999;game.rolled=true;
     const offer={...D.small.find(c=>c.type==='stock'),price:500};
     state.assets=[{id:1,...offer,quantity:99999,cost:99999*500,value:99999*500,debt:0,income:0}];
     state.pending={kind:'deal',title:'股票份数核对',offer};E.openStock(state,mode);render();
    },mode);
    for(const quantity of ['1','10000','99999']){
     await page.locator('#quantity').fill(quantity);
     await page.waitForTimeout(25);
     const column=page.locator('.reference-stock-total'),caption=column.locator('span'),amount=column.locator('b');
     const c=await column.boundingBox(),a=await caption.boundingBox(),b=await amount.boundingBox();
     assert.ok(b.y>=a.y+a.height,'currency starts below caption');assert.ok(b.x>=c.x&&b.x+b.width<=c.x+c.width+.1,'currency column bounds');
     assert.ok(await amount.evaluate(e=>e.scrollWidth<=e.clientWidth+1),'entire currency text fits');
     assert.equal(await amount.textContent(),'$'+(Number(quantity)*500).toLocaleString('en-US'));
    }
   }
   await page.locator('#quantity').fill('123');const pendingBefore=await page.evaluate(()=>JSON.stringify(state.pending));
   await page.locator('#toggle-board-view').click();await page.waitForTimeout(100);
   assert.equal(await page.locator('dialog[open]').count(),0,'all sheets/cards retract for full board');
   assert.equal(await page.locator('#classic-footer').isVisible(),false);
   assert.equal(await page.locator('#statement-edge-tab').isVisible(),false);
   const boardPixels=await page.evaluate(()=>{
    const f=ClassicArt.sprites.board.board,c=document.createElement('canvas');c.width=1024;c.height=768;const g=c.getContext('2d');
    g.setTransform(922/f[2],0,0,610/f[3],52.15,86);g.drawImage(ReferenceArt.images.board,f[0],f[1],f[2],f[3],-f[5],-f[6],f[2],f[3]);
    return{actual:Array.from(document.getElementById('original-scene-art').getContext('2d').getImageData(800,120,40,30).data),expected:Array.from(g.getImageData(800,120,40,30).data)};
   });assert.deepEqual(boardPixels.actual,boardPixels.expected,'previously covered fast-track tiles are visible');
   await page.keyboard.press('r');await page.keyboard.press('e');
   assert.equal(await page.evaluate(()=>JSON.stringify(state.pending)),pendingBefore,'board viewing does not settle or roll');
   await page.locator('#toggle-board-view').click();await page.waitForTimeout(100);
   assert.equal(await page.locator('#quantity').inputValue(),'123','draft survives board inspection');
   assert.equal(await page.locator('#event-dialog').evaluate(e=>e.open),true);
   assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open),true);
   await page.locator('#quantity').fill('');
   await page.locator('#toggle-board-view').click();await page.locator('#toggle-board-view').click();
   assert.equal(await page.locator('#quantity').inputValue(),'');
   assert.equal(await page.locator('#stock-total').textContent(),'—','empty draft and its total restore together');
   await page.evaluate(()=>{
    state.stage='fast';state.fastBase=1030000;state.fastGain=50000;state.cash=1953080;state.lastDice=[1];
    state.pending={kind:'notice',title:'蒙大拿湖畔钓鱼',text:'这不是你开局选择的梦想。'};render();
   });
   const sourceIcon=await page.locator('#card-symbol>svg').getAttribute('data-art-sprite');
   for(let i=0;i<5;i++){
    if(!await page.locator('#finance-dialog').evaluate(e=>e.open))await page.locator('#statement-edge-tab').click();
    assert.equal(await page.locator('.classic-fast-income').count(),1);
    assert.equal(await page.locator('.fast-sheet-goals,.fast-sheet-totals').count(),0,'old fast markup never returns');
    assert.equal(await page.locator('#reference-sheet').isVisible(),false);
    assert.equal(await page.locator('#fast-sheet-income').textContent(),'$1,080,000');
    await page.locator('#statement-edge-tab').click();await page.waitForTimeout(60);
   }
   await page.locator('#statement-edge-tab').click();
   assert.equal(await page.locator('#card-symbol>svg').getAttribute('data-art-sprite'),sourceIcon,'drawer toggle preserves original card icon');
   const pixels=rect=>page.evaluate(rect=>Array.from(document.getElementById('original-scene-art').getContext('2d').getImageData(...rect).data),rect);
   const outside=await pixels([696,660,120,108]),inside=await pixels([106,688,523,78]);
   await page.evaluate(()=>{state.cash=9999999999999;state.fastBase=999999999999;render()});
   assert.deepEqual(await pixels([696,660,120,108]),outside,'large amounts cannot paint beyond statement');
   assert.notDeepEqual(await pixels([106,688,523,78]),inside,'large balances are actually painted');
   for(const selector of ['.classic-fast-target','.classic-fast-current>b'])assert.ok(await page.locator(selector).evaluate(e=>e.scrollWidth<=e.clientWidth+1),selector+' fits');
   assert.equal(await page.locator('#original-scene-art').getAttribute('data-dice-origin'),'483.3,436.2');
   await page.locator('#statement-edge-tab').click();await page.waitForTimeout(60);
   await page.locator('#statement-edge-tab').click();await page.waitForTimeout(60);
   assert.equal(await page.locator('.classic-fast-income').count(),1,'async close refresh preserves canonical layout');
   await page.locator('#toggle-board-view').click();
   await page.evaluate(()=>{state.pending={kind:'payment',effect:'tax',title:'税务检查',cost:1000};render()});
   assert.equal(await page.evaluate(()=>CashflowUI.inspecting()),false,'new decisions restore controls');
   assert.equal(await page.locator('#event-dialog').evaluate(e=>e.open),true);
   await page.evaluate(()=>{state.lastDice=[1];state.pending={kind:'investmentRoll',title:'投资结果',die:6,rollmin:6,reward:50000,income:0,paid:1000};render()});
   assert.equal(await page.locator('#original-scene-art').getAttribute('data-dice-values'),'6','risk card shows its own die rather than previous movement roll');
   await page.setViewportSize({width:390,height:844});
   assert.equal(await page.locator('.fast-sheet-goals,.fast-sheet-totals').count(),0);
   assert.deepEqual(errors,[]);
   await context.close();
  }
  console.log('PASS attachment regressions at 1x/2x: original dice image/frames/anchor; buy/sell captions and amounts never overlap; asynchronous drawer toggles keep one fast sheet; large balances stay within paper; unobstructed fast-track board view and draft restoration; keyboard guard, new-decision restore and phone resize.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
