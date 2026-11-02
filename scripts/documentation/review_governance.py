#!/usr/bin/env python3
"""Rebuild the governance review and idempotently update controlled phase specifications."""
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
import json
ROOT = Path(__file__).resolve().parents[2]
root = ROOT / 'docs/professional-delivery'
out=root/'10-专家审核与修订';out.mkdir(exist_ok=True)
findings=[
('GOV-01','高','流程仅九阶段，发现与可行性、技术/玩法原型没有独立通过条件','01项目章程阶段表；05实施计划子阶段表','补充发现、预研、切片、Alpha、Beta、候选和退役的映射与裁剪依据','文档整改完成；阶段执行未追认'),
('GOV-02','高','门禁通过标准过于概括，未明确否决、例外与复开机制','治理职责与风险台账/阶段门禁','逐门禁定义输入、输出、责任、否决及例外规则','文档整改完成；实际批准待执行'),
('GOV-03','中','维护只有变更流程，未定义事故分级、交接及停服归档','缺陷变更与维护规范/问题生命周期','新增事件响应、离线和在线不同处置、退役保留与删除规则','文档整改完成；SLA与人员待批准'),
('GOV-04','高','职责只有角色，缺实际任命与批准权限；这是真实项目执行缺口','章程批准状态；治理工作簿RACI','增角色任命与权限记录，明确人少可兼任但提交/批准分开','记录结构完成；不代填人名与签名'),
('GOV-05','中','工作计划缺估算假设、资源可用性、依赖控制及变更后重排规则','WBS需求追踪与交接/WBS','增滚动规划、三点估算字段、关键依赖、无承诺日期规则','文档整改完成；估算和承诺待研发执行'),
('GOV-06','高','“大公司一样”没有适用性判断，不能由文件数量推出流程等效','交付依据与阶段复核报告/公开研究','定义规模裁剪矩阵与证据等级，不宣称任何公司认证或成熟度级别','文档整改完成；外部认证不在范围'),
('GOV-07','中','变更表缺成本/排期影响、批准条件、例外到期与复评字段','问题变更与决策台账/变更控制','新增CCB议程、状态流转、基线冻结及例外到期自动阻断规范','文档整改完成；具体变更逐项评审'),
]
stages=[
('L0','发现与可行性','01','用户问题、参考版次、使用权、目标设备、风险初筛','立项建议/可行性结论、初始范围、否决项','产品负责；技术/规则/QA会签','版次、权利或目标不可执行则不通过'),
('L1','预研与制作准备','02/03/04','PRD/GDD、关键原型、技术试验、规则来源','范围基线、设计/技术契约、未决清单','产品A；策划/UX/技术R','未经实测的原站行为不得填已确认'),
('L2','纵向切片','05/06','一个完整回合、买卖、报表、保存、联机错误','可玩切片与自动化/人工证据','技术A；研发R；QA复核','取消/刷新/断线无法恢复则不通过'),
('L3','Alpha功能完整','05/06','核心状态、数据全量、异常路径、需求追踪','功能覆盖清单、缺陷、兼容记录','技术A；研发/QA R','核心路径缺失、状态丢失阻断'),
('L4','Beta质量与表现','03/06','冻结设计、长中文、金额、设备矩阵、性能/安全目标','候选质量报告、已知问题、原版对照记录','QA A；设计/研发R','未核验原版覆盖不能宣称完全一致'),
('L5','发布候选与UAT','07/08','唯一提交与包SHA、回退结果、UAT场景与例外','签收/拒收记录、发布建议与留存证据','产品A；QA/用户R；发布执行','未签收/高严重性阻断缺陷/包不一致不得正式发布'),
('L6','上线与持续维护','07/09','运维交接、告警/日志、负责人、版本存档','运行记录、事故复盘、增量变更回归','发布/运维A；研发/QA R','在线无恢复演练或关键告警方案不能扩大发布'),
('L7','退役与归档','09','停服范围、用户通知方案、数据去向、授权限制','停服检查表、离线可用性说明、归档目录','产品A；运维/技术R','未批准数据保留删除方案不得执行销毁'),
]

