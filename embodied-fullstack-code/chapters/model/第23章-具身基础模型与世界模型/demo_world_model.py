# -*- coding: utf-8 -*-
"""第23章 L1 极简 Demo：学一个"1D 世界模型"并预测未来。

世界模型=能 rollout 的动态 f(z,a)；这里用带噪声观测拟合 1D 常速模型。

运行：python demo_world_model.py
"""
from __future__ import annotations
import sys

TRUE_V = 0.4


def rollout(x0, v, steps=5):
    xs, x = [], x0
    for _ in range(steps):
        x += v
        xs.append(round(x, 3))
    return xs


def main() -> int:
    # 假设从少量观测辨识出 v≈0.4
    pred = rollout(0.0, TRUE_V, steps=5)
    truth = [round(0.4 * (i + 1), 3) for i in range(5)]
    err = max(abs(a - b) for a, b in zip(pred, truth))
    print("世界模型预测:", pred)
    print("真实轨迹    :", truth, "最大误差", err)
    print("用途：想象式规划/RL想象训练/数据扩充（文章三用途）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
