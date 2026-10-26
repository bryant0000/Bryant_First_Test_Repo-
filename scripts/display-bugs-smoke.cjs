/* User-reported regressions: immediate drawer repaint, exclusive sheets and visible dice. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:960}});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  if(process.env.CASHFLOW_FAIL_FONT==='1')await page.addInitScript(()=>{document.fonts.load=()=>Promise.reject(Error('simulated local font denial'))});
  await page.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3041');
  await page.waitForFunction(()=>document.body.classList.contains('native-scene-ready'));
  await page.evaluate(()=>{localStorage.clear();ClassicStage.enter();$('offline-mode').click()});
  const pixels=()=>page.evaluate(()=>Array.from(document.getElementById('original-scene-art').getContext('2d').getImageData(80,100,120,120).data));
  const hash=data=>crypto.createHash('sha256').update(Buffer.from(data)).digest('hex');
  for(let job=0;job<12;job++){
   await page.evaluate(job=>{game=T.create([{name:'报表验收',jobId:job,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);render()},job);
   const closed=hash(await pixels());
   await page.locator('#statement-edge-tab').click();
   assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open),true);
   assert.notEqual(hash(await pixels()),closed,'opening repaints sheet immediately for job '+job);
   assert.equal(await page.locator('#reference-sheet').isVisible(),true);
   assert.equal(await page.locator('#reference-fast-sheet').isVisible(),false);
   const amounts=await page.locator('#ref-financial-summary>.finance-row').evaluateAll(rows=>rows.map(e=>({y:e.getBoundingClientRect().y,height:e.getBoundingClientRect().height})));
   assert.equal(amounts.length,3);
   for(let i=1;i<amounts.length;i++)assert.ok(amounts[i].y>=amounts[i-1].y+amounts[i-1].height,'summary rows do not overlap');
   if(job===3)await page.screenshot({path:'/tmp/cashflow-v063-rat-statement.png'});
   await page.locator('#statement-edge-tab').click();
   assert.equal(hash(await pixels()),closed,'closing restores board immediately for job '+job);
  }
  await page.evaluate(()=>{state.stage='fast';state.fastBase=350000;state.fastGain=10000;render()});
  await page.locator('#statement-edge-tab').click();
  assert.equal(await page.locator('#reference-sheet').isVisible(),false,'rat text must not appear over fast sheet');
  assert.equal(await page.locator('#reference-fast-sheet').isVisible(),true);
  assert.equal(await page.locator('#finance-slot').isVisible(),false);
  const heading=await page.locator('.classic-fast-win').boundingBox(),goal=await page.locator('.classic-fast-goal').boundingBox();
  assert.ok(heading.x+heading.width<=goal.x,'Chinese fast-track headings do not overlap');
  await page.screenshot({path:'/tmp/cashflow-v063-fast-statement.png'});
  await page.locator('#statement-edge-tab').click();
  for(const count of [1,2,3]){
   await page.evaluate(count=>{game=T.create([{jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});state=T.current(game);state.stage=count===3?'fast':'rat';state.charity=3;state.fastCharity=true;render()},count);
   if(!await page.locator('#finance-dialog').evaluate(e=>e.open))await page.locator('#statement-edge-tab').click();
   await page.locator('[data-turn-dice="'+count+'"]').click();
   await page.waitForSelector('#original-scene-art[data-dice-rolling="true"]',{state:'attached'});
   assert.equal(await page.locator('#finance-dialog').evaluate(e=>e.open),true);
   assert.equal(await page.locator('#original-scene-art').getAttribute('data-dice-origin'),'483.3,436.2','dice keep original anchor while the statement is open');
   await page.waitForFunction(()=>!CashflowUI.moving());
   const result=await page.evaluate(()=>({dice:state.lastDice,values:document.getElementById('original-scene-art').dataset.diceValues,rolling:document.getElementById('original-scene-art').dataset.diceRolling}));
   assert.equal(result.dice.length,count);assert.equal(result.values,result.dice.join(','));assert.equal(result.rolling,'false');
   if(await page.locator('#finance-dialog').evaluate(e=>e.open))await page.locator('#statement-edge-tab').click();
   const rendered=await page.evaluate(({count,frames})=>{
    const value=state.lastDice[0],f=frames['die'+value],left=483.3-(count-1)*76/2,top=436.2;
    const expected=document.createElement('canvas');expected.width=1024;expected.height=768;const ctx=expected.getContext('2d');
    ctx.setTransform(64/f[2],0,0,59/f[3],left,top);ctx.drawImage(ReferenceArt.images.dice,f[0],f[1],f[2],f[3],-f[5],-f[6],f[2],f[3]);
    const rect=[Math.round(left+18),Math.round(top+18),24,18];
    return {actual:Array.from(document.getElementById('original-scene-art').getContext('2d').getImageData(...rect).data),expected:Array.from(ctx.getImageData(...rect).data)};
   },{count,frames:require('../audit/dice-layout-fixtures.json').frames});
   assert.deepEqual(rendered.actual,rendered.expected,'original dice bitmap is actually drawn at the template anchor');
   if(count===3)await page.screenshot({path:'/tmp/cashflow-v063-three-dice.png'});
  }
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.locator('main').evaluate(e=>e.getBoundingClientRect().width),1024);
  assert.deepEqual(errors,[]);
  console.log('PASS 12 profession drawers repaint on click and close; statement rows do not overlap; fast/rat/legacy sheets are exclusive; 1/2/3 original atlas dice animate, retain actual results and keep their template anchor; phone fixed stage; font rejection does not stop renderer.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
