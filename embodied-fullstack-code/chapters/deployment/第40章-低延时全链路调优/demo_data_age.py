# -*- coding: utf-8 -*-
"""第40章 L1 极简 Demo：数据年龄（age of data）分析。"""
from __future__ import annotations
import statistics, sys

AGES_MS = [35, 38, 41, 45, 120, 39, 42, 150, 44, 40]


def main() -> int:
    a = sorted(AGES_MS)
    p95 = a[int(len(a) * 0.95)]
    print(f"数据年龄: 均值 {statistics.mean(AGES_MS):.0f}ms "
          f"P95 {p95}ms Max {max(AGES_MS)}ms")
    print("年龄=观测到执行的时间差；偶发 120/150ms 才是机器人'感觉慢'的来源")
    return 0


if __name__ == "__main__":
    sys.exit(main())
