"""Source-backed v0.6.5 gap register, controlled specs and iteration report."""
from pathlib import Path
import json,shutil,html,urllib.parse
from docx import Document
from docx.shared import Pt
from openpyxl import Workbook,load_workbook
from integrate_expert_review import style_doc,table,sheet
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/professional-delivery';DEST=OUT/'11-v0.6.5差距分析与迭代';DEST.mkdir(exist_ok=True)
gaps=[
('GAP-01','已证实数值差异','官网历史记录现金310400→311000；v0.6.4金币出售加6000','audit/official-runtime.json additional_runtime_observations.gold_settlement','已修复（官网兼容模式）','10枚金币报价、确认和到账均600；旧规则模式保留6000','规则/QA；原版当前复访仍待补'),
('GAP-02','内部交互与接口不一致','表单上限99999，直接buy可达1000000','engine.js buy/stockQuantity/confirmStock；GX-07','已修复（全层同限）','官网兼容模式统一99999；旧规则保留1000000；超限不改现金/资产/版本','前端/后端/QA；不是原站私有API的比较结论'),
('GAP-03','旧版本迁移风险','旧存档金币出售确认可能仍缓存6000','v0.6.4 assetSale gross/net；新结算quote','已修复（拒绝过期报价）','确认前复核报价；不符时拒绝并提示返回重选，不追溯修改既有现金','规则/存档/QA；旧版已完成交易不重算'),
('GAP-04','原版语义未决','快车道发薪含salary-expenses，报表只显示fastBase+fastGain','DEC-09；engine.js totals；classic-stage.js','待原版证据／裁决','对照原站相同职业、资产、负债的入圈与发薪；不凭猜测改算式','规则/产品'),
('GAP-05','视觉证据不全','单骰源图与锚点已有依据，多骰及所有卡片下位置未封板','audit/dice-layout-fixtures.json；DEC-05','待逐页配对核验','同视口、DPR、缩放和状态录制原站/候选，检查位置、尺寸、遮挡','UX/QA'),
('GAP-06','卡面与文案未全等','182机制卡有数据映射，原文/中文翻译/美术未逐张一致','audit/official-card-facts.json；reference-coverage.json','待完整卡面与来源核验','逐卡逐字段对照，翻译目标需明确；不得由机制数量推定内容全等','策划/美术/本地化'),
('GAP-07','比较版本未统一','实体101规则书、官网在线版、中文参考站不可默认同版','DEC-01/02/04；公开访问本轮均403','待确定全部参考与资料','本迭代仅以既有官网兼容profile修确定差异；实体版不宣称通过','产品/规则'),
('GAP-08','分支运行证据缺口','梦想胜利、离婚、诉讼、破产/队列及组合未全部原站对照','audit/official-runtime.json；reference-coverage.json','待运行核验','49项正式运行画面覆盖门禁仍0/49；已有历史观察不等于逐项封板','规则/QA'),
('GAP-09','财务与显示验证缺口','极值与报表有自动化，缺全职业全状态的原版逐页批准','DEC-03；UX视觉矩阵；v0.6.4用户截图','部分回归通过，原版一致性未通过','测字体/长金额/表格/抽屉/快车道；自动化通过不替代原版对照','前端/UX/QA'),
('GAP-10','入口与设备证据缺口','当前环境限制file导航，不能声称真双击入口已自动验证','DEC-06；浏览器HTTP离线回归','HTTP离线路径通过；真实file待用户测试','解压后Chrome/Edge双击index及offline，记录系统、缩放、字体、SHA','QA/实际用户'),
('GAP-11','联机质量缺口','自建房间协议/持久化/代理信任/限流TTL与原站服务不同','TQ-02/03/04；scripts/rooms.cjs','本轮未实施安全运维加固','按技术矩阵故障注入与安全整改；对局功能测试不是上线安全证明','后端/安全/运维'),
('GAP-12','最终验收缺口','规则决定、容量/恢复/可访问性目标、最终UAT仍未签署','DEC-07/08；08UAT；10审核追踪','仍阻断完整原版等同声明','冻结候选版本与SHA，完成遗留核验后签收；不降低release门禁','产品/QA/用户')]

