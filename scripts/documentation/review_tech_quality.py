from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
import json,hashlib,subprocess
root=Path(__file__).resolve().parents[2]; base=root/'docs/professional-delivery'; out=base/'10-专家审核与修订';out.mkdir(exist_ok=True)
findings=[
('TQ-01','高','安全设计缺项','04技术设计仅罗列控制，无信任边界、滥用场景、残余风险和验证责任。','补充威胁模型、控制证据及上线前安全门禁。','文档已修订；工程安全验证待执行'),
('TQ-02','高','持久化语义不足','scripts/rooms.cjs:14,20,50：内存先变更、persist后响应；rename原子替换不等于内存磁盘事务。','明确失败后状态可能已变更；客户端先GET恢复，不能无条件重放；补断电/写失败演练。','文档已修订；故障演练待执行'),
('TQ-03','高','容量与滥用控制未设计','rooms.cjs:20仅有200房间上限；未见IP级限流、密码重试退避、过期房间回收。','增加滥用测试、代理限流和TTL方案评审；200房间不是容量测试结果。','文档已修订；实现加固待开发'),
('TQ-04','高','部署信任边界不明确','rooms.cjs:57直接使用x-forwarded-host参与Origin允许列表；serve.cjs:18仅报告进程活。','固定代理清理转发头及可信来源；区分liveness/readiness，避免将healthz视为写盘健康。','文档已修订；部署验证待执行'),
('TQ-05','高','测试覆盖矩阵过粗','06工作簿仅概要场景，不能独立指导极值、并发、存档损坏、断网和回退验收。','新增可执行技术质量矩阵，列前置/动作/断言/证据/责任/状态。','文档已修订；非单元用例未执行'),
('TQ-06','中','接口响应状态表过宽','openapi.json把400/401/403/404/409/413/503统一分配每个操作；不能视为逐接口已触发证据。','已实际收敛10个操作错误码并标注静态证据；逐分支动态验证仍待执行。','契约与文档已修订；动态分支验证待执行'),
('TQ-07','高','发布运维不可直接执行','07无停写恢复具体顺序、故障分支、双击入口的清晰阻断要求。','增加具体恢复作业卡、证据路径、分层发布门禁和真实入口判据。','文档已修订；真实环境演练待执行'),
('TQ-08','中','复现工具链未固定','package.json仅Node>=18；无固定浏览器/运行时/负载环境基线。','新增执行环境记录与依赖冻结要求，不宣称全部Node版本兼容。','文档已修订；正式支持矩阵待批准'),
]
def table(d,heads,rows):
 t=d.add_table(rows=1,cols=len(heads));t.style='Light Shading Accent 1'
 for c,v in zip(t.rows[0].cells,heads):c.text=str(v)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for r in t.rows:
  for c in r.cells:
   for p in c.paragraphs:
    for run in p.runs:run.font.size=Pt(9)
 return t
def setup(title,code):
 d=Document();sec=d.sections[0];sec.header.paragraphs[0].text='CASHFLOW / 技术与质量领域审核 / 受控评审稿'
 style=d.styles['Normal'];style.font.name='Noto Sans CJK SC';style.font.size=Pt(10);style._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
 d.add_heading(title,0);table(d,['受控项','内容'],[('编号',code),('版本与日期','1.1 / 2026-11-02'),('实现基线','v0.6.4 / 236a3933ecef；本轮未改游戏实现'),('审查性质','AI领域审查；不代表真人专家签名或任何企业认证'),('状态','文档整改已执行；产品批准、工程待办、用户验收另行记录')]);return d

d=setup('技术质量专家审核','CF-AUD-TQ-01');d.add_heading('审查结论',1);d.add_paragraph('现有技术、测试和发布文档具备骨架，但专业细化程度不足以单独指导安全上线、故障演练与完整验收。已补齐可执行设计和验证依据；仍不能据此认定原版全等、生产就绪或真实文件入口通过。本轮独立运行353项单元测试通过；原版全等门禁仍阻断。')
d.add_heading('审查范围与方法',1);d.add_paragraph('逐段读取04/06/07原生Word和OpenAPI，静态核对scripts/rooms.cjs、scripts/serve.cjs、package.json及发布门禁；运行npm test和check-release。未做渗透测试、压力测试或真实域名部署。')
for f in findings:
 d.add_heading(f[0]+' '+f[2],2);table(d,['维度','审查记录'],[('级别',f[1]),('证据/问题',f[3]),('修订动作',f[4]),('关闭边界',f[5])])
