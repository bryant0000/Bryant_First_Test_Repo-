"""Integrate independently produced domain reviews without changing game code."""
from pathlib import Path
import json, html, urllib.parse, hashlib
from collections import Counter
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/professional-delivery'
AUD=OUT/'10-专家审核与修订'
DATE='2026-11-02'
BASE='fdc8f68817c421754b94bc9b7984a53eebc28169'
NAVY='18354B'

def gather():
    rows=[]
    for name,domain in [('流程治理审核发现.json','项目治理与协作'),('玩法体验审核问题.json','玩法数值与交互视觉'),('技术质量审核问题.json','技术安全与质量运维')]:
        obj=json.loads((AUD/name).read_text())
        for f in obj.get('findings',obj.get('issues',[])):
            f=dict(f);f['domain']=domain
            f['finding']=f.get('finding',f.get('problem',f['evidence']))
            for rel in f['files']:
                assert (OUT/rel).exists(),rel
            rows.append(f)
    assert len(rows)==22
    return rows

def style_doc(d):
    for sec in d.sections:
        sec.top_margin=Inches(.72);sec.bottom_margin=Inches(.7)
        sec.left_margin=sec.right_margin=Inches(.72)
        sec.header.paragraphs[0].text='Cashflow  开发生命周期与文档质量审核'
        foot=sec.footer.paragraphs[0];foot.text='文档修订 1.1   2026-11-02   产品验收未签署    '
        fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');foot._p.append(fld)
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
        st=d.styles[name];st.font.name='Noto Sans CJK SC';st.font.color.rgb=RGBColor(0,0,0)
        st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
        st.font.size=Pt(10.5 if name=='Normal' else 25 if name=='Title' else 15 if name=='Heading 1' else 12)
        ppr=st.element.find(qn('w:pPr'))
        if ppr is not None:
            for border in list(ppr.findall(qn('w:pBdr'))):ppr.remove(border)
    d.styles['Normal'].paragraph_format.space_after=Pt(6)

def table(d,heads,rows,widths=None):
    t=d.add_table(rows=1,cols=len(heads));t.style='Table Grid';t.autofit=False
    if widths:
        for c,w in zip(t.columns,widths):c.width=Inches(w)
    for c,v in zip(t.rows[0].cells,heads):c.text=str(v)
    for row in rows:
        for c,v in zip(t.add_row().cells,row):c.text=str(v)
    for i,r in enumerate(t.rows):
        pr=r._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if i==0:pr.append(OxmlElement('w:tblHeader'))
        for j,c in enumerate(r.cells):
            if widths:c.width=Inches(widths[j])
            if i==0:
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),NAVY);c._tc.get_or_add_tcPr().append(sh)
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4)
                for run in p.runs:
                    run.font.size=Pt(9);run.font.bold=i==0
                    if i==0:run.font.color.rgb=RGBColor(255,255,255)
    d.add_paragraph('')
    return t

def sheet(w,name,heads,rows):
    s=w.create_sheet(name);s.append([name]);s.append(['2026-11-02 / v0.6.4 / 文档修订不等于产品验收']);s.append(heads)
    for row in rows:s.append(row)
    for row in s:
        for c in row:
            c.font=Font(name='Microsoft YaHei',size=10,color=NAVY)
            c.alignment=Alignment(wrap_text=True,vertical='center')
    for c in s[3]:c.fill=PatternFill('solid',fgColor=NAVY);c.font=Font(name='Microsoft YaHei',color='FFFFFF',bold=True)
    for i in range(1,s.max_column+1):s.column_dimensions[s.cell(3,i).column_letter].width=22 if i==1 else 44
    for i in range(4,s.max_row+1):s.row_dimensions[i].height=108
    s.freeze_panes='B4';s.auto_filter.ref=f'A3:{s.cell(s.max_row,s.max_column).coordinate}'
    s.print_title_rows='1:3';s.page_setup.orientation='landscape';s.page_setup.paperSize=s.PAPERSIZE_A3
    s.sheet_properties.pageSetUpPr.fitToPage=True;s.page_setup.fitToWidth=1;s.page_setup.fitToHeight=0
    return s

