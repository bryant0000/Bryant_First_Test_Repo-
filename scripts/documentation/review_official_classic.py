"""Apply the user-confirmed sole official-web target to controlled native documents."""
from pathlib import Path
import json,hashlib,subprocess
from collections import Counter
from docx import Document
from docx.shared import Pt
from openpyxl import Workbook,load_workbook
from copy import copy
from integrate_expert_review import style_doc,table,sheet
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/professional-delivery';NEW=OUT/'12-官网唯一目标复核';NEW.mkdir(exist_ok=True)
target=json.loads((ROOT/'audit/official-classic-target.json').read_text());receipts=json.loads((ROOT/'audit/review-official-classic-2026-11-04/source-receipts.json').read_text())
issues=[
 ['REV-01','目标范围混合','旧release gate将实体规则书/B站完整阅读作为主要阻断；主目标已由用户明确为官网经典版','已修订','唯一primary_origin固定官网；只有指定辅助条目可非阻断；官网内容/页面/交互要求不降级','scripts/check-release.cjs；scripts/reference-acceptance.cjs'],
 ['REV-02','原版事实与候选通过混淆','旧门禁接受unit_verified且无逐项来源/设计/候选证据链','已修订','335项逐项要求原版证据、独立预期、设计锚点、代码指纹与对应比较记录','audit/official-classic-target.json；reference-acceptance.test.cjs'],
 ['REV-03','原版当前快照缺失','草稿已包含官网域名，运行代理在普通及授权通道仍CONNECT403','外部阻断','需运行环境能通过受支持代理访问已授权官网；不是重复添加域名或索取账号','audit/review-official-classic-2026-11-04/network-diagnosis.json'],
 ['REV-04','职业自选争议未闭环','候选随机分配，历史pickCareer线索随机；官网当前JS与实际操作尚未取得','待官网核验','在官网定位分配/可否自选/可否重抽及触发时机；没有证据不添自选控件','rule:random_career_with_replacement；screen:DreamSelectCard'],
 ['REV-05','中文与官网历史英文存在差异','官网历史英文资料与当前中文展示不等同','待官网核验','对照语言必须明确并相同；不能用翻译义近认定像素/文案一致','audit/official-classic-target.json language_review'],
 ['REV-06','静态源资料不等于运行画面','15份固定镜像资料中9份历史官网同哈希，另6份仅镜像；49页未封板','已区分证据等级，实施待核验','镜像数字/模板只能支撑对应功能事实，不替代官网运行控件、状态和截图','audit/review-official-classic-2026-11-04/source-receipts.json'],
 ['REV-07','缺完整目标目录与验收关联','角色、卡牌、外圈格、规则和页面原先分散登记，缺一套机器核对的必选ID','已建立目录；335项均待封板','缺目标、错来源、旧代码、错测试、视口/语言不同均保持阻断','scripts/reference-acceptance.cjs requiredTargets'],
 ['REV-08','正式放行与产品完成不能代填','当前原版全等目标未实现，用户签收未完成','继续阻断','不得生成完整等同版本声明；本轮验收工具改进不冒充UI/玩法已还原','audit/reference-coverage.json release_allowed=false']]
issues.extend([['REV-09','标题提示偏差','历史官网截图为英文，候选为中文且DOM基线存在偏移','局部修复并核验','恢复原文并按原始画布几何定位；历史提示区域最大通道误差1，非全屏验收','classic-stage.js；scene-canvas.js；title-target-fixture.json'],['REV-10','版本标识过期','v0.6.5仍硬编码v0.6.4','已修复','读取index构建meta；离线构建检查与package版本一致','index.html；classic-stage.js；scripts/build-offline.py']])