def doc(name,docid,title):
 d=Document();sec=d.sections[0];sec.header.paragraphs[0].text='CASHFLOW  |  PROJECT GOVERNANCE'
 sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.65)
 s=d.styles['Normal'];s.font.name='Noto Sans CJK SC';s.font.size=Pt(10);s._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
 d.add_heading(title,0)
 d.add_paragraph(f'{docid} · 修订 1.1 · 2026-11-02\n实现基线：v0.6.4 / 236a3933ecef；被审文档基线：fdc8f68817c4。')
 d.add_paragraph('审查性质：AI领域审查；不代表已聘请外部真人专家、取得企业内部模板或通过认证。本文修订设计依据，不追认历史执行或代填正式批准。')
 sec.footer.paragraphs[0].text=docid+' · 受控评审稿 · 未经正式签署不得视为已批准'
 return d

def table(d,heads,rows):
 t=d.add_table(rows=1,cols=len(heads));t.style='Light Shading Accent 1'
 for c,v in zip(t.rows[0].cells,heads):c.text=str(v)
 repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
 for vals in rows:
  r=t.add_row()
  for c,v in zip(r.cells,vals):c.text=str(v)
  r._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 return t

r=doc('review','CF-GOV-AUD-02','流程治理领域审核报告')
r.add_heading('1. 审核结论',1)
r.add_paragraph('现有文档覆盖立项到维护的主链，但不足以证明与某一家大型游戏公司的私有流程相同，更不能证明历史门禁全部执行。此次逐项核对发现7个流程治理问题，已用生命周期与治理补充基线及执行工作簿补足可编辑依据；人员任命、版次选择、现场验收与正式批准保留未完成。结论：文档治理设计经整改后可供实施评审；产品发布与原版完全一致性仍不通过。')
r.add_heading('2. 证据与审查方法',1)
r.add_paragraph('逐读项目章程与治理、实施计划与部门交接、缺陷变更与维护规范和交付依据与阶段复核报告DOCX；核对治理职责与风险台账、WBS需求追踪与交接、问题变更与决策台账及交付物清单工作簿；核对package.json中的release:check、scripts/check-release.cjs及audit/reference-coverage.json的release_allowed=false。未执行游戏全套测试，历史353/27结果不重标为本轮。')
r.add_heading('3. 发现—整改—复核',1)
for f in findings:
 r.add_heading(f[0]+' '+f[2],2)
 table(r,['要素','内容'],[('严重性',f[1]),('证据',f[3]),('整改',f[4]),('复核结论',f[5])])
r.add_heading('4. 退出条件',1)
r.add_paragraph('治理文档缺口可由本轮修改关闭；实际人员任命、规则版次与商业使用边界、原版未核验范围、真实双击入口、回退演练、性能与安全目标及UAT必须由对应角色执行并记录证据。不得通过改状态或削弱release:check来满足目标。')
r.save(out/'流程治理专家审核.docx')

d=doc('base','CF-GOV-BASE-02','生命周期、阶段门禁与跨部门治理补充基线')
d.add_heading('1. 生命周期完整性与现有目录映射',1)
d.add_paragraph('大型组织通常将阶段门禁与迭代交付并用。以下是本项目采用的流程模型，不宣称所有大公司统一采用。既有01—09目录按专业资料组织，L0—L7按交付成熟度组织，二者不是一一对应。文档存在不代表阶段已获批。')
for s in stages:
 d.add_heading(s[0]+' '+s[1],2)
 table(d,['门禁字段','本项目要求'],[('对应目录',s[2]),('入场输入',s[3]),('出场产物',s[4]),('责任角色',s[5]),('否决条件',s[6]),('当前执行状态','待以实际证据评审；不追认历史通过')])
