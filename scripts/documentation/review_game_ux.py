from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
import re,json
R=Path(__file__).resolve().parents[2]; P=R/'docs/professional-delivery'; O=P/'10-专家审核与修订'; O.mkdir(exist_ok=True)

# Remove only this script's previous controlled amendment for idempotent rebuilds.
for rel in ['02-需求与游戏规则/PRD产品需求规格.docx','02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx']:
 f=P/rel; prior=Document(f); removing=False
 for para in list(prior.paragraphs):
  if para.text.startswith('2026-11-02 专项审核修订（受控补充）'): removing=True
  if removing: para._element.getparent().remove(para._element)
 prior.save(f)

states=[
('choose','机会格','deal(s,size)','deal / stockSplit','dismiss可放弃','不抽取两次；牌堆仅权威层'),
('deal','抽出投资牌或共享证券报价','buy / openStock / dismiss','完成或stockTrade / loanOffer','原报价','queued且非anyoneBuy只许卖出'),
('stockTrade','openStock','stockQuantity / confirmStock / cancelStock','完成 / loanOffer / previous','回原deal','1..99999整数；卖出≤持仓'),
('stockSplit','拆股事件或队列','acceptSplit','下一队列或回合','不可跳过','合股向下取整；总成本按剩余数量同比'),
('market','可选资产收购','openAssetSale / sell / dismiss','assetSale或结束','原市场卡','匹配key及units；出售净额扣债'),
('marketMust','强制市场效果','payEvent','效果完成 / loanOffer','不可跳过','费用／失去资产／创业改善／强制收购分别验证'),
('payment','失业/支出/税/离婚/诉讼','payEvent','完成 / loanOffer','不可跳过','现金不足先贷款；确认一次结算'),
('doodadChoice','带分期支出','payDoodad(finance)','完成 / loanOffer','不可跳过','全款与首付、负债、月供分开'),
('baby','添丁格','confirmChild','完成','不可跳过','最多3名；上限事件仍确认'),
('charity','慈善格','donate / dismiss','完成','可拒绝','内圈3次资格；快车道固定费用'),
('loanOffer','付款现金不足','acceptLoan / cancelLoan','previous','回previous','按千向上取整；证券贷款返回份数重置1'),
('borrowReview','空闲内圈借款','confirmBorrowReview / cancelBorrowReview','完成 / 原表单报错','空闲回合','正整千；单次≤9999000；破产禁止'),
('debtPicker','空闲内圈还款','openDebtReview / cancelDebtPicker','debtReview / previous','空闲回合','仅可选有效负债'),
('debtReview','选择负债','confirmDebtReview / cancelDebtReview','完成 / previous','恢复previous','银行按千；其他债务全清'),
('assetSale','选中可售资产','confirmAssetSale / cancelAssetSale','完成 / previous','回报价/破产卡','按assetId结算并移除对应资产'),
('insolvent','现金危机或重整','借款/清算/偿债/债务减免','原事件 / recovery / debtHalved','不可跳过','普通危机与inBankruptcy权限不同'),
('debtHalved','破产减免完成','confirmRelief','recovery / bankruptLost','不可跳过','车/信用卡/零售余额和月供减半'),
('recovery','破产现金流恢复正','completeRecovery','休整3回合','不可跳过','清空队列、重整标记'),
('bankruptLost','重整失败','confirmBankruptLoss','bankrupt终局','不可跳过','不再允许交易或掷骰'),
('enterFast','被动收入严格大于支出','enterFast','快车道并交棒','不可跳过','现金替换P×100；pos42；DEC09未决'),
('fastDeal','快车道事业格','buy / dismiss','完成 / investmentRoll','可放弃','已被他人买走不可再买；风险先扣投入'),
('investmentRoll','风险投资已扣款','resolveInvestment','完成','不可跳过','die≥rollmin；只按已存骰结算一次'),
('dream','自己梦想位置','buy / dismiss','won / 完成','可放弃','梦想成本乘dreamMultiplier'),
('notice','无交易通知','dismiss','完成','确认关闭','不重复执行已完成效果'),
('skipTurn','table.advanceQueue休整','confirmSkip','自动交棒','不可跳过','减skip并增turn；休整不处理共享队列'),
]
issues=[
('GX-01','P1','GDD决策表只列DEC01—05，规则工作簿已列9项','GDD表格与规则决策页逐项对照','同步9项到GDD并注明受控源','文档已修订；规则批准未完成'),
('GX-02','P1','14个UI分组未展开25种pending，研发缺少子状态退出规则','engine.js/table.js kind赋值与dismiss禁止列表','新增25行状态/动作/取消/数据约束矩阵并在UX引用','文档已修订；全状态运行测试待执行'),
('GX-03','P1','骰子原版多页面、多骰运行证据未齐','UX单骰几何与DEC05','建立原版截图与候选图成对采集验收矩阵','验收方法已补；原版证据未齐'),
('GX-04','P1','数值上限和视口覆盖缺乏逐项判定模板','PRD REQ004/014，CSS93px列','新增边界与几何测量规范及记录字段','文档已修订；真实file设备待实测'),
('GX-05','P1','现有快车道发薪与报表口径差异待裁决','engine.js:19；classic-stage.js:34','DEC09同步规格并保留原版观察门禁','登记完成；产品/规则裁决待办'),
('GX-06','P2','原版一致性目标缺少逐页可交付判定记录','REQ010及DEC01/03','新增覆盖证据、视觉与行为独立门禁','规格已补；原版全等仍阻断'),
]
bounds=[
('NUM01','股票份数','空白、0、1、99999、100000、小数、科学计数法','明确区分输入草稿与提交整数；提交非法不得结算','stockQuantity/confirmStock；REQ011'),
('NUM02','股票金额','price500×99999=49999500；0持仓卖出','金额完整落入93px列，无截断、无邻框覆盖','classic-stage.css:294-296；REQ004'),
('NUM03','快车道收入','0、50000阈值、1000000以上；长中文资产名','标签/金额不重叠；资产行溢出有明确展示策略','classic-stage.js:34/fitAmounts；REQ004/012'),
('NUM04','借还','999/1000/1001；9999000/10000000；现金不足','按千与上限；现金/负债/月供同步；取消不改账','engine.borrow/repay；REQ002/011'),
('NUM05','进入快车道','被动收入=支出及>支出','相等不进入；确认后现金替换与原版裁决分开','engine.check/enterFast；DEC09'),
('NUM06','孩子与分期','0/1/3孩子；按孩子计费与无孩免付','3名上限，分期首付/负债/月供仅计一次','engine.doodad/confirmChild'),
('NUM07','拆股','1/2/3份×0.5；不同成本多批次','合股取整，零持仓移除，成本调整口径记录','engine.splitShares/confirmStock'),
('NUM08','风险投资','rollmin-1 / rollmin；刷新结果卡','投入已扣，刷新不重掷，不重复收益','engine.resolveInvestment'),
]
visual=[
('VIS01','内圈空闲','单骰1—6点，纸张开/关','官方运行截图+版本+视口+时间；候选同状态','单骰64×59；锚点483.3/436.2为当前模板，原版运行需确认'),
('VIS02','慈善选骰','内圈1/2骰；快车道1/2/3骰','每个骰数、每个页面分别采集','不能以单骰模板代替多骰实际位置'),
('VIS03','投资检定','成功/失败结果卡+报告开关','结果die与当前检定一致','资产骰图集、尺寸、层级、点击命中区分别比对'),
('VIS04','财务报表','内圈/快车道；高金额；多资产','完整截图+字段裁剪+DOM/Canvas边界测量','固定舞台1024×768；总布局与局部文字独立检查'),
('VIS05','右上卡片与棋盘','卡片打开、B查看、Esc返回','输入草稿含空白；交互录像及state摘要','查看不结算，纸张全收起，返回草稿一致'),
('VIS06','本地与在线入口','Windows Chrome/Edge；100/125/150%缩放','包SHA、系统/字体、DPR、浏览器版、入口绝对路径','实际file入口人工执行；不以HTTP路由替代'),
]

