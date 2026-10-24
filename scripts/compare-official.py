"""Compare retrieved public publisher resources with pinned research sources.
Does not execute publisher code, log in, or copy card prose into the application.
"""
from pathlib import Path
import hashlib,json,re,sys
root=Path(__file__).resolve().parent.parent
official=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/cashflow-official-evidence')
mirror=Path(sys.argv[2] if len(sys.argv)>2 else '/tmp/cashflow-research-dadish/src/assets/data')
reference=Path(sys.argv[3] if len(sys.argv)>3 else '/tmp/cashflow-live-cashflow.js')
source=(official/'cashflowjs__cashflow.js').read_text()
other=reference.read_text()
rows=[]
for p in sorted(official.glob('cashflowjs__assets__data__*.json')):
 rel=p.name.replace('cashflowjs__assets__data__','').replace('__','/')
 rows.append({'resource':rel,'same_json_as_pinned_mirror':json.loads(p.read_text())==json.loads((mirror/rel).read_text()),'official_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def body(text,name):
 m=re.search(r'function\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{',text)
 if not m:return None
 start=m.end()-1;i=start;depth=0;state=None
 while i<len(text):
  c=text[i];n=text[i+1:i+2]
  if state in ['"',"'",'`']:
   if c=='\\':i+=2;continue
   if c==state:state=None
  elif state=='line':
   if c=='\n':state=None
  elif state=='block':
   if c=='*' and n=='/':state=None;i+=2;continue
  elif c in ['"',"'",'`']:state=c
  elif c=='/' and n=='/':state='line';i+=2;continue
  elif c=='/' and n=='*':state='block';i+=2;continue
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return text[start:i+1]
  i+=1
 raise ValueError('Unclosed function: '+name)
names=['onEnterFastTrackClicked','onShowEndCard','onAttemptDealPurchase','onAttemptInvestmentPurchase','onAttemptInvestmentChancePurchase','purchaseInvestment','onSellMarketCard','onMarketMustClicked','attemptPayCash','offerLoan','onLoanBorrowClicked','onLoanCancelClicked','onDownsizeClicked','onDoodadLoanNeeded','onDonateClicked','onDivorceClicked','onTaxClicked','onLawsuitClicked','onAddChild','onSpecialStockCardClicked','stillBankruptCheck','onBankruptSellProperty','onBankruptHalveClicked','onBankruptCompleteClicked','onBankruptLoseClicked','onBankruptPayOffClicked','handleCardDrawn','addCardtoCardQueue','_increaseDreamCountPromise']
callbacks=[]
for name in names:
 a,b=body(source,name),body(other,name)
 callbacks.append({'name':name,'present':a is not None and b is not None,'exact_function_body_match':a is not None and a==b,'official_body_sha256':hashlib.sha256(a.encode()).hexdigest() if a else None})
def classes(text):
 ms=list(re.finditer(r'^var\s+(\w+)\s*=\s*\(function',text,re.M))
 return {m.group(1):text[m.start():ms[i+1].start() if i+1<len(ms) else len(text)] for i,m in enumerate(ms)}
a,b=classes(source),classes(other);changed=[k for k in sorted(a.keys()&b.keys()) if re.sub(r'\s+','',a[k])!=re.sub(r'\s+','',b[k])]
report={'publisher_origin':'https://cfclassic.richdad.com/','resources':rows,'callbacks':callbacks,'class_text_comparison':{'common':len(a.keys()&b.keys()),'changed_ignoring_whitespace':changed,'not_a_semantic_equivalence_proof':True},'authenticated_runtime_observed':False,'complete_physical_or_visual_equivalence_proven':False}
(root/'audit/official-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(root/'audit/official-resources.json').write_text((official/'manifest.json').read_text())
print('Publisher JSON resources identical to pinned mirror:',sum(x['same_json_as_pinned_mirror'] for x in rows),'/',len(rows))
print('Publisher rule callbacks with exact body match:',sum(x['exact_function_body_match'] for x in callbacks),'/',len(callbacks))
for x in callbacks:
 if not x['exact_function_body_match']:print('REVIEW CALLBACK:',x['name'])
if not all(x['same_json_as_pinned_mirror'] for x in rows):sys.exit(1)
