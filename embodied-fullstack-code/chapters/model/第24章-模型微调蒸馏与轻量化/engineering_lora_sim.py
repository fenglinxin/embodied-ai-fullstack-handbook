# -*- coding: utf-8 -*-
"""第24章 L2 工业工程版：全参微调 vs 低秩适配（LoRA 教学实现）。"""
from __future__ import annotations
import random, sys


def gen(n=200, seed=1):
    rng = random.Random(seed)
    X = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    y = [sum(x) + rng.gauss(0, 0.1) for x in X]     # w_true=ones
    return X, y


def mse(X, y, w):
    s = 0.0
    for xi, yi in zip(X, y):
        e = sum(a * b for a, b in zip(xi, w)) - yi
        s += e * e
    return s / len(y)


def least_squares(X, y):
    d = len(X[0]); n = len(X)
    A = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(d)]
         for i in range(d)]
    b = [sum(X[k][i] * y[k] for k in range(n)) for i in range(d)]
    for c in range(d):
        p = max(range(c, d), key=lambda r: abs(A[r][c]))
        A[c], A[p] = A[p], A[c]; b[c], b[p] = b[p], b[c]
        for r in range(c + 1, d):
            f = A[r][c] / A[c][c]
            for j in range(c, d):
                A[r][j] -= f * A[c][j]
            b[r] -= f * b[c]
    w = [0.0] * d
    for r in range(d - 1, -1, -1):
        w[r] = (b[r] - sum(A[r][j] * w[j] for j in range(r + 1, d))) / A[r][r]
    return w


def low_rank_fit(X, y, w0, rank=2):
    """低秩适配（教学版）：固定投影 U(d x rank)，闭式求解 v。
    冻结主干 w0，只训练 rank 个参数。"""
    d = len(w0)
    rng = random.Random(0)
    U = [[rng.gauss(0, 1.0) for _ in range(rank)] for _ in range(d)]
    Z = [[sum(xi[j] * U[j][k] for j in range(d)) for k in range(rank)]
         for xi in X]
    res = [yi - sum(w0[j] * xi[j] for j in range(d)) for xi, yi in zip(X, y)]
    v = least_squares(Z, res)
    w = [w0[j] + sum(U[j][k] * v[k] for k in range(rank)) for j in range(d)]
    return w, rank


def main() -> int:
    X, y = gen()
    cut = 150
    Xtr, ytr, Xte, yte = X[:cut], y[:cut], X[cut:], y[cut:]
    w_full = least_squares(Xtr, ytr)
    full_err = mse(Xte, yte, w_full)
    rng = random.Random(3)
    w0 = [rng.gauss(0, 0.3) for _ in range(8)]
    print(f"全参微调: 可训练参数量 8, 测试MSE {full_err:.4f}")
    for rank in (2, 4, 8):
        w_adapt, _ = low_rank_fit(Xtr, ytr, w0, rank=rank)
        err = mse(Xte, yte, w_adapt)
        print(f"低秩适配 rank={rank}: 只训练 {rank} 个参数, 测试MSE {err:.4f}")
    print("结论：冻结主干+低秩增量，rank 越高越接近全参（容量-成本权衡）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
