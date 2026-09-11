# GitHub 同类项目对照(不重复造轮子)

> 落盘日期:2026-09-11
> 本仓 remote:`github.com/18809887736/quant`(private)。不是从某个公开项目 fork 来的。
> 判定依据:本仓定位(freqtrade 研究基础设施 + 费率观察器只提醒不下单 + 下一策略须先过数学门闩)+ `user_data/research/funding-verdict-2026-09-11.md`

## 结论

公开 GitHub 上同题材仓库很多,但**没有一个值得整仓当模板抄**。

基础设施已经站在官方轮子上:[freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) + [官方 docker-compose 模板](https://www.freqtrade.io/en/stable/docker_quickstart/)。不要再复制一套「完整量化系统」。

公开套利仓普遍直接下场,几乎不做「可对冲 + 0.35% 成本」这道账。那正是本仓已经算过、他们没算的部分。

## 分层对照

| 层 | 直接复用 | 不要当模板抄 |
|---|---|---|
| 交易/回测/模拟盘 | [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade)(已用) | 各类 `freqtrade-docker` 二次封装 |
| 下一策略候选(仍须先过数学门闩) | [freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies)、[NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity) | 未含手续费/未过回测的「能赚钱策略」合集 |
| 费率观察(只提醒不下单) | 告警管道可借,见下方观察器列表 | 自研第二套全市场矩阵引擎(本仓 `user_data/research/scripts/` 已有历史判定) |
| 资金费率套利执行 | — | 见下方「不要抄」列表。本仓 2026-09-11 已用全市场数据否决可对冲正向套利 |

本仓真正要自己写的只有:研究结论落盘、观察器的「极端费率 + 可对冲」双条件、以及过门闩之后的策略参数。密钥、dry-run、仓位熔断仍以 [CLAUDE.md](../CLAUDE.md) 为准。

## 基础设施(已在用,不必再找替代)

| 仓库 | 星数量级 | 用途 |
|---|---|---|
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | ~5.4 万 | 交易机器人、数据下载、回测、dry-run |
| [freqtrade/frequi](https://github.com/freqtrade/frequi) | ~1 千 | FreqUI 前端(镜像已带) |
| [freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies) | ~5 千 | 官方策略示例,下一策略候选池 |
| [iterativv/NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity) | ~3 千 | 社区高关注策略;只能当候选,须含手续费回测 |

本仓 `docker-compose.yml` 就是官方模板的薄封装(`freqtradeorg/freqtrade:stable` + `user_data` 挂载 + 回环 8080)。各类 `*-freqtrade-docker` 二次封装不要再套一层。

## 费率观察器(只提醒不下单)——可借管道

历史判定继续用本仓 `user_data/research/scripts/`(全市场 CSV + `funding_matrix.py`)。线上观察只借告警/看板,加上已定双条件:**极端费率 + 现货可对冲**,不下单。

| 项目 | 说明 |
|---|---|
| [Flotapponnier/funding-radar](https://github.com/Flotapponnier/funding-radar) | 跨所费率发散 → Telegram。可借告警管道,过滤条件要改成本仓双条件 |
| [moonzyr17/funding-rate-arb-scanner](https://github.com/moonzyr17/funding-rate-arb-scanner) | Binance/Bybit 无密钥看板,APR 未扣手续费/滑点,只作盘面,不当结论 |
| [supervik/funding-rate-arbitrage-scanner](https://github.com/supervik/funding-rate-arbitrage-scanner) | 永续-永续 / 永续-现货机会扫描 |
| [n8n 小时告警模板](https://n8n.io/workflows/16341-monitor-binance-futures-funding-rates-and-alert-telegram-hourly/) | 定时拉 Binance `premiumIndex` → Telegram。适合 VPS cron 替代方案 |

freqtrade 原生也可读 `funding_rate` 蜡烛(`@informative('1h', candle_type='funding_rate')` / `dp.funding_rate(pair)`),但这是期货策略输入,不是「全市场 + 可对冲」观察器。观察器不要塞进 `ResearchStub`。

## 资金费率套利执行——不要抄

本仓 MVP-1 已否决(可对冲口径乐观年化上限约 5%,中位事件盖不住 0.35% 成本)。下列仓库是执行器/搜索器,不是观察器,不要 fork 进本仓。

| 项目 | 说明 |
|---|---|
| [aoki-h-jp/funding-rate-arbitrage](https://github.com/aoki-h-jp/funding-rate-arbitrage) | 跨所费率套利框架 |
| [50shadesofgwei/funding-rate-arbitrage](https://github.com/50shadesofgwei/funding-rate-arbitrage) | Delta-neutral 搜索器 |
| [realm520/FreqBot](https://github.com/realm520/FreqBot) | freqtrade Docker 套件;其中 `FundingRateEnhancedStrategy` 是费率增强**方向性**交易,不是现货+永续对锁 |
| [cryptocj520/bphltaoli](https://github.com/cryptocj520/bphltaoli) | Hyperliquid × Backpack 跨所套利 |
| [R1cK-ChaN/crypto-funding-arbitrage](https://github.com/R1cK-ChaN/crypto-funding-arbitrage) | 现货多 + 永续空正向费率 |
| [IrakliXYZ/ARBOT](https://github.com/IrakliXYZ/ARBOT) | 宣传 15–30% 年化,未按本仓成本口径验证 |
| [godzilla-foundation/godzilla-community](https://github.com/godzilla-foundation/godzilla-community) | 自托管做市/费率基建,体量远超本仓需求 |

负费率借币变体仍是未测项(等 VPS 只读 key),不因上述仓库存在而开绿灯。

## 最佳做法(最小改动)

1. **基础设施继续用官方 freqtrade**,不替换本仓骨架,不改现有策略代码。
2. **观察器不要从零写矩阵**:历史判定用现有脚本;线上只借 Telegram/看板,加上「极端费率 + 现货可对冲」,不下单。
3. **下一策略**:从 `freqtrade-strategies` 里挑,先回测含手续费,报告落到 `user_data/research/`,过门闩再谈模拟盘。
4. **不要 fork 一个「完整量化平台」** 来替换本仓。要自己留的是研究结论、风控规则和观察条件,这些公开仓替不了。

## 下一步(需用户点头)

- 观察器:接现成 Telegram / n8n 模板,还是 VPS cron + 本仓脚本增量
- 下一策略:从官方策略库指定 1 个候选做数学门闩