def table(doc,heads,rows):
 t=doc.add_table(rows=1, cols=len(heads)); t.style='Light Shading Accent 1'
 for c,h in zip(t.rows[0].cells,heads):c.text=str(h)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 return t

def newdoc(title,id):
 d=Document();sec=d.sections[0];sec.header.paragraphs[0].text='CASHFLOW | 受控研发文档 · 专项审核'
 normal=d.styles['Normal'];normal.font.name='Noto Sans CJK SC';normal.font.size=Pt(10);normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
 d.add_heading(title,0)
 table(d,['受控项','内容'], [('编号',id),('日期','2026-11-02'),('范围','v0.6.4 / 236a3933ecef；文档基线2026-10-27'),('审查性质','AI领域专项审查；不是外聘真人专家签名或大公司认证'),('批准','待产品/策划/设计/QA责任人评审；不得自动签收')])
 return d

d=newdoc('玩法与体验专家审核','CF-REV-GX-02')
d.add_heading('审核结论',1);d.add_paragraph('现有需求、数值数据和UI规格具备可追溯基线，但不能判为全部覆盖或与原版完全相同。本轮修订关闭的是文档表达与追踪缺口；外部原版观察、设备测试和规则裁决仍是独立门禁。文件格式专业不等同于内容已批准。')
d.add_heading('审查方法与证据',1);table(d,['维度','执行','边界'], [('玩法','阅读GDD、PRD及engine.js/table.js全部状态与金融函数','静态复核，不声称本轮重跑游戏'),('数值','读取规则工作簿页签及数量；确认9项决策与GDD差异','数据源本身未完整获官方版次核验'),('体验','读取UX与classic-stage.js/css及页面状态表','无新增官网登录、截图或真人可用性试验')])
d.add_heading('问题、处置与关闭范围',1);table(d,['ID','等级','问题','证据','整改','关闭范围'],issues)
d.add_heading('交付前门禁',1);table(d,['门禁','通过条件','当前'], [('文档开发依据','25种pending逐行有进入、动作、退出及取消规则；PRD/GDD/UX指向同一专项附件','本轮补充，可进入责任人评审'),('原版等价','明确版本/语言后逐页逐状态提供官方证据与差异裁决','未通过；不得声称完全一样'),('视觉交互','按VIS01—06测量，记录视口、DPR、字体及包SHA','方法补全；运行证据待补'),('用户签收','真实file入口、在线入口及终局用户实测','未签收')])
d.add_heading('附件与修订',1);d.add_paragraph('《玩法交互专项规格补充.docx》《玩法交互覆盖与验收矩阵.xlsx》为本轮受控设计依据；既有PRD、GDD、UX已增加受控引用，GDD同步完整9项规则决策。工作簿标为设计用例，不冒充执行结果。')
d.save(O/'玩法与体验专家审核.docx')

