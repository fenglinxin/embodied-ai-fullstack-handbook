# -*- coding: utf-8 -*-
"""第28章 L2 工业工程版：域随机化鲁棒性对比（基线 vs DR 策略）。"""
from __future__ import annotations
import random, sys

NOMINAL = 0.6
DR_LO, DR_HI = 0.3, 0.9
N = 2000


def main() -> int:
    rng = random.Random(1)
    baseline_ok = dr_ok = 0
    for _ in range(N):
        mu = rng.uniform(0.2, 1.0)       # 真实世界参数分布
        if abs(mu - NOMINAL) < 0.1:      # 基线只在标称附近能成功
            baseline_ok += 1
        if DR_LO <= mu <= DR_HI:         # DR 策略在训练区间内成功
            dr_ok += 1
    print(f"基线策略(仅标称μ={NOMINAL})成功率 {baseline_ok / N:.0%}")
    print(f"DR策略(μ∈[{DR_LO},{DR_HI}]) 成功率 {dr_ok / N:.0%}")
    print("DR 把'参数点'变成'参数区间鲁棒'；中心先做系统辨识(L1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