def make_docs():
 d=Document();style_doc(d);d.sections[0].footer.paragraphs[0].runs[0].text=d.sections[0].footer.paragraphs[0].runs[0].text.replace('1.1','1.2');d.add_heading('Cashflow 原版差距分析与 v0.6.5 迭代规格',0)
 d.add_paragraph('结论：v0.6.4尚未达到原版全部玩法、交互和页面一致。以下按源码、历史原站观察及验收证据分别列出差距，不给没有依据的“一致率”。v0.6.5收敛两个确定问题，并增加旧存档报价保护；未验证的原版分支保持未通过。')
 table(d,['控制项','依据'],[['版本/日期','游戏0.6.5；文档修订1.2；2026-11-02'],['比较基准','当前官网兼容规则profile；实体101与中文站差异分别记录'],['原站观察范围','本轮三个参考链接均被代理403拒绝；使用仓库2026-10-23历史观察摘要，不声称本轮重新登录'],['证据限制','金币原始临时采集文件未随仓库保留；历史摘要有前后现金和SHA，仍需后续独立复访'],['受控历史','00与10为v0.6.4历史审核；本目录控制本轮改动。旧审核SHA不代表修订后文件的当前SHA']],[1.4,5.3])
 d.add_heading('差距清单与处理范围',1)
 for ident,kind,problem,evidence,status,accept,owner in gaps:
  d.add_heading(ident+' '+kind,2)
  d.add_paragraph(problem+'。依据：'+evidence+'。')
  table(d,['本轮状态','验收要求与后续责任'],[[status,accept+'。'+owner]],[1.55,5.15])
 d.add_heading('已实施的规则与兼容性变更',1)
 table(d,['事项','v0.6.4','v0.6.5'],[['金币官网兼容','10×600=6000','一个10枚金币资产包卖出总到账600；legacy仍6000'],['证券买入','直接buy允许1000000；表单99999','共享stockBuyLimit；参考模式全部99999，旧模式1000000'],['旧存档出售确认','缓存报价可能与新版实际结算不同','复核gross/net/debt；不符拒绝，提示返回重选；现金和资产保持不变'],['存档与版本','Game v3 / classic-research-v3','结构不变；不重算历史现金，重新确认未来交易']],[1.4,2.35,2.95])
 d.add_paragraph('不修改尚未查清的快车道发薪口径，不据猜测补原版卡面，也不将通过本地自动化标成原版完全一致。新的stockBuyLimit为规则函数，不是新增HTTP端点。相关接口形状和存档结构无需更改。')

 for para in d.paragraphs:
  nxt=para._p.getnext()
  if nxt is not None and nxt.tag.endswith('}tbl'):para.paragraph_format.keep_with_next=True
 d.save(DEST/'原版差距分析与迭代规格.docx')
 w=Workbook();w.remove(w.active)
 sheet(w,'差距与版本处置',['ID','性质','v0.6.4现状','证据','v0.6.5状态','验收要求','责任与边界'],gaps)
 cases=[['IT065-01','金币参考/旧规则各一次出售','600/6000；资产移除；重复出售拒绝','reference.test.cjs'],['IT065-02','直接buy边界和非法数值','99999通过，100000/1000000/非整数拒绝，拒绝无状态变化','reference.test.cjs'],['IT065-03','旧规则与已有大持仓','旧规则1000000可买；参考已有150000可全卖','reference.test.cjs'],['IT065-04','服务端绕过','超限拒绝，版本/现金/资产不变；合法量成功','rooms.test.cjs'],['IT065-05','旧版确认卡JSON恢复','旧6000确认拒绝；取消重选600再确认成功','reference.test.cjs'],['IT065-06','真实界面操作','输入上限、确认买入、财务行选金、取消/确认出售','scripts/iteration-065-smoke.cjs']]
 sheet(w,'迭代验收用例',['ID','路径','断言','自动化依据'],cases)
 sheet(w,'用户测试顺序',['序号','操作','期望与记录'],[[1,'解压完整包，双击index.html','标题版本0.6.5；若打不开记录浏览器/系统；此项需真实file测试'],[2,'创建本地房间，选梦想，掷骰并打开财务表','骰子显示、文字可读；开关报表与查看棋盘无异常遮挡'],[3,'正常遇到股票/基金卡，试输入100000','官网兼容模式应限制99999；已有超过99999的持仓仍可出售'],[4,'如持有10枚金币并抽到600市场卡','从财务行选资产；确认卡与到账均600'],[5,'恢复v0.6.4保存的金币出售确认','如原确认仍6000，应拒绝并要求返回重选，不能静默到账600'],[6,'在线模式另开两个浏览器测试联机','同一Node服务，使用独立会话；检查回合归属、报表和重连']])
 w.save(DEST/'差距追踪与迭代验收.xlsx')
 # Update the actual controlling specs, while preserving prior audit records as historical.
 for rel in ['02-需求与游戏规则/PRD产品需求规格.docx','02-需求与游戏规则/GDD玩法与数值设计.docx','03-交互与视觉设计/交互与视觉设计规格.docx']:
  f=OUT/rel;doc=Document(f)
  for p in doc.paragraphs:
   if p.text.startswith('GX-07边界澄清：'):p.text='GX-07已在v0.6.5修复：官网兼容模式界面、引擎直接buy、联机服务端统一99,999份上限；旧规则模式保留1,000,000份；已有大持仓出售不受买入上限影响。见11目录迭代规格与回归证据。'
  for t in doc.tables:
   for row in t.rows:
    if row.cells[0].text=='DEC-02':
     vals=['DEC-02','黄金结算 | v0.6.5官网兼容按历史观察到账600；旧规则仍6000','官网兼容已实施并回归；实体版与最新原站复访待补','规则/QA | 实体目标仍待核验']
     for c,v in zip(row.cells,vals):c.text=v
  if not any(p.text=='v0.6.5 受控修订' for p in doc.paragraphs):
   doc.add_heading('v0.6.5 受控修订',1)
   doc.add_paragraph('文档修订1.2，2026-11-02。当前实施基线为v0.6.5，新增条款及结果以11-v0.6.5差距分析与迭代目录为准；前述v0.6.4审核记录及原有待办保留历史范围。')
   table(doc,['变更','当前要求'],[['GAP-01金币','参考模式报价与确认总到账600；旧规则6000。旧版已结算金额不追溯重算。'],['GAP-02数量','E.stockBuyLimit统一规则与UI上限；参考99999/旧规则1000000；非法拒绝不得改变资金、持仓或联机版本。'],['GAP-03存档','过期出售确认必须拒绝并提示返回重选；不得显示6000却静默结算600。'],['仍待办','DEC-09、原版逐页/逐卡/多骰核验、真实file、上线安全及正式UAT保持未通过。']],[1.5,5.2])
  for row in doc.tables[0].rows:
   if row.cells[0].text=='实现基线':row.cells[1].text='v0.6.5 / 文档修订1.2；源码指纹见11目录'
   if row.cells[0].text=='编制与复核日期':row.cells[1].text='2026-11-02（初版2026-10-27）'
  for sec in doc.sections:
   for para in sec.footer.paragraphs:
    for run in para.runs:run.text=run.text.replace('v0.6.4','v0.6.5').replace('2026-10-27','2026-11-02')
  for para in doc.paragraphs:
   if rel.endswith('GDD玩法与数值设计.docx') and '专项审核修订' in para.text:para.paragraph_format.page_break_before=False
  for t in doc.tables:
   for row in t.rows:
    if row.cells[0].text=='DEC-08':row.cells[1].text='最终签收 | v0.6.5本轮358单测、29浏览器回归通过；无正式UAT批准'
    if row.cells[0].text in ['DEC-02','DEC-08']:
     for c in row.cells:
      for para in c.paragraphs:
       para.paragraph_format.space_after=Pt(3);para.paragraph_format.space_before=Pt(2)
       for run in para.runs:run.font.size=Pt(9)
   if rel.endswith('GDD玩法与数值设计.docx') and t.rows[0].cells[0].text=='角色':
    for i,row in enumerate(t.rows):
     for c in row.cells:
      for para in c.paragraphs:para.paragraph_format.keep_with_next=i<len(t.rows)-1
  doc.save(f)
 # Keep cached formulas by recalculating this changed workbook before packaging.
 for rel in ['02-需求与游戏规则/需求规则与数值主表.xlsx','09-维护与变更/问题变更与决策台账.xlsx','08-用户验收/UAT签收与遗留事项.xlsx']:
  f=OUT/rel;book=load_workbook(f)
  for ws in book:
   for row in ws:
    if row[0].value=='DEC-02':
     row[2].value='v0.6.5参考模式金币总到账600；旧规则6000；依据历史原站观察'
     row[3].value='参考模式已实现并回归；实体版目标及原站当前复访仍待补'
     if len(row)>5:row[5].value='部分关闭；实体规则待核验'
    if row[0].value=='DEC-08':row[2].value='v0.6.5本轮358单测/29浏览器回归通过；正式UAT仍未签署'
  book.save(f)
 sources=json.loads(Path('/tmp/cf065-live-access.json').read_text());(DEST/'本轮原站访问结果.json').write_text(json.dumps({'date':'2026-11-02','accesses':sources,'new_original_runtime_verification':False},ensure_ascii=False,indent=2))
 (DEST/'差距清单.json').write_text(json.dumps({'version':'0.6.5','scope':'官网兼容迭代；不是完整原版验收','gaps':[dict(zip(['id','kind','before','evidence','status','acceptance','owner'],g)) for g in gaps]},ensure_ascii=False,indent=2))
 print('Created gap report/ledger and revised PRD, GDD, UX and rule/decision/UAT workbooks.')