d=newdoc('玩法交互专项规格补充','CF-GX-SPEC-02')
d.add_heading('执行优先级与范围',1);d.add_paragraph('本规格补充既有PRD/GDD/UX，不改变现有游戏代码。玩法以所选profile为准；原版目标以DEC01确定的版本为准。冲突进入规则决策台账，不由前端排版或自动测试擅自决定。游戏状态、页面状态、权限状态必须分别描述。')
table(d,['层','权威字段','实现规则'], [('游戏','player.pending / game.active/rolled/ui','引擎和table决定结算，画面仅发动作'),('表现','报表/卡片/聊天/棋盘查看、输入草稿','查看或动画不创建交易；恢复不复用过期决策'),('权限','当前玩家、旁观、重连','线上服务校验；控件隐藏不能替代鉴权')])
d.add_heading('全量事件状态契约',1);d.add_paragraph('下列25种为engine/table直接创建的pending状态；split、stockQuote是共享事件类型，市场报价等是quote分类，不是pending页面，避免将其误算成新界面。空pending、梦想介绍、终局与断线另由UI/权限层处理。')
table(d,['pending','进入','动作','后继','取消','约束'],states)
d.add_heading('金融与输入边界',1);table(d,['ID','对象','边界','预期','依据'],bounds)
d.add_heading('原版视觉与交互验收规范',1);d.add_paragraph('严格式像素目标须先锁定相同语言、字体、操作系统、浏览器、视口和缩放。中文与英文不同长度不能在未批准语言基线时直接承诺像素完全相同。模板坐标属于当前实现，只有成对运行证据才能关闭等价问题。')
table(d,['ID','页面','组合','证据','判定'],visual)
d.add_paragraph('测量记录字段：caseId、sourceVersion、sourceURL、captureTime、packageSHA、codeCommit、os、browser、viewport、DPR、zoom、font、gameStage、pendingKind、diceCount、paperState、referenceImageSHA、candidateImageSHA、geometryJSON、actionSequence、beforeAfterState摘要、diff解释、结论、责任人。像素差异阈值须经设计批准，当前不编造统一通过百分比。')
d.add_heading('关闭与变更',1);d.add_paragraph('不得将设计用例改写成已执行。未获得官方状态或设备不能关闭原版一致性项。若调整布局、骰子或报表，重测相关VIS项、NUM项与既有display/attachment回归；若更改金融语义，同时更新GDD、数值样例、规则夹具、存档兼容说明和用户可见报表。')
d.save(O/'玩法交互专项规格补充.docx')

