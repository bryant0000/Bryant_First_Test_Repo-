"""Build native Office and machine-readable Cashflow review deliverables, not Markdown exports."""
from pathlib import Path
import json,subprocess,hashlib,re,html,datetime,copy,textwrap
from docx import Document
from docx.shared import Inches,Pt,RGBColor,Cm
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.worksheet.table import Table,TableStyleInfo
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from pptx import Presentation
from pptx.util import Inches as PI,Pt as PP
from pptx.dml.color import RGBColor as PC
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/professional-delivery';DATE='2026-10-27';BASELINE='v0.6.4';GAME_COMMIT='236a3933ecefbf34da7ec5c434dcd8b87efc0d41'
assert json.loads((ROOT/'package.json').read_text())['version']==BASELINE.removeprefix('v'), 'Review the document baseline before generating for another game version.'
NAVY='18354B';TEAL='087F8C';ORANGE='B76B16';GRAY='64748B';PALE='EAF3F5'
folders=['00-阅读入口与复核','01-立项与治理','02-需求与游戏规则','03-交互与视觉设计','04-技术与接口契约','05-开发计划与协作','06-测试与质量保证','07-发布与运维','08-用户验收','09-维护与变更']
for f in folders:(OUT/f).mkdir(parents=True,exist_ok=True)
facts=json.loads(subprocess.check_output(['node','-e',"const D=require('./reference-data.js'),E=require('./engine.js'),T=require('./table.js');const p=E.create(4,0,E.REFERENCE_PROFILE);const before={cash:p.cash,...E.ratTotals(p)};E.borrow(p,2000);console.log(JSON.stringify({data:D,game:T.create([{name:'契约样例',jobId:4,dreamId:0}],{rulesProfile:E.REFERENCE_PROFILE,chooseDreamsOnTurn:true}),borrowExample:{before,after:{cash:p.cash,...E.ratTotals(p)}}}));"],cwd=ROOT))
D=facts['data'];validation=json.loads((ROOT/'audit/validation-latest.json').read_text());report=json.loads((ROOT/'audit/display-fixes-v0.6.4.json').read_text());coverage=json.loads((ROOT/'audit/reference-coverage.json').read_text());sources=json.loads((OUT/folders[0]/'公开研究来源.json').read_text())
requirements=[
('REQ-001','完整包本地入口','解压完整包后打开index；无外部资源／接口仍可建房、开局、保存和恢复。','前端／构建','scripts/standalone-smoke.cjs','UAT-01','真实file入口仍待设备实测'),
('REQ-002','规则与财务','现金、资产、债务、月供与现金流按选定profile结算，不混用实体与在线版。','规则／数值','engine.test.cjs','UAT-02','机械测试通过，参考差异未关闭'),
('REQ-003','完整轮次','逐人选梦想、掷骰、待处理事件、结束回合与终局的先后关系正确。','规则／前端','scripts/reference-ui-smoke.cjs','UAT-02','有自动化证据，待用户验收'),
('REQ-004','显示与金额','中文标签、份数与最大允许交易金额不重叠；报表开合不写回旧布局。','UI／前端','scripts/attachment-regressions-smoke.cjs','UAT-03','1x/2x局部验证通过'),
('REQ-005','在线权威结算','非当前座位不能发游戏动作；过期version被拒绝；客户端不接收未来牌序。','后端','rooms.test.cjs','UAT-07','有自动化证据'),
('REQ-006','持久化与恢复','刷新／短暂断网恢复会话；未确认交易不被当作已完成。','前后端','scripts/online-smoke.cjs','UAT-06','跨版本迁移矩阵待补'),
('REQ-007','无遮挡查看棋盘','B或查看棋盘暂收卡片、报表、聊天；返回保留输入；R/E不结算。','前端','scripts/attachment-regressions-smoke.cjs','UAT-05','有自动化证据'),
('REQ-008','参考来源可追溯','原素材、规则观察和推断分别记录；不能把模板坐标当作所有运行分支已验证。','策划／QA','audit/dice-layout-fixtures.json','UAT-08','多骰运行位置待核验'),
('REQ-009','受测包可定位','版本、代码提交、入口HTML及ZIP SHA与测试证据关联。','发布／QA','audit/validation-latest.json','UAT-01','当前快照有记录'),
('REQ-010','原版一致性范围','版次、全部文案／规则／状态均有对照依据后才可宣布原版完全一致。','产品／规则审阅','audit/reference-coverage.json','UAT-08','阻断：原版全等未成立'),
('REQ-011','股票与借还子状态','取消不扣款；不足现金走差额贷款；返回后的份数与债务选择符合规则。','规则／前端','scripts/reference-ui-smoke.cjs','UAT-03','有局部自动化证据'),
('REQ-012','快车道与破产','税、投资检定、重整、出局和两类胜利的确认行为可恢复且不重复结算。','规则／QA','scripts/terminal-ui-smoke.cjs','UAT-08','罕见原站分支未完整观察'),
('REQ-013','声音与字体失败','音效开关有效，字体拒绝不阻断画布；音效失败不改变规则状态。','前端／音频','scripts/classic-sound-smoke.cjs','UAT-04','有自动化证据'),
('REQ-014','兼容性范围','在确定的系统、浏览器、显示比例、文件及在线入口组合实测。','QA','docs/development/06-测试与质量保证/测试策略与执行依据.md','UAT-01','目标矩阵待评审／实测'),
('REQ-015','安全边界','验证会话、来源、参数、权限、消息长度及存档保护；不声称已过安全审计。','后端／QA','scripts/rooms.cjs','UAT-07','局部控制已有，审计待执行'),
('REQ-016','可运维与回退','启动健康检查、磁盘备份、版本回退与迁移兼容有执行记录。','发布／运维','scripts/serve.cjs','UAT-06','回退演练待执行'),
('REQ-017','容量与性能','基于批准的并发、响应与资源预算做负载试验；服务器数量上限不等于性能承诺。','技术负责人／QA','scripts/rooms.cjs','UAT-07','指标待批准，尚无压测结论'),
('REQ-018','用户验收闭环','指定候选包与设备，逐场景记录实测、缺陷、遗留项和签收。','产品／用户／QA','audit/validation-latest.json','UAT-08','尚无正式最终签收')]
decisions=[('DEC-01','参考版次','官网经典在线版与实体101不可默认等同','确认最终比较版本和合法使用边界','产品／策划','待确认'),('DEC-02','黄金结算','官网观察600；当前按10×600=6000','选择复现网站行为或卡面计算','规则审阅／产品','待确认'),('DEC-03','语言与视觉','当前中文、参考站英文','分开确认文案、布局、像素与字体目标','UX／产品','待确认'),('DEC-04','教育贷款','参考profile初始化省略school债务','确认兼容范围，保留旧profile区别','规则审阅','待核验'),('DEC-05','多骰位置','原图与单骰模板锚点已核对，多骰居中属实现选择','补充不同页面的原站运行坐标证据','UX／QA','待核验'),('DEC-06','真实文件入口','内嵌index已在HTTP离线路径验证，环境阻止file自动化','Windows/Edge及Chrome真实双击并记录SHA','QA／用户','待执行'),('DEC-07','性能目标','单进程Node，rooms上限200不是容量结果','确定并发、响应延迟、存档写入预算','技术负责人','待评审'),('DEC-08','最终签收','已有353单测、27浏览器检查；无正式UAT批准','产品、规则审阅与用户签收具体候选包','产品／用户','待执行')]
decisions.append(('DEC-09', '快车道发薪口径', '当前参考profile发薪包含内圈salary − ratExpenses；报表收入仅fastBase + fastGain', '对照原版实际发薪，确认目标口径后再决定是否改规则', '规则审阅／产品', '待核验'))
risk=[('RSK-01','参考差异','高','规则冲突未决导致验收标准漂移','DEC-01/02/04','先确认比较基准，差异持续列账','产品／策划','开放'),('RSK-02','真实入口','高','HTTP测试不能替代用户file入口','DEC-06','指定设备实测完整包，不假造通过','QA','开放'),('RSK-03','存档升级','高','版本回退未演练可能读不回数据','REQ-006/016','备份、样本迁移矩阵、回退演练','技术／运维','开放'),('RSK-04','显示回归','中','异步刷新与长中文导致覆盖','REQ-004','连续开关、最大金额、DPR场景回归','前端／QA','受控但需持续回归'),('RSK-05','多进程与规模','中','文件存储不提供分布式事务','REQ-017','限制已验证部署范围，扩展前设计共享存储','后端','开放'),('RSK-06','素材与术语','高','公开可下载不等于已取得商业使用授权','REQ-008/010','发布前核对素材、商标与文案授权依据','产品／授权审查','待核验')]
state_rows=[('UI-01','标题／房间列表','无会话','创建／选择房间','房间不存在、容量满、密码错误','REQ-001/005'),('UI-02','建房／等待','有效房间','命名、准备、开始','UI名8／密码4；服务端上限不同，勿混淆','REQ-003/005'),('UI-03','梦想选择','本座位首回合','前后切换／确认','选定前不能掷骰','REQ-003'),('UI-04','开始／休整','未移动、无pending','借还、选骰、掷骰或确认休整','非当前玩家不可操作','REQ-003/011'),('UI-05','选择牌堆／报价','机会事件','小买卖、大买卖、买卖或跳过','不能越过强制事件','REQ-002/011'),('UI-06','股票份数','stockTrade','增减、输入、确认、取消','标签与总价分行，实时更新','REQ-004/011'),('UI-07','借款／偿债','borrowReview/debtPicker/debtReview','选择金额或负债、确认／取消','按整千及现金约束处理，不直接改DOM现金','REQ-002/011'),('UI-08','市场／支出','market/payment等','出售、支付、确认','匹配条件和全局分发按规则层决定','REQ-002/003'),('UI-09','报表','个人座位数据','展开／关闭','rat/fast互斥；close异步不能重建旧表','REQ-004/006'),('UI-10','快车道／风险','fastDeal/investmentRoll','购买／确认结果','风险显示本次die，不用上一回合骰点','REQ-008/012'),('UI-11','破产与终局','insolvent/recovery/胜负','清算／还款／确认／直接退出','操作去向和刷新恢复必须一致','REQ-012'),('UI-12','棋盘查看','保留表单与当前状态','查看／返回、B、Esc','暂收纸张，禁R/E，不触发结算','REQ-007'),('UI-13','退出确认','用户选择退出','是／否','保留当前卡；终局直接退出另处理','REQ-003/012'),('UI-14','断线／旁观','在线恢复或非当前座位','重连／查看自己的报表','不暴露其他玩家操作权限或未来牌序','REQ-005/006')]
modules=[('engine.js','规则引擎','玩家现金、资产、贷款与pending转换','不得依赖DOM或音效成功'),('table.js','多人轮序','active、rolled、队列、逐人梦想','共享事件不能重复执行'),('reference-data.js','规则数据','12职业、182机制牌、48外圈','来源字段与sourceId可追溯'),('online.js','会话客户端','版本、指令、重连和UI权限','不能在断线时自行结算在线交易'),('local-rooms.js','离线适配','同机房间与持久化','不是跨设备安全或联机服务'),('scripts/rooms.cjs','权威房间服务','认证、轮序、版本、磁盘保存','单进程文件模型，非分布式事务'),('interaction.js','状态展示与操作','卡片、报表、检查棋盘、草稿','关闭窗口不应改变交易状态'),('classic-stage.js / scene-canvas.js','布局与绘制','固定舞台、原图、文本和动态层','Canvas和DOM需同步且受字段边界约束'),('scripts/build-preview.py','交付构建','内嵌index与离线HTML、版本与SHA','候选构建不等于正式原版全等验收')]
phases=[('01','立项与治理','项目章程、RACI、风险','范围与责任明确','产品／技术负责人'),('02','需求与规则','PRD、GDD、数据与决策工作簿','规则、来源和通过条件可执行','产品／策划'),('03','交互与视觉','UI规格、流程原型、素材表','关键状态、异常和长文案有依据','UX／UI／前端'),('04','技术契约','架构、OpenAPI、JSON Schema','客户端／服务端／存档边界一致','技术负责人／前后端'),('05','实施与协作','WBS、追踪、交接与变更','任务有输入、依赖、完成定义','制作人／研发'),('06','测试与质量','用例、环境矩阵、缺陷及报告','阻断缺陷关闭，证据范围明确','QA／研发'),('07','发布与运维','构建、配置、备份、回退','解压包与受测文件一致','发布／运维'),('08','用户验收','UAT、签收记录、遗留项','指定包、环境、责任人明确结论','产品／规则审阅／用户'),('09','维护与变更','问题、决策、回归与归档','修复可追溯，旧流程不破坏','产品／研发／QA')]
# Office helpers: native editable headings/tables, repeated headers, revision control and controlled signatures.
def font_run(run,size=None,color=None,bold=False):
 run.font.name='Noto Sans CJK SC';run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC');run.bold=bold
 if size:run.font.size=Pt(size)
 if color:run.font.color.rgb=RGBColor.from_string(color)
