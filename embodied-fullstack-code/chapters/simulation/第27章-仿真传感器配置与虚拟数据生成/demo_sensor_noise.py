# -*- coding: utf-8 -*-
"""第27章 L1 极简 Demo：传感器噪声合成（相机/深度）。"""
from __future__ import annotations
import math, random, statistics, sys

SIZE = 32


def base_image():
    return [[120 + 40 * math.sin(x / 4.0) for x in range(SIZE)]
            for _ in range(SIZE)]


def add_noise(img, sigma, impulse=0.01):
    rng = random.Random(1)
    out = []
    for row in img:
        nr = []
        for v in row:
            if rng.random() < impulse:
                v = rng.choice([0, 255])
            else:
                v = v + int(rng.gauss(0, sigma))
            nr.append(max(0, min(255, v)))
        out.append(nr)
    return out


def mean_signal(img):
    vals = [v for row in img for v in row]
    return statistics.mean(vals)


def main() -> int:
    clean = base_image()
    noisy = add_noise(clean, 12)
    print(f"干净图均值 {mean_signal(clean):.1f} 噪声图均值 "
          f"{mean_signal(noisy):.1f} (含椒盐)")
    print("真实相机噪声=高斯+坏点+曝光波动；仿真不配噪声=模型只会'干净世界'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
