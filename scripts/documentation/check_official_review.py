"""Validate current native review documents and regression records without claiming source parity."""
from pathlib import Path
import json,hashlib,zipfile,re,unicodedata
from collections import Counter
from docx import Document
from openpyxl import load_workbook
import fitz
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/professional-delivery';OUT=BASE/'12-官网唯一目标复核'
def normal(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
rels=['01-立项与治理/项目章程与治理.docx','02-需求与游戏规则/PRD产品需求规格.docx','02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx','06-测试与质量保证/测试设计与质量报告.docx','08-用户验收/UAT与最终验收方案.docx','12-官网唯一目标复核/官网唯一目标复核与修订报告.docx']
results=[]
for rel in rels:
 p=BASE/rel;d=Document(p);pdf=fitz.open(p.with_suffix('.pdf'));text=normal(''.join(page.get_text() for page in pdf));parts=[x.text for x in d.paragraphs]
 for table in d.tables:
  for row in table.rows:
   for cell in row.cells:parts.extend(x.text for x in cell.paragraphs)
 missing=[s for s in parts if len(normal(s))>=10 and normal(s) not in text]
 assert not missing,(rel,missing)
 for page in pdf:
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     x0,y0,x1,y1=span['bbox'];assert x0>=-1 and y0>=-1 and x1<=page.rect.width+1 and y1<=page.rect.height+1,(rel,span)
 results.append({'file':rel,'pages':len(pdf),'all_body_and_table_text_in_pdf':True,'text_within_page':True})
formula_count=0
for p in BASE.rglob('*.xlsx'):
 w=load_workbook(p,data_only=False);cache=load_workbook(p,data_only=True)
 for ws in w:
  for row in ws:
   for cell in row:
    if cell.data_type=='f':formula_count+=1;v=cache[ws.title][cell.coordinate].value;assert v is not None and not (isinstance(v,str) and v.startswith(('#REF!','#DIV/0!','#VALUE!','#NAME?','#N/A'))),(p,ws.title,cell.coordinate,v)
for p in BASE.rglob('*'):
 if p.suffix in {'.docx','.xlsx','.pptx'}:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
ledger=load_workbook(OUT/'官网目标与复核整改.xlsx',data_only=True);assert {row[0] for row in list(ledger['335项目标目录'].values)[3:]}=={i['id'] for i in json.loads((ROOT/'audit/official-classic-target.json').read_text())['items']}
j=json.loads((ROOT/'audit/validation-latest.json').read_text());assert j['delivery_version']=='0.6.6-preview' and j['unit_tests']['passed']==370 and j['unit_tests']['failed']==0
assert len(j['browser_checks'])==31 and all(r['exit_code']==0 for r in j['browser_checks'])
for row in j['browser_checks']:assert hashlib.sha256((ROOT/row['log']).read_bytes()).hexdigest()==row['log_sha256']
for rel,h in j['tested_files'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
report={'date':'2026-11-04','version':'0.6.6','document_revision':'1.3','passed':True,'rendered_current_docs':results,'cached_formulas_checked':formula_count,'formats':dict(Counter(p.suffix for p in BASE.rglob('*') if p.is_file())),'browser_groups_passed':31,'unit_tests_passed':370,'formal_original_equivalence':False,'limits':'Structural/text integrity and candidate regression only; UAT unsigned; current official site inaccessible. Historical reports retain their original scope.'}
(OUT/'本轮文档复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
