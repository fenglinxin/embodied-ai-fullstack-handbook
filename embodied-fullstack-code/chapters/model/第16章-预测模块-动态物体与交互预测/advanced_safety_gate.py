# -*- coding: utf-8 -*-
"""第16章 L3 高阶优化版：预测-规划安全门（概率分级决策）。

输入：ego_path.json [[x,y],...] + predictions.json（多假设轨迹带概率）
输出：每条假设最小间距、碰撞概率合计、动作决策：
  continue / slow(减速) / stop(让行)——对应文章"多假设+概率分级"。

运行：
  python engineering_prediction_eval.py --make-sample sample
  python advanced_safety_gate.py --ego sample/ego_path.json \
      --pred sample/predictions.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path

logger = logging.getLogger("safety_gate")
SAFE_DIST = 0.5
SLOW_PROB = 0.2
STOP_PROB = 0.5


def min_dist_over_time(path_a, traj_b):
    """两轨迹逐时刻最小欧氏距离（不足时刻截断）。"""
    n = min(len(path_a), len(traj_b))
    return min(math.dist(path_a[i], traj_b[i]) for i in range(n))


def main() -> int:
    ap = argparse.ArgumentParser(description="预测安全门(L3)")
    ap.add_argument("--ego", required=True, type=Path)
    ap.add_argument("--pred", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        ego = json.loads(args.ego.read_text(encoding="utf-8"))
        cases = json.loads(args.pred.read_text(encoding="utf-8"))
        collision_prob = 0.0
        rows = []
        for c in cases:
            for h in c["hypotheses"]:
                d = min_dist_over_time(ego, h["traj"])
                rows.append({"case": c.get("case"), "prob": h["prob"],
                             "min_dist": round(d, 3),
                             "collide": d < SAFE_DIST})
                if d < SAFE_DIST:
                    collision_prob += h["prob"]
        collision_prob = round(collision_prob, 3)
        if collision_prob >= STOP_PROB:
            action = "stop"
        elif collision_prob >= SLOW_PROB:
            action = "slow"
        else:
            action = "continue"
        rep = {"hypotheses": rows, "collision_probability": collision_prob,
               "safe_dist": SAFE_DIST, "action": action,
               "note": "概率>0.5停、0.2-0.5减速、否则继续并保持可重规划"}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "safety_gate.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"hyp prob={r['prob']} min_dist={r['min_dist']}m "
              f"collide={r['collide']}")
    print(f"碰撞概率合计 {collision_prob} -> 动作: {action}")
    print(f"报告: {(args.out_dir / 'safety_gate.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
