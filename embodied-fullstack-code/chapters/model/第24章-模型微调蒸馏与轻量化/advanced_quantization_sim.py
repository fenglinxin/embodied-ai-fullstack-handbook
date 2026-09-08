# -*- coding: utf-8 -*-
"""第24章 L3 高阶优化版：PTQ vs QAT 精度模拟（INT8 权重量化）。"""
from __future__ import annotations
import math, random, sys


def gen(seed=0):
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(400):
        if rng.random() < 0.5:
            X.append([rng.gauss(1.0, 0.6), rng.gauss(0.5, 0.6)])
            y.append(1)
        else:
            X.append([rng.gauss(-1.0, 0.6), rng.gauss(-0.5, 0.6)])
            y.append(-1)
    return X, y


def acc(X, y, w, b):
    ok = 0
    for xi, yi in zip(X, y):
        pred = 1 if sum(a * c for a, c in zip(xi, w)) + b >= 0 else -1
        ok += pred == yi
    return ok / len(X)


def train(X, y, w=None, b=None, iters=200, lr=0.2):
    d = len(X[0])
    if w is None:
        w = [0.0] * d
    if b is None:
        b = 0.0
    for _ in range(iters):
        gw = [0.0] * d
        gb = 0.0
        for xi, yi in zip(X, y):
            s = sum(a * c for a, c in zip(xi, w)) + b
            err = 1.0 if s * yi < 1 else 0.0      # hinge 简化
            for j in range(d):
                gw[j] += -yi * xi[j] * err
            gb += -yi * err
        for j in range(d):
            w[j] -= lr * gw[j] / len(X)
        b -= lr * gb / len(X)
    return w, b


def quantize(w, bits=8):
    qmax = 2 ** (bits - 1) - 1
    scale = max(abs(v) for v in w) / qmax
    q = [int(round(v / scale)) for v in w]
    deq = [qi * scale for qi in q]
    return q, deq, scale


def main() -> int:
    X, y = gen()
    Xtr, ytr, Xte, yte = X[:300], y[:300], X[300:], y[300:]
    wf, bf = train(Xtr, ytr, iters=300)
    acc_float = acc(Xte, yte, wf, bf)
    q, wq, scale = quantize(wf)
    acc_ptq = acc(Xte, yte, wq, bf)
    # QAT：从量化权重附近继续训练（模拟量化感知微调）
    wqat, bqat = train(Xtr, ytr, w=[v * 0.9 for v in wq], b=bf, iters=300, lr=0.05)
    _, wqat_q, _ = quantize(wqat)
    acc_qat = acc(Xte, yte, wqat_q, bqat)
    print(f"FP32  : 精度 {acc_float:.1%}")
    print(f"PTQ   : 精度 {acc_ptq:.1%} (损失 {acc_float - acc_ptq:.1%})")
    print(f"QAT   : 精度 {acc_qat:.1%} (损失 {acc_float - acc_qat:.1%})")
    print("红线纪律：掉点>1-3%时先修校准集/混合精度，再考虑QAT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
