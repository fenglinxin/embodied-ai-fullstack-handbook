# -*- coding: utf-8 -*-
"""第10章 L1 极简 Demo：观测扰动增强（保真度优先，纯标准库）。

对灰度矩阵做 亮度/对比度/高斯噪声 三类 L1 增强，
并校验"身份不变"：增强前后中心物体区域平均亮度变化有界。
动作通道绝不扰动（文章红线：共享物理规律）。

运行：python demo_augment.py
"""
from __future__ import annotations

import random
import statistics
import sys


def fake_image(size: int = 32) -> list[list[int]]:
    rng = random.Random(0)
    img = [[rng.randint(0, 60) for _ in range(size)] for _ in range(size)]
    for y in range(12, 20):                      # 中心高亮物体
        for x in range(12, 20):
            img[y][x] = 200
    return img


def brightness(img: list[list[int]], delta: int) -> list[list[int]]:
    return [[max(0, min(255, v + delta)) for v in row] for row in img]


def contrast(img: list[list[int]], factor: float) -> list[list[int]]:
    n = len(img) * len(img[0])
    mean = sum(sum(r) for r in img) / n
    return [[max(0, min(255, int(mean + (v - mean) * factor)))
             for v in row] for row in img]


def noise(img: list[list[int]], sigma: float) -> list[list[int]]:
    rng = random.Random(7)
    return [[max(0, min(255, v + int(rng.gauss(0, sigma)))) for v in row]
            for row in img]


def center_mean(img: list[list[int]]) -> float:
    vals = [img[y][x] for y in range(12, 20) for x in range(12, 20)]
    return statistics.mean(vals)


def main() -> int:
    img = fake_image()
    base = center_mean(img)
    ops = {"brightness+20": brightness(img, 20),
           "contrast*1.2": contrast(img, 1.2),
           "noise_sigma5": noise(img, 5)}
    print(f"{'增强':<14}{'中心均值变化':<14}{'身份边界'}")
    for name, out in ops.items():
        delta = center_mean(out) - base
        ok = abs(delta) < 60                      # 物体不应扰动到不可识别
        print(f"{name:<14}{delta:+.1f}          {'OK' if ok else '越界!'}")
    print("动作通道不参与扰动（物理语义红线）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