w=Workbook();w.remove(w.active)
def sheet(name,heads,rows):
 s=w.create_sheet(name);s.append(heads)
 for r in rows:s.append(list(r))
 s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
 for c in s[1]:c.font=Font(name='Microsoft YaHei',bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='17365D')
 for row in s.iter_rows(min_row=2):
  for c in row:c.font=Font(name='Microsoft YaHei',size=10);c.alignment=Alignment(vertical='top',wrap_text=True)
 for col in s.columns:s.column_dimensions[col[0].column_letter].width=25 if col[0].column<3 else 48
 for n in range(2,s.max_row+1):s.row_dimensions[n].height=64
sheet('阅读控制',['项目','值'], [('版本','2026-11-02 / CF-GX-MAT-02'),('基线','v0.6.4 / 236a3933ecef'),('范围','AI静态领域审核；设计矩阵，不代表运行通过'),('状态数',len(states)),('实施权限','依据规格执行；原版及用户验收未关闭')])
sheet('状态转换契约',['pending','进入','允许动作','后继','取消','约束'],states)
sheet('边界验收设计',['ID','对象','边界','预期','依据','执行状态'],[(*r,'未执行（本轮仅设计复核）') for r in bounds])
sheet('原版视觉证据矩阵',['ID','页面','组合','证据要求','判定依据','状态'],[(*r,'待采集/待批准') for r in visual])
sheet('审核问题闭环',['ID','等级','问题','证据','整改','关闭范围'],issues)
sheet('状态外覆盖',['对象','条件','动作与预期','证据状态'], [('梦想介绍','game.ui且本座位首次回合','chooseDream后方可roll','规格依据table.js:12-14；运行待复核'),('空闲','pending空、无介绍、未rolled','借/还/慈善骰数/roll','需按内外圈及权限组合验证'),('终局','won/bankrupt/game.over','禁金融及掷骰；允许退出和只读报表','终局用例引用既有自动化证据，未新增执行'),('查看棋盘','有卡片及可编辑草稿','B/Esc恢复；R/E禁推进；新决策退出查看','VIS05'),('断线/旁观','非当前玩家或服务不可用','恢复权威状态前禁动作；不获得他人权限','UI14/REQ005/006')])
w.save(O/'玩法交互覆盖与验收矩阵.xlsx')
# Update original controlled specs, no formula workbook mutation.
for name in ['02-需求与游戏规则/PRD产品需求规格.docx','02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx']:
 f=P/name;d=Document(f)
 if 'GDD' in name:
  sw=load_workbook(P/'02-需求与游戏规则/需求规则与数值主表.xlsx',data_only=True)['规则决策']
  decisions=[]
  for r in sw.iter_rows(values_only=True):
   if r[0] and re.match(r'DEC-\d+',str(r[0])): decisions.append([str(x or '') for x in r[:6]])
  for t in d.tables:
   if t.rows[0].cells[0].text=='决策':
    for row in list(t.rows)[1:]:t._tbl.remove(row._tr)
    for r in decisions:
     cells=t.add_row().cells
     cells[0].text=r[0];cells[1].text=' | '.join(r[1:3]);cells[2].text=r[3];cells[3].text=' | '.join(r[4:])
  print('synced',len(decisions),'decisions')
 d.add_heading('2026-11-02 专项审核修订（受控补充）',1)
 d.add_paragraph('本文件与 ../10-专家审核与修订/玩法交互专项规格补充.docx、玩法交互覆盖与验收矩阵.xlsx 联合使用。CF-GX-SPEC-02展开25种pending转换、8组数值边界、6组视觉/原版证据矩阵；不是已执行测试或已批准原版等价结论。')
 d.add_paragraph('优先级：本文件保留产品目标及现行实现基线；专项补充提供开发/验收细节。出现规则冲突先登记DEC并由产品/规则责任人裁决。GX01—06整改记录见玩法与体验专家审核。文档版本1.1，批准状态仍待签署。')
 d.save(f)
