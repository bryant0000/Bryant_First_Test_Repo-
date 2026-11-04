'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const ORIGIN='https://cfclassic.richdad.com';
function digest(bytes){return crypto.createHash('sha256').update(bytes).digest('hex')}
function inspectArtifact(root,record){
 if(!record||typeof record.file!=='string'||path.isAbsolute(record.file))throw Error('artifact must have a repository-relative path');
 const base=fs.realpathSync(root),file=fs.realpathSync(path.resolve(base,record.file));
 if(!file.startsWith(base+path.sep))throw Error('artifact escapes repository');
 if(!/^[a-f0-9]{64}$/.test(record.sha256||''))throw Error('missing artifact SHA-256');
 const bytes=fs.readFileSync(file);if(digest(bytes)!==record.sha256)throw Error('artifact hash mismatch: '+record.file);
 return bytes;
}
function official(url){try{return new URL(url).origin===ORIGIN}catch{return false}}
function assess({root,target,coverage,requiredIds}){
 const blockers=[],auxiliary=[];const add=(id,reason)=>blockers.push({id,reason});
 if(target.primary_origin!==ORIGIN+'/')add('primary_target','Primary target must be the official classic website');
 const snapshot=target.reference_snapshot;
 try{
  if(snapshot?.status!=='captured'||!official(snapshot.url)||!snapshot.version||!Number.isFinite(Date.parse(snapshot.captured_at)))throw Error('versioned official snapshot has not been captured');
  inspectArtifact(root,snapshot.artifact);
 }catch(e){add('official_snapshot',e.message)}
 const items=target.items||[],byId=new Map();
 for(const item of items){if(byId.has(item.id))add(item.id,'duplicate target ID');byId.set(item.id,item)}
 for(const id of requiredIds){
  const item=byId.get(id);
  if(!item){add(id,'required target omitted');continue}
  if(item.status!=='reference_verified'){add(id,'original target/design/comparison not signed off');continue}
  try{
   if(item.expected===null||item.expected===undefined)throw Error('original expected behavior is unknown');
   const reference=item.reference;
   if(!official(reference?.url)||!['official_static','official_runtime'].includes(reference.kind))throw Error('reference must identify primary official evidence');
   if(reference.snapshot_sha256!==snapshot?.artifact?.sha256)throw Error('reference belongs to a different or unspecified official snapshot');
   const original=inspectArtifact(root,reference.artifact),candidate=inspectArtifact(root,item.candidate);
   inspectArtifact(root,item.target_spec);
   if(!item.target_spec.anchor)throw Error('missing design-specification anchor');
   if(!item.implementation||!Object.keys(item.implementation).length)throw Error('implementation fingerprints missing');
   for(const [file,sha256] of Object.entries(item.implementation))inspectArtifact(root,{file,sha256});
   const test=JSON.parse(inspectArtifact(root,item.comparison));
   if(test.case_id!==id||test.passed!==true||test.original_sha256!==digest(original)||test.candidate_sha256!==digest(candidate)||test.reference_snapshot_sha256!==snapshot?.artifact?.sha256)throw Error('comparison is not linked to this original/candidate pair and snapshot');
   if(item.kind==='screen'){
    if(reference.kind!=='official_runtime')throw Error('screen acceptance requires original runtime evidence');
    const keys=['width','height','deviceScaleFactor','zoom','language'];
    for(const key of keys){if(reference.viewport?.[key]===undefined||reference.viewport[key]!==item.candidate.viewport?.[key])throw Error('screen viewport/language mismatch: '+key)}
    for(const key of keys.filter(k=>k!=='language'))if(typeof reference.viewport[key]!=='number'||!Number.isFinite(reference.viewport[key])||reference.viewport[key]<=0)throw Error('invalid screen metadata: '+key);
    if(typeof reference.viewport.language!=='string'||!reference.viewport.language.trim())throw Error('invalid screen language');
    const png=Buffer.from('89504e470d0a1a0a','hex');
    if(original.length<24||candidate.length<24||!original.subarray(0,8).equals(png)||!candidate.subarray(0,8).equals(png))throw Error('screen artifacts must be PNG captures');
    const width=Math.round(reference.viewport.width*reference.viewport.deviceScaleFactor),height=Math.round(reference.viewport.height*reference.viewport.deviceScaleFactor);
    for(const capture of [original,candidate])if(capture.readUInt32BE(16)!==width||capture.readUInt32BE(20)!==height)throw Error('PNG dimensions do not match the declared viewport/DPR');
   }
  }catch(e){add(id,e.message)}
 }
 for(const item of coverage.blockers||[]){
  if(item.scope==='auxiliary'){
   if(!['canonical_physical_rulebook','bilibili_reference_video'].includes(item.id))add(item.id,'primary web acceptance cannot be demoted to an auxiliary source');
   else auxiliary.push({id:item.id,reason:item.detail});
   continue;
  }
  if(item.status!=='resolved')add(item.id,item.detail);
 }
 if(!coverage.release_allowed)add('release_authorization','Formal acceptance/release authorization is still false');
 return {primary_origin:target.primary_origin,required:requiredIds.length,reference_verified:requiredIds.filter(id=>byId.get(id)?.status==='reference_verified'&&!blockers.some(b=>b.id===id)).length,passed:blockers.length===0,blockers,auxiliary};
}
function requiredTargets(coverage,facts,careers){
 return [...coverage.rules.map(r=>'rule:'+r.id),...coverage.runtime_screens.map(r=>'screen:'+r.id),...careers.map(c=>'career:'+c.title),...Object.entries(facts.decks).flatMap(([name,deck])=>deck.cards.map((_,i)=>`card:${name}.${i}`)),...Array.from({length:48},(_,i)=>'space:'+i)];
}
module.exports={ORIGIN,digest,inspectArtifact,assess,requiredTargets};