d.add_heading('本轮验证',1);table(d,['项目','结果','证据'],[('规则/房间单测','353通过；0失败；0跳过','证据/本轮单元测试-2026-11-02.log'),('原版全等发布门禁','预期阻断；运行界面核验0/49','证据/本轮原版全等门禁-2026-11-02.log'),('浏览器、安全、容量、回退、真实双击入口','本轮未执行，不沿用历史作为新通过','技术质量验证矩阵.xlsx')]);table(d,['评审角色','必须核准事项','当前状态'],[('技术负责人','信任边界/恢复与部署方案','待指定、未签署'),('QA负责人','环境矩阵和可复现结果','待指定、未签署'),('产品/用户','发布范围和原版差异','未签署')]);d.save(out/'技术质量专家审核.docx')

d=setup('技术安全与恢复补充规格','CF-TQ-SPEC-01');d.add_heading('1 信任边界与安全控制',1)
threats=[('浏览器→HTTP服务','伪造座位/改action/旧version','Bearer哈希会话、轮序和version校验；服务端结算','越权和重放必须拒绝且余额不变；令牌不进日志'),('互联网→反向代理','洪泛建房/密码猜测/伪造转发头','当前未见应用限流；x-forwarded-host进入允许列表','代理清理客户端转发头；固定Host/Origin；限流阈值先审批再压测'),('房间服务→磁盘','磁盘满/权限错/异常终止','写.tmp后rename；内存先更新','确认失败后内存与磁盘分歧；停止写入、备份两者、重启恢复验证'),('静态根目录→公网','非预期源码/审计文档被公开','serve以仓库为静态根，拒绝点目录和越界symlink','上线使用受控发布根；列允许资源，禁止含会话/个人信息文件'),('浏览器存储→本机用户','令牌/存档读取与篡改','离线无跨设备权限保证；在线权威在服务','共享设备退出清会话；不把离线存档当可信服务器状态')]
table(d,['边界','威胁','当前机制','准入/改进要求'],threats)
d.add_heading('2 一致性、恢复与接口约定',1);d.add_paragraph('写磁盘队列只串行化落盘，不承诺通用数据库事务或通用幂等。action在克隆规则状态成功后替换，但persist抛错仍可能已修改内存。收到失败或超时先GET状态并核对version、pending与金额；不能把超时等同于未执行。GET可更新presence，故不得仅凭version变化认定交易成功。任何补偿必须依据业务状态并经授权。')
table(d,['情况','服务/客户端动作','应保存证据'],[('409并发/旧版本','拉取最新状态，核对当前决策；用户确认后重新发起仍有效动作','前后version、action、无敏感token的请求ID、金额快照'),('超时/5xx/写盘失败','冻结自动重放，GET核对；运维检查写盘，必要停写','错误码、内存/磁盘副本hash、恢复过程'),('坏存档启动','服务load报错不监听；保留损坏原件，从已校验备份恢复','原件hash、备份hash、启动日志和房间回放'),('滚动/多副本','当前禁止多个进程共享JSON存储；升级先停写','进程数、配置与唯一写入者证明'),('契约状态码','OpenAPI已按端点收敛错误码并标注静态证据，动态覆盖另行记录','逐路径实际触发日志；未验证标待执行')])
d.add_heading('3 恢复作业卡（隔离演练）',1)
steps=[('1 选环境','仅在隔离测试目录设置CASHFLOW_ROOMS_FILE；记录版本、OS、Node、浏览器','禁止对用户当前存档直接故障注入'),('2 建基线','建房/加入/开局/合法动作，保存room及存档sha256','脱敏room快照、余额/资产/version'),('3 停写备份','停止入口流量；结束服务；复制存档、配置、版本包到只读备份','备份路径、hash、权限、时间'),('4 故障注入','分别测试无写权限、损坏JSON、旧版本样例；每次使用独立副本','预期失败不得默默覆盖原档；不要报告已测'),('5 恢复','还原同版本兼容备份；单进程启动；GET健康及认证房间','healthz只证明进程活；需真实读写才证明可用'),('6 验证解除','双客户端检查轮序、pending、资产、现金；一次动作后重启再核对','QA与技术签署；恢复耗时实测后再设RTO/RPO')]
table(d,['步骤','操作','退出条件/证据'],steps)
d.add_heading('4 环境与分级准入',1);table(d,['级别','要求','当前结论'],[('文档评审交付','结构可读、证据可追溯、待办不伪关闭','本轮修订可交付评审'),('阶段试玩','受测构建hash一致、核心回归通过、已知差异明示','已有历史阶段包；非本轮重发游戏'),('公开在线服务','安全、负载、恢复、隐私与资源权利评审；实际域名测试','未取得生产签署'),('原版全等','全部原版内容与49运行界面证据、规则差异决策、真实入口与UAT','门禁阻断')]);d.add_paragraph('工具链应随每次执行记录：git提交、ZIP SHA、Node精确版本、npm/Playwright版本、Chromium版本、OS、CPU/内存、视口/DPR/缩放、网络与代理配置。支持矩阵和NFR必须先批准；本说明不擅自制定SLA。');d.save(out/'技术安全与恢复补充规格.docx')

