# -*- coding: utf-8 -*-
"""第34章 L1 极简 Demo：TCP 四点法标定。"""
from __future__ import annotations
import sys

# 已知固定尖点（机器人基座系）
P = [0.5, 0.0, 0.3]
# 四个姿态下的法兰位姿 t（旋转假设近似单位阵+小旋转，教学简化为平移+旋转z）
TRANSLATIONS = [[0.4, 0.0, 0.25], [0.42, 0.05, 0.28],
                [0.39, -0.04, 0.27], [0.43, 0.02, 0.24]]


def rot_z(deg):
    import math
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def mat_vec(R, v):
    return [sum(R[i][j] * v[j] for j in range(3)) for i in range(3)]


def main() -> int:
    tcp = [0.0, 0.0, 0.0]
    for i, t in enumerate(TRANSLATIONS):
        R = rot_z(i * 25)
        # 解 R*tcp = P - t
        b = [P[j] - t[j] for j in range(3)]
        Rinv = [[R[0][0], R[1][0], R[2][0]],
                [R[0][1], R[1][1], R[2][1]],
                [R[0][2], R[1][2], R[2][2]]]
        est = mat_vec(Rinv, b)
        tcp = [tcp[j] + est[j] / len(TRANSLATIONS) for j in range(3)]
    print(f"标定 TCP = ({tcp[0]:.3f}, {tcp[1]:.3f}, {tcp[2]:.3f})")
    # 真值：法兰到尖点 0.1m 沿x 附近（本样例假设）
    print("验证：任意姿态下 TCP 都应指向同一固定点")
    return 0


if __name__ == "__main__":
    sys.exit(main())
