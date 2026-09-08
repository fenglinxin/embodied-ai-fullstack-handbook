# -*- coding: utf-8 -*-
"""第36章 L3 高阶优化版：环境试验矩阵（温度×电压×振动）。"""
from __future__ import annotations

import argparse, itertools, json, logging, sys
from pathlib import Path

logger = logging.getLogger("env_matrix")
LEVELS = {"temp_c": [20, 40, 50], "volt_pct": [90, 100, 110],
          "vib_g": [0.5, 1.0, 2.0]}


def simulate(combo):
    # 高温50 + 低压90 视为高风险
    return not (combo["temp_c"] >= 50 and combo["volt_pct"] <= 90)


def main() -> int:
    ap = argparse.ArgumentParser(description="环境试验矩阵(L3)")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    combos = list(itertools.product(*(LEVELS[k] for k in LEVELS)))
    rows = []
    fails = []
    for combo in combos:
        c = dict(zip(LEVELS, combo))
        ok = simulate(c)
        rows.append({**c, "pass": ok})
        if not ok:
            fails.append(c)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"total_combos": len(combos), "fail_combos": fails,
           "pass_rate": round(1 - len(fails) / len(combos), 3),
           "advice": "全因子27组；可先跑边界组合(高温+低压)做筛选"}
    (args.out_dir / "env_matrix.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"组合 {len(combos)} 组，失败 {len(fails)} 组")
    for f in fails[:5]:
        print("  失败组合:", f)
    print("建议:", rep["advice"])
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
