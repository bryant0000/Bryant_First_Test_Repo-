"""Current v0.6.6 reading portal and inventory; old review evidence stays historical."""
from pathlib import Path
import json,hashlib,html,urllib.parse
from openpyxl import load_workbook
from openpyxl.styles import Font,Alignment
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/professional-delivery';NEW=OUT/'12-官网唯一目标复核'
for name in ['本轮文档复核.json','当前源码指纹.json']:
 p=NEW/name
 if not p.exists():p.write_text(json.dumps({'status':'待复核，不是通过结论'},ensure_ascii=False))
names=['package.json','index.html','engine.js','app.js','table.js','reference-ui.js','classic-stage.js','classic-stage.css','scene-canvas.js','local-rooms.js','online.js','scripts/rooms.cjs','reference-layout-data.js','scripts/reference-acceptance.cjs','scripts/online-smoke.cjs']
(NEW/'当前源码指纹.json').write_text(json.dumps({'version':'0.6.6','date':'2026-11-04','files':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},'history':'00/10/11目录源码与审核SHA仅描述v0.6.4/0.6.5历史，不是本轮当前文件的校验结果。'},ensure_ascii=False,indent=2))
(OUT/'00-阅读入口与复核/阅读与复现说明.txt').write_text('Cashflow v0.6.6 游戏开发文档，修订1.3，2026-11-04\n\n打开开始阅读.html，优先12-官网唯一目标复核。\n12含当前差距清单、规格、验收步骤、测试报告与源码指纹；02/03 PRD/GDD/UX以及规则/决策/UAT台账已同步修订。00/10是此前v0.6.4审核记录和通用方法，旧SHA只针对当时文件，不能作为当前文件指纹。\n\nv0.6.6修复标题原文与画布位置、过期版本标识，并加强原版证据门禁；其余原版对照与正式UAT仍待办。完整日志在游戏完整包audit/test-logs/v0.6.6。本轮370单元与31浏览器回归通过；file://真双击入口待用户测试。\n\n复现本轮文档：review_official_classic.py，待实际回归后更新validation-latest.json；Office导出PDF/重算修改过的工作簿；finalize_official_review.py更新入口与清单；当前文档与测试证据复核后打包。旧check_delivery/check_expert_review脚本是v0.6.4历史基线，不能不加区分地用于0.6.5。\n')
fs=sorted(p for p in OUT.rglob('*') if p.is_file() and '证据快照' not in p.parts)
p=OUT/'00-阅读入口与复核/交付物清单.xlsx';w=load_workbook(p);s=w['交付物清单'];s.delete_rows(5,s.max_row)
for i,f in enumerate(fs,1):
 rel=f.relative_to(OUT);stage=rel.parts[0] if len(rel.parts)>1 else '00-阅读入口与复核'
 s.append([f'DEL-{i:03d}',stage,f.name,f.suffix[1:].upper(),'当前迭代依据' if stage.startswith('12-') else '通用设计或历史审核；具体版本见文件','对应领域角色','v0.6.6文档1.3；旧审核限定历史范围',str(rel)])
s.auto_filter.ref=f'A4:H{s.max_row}'
for row in s.iter_rows(min_row=5):
 for c in row:c.font=Font(name='Microsoft YaHei',size=10);c.alignment=Alignment(wrap_text=True,vertical='center')
 s.row_dimensions[row[0].row].height=64
w['使用说明']['B2']='当前游戏0.6.6 / 文档修订1.3 / 2026-11-04'
w['使用说明']['B4']='优先12目录；00/10/11历史v0.6.4/0.6.5审查，不代替当前结果；UAT仍未签署'
for row in w['交付摘要']:
 if row[0].value=='本轮单元测试':row[1].value=370;row[2].value='v0.6.6解压候选实际执行'
 if row[0].value=='已有浏览器检查':row[0].value='本轮浏览器检查';row[1].value=31;row[2].value='v0.6.6解压候选实际执行'
 if row[0].value=='本轮HTTP契约样例':row[0].value='前轮HTTP契约样例';row[2].value='20次为v0.6.4文档审核历史；本轮另执行联机/规则测试'
if not any(row[0].value=='12' for row in w['格式与阶段']):w['格式与阶段'].append(['12','当前原版差距／迭代规格／测试报告','DOCX/PDF/XLSX/JSON','产品／研发／QA／用户'])
w.save(p)
groups={}
for f in fs:
 rel=f.relative_to(OUT)
 if len(rel.parts)>1:groups.setdefault(rel.parts[0],[]).append(f)
def link(p):return urllib.parse.quote(str(p.relative_to(OUT)),safe='/')
css='body{max-width:1200px;margin:auto;padding:24px;background:#f3f6f8;color:#18354b;font:16px/1.7 system-ui,"Microsoft YaHei"}header{background:#18354b;color:white;padding:24px;border-radius:12px}section{background:white;padding:20px;margin:24px 0;border-radius:10px}nav{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}a{color:#087f8c}nav a,.primary{background:#dff1f0;padding:8px;text-decoration:none;border-radius:5px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.file{border:1px solid #d6e0e6;padding:12px;border-radius:8px;overflow-wrap:anywhere;text-decoration:none}.file small{display:block;color:#58727a}'
nav=''.join(f'<a href="#s{g[:2]}">{html.escape(g)}</a>' for g in sorted(groups))
sections=[]
for g,files in sorted(groups.items()):
 cards=''.join(f'<a class="file" href="{link(f)}">{html.escape(f.name)}<small>{f.suffix[1:].upper()}</small></a>' for f in files)
 sections.append(f'<section id="s{g[:2]}"><h2>{html.escape(g)}</h2><div class="grid">{cards}</div></section>')
report=NEW/'官网唯一目标复核与修订报告.pdf';tests=NEW/'官网目标与复核整改.xlsx'
page=f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cashflow v0.6.6 迭代文档</title><style>{css}</style><header><p>游戏v0.6.6 · 文档修订1.3 · 2026-11-04</p><h1>原版差距分析与迭代文档</h1><p>官网唯一目标已确认；标题局部与版本标识修复；370项单元与31套浏览器回归结果见当前报告，完整一致性尚未通过。</p></header><nav>{nav}</nav><section><h2>先读当前迭代</h2><p><a class="primary" href="{link(report)}">官网唯一目标复核 PDF</a> <a class="primary" href="{link(tests)}">目标与复核整改 XLSX</a></p><p>12目录为当前版本依据；02/03规格已同步修订。00/10/11目录保留v0.6.4/0.6.5历史审核，旧源码及文档SHA不作为本轮当前指纹。真实file入口仍需用户在本机测试，正式UAT未签署。</p></section>'+''.join(sections)+'</html>'
(OUT/'开始阅读.html').write_text(page)
print('Refreshed v0.6.6 portal, 13 directory groups and native inventory.')