d.add_heading('2. 项目规模裁剪与全程工作流',1)
table(d,['工作流','本项目裁剪','不可裁掉的证据'],[
('商业化/充值/经济运营','当前无充值与排行榜，付费风控、支付对账暂不适用；新增则重新评审','适用性决定、范围变更及产品批准'),
('美术与音频生产','现为参考资源与本地素材，不另建大型外包流水线','素材ID、来源、用途、授权依据、版本、字体与音频失败策略'),
('数据与隐私','无账号体系不等于无数据：房间会话、聊天、存档仍纳入','数据分类、访问边界、日志脱敏、保留/删除决定'),
('安全与性能','单进程文件存储不按大规模云游戏承诺容量','威胁与负载模型、批准的目标、测量环境、结果和扩展限制'),
('用户研究/可访问性','小团队可合并角色，不自动豁免','目标用户、任务验证、键盘焦点/可读性范围与接受例外'),
('配置/质量/权利管理','贯穿所有L阶段，不作为末尾一次性检查','基线提交、包SHA、变更ID、测试证据、来源与批准'),
])
d.add_heading('3. 门禁会议与批准权限',1)
d.add_paragraph('会前由项目负责人冻结评审包，列明文档版本、提交、候选包SHA、问题和必需评审人。负责人先审证据，再记录通过、附条件通过或拒绝。技术负责人可否决状态损坏及不可恢复风险；QA可否决证据失配与阻断缺陷；产品/规则角色可否决规则基准不清与用户目标缺失。最终用户签收独立于研发完成。角色未任命时门禁保持待评审。')
d.add_paragraph('附条件通过仅允许非阻断项，逐条记录范围、风险、责任角色、到期条件、关闭证据与批准人。原版全等声明、数据损坏、权限越界、未验证候选包不能通过例外绕过。例外逾期或基础需求/接口/数据变更时自动复开相应门禁，禁止静默展期。')
d.add_heading('4. 迭代、估算与跨部门交接',1)
d.add_paragraph('每次迭代：选择已满足准备定义的需求→估算与依赖分析→实现和自测→设计/规则复核→QA回归→演示和问题登记→更新基线。准备定义要求需求ID、可执行接受条件、来源、数据边界、接口与设计状态明确；未决项影响实现时拆分为研究任务。完成定义要求代码/数据/设计/测试/包和文档同步，阻断项关闭且证据可复现；不自动等于用户验收。')
d.add_paragraph('WBS先由实际研发给出乐观/最可能/悲观工日及估算假设，可用(乐观+4×最可能+悲观)/6作规划参考。未填人员与可用性不得承诺发布日期；研究任务以时间盒和产出限定，不以无法证实的全覆盖承诺排期。每次范围变更重新计算依赖、资源和关键路径，保留原基线及差异。')
table(d,['交接','必须交付','接收检查与拒收条件'],[
('产品/策划→UX/研发','需求ID、规则版本、来源与接受条件、未决影响','有冲突且无决定不得作为确定规则开发'),
('UX/美术→前端','页面ID/状态、画布与层级、输入/取消、素材与字体边界','未标长文案和错误态时列设计缺口'),
('前后端→QA','接口/Schema、版本、有效/无效样例、权限与恢复约束','请求与响应不一致拒收并联调'),
('研发→发布','受测提交、包SHA、变更影响、迁移回退与测试结果','重打包或SHA变化重新验证'),
('QA/产品→用户','环境、步骤、原版对照范围、遗留与签收栏','历史测试不可替代指定包的人工结果'),
])
d.add_heading('5. 变更控制与文档优先级',1)
d.add_paragraph('CCB由产品、技术、QA及受影响设计/规则角色组成；不以工具生成签字。变更单记录触发、需求/决策ID、旧新行为、数据与存档影响、工作量与排期、风险、回归、批准条件及回退。紧急修复先留最小事件记录并按风险控制，发布后补完整复盘，不能借紧急渠道宣布原版等同。')
d.add_paragraph('优先级：实际已批准决定→版本化需求/规则/设计契约→实现与测试证据。冲突必须登记并由负责角色决定，不能默认代码正确。当前所有未批准原生资料为评审依据；本补充文件在治理字段上补足v1.0，但不覆盖原规则事实与实现。')
d.add_heading('6. 运行事件、退出和归档',1)
table(d,['级别','实例与即时动作','关闭依据'],[
('SEV1','数据损坏、越权或大量房间不可玩：停止受影响新会话、保护日志/存档、隔离并判断回退','恢复校验、用户影响范围、根因和防复发回归；响应时限待批准'),
('SEV2','单房间无法继续或关键报表错误：保存复现包、提供恢复方案并发布修复候选','指定环境复验、状态一致性和影响回归'),
('SEV3','非阻断排版和提示：截图/画布/缩放/字体及重现路径登记','修复前后对照、针对性和必要回归'),
('离线包','无中央停服能力：旧包保留可重现备份，发布新包及版本/存档说明','用户确认版本和迁移；不得声称已远程修复所有旧包'),
('退役','产品提出停止范围，通知需经用户明确授权；评审在线数据保留和删除、离线可用性','归档代码/包/契约/证据及SHA；执行删除需单独批准，不设虚构法定期限'),
])
d.add_heading('7. 受控记录与复核结果',1)
d.add_paragraph('配套工作簿提供阶段门禁、裁剪、任命、CCB、例外和滚动计划结构，并填写当前可证实状态。补充文档经逐项回查已覆盖GOV-01—07的设计缺口；阶段执行、人员签署和产品验收仍未完成。')
d.save(root/'01-立项与治理'/'生命周期与治理补充基线.docx')

