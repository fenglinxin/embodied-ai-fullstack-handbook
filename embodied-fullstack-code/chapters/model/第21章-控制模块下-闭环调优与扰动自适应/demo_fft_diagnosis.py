# -*- coding: utf-8 -*-
"""第21章 L1 极简 Demo：FFT 定位谐振峰（抖动是增益还是结构？）。"""
from __future__ import annotations
import math, random, sys

FS = 1000.0
N = 2048


def signal():
    rng = random.Random(1)
    out = []
    for i in range(N):
        t = i / FS
        v = (math.sin(2 * math.pi * 8 * t)          # 低频运动
             + 0.8 * math.sin(2 * math.pi * 47.3 * t)  # 结构谐振 47.3Hz
             + rng.gauss(0, 0.05))
        out.append(v)
    return out


def dft_mag_peak(x):
    """只扫 0~200Hz 的 DFT 找峰值（教学简化，生产用 FFT 库）。"""
    best = (0.0, 0.0)
    for k in range(int(20 * N / FS), int(200 * N / FS)):
        f = k * FS / N
        re = sum(x[n] * math.cos(2 * math.pi * k * n / N) for n in range(N))
        im = sum(x[n] * math.sin(2 * math.pi * k * n / N) for n in range(N))
        mag = math.hypot(re, im)
        if mag > best[1]:
            best = (f, mag)
    return best


def main() -> int:
    x = signal()
    f, mag = dft_mag_peak(x)
    print(f"信号主峰频率 ≈ {f:.1f} Hz (幅度 {mag:.0f})")
    print("诊断：若≈结构谐振频段 -> 加陷波滤波，而不是盲降增益")
    return 0


if __name__ == "__main__":
    sys.exit(main())
