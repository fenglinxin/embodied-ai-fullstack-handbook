# -*- coding: utf-8 -*-
"""第17章 L3 高阶优化版：DWA 局部规划仿真（速度采样+避障+卡死检测）。

机制：对 (v,w) 网格采样 -> 前向仿真 -> 按 朝向/障碍距离/速度 打分
      -> 执行最优；连续无进展触发 replan_trigger（文章"卡死重规划"）。

运行：python advanced_dwa_sim.py
"""
from __future__ import annotations
import math, sys

GOAL = (5.0, 0.0)
OBS = [(2.0, 0.0, 0.5), (3.0, -0.4, 0.3)]
DT, PRED_T = 0.1, 1.0
V_MAX, W_MAX = 1.0, 2.0
V_RES, W_RES = 0.1, 0.4


def sim_traj(x, y, th, v, w):
    pts = []
    for _ in range(int(PRED_T / DT)):
        x += v * math.cos(th) * DT
        y += v * math.sin(th) * DT
        th += w * DT
        pts.append((x, y))
    return pts


def clearance(pts):
    d = 1e9
    for px, py in pts:
        for ox, oy, r in OBS:
            d = min(d, math.hypot(px - ox, py - oy) - r)
    return max(0.0, d)


def heading_cost(pts, gx, gy):
    x, y = pts[-1]
    angle = math.atan2(gy - y, gx - x)
    # 用上一朝向近似（简化）
    return abs(angle)


def step(x, y, th, v, w):
    for _ in range(1):
        x += v * math.cos(th) * DT
        y += v * math.sin(th) * DT
        th += w * DT
    return x, y, th


def main() -> int:
    x, y, th = 0.0, 0.0, 0.0
    stuck = 0
    replan = False
    steps = 0
    while math.hypot(GOAL[0] - x, GOAL[1] - y) > 0.1 and steps < 200:
        best = None
        v = 0.0
        while v <= V_MAX:
            w = -W_MAX
            while w <= W_MAX:
                pts = sim_traj(x, y, th, v, w)
                cl = clearance(pts)
                if cl < 0.1:            # 碰撞轨迹直接淘汰
                    w += W_RES
                    continue
                score = -heading_cost(pts, *GOAL) + 0.5 * min(cl, 1.0) + 0.1 * v
                if best is None or score > best[0]:
                    best = (score, v, w)
                w += W_RES
            v += V_RES
        if best is None:
            print("无可避障速度 -> stop 并触发重规划")
            replan = True
            break
        _, v, w = best
        x, y, th = step(x, y, th, v, w)
        steps += 1
        if v < 0.05:
            stuck += 1
        else:
            stuck = 0
        if stuck >= 5:
            replan = True
            print(f"step {steps}: 连续无进展 -> 触发全局重规划")
            break
    print(f"终点 ({x:.2f},{y:.2f}) 目标 {GOAL} 步数 {steps} "
          f"replan={replan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
