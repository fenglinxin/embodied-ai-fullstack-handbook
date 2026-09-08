# -*- coding: utf-8 -*-
"""第21章 L2 工业工程版：负载参数辨识（最小二乘，前馈更新用）。

模型：tau = m*a + fric*sign(v) + b*v + c
用 采集(a,v,tau) 最小二乘解 [m,fric,b,c]；
辨识结果可自动更新重力/惯量前馈（文章"负载辨识自动化"）。

运行：python engineering_load_identification.py
"""
from __future__ import annotations
import math, random, sys


def gen_data(m_true=2.0, fric_true=1.5, b_true=0.3, n=300):
    rng = random.Random(0)
    a, v, tau = [], [], []
    for i in range(n):
        ai = rng.uniform(-2, 2)
        vi = rng.uniform(-1, 1)
        t = m_true * ai + fric_true * math.copysign(1, vi if vi else 1)             + b_true * vi + rng.gauss(0, 0.2)
        a.append(ai); v.append(vi); tau.append(t)
    return a, v, tau


def solve(X, y):
    """正规方程解线性最小二乘（4x4，Gauss 消元）。"""
    n = len(X[0])
    A = [[sum(X[k][i] * X[k][j] for k in range(len(y)))
          for j in range(n)] for i in range(n)]
    bvec = [sum(X[k][i] * y[k] for k in range(len(y))) for i in range(n)]
    # 高斯消元
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        A[col], A[piv] = A[piv], A[col]
        bvec[col], bvec[piv] = bvec[piv], bvec[col]
        for r in range(col + 1, n):
            f = A[r][col] / A[col][col]
            for c in range(col, n):
                A[r][c] -= f * A[col][c]
            bvec[r] -= f * bvec[col]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = bvec[r] - sum(A[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / A[r][r]
    return x


def main() -> int:
    a, v, tau = gen_data()
    X = [[ai, math.copysign(1, vi if vi else 1), vi, 1.0]
         for ai, vi in zip(a, v)]
    m, fric, b, c = solve(X, tau)
    print(f"辨识结果: 惯量m={m:.3f} (真2.0) 摩擦={fric:.3f} (真1.5) "
          f"阻尼b={b:.3f} (真0.3) 偏置c={c:.3f}")
    print("用法：把 m/fric 写回重力前馈与摩擦前馈，换夹具后自动重辨识")
    return 0


if __name__ == "__main__":
    sys.exit(main())