w=Workbook();w.remove(w.active)
def sheet(name,heads,rows):
 s=w.create_sheet(name);s.append(heads)
 for row in rows:s.append(row)
 s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
 for c in s[1]:c.fill=PatternFill('solid',fgColor='17365D');c.font=Font(name='Microsoft YaHei',color='FFFFFF',bold=True)
 for row in s.iter_rows(min_row=2):
  for c in row:c.font=Font(name='Microsoft YaHei',size=10);c.alignment=Alignment(vertical='top',wrap_text=True)
 for i in range(1,s.max_column+1):s.column_dimensions[get_column_letter(i)].width=22 if i<3 else 42
 for i in range(2,s.max_row+1):s.row_dimensions[i].height=70
 s.sheet_properties.pageSetUpPr.fitToPage=True;s.page_setup.orientation='landscape';s.page_setup.paperSize=s.PAPERSIZE_A3;s.page_setup.fitToWidth=1;s.page_setup.fitToHeight=0;s.print_title_rows='1:1'
 return s
sheet('审核发现',['ID','级别','问题','证据','整改','复核'],findings)
sheet('生命周期门禁',['ID','阶段','目录','入场输入','退出证据','责任','否决','批准状态'],[list(s)+['待实际评审，未签署'] for s in stages])
sheet('角色任命',['角色','职责与权限','实际人名','可用性','批准人','任命日期','状态'],[
 ['产品负责人','范围/版次与最终发布A','待指定','待确认','待指定','待任命','未任命'],['规则策划','规则冲突与数值证据R','待指定','待确认','待指定','待任命','未任命'],['技术负责人','架构/数据风险A，可否决不可恢复风险','待指定','待确认','待指定','待任命','未任命'],['UX/UI','页面基线与视觉对照R','待指定','待确认','待指定','待任命','未任命'],['QA负责人','证据复核A，可否决阻断缺陷','待指定','待确认','待指定','待任命','未任命'],['发布运维','唯一包发布与恢复R','待指定','待确认','待指定','待任命','未任命'],['实际用户','指定包UAT签收','待指定','待确认','待指定','待任命','未任命']])
sheet('阶段裁剪',['领域','处理','原因','复评触发','批准状态'],[
 ['商业化/支付','当前不适用','当前无支付','新增付费功能','待产品确认'],['大型外包流水线','裁剪为素材台账与来源复核','现有小型项目','引入外包或新资产管线','待产品/设计确认'],['安全/隐私','适用，不可删除','会话、聊天、存档实际存在','数据流改变','目标待批准'],['性能容量','适用，限定单进程范围','不可将rooms上限当压测容量','多进程或扩大并发','目标待批准'],['Alpha/Beta门禁','保留，用L3/L4组织现有05/06','避免目录阶段与质量成熟度混淆','关键功能/设计改变','待实际评审']])