cases=[
('TQ-C01','单元','npm test','当前源码基线，无改动','执行全部五组单测','353通过0失败0跳过','已执行通过','规则/后端'),
('TQ-C02','门禁','node scripts/check-release.cjs','当前coverage基线','执行原版全等发布门禁','阻断，原版运行核验0/49','已执行预期阻断','发布/QA'),
('TQ-C03','权限','HTTP create/join/action','两个合法会话','非当前座位发action','403且现金资产pending不变','待执行','后端/QA'),
('TQ-C04','并发','相同version同时写','一个房间两客户端','相同version并发不同合法动作','最多一次结算；另一请求409；刷新一致','待执行','后端/QA'),
('TQ-C05','重放','超时后重试','合法交易并记录前值','中断响应，GET确认后发送旧version','不会重复结算；恢复提示明确','待执行','前端/后端'),
('TQ-C06','输入','边界与非法JSON','隔离HTTP实例','8192字节边界/超出/畸形/null/数组体','正确错误且进程存活，无状态污染','待执行','后端/QA'),
('TQ-C07','滥用','建房/密码重试','隔离实例；预先批准负载','重复失败密码和房间创建，检查上限','记录当前缺少限流风险；达批准阈值才可通过','待执行','安全/运维'),
('TQ-C08','代理','Origin与Host','可信反代与直连隔离','伪造Origin及x-forwarded-host','反代清理转发头；非法来源拒绝；不泄token','待执行','安全/运维'),
('TQ-C09','存储','写失败','可丢弃存档副本','移除写权限后合法写入再恢复','记录内存磁盘分歧；不盲重放；恢复一致','待执行','后端/运维'),
('TQ-C10','恢复','坏JSON/临时文件','完整备份与基线hash','损坏副本重启；恢复好备份','坏档不被覆盖；恢复现金资产pending一致','待执行','运维/QA'),
('TQ-C11','容量','负载基准','冻结硬件/Node/网络/指标','按批准并发、时长及流量模型执行','P95/错误率/CPU/内存/磁盘达到批准值','待执行','性能/运维'),
('TQ-C12','入口','真实file双击','下载完整包/sha一致/干净配置','断网解压双击index；完整一轮+报表+重载','无外部请求、骰子可见、无重叠且存档可恢复','待执行','兼容QA/用户'),
('TQ-C13','入口','在线双客户端','实际部署域名和TLS','开局/交易/断网恢复/旁观/退出','权威一致，断线不本地结算，遮挡可解除','待执行','前端/QA'),
('TQ-C14','兼容','OS/浏览器/DPR','批准支持矩阵','Windows/macOS Chrome/Edge/Safari按矩阵执行','实测记录版本视口DPR缩放；未测不得通过','待执行','兼容QA'),
('TQ-C15','发布','备份与回退演练','隔离旧包/新包/存档','按恢复作业卡停写备份回退','兼容存档可读且关键规则完整，耗时有证据','待执行','运维/QA'),
('TQ-C16','安全','发布资源/日志','最终发布目录','检查静态可访问资源和服务日志','不含token/会话备份/个人信息；资源权利单有效','待执行','安全/发布'),
]
w=Workbook();s=w.active;s.title='可执行验证矩阵';s.append(['ID','领域','用例','前置','操作','预期断言','本轮状态','责任角色','实际环境/构建','证据/缺陷链接','批准']);
for row in cases:s.append(list(row)+['待补（C01/C02见证据）','C01/C02见证据目录；其余未执行','未签署'])
s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
for col,width in {'A':14,'B':14,'C':26,'D':40,'E':44,'F':55,'G':22,'H':22,'I':30,'J':45,'K':14}.items():s.column_dimensions[col].width=width
s2=w.create_sheet('审查问题闭环');s2.append(['问题ID','级别','主题','证据','文档整改','关闭边界']);
for f in findings:s2.append(f)
s3=w.create_sheet('执行环境');s3.append(['字段','本轮值/要求']);
for k,v in [('日期','2026-11-02'),('实现版本','0.6.4 / 236a3933ecef'),('Node',subprocess.check_output(['node','--version'],text=True).strip()),('说明','仅C01/C02本轮执行；其他验证为可执行设计，不伪造结果'),('游戏源码修改','无'),('浏览器矩阵/容量/RTO','待正式批准及实测')]:s3.append([k,v])
for sh in w:
 sh.freeze_panes='A2'
 for c in sh[1]:c.font=Font(name='Microsoft YaHei',bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='15354C')
 for row in sh.iter_rows(min_row=2):
  for c in row:c.font=Font(name='Microsoft YaHei',size=10);c.alignment=Alignment(vertical='top',wrap_text=True)
  sh.row_dimensions[row[0].row].height=64
 if sh!=s:
  for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=34
