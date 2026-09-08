# -*- coding: utf-8 -*-
"""第29章 L2 工业工程版：小网格超参搜索（固定预算 + 成功率决策）。"""
from __future__ import annotations

import itertools, random, sys

LRS = [1e-4, 3e-4, 1e-3]
ENT = [0.0, 0.01, 0.1]
ENVS = [32, 128]
BUDGET_STEPS = 1_000_000


def simulate(lr, ent, envs):
    """玩具成功率代理（真实项目替换为训练+评测）。"""
    rng = random.Random(hash((lr, ent, envs)) & 0xffff)
    lr_ok = 1.0 - abs(math_log10(lr) - math_log10(3e-4)) / 1.0
    ent_ok = 1.0 if ent < 0.05 else 0.6
    env_ok = min(1.0, envs / 128.0)
    base = 0.5 + 0.3 * lr_ok + 0.1 * ent_ok + 0.1 * env_ok
    return max(0.0, min(1.0, base + rng.gauss(0, 0.02)))


def math_log10(v):
    import math
    return math.log10(v)


def main() -> int:
    rows = []
    for lr, ent, envs in itertools.product(LRS, ENT, ENVS):
        s = simulate(lr, ent, envs)
        rows.append({"lr": lr, "entropy": ent, "envs": envs,
                     "success": round(s, 3)})
    rows.sort(key=lambda r: -r["success"])
    print(f"固定预算 {BUDGET_STEPS} 步/组，共 {len(rows)} 组（种子固定可复现）")
    for r in rows[:5]:
        print(f"  lr={r['lr']:.0e} ent={r['entropy']} envs={r['envs']} "
              f"success={r['success']:.1%}")
    best = rows[0]
    print(f"推荐: lr={best['lr']:.0e}, entropy={best['entropy']}, "
          f"envs={best['envs']}")
    print("纪律：一次只动一个超参；成功率>学习曲线做决策")
    return 0


if __name__ == "__main__":
    sys.exit(main())
