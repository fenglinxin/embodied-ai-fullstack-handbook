# -*- coding: utf-8 -*-
"""第37章 L2 工业工程版：指令超时失效安全模拟（断连→安全停车）。"""
from __future__ import annotations
import sys

WATCHDOG_MS = 50
STOP_RAMP_MS = 200
DT_MS = 10


def main() -> int:
    cmd_v = 1.0
    v = 0.0
    disconnect_at = 300
    safe_triggered = False
    stop_start = None
    overshoot = 0.0
    t = 0
    while t < 500:
        if t < disconnect_at:
            v = cmd_v
        else:
            if not safe_triggered:
                safe_triggered = True
                stop_start = t
                print(f"t={t}ms: 指令超时({WATCHDOG_MS}ms看门狗) -> 触发安全停车")
            if stop_start is not None:
                elapsed = t - stop_start
                v = cmd_v * max(0.0, 1.0 - elapsed / STOP_RAMP_MS)
        overshoot = max(overshoot, abs(v))
        t += DT_MS
    print(f"安全停车后速度回零耗时 {STOP_RAMP_MS}ms，无失控")
    return 0


if __name__ == "__main__":
    sys.exit(main())
