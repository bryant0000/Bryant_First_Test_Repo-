"""Define original-source targets separately from current-code facts and uncertain observations."""
from pathlib import Path
import json,hashlib,shutil,html,urllib.parse
from docx import Document
from docx.shared import Pt
from integrate_expert_review import style_doc,table,sheet
from openpyxl import Workbook
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/original-target-baseline';OUT.mkdir(parents=True,exist_ok=True)
S=ROOT/'audit/original-target-2026-11-04';source=json.loads((S/'careers.json').read_text())['careers']['careerData'];current=json.loads(Path('/tmp/cf-target-current.json').read_text());coverage=json.loads((ROOT/'audit/reference-coverage.json').read_text())
prov=json.loads((S/'provenance.json').read_text());official=json.loads((ROOT/'audit/official-resources.json').read_text())
for p in prov:
 rec=next(x for x in official if x['file']=='cashflowjs__assets__data__'+p['path'].replace('/','__'))
 assert p['sha256']==rec['sha256'];p['matches_historical_official_resource_hash']=True
provenance={'date':'2026-11-04','game_version':'0.6.5 unchanged','scope':'本轮公开镜像读取及历史官网SHA校验；不等于原站当前页面或流程核验','resources':prov,'direct_access':json.loads((S/'direct-access.json').read_text())}
(OUT/'原版来源与证据等级.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
raw=OUT/'原版功能资料';raw.mkdir(exist_ok=True)
for n in ['careers.json','templates__game_screen.json','templates__card_template.json']:shutil.copyfile(S/n,raw/n)
fields={'salary':'salary','tax':'taxes','homePayment':'mortgagePayment','schoolPayment':'schoolLoanPayment','carPayment':'carLoanPayment','creditPayment':'creditCardPayment','retailPayment':'retailPayment','other':'otherExpenses','savings':'savings','childCost':'childPerExpense','homeDebt':'mortgageLiability','schoolDebt':'schoolLoanLiability','carDebt':'carLoanLiability','creditDebt':'creditCardLiability','retailDebt':'retailDebtLiability'}
w=Workbook();w.remove(w.active)
sheet(w,'目标与证据门禁',['ID','目标／要求','原版依据','当前差异／状态','实施条件'],[
 ['BASE-01','先固定原版版本，再设计及实现','官网经典版、中文站、实体101分别建基线','唯一主对照官网经典版已确认；职业交互待原站核验','不跨版本拼接规则，不以现代码倒推原版'],
 ['CAREER-01','核实分配还是自选、何时确定及能否改选','历史pickCareer锚点记为12职业随机，可重复；本轮原始JS未取得','当前入房随机分配；当前没有原版自选职业的新证据','取得原站实际流程/源码快照或实体规则页再改交互'],
 ['CAREER-02','职业字段逐项按原版资料建立','本轮career源资料15数值字段×12职业','按英文title映射；不能按数组下标当相同职业ID','源数据对齐不等于职业选择页面一致'],
 ['UI-01','页面几何、字体、素材和交互分别验收','game_screen v84/card_template v41功能模板','原坐标可追溯，运行缩放与中文字体另核实','原站/候选同状态、同视口截图成对测量'],
 ['RULE-01','每条规则保留原始证据与预期状态','历史44条规则锚点，非本轮全部复访','单元通过不作为原站全部行为通过','转写预期→评审→设计→实现→双侧复验'],
 ['PAGE-01','49个组件逐项建立行为和视觉目标','历史正常操作观察与组件ID','完整签收仍0/49；没有原截图者不得自动关闭','入口/前置/动作/输出/取消/恢复/截图均齐'],
 ['RELEASE-01','最终原版等同需全链证据','12职业、卡牌/规则、页面/操作、真实入口','v0.6.5仍是测试版，本轮不改运行时代码','通过完整目标矩阵与用户实际验收后再宣称一致']])
rows=[]
for i,c in enumerate(source):
 own=next(j for j in current['jobs'] if j['english']==c['title'])
 for a,b in fields.items():assert own[a]==c[b]
 rows.append([i,c['title'],own['id'],own['name']]+[c[v] for v in fields.values()]+['15数值字段匹配；中文及原版职业交互待核验'])
sheet(w,'原版职业数据与映射',['原版数据索引','原版title','本地ID','本地中文']+list(fields.values())+['结论'],rows)
# Both target values and current projected constants are kept, with their limitation.
geo=[]
for name,kind in [('templates__card_template.json','card'),('templates__game_screen.json','game')]:
 t=json.loads((S/name).read_text())['template']
 for ident,v in t.items():
  if not isinstance(v,dict):continue
  own=current['layout']['card'].get(ident) if kind=='card' else current['layout']['dice'] if ident=='die' else None
  for key in ['x','y','width','height','font','size','bold','align']:
   if key not in v:continue
   val=v[key]
   if key in ['x','y','width','height','size']:val=float(val)
   found=own is not None and key in own
   status=('常量一致，未证明实际渲染一致' if own[key]==val else '常量差异，需设计复核') if found else '尚未建立实际渲染映射'
   geo.append([name,ident,key,val,own.get(key) if found else '未映射',status,'原版功能模板；不是原站运行截图'])
sheet(w,'原版模板目标与当前映射',['原版资料','组件','字段','原版目标值','当前投影常量','比较结论','证据限制'],geo)
sheet(w,'49页面目标核验',['原版组件','历史正常操作观察','原版完整视觉/交互目标','当前状态','待补验收依据'],[[x['id'],'有历史摘要' if x.get('official_runtime_observed') else '无完整历史观察','逐页目标尚未完全确立，不用候选DOM填成原版目标',x['status'],'原站入口、前置、操作/取消/恢复、结果及同视口截图/录屏；规则另关联'] for x in coverage['runtime_screens']])
sheet(w,'规则目标与证据级别',['规则ID','历史源锚点','历史登记的预期','证据等级与限制','本轮处理'],[[x['id'],x.get('source_anchor',''),json.dumps(x['expected'],ensure_ascii=False) if not isinstance(x['expected'],str) else x['expected'],'历史源码/运行摘要；本轮未取得所有原始函数与操作证据','作为核验线索；不是根据当前单测反证原版已全等'] for x in coverage['rules']])
steps=[['01 原版调查','选定版次和站点，保存来源、日期、哈希、截图','产品/规则/UX','目标不明则登记未知，不进入“已对齐”'],['02 目标规格','原版规则、职业、页面与状态写成独立预期','策划/UX/UI','目标字段不从候选代码生成；假设必须标识'],['03 差异设计','原版预期→当前行为→变更规格→验收用例','架构/前后端/QA','职业自选若无证据，不擅自新增到原版模式'],['04 实施','按已确认差异修改代码及迁移策略','前端/规则/后端','不能凭猜测更改未确认分支'],['05 双侧验证','候选测试+原版同状态对照+真实本地入口','QA/UX/规则','通过单侧单测不关闭原版交互或视觉问题'],['06 用户验收','冻结包SHA，逐项签收并保留遗留','产品/实际用户','仍有未知就称测试版，不称完整原版复刻']]
sheet(w,'设计到实现的交接',['阶段','应做的工作','责任','门禁'],steps)
if (S/'career-verification.json').exists():
 test=json.loads((S/'career-verification.json').read_text());shutil.copyfile(S/'career-verification.json',OUT/'当前职业路径验证.json')
 sheet(w,'本轮候选职业实测',['本地ID','职业','初始现金','切换梦想保持职业','报表有职业','刷新保持职业','范围'],[[x['id'],x['career'],x['starting_cash'],x['dream_change_preserves_career'],x['statement_displays_career'],x['reload_preserves_career'],'仅候选本机模拟；不证明原版是否允许职业自选'] for x in test['careers']])
w.save(OUT/'原版目标与实现追溯.xlsx')
d=Document();style_doc(d)
d.styles['Normal'].paragraph_format.space_after=Pt(4)
for name,before,after in [('Heading 1',12,6),('Heading 2',8,4)]:d.styles[name].paragraph_format.space_before=Pt(before);d.styles[name].paragraph_format.space_after=Pt(after)
for sec in d.sections:
 for p in sec.footer.paragraphs:
  for run in p.runs:run.text=run.text.replace('文档修订 1.1','目标核验稿').replace('2026-11-02','2026-11-04')
d.add_heading('Cashflow 原版目标识别与职业流程核验',0)
d.add_paragraph('这份资料将原版目标与当前实现分开记录。最终目标仍是规则、职业、玩法、页面和操作与选定原版一致；设计文档不是对当前代码的说明书。本轮先核实“不能选择职业”是否属于原版差异，没有依据时不向原版模式增加自选职业。')
table(d,['控制项','当前结论'],[['日期/版本','2026-11-04；候选游戏仍v0.6.5，本轮未改运行时代码'],['对照对象','唯一主目标已确认为官网经典版；中文站和实体仅辅助。官网当前版本快照待采集'],['职业交互','历史证据登记pickCareer随机分配12职业且可重复；当前也随机分配，首次回合可选梦想。尚无本轮原版可自选职业的证据'],['访问限制','官网入口与JS、中文站本轮被代理403拒绝；不宣称已重新登录或实玩'],['新取得资料','固定版本公开镜像的careers、game_screen、card_template三资料，SHA均匹配仓库历史官网资源记录']],[1.5,5.2])
d.add_heading('职业问题调查结论',1)
d.add_paragraph('当前不能主动选职业并不表示没有实现职业。已将原版职业功能资料独立保存，按英文title对应本地ID逐项核对15个数值字段。原版资料的职业数组顺序与本地ID顺序不同，因此不能用相同数组下标判断相同角色。未经迁移设计也不应重排旧存档中的职业ID。')
d.add_paragraph('候选验证采用自己的本地浏览器和确定性测试随机数，依次走12个职业的标题、建房、开始、切换梦想、财务表及刷新恢复路径。此项证明候选的职业数据与保持逻辑，不能反过来证明原版是否提供职业选择器。原站当前职业分配触发时机、是否有不同模式可改选，仍需对应页面或规则依据。')
d.add_heading('原版依据与当前实现分别记录',1)
table(d,['资料','本轮取得内容','不能推出的结论'],[['职业资料','12职业及180个数值字段可独立对照；历史官网同哈希','不证明职业选择交互或中文文案已一致'],['页面功能模板','原始坐标、宽高、字体与组件名；逐字段保存在Excel','不证明实际绘制、遮挡、动画及多骰位置全等'],['历史规则记录','44条源锚点及49个页面组件核验线索','不是本轮44条规则/49页已重新观察'],['候选实测','12职业的本机分配、梦想不改职业、财务显示和刷新保持','不是原站实测，也不是原版全等验收']],[1.3,2.7,2.7])
d.add_heading('后续设计与开发的约束',1)
for title,work,owner,gate in steps:
 d.add_heading(title,2);d.add_paragraph(work+'。责任：'+owner+'。'+gate+'。')
d.add_heading('本轮交付与仍待解决的事项',1)
d.add_paragraph('Excel包含原版职业字段、原版模板目标、49页证据缺口、44条规则线索和设计到实施门禁。原始功能资料及来源哈希随包保存。原版截图或规则未齐的格子保持未知；不会用“当前实现如此”填成“原版要求如此”。')
d.add_paragraph('尚未解决最终原版等同目标。需在已确定的官网经典版核实职业分配和可否自选的实际页面，补充该流程证据后，再决定修正交互还是继续保留随机职业规则。其余视觉与特殊规则继续按逐项目标表核验，不据本轮数据匹配或自动化通过宣布全等。')
d.save(OUT/'原版目标识别与职业流程核验.docx')
(OUT/'阅读说明.txt').write_text('先打开开始阅读.html。职业来源与页面功能模板是本轮重新取得的固定版本公开镜像，SHA匹配历史官网资源记录；不等于本轮原站实玩。\n游戏仍v0.6.5，未因职业投诉擅改随机/自选规则。先固定原版目标，再调整设计、代码和双侧验收。\nExcel为可编辑目标台账，DOCX/PDF为核验报告，JSON保存功能事实与来源。未知目标保持未知。\n')
links=''.join(f'<li><a href="{urllib.parse.quote(str(p.relative_to(OUT)),safe="/")}">{html.escape(str(p.relative_to(OUT)))}</a></li>' for p in sorted(OUT.rglob('*')) if p.is_file())
(OUT/'开始阅读.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>原版目标基线</title><style>body{font:16px/1.8 system-ui;max-width:960px;margin:40px auto;padding:20px;color:#18354b}a{color:#087f8c}li{margin:10px 0}</style><h1>原版目标识别与职业流程核验</h1><p>2026-11-04。先读报告和Excel；未确认的目标不当作原版事实。本轮不修改v0.6.5运行时。</p><ul>'+links+'</ul></html>')
print('Created source-first target baseline:',len(source),'careers,',len(geo),'template fields,49 pages,44 historical rule leads.')
