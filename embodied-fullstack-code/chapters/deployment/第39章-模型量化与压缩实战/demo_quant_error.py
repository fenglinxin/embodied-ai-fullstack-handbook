# -*- coding: utf-8 -*-
"""第39章 L1 极简 Demo：INT8/INT4 量化误差与 SNR。"""
from __future__ import annotations
import math, random, sys


def quant_err(w, bits):
    qmax = 2 ** (bits - 1) - 1
    scale = max(abs(x) for x in w) / qmax
    err = 0.0
    power = 0.0
    for x in w:
        q = int(round(x / scale))
        e = x - q * scale
        err += e * e
        power += x * x
    snr = 10 * math.log10(power / max(1e-12, err))
    return round(snr, 2)


def main() -> int:
    rng = random.Random(0)
    w = [rng.gauss(0, 0.5) for _ in range(1000)]
    print(f"FP32 权重数 {len(w)}，量化 SNR:")
    for bits in (8, 6, 4):
        print(f"  INT{bits}: {quant_err(w, bits)} dB")
    print("结论：位数越低 SNR 越低——INT4 需要离群值处理/混合精度")
    return 0


if __name__ == "__main__":
    sys.exit(main())
