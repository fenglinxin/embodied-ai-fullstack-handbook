# -*- coding: utf-8 -*-
"""第33章 L1 极简 Demo：里程计标定（直行/旋转）。"""
from __future__ import annotations
import sys


def main() -> int:
    # 直行标定：名义跑10m，编码器认为9.6m
    nominal = 10.0
    measured = 9.6
    scale = nominal / measured
    # 旋转标定：名义360°，实际转350°
    angle_nom = 360.0
    angle_meas = 350.0
    track_scale = angle_nom / angle_meas
    print(f"直行比例因子 {scale:.4f}（里程计=编码×比例）")
    print(f"旋转轮距修正 {track_scale:.4f}")
    print("验收：修正后直行10m误差<1-2%，旋转360°误差<2°量级")
    return 0


if __name__ == "__main__":
    sys.exit(main())
