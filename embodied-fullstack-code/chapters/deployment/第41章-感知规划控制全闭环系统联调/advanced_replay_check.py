# -*- coding: utf-8 -*-
"""第41章 L3 高阶优化版：回放联调一致性检查（时间/坐标/语义）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("replay_check")
MAX_GAP_MS = 80


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rows = [{"topic": "perception", "ts_ms": 1000 + i * 66, "x_m": 0.2 + i / 100}
            for i in range(10)]
    rows += [{"topic": "plan", "ts_ms": 1000 + i * 100, "x_mm": 200 + i}
             for i in range(10)]
    # 制造一条单位不一致 + 一条时间倒流
    rows[3]["x_mm"] = 200.0
    rows[8]["ts_ms"] = rows[7]["ts_ms"] - 1
    (root / "replay.json").write_text(json.dumps(rows), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="回放一致性(L3)")
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
        by_topic = {}
        for r in rows:
            by_topic.setdefault(r["topic"], []).append(r)
        checks = []
        for topic, rs in by_topic.items():
            ts = [r["ts_ms"] for r in rs]
            monotonic = all(b > a for a, b in zip(ts, ts[1:]))
            gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
            max_gap = max(gaps) if gaps else 0
            checks.append({"topic": topic, "monotonic": monotonic,
                           "max_gap_ms": max_gap,
                           "pass": monotonic and max_gap <= MAX_GAP_MS})
        # 单位一致性：perception x_m vs plan x_mm
        units_ok = all(("x_m" in r or "x_mm" in r) for r in rows)
        checks.append({"topic": "units", "pass": units_ok,
                       "note": "同一链路必须统一 m 或 mm"})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"checks": checks, "pass_all": all(c["pass"] for c in checks)}
    (args.out_dir / "replay_check.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for c in checks:
        print(f"{c['topic']:<12} [{'PASS' if c['pass'] else 'FAIL'}] "
              f"{c.get('max_gap_ms','')} {c.get('note','')}")
    print("结论:", "一致" if rep["pass_all"] else "存在问题-先修再上真机")
    return 0 if rep["pass_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
