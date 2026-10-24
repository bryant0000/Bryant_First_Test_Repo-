"""Extract mechanical facts for independent regression fixtures; omit card prose/art."""
import hashlib,json,sys
from pathlib import Path
source=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/cashflow-official-evidence')
root=Path(__file__).resolve().parent.parent
fields=['type','key','cost','downpay','mortgage','cashflow','units','queue','child','payment']
result={'origin':'https://cfclassic.richdad.com/','scope':'Numeric and functional fields only; not a full-text, artwork or runtime equivalence proof.','decks':{}}
for local,name in [('small','smalldeal'),('big','bigdeal'),('market','market'),('doodads','doodads')]:
 file=source/f'cashflowjs__assets__data__{name}.json'
 raw=json.loads(file.read_text());cards=next(iter(raw.values()))['cards']
 result['decks'][local]={'source_url':f'https://cfclassic.richdad.com/cashflowjs/assets/data/{name}.json','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'cards':[{k:c[k] for k in fields if k in c} for c in cards]}
file=source/'cashflowjs__assets__data__fasttrack.json'
raw=json.loads(file.read_text())['fasttrack']['spaces']
result['fasttrack']={'source_url':'https://cfclassic.richdad.com/cashflowjs/assets/data/fasttrack.json','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'spaces':[{k:c[k] for k in ['id','type','cost','cashflow','reward','rollmin','stock'] if k in c} for c in raw]}
(root/'audit/official-card-facts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Extracted mechanical facts for',sum(len(d['cards']) for d in result['decks'].values()),'cards; no card prose.')
