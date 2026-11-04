from pathlib import Path
import json,subprocess,hashlib
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--archive',default='/tmp/cashflow-source-review');args=parser.parse_args()
root=Path(__file__).resolve().parents[2];out=root/'audit/review-official-classic-2026-11-04';out.mkdir(parents=True,exist_ok=True);git=args.archive
previous=root/'audit/official-classic-target.json'
if previous.exists() and any(i.get('status')!='pending' or i.get('reference') for i in json.loads(previous.read_text())['items']):
 raise RuntimeError('Reviewed official targets already exist; do not overwrite them with an archive bootstrap. Establish an explicit new baseline instead.')
coverage=json.loads((root/'audit/reference-coverage.json').read_text());facts=json.loads((root/'audit/official-card-facts.json').read_text());official=json.loads((root/'audit/official-resources.json').read_text());receipts=[];source={}
paths=['careers.json','smalldeal.json','bigdeal.json','market.json','doodads.json','fasttrack.json','vocab_en_us.json','templates/game_screen.json','templates/card_template.json','templates/dream_selector_screen.json','templates/party_setup_screen.json','templates/statement_sheet_template.json','templates/lobby_screen.json','templates/title_screen.json','templates/player_header.json']
for name in paths:
 b=subprocess.check_output(['git','show','2edcdbc15785ac2141f3d1fe544b14e0de2775b4:src/assets/data/'+name],cwd=git);sha=hashlib.sha256(b).hexdigest();x=json.loads(b);source[name]=x
 entry=next((v for v in official if v['file']=='cashflowjs__assets__data__'+name.replace('/','__')),None)
 if entry:assert entry['sha256']==sha,name
 receipts.append({'resource':name,'archive_url':'https://raw.githubusercontent.com/dadish/cashflow/2edcdbc15785ac2141f3d1fe544b14e0de2775b4/src/assets/data/'+name,'bytes':len(b),'sha256':sha,'historical_official_hash_match':bool(entry),'evidence_level':'historically matched official static' if entry else 'unverified mirror only','current_official_runtime':False})
 if name.startswith('templates/'):
  # Functional coordinates and short interface labels; not card prose.
  (out/name.split('/')[-1]).write_text(json.dumps(x,ensure_ascii=False,indent=2))
(out/'source-receipts.json').write_text(json.dumps({'date':'2026-11-04','archive_commit':'2edcdbc15785ac2141f3d1fe544b14e0de2775b4','scope':'independent archive retrieval; historical hash checks do not prove current runtime parity','resources':receipts},ensure_ascii=False,indent=2))
items=[]
def item(ident,kind,expected,source_hint):return {'id':ident,'kind':kind,'status':'pending','expected':expected,'source_hint':source_hint,'reference':None,'target_spec':None,'implementation':{},'candidate':None,'comparison':None}
for r in coverage['rules']:items.append(item('rule:'+r['id'],'rule',r['expected'],{'kind':'historical_rule_anchor','anchor':r.get('source_anchor'),'limitation':'source body/current runtime not captured in this review'}))
for r in coverage['runtime_screens']:items.append(item('screen:'+r['id'],'screen',None,{'kind':'historical_component','observed_before':bool(r.get('official_runtime_observed')),'limitation':'complete original expected interactions and paired captures still required'}))
for c in source['careers.json']['careers']['careerData']:items.append(item('career:'+c['title'],'career',c,{'kind':'historically_matched_static_archive','resource':'careers.json'}))
mechanical={};fields=['type','key','cost','downpay','mortgage','cashflow','units','queue','child','payment']
for deck,resource in [('small','smalldeal.json'),('big','bigdeal.json'),('market','market.json'),('doodads','doodads.json')]:
 cards=next(iter(source[resource].values()))['cards'];mechanical[deck]=[]
 assert len(cards)==len(facts['decks'][deck]['cards'])
 for i,c in enumerate(cards):
  numbers={k:c[k] for k in fields if k in c};assert numbers==facts['decks'][deck]['cards'][i]
  text={k:v for k,v in c.items() if isinstance(v,str) and k not in fields};row={'mechanical':numbers,'text_fields_sha256':hashlib.sha256(json.dumps(text,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'text_fields':list(text),'full_prose_distributed':False}
  mechanical[deck].append(row);items.append(item(f'card:{deck}.{i}','card',row,{'kind':'historically_matched_static_archive','resource':resource,'limitation':'mechanical facts and prose fingerprints are not page/interaction equivalence'}))
space_map={x['id']:x for x in facts['fasttrack']['spaces']};geom=source['templates/game_screen.json']['template']
import re
for i in range(48):
 slots=[k for k in geom if re.match(r'^ft_.*_'+str(i)+r'$',k)]
 expected={'position':i,'mechanical':space_map.get(i),'original_template_slots':slots}
 items.append(item('space:'+str(i),'space',expected,{'kind':'static_archive','resource':'templates/game_screen.json and fasttrack.json','limitation':'special-space behavior requires original rule evidence'}))
assert len(items)==335
manifest={'schema_version':1,'confirmed_at':'2026-11-04','primary_origin':'https://cfclassic.richdad.com/','confirmed_by':'user instruction: target must match official classic website','auxiliary_sources':['physical CASHFLOW 101 cards/rulebook','richdad.aiserve.top','bilibili videos'],'auxiliary_policy':'research only; must not override primary official behavior','reference_snapshot':{'status':'unavailable','url':'https://cfclassic.richdad.com/','version':None,'captured_at':None,'artifact':None,'blocker':'proxy CONNECT 403, including normal and authorized execution channels; allowed domain exists in saved configuration'},'language_review':{'historical_reference':'en-US','candidate':'zh-CN','status':'unresolved','note':'Do not equate translated labels with byte/pixel-identical official pages without reference validation'},'items':items}
(root/'audit/official-classic-target.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(out/'mechanical-targets.json').write_text(json.dumps(mechanical,ensure_ascii=False,indent=2))
coverage['target']='https://cfclassic.richdad.com/ official classic web version only'
for b in coverage['blockers']:
 b['scope']='auxiliary' if b['id'] in ['canonical_physical_rulebook','bilibili_reference_video'] else 'primary'
 if b['id']=='all_content_equivalence':b['detail']='All official web card text/art, rules, visual states and interactive branches must match the selected official snapshot. Numeric fixtures alone are insufficient; current snapshot remains unavailable.'
coverage['primary_target_manifest']='audit/official-classic-target.json'
(root/'audit/reference-coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
print('Independent source receipts:',len(receipts),'historical official hash matches:',sum(r['historical_official_hash_match'] for r in receipts),'required targets:',len(items),'mechanical card records:',sum(len(v) for v in mechanical.values()))
