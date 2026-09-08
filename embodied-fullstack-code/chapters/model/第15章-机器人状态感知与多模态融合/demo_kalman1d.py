# -*- coding: utf-8 -*-
"""第15章 L1 极简 Demo：一维卡尔曼滤波（纯标准库）。

理解状态估计核心：预测(运动模型) + 更新(测量)，噪声大也能跟住真值。

运行：python demo_kalman1d.py
"""
from __future__ import annotations
import math, random, statistics, sys


def kf1d(measurements, dt=0.1, q=0.1, r=0.5):
    x, p = 0.0, 1.0
    out = []
    for z in measurements:
        # 预测
        x = x
        p = p + q
        # 更新
        k = p / (p + r)
        x = x + k * (z - x)
        p = (1 - k) * p
        out.append(x)
    return out


def main() -> int:
    rng = random.Random(0)
    truth = [math.sin(0.5 * t) for t in range(120)]
    meas = [v + rng.gauss(0, 1.0) for v in truth]
    est = kf1d(meas)
    raw_err = statistics.mean(abs(m - t) for m, t in zip(meas, truth))
    kf_err = statistics.mean(abs(e - t) for e, t in zip(est, truth))
    print(f"原始测量误差: {raw_err:.3f}")
    print(f"卡尔曼滤波误差: {kf_err:.3f} (降噪 {raw_err / max(1e-9, kf_err):.1f}x)")
    print("原理: 预测(Q不确定) + 更新(R噪声)，输出=加权折中")
    return 0


if __name__ == "__main__":
    sys.exit(main())
