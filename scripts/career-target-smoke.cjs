/* Source-first career verification. Seed only our own local client; never the publisher. */
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const E=require('../engine.js'),source=require('../audit/original-target-2026-11-04/careers.json').careers.careerData;
const fields={salary:'salary',tax:'taxes',homePayment:'mortgagePayment',schoolPayment:'schoolLoanPayment',carPayment:'carLoanPayment',creditPayment:'creditCardPayment',retailPayment:'retailPayment',other:'otherExpenses',savings:'savings',childCost:'childPerExpense',homeDebt:'mortgageLiability',schoolDebt:'schoolLoanLiability',carDebt:'carLoanLiability',creditDebt:'creditCardLiability',retailDebt:'retailDebtLiability'};
(async()=>{
 let fieldChecks=0;for(const job of E.jobs){const target=source.find(c=>c.title===job.english);assert.ok(target,job.english);for(const [current,original] of Object.entries(fields)){assert.equal(job[current],target[original],job.english+' '+current);fieldChecks++}}
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']}),rows=[];
 try{for(let id=0;id<E.jobs.length;id++){
  const context=await browser.newContext({viewport:{width:1280,height:960}});await context.addInitScript(value=>{Math.random=()=>value},(id+.25)/E.jobs.length);
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3304/index.html?offline=1');
  await page.locator('#classic-title').click();await page.locator('#show-room-create').click();await page.locator('#room-name').fill('职业核验');await page.locator('#create-room').click();await page.locator('#start-room').click();
  assert.equal(await page.evaluate(()=>state.jobId),id);assert.equal(await page.evaluate(()=>state.cash),E.jobs[id].savings);
  await page.locator('[data-ui="dream-next"]').click();assert.equal(await page.evaluate(()=>state.jobId),id);
  await page.locator('[data-ui="accept-dream"]').click();await page.locator('#statement-edge-tab').click();assert.match(await page.locator('#income-table').textContent(),new RegExp(E.jobs[id].name));
  await page.reload();await page.waitForFunction(()=>state&&game);assert.equal(await page.evaluate(()=>state.jobId),id);assert.deepEqual(errors,[]);
  rows.push({id,career:E.jobs[id].english,name:E.jobs[id].name,starting_cash:E.jobs[id].savings,assigned:true,dream_change_preserves_career:true,statement_displays_career:true,reload_preserves_career:true});await context.close();console.log('PASS local career '+id+' '+E.jobs[id].english);
 }}finally{await browser.close()}
 const report={date:'2026-11-04',game_version:'0.6.5',passed:true,source:'Pinned public careers.json, SHA matches historical official resource record; not a new live publisher observation',field_checks:fieldChecks,careers:rows,scope:'Our own local browser entry with deterministic test RNG; proves 12 careers are implemented and retained, not whether original offers a career selector',original_career_selection_confirmed_today:false};fs.writeFileSync(path.resolve(__dirname,'../audit/original-target-2026-11-04/career-verification.json'),JSON.stringify(report,null,2));
 console.log('PASS '+fieldChecks+' original numeric field comparisons and '+rows.length+' real local-browser career/dream/statement/reload paths.');
})().catch(e=>{console.error(e);process.exitCode=1});