sheet('CCB变更登记',['变更ID','触发/关联','旧行为与目标','受影响资料','成本/排期','风险/回退','批准/复验','状态'],[
 ['DOC-GOV-20261102','GOV-01—07','补足治理字段，不改游戏','治理补充基线及工作簿','本轮文档修订；无虚构工期','旧资料保留；新补充优先说明治理字段','AI复核设计覆盖；正式批准未签','文档整改完成，待实施评审'],['DEC-09','快车道发薪口径','规则决定待作出','GDD/引擎/报表/测试/原版对照','待研发评估','不得自行把未核验目标写成事实','产品/规则角色待批准','开放']])
sheet('例外登记',['例外ID','范围','理由/风险','责任角色','到期条件','批准人','关闭证据','状态'],[['无已批准例外','不适用','不能以空表宣称允许绕过门禁','待具体事件指定','待批准','未签署','无','没有已批准例外']])
sheet('滚动计划',['工作项','前置','验收产物','责任','乐观工日','最可能工日','悲观工日','估算假设/资源','承诺日期','状态'],[
 ['版次/冲突决定','无','DEC-01/02/04/09具体结论','产品/策划','待估','待估','待估','人员与资料可用性待确认','未承诺','待评审'],['原版逐页基线','版次决定','带状态和版本的批准截图/录屏','UX/QA','待估','待估','待估','原站正常操作证据受限','未承诺','待核验'],['实际双击入口','指定候选包SHA','Windows实际解压入口记录','QA/用户','待估','待估','待估','设备可用性待确认','未承诺','待执行'],['回退与质量验证','契约/目标批准','迁移回退/容量/安全记录','研发/QA/运维','待估','待估','待估','环境与目标待批准','未承诺','待执行'],['最终UAT','前述阻断关闭','唯一包签收或拒收结论','产品/用户','待估','待估','待估','用户可用性待确认','未承诺','待执行']])
w.save(root/'01-立项与治理'/'生命周期门禁与协作执行台账.xlsx')
(out/'流程治理审核发现.json').write_text(json.dumps({'date':'2026-11-02','review_type':'AI领域审查','baseline':'fdc8f68817c421754b94bc9b7984a53eebc28169','findings':[dict(zip(['id','severity','finding','evidence','remediation','status'],f)) for f in findings],'product_release_approved':False},ensure_ascii=False,indent=2))
print('created',out/'流程治理专家审核.docx')

