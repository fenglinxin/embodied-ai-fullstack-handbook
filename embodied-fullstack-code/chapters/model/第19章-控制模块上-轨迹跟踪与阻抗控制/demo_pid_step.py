# -*- coding: utf-8 -*-
"""第19章 L1 极简 Demo：PID 阶跃响应（P/PD/PID 对比）。

运行：python demo_pid_step.py
"""
from __future__ import annotations
import sys


def simulate(kp, kd=0.0, ki=0.0, target=1.0, dt=0.01, steps=500, mass=1.0):
    x, v, err_sum = 0.0, 0.0, 0.0
    peak = 0.0
    settle = None
    for i in range(steps):
        e = target - x
        err_sum += e * dt
        a = (kp * e + kd * (0 - v) + ki * err_sum) / mass
        v += a * dt
        x += v * dt
        peak = max(peak, x)
        if settle is None and i > 100 and abs(e) < 0.02:
            settle = i * dt
    return x, peak, settle


def main() -> int:
    dt = 0.01
    for name, kp, kd, ki in [("P", 30, 0, 0), ("PD", 60, 10, 0),
                             ("PID", 60, 10, 80)]:
        x, peak, settle = simulate(kp, kd, ki, dt=dt)
        overshoot = (peak - 1.0) / 1.0 * 100
        print(f"{name:<5} Kp={kp:<4} Kd={kd:<4} Ki={ki:<4} "
              f"终值={x:.3f} 超调={overshoot:.1f}% "
              f"稳定时间={settle or '>5s':>5}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
