# -*- coding: utf-8 -*-
"""第23章 L3 高阶优化版：想象式规划 + 置信度红线。"""
from __future__ import annotations
import argparse, random, sys

GOAL = 2.0
HORIZON = 5


def rollout(x0, v, noise=0.0):
    x = x0
    xs = []
    for _ in range(HORIZON):
        x += v + (random.uniform(-noise, noise) if noise else 0.0)
        xs.append(x)
    return xs


def plan():
    best = None
    v = -1.0
    while v <= 1.0 + 1e-9:
        xs = rollout(0.0, v)
        cost = abs(xs[-1] - GOAL) + 0.1 * abs(v)
        if best is None or cost < best[0]:
            best = (cost, v, xs)
        v += 0.1
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description="想象式规划(L3)")
    ap.add_argument("--use-model", action="store_true",
                    help="信任世界模型做想象式规划（默认演示置信度红线回退）")
    ap.add_argument("--noise", type=float, default=0.0,
                    help="世界模型 rollout 噪声（不确定性演示）")
    args = ap.parse_args()
    if not args.use_model or args.noise > 0.3:
        print("WM 不确定性高 -> 置信度红线：回退保守策略 v=0.2")
        print("rollout:", [round(x, 2) for x in rollout(0.0, 0.2, args.noise)])
        return 0
    cost, v, xs = plan()
    print(f"想象式规划: v={v:.1f} cost={cost:.3f}")
    print("rollout:", [round(x, 3) for x in xs])
    print("执行 v 并在执行中重规划；预测置信度下降即回退（红线）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
