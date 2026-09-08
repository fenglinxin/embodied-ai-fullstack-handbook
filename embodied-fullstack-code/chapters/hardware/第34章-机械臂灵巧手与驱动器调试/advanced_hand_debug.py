# -*- coding: utf-8 -*-
"""第34章 L3 高阶优化版：灵巧手自由度自检 + 滑觉-握力联动。"""
from __future__ import annotations
import sys

DOF_TOL = 0.05   # rad 反馈误差容忍
GRIP_STEP = 1.3


def main() -> int:
    # 自由度清单: 命令/反馈
    fingers = [("thumb_MCP", 0.5, 0.49), ("thumb_IP", 0.4, 0.41),
               ("index_PIP", 0.8, 0.62), ("middle_PIP", 0.8, 0.79),
               ("ring_PIP", 0.8, 0.0)]
    issues = []
    for name, cmd, fb in fingers:
        err = abs(cmd - fb)
        ok = err <= DOF_TOL
        if not ok:
            issues.append({"joint": name, "cmd": cmd, "feedback": fb,
                           "err": round(err, 3)})
        print(f"{name:<12} cmd={cmd} fb={fb} "
              f"[{'OK' if ok else 'ERR'}]")
    # 滑觉联动
    grip = 2.0
    print("滑觉事件: 握力", grip, "->", round(grip * GRIP_STEP, 2), "N (分级增力)")
    print("自检结果:", "通过" if not issues else f"{len(issues)} 个关节异常")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
