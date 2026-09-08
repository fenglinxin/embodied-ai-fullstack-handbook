# -*- coding: utf-8 -*-
"""第24章 L1 极简 Demo：知识蒸馏（学生学老师的软标签）。

老师=真实分布，学生=logits；loss=CE(soft label)（+可加KL）。

运行：python demo_distill.py
"""
from __future__ import annotations
import math, sys

P = [0.1, 0.7, 0.2]          # 老师分布（软标签）


def softmax(z):
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]


def ce(p, q):
    return -sum(pi * math.log(qi + 1e-9) for pi, qi in zip(p, q))


def main() -> int:
    z = [0.0, 0.0, 0.0]
    lr = 0.3
    for it in range(300):
        q = softmax(z)
        loss = ce(P, q)
        # 梯度：dL/dz_i = q_i - p_i
        for i in range(3):
            z[i] -= lr * (q[i] - P[i])
    q = softmax(z)
    print(f"蒸馏后学生分布: {[round(x, 3) for x in q]}")
    print(f"老师分布: {P}")
    print("误差(MAE):", round(sum(abs(a - b) for a, b in zip(q, P)) / 3, 4))
    return 0


if __name__ == "__main__":
    sys.exit(main())
