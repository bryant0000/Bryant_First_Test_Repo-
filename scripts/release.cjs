'use strict';
const {spawnSync}=require('node:child_process');
const path=require('node:path');
const gate=spawnSync(process.execPath,[path.join(__dirname,'check-release.cjs')],{stdio:'inherit'});
if(gate.status!==0)process.exit(gate.status||1);
const build=spawnSync('python3',[path.join(__dirname,'build-offline.py')],{stdio:'inherit'});
process.exit(build.status===0?0:(build.status||1));