def make_test_report():
 r=json.loads((ROOT/'audit/validation-v0.6.5.json').read_text());assert r['passed']
 shutil.copyfile(ROOT/'audit/validation-v0.6.5.json',DEST/'本轮游戏回归结果.json')
 d=Document();style_doc(d);d.sections[0].footer.paragraphs[0].runs[0].text=d.sections[0].footer.paragraphs[0].runs[0].text.replace('1.1','1.2');d.add_heading('Cashflow v0.6.5 迭代测试报告',0)
 d.add_paragraph('本轮以解压后的完整测试包执行自动化。结果仅证明下列功能和布局回归通过；原版全等门禁继续阻断，真实file双击入口仍需用户实测。')
 table(d,['检查','本轮结果'],[['执行基线','0.6.5-preview / '+r['checked_at_utc']],['单元测试',str(r['unit_tests']['passed'])+'通过，0失败；解压候选包执行'],['浏览器检查',str(r['browser_check_count'])+'套通过；在线、内嵌离线、auto index本地适配及字体回退'],['新增路径','真实输入与金币财务行选择、取消、确认出售；服务端超限拒绝；旧存档报价复核'],['原版全等','BLOCKED；正式49项画面证据尚未封板，不降低门禁'],['未执行','真实file入口、原站本轮运行、容量安全演练及最终UAT']],[1.5,5.2])
 d.add_heading('逐项浏览器结果',1)
 table(d,['检查脚本','入口／条件','结果'],[[x['command'].replace('node scripts/',''),x['environment'].get('CASHFLOW_TEST_URL','')+(' 字体拒绝' if x['environment'].get('CASHFLOW_FAIL_FONT') else ''),x['status']] for x in r['browser_checks']],[2.5,3.4,.8])
 d.add_heading('证据与交付完整性',1)
 d.add_paragraph('完整日志见audit/test-logs/v0.6.5；本轮游戏回归结果.json含日志SHA与已测关键文件SHA。最终ZIP会核对这些关键游戏文件与已测解压候选完全相同；文档和证据更新不替代对游戏代码的回归。')
 d.add_paragraph('用户优先测试：解压后直接打开index.html，再验证骰子、财务抽屉、文字边界与旧存档。如仍有显示差异，请记录系统、浏览器、窗口尺寸、缩放与页面截图，以便定位未覆盖环境。')
 d.save(DEST/'迭代测试报告.docx')
 print('Created actual iteration test report from',r['browser_check_count'],'browser checks.')

if __name__=='__main__':
 import sys
 make_test_report() if '--test-report' in sys.argv else make_docs()
