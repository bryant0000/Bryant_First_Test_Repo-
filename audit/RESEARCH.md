# 本轮资料检索与版本核对（2026-10-23）

目标仍是经典 CASHFLOW 101，并以用户指定的 richdad.aiserve.top 核对网页操作。实体桌游与在线实现的差别须保留，不能将不同版次和家规混拼后称为原版。

## 已取得、可用于核对的公开资料

| 链接 | 实际读到的内容 | 可验证的范围 |
| --- | --- | --- |
| [参考站公开脚本](https://richdad.aiserve.top/js/cashflow.js?v=1.3.0) | 完整公开脚本，再抓取后 SHA-256 未变 | 回调、界面状态及配置逻辑；不能证明原站实际运行的每一帧 |
| [职业数据](https://richdad.aiserve.top/js/assets/data/careers_zh_cn.json) | 12 个职业的结构和金额 | 职业字段及数值 |
| [小买卖](https://richdad.aiserve.top/js/assets/data/smalldeal_zh_cn.json) | 55 条牌堆记录 | 股票、房产、创业及拆并股字段 |
| [大买卖](https://richdad.aiserve.top/js/assets/data/bigdeal_zh_cn.json) | 40 条牌堆记录 | 首付、总价、贷款、现金流等字段 |
| [市场卡](https://richdad.aiserve.top/js/assets/data/market_zh_cn.json) | 45 条牌堆记录 | 报价、强制事件及共享标记 |
| [额外支出](https://richdad.aiserve.top/js/assets/data/doodads_zh_cn.json) | 42 条牌堆记录 | 支出、子女条件及分期字段 |
| [快车道](https://richdad.aiserve.top/js/assets/data/fasttrack_zh_cn.json) | 41 个内容格记录；另外的特殊格由代码定义 | 梦想、事业、风险投资参数 |
| [棋盘页面模板](https://richdad.aiserve.top/js/assets/data/templates/game_screen_zh_cn.json) | 公开页面模板 | 布局配置；不是已登录原站的截图 |
| [卡片模板](https://richdad.aiserve.top/js/assets/data/templates/card_template_zh_cn.json) | 公开卡片模板 | 卡片组件配置；不是全部操作状态的运行证明 |

这批资源来自第三方参考站。当前只使用机械事实和自行编写的程序／中文说明，没有将整套原版卡牌长文与美术复制到本项目。版本、发行批次和视觉仍须单独核对。

## 已找到入口，但正文或视频尚未读到

| 链接 | 本轮结果 |
| --- | --- |
| [Rich Dad 官网](https://www.richdad.com/) | HTTP 200；首页可读。旧 `/classic-board-game-rules` 与产品路径已为 404，不能沿用此前“官网全被代理阻断”的结论。当前 cashflow 页面和站点索引请求为 403。 |
| [16 页经典手册介绍页](https://www.scribd.com/doc/78845529/Cashflow-101-Manual-Awaken-Your) | HTTP 200；未登录浏览器显示标题、页数与空白阅读区，没有读取 16 页正文。页面 AI 简介和关键词释义不作为手册原文。 |
| [2020 版说明介绍页](https://www.scribd.com/document/748086209/CASHFLOW-Board-Game-Instructions-2020) | HTTP 200；只核实入口与元数据，未读全文；即使取得也不能直接等同经典 101。 |
| [培训材料介绍页](https://www.scribd.com/document/84035868/Guide-to-Cashflow-101-Training) | HTTP 200；没有将培训材料认定为经典原版规则。 |
| [用户指定的 B 站视频](https://www.bilibili.com/video/BV1qrJBzqE7d/) | HTTP 200 的 HTML 页面壳；浏览器正文空白，视频未观看，元数据接口为 412。 |
| [BGG 文件页](https://boardgamegeek.com/boardgame/1552/cashflow-101/files) | HTTP 403；未获取文件列表。 |

Bing、Google、DuckDuckGo、YouTube 以及尝试的独立规则站请求仍在代理连接阶段返回 403。完整请求结果保存在 `source-search.json`；未访问成功的候选 URL 不会被称为“可用规则链接”。

## 实物照片排除记录

在 `zweiqin/cash-flow` 的公开仓库找到 91 张资料图片。实际查看其中的规则照片可见“财富流”、人民币、客服职业及精力规则；职业也包含 HR、产品经理等，与经典 101 的职业集不符。因此不能仅凭同属现金流沙盘，就把这些照片中的卡牌和规则导入本项目。照片路径和哈希保存在 `source-search.json`。

## 本轮已据公开代码修正并测试

- 额外支出先显示待付款卡；确认付款后扣款。不能通过结束回合跳过强制付款。
- 不足金额按 1,000 向上取整，提供贷款卡；取消返回原卡，接受后仍需在原卡确认，不自动购买或重复付款。
- 失业费用按该事件生成时的金额保存；借款增加月供后，不把本次费用重新提高。支付后才设置休整两回合并清除慈善资格。
- 税务、诉讼、离婚待确认后处理。
- 市场强制事件待确认后改变资产和收入；维修费每个事件只收一次；其他玩家的排队事件确认后不重复广播。
- 新局购买卡直接提交，去掉附加的购买二次确认和自动收据。旧规则存档的交互单独回归测试。

单元测试验证这些已实现的结果；浏览器测试验证本程序的操作路径。它们都不等于与原站、实体卡牌全部一致的验收。49 个已识别的参考界面组件仍未完成原站运行画面对照，发布门槛继续保持未通过。
