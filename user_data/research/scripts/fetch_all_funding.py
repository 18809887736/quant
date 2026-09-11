"""全市场拉取 Binance USDT 永续资金费率历史(断点续传)。

公开 REST,无需密钥。输出 user_data/data/funding/<SYMBOL>.csv。
已有 CSV 的币从最后一期续拉。429/418 自动退避。进度打到 stdout。
"""
import csv
import json
import os
import time
import urllib.error
import urllib.request

START_MS = 1735689600000  # 2025-01-01 UTC
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "data", "funding"))


def get(url: str, tries: int = 5) -> bytes:
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "quant-research/0.1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 418):
                wait = 30 * (k + 1)
                print(f"  限频 {e.code},等 {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(5)
    raise RuntimeError(f"重试耗尽: {url}")


def last_ts(path: str) -> tuple[int, int]:
    if not os.path.exists(path):
        return START_MS, 0
    last, n = 0, 0
    with open(path, encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0].isdigit():
                last, n = max(last, int(row[0])), n + 1
    return max(last + 1, START_MS), n


def fetch_symbol(symbol: str) -> int:
    path = os.path.join(OUT_DIR, f"{symbol}.csv")
    start, existing = last_ts(path)
    new_rows, url_start = [], start
    while True:
        data = json.loads(get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&startTime={url_start}&limit=1000"))
        if not data:
            break
        new_rows.extend(data)
        if len(data) < 1000:
            break
        url_start = int(data[-1]["fundingTime"]) + 1
        time.sleep(0.25)
    if new_rows:
        write_header = existing == 0
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["fundingTime", "fundingRate"])
            w.writerows([[r["fundingTime"], r["fundingRate"]] for r in new_rows])
    return len(new_rows)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    info = json.loads(get("https://fapi.binance.com/fapi/v1/exchangeInfo"))
    symbols = [s["symbol"] for s in info["symbols"]
               if s.get("quoteAsset") == "USDT"
               and s.get("contractType") == "PERPETUAL"
               and s.get("status") == "TRADING"]
    print(f"目标 {len(symbols)} 个 USDT 永续", flush=True)
    t0, done, total_new = time.time(), 0, 0
    for sym in symbols:
        try:
            n = fetch_symbol(sym)
            total_new += n
        except Exception as e:
            print(f"  !! {sym} 失败: {e}", flush=True)
            n = -1
        done += 1
        if done % 25 == 0 or done == len(symbols):
            rate = done / (time.time() - t0)
            print(f"[{done}/{len(symbols)}] 新增 {total_new} 行, {rate:.1f} 币/秒, 预计剩余 {((len(symbols)-done)/rate/60):.1f} 分钟", flush=True)
        time.sleep(0.25)
    print("完成", flush=True)


if __name__ == "__main__":
    main()