# Synchronize existing phase specifications without duplicating revision sections.
changes = {'01-立项与治理/项目章程与治理.docx': ('治理修订1.1：成熟度阶段与目录分离',
                           [['流程补全',
                             '既有01—09为专业目录；新增L0发现/可行性、L1预研、L2纵向切片、L3 Alpha、L4 '
                             'Beta、L5候选/UAT、L6运行、L7退役成熟度门禁，详见同目录生命周期与治理补充基线。'],
                            ['评审权限', '产品对范围负责；技术与QA可否决不可恢复风险或证据失配。未任命负责人或未签署时不得标门禁通过。'],
                            ['适用性', '与公开工程实践的要素对照不等于与任何大公司私有流程完全相同；商业化等当前不适用项须留下裁剪决定。'],
                            ['受控记录', '新增生命周期门禁与协作执行台账.xlsx提供角色任命、门禁、裁剪、CCB、例外和滚动计划。当前真实人员与批准仍待执行。']]),
 '05-开发计划与协作/实施计划与部门交接.docx': ('实施修订1.1：迭代准备、估算和证据交接',
                               [['准备定义', '需求ID、接受条件、规则来源、异常和数据边界明确；未决规则影响实现时先拆研究任务，不当作已确定需求实施。'],
                                ['迭代节奏', '按准备→依赖/估算→实现自测→规则/设计复核→QA回归→演示→基线更新组织；L2切片、L3 Alpha和L4 Beta分别检查贯通、完整性和质量。'],
                                ['排期控制', '三点估算由实际研发填，资源可用性和关键依赖未确认不承诺日期；范围变更重新评估并保存旧基线。'],
                                ['交接拒收', '接口不一致、未标异常态、候选包SHA变化或回归证据不对应均应拒收并复开相关门禁。'],
                                ['治理依赖', '采用01目录生命周期与治理补充基线及生命周期门禁与协作执行台账；文档整改完成不代表计划实际执行。']]),
 '08-用户验收/UAT与最终验收方案.docx': ('验收修订1.1：证据范围与阻断规则',
                             [['候选锁定', '每次验收必须登记代码提交、完整ZIP SHA、入口、操作系统/浏览器/缩放、规则profile、角色和测试日期；不允许拿不同包报告代替。'],
                              ['阶段关系', '最终验收属于L5门禁；L3功能完整和L4质量验证不等于用户签收。用户可给出通过、附条件通过或拒收。'],
                              ['不可豁免', '原版全等目标未核验、关键规则未决、状态损坏、权限越界或候选包与证据不一致不能以文档齐全或无签字例外越过。'],
                              ['待执行', 'DEC-01/02/04/05/06/09以及实际设备双击、原版逐页对照、迁移回退等需对应证据；现有签收继续未签署。'],
                              ['配套治理', '附条件通过逐项记录范围、风险、负责人、到期和关闭证据；依据01目录生命周期与治理补充基线及协作执行台账。']]),
 '09-维护与变更/缺陷变更与维护规范.docx': ('维护修订1.1：事故、例外及退役',
                             [['事件分级',
                               'SEV1数据损坏/越权/大面积不可玩先保护状态并限制影响；SEV2单房间阻断保留复现包与恢复方案；SEV3非阻断显示问题以截图和环境复验。响应时限须实际批准，不填虚构SLA。'],
                              ['离线与在线', '在线可限制新会话并评估恢复；离线已分发包不能远程替换，需发布新版本和存档兼容说明。'],
                              ['CCB与复开', '变更记录规则/数据/存档/接口/设计/测试、成本与排期影响、回退和批准；已批准例外逾期或基础条件变化应复开门禁。'],
                              ['退役', 'L7要求明确停服范围、离线可用性、归档包/源码/契约/SHA及数据保留删除计划；发送通知和执行数据删除须有相应授权，不自动执行。'],
                              ['执行依据', '同01目录生命周期与治理补充基线及执行台账；既有问题单保持真实未决状态。']])}

for rel, (title, rows) in changes.items():
    path = root / rel
    current = Document(path)
    for paragraph in current.paragraphs:
        if paragraph.text == title:
            element = paragraph._p
            # Replace exactly this heading, explanatory paragraph and owned table.
            next_element = element.getnext()
            if next_element is not None and next_element.tag == qn('w:p'):
                after = next_element.getnext()
                next_element.getparent().remove(next_element)
                if after is not None and after.tag == qn('w:tbl'):
                    after.getparent().remove(after)
            element.getparent().remove(element)
            break
    current.add_heading(title, 1)
    current.add_paragraph('修订日期2026-11-02；AI领域审查整改，未改游戏实现。以下补充替代v1.0中相应概括性治理要求，正式批准仍待真实责任角色执行。')
    table(current, ['修订项', '受控要求'], rows)
    for paragraph in current.paragraphs:
        if paragraph.text.startswith('变更登记：文档版本1.0；'):
            paragraph.text = '变更登记：原始资料版本1.0（2026-10-27）；本次治理修订1.1（2026-11-02）。新增生命周期门禁、协作和验收阻断要求；未改游戏实现，未代填批准。后续变更须记录需求/决策ID、影响范围、评审与构建。'
    current.save(path)
for path in [out/'流程治理专家审核.docx', root/'01-立项与治理/生命周期与治理补充基线.docx']:
    current = Document(path)
    for style in current.styles:
        if style.name.startswith('Heading') or style.name == 'Title':
            style.font.color.rgb = RGBColor(0, 0, 0)
    current.save(path)
path = out/'流程治理审核发现.json'
result = json.loads(path.read_text())
for item in result['findings']:
    item['fix'] = item.pop('remediation')
    item['doc_status'] = '已修订并交叉复核'
    item['execution_status'] = '待实际角色任命/审批/执行，不追认通过'
    item['files'] = ['01-立项与治理/生命周期与治理补充基线.docx',
                     '01-立项与治理/生命周期门禁与协作执行台账.xlsx'] + list(changes)
