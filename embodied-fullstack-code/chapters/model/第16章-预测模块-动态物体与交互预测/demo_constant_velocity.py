# -*- coding: utf-8 -*-
"""第16章 L1 极简 Demo：匀速外推基线 vs 保持静止（预测的"地板"）。

运行：python demo_constant_velocity.py
"""
from __future__ import annotations
import math, sys

HORIZON = 1.0
DT = 0.2


def truth_traj():
    """真值：先匀速再转弯（模拟行人转向，基线会暴露误差）。"""
    out, x, y, vx, vy = [], 0.0, 0.0, 1.0, 0.0
    for i in range(int(HORIZON / DT) + 1):
        t = i * DT
        if t >= 0.6:                       # 0.6s 后转向
            vx, vy = 0.3, 0.9
        x += vx * DT
        y += vy * DT
        out.append([round(x, 3), round(y, 3)])
    return out


def predict_cv(history):
    vx = (history[-1][0] - history[-2][0]) / DT
    vy = (history[-1][1] - history[-2][1]) / DT
    out = []
    for i in range(1, int(HORIZON / DT) + 1):
        out.append([history[-1][0] + vx * DT * i,
                    history[-1][1] + vy * DT * i])
    return out


def predict_stay(history):
    return [history[-1][:] for _ in range(int(HORIZON / DT))]


def main() -> int:
    history = truth_traj()[:2]              # 只用前两帧做预测
    truth = truth_traj()[1:]
    cv = predict_cv(history)
    stay = predict_stay(history)
    err_cv = sum(math.dist(a, b) for a, b in zip(cv, truth)) / len(truth)
    err_stay = sum(math.dist(a, b) for a, b in zip(stay, truth)) / len(truth)
    print(f"真值末端 {truth[-1]}  匀速末端 {cv[-1]}  静止末端 {stay[-1]}")
    print(f"匀速基线平均误差 {err_cv:.3f} m  (行人 0.6s 后转向仍可跟住前半段)")
    print(f"保持静止误差 {err_stay:.3f} m —— 任何预测模型必须先赢过 CV 基线")
    return 0


if __name__ == "__main__":
    sys.exit(main())
