"""全市场资金费率事件期望矩阵(MVP-1 生死判据)。

对 data/funding/*.csv 逐币计算事件(费率上穿进场门槛,持有到 <0.01% 退场,
含触发期),输出 成本×门槛 的期望矩阵与分币明细。
用法: python funding_matrix.py [--detail]
"""
import csv
import glob
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data", "funding"))
SPOT_CACHE = os.path.join(DATA, "_spot_symbols.json")
FLOOR = 0.0001      # 退场线:低于即离场
COSTS = [0.0035, 0.002, 0.0015]
ENTERS = [0.001, 0.0015, 0.002]


def spot_symbols() -> set[str]:
    if os.path.exists(SPOT_CACHE):
        return set(json.load(open(SPOT_CACHE, encoding="utf-8")))
    with urllib.request.urlopen("https://api.binance.com/api/v3/exchangeInfo", timeout=60) as r:
        syms = {s["symbol"] for s in json.loads(r.read())["symbols"]
                if s.get("status") == "TRADING" and s.get("quoteAsset") == "USDT"}
    json.dump(sorted(syms), open(SPOT_CACHE, "w", encoding="utf-8"))
    return syms


def hedgeable(perp: str, spot: set[str]) -> bool:
    """永续能否在同所用现货对冲;1000X 永续对应 X 现货。"""
    base = perp[:-4]
    if base.startswith("1000"):
        base = base[4:]
    return (base + "USDT") in spot


def episodes(rates: list[float], enter: float) -> list[float]:
    eps, i = [], 0
    while i < len(rates):
        if rates[i] >= enter:
            acc = 0.0
            while i < len(rates) and rates[i] >= FLOOR:
                acc += rates[i]
                i += 1
            eps.append(acc)
        else:
            i += 1
    return eps


def main() -> None:
    detail = "--detail" in sys.argv
    spot = spot_symbols()
    per_symbol = {}
    t_min, t_max = 2**62, 0
    for path in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
        sym = os.path.basename(path)[:-4]
        rates = []
        for r in csv.DictReader(open(path, encoding="utf-8")):
            try:
                rates.append(float(r["fundingRate"]))
            except (TypeError, ValueError):
                continue  # 并发写入产生的撕裂行
        if len(rates) < 30:
            continue
        per_symbol[sym] = {e: episodes(rates, e) for e in ENTERS}
        ts = [int(r["fundingTime"]) for r in csv.DictReader(open(path, encoding="utf-8")) if r.get("fundingTime", "").isdigit()]
        if ts:
            t_min, t_max = min(t_min, min(ts)), max(t_max, max(ts))

    print(f"参与统计币数(>=30 期): {len(per_symbol)},其中现货可对冲: {sum(1 for s in per_symbol if hedgeable(s, spot))}\n")
    for label, use_hedge in (("全部永续", False), ("仅现货可对冲", True)):
        pool = {s: d for s, d in per_symbol.items() if hedgeable(s, spot) == use_hedge or not use_hedge}
        print(f"=== {label}({len(pool)} 币) ===")
        print(f"{'进场门槛':>8} | {'事件数':>6} | {'单事件均值':>10} | {'中位':>8} | ", end="")
        print(" | ".join(f">={c:.2%}成本占比" for c in COSTS))
        print("-" * 90)
        for e in ENTERS:
            all_eps = [x for sym in pool for x in pool[sym][e]]
            if not all_eps:
                print(f"{e:>8.2%} | {0:>6} | -")
                continue
            s = sorted(all_eps)
            n = len(s)
            med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
            cov = " | ".join(f"{sum(1 for x in all_eps if x >= c)/n:>12.1%}" for c in COSTS)
            print(f"{e:>8.2%} | {n:>6} | {sum(all_eps)/n:>10.3%} | {med:>8.3%} | {cov}")

        # 净期望(均值-成本)矩阵
        print("\n净期望矩阵(单事件均值 - 成本,负=亏):")
        hdr = "门槛\\成本"
        print(f"{hdr:>10} | " + " | ".join(f"{c:>8.2%}" for c in COSTS))
        for e in ENTERS:
            all_eps = [x for sym in pool for x in pool[sym][e]]
            avg = sum(all_eps) / len(all_eps) if all_eps else 0
            print(f"{e:>10.2%} | " + " | ".join(f"{avg-c:>+8.3%}" for c in COSTS))

        # 年化粗估:事件频率 × 单事件净期望(按全部资金单事件滚动部署的口径)
        months = max((t_max - t_min) / 2.63e9, 0.1)
        print(f"\n年化粗估(数据跨度 {months:.0f} 个月;假设资金逐事件滚动,单事件满仓):")
        for e in ENTERS:
            all_eps = [x for sym in pool for x in pool[sym][e]]
            n = len(all_eps)
            freq = n / months
            avg = sum(all_eps) / n if n else 0
            print(f"  门槛{e:.2%}: {freq:.1f} 事件/月 | " + " | ".join(f"成本{c:.2%}:年化 {freq*12*(avg-c):+.1%}" for c in COSTS))
        print()

        if detail and use_hedge:
            print("单币明细(仅可对冲,事件数>=3,按 0.10% 门槛累计费率降序,前 30):")
            rows = []
            for sym, d in pool.items():
                eps = d[0.001]
                if len(eps) >= 3:
                    rows.append((sum(eps) / len(eps), sym, len(eps), max(eps)))
            rows.sort(reverse=True)
            for avg, sym, n, mx in rows[:30]:
                print(f"  {sym:16s} 事件{n:3d} 均值{avg:.3%} 最大{mx:.3%}")
            print()


if __name__ == "__main__":
    main()