w.save(out/'技术质量验证矩阵.xlsx')
# Apply normative additions in existing stage documents, preserving the old structure and metadata.
for directory,file,heading,text,rows in [
('04-技术与接口契约','技术设计与联调契约.docx','1.1修订：安全边界与一致性约束','本轮技术质量审查发现TQ-01至TQ-04、TQ-06。技术设计应与10-专家审核与修订/技术安全与恢复补充规格.docx联合使用；其中信任边界、错误恢复和分级准入为新增设计依据。OpenAPI已按端点收敛为实际可达响应并标注静态分支证据，不代表逐分支运行通过。', [('持久化','写.tmp及rename不等于内存磁盘事务；persist失败可能已改内存；先GET核对再处理，禁止盲目重放。'),('反向代理','当前x-forwarded-host参与Origin比较；部署必须清理客户端转发头并限定可信代理。'),('滥用与容量','200房间只是代码上限；应用限流、密码退避、TTL未实现，需专项评审和工程补强。'),('单进程','不允许多副本共享同一个JSON文件；/healthz不证明存储就绪。')]),
('06-测试与质量保证','测试设计与质量报告.docx','1.1修订：本轮执行与可执行质量矩阵','本轮2026-11-02独立运行npm test：353通过、0失败、0跳过；原版全等发布门禁仍预期阻断。历史27套浏览器记录不改为今日重跑。新增10-专家审核与修订/技术质量验证矩阵.xlsx包含17条具体用例；仅C01/C02已执行，其余均待执行。', [('覆盖新增','权限、并发、超时重放、请求边界、代理、滥用、磁盘失败、坏档恢复、容量、真实file、兼容、回退、静态资源。'),('执行依据','每条必须记录实际构建/ZIP哈希、环境、日志、缺陷、复测和批准；不能仅勾选通过。'),('文件入口阻断','HTTP模拟离线路径不能替代下载包断网双击；由实际设备验证并保存证据。'),('范围边界','单测通过不代表安全审计、负载、浏览器或最终UAT通过。')]),
('07-发布与运维','发布运维与回退手册.docx','1.1修订：发布分级及恢复作业卡','使用10-专家审核与修订/技术安全与恢复补充规格.docx第3节的六步作业卡；在隔离副本演练后才能作为实际回退依据。发布检查必须区分文档评审、阶段试玩、公开服务、原版全等四个等级。', [('停写与备份','停止入口流量和服务后备份存档、配置和版本包；保留SHA与权限，不在用户存档故障注入。'),('恢复验证','坏档不能静默覆盖；还原兼容备份；房间读写、一次交易和重启复核后才恢复流量。'),('上线限制','单进程文件存储；可信反代/TLS/限流/资源白名单需实测，healthz仅作进程探针。'),('门禁状态','本轮原版全等门禁阻断；不得将阶段包或单测通过标成正式原版全等发布。')])]:
 p=base/directory/file;d=Document(p)
 if any(x.text==heading for x in d.paragraphs):continue
 d.add_heading(heading,1);d.add_paragraph(text);table(d,['新增受控要求','实施及验收依据'],rows);d.add_paragraph('修订记录：1.1 / 2026-11-02 / AI技术质量领域审查补充；原有审批仍待指定责任人签署。');d.save(p)

