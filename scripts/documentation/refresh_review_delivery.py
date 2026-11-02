"""Refresh native inventory and local reading portal for the reviewed baseline."""
from pathlib import Path
import json,html,urllib.parse
from openpyxl import load_workbook
from openpyxl.styles import Font,Alignment,PatternFill
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/professional-delivery'
AUD=OUT/'10-专家审核与修订'

def refresh():
    result=AUD/'本轮综合复核结果.json'
    if not result.exists():result.write_text(json.dumps({'date':'2026-11-02','status':'复核进行中，非通过结论'},ensure_ascii=False))
    p=OUT/'00-阅读入口与复核/交付物清单.xlsx';w=load_workbook(p)
    s=w['交付物清单'];s.delete_rows(5,s.max_row)
    fs=[f for f in sorted(OUT.rglob('*')) if f.is_file() and '证据快照' not in f.parts]
    for i,f in enumerate(fs,1):
        rel=f.relative_to(OUT);stage=rel.parts[0] if len(rel.parts)>1 else '00-阅读入口与复核'
        s.append([f'DEL-{i:03d}',stage,f.name,f.suffix[1:].upper(),'受控规格／证据；细则见综合报告','对应领域角色；人员待任命','文档修订1.1；游戏验收未签署',str(rel)])
    s.auto_filter.ref=f'A4:H{s.max_row}'
    for row in s.iter_rows(min_row=5):
        for c in row:c.font=Font(name='Microsoft YaHei',size=10);c.alignment=Alignment(wrap_text=True,vertical='center')
        s.row_dimensions[row[0].row].height=64
    w['使用说明']['B2']='文档修订1.1 / 2026-11-02；游戏基线v0.6.4未改'
    w['使用说明']['B4']='综合及专项文档已修订；人的批准、规则裁决与实际发布仍待执行。'
    stage=w['格式与阶段']
    if not any(row[0].value=='10' for row in stage):
        stage.append(['10','领域审核／专项规格／整改与本轮验证','DOCX/PDF/XLSX/JSON/LOG','制作人／策划／设计／研发／QA／运维'])
    if '本轮审核摘要' in w:del w['本轮审核摘要']
    q=w.create_sheet('本轮审核摘要')
    for row in [['指标','结论','边界'],['本轮日期','2026-11-02','历史报告保留原日期'],['独立审查任务',3,'覆盖六类专业职责；AI审核'],['问题登记',22,'7治理+7玩法体验+8技术质量'],['单元测试',353,'本轮重跑通过；0失败'],['HTTP交换',20,'本轮收敛后的契约校验通过；10成功请求体'],['原版全等门禁','BLOCKED','运行画面0/49'],['正式UAT','未签署','禁止代签'],['文档复核结果','10-专家审核与修订/本轮综合复核结果.json','详见结果与范围']]:q.append(row)
    for c,width in [('A',25),('B',65),('C',70)]:q.column_dimensions[c].width=width
    for row in q:
        for c in row:c.font=Font(name='Microsoft YaHei',size=10);c.alignment=Alignment(wrap_text=True,vertical='center')
        q.row_dimensions[row[0].row].height=45
    # Original dashboard is retained but its evidence labels must no longer claim today's unit run was historical.
    dash=w['交付摘要']
    for row in dash:
        if row[0].value=='已有单元测试':row[0].value='本轮单元测试';row[2].value='2026-11-02实际重跑；353通过'
        if row[0].value=='本轮HTTP契约样例':row[2].value='2026-11-02实际重跑20交换并校验收敛契约'
    w.save(p)
    groups={}
    for f in fs:
        rel=f.relative_to(OUT)
        if len(rel.parts)>1:groups.setdefault(rel.parts[0],[]).append(f)
    def link(f):return urllib.parse.quote(str(f.relative_to(OUT)),safe='/')
    nav=''.join(f'<a href="#s{g[:2]}">{html.escape(g)}</a>' for g in sorted(groups))
    sections=[]
    for g,files in sorted(groups.items()):
        cards=''.join(f'<a class="file" href="{link(f)}"><span>{f.suffix[1:].upper()}</span><strong>{html.escape(f.name)}</strong></a>' for f in files)
        sections.append(f'<section id="s{g[:2]}"><h2>{html.escape(g)}</h2><div class="grid">{cards}</div></section>')
    report=AUD/'综合审核与修订报告.pdf'
    body='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cashflow 开发文档审核修订包</title><style>body{margin:0;background:#f2f5f7;color:#18354b;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}header,main,nav{max-width:1180px;margin:auto;padding:24px}header{background:#18354b;color:white;border-radius:0 0 18px 18px}h1{font-size:30px;margin:8px 0}nav{display:flex;gap:10px;flex-wrap:wrap}nav a,.primary{padding:8px 12px;background:#e0f2f1;color:#075c65;border-radius:6px;text-decoration:none}section{background:white;padding:22px;margin:0 0 24px;border-radius:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.file{border:1px solid #d8e1e8;border-radius:8px;padding:14px;text-decoration:none;color:inherit;overflow-wrap:anywhere}.file strong{display:block}.file span{color:#087f8c;font-size:12px}.note{border-left:4px solid #bf8d25;padding:12px 16px;background:#fff9e9}@media(max-width:600px){header,main,nav{padding:16px}h1{font-size:24px}}</style>'''
    body+=f'<header><p>文档修订 1.1 · 2026-11-02 · 游戏实现 v0.6.4</p><h1>Cashflow 开发文档审核修订包</h1><p>完整阶段资料、分领域审核、修订依据与验证记录</p></header><nav>{nav}</nav><main><section><h2>先读综合结论</h2><p>三个独立AI领域任务覆盖项目治理、玩法数值、交互视觉、架构安全、测试和发布运维；登记22项问题，原文与专项规格同步修订。</p><p><a class="primary" href="{link(report)}">阅读综合审核报告 PDF</a> <a class="primary" href="{link(AUD/"综合审核问题与修订追踪.xlsx")}">查看问题整改工作簿</a></p><p class="note">本轮单元测试353通过，20次HTTP交换契约校验通过。原版全等门禁仍BLOCKED；真实file入口、安全容量实测和正式UAT未通过或未签署。此包是开发文档，不是游戏安装包。</p></section>'
    body+=''.join(sections)+'</main></html>'
    (OUT/'开始阅读.html').write_text(body)
    print('Refreshed native inventory and',len(groups),'stage navigation groups.')

if __name__=='__main__':refresh()
