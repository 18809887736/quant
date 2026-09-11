# quant 项目 — AI 协作约定

本文件是所有 AI(Claude Code / Cursor / Grok)与人在本项目中共同遵守的约定。修改本文件需用户确认。

## 项目定位

- 量化交易研究与实盘系统(crypto)
- 路线:先研究回测,后小资金模拟,最后实盘(详见路线图)
- 起步主策略方向:资金费率套利(方向中性);freqtrade 作为研究/回测基础设施
- 运行环境:海外 VPS(Docker)。本 Windows 机器只做文件编辑,没有 Docker

## 硬性规则(优先级最高)

1. `config.json` 中 `dry_run` 必须为 `true`。改为 `false` 需用户在当前对话明确确认
2. 交易所 API key/secret 只允许存放于 VPS 上的 `.env` 或系统环境变量。禁止写入任何 json/py/md 文件、代码注释、聊天回复
3. 交易所 API key 只开交易权限、禁提现权限,并绑定 VPS 出口 IP 白名单
4. 任何新策略必须先跑 backtest(含手续费),报告落盘到 `user_data/research/` 后才能进入模拟盘
5. 不改写 git 历史;实验性改动开新分支,不动 main
6. 实盘阶段仓位规则:日亏 2% 熔断、账户回撤 10% 减半仓位、20% 停机——这些写进代码,不允许运行时手动豁免

## 目录结构

| 路径 | 用途 |
|------|------|
| `user_data/strategies/` | freqtrade 策略代码 |
| `user_data/config.json` | 主配置(dry-run) |
| `user_data/research/` | 回测报告、实验记录、结论(跨会话共享记忆,重要结论必须落盘到这里) |
| `user_data/data/` | 历史K线数据(git 忽略) |
| `user_data/logs/` | 运行日志(git 忽略) |
| `.env`(仅 VPS) | 交易所密钥,永不入库 |

## 常用命令(在 VPS 项目根目录)

```bash
docker compose pull                                                  # 拉镜像
docker compose run --rm freqtrade download-data -t 15m 1h --timerange 20250101-   # 下载历史数据
docker compose run --rm freqtrade backtesting --strategy ResearchStub --timerange 20250101-   # 回测
docker compose up -d                                                 # 模拟盘(dry-run)
# FreqUI 访问:本地执行 ssh -L 8080:127.0.0.1:8080 <vps> 后浏览 http://127.0.0.1:8080
```

## 已知技术边界

- freqtrade 原生不支持资金费率套利(现货多 + 永续空的双腿对锁)。它的角色是:数据管道、回测框架、模拟盘基础设施
- 资金费率套利需要自研模块(funding 费率采集 + 双腿执行 + 保证金监控),规划见 `user_data/research/funding-arb-plan.md`(待创建)

## 路线图(更新:2026-09-11)

- [x] 项目骨架(本机)
- [ ] 部署到海外 VPS,跑通首次 backtest(ResearchStub 验证管道)
- [ ] 创建 `research/funding-arb-plan.md`:费率数据源、双腿执行、爆仓边缘数学
- [ ] 资金费率套利模块开发
- [ ] 模拟盘运行 3 个月,期望值验证
- [ ] 小资金实盘($1000-2000 等值)

## 协作分工

- 本机(Claude Code / Cursor):代码编写、策略研究、文件编辑
- VPS:运行(Docker Compose 部署后通过 ssh 操作)
- 会话之间不共享记忆——所有需要延续的结论写入 `user_data/research/`
