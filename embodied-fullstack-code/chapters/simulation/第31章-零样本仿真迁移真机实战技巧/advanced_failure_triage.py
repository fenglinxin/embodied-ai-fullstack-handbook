# -*- coding: utf-8 -*-
"""第31章 L3 高阶优化版：首跑失败归因与决策（修仿真/修适配/转微调）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path
from collections import Counter

logger = logging.getLogger("triage")

RULE = [
    ("sync|timing|frame", "fix-adapter", "链路/时间同步问题：修适配层"),
    ("perception|camera|light|detect", "fix-adapter", "感知链路问题：查相机/光照/标定"),
    ("slip|contact|grasp|dynamics", "fix-sim", "物理差距：回仿真补辨识/DR"),
    ("latency|delay", "fix-adapter", "延迟问题：查执行链路预算"),
]


def classify(mode: str):
    for key, cat, advice in RULE:
        if any(k in mode for k in key.split("|")):
            return cat, advice
    return "retrain-finetune", "失败模式不明确/全场景差距大：转真机微调"


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    fails = [{"scene": "a", "phase": "grasp", "mode": "grasp_slip"},
             {"scene": "b", "phase": "perception", "mode": "detect_miss_light"},
             {"scene": "c", "phase": "control", "mode": "action_latency_80ms"},
             {"scene": "d", "phase": "unknown", "mode": "random_fail"}]
    (root / "failures.json").write_text(json.dumps(fails), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="失败归因(L3)")
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
        fails = json.loads(args.input.read_text(encoding="utf-8"))
        cats = Counter()
        rows = []
        for f in fails:
            cat, advice = classify((f.get("mode") or "").lower())
            cats[cat] += 1
            rows.append({**f, "category": cat, "advice": advice})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"rows": rows, "category_counts": dict(cats)}
    (args.out_dir / "triage_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['scene']}/{r['mode']:<18} -> {r['category']} | {r['advice']}")
    print("汇总:", dict(cats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
