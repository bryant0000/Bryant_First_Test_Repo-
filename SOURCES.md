# CASHFLOW 101 资料来源与核验

用户要求以 CASHFLOW 101 经典版为目标。以下区分实际读到的资料与尚未取得的资料；未把第三方实现当作官方规则书。

## 已实际取得的组件数据

**主要来源：[dadish/cashflow](https://github.com/dadish/cashflow/tree/2edcdbc15785ac2141f3d1fe544b14e0de2775b4)**，固定提交 `2edcdbc15785ac2141f3d1fe544b14e0de2775b4`。

该仓库的 `scripts/downloadAsset.js` 声明从以下 Rich Dad 在线游戏资源路径下载文件：

`https://www.richdad.com/cmsscripts/custom/cashflowjs/`

本轮通过 GitHub 取得镜像文件，并查看了其中的棋盘图及版面坐标。没有成功从 richdad.com 独立重新下载，故准确描述为“保留官方在线版路径来源的第三方镜像”，不是“已核验实体经典版扫描”。

| 文件 | 已提取的规则事实 |
| --- | --- |
| `src/assets/data/careers.json` | 12 种职业，工资、税金、每项月供、储蓄、育儿费用和完整负债本金 |
| `smalldeal.json` | 55 张：证券、股票拆并、房产、土地、贵金属、创业及亲属借款 |
| `bigdeal.json` | 40 张：多户住宅、公寓楼、企业、合伙、土地等 |
| `market.json` | 45 张：按单位报价、最低户数、创业增收、维修、合伙强制收购、法拍等 |
| `doodads.json` | 42 张：日常支出、有子女条件、按人数计算、电视和游艇分期 |
| `fasttrack.json` | 23 个梦想与 18 个投资格的成本、现金流和骰子检定条件 |
| `templates/game_screen.json` | 24 格内圈和 48 格外圈的格子种类、索引及位置；剩余外圈为慈善、3 个现金流日和 3 个风险格 |
| `vocab_en_us.json` | 开局现金含储蓄、失业取消慈善、银行千元单位及 10% 月支出、清算按首付一半、特定债务减半、外圈慈善 100,000 与 1–3 骰等机械规则 |

只提取数值、类别、数量及位置事实；中文名称和规则说明重新撰写。没有复制该仓库的游戏代码、卡牌长篇文案、棋盘图、字体或音频。页面 SVG 棋盘由本项目生成。文件 SHA-256 记录在 `reference-manifest.json`，生成器是 `scripts/build-reference-data.py`，输出为 `reference-data.js`，运行游戏不需要研究仓库或 Python 依赖。

## 交叉参照及排除的数据

1. [Sleighs/CashFlowJs](https://github.com/Sleighs/CashFlowJs/tree/c081d2becf200bba80166fa75fd1c4628c532db4)，MIT，第三方经典版改编。其 `scenarioChoices` 与主要来源的多项旧职业数据一致，但缺教育贷款；航空驾驶员月供也存在差异。没有整表照搬，也未把其 README 明确标为新模式的内容加入经典规则。
2. [NathanStrutz/cashflow-balance-sheet](https://github.com/NathanStrutz/cashflow-balance-sheet)，财务报表辅助工具。`YourBuyout.vue` 和 fasttrack store 可交叉支持被动收入取整至最近千元后乘 100 的公式。
3. [step-8/cashflow-holmes](https://github.com/step-8/cashflow-holmes/tree/dd96fc843bc8fb5001a2021d1969e51186a00fce)，另一个多人实现。职业数据与所需旧版差异很大，未将其税金、育儿费用等混入主表。它的内圈部分特殊格与在线版不同，因此本作的格序统一采用主要镜像，不混拼。
4. [nkjsy/cashflow101 的规则研究](https://github.com/nkjsy/cashflow101/blob/main/docs/cashflow-101-rules-research.md)，提供手册、财务表及规则争议的检索线索；这只是二手研究，未照抄其自定义经济系统或职业。
5. 搜索到的其他中文实现有人民币本土化、年度结算、信用贷月息 1% 等改动，均排除。

## 规则书和用户参考站访问结果

- 搜索取得经典手册线索：[Cashflow 101 Manual: Awaken Your Financial Genius](https://www.scribd.com/doc/78845529/Cashflow-101-Manual-Awaken-Your)。当前访问被代理以 403 拒绝，没有读到该扫描的正文。
- [Rich Dad 经典规则页](https://www.richdad.com/classic-board-game-rules)：403，未获得正文。
- 用户的 B 站视频及 `richdad.aiserve.top`：均为代理连接阶段 403，未观看/读取，不将其列为已核验来源。
- GitHub 搜索页和仓库读取实际成功，通过这些渠道自行找到了上述可用资料。

## 实现中的明确兼容处理与剩余差异

- 开局：工资减支出，再加一次性储蓄。职业可以手动选，也可随机发放；当前同屏轮序由玩家 1 开始，没有模拟掷骰争先。
- 发薪：逐格自动领取，没有桌游中的“忘记向银行领取则失去收入”。
- 出圈：严格被动收入大于支出；被动收入四舍五入至千元后乘 100。默认领取一次入场收入；是否立即发放的经典实体版依据仍不完整。
- 外圈：按所取在线版资料的 48 格，不再使用之前虚构的 32 格。慈善用该在线版固定 100,000 的永久 1–3 骰规则，不混用内圈的 3 回合规则。
- 并股：保留半股，不猜测奇数股如何取整。
- 亲属四年期赊购市场卡（`market.44`）：没有可核实的四年与棋盘回合对应规则，本次保留卡牌索引、展示提议但不成交；这是未完整实现的一张卡，而不是伪造一个必然回款规则。
- 多人：支持 1–6 人同屏轮流、共享牌堆、公开报价响应、共享拆股及企业成长、双方确认的资产交易。未实现远程联机、购买权转卖、向其他玩家放贷及梦想涨价干扰。
- 破产：负现金触发补款；同时为负现金流时进入调整流程，可半首付清算及特定债务减半。未自动推断无法偿付者出局，玩家可明确宣布破产。

因此目前是**有来源支撑的经典机制兼容版本**，不是宣称所有实体发行版、规则和美术逐项完全相同的官方产品。当前无需用户代为搜集资料；继续取得可公开读取的经典版原件后，可针对上述差异继续核验。
