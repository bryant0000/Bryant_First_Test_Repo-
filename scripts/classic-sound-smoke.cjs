/* Source sound contracts: original public card callbacks and statement tween. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const page=await browser.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.stack));
  await page.addInitScript(()=>{
   window.playedClips=[];
   HTMLMediaElement.prototype.play=function(){playedClips.push(this.src);return Promise.resolve()};
   HTMLMediaElement.prototype.pause=function(){};
  });
  await page.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3000');
  await page.locator('#classic-title').click();
  await page.evaluate(()=>{
   $('offline-mode').click();
   game=T.create([{jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE});
   state=T.current(game);state.cash=10000;save();render();
  });
  const played=id=>page.evaluate(id=>playedClips.includes(new URL(ClassicAudio[id],location.href).href),id);
  const reset=()=>page.evaluate(()=>{playedClips.length=0});
  assert.equal(await page.locator('#ui-sound').getAttribute('aria-pressed'),'true');
  await page.locator('#ui-sound').click();
  assert.equal(await page.locator('#ui-sound').getAttribute('aria-pressed'),'false');
  await reset();
  await page.locator('#turn-borrow').click();
  await page.locator('[data-action="cancelBorrowReview"]').click();
  assert.equal(await page.evaluate(()=>playedClips.length),0);
  await page.locator('#ui-sound').click();
  await reset();
  await page.locator('#statement-edge-tab').click();
  assert.ok(await played('financialStatementsOut'),'source opening callback uses Out clip');
  await reset();
  await page.locator('#statement-edge-tab').click();
  assert.ok(await played('financialStatementsIn'),'source closing callback uses In clip');
  await page.locator('#turn-repay').click();
  await reset();
  await page.locator('[data-repay="retail"]').click();
  assert.ok(await played('openToHumanv1'),'repayment card creation uses open clip');
  assert.equal(await played('paydayLand'),false,'payday clip waits for repayment confirmation');
  await reset();
  await page.locator('[data-action="confirm-debt"]').click();
  assert.ok(await played('paydayLand'),'repayment confirmation uses payday clip');
  await page.locator('#begin-turn').click();
  await page.waitForFunction(()=>!CashflowUI.moving());
  assert.ok(await played('diceRoll'));
  assert.deepEqual(errors,[]);
  console.log('PASS source sound controls: default on, mute suppresses sounds, original roll clip, source statement open/close IDs and repayment creation/confirmation timing; no browser errors.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
