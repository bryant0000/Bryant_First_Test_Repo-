const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',args:['--no-sandbox'],headless:true});const errors=[];const contexts=[];try{
 for(let i=0;i<2;i++)contexts.push(await browser.newContext({viewport:{width:1360,height:960},reducedMotion:'reduce'}));
 const [host,guest]=await Promise.all(contexts.map(c=>c.newPage()));for(const p of [host,guest])p.on('pageerror',e=>errors.push(e.message));
 const base=process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3000',name='browser-'+Date.now();
 async function settled(p){await p.waitForFunction(()=>!OnlineGame.busy&&!CashflowUI.moving())}
 async function click(p,selector){await p.locator(selector).click();await settled(p)}
 await host.goto(base);await host.locator('#classic-title').click();await click(host,'#show-room-create');await host.locator('#room-name').fill(name);await host.locator('[data-room-capacity="2"]').click();await host.locator('#room-password').fill('1234');await click(host,'#create-room');await host.locator('#waiting-player-name').fill('房主');await host.locator('#waiting-player-name').press('Tab');await settled(host);
 await host.locator('#room-waiting').waitFor({state:'visible'});assert.equal(await host.locator('#start-room').isDisabled(),true);
 const id=await host.evaluate(()=>JSON.parse(localStorage.getItem('cashflow-online-session-v1')).id);
 await guest.setViewportSize({width:390,height:844});await guest.goto(base);await guest.locator('#classic-title').click();await click(guest,`[data-room-join="${id}"]`);await guest.locator('#join-room-password').fill('1234');await click(guest,'#confirm-room-join');await guest.locator('#waiting-player-name').fill('来宾');await guest.locator('#waiting-player-name').press('Tab');await settled(guest);
 await guest.locator('#room-ready').waitFor({state:'visible'});await click(guest,'#room-ready');await host.waitForFunction(()=>!document.getElementById('start-room').disabled);
 await click(host,'#start-room');await host.locator('[data-ui="accept-dream"]').waitFor({state:'visible'});await guest.waitForFunction(()=>OnlineGame.active);
 assert.equal(await guest.locator('[data-ui="accept-dream"]').isVisible(),false);
 await click(guest,'#toggle-classic-log');await guest.waitForTimeout(600);await guest.locator('#classic-chat-text').fill('<b>本地联机测试</b>');await guest.locator('#classic-chat-text').press('Enter');await settled(guest);await click(guest,'#toggle-classic-log');await host.waitForFunction(()=>OnlineGame.messages.some(m=>m.message==='<b>本地联机测试</b>'));await host.locator('#toggle-classic-log').click();assert.match(await host.locator('#classic-chat-log').textContent(),/<b>本地联机测试<\/b>/);assert.equal(await host.locator('#classic-chat-log b').count(),0);await host.locator('#toggle-classic-log').click();
 
 const hostRole=await host.evaluate(()=>state.jobId);await click(host,'[data-ui="dream-next"]');assert.equal(await host.evaluate(()=>state.dreamId),1);
 await click(host,'[data-ui="accept-dream"]');assert.equal(await host.evaluate(()=>game.ui),null);
 const hostCash=await host.evaluate(()=>state.cash),guestCash=await guest.evaluate(()=>OnlineGame.player().cash);
 await click(host,'#turn-borrow');await host.locator('#borrow-review-amount').fill('1000');await click(host,'[data-action="confirm-borrow"]');assert.equal(await host.evaluate(()=>state.cash),hostCash+1000);
 await guest.keyboard.press('f');assert.match(await guest.locator('#finance-heading').textContent(),/来宾/);assert.equal(await guest.evaluate(()=>OnlineGame.player().cash),guestCash);
 await click(host,'#turn-borrow');await guest.waitForFunction(()=>state.pending?.kind==='borrowReview');assert.equal(await guest.locator('#borrow-review-amount').isVisible(),false);assert.equal(await guest.locator('#finance-dialog').evaluate(e=>e.open),true);assert.match(await guest.locator('#finance-heading').textContent(),/来宾/);
 await click(host,'[data-action="cancelBorrowReview"]');await guest.waitForFunction(()=>!state.pending);assert.equal(await guest.locator('#finance-dialog').evaluate(e=>e.open),true);await guest.locator('#statement-edge-tab').click();
 let interruptResume=true;await host.route('**/api/rooms/'+id,route=>interruptResume?route.abort('failed'):route.continue());
 await host.reload();await host.waitForFunction(()=>document.getElementById('online-connection-notice').textContent.includes('重试'));assert.equal(await host.evaluate(()=>!!JSON.parse(localStorage.getItem('cashflow-online-session-v1'))?.token),true);assert.equal(await host.evaluate(()=>OnlineGame.active),false);
 const savedCash=await host.evaluate(()=>state.cash);await host.evaluate(()=>T.perform(game,'openBorrowReview'));assert.equal(await host.evaluate(()=>state.cash),savedCash);assert.equal(await host.evaluate(()=>state.pending),null);
 interruptResume=false;await host.waitForFunction(()=>OnlineGame.active);await host.unroute('**/api/rooms/'+id);assert.equal(await host.evaluate(()=>state.jobId),hostRole);assert.equal(await host.evaluate(()=>state.cash),hostCash+1000);
 await click(host,'#begin-turn');assert.equal(await host.evaluate(()=>game.rolled),true);
 for(let i=0;i<12;i++){const kind=await host.evaluate(()=>state.pending?.kind);if(!kind)break;const selectors={choose:'small',deal:'dismiss',charity:'dismiss',notice:'dismiss',stockSplit:'acceptSplit',payment:'payEvent',marketMust:'payEvent',loanOffer:'acceptLoan',baby:'confirmChild',debtHalved:'confirmRelief',recovery:'completeRecovery'};if(kind==='doodadChoice'){await click(host,'[data-action="pay-finance"]');continue}assert.ok(selectors[kind],'Unexpected first-turn card: '+kind);await click(host,`[data-action="${selectors[kind]}"]`)}
 assert.equal(await host.evaluate(()=>state.pending),null);await click(host,'#end-turn');await guest.waitForFunction(()=>game?.active===1&&game.ui?.introIndex===1);
 assert.equal(await host.locator('[data-ui="accept-dream"]').isVisible(),false);await host.keyboard.press('r');assert.equal(await host.evaluate(()=>game.rolled),false);
 await click(guest,'[data-ui="accept-dream"]');assert.equal(await guest.evaluate(()=>state.name),'来宾');
 await click(guest,'#turn-borrow');await guest.locator('#borrow-review-amount').fill('1000');await click(guest,'[data-action="confirm-borrow"]');assert.equal(await guest.evaluate(()=>state.cash),guestCash+1000);
 assert.equal(await guest.evaluate(()=>document.documentElement.scrollWidth>innerWidth),true);await click(guest,'#ui-exit');await click(guest,'#confirm-yes');await host.waitForFunction(()=>game?.active===0&&game.players[1].inactive);
 assert.equal(await host.evaluate(()=>state.bankrupt),false);assert.equal(await guest.evaluate(()=>OnlineGame.active),false);
 await click(host,'#ui-exit');await click(host,'#confirm-yes');assert.equal(await host.evaluate(()=>OnlineGame.active),false);
 assert.deepEqual(errors,[]);console.log('PASS: two isolated browsers, private room, ready/start, authoritative turn ownership, per-turn dreams, borrowing, own financial sheet, reload/resume after a temporary network failure, server dice/card settlement, handoff, mobile room exit and off-turn chat with escaped text; no browser errors');
 }finally{await browser.close()}})().catch(error=>{console.error(error);process.exitCode=1});
