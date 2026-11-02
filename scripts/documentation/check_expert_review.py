"""Review-specific evidence checks; never grant product release approval."""
from pathlib import Path
import json,hashlib,re,unicodedata,zipfile
from collections import Counter
from docx import Document
from openpyxl import load_workbook
import fitz
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/professional-delivery';AUD=OUT/'10-专家审核与修订'
checks=[]
def add(name,detail):checks.append({'check':name,'passed':True,'details':detail})
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum())

findings=json.loads((AUD/'综合审核问题.json').read_text())['findings']
assert len(findings)==len({x['id'] for x in findings})==22
for f in findings:
    assert f['execution_status'] and f['fix'] and f['evidence']
    for file in f['files']:assert (OUT/file).is_file(),file
add('22项问题的证据、整改、执行边界与引用文件',22)
coverage=json.loads((AUD/'玩法体验覆盖复核.json').read_text())
assert coverage.get('passed') is True
w=load_workbook(AUD/'玩法交互覆盖与验收矩阵.xlsx',data_only=True)
assert w['状态转换契约'].max_row-1==25
assert w['边界验收设计'].max_row-1==9
assert w['原版视觉证据矩阵'].max_row-1==6
gdd=Document(OUT/'02-需求与游戏规则/GDD玩法与数值设计.docx')
text=''.join(c.text for t in gdd.tables for row in t.rows for c in row.cells)
for i in range(1,10):assert f'DEC-{i:02d}' in text or f'DEC{i:02d}' in text
add('玩法覆盖矩阵与GDD决策同步',{'pending':25,'boundary_groups':9,'visual_groups':6,'decisions':9})
oas=json.loads((OUT/'04-技术与接口契约/openapi.json').read_text())
ops=[(p,m,o) for p,item in oas['paths'].items() for m,o in item.items()]
assert len(ops)==10
assert [(p,m) for p,m,o in ops if '503' in o['responses']]==[('/api/rooms','post')]
assert '409' not in oas['paths']['/api/rooms/{id}/chat']['post']['responses']
api=json.loads((OUT/'00-阅读入口与复核/接口与Schema复核结果.json').read_text())
assert api['date']=='2026-11-02' and api['validated_count']==20 and api['validated_success_request_bodies']==10
add('端点响应收敛与本轮真实HTTP契约证据',{'operations':10,'exchanges':20,'successful_request_bodies':10})
log=(AUD/'证据/本轮单元测试-2026-11-02.log').read_text()
assert re.search(r'(?:#|ℹ) pass 353\b',log) and re.search(r'(?:#|ℹ) fail 0\b',log)
gate=(AUD/'证据/本轮原版全等门禁-2026-11-02.log').read_text()
assert 'BLOCKED' in gate and '0/49' in gate
add('真实单测与原版门禁边界',{'unit_pass':353,'unit_fail':0,'original_equivalence':'BLOCKED 0/49'})
# Content coverage catches entire rows silently omitted by PDF pagination.
pages=0;body_checks=0
for f in sorted(OUT.rglob('*.docx')):
    d=Document(f);pdf=fitz.open(f.with_suffix('.pdf'));pages+=len(pdf)
    actual=norm(''.join(p.get_text() for p in pdf))
    paras=[p.text for p in d.paragraphs]
    for t in d.tables:paras.extend(p.text for row in t.rows for cell in row.cells for p in cell.paragraphs)
    for para in paras:
        n=norm(para)
        if len(n)<8:continue
        for part in [n[:16],n[-16:]]:assert part in actual,(f.name,para)
        body_checks+=1
add('全部Word正文与表格在PDF中的前后文字覆盖',{'docx':18,'pages':pages,'paragraphs_or_cells':body_checks,'method':'Unicode规范化后首尾16字；另有逐页视觉复核，不是像素完美证明'})
for name in ['治理版式复核.json','玩法体验版式复核.json','技术质量版式复核.json','综合版式复核.json']:
    obj=json.loads((AUD/name).read_text());assert obj.get('final_pass') is True,name
add('分领域及综合报告全页视觉复核记录','4份最终记录通过；具体已查看页码及PDF指纹见对应JSON')
fingers=json.loads((OUT/'00-阅读入口与复核/源码复核指纹.json').read_text())
for name,digest in fingers['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
add('游戏实现未修改',{'fingerprints':len(fingers['files'])})
master=load_workbook(OUT/'00-阅读入口与复核/交付物清单.xlsx',data_only=True)
listed={master['交付物清单'].cell(i,8).value for i in range(5,master['交付物清单'].max_row+1)}
actual={str(f.relative_to(OUT)) for f in OUT.rglob('*') if f.is_file() and '证据快照' not in f.parts}
assert listed==actual,{'missing':sorted(actual-listed),'stale':sorted(listed-actual)}
counts=Counter(f.suffix for f in OUT.rglob('*') if f.is_file() and '证据快照' not in f.parts)
dash=master['交付摘要']
for i,ext in [(5,'.docx'),(6,'.pdf'),(7,'.xlsx'),(8,'.pptx')]:assert dash.cell(i,2).value==counts[ext],(i,dash.cell(i,2).value,counts[ext])
add('交付物清单、实际文件与已重算数量一致',dict(counts))
result={'date':'2026-11-02','passed':True,'scope':'开发文档领域审核与修订交付复核；不是游戏上线批准','checks':checks,'counts':dict(counts),'issues':22,'docx_pages':pages,'product_release_approved':False,'remaining':['原版完整资料与规则裁决','真实file入口和完整浏览器设备矩阵','在线安全加固、容量与恢复演练','实际角色任命与正式UAT签署']}
(AUD/'本轮综合复核结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