path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

# Avoid a nearly blank final governance page, observed in the first rendered review.
path = root/'01-立项与治理/生命周期与治理补充基线.docx'
current = Document(path)
current.styles['Normal'].paragraph_format.line_spacing = 1.15
current.styles['Normal'].paragraph_format.space_after = Pt(4)
for style_name in ['Heading 1', 'Heading 2']:
    current.styles[style_name].paragraph_format.space_before = Pt(10)
    current.styles[style_name].paragraph_format.space_after = Pt(4)
current.save(path)

# Review correction: use 26/74 label/content split for owned two-column tables.
for rel in ['01-立项与治理/生命周期与治理补充基线.docx', '10-专家审核与修订/流程治理专家审核.docx', '01-立项与治理/项目章程与治理.docx', '05-开发计划与协作/实施计划与部门交接.docx', '08-用户验收/UAT与最终验收方案.docx', '09-维护与变更/缺陷变更与维护规范.docx']:
    current = Document(root/rel)
    section = current.sections[0]
    total = section.page_width-section.left_margin-section.right_margin
    owned_tables = current.tables if rel in ['01-立项与治理/生命周期与治理补充基线.docx', '10-专家审核与修订/流程治理专家审核.docx'] else [current.tables[-1]]
    for owned_table in owned_tables:
        if len(owned_table.columns) != 2:
            continue
        owned_table.autofit = False
        widths = [int(total*.26), int(total*.74)]
        for column, width in zip(owned_table.columns, widths):
            column.width = width
        for row in owned_table.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = width
    current.save(root/rel)

# Keep the maintenance decision summary consistent with the rules master.
path = root/'09-维护与变更/缺陷变更与维护规范.docx'
current = Document(path)
for decision_table in current.tables:
    all_text = '\n'.join(cell.text for row in decision_table.rows for cell in row.cells)
    if len(decision_table.columns) == 4 and 'DEC-08' in all_text and 'DEC-09' not in all_text:
        cells = decision_table.add_row().cells
        for cell, value in zip(cells, ['DEC-09', '快车道发薪口径', '对照原版实际发薪，确认报表与结算口径后决定是否改规则', '待核验']):
            cell.text = value
current.save(path)

# Visual review correction: avoid a sparse final review page.
path = out/'流程治理专家审核.docx'
current = Document(path)
current.styles['Normal'].paragraph_format.line_spacing = 1.1
current.styles['Normal'].paragraph_format.space_after = Pt(3)
for style_name in ['Heading 1', 'Heading 2']:
    current.styles[style_name].paragraph_format.space_before = Pt(9)
    current.styles[style_name].paragraph_format.space_after = Pt(3)
for paragraph in current.paragraphs:
    if '未执行游戏全套测试，历史353/27结果不重标为本轮。' in paragraph.text:
        paragraph.text = paragraph.text.replace('未执行游戏全套测试，历史353/27结果不重标为本轮。', '本领域未执行游戏全套测试；历史353/27结果不重标为本轮。项目本轮实际回归另见综合审核与修订报告。')
current.save(path)

# Second visual pass: prevent the final maintenance row spilling one character to an empty page.
path = root/'09-维护与变更/缺陷变更与维护规范.docx'
current = Document(path)
for row in current.tables[-1].rows:
    row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    for cell in row.cells:
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.line_spacing = 1.05
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
for decision_table in current.tables:
    if len(decision_table.columns) != 4:
        continue
    for row in decision_table.rows:
        if row.cells[0].text == 'DEC-09':
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = 'Noto Sans CJK SC'
                        run.font.size = Pt(9)
                        run.font.color.rgb = RGBColor.from_string('17365D')
current.save(path)

# Keep the original charter paragraph aligned with the controlled L0-L7 model.
path = root/'01-立项与治理/项目章程与治理.docx'
current = Document(path)
for paragraph in current.paragraphs:
    if paragraph.text.startswith('G0范围确认'):
        paragraph.text = '上述01—09表示专业资料目录。正式成熟度门禁统一采用治理补充基线L0—L7：发现与可行性→预研与制作准备→纵向切片→Alpha功能完整→Beta质量与表现→发布候选与UAT→上线与持续维护→退役与归档。未取得批准的门禁不因为存在代码而自动通过。'
