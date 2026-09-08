# -*- coding: utf-8 -*-
"""第25章 L1 极简 Demo：物理步长与穿透（为什么接触仿真要小步长）。"""
from __future__ import annotations
import sys

G = 9.81
H = 0.05       # 小球离地 5cm


def drop(dt):
    y, v = H, 0.0
    penetration = 0.0
    steps = 0
    while steps < 200:
        v += G * dt
        y -= v * dt
        if y <= 0:
            penetration = -y
            break
        steps += 1
    return steps, penetration


def main() -> int:
    for dt in (0.1, 0.02, 0.005):
        steps, pen = drop(dt)
        print(f"dt={dt:<5} 落地步数 {steps:<4} 穿透 {pen*1000:.2f} mm")
    print("结论：接触任务步长要小（1ms级），否则穿透/能量错误=真机白练")
    return 0


if __name__ == "__main__":
    sys.exit(main())
