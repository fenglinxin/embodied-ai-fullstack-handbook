# -*- coding: utf-8 -*-
"""第19章 L2 工业工程版：前馈+反馈轨迹跟踪仿真（1D 质量系统）。"""
from __future__ import annotations
import math, sys


def reference(t, T=2.0, target=1.0):
    """梯形速度参考（加速0.4s-匀速-减速），返回位置/速度/加速度。"""
    # 简化：三次多项式平滑轨迹
    tc = min(1.0, t / T)
    s = tc * tc * (3 - 2 * tc)          # smoothstep
    return target * s, target * 6 * tc * (1 - tc) / T, 0.0


def simulate(kp=200.0, kd=20.0, mass=2.0, dt=0.001, T=2.0):
    x, v = 0.0, 0.0
    errs = []
    for i in range(int(T / dt) + 1):
        t = i * dt
        xr, vr, ar = reference(t, T=T)
        e, ed = xr - x, vr - v
        ff = mass * 0.0        # 简化：平滑轨迹无解析加速度
        u = kp * e + kd * ed + ff
        a = u / mass
        v += a * dt
        x += v * dt
        errs.append(abs(e))
    return max(errs), sum(errs) / len(errs)


def main() -> int:
    dt = 0.001
    for kp, kd in [(50, 5), (200, 20), (800, 60)]:
        mx, avg = simulate(kp, kd, dt=dt)
        print(f"Kp={kp:<4} Kd={kd:<4} 最大误差 {mx:.4f} m "
              f"平均误差 {avg:.4f} m")
    print("原则：高速段靠前馈/带宽，不靠硬加P；到位后检查阻尼。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