# Existing controlling specs receive a visible revision and concrete department requirements.
changes={
'01-立项与治理/项目章程与治理.docx':'治理范围：官网经典版为唯一规范来源；其他站点、实体卡牌和视频仅为辅助。需要取得原版版本快照后才能冻结逐项目标，任何不明行为登记未知。正式门禁不再要求先完成与官网目标无关的实体版等同。',
'02-需求与游戏规则/PRD产品需求规格.docx':'需求先写官网预期及来源，再写候选差距。职业是否可自选、何时分配、能否重抽以官网当前流程证据确定；当前随机分配及其单元通过不能证明官网如此。335项明细是核验目录，不表示335项已明确或通过。',
'02-需求与游戏规则/GDD玩法与数值设计.docx':'规则、职业、182卡与48外圈格逐项关联原版事实。既有44条规则是历史锚点，不作为本轮已核实的完整目标。静态机械字段与卡面文案/美术/交易后果分开；官网观察与实体卡面不一致时不混拼。',
'03-交互与视觉设计/交互与视觉设计规格.docx':'49类页面需要入口、前置、可见控件、动作、取消/恢复及结果。原版与候选同视口、DPR、缩放、语言并保存原图与候选图；模板坐标不能代替运行截图。未取得职业选择控件证据前不得添加为原版交互。',
'06-测试与质量保证/测试设计与质量报告.docx':'运行npm test验证候选规则，npm run test:acceptance验证证据门禁，再运行release:check。358单测与12门禁测试本轮通过，原版门禁按预期阻断；本轮执行既有29套与新增2套标题浏览器组，实际结果以validation-latest.json为准。335项未形成原版闭环不能算功能失败率或已完成率。',
'08-用户验收/UAT与最终验收方案.docx':'验收仅对官网经典版，不将辅助来源当成额外主目标。逐项原版证据、设计锚点、代码与比较链必须齐全，正式release_allowed仍为false。真实file入口、官网交互/显示及用户签收未完成；不得把测试工具通过签成产品通过。'}
for rel,note in changes.items():
 p=OUT/rel;d=Document(p)
 if not any(x.text=='官网唯一目标复核修订 1.3' for x in d.paragraphs):
  d.add_heading('官网唯一目标复核修订 1.3',1)
  d.add_paragraph('2026-11-04。用户已确定唯一主目标为https://cfclassic.richdad.com/官网经典版；中文站、实体卡牌和视频均为辅助。本节优先解释目标范围，历史测试与资料日期保持其原始范围。')
  d.add_paragraph(note)
  table(d,['交接依据','当前状态'],[['原版目标目录','audit/official-classic-target.json：44规则、49页面、12职业、182卡、48外圈格；335项待逐项封板'],['验收实现','scripts/reference-acceptance.cjs：验证原版/设计/代码/候选/比较链；不自动证明证据真实性，需人工审阅来源'],['本轮结论','官网连接在代理阶段拒绝；不能完成新实玩；仅凭独立历史截图修复标题提示，原版等同尚未实现']],[1.5,5.2])
 if rel.startswith('03-') and not any(x.text=='标题提示局部目标 UX-TITLE-01' for x in d.paragraphs):
  d.add_heading('标题提示局部目标 UX-TITLE-01',2)
  d.add_paragraph('依据历史官网title.png，SHA256 239c27af3d3a6ef0e5c4f59f98aa885219f7d46dd5cb5ee734431e894ce71acd；截图可见版本1.0.0(0.0.8)，当前官网版本未知。显示Click Anywhere to Continue，黑色、Helvetica粗体26；原始画布x630.4/y727.45/w390.95/h34，水平居中，顶部文字基线。native画布绘制，DOM仅保留回退与辅助入口。点击标题任意位置进入房间列表。')
  d.add_paragraph('验收：1280×960、DPR1，比较视口x756/y750/w388/h43全部像素，最大通道差≤1，不屏蔽文字；版本号另验为自身构建0.6.6。此局部符合历史截图不能关闭整个TitleScreen或当前官网验收。')
 for row in d.tables[0].rows:
  if row.cells[0].text=='实现基线':row.cells[1].text='游戏v0.6.6；文档修订1.3；唯一官网目标已确定，当前快照待采集'
  if row.cells[0].text=='编制与复核日期':row.cells[1].text='2026-11-04（保留历史资料/测试原日期）'
 for para in d.paragraphs:
  if para.text.startswith('蓝色章节对应开发依据'):
   para.text='文档修订1.3以官网经典版为唯一目标。本轮新增目标与验收要求见末节及12目录；前文候选实现和历史测试不作为官网当前行为或完整一致性证明。'
 for t in d.tables:
  for row in t.rows:
   if row.cells[0].text=='DEC-01':
    for c,v in zip(row.cells,['DEC-01','唯一官网目标已确定；官网当前版本与状态快照待采集','以官网实际规则、页面与操作为准；其他来源只辅助','主目标已确认；原版快照待核验']):c.text=v
    for c in row.cells:
     for para in c.paragraphs:
      for run in para.runs:run.font.size=Pt(9)
 for para in d.paragraphs:
  if para.text=='官网唯一目标复核修订 1.3':para.paragraph_format.page_break_before=True
  if para.text.startswith('实现基线为 v0.6.4；'):para.text='原始实现基线为v0.6.4，本轮游戏v0.6.6。唯一对照官网经典版；实体卡牌和其他网站只辅助，历史资料按来源和日期保留。'
  if para.text.startswith('最近已有 v0.6.4 报告记录'):para.text=para.text.replace('最近已有 v0.6.4 报告记录','初版历史记录：v0.6.4报告包含')
 for sec in d.sections:
  for para in sec.footer.paragraphs:
   for run in para.runs:run.text=run.text.replace('v0.6.4','v0.6.6').replace('待评审基线','文档修订1.3').replace('2026-10-27','2026-11-04').replace('2026-11-02','2026-11-04')
 
 for para in d.paragraphs:
  updated=para.text.replace('游戏v0.6.5','游戏v0.6.6').replace('本轮游戏v0.6.5','本轮游戏v0.6.6').replace('本轮未重跑29套v0.6.5浏览器组','本轮执行29套既有及2套标题浏览器组，实际结果见validation-latest.json')
  if updated!=para.text:para.text=updated
  if '官网连接在代理阶段拒绝；不能完成新实玩或据此修改' in para.text:para.text='官网连接在代理阶段拒绝；标题局部按历史官网截图修复，其他完整原版对照仍未闭环。'
 for t in d.tables:
  for row in t.rows:
   for c in row.cells:
    for para in c.paragraphs:
     if '游戏v0.6.5' in para.text:para.text=para.text.replace('游戏v0.6.5','游戏v0.6.6')
 for sec in d.sections:
  for para in sec.footer.paragraphs:
   for run in para.runs:run.text=run.text.replace('v0.6.5','v0.6.6')
 d.save(p)

