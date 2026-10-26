# 原版一致性验收：当前未通过

当前开发版本 v0.6.4。对照对象为 https://cfclassic.richdad.com/ 的经典在线游戏。通过自己创建的私人房间正常操作，已观察医生、护士、机械师、工程师、卡车司机、清洁工和律师；没有使用账户凭据、进入他人房间、修改原站状态或读取未来牌序。中文参考站只能观察登录首页；没有登录后的页面证据。

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

未完成：经典实体规则书版本核验、未观察分支、全部画面和卡牌文字逐项比较、B 站视频内容与中文站登录后页面核验。官网黄金出售观察到错误金额，本程序按 10 × 600 = 6,000 结算，与官网实际入账 600 存在已知差异。联机 90 秒暂离阈值是本程序的实现选择，也未证明与原站相同。

`release:check` 继续阻止完整一致性发布。阶段构建不能被表述为通过了这项验收。

本地页面修复：v0.6.3 的 353 项单元测试及 24 套浏览器检查通过。完整包 index.html 改为资源内嵌入口；报表开合重画、互斥页面、中文标题及可见骰子的回归见 [display-fixes-v0.6.3.json](display-fixes-v0.6.3.json) 和 [display-fixes-v0.6.3.md](display-fixes-v0.6.3.md)。

v0.6.4 根据用户附件修正股票金额、快车道异步报表回退和遮挡，并引入原始木纹骰子。实现与验收边界见 [attachment-fixes-v0.6.4.md](attachment-fixes-v0.6.4.md)，当前模板单骰锚点已经核对；多骰页面原版运行坐标仍非完整核验。