def table(doc,headers,rows):
 t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
 for c,h in zip(t.rows[0].cells,headers):c.text=str(h);pr=c._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),NAVY);pr.append(sh)
 repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
 for row in rows:
  cells=t.add_row().cells
  for c,value in zip(cells,row):c.text=str(value)
 for i,row in enumerate(t.rows):
  pr=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(pr)
  for c in row.cells:
   for p in c.paragraphs:
    p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(3)
    for run in p.runs:font_run(run,9,color='FFFFFF' if i==0 else '22384A',bold=i==0)
 return t
def make_doc(folder,filename,docid,title,subtitle,sections):
 doc=Document();s=doc.sections[0];s.page_height=Cm(29.7);s.page_width=Cm(21);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.7);s.left_margin=Cm(1.8);s.right_margin=Cm(1.8)
 for st in ['Normal','Body Text']:
  doc.styles[st].font.name='Noto Sans CJK SC';doc.styles[st]._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC');doc.styles[st].font.size=Pt(10.5);doc.styles[st].paragraph_format.space_after=Pt(7);doc.styles[st].paragraph_format.line_spacing=1.2
 for name,size in [('Title',28),('Heading 1',17),('Heading 2',12)]:
  doc.styles[name].font.name='Noto Sans CJK SC';doc.styles[name]._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC');doc.styles[name].font.size=Pt(size);doc.styles[name].font.color.rgb=RGBColor.from_string(NAVY);doc.styles[name].paragraph_format.keep_with_next=True
 p=s.header.paragraphs[0];font_run(p.add_run('CASHFLOW  |  ENGINEERING REVIEW     '+docid),8,GRAY)
 p=s.footer.paragraphs[0];font_run(p.add_run(f'{BASELINE}  /  待评审基线  /  {DATE}                         '),8,GRAY)
 fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');p._p.append(fld)
 doc.add_paragraph('CASHFLOW · WEB GAME',style='Subtitle');doc.add_paragraph(title,style='Title');doc.add_paragraph(subtitle,style='Subtitle')
 table(doc,['受控项','当前值'],[['文档编号',docid],['实现基线',BASELINE+' / '+GAME_COMMIT[:12]],['编制与复核日期',DATE],['文档性质','基于现有实现补建的评审稿；不是已批准的大公司内部模板'],['批准状态','产品／技术／QA／用户角色待指定并签署；未补造历史批准']])
 doc.add_paragraph('阅读说明',style='Heading 1');doc.add_paragraph('蓝色章节对应开发依据；表格中的“已有证据”限定到列出的版本和测试范围。待评审、待实测和未决差异不得作为发布通过结论。数字、来源与代码路径均按当前仓库复核。')
 doc.add_paragraph('本文件目录',style='Heading 1')
 for i,(head,_) in enumerate(sections,1):doc.add_paragraph(f'{i:02d}   {head}')
 doc.add_page_break()
 for head,items in sections:
  doc.add_paragraph(head,style='Heading 1')
  for item in items:
   if isinstance(item,str):doc.add_paragraph(item)
   elif item[0]=='table':table(doc,item[1],item[2])
   elif item[0]=='image':
    doc.add_picture(str(item[1]),width=Cm(16.8));doc.add_paragraph(item[2],style='Caption')
 doc.add_paragraph('评审与变更控制',style='Heading 1');table(doc,['角色','应复核内容','当前状态'],[['产品／策划','范围、规则冲突和验收口径','待指定，未签署'],['设计／研发','页面、契约、实现与技术边界','需按文档问题单评审'],['QA／用户','证据可复现性及实际交付包','自动化证据与用户签收分开']])
 doc.add_paragraph('变更登记：文档版本1.0；本次建立原生Office交付与结构化契约。后续应记录需求／决策ID、受影响文件、修订内容、评审结论及关联构建；批准栏不得由生成工具自动填写。')
 path=OUT/folder/(filename+'.docx');doc.save(path);return path
wb_counter=0
def workbook(folder,name,sheets):
 global wb_counter
 wb=Workbook();intro=wb.active;intro.title='使用说明';intro.append(['CASHFLOW 评审工作簿',BASELINE,DATE]);intro.append(['状态','原生可编辑；事实、自动化证据、待评审及待执行分开']);intro.append(['操作','蓝色表头可筛选；冻结标题；金额为数值单元格；不填写虚构签字']);intro.append(['来源','当前代码、audit/validation-latest.json、公开来源台账']);intro.append(['批准','待指定责任角色正式评审；本次仅复核资料和文件有效性'])
 for title,heads,rows in sheets:
  ws=wb.create_sheet(title);ws.append([name]);ws.append(['基线 '+BASELINE+' | '+DATE+' | 自动化通过不代替最终验收']);ws.append(['请使用筛选定位ID；字段名称保留实现含义，来源与状态不得删除。']);ws.append(heads)
  for row in rows:ws.append([json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in row])
  ws.freeze_panes='B5';ws.sheet_view.showGridLines=False;ws.auto_filter.ref=f'A4:{ws.cell(max(4,ws.max_row),len(heads)).coordinate}'
  if rows:
   wb_counter+=1;t=Table(displayName='CFTable'+str(wb_counter),ref=f'A4:{ws.cell(ws.max_row,len(heads)).coordinate}');t.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True);ws.add_table(t)
  for row in ws.iter_rows(min_row=4):
   for c in row:c.font=Font(name='Microsoft YaHei',size=10,color='24374B');c.alignment=Alignment(vertical='top',wrap_text=True)
  for c in ws[4]:c.fill=PatternFill('solid',fgColor=NAVY);c.font=Font(name='Microsoft YaHei',bold=True,color='FFFFFF',size=10)
  for col in range(1,len(heads)+1):
   sample=[str(ws.cell(i,col).value or '') for i in range(4,min(ws.max_row,100)+1)];width=min(48,max(14,max((len(x) for x in sample),default=12)*1.4))
   if any(x in heads[col-1] for x in ['说明','预期','依据','证据','操作','标准','范围','理由','处理']):width=45
   ws.column_dimensions[ws.cell(4,col).column_letter].width=width
  ws.row_dimensions[1].height=28;ws.row_dimensions[4].height=32
  for i in range(5,ws.max_row+1):ws.row_dimensions[i].height=48 if any(len(str(c.value or ''))>35 for c in ws[i]) else 32
  ws.sheet_properties.pageSetUpPr.fitToPage=True;ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0;ws.print_title_rows='1:4';ws.print_options.horizontalCentered=True
  for col,head in enumerate(heads,1):
   if head=='状态':
    values=sorted(set(str(ws.cell(i,col).value) for i in range(5,ws.max_row+1) if ws.cell(i,col).value))
    options=','.join(values)
    if len(options)<220:
     dv=DataValidation(type='list',formula1='"'+options+'"');ws.add_data_validation(dv);dv.add(f'{ws.cell(5,col).column_letter}5:{ws.cell(5,col).column_letter}500')
 for ws in [intro]:
  ws.column_dimensions['A'].width=25;ws.column_dimensions['B'].width=95;ws.column_dimensions['C'].width=20
  for row in ws:
   for c in row:c.font=Font(name='Microsoft YaHei',size=11,color=NAVY);c.alignment=Alignment(wrap_text=True,vertical='top')
  for i in range(1,6):ws.row_dimensions[i].height=40
 wb.calculation=CalcProperties(calcId=191029,fullCalcOnLoad=True)
 path=OUT/folder/(name+'.xlsx');wb.save(path);return path
