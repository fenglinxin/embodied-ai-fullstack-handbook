# -*- coding: utf-8 -*-
"""第37章 L1 极简 Demo：端到端延迟预算表。"""
from __future__ import annotations
import sys

STAGES = {"感知": 20, "规划": 30, "通信": 5, "控制": 2}
BUDGET = 80


def main() -> int:
    total = sum(STAGES.values())
    print("延迟预算(ms):")
    for k, v in STAGES.items():
        print(f"  {k}: {v}")
    print(f"合计 {total}ms vs 预算 {BUDGET}ms "
          f"-> {'达标' if total <= BUDGET else '超预算'}")
    print("注意：验收看 P99，不是平均值；控制段抖动≤周期20%")
    return 0 if total <= BUDGET else 1


if __name__ == "__main__":
    sys.exit(main())