for rel in ['02-需求与游戏规则/需求规则与数值主表.xlsx','09-维护与变更/问题变更与决策台账.xlsx','08-用户验收/UAT签收与遗留事项.xlsx']:
 p=OUT/rel;w=load_workbook(p)
 for ws in w:
  for row in ws:
   if row[0].value=='DEC-01':
    row[2].value='唯一目标cfclassic.richdad.com官网经典版已由用户确认；当前版本快照未取得'
    row[3].value='采集官网原版规则/职业/页面/交互证据；实体和中文站仅辅助'
    if len(row)>5:row[5].value='目标已确认；快照及逐项证据待核验'
 w.save(p)
# Correct the previously open choice, without asserting that career selection is now known.
p=ROOT/'docs/original-target-baseline/原版目标识别与职业流程核验.docx';d=Document(p)
for t in d.tables:
 for row in t.rows:
  for c in row.cells:
   for para in c.paragraphs:
    if '主目标确认仍待用户回应' in para.text:para.text=para.text.replace('暂按此前官网经典网页版；中文站和实体101分别留证，主目标确认仍待用户回应','唯一主目标已确认为官网经典版；中文站和实体仅辅助。官网当前版本快照待采集')
for para in d.paragraphs:
 if '需定位用户所指可选职业的版次/页面' in para.text:para.text=para.text.replace('需定位用户所指可选职业的版次/页面','需在已确定的官网经典版核实职业分配和可否自选的实际页面')
for para in list(d.paragraphs):
 if para.text.startswith('尚未解决最终原版等同目标。'):para._p.getparent().remove(para._p)
d.save(p)
p=ROOT/'scripts/documentation/build_original_target.py';s=p.read_text().replace('主对照暂按此前官网经典版；可选职业页面待用户定位','唯一主对照官网经典版已确认；职业交互待原站核验').replace('暂按此前官网经典网页版；中文站和实体101分别留证，主目标确认仍待用户回应','唯一主目标已确认为官网经典版；中文站和实体仅辅助。官网当前版本快照待采集').replace('需定位用户所指可选职业的版次/页面','需在已确定的官网经典版核实职业分配和可否自选的实际页面');p.write_text(s)
p=ROOT/'docs/original-target-baseline/原版目标与实现追溯.xlsx';w=load_workbook(p)
for row in w['目标与证据门禁']:
 if row[0].value=='BASE-01':row[3].value='唯一主目标官网经典版已确认；原站职业流程仍待核实'
