# -*- coding: utf-8 -*-
"""第20章 L1 极简 Demo：握持力与摩擦（为什么"夹多紧"是算出来的）。"""
from __future__ import annotations
import sys

G = 9.81


def min_grip(mass_kg, mu):
    """两指对称握持：2*mu*N >= m*g。"""
    return mass_kg * G / (2 * mu)


def main() -> int:
    for mass in (0.1, 0.5):
        for mu in (0.3, 0.8):
            n = min_grip(mass, mu)
            print(f"质量{mass:.1f}kg 摩擦μ={mu}: 最小握力 {n:.2f} N")
    print("经验：目标握力=最小握力×(1.5~2)安全系数，并留滑觉增力余量")
    return 0


if __name__ == "__main__":
    sys.exit(main())
