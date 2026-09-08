# -*- coding: utf-8 -*-
"""第37章 L3 高阶优化版：通信抖动监控（P50/P99/超限告警）。"""
from __future__ import annotations

import argparse, json, logging, statistics, sys
from pathlib import Path

logger = logging.getLogger("jitter_monitor")
CYCLE_MS = 10.0


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    import random
    rng = random.Random(0)
    vals = [rng.gauss(1.0, 0.2) for _ in range(900)]
    vals += [rng.uniform(3, 9) for _ in range(100)]     # 尾延迟
    (root / "latency_ms.json").write_text(json.dumps(vals), encoding="utf-8")


def pct(x, p):
    x = sorted(x)
    return x[min(len(x) - 1, int(len(x) * p))]


def main() -> int:
    ap = argparse.ArgumentParser(description="抖动监控(L3)")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        vals = json.loads(args.input.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    p50 = pct(vals, 0.50)
    p99 = pct(vals, 0.99)
    mx = max(vals)
    bad = p99 > CYCLE_MS * 0.2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"p50_ms": round(p50, 3), "p99_ms": round(p99, 3), "max_ms": round(mx, 3),
           "cycle_ms": CYCLE_MS, "verdict": "jitter-ok" if not bad
           else "jitter-over-budget"}
    (args.out_dir / "jitter_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"P50={p50:.2f}ms P99={p99:.2f}ms Max={mx:.2f}ms "
          f"(周期{CYCLE_MS}ms 20%={CYCLE_MS*0.2:.1f}ms)")
    if bad:
        print("超预算 -> RT线程/锁内存/禁换页/DDS QoS 调整")
    else:
        print("抖动可接受")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