w.save(p)

w=Workbook();w.remove(w.active)
sheet(w,'复核发现与整改',['ID','领域','复核发现','状态','整改/下一步','代码或资料'],issues)
def expected_summary(i):
 e=i['expected']
 if e is None:return '未知，不能用候选行为代填'
 if i['kind']=='career':return e['title']+'；工资'+str(e['salary'])+'；储蓄'+str(e['savings'])+'；其他职业字段见目标JSON，不等同原版分配/选择交互已确认'
 if i['kind']=='card':return json.dumps(e['mechanical'],ensure_ascii=False)+'；原文指纹见目标JSON，完整卡面待核验'
 if i['kind']=='space':return '原版模板槽位'+str(e['original_template_slots'])+'；机制'+str(e['mechanical'])
 return e if isinstance(e,str) else json.dumps(e,ensure_ascii=False)
sheet(w,'335项目标目录',['ID','类别','原版预期/功能事实','来源等级与限制','目标/设计/对照状态','待补'],[[i['id'],i['kind'],expected_summary(i),'；'.join(str(v) for v in i['source_hint'].values()),'未封板','原版证据→目标规格→代码指纹→候选结果→对应比较'] for i in target['items']])
sheet(w,'15份资料与来源等级',['资料','固定版本SHA256','历史官网同哈希','证据等级','限制'],[[r['resource'],r['sha256'],r['historical_official_hash_match'],r['evidence_level'],'不是本轮官网实玩或当前版本证明'] for r in receipts['resources']])
sheet(w,'证据链数据字典',['字段','用途','拒绝条件'],[['primary_origin','官网唯一主目标','非精确官网origin'],['reference_snapshot','原版版本/时间/入口资料及哈希','未取得、无版本或文件不匹配'],['expected','原版独立预期','未知不允许通过'],['reference','官网来源URL、类型、文件SHA','第三方冒充官网、文件缺失、哈希不符'],['reference.snapshot_sha256','绑定已选原版快照','混用不同版本的官网证据'],['target_spec','设计文件与章节/目标ID','文件缺失或没有定位'],['implementation','参与实现的源文件SHA','当前代码不同于受测代码'],['candidate','候选截图或结果文件','缺失/哈希不符'],['comparison','对应目标ID和原/候选哈希的测试记录','错用其他用例或未通过'],['screen metadata','同视口、DPR、缩放、语言及PNG实际尺寸','参数不同，或仅静态模板当运行画面'],['release_allowed','正式签收/放行','当前false；工具不代签']])
sheet(w,'实际验证结果',['检查','结果','边界'],[['npm test','370通过/0失败（358规则+12门禁）','本轮自动化；不是原版对照通过'],['npm run test:acceptance','12通过/0失败','门禁正反用例，不是335项目标已核实'],['npm run release:check','预期阻断，0/335完整证据链','原版网页当前不可达；49页正式封板仍0/49'],['官网网络','普通、本轮网络授权及授权执行通道均CONNECT403','配置草稿已含域名，不再重复要求添加域名'],['浏览器组','29套既有+2套标题组，结果见validation-latest.json','候选回归不等于官网全等'],['UI/玩法变更','修复标题原文/画布定位与构建版本号','仅历史官网标题局部证据通过，不代表全屏封板']])
for ws in w:
 for c in ws[3]:
  a=copy(c.alignment);a.wrap_text=True;c.alignment=a
 ws.row_dimensions[3].height=36
 ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=ws.max_column);ws.row_dimensions[1].height=34
 ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=ws.max_column);ws.cell(2,1,'2026-11-04 / 游戏v0.6.6 / 官网唯一目标核验；335为一级目录，不是完整测试用例数量');ws.row_dimensions[2].height=36
w.save(NEW/'官网目标与复核整改.xlsx')

d=Document();style_doc(d)
d.styles['Normal'].paragraph_format.space_after=Pt(4)
for name,b,a in [('Heading 1',12,6),('Heading 2',8,4)]:d.styles[name].paragraph_format.space_before=Pt(b);d.styles[name].paragraph_format.space_after=Pt(a)
for sec in d.sections:
 for para in sec.footer.paragraphs:
  for run in para.runs:run.text=run.text.replace('文档修订 1.1','文档修订 1.3').replace('2026-11-02','2026-11-04')
