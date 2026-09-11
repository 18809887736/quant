# quant

量化交易研究与实盘系统(crypto)。起步方向:资金费率套利 + freqtrade 研究基础设施。

**先读 [CLAUDE.md](CLAUDE.md)** — 所有 AI 协作与安全约定在那里,尤其是硬性规则(dry-run 默认、密钥管理、回测前置)。

## 快速开始(在海外 VPS 上)

```bash
# 1. 把本目录同步到 VPS(如 rsync/scp)
# 2. 在 VPS 上进入项目目录
cp .env.example .env   # 填入 API key(仅 dry-run 阶段可留空)
docker compose pull
docker compose run --rm freqtrade download-data -t 15m 1h --timerange 20250101-
docker compose run --rm freqtrade backtesting --strategy ResearchStub --timerange 20250101-
```

回测报告与实验结论统一落盘到 `user_data/research/`。
