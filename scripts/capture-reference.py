"""Read public reference resources; record hashes and rule evidence, never credentials.
No login requests, application API calls or remote state mutations are made.
"""
from pathlib import Path
import urllib.request,hashlib,json,re,concurrent.futures,sys
output=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/cashflow-reference-audit');output.mkdir(parents=True,exist_ok=True)
base='https://richdad.aiserve.top/'
paths=['js/cashflow.js?v=1.3.0','js/assets/data/careers_zh_cn.json','js/assets/data/smalldeal_zh_cn.json','js/assets/data/bigdeal_zh_cn.json','js/assets/data/doodads_zh_cn.json','js/assets/data/market_zh_cn.json','js/assets/data/fasttrack_zh_cn.json','js/assets/data/vocab_zh_cn.json','js/assets/data/templates/game_screen_zh_cn.json','js/assets/data/templates/card_template_zh_cn.json']
def download(path):
 with urllib.request.urlopen(base+path,timeout=30) as r:data=r.read()
 name=path.split('?')[0].replace('/','__');(output/name).write_bytes(data)
 if path.split('?')[0].endswith('.json'):json.loads(data)
 return {'url':base+path,'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
records=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(download,paths))
source=(output/records[0]['file']).read_text()
classes=re.findall(r'^var\s+(\w+)\s*=\s*\(function',source,re.M)
ui=[x for x in classes if x.endswith('Card') or x.endswith('Screen') or x in ['StatementElement','HeaderWidget','FooterWidget','BoardElement']]
evidence={}
for name in ['onEnterFastTrackClicked','onDivorceClicked','onLawsuitClicked','onTaxClicked','onSellMarketCard','onDonateClicked','onDoodadLoanNeeded','onShowEndCard','onAttemptDealPurchase','onDreamPassed','_increaseDreamCountPromise']:
 m=re.search(r'function\s+'+re.escape(name)+r'\s*\(',source)
 if m:evidence[name]={'line':source[:m.start()].count('\n')+1,'anchor':name}
manifest={'source':'richdad.aiserve.top public resources','authenticated_gameplay_observed':False,'resources':records,'screen_and_card_states':ui,'rule_anchors':evidence}
(output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Captured',len(records),'public resources;',len(ui),'screen/card components;',len(evidence),'rule anchors')
print(output/'manifest.json')