# Endpoint-level response contract: reachable code branches, not dynamic pass assertions.
p=base/'04-技术与接口契约/openapi.json'; contract=json.loads(p.read_text())
for path,ops in contract['paths'].items():
 for method,op in ops.items():
  success='201' if path=='/api/rooms' and method=='post' else '200'
  if method=='get': codes=[success,'400']+(['401','404'] if '{id}' in path else [])
  elif path=='/api/rooms':codes=[success,'400','403','413','503']
  elif path.endswith('/join'):codes=[success,'400','403','404','413']
  else:codes=[success,'400','401','403','404','413']+([] if path.endswith('/chat') else ['409'])
  op['responses']={k:v for k,v in op['responses'].items() if k in codes}
  op['x-contract-status']='Observed reachable branches in scripts/rooms.cjs; not dynamic execution-pass evidence.'
p.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
issues=[dict(id=f[0],severity=f[1],evidence=f[3],fix=f[4],doc_status='已修订，待综合复核',execution_status=f[5],files=['10-专家审核与修订/技术质量专家审核.docx','10-专家审核与修订/技术安全与恢复补充规格.docx','10-专家审核与修订/技术质量验证矩阵.xlsx']) for f in findings]
(out/'技术质量审核问题.json').write_text(json.dumps(dict(date='2026-11-02',review_type='AI领域审查',issues=issues),ensure_ascii=False,indent=2))
# GX-07 cross-disciplinary numeric boundary: preserve actual behavior until product decision.
p=out/'技术安全与恢复补充规格.docx';d=Document(p);d.add_heading('GX-07交易数量上限交叉审查',1);d.add_paragraph('engine.js:70通用buy允许1至1,000,000份；184/188行证券买入上限99,999，卖出上限持仓。须由玩法负责人决定统一或保留分支；不能仅设UI max。增加99999、100000、1000000、1000001直接引擎及在线action边界测试。当前未改代码，未判定原版上限。');d.save(p)
p=out/'技术质量验证矩阵.xlsx'
from openpyxl import load_workbook
w=load_workbook(p);s=w['可执行验证矩阵'];s.append(['TQ-C17','数值边界','GX-07双上限','批准规则前先记录现状','buy与confirmStock各输入99999/100000/1000000/1000001','直接引擎及在线结果与批准规则一致','待执行','玩法/后端/QA','待补','GX-07','未签署']);s.auto_filter.ref=s.dimensions;w.save(p)

# Pagination quality: no split rows and repeated headers, small audit tables stay together.
for name in ['技术质量专家审核.docx','技术安全与恢复补充规格.docx']:
 p=out/name; d=Document(p)
 for t in d.tables:
  for i,row in enumerate(t.rows):
   pr=row._tr.get_or_add_trPr()
   if pr.find(qn('w:cantSplit')) is None:pr.append(OxmlElement('w:cantSplit'))
   if i==0 and pr.find(qn('w:tblHeader')) is None:pr.append(OxmlElement('w:tblHeader'))
   for cell in row.cells:
    for para in cell.paragraphs:
     if i==0 or (name=='技术质量专家审核.docx' and i<len(t.rows)-1):para.paragraph_format.keep_with_next=True
 d.save(p)

# LibreOffice layout regression: keep test evidence and sign-off table on explicit final page.
p=out/'技术质量专家审核.docx';d=Document(p)
for paragraph in d.paragraphs:
 if paragraph.text=='本轮验证' or paragraph.text.startswith('TQ-06'):paragraph.paragraph_format.page_break_before=True
d.save(p)
