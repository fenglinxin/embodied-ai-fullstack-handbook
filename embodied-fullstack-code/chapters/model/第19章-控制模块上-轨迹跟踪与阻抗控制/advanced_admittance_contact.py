# -*- coding: utf-8 -*-
"""第19章 L3 高阶优化版：导纳控制接触仿真（刚度整定 + 力监控）。"""
from __future__ import annotations
import sys

WALL_X = 0.30
WALL_K = 5000.0
F_DES = 5.0
DT = 0.001


def run(ka=800.0, vel=0.1):
    x = 0.0
    max_f = 0.0
    for i in range(5000):
        xd = vel * i * DT
        if xd > WALL_X:
            # 环境接触力（按期望穿透估计）
            f_raw = WALL_K * (xd - WALL_X)
            # 导纳修正：力偏差 -> 目标位置回退
            dx = (F_DES - f_raw) / ka
            xd = xd + dx
            f = max(0.0, WALL_K * (xd - WALL_X))
            x = WALL_X + f / WALL_K if f > 0 else xd
        else:
            f = 0.0
            x = xd
        max_f = max(max_f, f)
    return max_f


def main() -> int:
    for ka in (200.0, 800.0, 3000.0, 10000.0):
        max_f = run(ka=ka)
        print(f"导纳刚度 Ka={ka:<7} 峰值接触力 {max_f:.2f} N (目标 {F_DES} N)")
    print("Ka 太小=发飘退很多；Ka 太大接近硬碰；按任务在 0.8-3x 环境刚度取中。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
