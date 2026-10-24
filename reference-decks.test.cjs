/* Expected transaction amounts come from publisher JSON projections, not game data.
 * These are source/data regressions; they do not certify full screen/text equivalence. */
const test=require('node:test'),assert=require('node:assert/strict');
const E=require('./engine.js'),facts=require('./audit/official-card-facts.json');
const fresh=()=>E.create(0,0,E.REFERENCE_PROFILE);
for(const deck of ['small','big'])for(const [index,card] of facts.decks[deck].cards.entries())test(`publisher ${deck}.${index}: mapped facts and completed transaction`,()=>{
 const s=fresh();s.cash=1000000000;s.pending={kind:'choose'};s.decks[deck]=[index];E.deal(s,deck);
 if(card.type.includes('stock')){
  if(card.cost<0){const offer=s.pending.offer;s.assets=[{id:s.uid++,type:'stock',key:card.key,symbol:card.key,name:card.key,quantity:3,cost:300,value:300,debt:0,income:0,dividend:0}];assert.equal(s.pending.kind,'stockSplit');E.acceptSplit(s);assert.equal(s.assets[0].quantity,card.cost===-1?6:1);assert.equal(s.cash,1000000000);return}
  assert.equal(s.pending.offer.anyoneBuy,card.type==='smalldeal_anystock');E.openStock(s,'buy');E.confirmStock(s,3);
  assert.equal(s.cash,1000000000-card.cost*3);assert.equal(s.assets[0].cost,card.cost*3);assert.equal(s.assets[0].income,(card.cashflow||0)*3);assert.equal(s.assets[0].key,card.key);assert.equal(s.assets[0].quantity,3);return;
 }
 E.buy(s);const a=s.assets[0];assert.equal(a.key,card.key);assert.equal(a.quantity,1);assert.equal(a.value,card.cost);assert.equal(a.cost,card.downpay??card.cost);assert.equal(a.debt,card.mortgage||0);assert.equal(a.income,card.cashflow||0);assert.equal(a.units,Number(card.units||1));assert.equal(s.cash,1000000000-(card.downpay??card.cost));
});
for(const [index,card] of facts.decks.doodads.cards.entries())for(const kids of [0,2])test(`publisher doodads.${index}: ${kids} children, cash confirmation`,()=>{
 const s=fresh();s.cash=1000000;s.kids=kids;s.pos=0;s.decks.doodads=[index];E.roll(s,1,()=>0);
 if(card.child&&!kids){assert.equal(s.pending.kind,'notice');assert.equal(s.cash,1000000);return}
 assert.equal(s.cash,1000000);const cost=card.child==='per'?card.cost*kids:card.cost;
 if(card.type==='specialDoodad')E.payDoodad(s,false);else{assert.equal(s.pending.kind,'payment');E.payEvent(s)}
 assert.equal(s.cash,1000000-cost);assert.equal(s.pending,null);
});
test('all 45 publisher market facts map to the displayed deck without dropping duplicate cards',()=>{
 assert.equal(E.data.market.length,45);for(const [index,card] of facts.decks.market.cards.entries()){const own=E.data.market[index];assert.equal(own.sourceId,`market.${index}`);assert.equal(own.mode,card.type.replace('market_',''));assert.equal(own.key,card.key);assert.equal(own.amount,card.cost);assert.equal(own.global,card.queue==='true')}
});
for(const card of facts.fasttrack.spaces)test(`publisher fast-track ${card.id}: cost, income, reward and completed purchase`,()=>{
 const s=fresh();s.stage='fast';s.cash=1000000000;s.fastBase=100000;s.pos=(card.id+47)%48;if(card.type==='dream')s.dreamId=E.dreams.findIndex(d=>d.position===card.id);
 E.roll(s,1,()=>0);assert.equal(s.pos,card.id);assert.equal(s.pending.cost,card.cost);
 if(card.type==='dream'){E.buy(s);assert.equal(s.cash,1000000000-card.cost);assert.equal(s.won,true);return}
 assert.equal(s.pending.kind,'fastDeal');assert.equal(s.pending.income,card.cashflow||0);E.buy(s,1,()=>.999);
 if(card.rollmin){assert.equal(s.pending.kind,'investmentRoll');assert.equal(s.pending.die,6);E.resolveInvestment(s)}
 assert.equal(s.cash,1000000000-card.cost+(card.reward||0));assert.equal(s.fastGain,card.cashflow||0);assert.equal(s.fastAssets.length,1);assert.equal(s.fastAssets[0].position,card.id);
});
for(const card of facts.fasttrack.spaces.filter(c=>c.rollmin))test(`publisher fast-track ${card.id}: failed roll loses the investment without claiming the space`,()=>{
 const s=fresh();s.stage='fast';s.cash=1000000;s.fastBase=100000;s.pos=(card.id+47)%48;E.roll(s,1,()=>0);E.buy(s,1,()=>0);assert.equal(s.pending.die,1);assert.equal(s.cash,1000000-card.cost);E.resolveInvestment(s);assert.equal(s.fastGain,0);assert.equal(s.fastAssets.length,0);assert.equal(s.cash,1000000-card.cost);
});
