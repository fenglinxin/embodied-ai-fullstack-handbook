# -*- coding: utf-8 -*-
"""第35章 L1 极简 Demo：相机带宽预算。"""
from __future__ import annotations
import sys


def mbps(w, h, fps, bits=8):
    return w * h * fps * bits / 1e6


def main() -> int:
    cams = [("rgb_1080p30", 1920, 1080, 30), ("depth_720p15", 1280, 720, 15)]
    total = 0
    for name, w, h, fps in cams:
        b = mbps(w, h, fps)
        total += b
        print(f"{name}: {b:.0f} Mbps")
    print(f"合计 {total:.0f} Mbps -> USB3(≈4000Mbps有效) 余量 "
          f"{100*(1-total/3200):.0f}%")
    print("纪律：带宽占用 ≤70-80%，多相机要分控制器/GMSL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
