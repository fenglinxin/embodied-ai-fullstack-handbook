# -*- coding: utf-8 -*-
"""第12章 L1 极简 Demo：失败模式聚类 -> 补采方向。

文章核心：评测失败 -> 归因 -> 补采"不会的"桶。
演示：100 次评测结果，失败样本带 场景/任务/失败模式，聚类后输出 Top 补采建议。

运行：python demo_error_mining.py
"""
from __future__ import annotations
import argparse, json, random, sys
from collections import Counter
from pathlib import Path


def simulate_eval(n: int = 100, seed: int = 3) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        scene = rng.choice(["kitchen_light", "kitchen_shadow", "warehouse"])
        task = "pick_cup" if rng.random() < 0.7 else "place_cup"
        ok = rng.random() > 0.20
        fail_mode = "" if ok else rng.choice(
            ["not_found", "grasp_slip", "place_misalign", "occluded"])
        out.append({"trial_id": f"t-{i:04d}", "scene": scene, "task": task,
                    "success": ok, "failure_mode": fail_mode})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="失败挖掘Demo")
    ap.add_argument("--out", type=Path, default=Path("eval_results.json"))
    args = ap.parse_args()
    trials = simulate_eval()
    fails = [t for t in trials if not t["success"]]
    modes = Counter(t["failure_mode"] for t in fails)
    buckets = Counter((t["scene"], t["task"]) for t in fails)
    print(f"评测 {len(trials)} 次，失败 {len(fails)} 次 "
          f"({len(fails)/len(trials):.0%})")
    print("失败模式Top:", dict(modes.most_common(3)))
    print("失败桶Top:", dict(buckets.most_common(3)))
    top = buckets.most_common(1)[0]
    print(f"建议优先补采: {top[0]} (失败 {top[1]} 次)")
    args.out.write_text(json.dumps(trials, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
