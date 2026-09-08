# -*- coding: utf-8 -*-
"""第38章 L3 高阶优化版：端侧长跑稳定性（显存泄漏/P99漂移）。"""
from __future__ import annotations

import argparse, json, logging, statistics, sys
from pathlib import Path

logger = logging.getLogger("soak")
LEAK_MA = 0.02


def make_sample(root: Path, leak: bool = True) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    mem = 400
    base_lat = 11.0
    for i in range(120):
        mem += (0.5 if leak else 0.0)
        p99 = base_lat + (0.03 * i if leak else 0.0)
        rows.append({"min": i, "mem_mb": round(mem, 1),
                     "p99_ms": round(p99, 2), "temp_c": 45 + i * 0.05})
    (root / "soak.json").write_text(json.dumps(rows), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="长跑稳定性(L3)")
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
        rows = json.loads(args.input.read_text(encoding="utf-8"))
        n = len(rows)
        warm = rows[n // 4:]                     # 预热后
        mem_start = warm[0]["mem_mb"]
        mem_end = warm[-1]["mem_mb"]
        drift = (mem_end - mem_start) / max(1, len(warm))
        p99_first = statistics.mean(r["p99_ms"] for r in warm[:10])
        p99_last = statistics.mean(r["p99_ms"] for r in warm[-10:])
        leak = drift > LEAK_MA
        lat_drift = p99_last - p99_first > 2.0
        rep = {"mem_drift_mb_per_min": round(drift, 3), "leak": leak,
               "p99_drift_ms": round(p99_last - p99_first, 2),
               "latency_drift": lat_drift,
               "verdict": "leak-or-drift" if leak or lat_drift else "stable"}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "soak_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"显存漂移 {drift:.2f}MB/分 -> {'泄漏!' if leak else 'OK'}")
    print(f"P99 漂移 {p99_last - p99_first:.2f}ms "
          f"-> {'漂移!' if lat_drift else 'OK'}")
    print("判定:", rep["verdict"])
    return 1 if rep["verdict"] != "stable" else 0


if __name__ == "__main__":
    sys.exit(main())
