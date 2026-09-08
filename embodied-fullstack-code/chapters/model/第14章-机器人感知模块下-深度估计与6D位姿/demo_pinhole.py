# -*- coding: utf-8 -*-
"""第14章 L1 极简 Demo：针孔投影与深度反投影（纯标准库）。

理解 2D<->3D 的最小数学：
  pixel -> camera ray (用深度反投影)
  3D -> pixel (投影)
实际相机还要畸变校正/外参变换（第2/3章标定提供）。

运行：python demo_pinhole.py
"""
from __future__ import annotations
import math, sys

FX = FY = 500.0
CX = CY = 320.0


def project(x, y, z):
    """相机系 3D -> 像素(未考虑畸变)。"""
    if z <= 0:
        return None
    return (CX + FX * x / z, CY + FY * y / z)


def backproject(u, v, depth):
    """像素+深度 -> 相机系 3D。"""
    return ((u - CX) * depth / FX,
            (v - CY) * depth / FY,
            depth)


def main() -> int:
    pts3 = [(0.1, 0.05, 0.8), (-0.2, 0.1, 1.2)]
    for x, y, z in pts3:
        u, v = project(x, y, z)
        xr, yr, zr = backproject(u, v, z)
        err = math.hypot(x - xr, y - yr)
        print(f"3D({x},{y},{z}) -> 像素({u:.1f},{v:.1f}) "
              f"-> 反投影误差 {err:.2e} m")
    print("结论: 深度+内参 = 每个像素都有 3D 坐标（第3章标定把外参接上后到机器人系）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
