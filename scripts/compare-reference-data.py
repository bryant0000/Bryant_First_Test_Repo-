"""Compare mechanical fields against downloaded public JSON without card prose."""
import json,sys,collections,pathlib
live=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/cashflow-reference-audit')
mirror=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else '/tmp/cashflow-research-dadish/src/assets/data')
def load_live(name):return json.loads((live/('js__assets__data__'+name+'_zh_cn.json')).read_text())
def cards(x):return next(iter(x.values()))['cards']
def signature(x,fields):
 result=[]
 for k in fields:
  v=x.get(k)
  if k=='units' and v is not None:v=int(v)
  result.append((k,v))
 return tuple(result)
report=[]
for name in ['smalldeal','bigdeal','market','doodads']:
 a=cards(load_live(name));b=cards(json.loads((mirror/(name+'.json')).read_text()))
 keys=['type','key','cost','downpay','mortgage','cashflow','units','child','payment','queue']
 equal=collections.Counter(signature(x,keys) for x in a)==collections.Counter(signature(x,keys) for x in b)
 report.append({'dataset':name,'live_count':len(a),'mirror_count':len(b),'mechanical_fields_match':equal})
a=load_live('careers')['careers']['careerData'];b=json.loads((mirror/'careers.json').read_text())['careers']['careerData'];keys=sorted(k for x in a for k,v in x.items() if isinstance(v,(int,float)));keys=sorted(set(keys));equal=collections.Counter(signature(x,keys) for x in a)==collections.Counter(signature(x,keys) for x in b)
report.append({'dataset':'careers','live_count':len(a),'mirror_count':len(b),'mechanical_fields_match':equal})
a=load_live('fasttrack')['fasttrack']['spaces'];b=json.loads((mirror/'fasttrack.json').read_text())['fasttrack']['spaces'];keys=['id','type','cost','cashflow','reward','rollmin','stock'];equal=collections.Counter(signature(x,keys) for x in a)==collections.Counter(signature(x,keys) for x in b)
report.append({'dataset':'fasttrack_content','live_count':len(a),'mirror_count':len(b),'mechanical_fields_match':equal})
print(json.dumps(report,ensure_ascii=False,indent=2))
pathlib.Path('audit/data-comparison.json').write_text(json.dumps({'checks':report,'does_not_verify':'card prose, display text, full page layouts or live gameplay'},ensure_ascii=False,indent=2)+'\n')
if not all(r['mechanical_fields_match'] for r in report):sys.exit(1)
