# v0.6.6 本轮复核（2026-11-04）

唯一规范来源： https://cfclassic.richdad.com/ 。辅助站点和实体版不作为另一个主目标。
本轮370项单元测试（358游戏+12验收门禁）及31组浏览器回归通过，详见 validation-latest.json；它们不构成完整官网等同验收。在线/离线标题提示局部与历史原图逐像素比较最大通道误差1。标题版本现随构建更新。

review-official-classic-2026-11-04/保存本轮资料来源分级、网络诊断、标题前后截图和局部比较。历史官网截图版本1.0.0(0.0.8)，不能冒充官网当前版本。运行环境代理仍CONNECT403，配置草稿已包含域名。official-classic-target.json中335项一级核验目录仍未形成完整原版→设计→实现→比较链，49整页封板0；不是功能完成率。release:check应继续返回失败，release_allowed=false。

联机回归首次遇到共享卡队列时脚本超时；修正测试先处理合法共享卡，再断言借款金额。首轮失败日志与修正后通过日志均保留。真实file://双击入口尚未在本环境验证；离线证据使用HTTP提供的全内嵌页面及断网/拒绝API检查。

以下保留历史版本审计说明，历史哈希和结论仅对应当时版本。

# 原版一致性验收：当前未通过

当前开发版本 v0.6.5。以下原站对局观察来自历史记录；本轮原站访问被代理403拒绝，没有新增登录后观察。对照对象为 https://cfclassic.richdad.com/ 的经典在线游戏。通过自己创建的私人房间正常操作，已观察医生、护士、机械师、工程师、卡车司机、清洁工和律师；没有使用账户凭据、进入他人房间、修改原站状态或读取未来牌序。中文参考站只能观察登录首页；没有登录后的页面证据。

当前登记 49 类运行界面，其中 40 类有正常操作观察，0 类被标记为全部分支、文字与显示完全一致。观察与实现验收是两件事，不能因自动测试通过而升级为完整原版一致。具体证据见 [official-runtime.json](official-runtime.json) 和 [reference-coverage.json](reference-coverage.json)。

12 职业、182 张牌及 41 个梦想／投资记录的机械字段有独立夹具。原站公开资源与固定镜像比较为 9 个 JSON 和 29 个选定回调函数体一致。这些比较不证明全部卡牌长文、实体版次或页面一致。

本轮对齐与截图边界见 [ui-restudy-2026-10-26.md](ui-restudy-2026-10-26.md)。选定棋盘、木纹、纸张、退出托盘、财务数字、操作按钮、建房／等待方框区域有独立原站截图摘要；标题大图保留最多 1 个色阶的透明合成容差。均不包含完整中文／英文文本等价声明。

测试证据见 [validation-latest.json](validation-latest.json) 及 [interface-verification-2026-10-26.json](interface-verification-2026-10-26.json)。离线单文件在禁止所有其他网页／接口请求的情况下验证流程；环境浏览器策略禁止 file://，不能声称已自动验证双击文件入口。

```sh
npm test
npm run test:reference:browser
npm run test:online:browser
npm run test:standalone:browser
npm run test:layout:browser
npm run test:visual:browser
npm run test:cards:browser
npm run test:terminal:browser
npm run test:sound:browser
npm run test:entry:browser
npm run test:entry-art:browser
npm run test:observer:browser
npm run release:check
```

未完成：经典实体规则书版本核验、未观察分支、全部画面和卡牌文字逐项比较、B 站视频内容与中文站登录后页面核验。v0.6.5官网兼容模式按历史原站观察，将金币资产包出售总到账改为600；旧规则模式仍6000，实体版规则仍待核验。联机 90 秒暂离阈值是本程序的实现选择，也未证明与原站相同。

`release:check` 继续阻止完整一致性发布。阶段构建不能被表述为通过了这项验收。

本地页面修复：v0.6.3 的 353 项单元测试及 24 套浏览器检查通过。完整包 index.html 改为资源内嵌入口；报表开合重画、互斥页面、中文标题及可见骰子的回归见 [display-fixes-v0.6.3.json](display-fixes-v0.6.3.json) 和 [display-fixes-v0.6.3.md](display-fixes-v0.6.3.md)。

v0.6.4 根据用户附件修正股票金额、快车道异步报表回退和遮挡，并引入原始木纹骰子。实现与验收边界见 [attachment-fixes-v0.6.4.md](attachment-fixes-v0.6.4.md)，当前模板单骰锚点已经核对；多骰页面原版运行坐标仍非完整核验。
