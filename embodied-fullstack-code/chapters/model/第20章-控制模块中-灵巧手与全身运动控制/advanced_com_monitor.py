# -*- coding: utf-8 -*-
"""第20章 L3 高阶优化版：全身重心-支撑域监控（静态站姿任务优先级）。

输入：双脚支撑多边形 + 当前 CoM(x,y)，评估：
  * CoM 是否在支撑多边形内（射线法）
  * 到最近边距离/安全内缩边界
  * 动作建议：stable / 髋部补偿 / 停止任务

运行：python advanced_com_monitor.py
"""
from __future__ import annotations
import sys

FEET = [(-0.12, -0.06), (0.12, -0.06), (0.12, 0.06), (-0.12, 0.06)]
INSET = 0.02     # 安全内缩 2cm


def inside(poly, pt):
    x, y = pt
    n = len(poly)
    inside_flag = False
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (
                x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1):
            inside_flag = not inside_flag
    return inside_flag


def margin(poly, pt):
    best = 1e9
    x, y = pt
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        px, py = x1 + t * dx, y1 + t * dy
        best = min(best, ((x - px) ** 2 + (y - py) ** 2) ** 0.5)
    return best


def shrink(poly, d):
    # 粗略内缩：向质心方向平移
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        vx, vy = cx - x, cy - y
        m = (vx * vx + vy * vy) ** 0.5 or 1.0
        out.append((x + vx / m * d, y + vy / m * d))
    return out


def main() -> int:
    inner = shrink(FEET, INSET)
    for label, com in [("中立", (0.0, 0.0)),
                       ("伸手取物", (0.0, 0.045)),
                       ("过度前伸(危险)", (0.0, 0.085))]:
        ok = inside(inner, com)
        m = margin(inner, com)
        if ok:
            action = "stable" if m > INSET else "shift-hip"
        else:
            action = "stop-task"
        print(f"{label:<14} CoM={com} 内缩域内={ok} 边距={m*100:.1f}cm "
              f"-> {action}")
    print("规则：任务优先级 平衡>限位>操作；CoM 越界先停任务再补偿。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
