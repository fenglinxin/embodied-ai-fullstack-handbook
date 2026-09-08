# -*- coding: utf-8 -*-
"""第28章 L1 极简 Demo：摩擦系数系统辨识（一个参数的开始）。"""
from __future__ import annotations
import random, statistics, sys

TRUE_MU = 0.6


def measure(mu_true, n=50):
    rng = random.Random(0)
    data = []
    for _ in range(n):
        v = rng.uniform(0.1, 1.0)
        f = mu_true * v + rng.gauss(0, 0.02)
        data.append((v, f))
    return data


def main() -> int:
    data = measure(TRUE_MU)
    mu_est = sum(f for _, f in data) / sum(v for v, _ in data)
    print(f"辨识摩擦 μ={mu_est:.3f} (真值 {TRUE_MU})")
    print("用途：写回仿真摩擦参数（系统辨识->仿真校准的第一步）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