print('created', [x.name for x in O.glob('*玩法*')])

from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import load_workbook
import json
P=Path(__file__).resolve().parents[2]/'docs/professional-delivery';O=P/'10-专家审核与修订'
newissue=['GX-07','P1','证券买入存在两种数量上限','engine.js buy允许1..1000000，confirmStock/stockQuantity为1..99999','规格区分引擎直接buy与参考表单提交，并登记统一契约裁决','文档口径已澄清；规则/API裁决待执行']
w=load_workbook(O/'玩法交互覆盖与验收矩阵.xlsx');w['审核问题闭环'].append(newissue);w['边界验收设计'].append(['NUM09','证券双路径','直接buy 99999/100000/1000000/1000001；confirmStock 99999/100000','当前引擎与表单上限不同；先记录真实接受/拒绝，再经规则/接口裁决统一目标','engine.buy/confirmStock','未执行；静态确认差异']);w.save(O/'玩法交互覆盖与验收矩阵.xlsx')
for f in [O/'玩法与体验专家审核.docx',O/'玩法交互专项规格补充.docx']:
 d=Document(f)
 if '专家审核' in f.name:
  for t in d.tables:
   if t.rows[0].cells[0].text=='ID':
    for c,v in zip(t.add_row().cells,newissue):c.text=v
 else:
  d.add_heading('证券数量双路径差异（GX-07）',1);d.add_paragraph('参考表单stockQuantity/confirmStock限定99,999份；engine.buy接受上限1,000,000份。两者不可写成统一已执行上限。直接buy与confirmStock须分别验证，并由规则/接口责任人裁决一致性目标；本轮仅澄清文档，不改变实现，也不擅自认定哪项为原版正确规则。')
 for sec in d.sections:
  sec.orientation=WD_ORIENT.LANDSCAPE;sec.page_width=Inches(11.7);sec.page_height=Inches(8.3);sec.left_margin=Inches(.55);sec.right_margin=Inches(.55)
 for sty in ['Title','Heading 1','Heading 2']:
  d.styles[sty].font.color.rgb=RGBColor(0,0,0);d.styles[sty].font.name='Noto Sans CJK SC';d.styles[sty]._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
 for t in d.tables:
  t.autofit=False
  for row in t.rows:
   trPr=row._tr.get_or_add_trPr();e=OxmlElement('w:cantSplit');trPr.append(e)
   for c in row.cells:
    c.width=Inches(10.6/len(row.cells))
    for p in c.paragraphs:
     for r in p.runs:r.font.size=Pt(9)
  t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 d.save(f)
