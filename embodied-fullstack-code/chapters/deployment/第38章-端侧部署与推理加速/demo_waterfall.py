# -*- coding: utf-8 -*-
"""第38章 L1 极简 Demo：延迟瀑布剖析（先测量再优化）。"""
from __future__ import annotations
import sys

STAGES = {"采集": 8, "预处理": 12, "模型推理": 45, "后处理": 6, "发布": 4}


def main() -> int:
    total = sum(STAGES.values())
    print("端到端延迟瀑布:")
    for k, v in STAGES.items():
        bar = "#" * v
        print(f"  {k:<6} {v:>3}ms ({v/total:>5.0%}) {bar}")
    top = max(STAGES, key=STAGES.get)
    print(f"当前最大瓶颈: {top} ({STAGES[top]}ms) -> 先优化这里")
    return 0


if __name__ == "__main__":
    sys.exit(main())
