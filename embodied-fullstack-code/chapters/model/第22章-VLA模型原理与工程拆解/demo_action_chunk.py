# -*- coding: utf-8 -*-
"""第22章 L1 极简 Demo：动作 token 化 + 分块（chunking）。

演示：连续动作 -> 量化 token -> 自回归还原 -> 一次预测 N 步（动作块）。

运行：python demo_action_chunk.py
"""
from __future__ import annotations
import sys

BIN = 0.02                       # 2cm 量化桶


def to_tokens(actions):
    toks = []
    for a in actions:
        toks.append(int(round(a / BIN)))
    return toks


def to_actions(tokens):
    return [t * BIN for t in tokens]


def main() -> int:
    chunk = [0.02, 0.04, 0.061, 0.08, 0.099]
    toks = to_tokens(chunk)
    rec = to_actions(toks)
    err = max(abs(a - b) for a, b in zip(chunk, rec))
    print("动作块:", chunk)
    print("token :", toks)
    print("还原  :", [round(x, 3) for x in rec], "最大量化误差", err)
    print("执行模型：模型每 0.5s 推一次 5 步动作块，控制层滚动执行=动作分块")
    return 0


if __name__ == "__main__":
    sys.exit(main())
