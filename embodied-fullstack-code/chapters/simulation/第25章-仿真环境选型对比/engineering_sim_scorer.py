# -*- coding: utf-8 -*-
"""第25章 L2 工业工程版：仿真器需求打分（能力画像可编辑）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("sim_scorer")

PROFILES = {
    "mujoco":   {"physics": 9, "render": 4, "rl": 8, "sensor": 5, "ecosystem": 8},
    "isaac":    {"physics": 8, "render": 9, "rl": 9, "sensor": 9, "ecosystem": 7},
    "gazebo":   {"physics": 6, "render": 5, "rl": 4, "sensor": 8, "ecosystem": 9},
    "webots":   {"physics": 6, "render": 6, "rl": 5, "sensor": 8, "ecosystem": 6},
    "genesis":  {"physics": 7, "render": 7, "rl": 8, "sensor": 6, "ecosystem": 5},
}
WEIGHTS = {"physics": 0.30, "render": 0.25, "rl": 0.20,
           "sensor": 0.15, "ecosystem": 0.10}


def main() -> int:
    ap = argparse.ArgumentParser(description="仿真器打分(工程版)")
    ap.add_argument("--task", choices=["rl", "vision_manip", "nav",
                                       "dexterous"], default="vision_manip")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    # 按任务覆盖默认权重
    w = dict(WEIGHTS)
    if args.task == "rl":
        w.update({"physics": 0.35, "render": 0.10, "rl": 0.35,
                  "sensor": 0.10, "ecosystem": 0.10})
    elif args.task == "nav":
        w.update({"physics": 0.20, "render": 0.20, "rl": 0.15,
                  "sensor": 0.20, "ecosystem": 0.25})
    elif args.task == "dexterous":
        w.update({"physics": 0.45, "render": 0.15, "rl": 0.20,
                  "sensor": 0.10, "ecosystem": 0.10})
    rows = []
    for name, p in PROFILES.items():
        score = sum(p[k] * w[k] for k in w)
        rows.append({"name": name, "score": round(score, 2), "profile": p})
    rows.sort(key=lambda r: -r["score"])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "sim_score.json").write_text(
        json.dumps({"task": args.task, "weights": w, "ranking": rows},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"任务: {args.task}")
    for r in rows:
        print(f"  {r['name']:<8} {r['score']:.2f}")
    print(f"推荐: {rows[0]['name']} (请按官方最新文档复核画像后再拍板)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
