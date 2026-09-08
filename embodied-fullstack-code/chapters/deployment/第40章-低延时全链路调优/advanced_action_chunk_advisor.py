# -*- coding: utf-8 -*-
"""第40章 L3 高阶优化版：动作块参数建议器（用块长掩盖低频推理）。"""
from __future__ import annotations
import sys, math

STAGE_P99 = {"perception": 20, "planning": 30, "comm": 5, "control": 2}
TARGET = 70


def main() -> int:
    total = sum(STAGE_P99.values())
    inference_ms = 500.0          # VLA 每 500ms 推一次
    ctrl_period_ms = 20.0
    chunk = max(1, int(math.ceil(inference_ms / ctrl_period_ms)))
    print(f"端到端 P99 预算 {TARGET}ms，当前 {total}ms "
          f"-> {'达标' if total <= TARGET else '超预算'}")
    print(f"推理周期 {inference_ms:.0f}ms / 控制 {ctrl_period_ms:.0f}ms "
          f"-> 建议动作块 {chunk} 步（20ms×{chunk}={chunk*ctrl_period_ms:.0f}ms 覆盖）")
    print("分块让控制层不缺指令；推理结束再滚动更新（rollout）")
    return 0 if total <= TARGET else 1


if __name__ == "__main__":
    sys.exit(main())