current.save(path)

def synchronize_existing_governance_workbooks(root):
    path=root/'01-立项与治理/治理职责与风险台账.xlsx'
    workbook=load_workbook(path);sheet=workbook['阶段门禁']
    sheet.cell(1,1,'治理职责与风险台账｜01—09资料域检查')
    sheet.cell(2,1,'01—09仅为专业资料域检查；正式成熟度门禁L0—L7以生命周期门禁与协作执行台账为准；不追认已通过。')
    sheet.cell(4,1,'资料域（非成熟度门禁）')
    workbook.save(path)
    path=root/'05-开发计划与协作/WBS需求追踪与交接.xlsx'
    workbook=load_workbook(path);sheet=workbook['WBS']
    additions=[
    ('WBS-09','统一证券数量上限契约','GX-07 / REQ-011','产品/规则先裁决1..1000000直接buy与1..99999表单数量上限；再更新引擎/界面/API/测试','策划／前端／后端／QA','批准一个目标或显式保留分支差异；0/1/99999/100000/1000000/超限逐分支断言，拒绝不结算；同步GDD/API/UI','待执行；现状已澄清，未批准规则变更'),
    ('WBS-10','持久化失败一致性与恢复加固','TQ-02 / REQ-006/016','WBS-04；批准内存先变更/磁盘失败后的产品语义与恢复方案','后端／前端／QA','磁盘只读/空间不足/rename失败注入；客户端先GET，不盲目重放；重启后磁盘/内存差异有可复现证据，无重复扣款；按批准方案决定代码加固','待执行；文档规定恢复语义，故障验证及加固未完成'),
    ('WBS-11','可信代理转发头与健康检查','TQ-04 / REQ-005/015','WBS-04；固定部署域名/可信代理链及TLS终止点','后端／运维／安全QA','代理剥离外来x-forwarded-host并设置受控值；伪造Host/Origin与绕过代理均拒绝越界请求；liveness/readiness分开验证，磁盘失败不能被活进程掩盖','待执行；实现/部署验证均未通过'),
    ('WBS-12','房间创建和密码尝试限流','TQ-03 / REQ-015/017','WBS-06批准负载/滥用模型；WBS-11可信客户端来源','后端／运维／QA','批准并实现按来源/会话的限流和密码退避；测正常多人不误伤、恶意创建/重试被限制、错误可恢复；无虚构阈值和已达容量','待执行；方案批准及实现待完成'),
    ('WBS-13','过期房间TTL与数据保留回收','TQ-03 / REQ-006/017','WBS-12；产品批准活跃房间、断线恢复窗口、TTL和数据保留政策','产品／后端／QA','明确最后活动时间与回收时机；活跃房不误删，过期房按批准规则回收；回收与写入/重启并发可恢复，TTL数值须先批准','待执行；当前无已通过TTL方案'),
    ('WBS-14','逐分支契约和恢复发布验证','TQ-05/06/07/08 / REQ-009/014/018','WBS-09—13；环境矩阵与候选SHA冻结；非适用项逐条批准','QA／研发／运维／用户','技术质量验证矩阵逐例留环境/动作/断言/日志；API负面分支、真实双击、停写备份恢复回退均有证据；不把353单测代替执行结果','待执行；仅单元回归已执行')]
    identifiers={sheet.cell(row,1).value for row in range(5,sheet.max_row+1)}
    for values in additions:
        if values[0] in identifiers:
            row=next(row for row in range(5,sheet.max_row+1) if sheet.cell(row,1).value==values[0])
        else:
            row=sheet.max_row+1
        for column,value in enumerate(values,1):
            cell=sheet.cell(row,column,value)
            cell._style=copy(sheet.cell(5,column)._style)
            cell.alignment=Alignment(wrap_text=True,vertical='top')
        sheet.row_dimensions[row].height=112
    sheet.auto_filter.ref=f'A4:G{sheet.max_row}'
    workbook.save(path)

synchronize_existing_governance_workbooks(root)