def main():
    findings=gather()
    d=Document();style_doc(d)
    d.add_heading('Cashflow 开发文档综合审核与修订报告',0)
    d.add_paragraph('提交给项目所有者及研发团队。本轮审查覆盖现有全部阶段的开发依据、源码对应关系和交付质量。原文档能够说明主要开发活动，但尚不足以单独指导完整交接与发布。本轮按三个独立审查任务、六类专业职责完成问题登记、文档修订和交叉复核，形成可继续执行的受控基线。')
    table(d,['控制项','本轮基线'],[['文档编号／版本','CF-REV-001 / 1.1'],['审核日期／组织','2026-11-02 / AI项目管理综合审查'],['独立领域任务','治理；玩法与体验；技术与质量。不是外部真人专家签字。'],['审查输入','原生文档提交 '+BASE+'；游戏 v0.6.4，实现指纹保留。'],['结论类别','文档补充与修订完成；实际门禁、原版核验和最终验收不追认。']],[1.5,5.2])
    d.add_heading('审核标准与结论边界',1)
    d.add_paragraph('大型团队并不共享一套完全相同的阶段名称或文件格式。可比较的是：是否先确定范围与风险，是否用原型证明可行性，设计与实现是否可追踪，独立质量检查能否否决发布，运维及退役是否有责任和记录。本轮用这些工程控制检验当前项目，采用适合小型网页游戏的裁剪，不宣称取得任何公司的私有流程、ISO认证或成熟度评级。')
    d.add_paragraph('公开资料可核验的部分包括Microsoft Xbox GDK公开样例的环境依赖与迁移说明、OpenAPI接口标准及OWASP ASVS安全验证目标。它们分别支持具体控制，并不直接证明本项目的生命周期等同任何大公司。本轮无法读取的微软SDL和Unity阶段网页保留失败记录，不作为已审阅证据。详见本轮公开依据核验.json。')
    table(d,['审核领域','审核内容','主要交付与判据'],[
        ['项目管理／制作','生命周期、裁剪、责任、门禁、变更、退役','治理补充基线；L0—L7逐门禁输入、输出、否决与例外'],
        ['策划／数值','职业卡、卡组、金额、回合状态、规则冲突','25种pending矩阵；9项既有决策；双数量上限显式区分'],
        ['交互／视觉','骰子、弹层、报表、极值及原版对照证据','视觉行为独立验收；逐截图记录视口、缩放、入口与SHA'],
        ['架构／安全','API、存档、并发、信任边界、滥用和恢复','技术安全补充；端点级契约；威胁与故障验证矩阵'],
        ['QA／质量','用例可执行性、证据日期、失败和发布门禁','本轮353单元通过；原版门禁仍阻断；未执行项明确'],
        ['发布／运维','停写恢复、回退、健康检查和用户验收','恢复作业卡；真file入口与正式签收不得由HTTP检查代替']
    ],[1.25,2.35,3.1])
    d.add_heading('开发阶段完整性与目录映射',1)
    d.add_paragraph('现有01—09目录继续作为部门资料归档，不等同于只有九个开发步骤。补充治理基线将发现、原型、生产和发布拆成L0—L7门禁；Alpha/Beta是生产与验证中的迭代成熟度。阶段允许迭代、并行和回退，但上一门禁未通过不能被文档生成行为自动追认。')
    phases=[
        ['L0 发现与可行性','01章程／治理补充；02范围','目标、参考版本、使用人群、资料可用性、风险与是否立项'],
        ['L1 预研与制作准备','02PRD/GDD；03原型与UX；04架构契约','离线与在线技术预研、受控需求设计、数值与素材、关键假设'],
        ['L2 纵向切片','05计划／交接；06验证','完整回合、买卖、报表、保存，以及取消、刷新和断线贯通'],
        ['L3 Alpha功能完整','05计划／交接；02—04规格','任务依赖、代码评审、内容导入、功能闭环与缺陷记录'],
        ['L4 Beta质量与表现','06测试；10专项验证矩阵','集成、兼容、极值、安全、恢复和已批准NFR的执行证据'],
        ['L5 发布候选与UAT','07发布；08验收','冻结候选SHA、真file入口、在线回退、用户和规则签收'],
        ['L6 上线与持续维护','07运维；09变更','监测、事故、根因、回归、版本维护和例外期限'],
        ['L7 退役与归档','01治理补充；09维护','停服通知、存档处理、备份保留、数据删除及关闭责任']
    ]
    table(d,['受控阶段','原生文件归属','门禁核心'],phases,[1.35,2.25,3.1])
    d.add_heading('领域问题整改与复核规则',1)
    d.add_paragraph('本轮登记22项问题，治理7项、玩法体验7项、技术质量8项。问题分成文档缺口与产品执行缺口：前者通过补充具体规格、原文同步及交叉引用整改；后者记录现状、实施任务与复验条件。安全加固、真实设备测试、原版资料和人的批准不能仅靠修改文档关闭。逐项证据及路径保存在综合审核问题与修订追踪.xlsx和三份领域审核JSON。')
    for title,ids,text in [
        ('治理修订','GOV-01—07','补足发现／预研／Alpha／Beta／退役，门禁否决、例外到期、角色任命、CCB、滚动估算和部门拒收；同步修订章程、实施计划、UAT及维护规范。角色任命、估算承诺和正式批准仍需实际负责人员完成。'),
        ('玩法与体验修订','GX-01—07','GDD同步全部9项既有决策；PRD明确参考表单买入上限99,999与引擎直接buy上限1,000,000的差异；新增25种pending转换、9类边界组和6类视觉证据组。骰子、原版数值和页面完全一致性的证据尚未齐全，不能判通过。'),
        ('技术与质量修订','TQ-01—08','补充内存与磁盘非事务写入的真实失败语义、转发头信任、限流与TTL缺口、活性／就绪区别、技术用例和停写恢复作业卡；修订技术、测试与发布原文。当前存在的实现风险仍交研发落实，禁止写成已加固。')]:
        d.add_heading(title,2);d.add_paragraph(ids+'。'+text)
    d.add_heading('本轮执行证据和未通过范围',1)
    table(d,['检查','本轮结果','使用限制'],[
        ['游戏单元测试','npm test：353通过，0失败，0跳过','完整日志在10/证据；不代表浏览器／设备／容量通过'],
        ['原版全等门禁','本轮执行，按预期BLOCKED；运行画面0/49','失败保持真实，未降低发布门禁'],
        ['领域覆盖','25个pending、9项决策、9组边界、6组视觉证据','源码静态覆盖；不能替代状态运行与原版对照'],
        ['原生文件与版式','本轮校验结果见本轮综合复核结果.json','需文件结构、PDF、链接与校验和均通过才打包'],
        ['历史浏览器证据','既有v0.6.4报告保留','27套历史检查未在本轮重新执行'],
        ['正式UAT与放行','未签署；不自动追认','规则、产品、QA和实际使用者按职责签收']
    ],[1.35,2.25,3.1])
    d.add_heading('修订控制与部门使用顺序',1)
    d.add_paragraph('本轮日期为2026-11-02，文档修订1.1；游戏版本仍为v0.6.4。旧报告、旧测试日期和源数据快照保留为历史证据，新增综合报告及专项规格控制本轮新增条款。原文中的新增1.1章节将读者引向具体规格。若仍出现正文与台账冲突，应登记问题并阻断相关门禁，不能自行选择有利版本。')
    table(d,['接收方','开始使用的依据','下一步必须形成的证据'],[
        ['产品／规则负责人','PRD、GDD、规则主表与GX矩阵','参考版本、9项既有决策及数量上限裁决；批准的验收范围'],
        ['UX／前端','UX规格、pending矩阵、视觉证据组','逐页截图与几何记录，真实file缩放／字体／骰子／报表回归'],
        ['后端／安全／运维','技术规格、OpenAPI、TQ矩阵','失败恢复、安全加固、并发与回退演练的日志和结果'],
        ['QA／项目管理','门禁台账、用例、综合问题追踪','逐项复验、遗留风险、冻结候选SHA及放行决定'],
        ['用户／最终批准人','UAT方案和签收工作簿','真实使用结果、拒收／有条件通过／通过及签署时间']
    ],[1.35,2.25,3.1])
    d.add_paragraph('审核结论：当前资料已经补充为可指导后续研发和验收的受控文档基线。本轮交付不构成游戏上线批准或原版完全一致性证明。对于仍需实施、测量和人为裁决的事项，文档已经给出接收角色、验证方法和门禁，不作虚假完成记录。')
    d.save(AUD/'综合审核与修订报告.docx')
    wb=Workbook();wb.remove(wb.active)
    sheet(wb,'阅读与结论',['项目','结论'],[['审核组织','三个独立AI领域审查任务覆盖六类职责；综合复核不冒充真人签署'],['文档／游戏基线','文档1.1 / 2026-11-02；游戏v0.6.4未修改'],['问题数',22],['文档修订状态','原文同步与专项规格已修订；文件检查见本轮综合复核结果'],['执行状态','正式人员、规则裁决、安全加固、现场设备及用户验收待执行'],['评审批准','未签署']])
    sheet(wb,'问题整改追踪',['ID','领域','级别','发现／现状','证据','文档修订','修订状态','实现／验证状态','受影响文件'],[[f['id'],f['domain'],f['severity'],f['finding'],f['evidence'],f['fix'],'已修订；综合复核见同目录结果JSON',f['execution_status'],'\n'.join(f['files'])] for f in findings])
    sheet(wb,'阶段与文档',['阶段','目录与文件','门禁核心'],phases)
    sheet(wb,'复核和关闭规则',['对象','关闭条件','不得替代的证据'],[['文档问题','原文及引用更新；核对实际代码；原生结构和版式通过','未来实现不写成已实现'],['规则分歧','规则负责人确定参考版本；观察/资料证据；变更影响评审','生成文档不代替裁决'],['实现风险','研发变更、评审、对应回归和失败分支实测通过','风险登记不代替代码修复'],['用户问题','真file入口与在线入口按批准环境复现并验收','路由模拟不代替双击操作'],['正式发布','原版目标与候选SHA匹配；批准人签署；无阻断项','单元全部通过不代替发布门禁']])
    sheet(wb,'交叉复核记录',['复核领域','检查点','证据／范围','结论'],[['治理→质量','放行与真实入口、UAT未签保持一致','治理基线、技术恢复、UAT新增章节','文档一致；放行未批准'],['玩法→技术','两种证券数量上限不可宣称统一','GX-07及技术矩阵关联','已登记，待规则/API裁决'],['技术→治理','高风险不得由项目管理单独豁免','安全/恢复与门禁例外规则','实施及批准仍阻断'],['总集成','主目录、原文、专项规格和数据契约','链接/文件/决策/公式/源码指纹复核','以本轮综合复核结果为准']])
    wb.save(AUD/'综合审核问题与修订追踪.xlsx')
    (AUD/'综合审核问题.json').write_text(json.dumps({'date':DATE,'review_type':'AI分领域审核与综合复核','baseline':BASE,'findings':findings,'product_release_approved':False},ensure_ascii=False,indent=2))
    sources=Path('/tmp/cf-review-sources.json')
    if sources.exists():
        data=json.loads(sources.read_text())
        for x in data:
            x['excerpt']=x.get('excerpt','')[:1300]
            x['use']='仅使用实际读取的公开说明；不是企业私有流程或完整合规评估。' if x['status']==200 else '未读取，不作为结论依据。'
        (AUD/'本轮公开依据核验.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    # Correct the old overview rather than leave a known five-versus-nine decision conflict.
    p=OUT/'00-阅读入口与复核/交付依据与阶段复核报告.docx';old=Document(p)
    for para in old.paragraphs:
        if 'DEC-01至DEC-05' in para.text:para.text=para.text.replace('DEC-01至DEC-05','DEC-01至DEC-09及本轮GX-07数量上限分歧')
    for para in list(old.paragraphs):
        if para.text=='2026-11-02综合审核修订' or para.text.startswith('本文2026-10-27原始交付记录作为历史保留。'):
            para._element.getparent().remove(para._element)
    for para in old.paragraphs:
        if para.text.startswith(('蓝色章节对应开发依据','2026-11-02文档修订1.1：')):
            para.text='2026-11-02文档修订1.1：优先阅读10目录综合审核报告及专项规格。353项单元测试本轮重跑通过，原版全等仍阻断；27套浏览器检查保持历史日期，正式UAT未签署。原始资料按下列基线保留，待审批与待实测不得作为发布通过结论。'
        if para.text.startswith('变更登记：文档版本1.0'):
            para.text=para.text.replace('文档版本1.0；本次建立','初版1.0建立').replace('批准栏不得由生成工具自动填写。','批准栏不得由生成工具自动填写。本轮1.1修订详见10目录综合问题追踪与专项规格。')
    old.save(p)
    (OUT/'00-阅读入口与复核/阅读与复现说明.txt').write_text('Cashflow 开发文档审核修订包\n文档修订1.1 / 2026-11-02；游戏实现仍为v0.6.4。\n\n先解压，打开 开始阅读.html，优先阅读10目录的综合审核与修订报告.pdf。\n包含完整原生Word、Excel、PDF、既有PPT、图示、HTML设计原型及JSON技术契约；不是游戏安装包。\n\n三个独立AI审查任务覆盖治理、玩法/体验、技术/质量六类职责，未冒充外部真人签字。22项问题逐项追踪；原文已同步修订。\n本轮单元353通过；原版全等门禁仍BLOCKED。未执行的安全、容量、真file设备和UAT不填通过。\n\n既有2026-10-27报告与日志保留为历史证据，2026-11-02审核条款以10目录综合报告及专项规格为准。\n本轮复现：review_governance.py、review_game_ux.py、review_tech_quality.py分别生成领域修订；integrate_expert_review.py集成；统一Office导出/工作簿重算后执行check_delivery.py与check_expert_review.py；最后生成文件校验清单及ZIP。生成后应重新渲染并核验。\n')
    print('Integrated 22 findings, revised overview, report and native audit workbook.')

if __name__=='__main__':main()
