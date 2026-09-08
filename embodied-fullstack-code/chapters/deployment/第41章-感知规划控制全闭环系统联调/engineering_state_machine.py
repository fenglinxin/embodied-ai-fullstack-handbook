# -*- coding: utf-8 -*-
"""第41章 L2 工业工程版：系统状态机（L0-L3 异常分级仲裁）。"""
from __future__ import annotations
import sys

STATE = "IDLE"
EVENTS = [("start", "L0"), ("lost_1", "L1"), ("lost_2", "L1"),
          ("lost_3", "L2"), ("recover", "L0"), ("estop", "L3"),
          ("reset", "IDLE")]


def main() -> int:
    state = "IDLE"
    l1_count = 0
    for ev, lvl in EVENTS:
        if ev == "start":
            state = "RUN"
        elif ev == "estop":
            state = "SAFE_STOP"
        elif ev == "reset":
            state = "IDLE"
        elif ev == "lost_1" or ev == "lost_2":
            l1_count += 1
        elif ev == "lost_3":
            state = "DEGRADED"
        elif ev == "recover":
            state = "RUN"
            l1_count = 0
        print(f"{ev:<8} level={lvl} -> state={state}")
    print("总结: L1重试/L2降级(减速保守)/L3安全停——异常由仲裁器统一处理")
    return 0


if __name__ == "__main__":
    sys.exit(main())