# Clarify PRD contract without changing its formulas elsewhere.
f=P/'02-需求与游戏规则/PRD产品需求规格.docx';d=Document(f);d.add_paragraph('GX-07边界澄清：REQ004的99,999份是参考UI表单上限。engine.buy直接调用另允许1,000,000份，见专项规格NUM09。统一规则及API边界待责任人裁决，不将UI限制当作已验证的全层保护。');d.save(f)
# Machine-readable independent findings.
a=Document(O/'玩法与体验专家审核.docx');findings=[]
for t in a.tables:
 if t.rows[0].cells[0].text=='ID':
  for row in t.rows[1:]:
   r=[c.text for c in row.cells];findings.append(dict(id=r[0],severity=r[1],problem=r[2],evidence=r[3],fix=r[4],doc_status='已修订待责任人评审',execution_status=r[5],files=['02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx','10-专家审核与修订/玩法交互专项规格补充.docx','10-专家审核与修订/玩法交互覆盖与验收矩阵.xlsx']))
(O/'玩法体验审核问题.json').write_text(json.dumps(dict(date='2026-11-02',reviewer='AI玩法与交互领域静态审查',baseline='v0.6.4 / 236a3933ecef',findings=findings),ensure_ascii=False,indent=2))
print(len(findings),'findings')

for rel in ['02-需求与游戏规则/PRD产品需求规格.docx','02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx']:
 f=P/rel;d=Document(f)
 for para in d.paragraphs:
  if 'GX01—06' in para.text: para.text=para.text.replace('GX01—06','GX-01—GX-07')
 d.save(f)
w=load_workbook(O/'玩法交互覆盖与验收矩阵.xlsx')
for s in w:
 s.auto_filter.ref=s.dimensions
 for row in s.iter_rows(min_row=2):
  s.row_dimensions[row[0].row].height=75
  for c in row:
   c.font=__import__('openpyxl').styles.Font(name='Microsoft YaHei',size=10)
   c.alignment=__import__('openpyxl').styles.Alignment(vertical='top',wrap_text=True)
w.save(O/'玩法交互覆盖与验收矩阵.xlsx')
coverage=dict(date='2026-11-02',method='静态源码与原生文档结构复核；非游戏运行测试',pending_expected=25,pending_documented=len(states),pending_missing=[],gdd_decisions=9,case_design_count=9,visual_groups=6,game_source_modified=False,passed=len(states)==25)
(O/'玩法体验覆盖复核.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))

# Set table grid, column and cell widths together; cell widths alone leave a narrow grid.
from docx.shared import Inches
for f in [O/'玩法与体验专家审核.docx',O/'玩法交互专项规格补充.docx']:
 d=Document(f)
 for t in d.tables:
  t.autofit=False;n=len(t.columns)
  for c in t.columns:c.width=Inches(10.6/n)
  for row in t.rows:
   for c in row.cells:c.width=Inches(10.6/n)
 d.save(f)

from docx.oxml import OxmlElement
for rel in ['02-需求与游戏规则/PRD产品需求规格.docx','02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx']:
 f=P/rel;d=Document(f)
 for a in d.paragraphs:
  if '8组数值边界' in a.text:a.text=a.text.replace('8组数值边界','9组数值边界')
  if a.text.startswith('2026-11-02 专项审核修订'):a.paragraph_format.page_break_before=True
 for t in d.tables:
  for r in t.rows:
   pr=r._tr.get_or_add_trPr()
   if pr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cantSplit') is None:pr.append(OxmlElement('w:cantSplit'))
 d.save(f)
