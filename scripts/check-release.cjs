'use strict';
const fs=require('node:fs');
const path=require('node:path');
const coverage=JSON.parse(fs.readFileSync(path.join(__dirname,'../audit/reference-coverage.json'),'utf8'));
const pending=[...coverage.rules,...coverage.runtime_screens,...coverage.blockers].filter(item=>!['unit_verified','reference_verified','resolved'].includes(item.status));
console.log('Reference rules with unit evidence:',coverage.rules.filter(r=>r.status==='unit_verified').length);
console.log('Reference runtime screens verified:',coverage.runtime_screens.filter(r=>r.status==='reference_verified').length+'/'+coverage.runtime_screens.length);
for(const b of coverage.blockers)console.log('BLOCKED:',b.id,'—',b.detail);
if(pending.length||!coverage.release_allowed){console.error('NOT READY FOR ORIGINAL-EQUIVALENCE RELEASE. No download package should be presented as fully equivalent.');process.exitCode=1}else console.log('Release gate passed');