d.add_heading('官网经典版唯一目标复核与修订报告',0)
d.add_paragraph('最终目标尚未实现。本轮将验收范围修正为用户明确指定的官网经典版，并修复仅靠通过标记即可放行的验收漏洞；原版规则、页面和交互的完整对照仍被官网连接阻断。不能将这些工具和文档修改当成游戏界面已还原。')
table(d,['控制项','当前基线'],[['日期/版本','2026-11-04；游戏v0.6.6，文档1.3'],['唯一对照','https://cfclassic.richdad.com/；实体卡牌/其他站点/视频仅辅助'],['调查资料','本轮独立取得15份固定镜像资料；9份SHA匹配历史官网资源，6份仅镜像未核实'],['当前官网访问','普通通道、受支持网络权限授权后、授权执行通道均在代理CONNECT阶段403；没有新的官网实玩'],['验收状态','335项未封板；49页正式核验仍0/49；release_allowed=false']],[1.5,5.2])
d.add_heading('复核问题与对应修改',1)
for ident,domain,finding,status,fix,files in issues:
 d.add_heading(ident+' '+domain,2);d.add_paragraph(finding+'。'+status+'：'+fix+'。依据/变更：'+files+'。')
d.add_heading('原版证据与设计修改的工作顺序',1)
d.add_paragraph('先取得官网原始规则、职业和卡牌事实，以及页面入口、动作、取消、恢复和结果；固定官网版本和语言，保存可追溯资料。随后将原版预期写成独立目标，再分析候选差异、调整设计和代码。最后用同状态、同视口的原版/候选结果比较并回归。未知保持未知，不根据当前实现补写“原版就是这样”。')
table(d,['类别','必须核验数量','当前闭环'],[['规则',44,'未逐项封板；单元证据与原版证据分开'],['页面组件',49,'完整显示/交互封板0/49'],['职业',12,'180数值字段先前匹配；分配/自选行为需官网证据'],['卡牌',182,'独立机制字段已复核；完整文案、美术、运行后果未全等'],['外圈格',48,'静态位置/内容线索与特殊格行为分别核验'],['合计',335,'0条完整原版→设计→实现→比较证据链；这不是功能完成率']],[1.3,1.5,3.9])
d.add_heading('本轮代码验证和未完成范围',1)
d.add_paragraph('358项游戏规则单测及12项新增门禁测试本轮通过。门禁测试覆盖缺证据、错来源、过时代码、混用原版快照、错误测试关联、缺设计定位、遗漏目标、视口/语言不同及越界文件路径；完整合法测试夹具可通过，生产目标保持阻断。另执行29套既有及2套新增标题浏览器组，详见本轮validation-latest.json，失败不放行。')
d.add_paragraph('门禁只能检查证据关联、文件完整性和过期状态，不能凭JSON元数据证明一张截图确实来自官网，不能替代人工来源审阅和真实对照。源码/模板相同也不能证明当前官网运行、动画和所有分支相同。')
d.add_heading('当前外部阻断',1).paragraph_format.page_break_before=True
d.add_paragraph('已读取配置草稿，官网域名已在允许列表。本轮网络权限也已通过受支持工具授予，但代理仍在建立官网连接前拒绝请求；当前工具未暴露运行环境配置的实际应用状态。不能将拒绝解释成用户未授权、缺少账号或官网登录失败，也不应重复要求添加同一域名。继续官网实玩需要平台提供能通过受支持代理访问该已授权域名的运行环境。')
d.add_paragraph('本轮v0.6.6修复两项可证实问题：标题提示恢复历史官网英文Click Anywhere to Continue并以原始画布坐标绘制；标题版本从硬编码v0.6.4改为读取构建版本。原图239c27af…来自历史官网画面，画面版本为1.0.0(0.0.8)，不是当前官网版本证明。在1280×960、DPR1下比较x756/y750/388×43提示区域，RGBA通道最大误差1，无通道超过1；未屏蔽区域内像素。自身版本号如实显示0.6.6，不冒充原版版本。详情见title-target-fixture.json和title-comparison-online/offline.json。其余页面、玩法完整一致性未达成，正式放行保持阻断。')
d.save(NEW/'官网唯一目标复核与修订报告.docx')
print('Updated six controlling DOCX specs, original target report, four workbooks, new review report and trace ledger.')
