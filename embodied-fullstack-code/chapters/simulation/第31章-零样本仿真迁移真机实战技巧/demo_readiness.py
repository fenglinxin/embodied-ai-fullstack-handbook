# -*- coding: utf-8 -*-
"""第31章 L1 极简 Demo：迁移就绪度评审（零样本≠零准备）。"""
from __future__ import annotations
import sys

CHECKS = [
    ("动力学差距已量化", True),
    ("域随机化覆盖边界", True),
    ("感知链路与仿真假设一致", False),
    ("真机锚点评测通过", True),
]


def main() -> int:
    fails = [n for n, ok in CHECKS if not ok]
    print("迁移就绪度评审:")
    for n, ok in CHECKS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}")
    if fails:
        print(f"不达标 {len(fails)} 项 -> 先补课，不要叫'零样本'")
        return 1
    print("达标 -> 可进入首跑 8 步清单")
    return 0


if __name__ == "__main__":
    sys.exit(main())
