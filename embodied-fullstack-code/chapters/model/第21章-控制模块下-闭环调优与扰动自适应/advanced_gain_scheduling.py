# -*- coding: utf-8 -*-
"""第21章 L3 高阶优化版：按负载档位的增益自适应调度（PD+稳定约束）。

保持 wn/zeta 不变：Kp=m*wn^2, Kd=m*2*zeta*wn
负载越重增益越高但系统动态特性一致（安全前提下的性能自适应）。

运行：python advanced_gain_scheduling.py
"""
from __future__ import annotations
import sys

WN, ZETA = 10.0, 1.0
DT = 0.001


def sim(m, kp, kd, steps=3000):
    x, v = 0.0, 1.0        # 扰动：初速脉冲
    max_x = 0.0
    for _ in range(steps):
        u = -kp * x - kd * v
        a = u / m
        v += a * DT
        x += v * DT
        max_x = max(max_x, abs(x))
    return max_x


def main() -> int:
    for m in (0.5, 2.0, 5.0):
        kp = m * WN * WN
        kd = m * 2 * ZETA * WN
        peak = sim(m, kp, kd)
        print(f"负载 {m:>3} kg: Kp={kp:>6.1f} Kd={kd:>5.1f} "
              f"脉冲扰动最大位移 {peak:.3f} m")
    print("调度规则：负载档(辨识结果,见L2) -> 查表增益，始终留稳定裕量")
    return 0


if __name__ == "__main__":
    sys.exit(main())
