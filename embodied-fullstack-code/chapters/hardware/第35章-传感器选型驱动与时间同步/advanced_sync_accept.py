# -*- coding: utf-8 -*-
"""第35章 L3 高阶优化版：事件法同步验收（偏差统计+常数补偿）。"""
from __future__ import annotations

import argparse, json, logging, statistics, sys
from pathlib import Path

logger = logging.getLogger("sync_accept")
MAX_JITTER_MS = 2.0


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    base = 1000.0
    events = {"rgb": [], "depth": [], "joint": []}
    for i in range(20):
        t = base + i * 500.0
        events["rgb"].append(t + 8 + (i % 3) * 0.3)     # 固定~8ms+抖动
        events["depth"].append(t + 12 + (i % 2) * 0.6)
        events["joint"].append(t + 1.0)
    (root / "events.json").write_text(json.dumps(events), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="同步验收(L3)")
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
        ev = json.loads(args.input.read_text(encoding="utf-8"))
        ref = ev["joint"]
        rows = []
        for name, ts in ev.items():
            if name == "joint":
                continue
            # 与参考最近事件差
            diffs = []
            for t in ts:
                d = min(abs(t - r) for r in ref)
                diffs.append(d)
            med = statistics.median(diffs)
            resid = [abs(d - med) for d in diffs]
            rows.append({"channel": name, "median_offset_ms": round(med, 2),
                         "max_jitter_ms": round(max(resid), 2),
                         "pass": max(resid) <= MAX_JITTER_MS,
                         "compensation_ms": round(med, 2)})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"rows": rows, "pass_all": all(r["pass"] for r in rows),
           "note": "常数偏差可写进对齐配置补偿；抖动超标查触发线/PTP"}
    (args.out_dir / "sync_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['channel']:<8} 偏差中位 {r['median_offset_ms']}ms "
              f"抖动 {r['max_jitter_ms']}ms "
              f"[{'PASS' if r['pass'] else 'FAIL'}]")
    print("结论:", "同步达标" if rep["pass_all"] else "查触发/PTP")
    return 0 if rep["pass_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
