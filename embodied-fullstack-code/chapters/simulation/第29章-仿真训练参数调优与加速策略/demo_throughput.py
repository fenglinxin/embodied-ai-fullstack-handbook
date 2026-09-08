# -*- coding: utf-8 -*-
"""第29章 L1 极简 Demo：训练吞吐估算（产能=步速×并行×利用率）。"""
from __future__ import annotations
import sys


def estimate(env_speed, n_envs, idle=0.1, total_steps=10_000_000):
    rate = env_speed * n_envs * (1 - idle)
    hours = total_steps / rate / 3600
    return rate, hours


def main() -> int:
    cases = [(200, 1, 0.1), (200, 64, 0.1), (800, 256, 0.05)]
    for speed, n, idle in cases:
        rate, hours = estimate(speed, n, idle)
        print(f"单环境{speed:>4}步/s × {n:>3}环境 空闲{idle:.0%} "
              f"-> {rate:.0f}步/s，1千万步需 {hours:.1f} 小时")
    print("加速三招：更快步速/更多并行/更少空闲——先算产能再调算法")
    return 0


if __name__ == "__main__":
    sys.exit(main())
