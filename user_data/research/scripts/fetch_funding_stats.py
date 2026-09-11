"""拉取 Binance USDT-M 永续资金费率历史并计算套利关键统计。

公开 REST,无需密钥。数据落 user_data/data/funding/<SYMBOL>.csv(git 忽略)。
用法: python fetch_funding_stats.py BTCUSDT ETHUSDT
"""
import csv
import json
import os
import sys
import time
import urllib.request

BASE = "https://fapi.binance.com/fapi/v1/fundingRate"
START_MS = 1735689600000  # 2025-01-01 UTC
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "data", "funding"))


def fetch(symbol: str) -> list[dict]:
    rows, start = [], START_MS
    while True:
        url = f"{BASE}?symbol={symbol}&startTime={start}&limit=1000"
        with urllib.request.urlopen(url, timeout=30) as r:
            batch = json.loads(r.read())
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 1000:
            break
        start = int(batch[-1]["fundingTime"]) + 1
        time.sleep(0.3)
    return rows


def stats(symbol: str, rows: list[dict]) -> dict:
    rates = [float(r["fundingRate"]) for r in rows]
    ts = sorted(int(r["fundingTime"]) for r in rows)
    gaps_h = [(b - a) / 3.6e6 for a, b in zip(ts, ts[1:])]
    gap_mode = max(set(gaps_h), key=gaps_h.count) if gaps_h else 0
    n = len(rates)
    mean = sum(rates) / n
    sr = sorted(rates)
    median = sr[n // 2] if n % 2 else (sr[n // 2 - 1] + sr[n // 2]) / 2
    per_year = 365 * 24 / gap_mode if gap_mode else 0
    ths = [0.0001, 0.0003, 0.0005, 0.001]
    above = {t: sum(1 for x in rates if x >= t) / n for t in ths}
    # 滚动 N 期累计费率 >= 往返成本 0.0035 的窗口占比(持有即收所有费率的最简口径)
    rt_cost = 0.0035
    for hold in (3, 6, 14):
        roll = [sum(rates[i:i + hold]) for i in range(n - hold + 1)]
        ok = sum(1 for x in roll if x >= rt_cost)
        print(f"  持有{hold}期累计>={rt_cost:.2%}往返成本: {ok}/{len(roll)} = {ok/len(roll):.1%} 的窗口")
    return {
        "periods": n, "gap_mode_h": gap_mode,
        "mean": mean, "median": median,
        "ann_mean": mean * per_year,
        "p90": sr[int(n * 0.9)], "p99": sr[int(n * 0.99)],
        "above": above,
    }


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for symbol in sys.argv[1:] or ["BTCUSDT", "ETHUSDT"]:
        rows = fetch(symbol)
        path = os.path.join(OUT_DIR, f"{symbol}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["fundingTime", "fundingRate"])
            w.writerows([[r["fundingTime"], r["fundingRate"]] for r in rows])
        print(f"\n== {symbol}: {len(rows)} 期, 已存 {path}")
        s = stats(symbol, rows)
        print(f"  结算间隔(众数): {s['gap_mode_h']:.0f}h | 年化期数: {365*24/s['gap_mode_h']:.0f}")
        print(f"  单期均值: {s['mean']:.4%} | 中位: {s['median']:.4%} | p90: {s['p90']:.4%} | p99: {s['p99']:.4%}")
        print(f"  均值年化: {s['ann_mean']:.2%}")
        for t, frac in s["above"].items():
            print(f"  单期费率>={t:.2%} 的占比: {frac:.1%}")


if __name__ == "__main__":
    main()
