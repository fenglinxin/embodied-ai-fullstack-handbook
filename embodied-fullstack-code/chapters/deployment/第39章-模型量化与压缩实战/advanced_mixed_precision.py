# -*- coding: utf-8 -*-
"""第39章 L3 高阶优化版：混合精度选择（误差-显存帕累托，贪心）。"""
from __future__ import annotations
import sys

LAYERS = [("attention_q", 60, 1.0, 0.02),
          ("attention_out", 60, 0.8, 0.02),
          ("conv1", 120, 0.2, 0.01),
          ("action_head", 30, 0.6, 0.01),
          ("conv2", 80, 0.1, 0.005)]
ERR_BUDGET = 0.35


def main() -> int:
    total_params = sum(mb for _, mb, _, _ in LAYERS)
    # 按"单位显存换来的误差下降"排序
    rows = []
    for name, mb, e8, e16 in LAYERS:
        extra_mb = mb * 0.5
        gain = (e8 - e16) * (mb / total_params)
        rows.append((gain / extra_mb, gain, extra_mb, name))
    rows.sort(reverse=True)
    total_err = sum(e8 * mb / total_params for _, mb, e8, _ in LAYERS)
    fp16_layers, used_mb = [], 0.0
    for _, gain, extra, name in rows:
        if total_err <= ERR_BUDGET:
            break
        fp16_layers.append(name)
        used_mb += extra
        total_err -= gain
    print(f"误差预算 {ERR_BUDGET}; 选 FP16: {fp16_layers}")
    print(f"额外显存 {used_mb:.0f}MB; 剩余误差 {max(total_err,0):.3f}")
    print("原则：最少高精度层换回精度；INT4 再配合离群值拆分")
    return 0


if __name__ == "__main__":
    sys.exit(main())
