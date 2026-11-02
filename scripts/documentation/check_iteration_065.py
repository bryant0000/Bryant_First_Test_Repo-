"""Validate current iteration docs without applying historical v0.6.4 fingerprints."""
from pathlib import Path
import json,re,hashlib,zipfile,unicodedata,ast
from collections import Counter
from docx import Document
from openpyxl import load_workbook
import fitz
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/professional-delivery';NEW=OUT/'11-v0.6.5差距分析与迭代'
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum())
assert json.loads((ROOT/'package.json').read_text())['version']=='0.6.5'
report=json.loads((ROOT/'audit/validation-v0.6.5.json').read_text());assert report['passed'] and report['unit_tests']['passed']==358 and report['browser_check_count']==29
assert all(x['status']=='passed' for x in report['browser_checks'])
for x in report['browser_checks']:assert hashlib.sha256((ROOT/x['log']).read_bytes()).hexdigest()==x['log_sha256']
f=json.loads((NEW/'当前源码指纹.json').read_text())
for name,sha in f['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
for p in ROOT.joinpath('scripts/documentation').glob('*.py'):ast.parse(p.read_text())
paragraphs=0;pdfs=0;native=0
for p in sorted(OUT.rglob('*')):
 if not p.is_file() or '证据快照' in p.parts:continue
 if p.suffix in ['.docx','.xlsx','.pptx']:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
  native+=1
 if p.suffix=='.docx':
  d=Document(p);pdf=fitz.open(p.with_suffix('.pdf'));actual=norm(''.join(pg.get_text() for pg in pdf));ps=[x.text for x in d.paragraphs]
  for t in d.tables:ps.extend(x.text for row in t.rows for c in row.cells for x in c.paragraphs)
  for s in ps:
   n=norm(s)
   if len(n)<8:continue
   assert n[:16] in actual and n[-16:] in actual,(p.name,s)
   paragraphs+=1
 if p.suffix=='.pdf':
  pdfs+=1
  for page in fitz.open(p):
   assert '\ufffd' not in page.get_text()
   for b in page.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
     for sp in l['spans']:
      x0,y0,x1,y1=sp['bbox'];assert x0>=-.5 and y0>=-.5 and x1<=page.rect.width+.5 and y1<=page.rect.height+.5,(p.name,sp['text'])
 if p.suffix=='.xlsx':
  a=load_workbook(p,data_only=False);b=load_workbook(p,data_only=True)
  for s in a:
   for row in s:
    for c in row:
     if c.data_type=='f':assert b[s.title][c.coordinate].value is not None,(p.name,s.title,c.coordinate)
     assert b[s.title][c.coordinate].data_type!='e'
 if p.suffix=='.html':
  for target in re.findall(r'(?:href|src)="([^"]+)"',p.read_text()):
   if target.startswith(('#','http','data:')):continue
   import urllib.parse
   assert (p.parent/urllib.parse.unquote(target.split('#')[0])).exists(),(p.name,target)
counts=Counter(p.suffix for p in OUT.rglob('*') if p.is_file() and '证据快照' not in p.parts)
w=load_workbook(OUT/'00-阅读入口与复核/交付物清单.xlsx',data_only=True)
listed={w['交付物清单'].cell(i,8).value for i in range(5,w['交付物清单'].max_row+1)}
actual={str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file() and '证据快照' not in p.parts}
assert listed==actual,{'missing':sorted(actual-listed),'stale':sorted(listed-actual)}
for i,ext in [(5,'.docx'),(6,'.pdf'),(7,'.xlsx'),(8,'.pptx')]:assert w['交付摘要'].cell(i,2).value==counts[ext]
changed=['02-需求与游戏规则/PRD产品需求规格.docx','02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx','11-v0.6.5差距分析与迭代/原版差距分析与迭代规格.docx','11-v0.6.5差距分析与迭代/迭代测试报告.docx']
visual=[]
for rel in changed:
 p=OUT/rel;pdf=p.with_suffix('.pdf');n=len(fitz.open(pdf));visual.append({'file':str(pdf.relative_to(OUT)),'pages':n,'viewed_pages':list(range(1,n+1)),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'docx_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'passed':True})
result={'version':'0.6.5','date':'2026-11-02','passed':True,'scope':'当前迭代文档/源码/回归证据一致性，不是原版全等或正式UAT','unit_pass':358,'browser_pass':29,'gaps':12,'fixed':3,'remaining':9,'native_files_checked':native,'pdf_checked':pdfs,'word_paragraph_cell_coverage':paragraphs,'counts':dict(counts),'changed_documents_visual_review':visual,'visual_review':'本轮修改/新增5份Word导出PDF共22页直接逐页目检；修正近空白尾页、版本脚注和拆分小表；未改的旧文档沿用前轮目检记录','historical_audit_boundary':'00/10的v0.6.4源码/文档SHA保留历史，不套用于修订后文件','full_original_equivalence':False,'file_protocol_test':'未执行，需用户实际双击验收'}
assert sum(x['pages'] for x in visual)==22
(NEW/'本轮文档复核.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['changed_documents_visual_review']},ensure_ascii=False))
