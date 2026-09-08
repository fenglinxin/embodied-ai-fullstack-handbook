# -*- coding: utf-8 -*-
"""第40章 L2 工业工程版：串行 vs 流水线并行延迟对比。"""
from __future__ import annotations
import sys

STAGES_MS = [8, 12, 25, 6]      # 采集/感知/决策/控制


def main() -> int:
    serial = sum(STAGES_MS)
    parallel_cycle = max(STAGES_MS)    # 稳态节拍
    first_latency = serial             # 首帧仍要串行
    print(f"串行: 单次延迟 {serial}ms；稳态吞吐节拍 {serial}ms")
    print(f"流水线并行: 稳态节拍 {parallel_cycle}ms（首帧仍 {first_latency}ms）")
    print("结论：并行解决'排队延迟'，让端到端≈最大单段；用双缓冲实现")
    return 0


if __name__ == "__main__":
    sys.exit(main())
