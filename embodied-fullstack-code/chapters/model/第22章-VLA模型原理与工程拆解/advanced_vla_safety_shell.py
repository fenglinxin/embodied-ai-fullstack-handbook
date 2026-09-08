# -*- coding: utf-8 -*-
"""第22章 L3 高阶优化版：VLA 真机安全壳（限速/限位/低置信回退）。

VLA 输出动作块(末端增量) + 置信度 -> 安全壳：
  1) 每步增量限速（m/s）
  2) 位置边界 clamp
  3) conf<阈值：执行上一次安全动作或原地停止（防乱动）

运行：python advanced_vla_safety_shell.py
"""
from __future__ import annotations
import sys

MAX_SPEED = 0.2        # m/s 每控制周期
BOUND = 1.0            # 工作空间边界 ±1m
CONF_FALLBACK = 0.6


def shell_step(action, conf, last_ok):
    x, y, z, g = action
    if conf < CONF_FALLBACK:
        return None, "fallback-stop" if last_ok is None else "fallback-last"
    # 限速
    norm = (x * x + y * y + z * z) ** 0.5
    if norm > MAX_SPEED:
        s = MAX_SPEED / norm
        x, y, z = x * s, y * s, z * s
    # 限位（简化：累计假设从原点开始）
    if abs(x) > BOUND or abs(y) > BOUND or abs(z) > BOUND:
        return None, "boundary-clip"
    return [round(x, 4), round(y, 4), round(z, 4), g], "ok"


def main() -> int:
    stream = [
        ([0.1, 0.0, 0.0, 0], 0.95),
        ([0.3, 0.0, 0.0, 0], 0.90),     # 超速 -> 限到0.2
        ([0.05, 0.02, 0.0, 0], 0.30),   # 低置信 -> 用上次安全动作
        ([0.0, 0.1, 0.0, 1], 0.88),
    ]
    last_ok = None
    executed = fallbacks = 0
    for action, conf in stream:
        out, tag = shell_step(action, conf, last_ok)
        if out is None:
            fallbacks += 1
            print(f"conf={conf:.2f} -> {tag}（未执行）")
            continue
        if tag == "ok":
            last_ok = out
        executed += 1
        print(f"conf={conf:.2f} -> 执行 {out} [{tag}]")
    print(f"安全壳统计: 执行 {executed}/4，回退 {fallbacks} 次")
    print("原则：VLA 负责聪明，安全壳负责不闯祸。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