# Diagrams are editable vector files, also consumed by the browser prototype and review deck.
def diagram(name,labels,edges,caption):
 positions=[(35+(i%3)*350,75+(i//3)*150) for i in range(len(labels))];height=120+((len(labels)+2)//3)*150
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#087f8c"/></marker></defs><rect width="1100" height="{height}" fill="#f5f8fb"/><text x="35" y="36" font-family="sans-serif" font-size="23" fill="#18354b">{html.escape(caption)}</text>']
 for a,b in edges:
  x,y=positions[a];xx,yy=positions[b];svg.append(f'<path d="M{x+300},{y+40} L{xx},{yy+40}" stroke="#087f8c" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')
 for i,(label,(x,y)) in enumerate(zip(labels,positions)):
  svg.append(f'<g><rect x="{x}" y="{y}" width="300" height="85" rx="12" fill="white" stroke="#087f8c"/><text x="{x+18}" y="{y+27}" font-family="sans-serif" font-size="12" fill="#64748b">{i+1:02d}</text><text x="{x+18}" y="{y+57}" font-family="sans-serif" font-size="20" fill="#18354b">{html.escape(label)}</text></g>')
 svg.append('</svg>');p=OUT/folders[3]/(name+'.svg');p.write_text(''.join(svg));return p
flow=diagram('用户回合流程',['标题／本地或在线房间','职业与逐人梦想','开始回合／休整','掷骰与移动','事件／贷款／交易子状态','更新报表与结束回合','进入快车道／投资','重整／胜利／退出','保存、刷新及重连'],[(0,1),(1,2),(2,3),(3,4),(4,5),(5,2),(5,6),(6,7),(7,8)],'用户流程｜跨子状态禁止重复结算')
arch=diagram('系统架构',['用户／DOM交互','本机房间适配','在线会话客户端','engine + table规则','Node权威房间服务','版本／轮序／权限检查','localStorage','JSON文件持久化','Canvas、声音与视觉资源'],[(0,1),(0,2),(1,3),(2,4),(4,5),(5,3),(1,6),(4,7),(3,8)],'运行架构｜离线与在线共享指令语义，权威边界不同')
# Native Word content: specific requirements and engineering decisions, not conversions of previous Markdown.
make_doc(folders[1],'项目章程与治理','CF-CHARTER-01','项目章程与治理基线','范围、角色、阶段门禁与风险',[
('项目目标与交付边界',['目标是中文经典现金流网页游戏：完整包index可本机运行，Node服务支持不同浏览器联机。用户关注规则、原版交互与显示、解压试玩和回归质量。当前不承诺账号排行、分布式房间、大规模匹配或全部原版全等。','实现基线为v0.6.4；当前文档通过源码与已有报告补建，不追溯伪造过去的评审。官网在线版、实体101与中文参考站需要分别建立版本来源。']),
('阶段门禁与职责',[('table',['阶段','核心交付','通过标准','责任角色'],[(a+' '+b,c,d,e) for a,b,c,d,e in phases]),'G0范围确认→G1规则与页面基线→G2技术契约→G3纵向切片→G4功能回归→G5候选包验证→G6用户验收。未取得批准的门禁不因为存在代码而自动通过。']),
('治理与风险',[('table',['风险','级别','风险描述','当前处理'],[(x[0],x[2],x[3],x[5]) for x in risk]),'负责角色可以由同一人兼任，规则确认、实现与最终签收仍需分开记录。实际任命、预算和排期没有已确认资料，工作簿保留待指定，不填写虚构人员或日期。']),
('公开研究与适配',['OpenAPI的官方规范支持将接口变成可生成文档、客户端和测试的结构化契约；JSON Schema官方仓库说明其用途是数据验证与注释。本交付将二者用于实际房间API和游戏快照，而非只提供文字描述。','Microsoft Xbox GDK Samples公开资料按工具、媒体、样例、环境与版本迁移组织信息；本项目采用相同的“环境基线、实现资料、兼容变更”分离原则。该资料同时使用Markdown，说明文件扩展名并不决定专业性；本次按用户评审需要提供Office和PDF。','W3C仓库提供可访问性内容组织参考。当前未完成WCAG审计，不标记合规。NASA及ISO等部分站点访问失败，未取得的内容不作为已学习的条款或企业内部模板依据。'])])
make_doc(folders[2],'PRD产品需求规格','CF-PRD-01','产品需求规格 PRD','目标场景、验收条件与范围约束',[
('用户与入口',['主要用户通过下载完整包、解压并打开index.html试玩；在线玩家需要访问同一个Node服务。index内嵌资源与纯离线cashflow-offline.html不同，HTTP访问自动入口仍可使用真实房间接口。','用户场景：建立单人或多人房间→逐人选择梦想→掷骰处理事件→买卖、借还→保存／恢复→进入快车道或破产→完成终局。旁观者可以看自己的报表，不获得当前玩家的结算权限。']),
('需求基线',[('table',['需求','可验证行为','责任角色','当前状态'],[(a+' '+b,c,d,g) for a,b,c,d,e,f,g in requirements])]),
('关键验收故事',['REQ-004：给定股票价格500和份数99,999，输入后应显示49,999,500；中文标签与金额分区，金额完整处于93px区域，不靠省略号隐藏数值。买入／卖出分别验证。','REQ-007：给定有未确认交易并已输入份数，查看棋盘时没有结算；R／E不会推进；返回时输入和原卡恢复。新的决策到来不能继续停在过期检查状态。','REQ-005：给定两名玩家，非当前玩家发送动作应拒绝；旧version不能被当成新指令执行。刷新后先恢复权威状态，再允许操作。']),
('非功能与非目标',['目前采用固定1024×768舞台，小屏横向查看。真实Windows浏览器的文件入口、跨系统字体、容量、性能及可访问性仍需矩阵实测。不能把Chromium测试替代所有浏览器。','建议评审的量化指标包括：支持的浏览器／系统版本、95分位响应延迟、房间并发和玩家数量、磁盘写入预算、恢复时间。现有200房间上限是代码限制，不是压测证明。','原版全等属于REQ-010的更强要求，当前仍阻断。对已知差异的批准或豁免需要产品与规则审阅记录，不在文档生成时自动决定。'])])
be=facts['borrowExample'];property_offer=next(x for x in D['small'] if x['type']=='property')
make_doc(folders[2],'GDD玩法与数值设计','CF-GDD-01','玩法与数值设计 GDD','规则profile、财务模型、卡牌与事件状态',[
('机制与组件',[f"当前数据修订：{D['revision']}。含{len(D['jobs'])}职业、{len(D['small'])}小买卖、{len(D['big'])}大买卖、{len(D['market'])}市场、{len(D['doodads'])}额外支出、{len(D['dreams'])}梦想、24内圈及48外圈。完整记录和sourceId在规则数据工作簿中。",'reference-web-2026-10-23与旧规则profile共存。引用官网机械字段不能自动证明实体版次、所有文案和全部运行分支一致。']),
('财务计算与实例',[('table',['量','实现关系','卡车司机实例'],[['月被动收入','assets中income之和','开局0'],['月支出','tax + other + 所有贷款payment + kids×childCost',str(be['before']['expenses'])],['月净现金流','salary + passive − expenses',str(be['before']['flow'])],['初始现金（参考profile）','一次性savings',str(be['before']['cash'])],['借入2000后','现金+2000；月供增加200',f"现金{be['after']['cash']}，支出{be['after']['expenses']}，净流入{be['after']['flow']}"]]),f"实牌样例 {property_offer['sourceId']}：{property_offer['name']}，总价{property_offer['value']}，首付{property_offer['down']}，抵押{property_offer['debt']}，净收入{property_offer['income']}。资产总价和首付不可混用；清算的回收基准需依所选规则，而非按总价随意打折。"]),
('事件、胜负与队列',['主状态由table控制active／rolled／ui，子状态由pending.kind承载。强制事件必须经确认或合法子流程完成后才可结束回合；取消应返回previous而不执行交易。','参考profile中，内圈被动收入严格大于支出才提出进入快车道确认；进入时基础现金流转换与初始资金按引擎实现处理。新增现金流达到50,000或购买自己的梦想可以获胜。破产包含资产清算、偿债、债务减半、恢复休整或出局。','随机骰与牌序只在规则／权威服务使用；DOM、音效或动画失败不得额外结算。在线响应不带未来decks。']),
('冲突与未决规则',[('table',['决策','当前事实','处理要求','状态'],[(a,b+': '+c,d,f) for a,b,c,d,e,f in decisions[:5]]),'原始官网实测、第三方镜像、独立机械夹具和推断需要在来源台账区分。金钱边界、银行按整千偿还与股票份数等应通过独立样例验证，不只镜像实现代码。'])])
make_doc(folders[3],'交互与视觉设计规格','CF-UX-01','交互与视觉设计规格','页面状态、几何、中文排版与恢复行为',[
('用户流程与状态',[('table',['状态','进入条件','操作','异常／约束'],[(a+' '+b,c,d,e) for a,b,c,d,e,f in state_rows]),'同目录提供可独立打开的HTML交互原型与可编辑SVG。原型用于评审布局和状态，不接管真实游戏结算。']),
('布局与字段规范',[('table',['区域','坐标／尺寸','设计要求'],[['舞台','1024×768；上边距25','保持坐标基准；窄屏横向查看'],['报表','x0 y56；696×712','内圈／快车道互斥；开关立即重画'],['卡片','x656 y98；354.5×388.3含操作区','保持主操作命中区，允许查看棋盘'],['主按钮','110×44','单独标签层，不能被旧CSS挤压'],['股票金额','相对事件内容x207；93px列','说明与金额上下分行，数值按宽度适配'],['单骰模板','x483.3 y436.2；64×59','使用官网原始木纹图集；不随报表移至右侧']]),'中文标签不能照搬短英文的固定起点。快车道底部标签与金额作为整行限宽绘制；当前收入及目标文字也需适配宽度。多骰围绕单骰锚点居中属于当前实现选择，未全部获得原版运行坐标证据。']),
('事件与显示层契约',['报表关闭后不能重新注入旧fast-sheet布局，也不能删除当前卡牌图标。事件状态转换、DOM和Canvas刷新应使用统一路径。','查看棋盘会暂收卡片、报表及聊天纸张；返回保留普通输入和空白输入对应的金额显示。禁止在查看状态使用R/E结算。新轮次或新决策应恢复控件。','字体加载拒绝时继续初始化并回退。画布金额限于字段边界，避免只在默认金额下可读。'],),
('实际实现截图（v0.6.4）',[('image',ROOT/'audit/screenshots/v0.6.4/stock-amount.png','基线截图：股票说明与金额分行；实际实现证据，不代替所有状态批准。'),('image',ROOT/'audit/screenshots/v0.6.4/full-board.png','基线截图：暂收纸张后完整快车道可见。')])])
make_doc(folders[4],'技术设计与联调契约','CF-TDD-01','技术设计与联调契约','模块边界、权威结算、持久化与故障处理',[
('运行架构',[('table',['模块','职责','输入／输出','约束'],modules),'原生接口文件openapi.json使用OpenAPI 3.1；game.schema.json使用JSON Schema 2020-12。它们是本次补建的联调契约，当前服务并未自动挂载Schema验证中间件；引擎与房间服务的业务校验仍为实际权威。']),
('在线协议与并发',['同源HTTP JSON接口，以Authorization: Bearer传会话。房间创建／加入签发token；服务端保存哈希并剔除客户端decks。多数写操作要求最新version，聊天例外。','version用于乐观并发和拒绝重复／过期动作，不等于已实现通用idempotency-key协议。GET读房间也更新presence；离线重连可能改变版本。客户端遇409应先拉取最新状态，不能悄悄再结算一次。','游戏动作先克隆状态、应用规则成功后替换房间；失败不能把半完成状态写回。POST来源校验、请求8192字节限制、密码scrypt与token哈希等控制已有实现，但尚无完整安全审计。']),
('数据与存档',['game v3、规则修订和rulesProfile分别表达结构、数据版本与兼容规则。schema覆盖外层、玩家、资产／贷款、历史与主要pending数据。无法由JSON Schema表达的轮序、金额平衡、引用存在性仍在规则层验证。','app本机游戏键cashflow-classic-table-v3；离线房间cashflow-local-rooms-v1；在线会话cashflow-online-session-v1。它们不是相同内容，不应只备份一个键就承诺全恢复。','服务端文件包version=1，默认.cashflow/rooms.json；写临时文件再rename。当前是单进程JSON存储模型，没有共享数据库与分布式锁，不应直接横向复制服务进程。']),
('错误与恢复',[('table',['情形','实际行为／要求','联调检查'],[['401/403','会话或权限失败；不在本地补操作','无token、旁观者动作、来源校验'],['409','version过期，恢复最新视图','重复点击、重连后旧版本'],['400/413','参数／规则错误或请求过大','金额、骰子、JSON与消息边界'],['短暂断网','保留会话并重试恢复；期间阻止本地在线结算','刷新、恢复、同一浏览器接回'],['存档不兼容','校验版本与字段；不默认迁移成功','旧样例与实际回退演练']]),'容量、TLS、代理信任、跨版本迁移和恢复时间尚无正式批准指标。需要按部署环境评审，不把现有代码限制写成通过的SLA。'])])
make_doc(folders[5],'实施计划与部门交接','CF-PLAN-01','实施计划与部门交接','WBS依赖、责任、需求追踪和完成定义',[
('开发阶段与产物',[('table',['子阶段','输入','输出','完成条件'],[['环境骨架','范围与技术边界','启动／构建入口','可复现环境记录'],['规则与数据','GDD、决策与字段字典','引擎、导入数据、独立夹具','金额和边界可验证'],['纵向切片','一个用户故事与接口','开局至一次结算与保存','取消、失败和刷新也贯通'],['完整闭环','全部关键状态','单机／联机与恢复','主流程及异常回归'],['表现与稳定','UI规格及缺陷台账','界面、音频、候选包','实际数据、长中文、字体失败验证']]),'已有功能并不能追溯证明所有历史门禁获批。工作分解表同时记录已有证据与剩余实施任务，不虚构承诺日期和人员。']),
('跨部门交接',[('table',['交接双方','必须交付','验收责任'],[['产品→策划／设计','带ID需求、范围和冲突决定','目标与标准可执行'],['策划→规则／数据','字段含义、公式、例子、来源和边界','结算与牌面不能各自解释'],['UX/UI→前端','状态表、坐标、字体、层级、素材和异常','中文与最大金额有处理策略'],['前端↔后端','指令、请求响应、权限、错误与恢复','双方用相同版本契约联调'],['研发→QA','受测提交、构建、样例、影响范围','证据能复现并追溯需求'],['QA→发布／用户','候选包SHA、缺陷与验收结果','包和报告一致、遗留明确']])]),
('变更与完成定义',['任务完成需同时满足：输入版本明确、实现可定位、针对性及必要回归通过、接口／Schema／数据／页面同步更新、未决问题记账。开发完成、QA通过、产品批准和用户签收是四个不同状态。','当前P0：真实file入口、规则比较基准和高影响差异决定。P1：逐页批准基线、存档迁移、接口契约评审。P2：容量性能、安全和可访问性目标及实测。工作簿给出前置依赖和负责角色；实际负责人、预算和时间待正式分配。'])])
make_doc(folders[6],'测试设计与质量报告','CF-QA-01','测试设计与质量报告','证据范围、环境矩阵、缺陷与发布门禁',[
('现有结果与证据边界',[f"最近已有v0.6.4报告记录{validation['unit_tests']['passed']}项单元测试、{validation['browser_check_count']}套浏览器检查通过，读取audit/validation-latest.json及各日志校验值。本次文档复核不会把这些历史执行重标为今日重跑。",'另有95个实际买卖牌布局边界扫描。选定区域像素相等、合成容差、规则夹具和真实用户验收是不同证据类型。原版运行界面虽有观察，完整内容与全部页面一致性仍未成立。']),
('测试分层与设计',[('table',['层次','检查重点','依据'],[['规则／数据','结算、阈值、份数、破产、胜负和非法输入','engine、reference、decks单测'],['接口／联机','座位权限、版本、重复请求、恢复与持久化','rooms单测、online／observer脚本'],['交互','确认、取消、贷款子流程、终局退出','reference-ui、card-contract、terminal'],['视觉','真中文、极值金额、连续开关、原图与遮挡','display、attachments、visual'],['打包','解压的index离线路径及独立服务','standalone、index-local、包哈希'],['人工／兼容','真实file、OS、浏览器、用户验收','当前待补实测矩阵']]),'新建用例设计工作簿不伪造执行结果；单独保留“已有自动化证据”和“待本轮人工执行”。异常条件与组合场景需要按风险选择，不以数量替代覆盖。']),
('缺陷与门禁',['P0：不能启动、数值错、越权、重复结算、丢档；P1：主流程卡住或关键字段不可读；P2：可绕过的局部展示问题。关闭缺陷必须关联修复提交、受测包、环境、复现与回归范围。','v0.6.3／0.6.4修复记录是历史事实；当前工作簿不将“已修复”改成“用户已签收”。原始附件相关的股票重叠、异步旧布局和棋盘遮挡均需在真实入口中由用户复验。']),
('尚未通过的验收范围',['环境策略阻止自动导航file://；已验证HTTP下的内嵌index离线路径及阻止额外资源／API，但不能声称已自动完成用户双击入口。','完整浏览器／系统矩阵、负载与容量、安全审计、可访问性、迁移与回退演练、原版全部运行分支和正式UAT仍未完成。原版全等发布门禁保持阻断。'])])
make_doc(folders[7],'发布运维与回退手册','CF-REL-01','发布运维与回退手册','受测包、环境、发布步骤与数据保护',[
('构建与环境',['Node.js 18+；运行服务无需安装运行依赖，浏览器测试另需Playwright和Chromium。npm run build:preview用于阶段包；npm run release:check针对更强的原版全等要求，当前应阻断。','完整包index内嵌运行资源并按协议选择本机／在线适配；cashflow-offline.html保持纯离线。本机双击与HTTP静态托管、Node联机服务属于不同交付场景，检查表必须分行记录。']),
('发布操作',['1. 固定提交与版本并备份存档；2. 执行适用回归并留存日志；3. 构建ZIP；4. 解压实际包分别检查入口和在线；5. 校验HTML与受测文件SHA；6. 保存下载地址、配置与已知差异；7. 记录批准和发布责任人。','Node启动命令：node scripts/serve.cjs --host 0.0.0.0 --port 3000。健康检查GET /healthz。默认存档.cashflow/rooms.json，可用CASHFLOW_ROOMS_FILE指定。域名、TLS、代理、磁盘权限和可访问范围必须按实际部署验证。']),
('回退与恢复',['先停止新写入、备份现有数据和配置，再恢复旧构建。只有旧版本已验证可读该存档才可直接接回；跨版本不兼容时先按演练的迁移／还原路径恢复，不承诺盲目降级成功。','现有记录没有完整迁移及回退演练结论。工作簿提供检查项目与执行证据栏，当前未执行的项目保持待执行。']),
('发布准入',[('table',['步骤','实际操作／命令','应留证据','当前状态'],[['备份', '停写后复制存档及配置', '备份路径、时间与可恢复性', '演练待执行'], ['构建', 'npm run build:preview', 'ZIP版本、提交与SHA', '有阶段构建记录'], ['启动', 'node scripts/serve.cjs --host 0.0.0.0 --port 3000', 'listening输出与GET /healthz', '实际部署需重测'], ['联机', '两个浏览器加入同一个服务', '准备、轮序和权限结果', '已有自动化证据'], ['本地入口', '解压并双击index.html', '设备、浏览器、缩放与完整流程', '真实文件入口待实测'], ['回退', '停写→备份→旧包与兼容存档', '旧版本可读及关键场景', '待演练']]),'受测文件与下载包一致；阻断缺陷关闭；遗留差异获明确处理；兼容及实际入口达到已约定范围；备份和回退步骤可执行；候选包被产品／QA确认。源码推送不能代替部署成功，阶段包也不能代替原版全等验收。'])])
make_doc(folders[8],'UAT与最终验收方案','CF-UAT-01','用户验收与最终关闭方案','用例、证据、遗留项及签收',[
('验收对象与角色',['验收必须指向一个不可变的候选ZIP、代码提交及入口HTML SHA。由产品确认范围，规则审阅者确认数值与版本依据，QA复核证据，用户在实际设备进行验收。角色尚未正式任命，不由文档工具代签。']),
('用户验收场景',[('table',['ID','操作','通过条件'],[['UAT-01','下载、解压、双击index及创建本机房间','无外部依赖；记录OS／浏览器／缩放和包SHA'],['UAT-02','选梦想、掷骰、处理事件与结束回合','轮序、现金和事件状态符合基线'],['UAT-03','股票极值、取消、借还与不足现金','金额完整可读；未确认不结算；返回正确'],['UAT-04','内外圈报表连续开关与字体失败','互斥、无旧布局回退、无字段溢出'],['UAT-05','查看棋盘并恢复输入','无遮挡、不推进、普通与空白输入保留'],['UAT-06','保存、刷新、断网与恢复','不重复结算；存档兼容范围有记录'],['UAT-07','两个浏览器加入和轮流操作','非当前座位拒绝动作；会话恢复正确'],['UAT-08','快车道、破产与终局、参考差异','行为与批准范围一致；未知项不默认为通过']])]),
('结论与遗留项',['验收结论只能为通过、不通过或有条件通过；有条件通过应列出明确遗留、影响、责任角色、约束和复验时间。当前没有正式最终签收记录。','原版全等验收还需要参考版次、全规则／文案／图像、全部特殊分支与交互的证据。黄金结算、多骰运行位置和实体手册等未决事项不能由自动化通过自动豁免。']),
('归档与关闭',['归档候选包与校验、实测环境、需求追踪、缺陷处理、规则差异结论和签收记录。维护版本继续保留历史；新增缺陷可重新打开，不删除原执行记录。'])])
make_doc(folders[9],'缺陷变更与维护规范','CF-OPS-01','缺陷、决策与持续维护','从用户反馈到复验关闭',[
('问题生命周期',['反馈→编号→复现→影响分析→决定范围→更新契约→修复→针对性测试→影响回归→候选包校验→用户复验→关闭。未复现、待验证、待用户复验不得直接标记为已关闭。']),
('当前问题与决定',[('table',['编号','事项','处理要求','当前状态'],[(a,b,d,f) for a,b,c,d,e,f in decisions]),'历史修复：v0.6.3本地入口、报表与骰子显示；v0.6.4股票金额、快车道旧布局回退、棋盘遮挡与原图骰子。记录对应源码和日志，不将历史自动化证据等同于用户已经签收。']),
('变更评审与影响',['每项变更记录需求／决策ID、规则数值与牌面、前后端指令、Schema、存档、素材、取消／恢复、测试与发布影响。实现可兼容不等于设计已批准，所有例外需要留下决定人与理由。','维护负责人实际姓名、响应时限和SLA尚未指定。当前文档提供职责与检查依据，不填写没有事实支持的服务承诺。'])])
# Native workbooks with actual data, traceability and explicit execution status.
workbook(folders[1],'治理职责与风险台账',[('阶段门禁',['阶段','名称','交付物','通过标准','负责角色','当前状态'],[(a,b,c,d,e,'待实际责任人评审') for a,b,c,d,e in phases]),('风险',['ID','类别','级别','事实／风险','关联','处理','负责角色','状态'],risk),('RACI',['活动','产品','策划','UX/UI','前端','后端','QA','发布','用户'],[['范围决定','A','R','C','C','C','C','I','C'],['规则核验','A','R','C','C','C','C','I','C'],['界面设计','A','C','R','R','C','C','I','C'],['API联调','I','C','C','R','A/R','C','C','I'],['质量回归','I','C','C','R','R','A/R','C','I'],['候选发布','A','C','I','R','R','R','R','I'],['最终签收','A','R','C','C','C','R','C','R']])])
heads=['需求ID','主题','通过标准','负责角色','测试／依据','UAT','状态']
sheets=[('需求清单',heads,requirements),('规则决策',['ID','主题','当前事实','处理要求','责任角色','状态'],decisions)]
for key,title in [('jobs','职业数据'),('small','小买卖'),('big','大买卖'),('market','市场'),('doodads','额外支出'),('dreams','梦想'),('fast','快车道')]:
 rows=D[key];keys=list(dict.fromkeys(k for row in rows for k in row));sheets.append((title,['记录序号']+keys,[[i]+[row.get(k,'') for k in keys] for i,row in enumerate(rows)]))
sheets.append(('数量复核',['组件','实际条数','来源'],[[k,len(D[k]),'reference-data.js'] for k in ['jobs','small','big','market','doodads','dreams','fast']]))
workbook(folders[2],'需求规则与数值主表',sheets)
assets=json.loads((ROOT/'assets/reference/SOURCES.json').read_text())
workbook(folders[3],'页面状态与素材规范',[('页面状态',['ID','页面','条件','操作','显示／异常要求','需求'],state_rows),('几何字段',['区域','x','y','宽','高','依据'],[['舞台',0,0,1024,768,'ClassicLayout'],['报表',0,56,696,712,'classic-stage.css'],['卡片',656,98,354.5,388.3,'ClassicLayout'],['主按钮',14.5,335.7,110,44,'cardTemplate'],['单骰锚点',483.3,436.2,64,59,'game_screen die'],['股票金额列',207,149.325,93,48,'v0.6.4中文适配']]),('素材台账',['文件','来源','SHA-256','用途范围'],[[a.get('file',''),a.get('source',''),a.get('sha256',''),a.get('scope','')] for a in assets])])
# API/schema generation follows current Rooms and actual client payload conventions.
tech=OUT/folders[4]
number={'type':'number'};integer={'type':'integer'};string={'type':'string'}
asset={'type':'object','required':['id','name','cost','value','debt','income','quantity'],'properties':{'id':number,'name':string,**{k:number for k in ['cost','value','debt','income','quantity']},'type':string},'additionalProperties':True}
loan={'type':'object','required':['id','name','balance','payment'],'properties':{'id':string,'name':string,'balance':number,'payment':number},'additionalProperties':True}
kinds=['notice','choose','deal','stockTrade','stockSplit','payment','doodadChoice','market','marketMust','baby','charity','enterFast','fastDeal','dream','investmentRoll','skipTurn','insolvent','debtHalved','recovery','bankruptLost','assetSale','debtPicker','debtReview','borrowReview','loanOffer']
pending={'type':['object','null'],'properties':{'kind':{'enum':kinds},'title':string,'amount':number,'cost':number,'loan':number,'die':{'type':'integer','minimum':1,'maximum':6},'quantity':number,'loanId':string,'assetId':number,'previous':{'type':['object','null']},'offer':{'type':'object'}},'required':['kind'],'additionalProperties':True,'description':'kind联合状态的结构检查；具体余额、引用存在性及合法转移由engine/table验证。'}
player={'type':'object','required':['version','ruleset','jobId','dreamId','turn','pos','stage','cash','assets','fastAssets','loans','lastDice','history','name'],'properties':{'version':{'const':3},'ruleset':string,'rulesProfile':{'type':['string','null']},'jobId':{'type':'integer','minimum':0,'maximum':11},'dreamId':{'type':'integer','minimum':0,'maximum':22},'name':string,'stage':{'enum':['rat','fast']},'pos':{'type':'integer','minimum':0,'maximum':47},'turn':{'type':'integer','minimum':0},'cash':number,'kids':{'type':'integer','minimum':0,'maximum':3},'assets':{'type':'array','items':{'$ref':'#/$defs/Asset'}},'fastAssets':{'type':'array','items':{'type':'object'}},'loans':{'type':'array','items':{'$ref':'#/$defs/Loan'}},'pending':{'$ref':'#/$defs/Pending'},'lastDice':{'type':'array','items':{'type':'integer','minimum':1,'maximum':6},'maxItems':3},'history':{'type':'array','items':{'type':'object','required':['turn','text'],'properties':{'turn':integer,'text':string}}}},'allOf':[{'if':{'properties':{'stage':{'const':'rat'}}},'then':{'properties':{'pos':{'maximum':23}}}}],'additionalProperties':True}
game={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:cashflow:game-v3','title':'Cashflow Game v3 snapshot','type':'object','required':['version','ruleset','players','active','rolled','decks','round'],'properties':{'version':{'const':3},'ruleset':string,'players':{'type':'array','minItems':1,'maxItems':6,'items':{'$ref':'#/$defs/Player'}},'active':{'type':'integer','minimum':0,'maximum':5},'rolled':{'type':'boolean'},'decks':{'type':'object','additionalProperties':{'type':'array','items':integer}},'round':{'type':'integer','minimum':1},'ui':{'type':['object','null']},'over':{'type':'boolean'}},'$defs':{'Player':player,'Asset':asset,'Loan':loan,'Pending':pending},'additionalProperties':True,'$comment':'active < players.length and monetary invariants require semantic validation; additional fields remain forward-compatible, not undocumented approval.'}
store={'$schema':game['$schema'],'title':'Server room store v1','type':'object','required':['version','rooms'],'properties':{'version':{'const':1},'rooms':{'type':'array','items':{'type':'object','required':['id','name','capacity','host','version','seats','game'],'properties':{'id':string,'name':string,'capacity':{'type':'integer','minimum':1,'maximum':6},'host':integer,'version':integer,'seats':{'type':'array','items':{'type':'object','required':['name','ready','tokenHash','jobId'],'properties':{'name':string,'ready':{'type':'boolean'},'tokenHash':string,'jobId':integer}}},'game':{'type':['object','null']}},'additionalProperties':True}}},'additionalProperties':True}
for name,data in [('game.schema.json',game),('room-store.schema.json',store),('game.example.json',facts['game']),('room-store.example.json',{'version':1,'rooms':[]})]:(tech/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
server=(ROOT/'scripts/rooms.cjs').read_text();allowed=re.search(r'const actions=new Set\(\[(.*?)\]\)',server).group(1);actions=re.findall(r"'([^']+)'",allowed);actions=[x for x in actions if x not in ['borrow','repay','sell']]+['chooseDream','cycleDream','end']
room_view={'type':'object','required':['id','name','capacity','version','chatRevision','chat','seat','host','players','game'],'properties':{'id':string,'name':string,'capacity':integer,'version':integer,'chatRevision':integer,'chat':{'type':'array','items':{'type':'object'}},'seat':integer,'host':integer,'players':{'type':'array','items':{'type':'object'}},'game':{'anyOf':[{'$ref':'#/components/schemas/Game'},{'type':'null'}]},'token':string},'additionalProperties':True}
oasgame=copy.deepcopy(game);oasgame.pop('$id',None)
def rew(v):
 if isinstance(v,dict):return{k:rew(x) for k,x in v.items()}
 if isinstance(v,list):return[rew(x) for x in v]
 if isinstance(v,str):return v.replace('#/$defs/','#/components/schemas/Game/$defs/')
 return v
oasgame=rew(oasgame)
schemas={'Error':{'type':'object','required':['error'],'properties':{'error':string}},'Game':oasgame,'RoomView':room_view,'RoomList':{'type':'object','required':['rooms'],'properties':{'rooms':{'type':'array','items':{'type':'object'}}}},'Left':{'type':'object','required':['left'],'properties':{'left':{'const':True}}},'CreateRoom':{'type':'object','properties':{'name':{'type':'string','maxLength':32},'capacity':{'type':'integer','minimum':1,'maximum':6},'playerName':{'type':'string','maxLength':8},'password':{'type':'string','maxLength':128}},'required':['capacity']},'JoinRoom':{'type':'object','properties':{'playerName':{'type':'string','maxLength':8},'password':{'type':'string','maxLength':128}}},'VersionBody':{'type':'object','required':['version'],'properties':{'version':integer}},'ReadyBody':{'type':'object','required':['version','ready'],'properties':{'version':integer,'ready':{'type':'boolean'}}},'RenameBody':{'type':'object','required':['version','name'],'properties':{'version':integer,'name':{'type':'string','maxLength':8}}},'ChatBody':{'type':'object','required':['message'],'properties':{'message':{'type':'string','minLength':1,'maxLength':256}}},'ActionBody':{'type':'object','required':['version','action'],'properties':{'version':integer,'action':{'enum':actions},'args':{'type':'array','maxItems':3,'default':[]}},'description':'Client payload convention. Per-action argument types and state guards are documented in the interface workbook; runtime semantic validation remains in Rooms/engine.'}}
oas={'openapi':'3.1.0','info':{'title':'Cashflow room API — implementation review contract','version':'0.6.4-doc1','description':'基于当前实现补建，供联调评审；不宣称服务已使用Schema中间件。UI房名8/密码4与服务端32/128上限分开。GET房间更新presence；除chat外的命令检查version。'},'servers':[{'url':'http://localhost:3000'}],'paths':{},'components':{'schemas':schemas,'securitySchemes':{'RoomBearer':{'type':'http','scheme':'bearer','description':'Room-scoped token issued by create/join; not an account or JWT.'}}}}
route_rows=[]
def op(path,method,name,body,response,auth=True,status='200',note=''):
 operation={'operationId':name,'summary':note or name,'responses':{status:{'description':'Success','content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+response}}}}},'security':[{'RoomBearer':[]}] if auth else []}
 if '{id}' in path:operation['parameters']=[{'name':'id','in':'path','required':True,'schema':string}]
 if body:operation['requestBody']={'required':True,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+body}}}}
 for code in ['400','401','403','404','409','413','503']:operation['responses'][code]={'description':'Validation/session/permission/version/limit failure as applicable','content':{'application/json':{'schema':{'$ref':'#/components/schemas/Error'}}}}
 oas['paths'].setdefault(path,{})[method]=operation;route_rows.append([method.upper(),path,body or '无',response,'Bearer' if auth else '无需已有会话',note])
op('/api/rooms','get','listRooms',None,'RoomList',False,note='列出可加入房间')
op('/api/rooms','post','createRoom','CreateRoom','RoomView',False,'201','创建房间并签发token；初始host就绪')
op('/api/rooms/{id}','get','readRoom',None,'RoomView',note='读取本座位视图并更新presence；decks为空')
op('/api/rooms/{id}/join','post','joinRoom','JoinRoom','RoomView',False,note='校验密码与容量，签发座位token')
for action,body,note in [('ready','ReadyBody','开局前准备'),('rename','RenameBody','开局前改名'),('start','VersionBody','房主开始；人员和准备需满足'),('action','ActionBody','仅当前座位；规则与状态校验'),('chat','ChatBody','独立chatRevision，无需version'),('leave','VersionBody','离开与轮序；等待房主可关闭房间')]:op('/api/rooms/{id}/'+action,'post',action+'Room',body,'Left' if action=='leave' else 'RoomView',note=note)
(tech/'openapi.json').write_text(json.dumps(oas,ensure_ascii=False,indent=2))
args_map={'roll':'[1|2|3]','deal':'["small"|"big"]','buy':'[可选份数]','payDoodad':'[是否分期:boolean]','openAssetSale':'[assetId:number]','openDebtReview':'[loanId:string]','changeDebtAmount':'[1|-1]','confirmDebtReview':'[可选金额:number]','confirmBorrowReview':'[金额:number]','openStock':'["buy"|"sell"]','stockQuantity':'[份数:number]','confirmStock':'[份数:number]','chooseDream':'[dreamId:number]','cycleDream':'[1|-1]'}
workbook(folders[4],'接口指令与数据字典',[('HTTP接口',['方法','路径','请求体Schema','响应Schema','会话','行为'],route_rows),('游戏指令',['action','参数约定','前置条件','代码依据'],[[a,args_map.get(a,'[]'),'当前座位、未结束、匹配pending；roll需未移动；梦想需ui状态','rooms.command / engine.'+a] for a in actions]),('Game字段',['字段','类型','约束／含义'],[[k,str(v.get('type',v.get('const','见引用'))),v.get('description','required' if k in game['required'] else '可选／见Schema')] for k,v in game['properties'].items()]),('玩家字段',['字段','类型','含义／限制'],[[k,str(v.get('type',v.get('$ref',v.get('enum','')))),json.dumps(v,ensure_ascii=False)] for k,v in player['properties'].items()]),('Pending分支',['kind','语义','验证边界'],[[k,'事件／交易子状态','JSON结构+engine合法转移、余额和引用检查'] for k in kinds]),('存储键',['位置／键','内容','边界'],[['cashflow-classic-table-v3','Game v3','本机游戏快照'],['cashflow-local-rooms-v1','本机房间包','同机适配，不是在线鉴权'],['cashflow-online-session-v1','在线会话','不输出真实token到日志'],['.cashflow/rooms.json','version=1 rooms[]','私密服务存档；备份与权限保护']])])
wbs=[('WBS-01','范围与冲突确认','DEC-01/02/04','无','产品／规则审阅','比较基准和差异有结论','待评审'),('WBS-02','真实文件入口','REQ-001/014','受测候选包','QA／用户','Windows真实index场景留证','待执行'),('WBS-03','逐页原版基线','REQ-004/008/010','WBS-01','UX／QA','截图／录屏、状态与位置对应','待核验'),('WBS-04','Schema与API评审','REQ-005/006','CF-TDD-01','前后端／QA','契约样例和实际服务相符','本次建立，待业务评审'),('WBS-05','存档迁移与回退','REQ-006/016','WBS-04','技术／运维','旧样本、升级回退演练通过','待执行'),('WBS-06','兼容与性能目标','REQ-014/017','WBS-01','技术／QA','指标批准再实测','待评审'),('WBS-07','安全及可访问性','REQ-015','WBS-04/06','技术／QA','按批准范围测试并关闭问题','待执行'),('WBS-08','最终UAT','REQ-018','WBS-01/02/03/05','产品／用户','具体包签收或明确条件','待执行')]
workbook(folders[5],'WBS需求追踪与交接',[('WBS',['ID','工作项','关联','前置依赖','负责角色','完成定义','状态'],wbs),('需求追踪',['需求ID','主题','设计依据','实现／测试依据','UAT','状态'],[[a,b,'CF-PRD-01 / CF-GDD-01 / CF-UX-01 / CF-TDD-01',e,f,g] for a,b,c,d,e,f,g in requirements]),('交接检查',['来源角色','目标角色','交接物','接收检查','状态'],[['产品','策划／研发','带ID需求与决策','范围和通过标准可执行','待评审'],['UX/UI','前端','页面／素材／异常状态','位置、输入、返回与字体边界','待评审'],['前端','后端','OpenAPI与指令矩阵','错误、版本、恢复和权限','本次建立'],['研发','QA','候选包与变更影响','可复现、提交与SHA完整','有历史证据'],['QA','用户／发布','报告、遗留和交付包','批准不代填','待签收']])])
cases=[('TC-01','REQ-001','完整包index离线路径','禁用额外请求，建房开局保存','无需外部资源、现金恢复','index-local-standalone-smoke'),('TC-02','REQ-002','规则数值','执行独立金额与职业夹具','数值和边界符合profile','unit'),('TC-03','REQ-003','梦想与轮次','逐人选梦想、掷骰和交棒','未选梦想不能推进','online-reference-ui-smoke'),('TC-04','REQ-004','买卖金额','500×99,999，买卖分别输入','49,999,500且说明不重叠','online-attachment-regressions-smoke'),('TC-05','REQ-004','报表异步开关','快车道连续开关5次','仅一套布局，图标不丢','online-attachment-regressions-smoke'),('TC-06','REQ-004','大额现金','百万级与更大金额','数值不绘到纸张外','online-attachment-regressions-smoke'),('TC-07','REQ-005','座位权限','非当前座位发动作','403且不结算','online-online-smoke'),('TC-08','REQ-005','过期版本','重复／旧version','拒绝且恢复权威状态','unit'),('TC-09','REQ-006','重连恢复','刷新时临时断网再恢复','保留会话，不重复结算','online-online-smoke'),('TC-10','REQ-007','查看棋盘','输入123和空白后查看／返回','输入、金额及原卡恢复','index-local-attachment-regressions-smoke'),('TC-11','REQ-007','查看期间键盘','按R/E及B/Esc','R/E不结算，可返回','online-attachment-regressions-smoke'),('TC-12','REQ-008','骰子图与位置','核图哈希、帧、模板及风险骰点','原图及锚点正确，风险用本次die','online-attachment-regressions-smoke'),('TC-13','REQ-011','股票子卡取消','进入份数再取消','返回报价，不扣款','online-reference-ui-smoke'),('TC-14','REQ-011','差额贷款','现金不足→贷款→返回确认','不丢事件，金额合法','online-reference-ui-smoke'),('TC-15','REQ-012','胜负退出','两类胜利与全员出局','正确按钮直接退出','online-terminal-ui-smoke'),('TC-16','REQ-013','音效与字体','静音／恢复，拒绝字体加载','声音时机正确，画布继续工作','font-denied'),('TC-17','REQ-014','1x/2x及手机','不同DPR与390px视口','局部字段与固定舞台可用','online-attachment-regressions-smoke'),('TC-18','REQ-005','旁观者自己的表','两浏览器操作与旁观','不出现可用借款／股票输入','online-observer-ui-smoke')]
manual=[('MAN-01','REQ-001/014','Windows 11 / Edge稳定版','真实file://双击index','待指定设备','待执行'),('MAN-02','REQ-001/014','Windows / Chrome稳定版','真实file://双击index','待指定设备','待执行'),('MAN-03','REQ-014','macOS / Safari及Chrome','文件／在线入口、字体','待指定设备','待执行'),('MAN-04','REQ-014','Firefox／移动浏览器','在线、横向查看和恢复','待指定设备','待执行'),('MAN-05','REQ-016','旧存档与回退版本','备份、升级、回退读取','样本及矩阵待整理','待执行'),('MAN-06','REQ-017','批准的负载环境','并发、延迟、磁盘写入','目标待评审','待执行'),('MAN-07','REQ-015','指定安全范围','认证、来源、输入、代理边界','审计范围待评审','待执行'),('MAN-08','REQ-018','用户实际设备','完整UAT与签收','候选包须固定SHA','待执行')]
bycheck={x['name']:x for x in report['checks']}
case_rows=[]
for a,b,c,d,e,key in cases:
 found=bycheck.get(key);case_rows.append([a,b,c,d,e,found['log'] if found else '见既有报告范围','v0.6.4既有自动化证据；未重标为今日执行'])
workbook(folders[6],'测试用例执行与缺陷',[('用例设计',['ID','需求','场景','操作','预期','已有证据','执行状态'],case_rows),('已有执行日志',['检查','命令','exit_code','日志','日志SHA','范围'],[[x['name'],' '.join(x['command']),x['exit_code'],x['log'],x['log_sha256'],'历史v0.6.4；不是本轮重新运行'] for x in report['checks']]),('人工环境矩阵',['ID','需求','环境','场景','前置要求','状态'],manual),('历史缺陷',['ID','现象','修复版本','验证依据','状态'],[['BUG-01','本地index外部资源／字体失败影响画布','0.6.3','display-fixes-v0.6.3.json','历史自动化有证据，待用户复验'],['BUG-02','财务表纸张与文字不同步、旧布局回退','0.6.3/0.6.4','attachment-fixes-v0.6.4.md','历史自动化有证据，待用户复验'],['BUG-03','股票标签与金额叠加、快车道超框','0.6.4','attachment-regressions脚本','历史自动化有证据，待用户复验'],['BUG-04','右侧卡片遮挡外圈','0.6.4','查看棋盘／返回及草稿回归','历史自动化有证据，待用户复验'],['BUG-05','多骰原版逐页位置缺少运行证据','未确认','dice-layout-fixtures.json','待核验']])])
release_rows=[('REL-01','固定代码提交、版本与构建','package.json／受测提交','发布','已有v0.6.4记录'),('REL-02','保存存档及配置备份','备份位置、时间、权限','运维','待执行演练'),('REL-03','适用回归与日志','validation-latest及实际日志SHA','QA','已有历史证据'),('REL-04','解压实际包启动','Node /healthz及双浏览器','发布／QA','已有自动化证据'),('REL-05','真实本地index','实际用户设备与文件入口','QA／用户','待执行'),('REL-06','包与受测HTML一致','HTML／ZIP SHA','发布','已有v0.6.4记录'),('REL-07','部署环境','域名、TLS、代理、存储和访问范围','运维','待实际部署验证'),('REL-08','升级与回退','兼容样本与演练记录','技术／运维','待执行'),('REL-09','用户验收与遗留','UAT签收或明确条件','产品／用户','待执行')]
workbook(folders[7],'发布与回退检查表',[('发布检查',['ID','检查项','证据要求','负责角色','状态'],release_rows),('配置基线',['配置','当前值／用法','注意'],[['Node','18+','测试工具另需Playwright/Chromium'],['启动','node scripts/serve.cjs --host 0.0.0.0 --port 3000','其他设备需访问同服务'],['健康','GET /healthz','源码推送不等于部署'],['存档','CASHFLOW_ROOMS_FILE / .cashflow/rooms.json','发布前备份，保护权限'],['结构版本','Game=3 / room-store=1','结构、规则修订、profile分别核对']])])
uat_rows=[('UAT-01','REQ-001/009/014','下载、解压、双击index并建房','无外部依赖；记录OS、浏览器和SHA'),('UAT-02','REQ-002/003','梦想、掷骰、事件与交棒','轮序、现金和状态符合基线'),('UAT-03','REQ-004/011','份数、极值金额、取消和贷款','完整可读，取消不扣，返回正确'),('UAT-04','REQ-004/013','报表开关、字体失败与音效','互斥、无旧布局及非法阻断'),('UAT-05','REQ-007','棋盘查看、键盘和草稿','无遮挡，不推进，返回输入保留'),('UAT-06','REQ-006/016','保存、刷新、断网及恢复','不重复结算，有存档兼容证据'),('UAT-07','REQ-005/015/017','不同浏览器轮流操作','会话、权限及批准容量范围正确'),('UAT-08','REQ-008/010/012/018','快车道、破产、胜负与差异','按批准范围明确结论，未决不默认通过')]
workbook(folders[8],'UAT签收与遗留事项',[('验收场景',['ID','需求','操作','通过条件','实际环境','包SHA','验收结论','责任人'],[[*x,'待实际记录','待锁定候选包','待执行／未签收','待指定'] for x in uat_rows]),('未决阻断',['ID','主题','事实','关闭要求','负责角色','状态'],decisions),('签收记录',['责任角色','需确认事项','结论','姓名／日期'],[['产品','范围及遗留差异','未签署','待实际填写'],['规则审阅','版次与规则冲突','未签署','待实际填写'],['QA','证据与发布门禁','未签署','待实际填写'],['用户','实际设备场景','未签署','待实际填写']])])
workbook(folders[9],'问题变更与决策台账',[('规则决策',['ID','主题','当前事实','关闭要求','负责角色','状态'],decisions),('变更控制',['变更ID','关联','变更内容','影响检查','当前结论'],[['CHG-01','REQ-001/004','内嵌index及字体回退','本地入口／打包／报表／存档','v0.6.3有历史证据'],['CHG-02','REQ-004/007/008','原骰子、金额、快车道布局与查看棋盘','原图／字段／异步刷新／输入／权限','v0.6.4有历史证据'],['CHG-03','REQ-009/018','专业文档和机器契约交付','资料准确性／文件显示／契约有效性','本次文档复核；未改变游戏逻辑']])])
# Review deck: actual state, evidence and decisions, not a fictional approval pitch.
prs=Presentation();prs.slide_width=PI(13.333);prs.slide_height=PI(7.5)
def slide(title,lines):
 sl=prs.slides.add_slide(prs.slide_layouts[6]);bg=sl.background.fill;bg.solid();bg.fore_color.rgb=PC.from_string('F5F8FB')
 sh=sl.shapes.add_textbox(PI(.55),PI(.35),PI(12.2),PI(.45));p=sh.text_frame.paragraphs[0];p.text='CASHFLOW  |  DEVELOPMENT REVIEW  |  '+BASELINE;p.font.size=PP(12);p.font.color.rgb=PC.from_string(TEAL)
 box=sl.shapes.add_textbox(PI(.6),PI(1.05),PI(12),PI(1));p=box.text_frame.paragraphs[0];p.text=title;p.font.name='Microsoft YaHei';p.font.size=PP(30);p.font.bold=True;p.font.color.rgb=PC.from_string(NAVY)
 box=sl.shapes.add_textbox(PI(.7),PI(2.05),PI(11.8),PI(4.6));tf=box.text_frame;tf.word_wrap=True
 for i,line in enumerate(lines):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='Microsoft YaHei';p.font.size=PP(21);p.font.color.rgb=PC.from_string('273E50');p.space_after=PP(20)
 foot=sl.shapes.add_textbox(PI(.6),PI(7),PI(12),PI(.3));p=foot.text_frame.paragraphs[0];p.text=f'{DATE}   待评审 · 不代填签收                                 {len(prs.slides):02d}';p.font.size=PP(10);p.font.color.rgb=PC.from_string(GRAY)
slide('研发资料与验收评审',['游戏实现基线 v0.6.4；代码236a3933ecef','本次交付原生Word／Excel／PowerPoint、PDF及机器可读契约','目的：让不同角色按同一版依据工作，并清楚区分证据与待办'])
slide('九阶段与门禁',['立项 → 需求／规则 → UX/UI → 技术契约 → 实施','测试 → 发布候选 → 用户验收 → 维护反馈','阶段文档、执行记录、评审批准和最终签收分别管理'])
slide('现有资产与证据',['12职业、182机制牌、23梦想、24／48格棋盘','已有报告：353单元测试、27套浏览器检查','这些是既有v0.6.4结果，不重标为今日重跑'])
slide('需求与规则基线',['18项带ID需求，关联实现、测试和UAT','黄金结算、版次、中文排版和多骰运行坐标仍有未决项','规则数据工作簿直接读取当前实现，保留sourceId与数值类型'])
slide('交互与视觉重点',['固定1024×768舞台；报表与卡片双层显示','中文和大额数值独立区域，避免英文定宽直接套用','交互原型、原图来源、几何、状态表和实际截图分开保存'])
slide('技术权威与契约',['engine／table共享规则；在线由Rooms校验轮序、version和权限','OpenAPI 3.1联调契约＋JSON Schema 2020-12快照契约','服务目前未挂Schema中间件；业务合法性仍需规则校验'])
slide('跨角色交接',['产品给范围与决策；策划给公式、条件与边界','设计给状态、标注与异常；前后端交换接口和恢复约定','QA拿受测包与证据；用户在真实设备确认结果'])
slide('质量与用户验收',['自动化、视觉区域、数值夹具与UAT是不同证据','真实file入口、浏览器矩阵、压测、安全和回退仍待实测','验收工作簿保持未签收，不预填“通过”'])
slide('发布与数据保护',['解压实际ZIP验证；核对提交、版本与入口／包SHA','启动检查 /healthz；持久化文件先备份再升级','单进程JSON存储不应直接当作分布式服务扩容'])
slide('当前优先级',['P0：参考版本及高影响规则决定、真实文件入口','P1：逐页对照、契约评审、迁移与回退演练','P2：兼容、容量、安全和可访问性目标及验证'])
slide('本次交付怎么使用',['先打开“开始阅读.html”按部门和阶段查找原生文件','Word/PDF用于评审；Excel用于筛选、追踪、执行与签收','SVG/HTML用于图与流程；JSON用于接口、存档和校验'])
slide('需要实际责任人决定的事项',['批准需求与比较基准，指定角色和实测设备','对未决差异作出决定或明确有条件接受','在指定候选包上执行UAT并记录通过／不通过／条件'])
prs.save(OUT/folders[0]/'研发阶段与验收评审简报.pptx')
# HTML prototype: explicitly a design artifact; no backend requests, no game settlement.
prototype='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Cashflow 交互设计原型</title><style>body{font:15px Arial,"Microsoft YaHei",sans-serif;background:#edf3f7;color:#18354b;margin:24px}button{padding:10px 18px;margin:4px;background:#087f8c;color:white;border:0;border-radius:5px;cursor:pointer}.stage{position:relative;width:1024px;height:768px;background:#d7bb8f;border:1px solid #9c8565;margin-top:20px}.board{position:absolute;left:52px;top:86px;width:922px;height:610px;border:12px solid #775478;box-sizing:border-box;background:repeating-linear-gradient(90deg,#dce5cb 0 55px,#c2d1b5 55px 62px)}.sheet{position:absolute;left:0;top:56px;width:696px;height:712px;background:#fff7e5ee;box-sizing:border-box;padding:26px}.card{position:absolute;left:656px;top:98px;width:354px;height:388px;box-sizing:border-box;padding:26px;background:#fff7e5;border-bottom:48px solid #775478;box-shadow:0 3px 6px #0004}.copy{color:#64748b}.amount{display:grid;grid-template-columns:1fr 93px;gap:12px;margin-top:38px}.col strong{display:block;font-size:14px;margin-top:6px}.bottom{position:absolute;bottom:35px;left:26px;right:65px;text-align:right;font-size:26px}.hide{display:none}.diagrams img{width:1100px;max-width:100%;background:white}small{color:#64748b}</style><h1>Cashflow｜交互与布局设计原型</h1><p>这是可点击的设计评审原型，不执行游戏结算；真实实现与证据见对应规格及截图。</p><button onclick="mode('start')">开始回合</button><button onclick="mode('trade')">股票份数</button><button onclick="mode('fast')">快车道报表</button><button onclick="mode('board')">查看棋盘</button><div class="stage"><div class="board"></div><div class="sheet hide" id="sheet"><h2 id="st">财务报表</h2><p>左列：收入／支出／资产负债</p><p>右列：目标与进度／现金摘要</p><div class="bottom">现金流日收入 $1,080,000<br>现金 $1,953,080</div></div><div class="card" id="card"><h2 id="ct">开始回合</h2><p id="body">查看财务报表后选择骰子。未确认事件不能结束回合。</p><div class="amount hide" id="qty"><div>买入份数：<input type="number" value="99999" style="width:70px"></div><div class="col">需要现金：<strong>$49,999,500</strong></div></div><p class="copy">此卡位置：x656 y98；金额列93px</p></div></div><h2>用户流程</h2><div class="diagrams"><img src="用户回合流程.svg" alt="用户流程"><h2>系统架构</h2><img src="系统架构.svg" alt="系统架构"></div><script>function mode(m){sheet.classList.toggle('hide',!['trade','fast'].includes(m));card.classList.toggle('hide',m==='board');qty.classList.toggle('hide',m!=='trade');ct.textContent=m==='trade'?'股票买入份数':m==='fast'?'快车道事件':'开始回合';st.textContent=m==='fast'?'快车道目标与收入':'收入、支出、资产与负债';body.textContent=m==='trade'?'说明与金额上下分行，金额完整处于独立列。':m==='fast'?'取消或返回不应重建旧布局。':'查看报表后选择骰子。'};</script></html>'''
(OUT/folders[3]/'交互设计原型.html').write_text(prototype)
# Reusable facts keep workbook and review text auditable.
(OUT/folders[0]/'构建事实快照.json').write_text(json.dumps({'baseline':BASELINE,'game_commit':GAME_COMMIT,'date':DATE,'counts':{k:len(D[k]) for k in ['jobs','small','big','market','doodads','dreams','fast']},'requirements':[r[0] for r in requirements],'prior_unit_count':validation['unit_tests']['passed'],'prior_browser_count':validation['browser_check_count'],'prior_test_report':'audit/validation-latest.json','research_successes':sum('已读取' in s['status'] for s in sources),'approval':'待评审／未签署'},ensure_ascii=False,indent=2))
print('Created native DOCX, XLSX, PPTX, SVG, prototype and machine contracts in',OUT)
make_doc(folders[0],'交付依据与阶段复核报告','CF-DOC-REVIEW-01','交付依据与阶段复核报告','专业交付形式、公开研究、阶段成熟度与验证边界',[
('交付形式与使用方法',[('table',['交付物性质','原生格式','主要用途'],[['受控规格与报告','DOCX + PDF','可编辑评审、版本控制、固定阅读副本'],['规则／需求／任务／测试台账','XLSX','真实数据、筛选、追踪、状态与执行记录'],['评审简报','PPTX + PDF','跨角色评审范围、风险与待决定事项'],['交互及架构','HTML + SVG','可点击的设计原型、可编辑矢量图'],['机器契约','OpenAPI JSON / JSON Schema','联调、数据结构验证与工具集成']]),'大公司并无适用于所有项目的统一Word模板。公开工程资料也经常使用Markdown；本交付按用户的阅读、部门协作与评审需要提供原生Office和PDF，保留JSON技术契约。文档深度、可追溯性和真实批准记录比扩展名更重要。']),
('公开研究与可用证据',[('table',['来源','读取范围','本次采用的原则'],[['OpenAPI官方规范3.1.0','已读取公开规范文本','接口可被人和工具理解，支持生成文档、测试及客户端'],['JSON Schema官方仓库','README说明与版本入口；主分支为后续草案工作区','使用稳定2020-12声明与本机验证器，区分结构和业务约束'],['Microsoft Xbox GDK Samples','公开README的样例、媒体、环境和版本布局迁移说明','单独管理环境／资源／实现与兼容变更，不冒充内部流程'],['Microsoft PlayFab仓库','取得的README仅为行为准则','不将其当作游戏生命周期或测试规范依据'],['W3C WCAG官方仓库','README的标准内容组织与维护说明','预留可访问性验收；没有据此宣称当前合规'],['NASA／ISO／部分Learn页面','站点访问受限，未取得内容','不引用未读取条款，不宣称标准符合性']]),'完整访问日期、URL、失败结果与短摘要位于公开研究来源.json；工作簿中的来源台账可筛选。参考公开标准不等于取得企业内部模板，也不等于项目已经认证。']),
('当前阶段复核',[('table',['阶段','当前事实','仍需完成'],[['范围与规则','历史用户目标与当前实现可定位','版次、冲突处理、批准范围与责任人'],['UX／技术契约','几何、截图及本次结构化规格已建立','逐页批准截图、OpenAPI／Schema业务评审'],['实施与质量','已有代码、353单测与27浏览器记录','真实入口、兼容、容量、安全及人工验证'],['发布与验收','已有阶段包、版本与SHA','实际部署／回退演练、用户签收'],['维护','已有版本和修复记录','实际角色任命、响应目标和持续回归']]),'本次文档复核执行文件结构、可编辑数据、契约样例、PDF输出与本地阅读入口检查。游戏原有27套浏览器报告是历史证据，本次不把它们重标为今日重跑；最终验证结果以复核结果.json为准。']),
('剩余批准与执行事项',['需求与规则评审：关闭或明确豁免DEC-01至DEC-05。实际入口：按MAN-01至MAN-04记录操作系统、浏览器、缩放及候选包SHA。技术质量：确定性能／容量／安全／可访问性目标，再执行相应测试。','最终签收：产品、规则审阅者、QA与实际用户需要分别留下结论；所有批准栏当前保持未签署。本次交付补足工作依据，不能替代缺失的原版资料和实测结果。'])])
# Detailed pending semantics and client action conventions replace generic placeholder rows.
pending_details={
'notice':('title, text','提示确认／跳过，按事件允许结束','不是任意强制事件的通用跳过'),
'choose':('title, text','选择small/big进入deal或stockSplit','当前必须为机会选择'),
'deal':('offer, title, text','buy或股票子卡；dismiss退出报价','股票与物业的确认语义不同'),
'stockTrade':('offer, mode, quantity, previous','confirmStock结算；cancelStock回previous','买入1..99999；卖出不超过持仓'),
'stockSplit':('offer.key, offer.factor','acceptSplit处理后清除pending','不允许在拆分卡交易'),
'payment':('effect, cost, sourceId, text','payEvent支付，或进入loanOffer','字段因事件不同，不全部必填'),
'doodadChoice':('cost, down, loan, payment','现金或分期，增加对应负债／月供','不足现金先进入贷款子状态'),
'market':('card, sourceId, text','匹配资产出售或跳过','只对匹配资产生成报价'),
'marketMust':('card, cost, sourceId','确认强制市场效果','不能直接dismiss'),
'baby':('atLimit, title','confirmChild，最多3个孩子','达到上限仍需确认但不加支出'),
'charity':('cost, title','捐赠或跳过，决定骰子权益','检查现金与对应阶段权益'),
'enterFast':('title, text','确认进入并按规则转换基础收入','被动收入严格超过支出'),
'fastDeal':('cost, income, rollmin, reward','购买事业；风险进入investmentRoll','事业占用与现金检查在规则层'),
'dream':('cost, title','购买自己的梦想或跳过','其他人的梦想不能直接获胜'),
'investmentRoll':('die, rollmin, paid, position, income, reward','resolveInvestment确认结果','显示本次die，不能再次扣已付投资'),
'skipTurn':('title, text','confirmSkip减少休整并推进本次确认','必须存在剩余休整'),
'insolvent':('title, text','清算／偿债直至恢复或进入后续破产分支','取消不能绕过现金危机'),
'debtHalved':('title, text','confirmRelief判断recovery或bankruptLost','减免范围按规则profile'),
'recovery':('title, text','completeRecovery清理队列并休整3回合','必须为破产恢复状态'),
'bankruptLost':('title, text','confirmBankruptLoss标记出局','清理该玩家待处理队列'),
'assetSale':('assetId, previous, gross, net, debt','确认出售；取消回previous','报价存在、资产非证券、合法市场／清算'),
'debtPicker':('previous, title, text','选择loanId；取消回previous','内圈、非破产、无其他pending'),
'debtReview':('loanId, amount, payment, previous','全额个人债务或整千银行债务确认','余额、现金、舍入和引用校验'),
'borrowReview':('amount, title, text','confirmBorrowReview或取消清除','内圈、非破产、无其他pending'),
'loanOffer':('loan, previous','acceptLoan后回原事件；取消恢复','不能因此直接确认原交易')}
from openpyxl import load_workbook
p=OUT/folders[4]/'接口指令与数据字典.xlsx';w=load_workbook(p);ws=w['Pending分支'];ws.cell(4,2,'实现使用字段（按分支核对）');ws.cell(4,3,'允许转换／业务约束')
for i,k in enumerate(kinds,5):
 fields,transition,guard=pending_details[k];ws.cell(i,2,fields);ws.cell(i,3,transition+'；'+guard);ws.row_dimensions[i].height=62
w.save(p)
# Complete the known outer player shape without claiming JSON Schema enforces monetary conservation.
p=tech/'game.schema.json';game=json.loads(p.read_text());props=game['$defs']['Player']['properties']
for key in ['dreamMultiplier','fastBase','fastGain','uid']:props[key]={'type':'number'}
for key in ['processingQueue','fastCharity','restructuring','won','bankrupt','inactive','dreamConfirmed','inBankruptcy']:props[key]={'type':'boolean'}
for key in ['charity','skip']:props[key]={'type':'integer','minimum':0}
props['color']={'type':'string'};props['cardQueue']={'type':'array','items':{'type':'object'}};props['suspended']={'$ref':'#/$defs/Pending'};props['decks']=copy.deepcopy(game['properties']['decks'])
props['fastAssets']['items']={'type':'object','required':['id','position','name','cost','income'],'properties':{'id':number,'position':{'type':'integer','minimum':0,'maximum':47},'name':string,'cost':number,'income':number},'additionalProperties':True}
p.write_text(json.dumps(game,ensure_ascii=False,indent=2))
oas['components']['schemas']['Game']=rew({k:v for k,v in game.items() if k!='$id'})
oas['info']['description']+=' 契约描述受支持的客户端载荷；服务端部分字段另有截断／回退处理，不声称已用Schema中间件实施所有约束。'
(tech/'openapi.json').write_text(json.dumps(oas,ensure_ascii=False,indent=2))
# Quantity overview uses real spreadsheet formulas, with source counts kept separately.
p=OUT/folders[2]/'需求规则与数值主表.xlsx';w=load_workbook(p);ws=w['数量复核'];ws.cell(4,4,'工作簿条数公式');ws.cell(4,5,'比对结果')
for row,key,title in [(i,k,t) for i,(k,t) in enumerate([('jobs','职业数据'),('small','小买卖'),('big','大买卖'),('market','市场'),('doodads','额外支出'),('dreams','梦想'),('fast','快车道')],5)]:
 ws.cell(row,4,f"=COUNTA('{title}'!A5:A1000)");ws.cell(row,5,f'=IF(B{row}=D{row},"PASS","CHECK")')
ws.column_dimensions['D'].width=24;ws.column_dimensions['E'].width=18
for c in ws[4]:c.fill=PatternFill('solid',fgColor=NAVY);c.font=Font(name='Microsoft YaHei',bold=True,color='FFFFFF')
for t in ws.tables.values():t.ref='A4:E11'
ws.auto_filter.ref='A4:E11';w.save(p)
# Source file fingerprints identify the implementation used for document review.
source_files=['engine.js','table.js','reference-data.js','scripts/rooms.cjs','scripts/serve.cjs','online.js','local-rooms.js','interaction.js','classic-stage.js','scene-canvas.js','scripts/build-preview.py','package.json']
(OUT/folders[0]/'源码复核指纹.json').write_text(json.dumps({'date':DATE,'game_baseline':GAME_COMMIT,'files':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_files}},indent=2))
