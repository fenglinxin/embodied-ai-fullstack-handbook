# -*- coding: utf-8 -*-
"""第13章 L1 极简 Demo：连通域检测器（纯标准库，理解检测=定位+分类）。

对阈值化灰度图做 8-连通域标记，输出 bbox：
理解"检测框从哪来"的最小实现；真实项目请接 YOLO 等（README 说明）。

运行：python demo_color_detector.py
"""
from __future__ import annotations
import sys


def fake_scene(size: int = 48) -> list[list[int]]:
    """桌面场景：背景40，两个"物体"：红杯(220) 与 蓝色干扰(120)。"""
    img = [[40] * size for _ in range(size)]
    for y in range(10, 22):          # 红杯
        for x in range(12, 17):
            img[y][x] = 220
    for y in range(26, 34):          # 干扰
        for x in range(30, 36):
            img[y][x] = 120
    return img


def detect(img, thresh: int = 180) -> list[dict]:
    h, w = len(img), len(img[0])
    seen = [[False] * w for _ in range(h)]
    boxes = []
    for sy in range(h):
        for sx in range(w):
            if seen[sy][sx] or img[sy][sx] < thresh:
                continue
            # BFS 收集同一连通域
            stack = [(sx, sy)]
            seen[sy][sx] = True
            xs, ys = [], []
            while stack:
                x, y = stack.pop()
                xs.append(x); ys.append(y)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < h and 0 <= nx < w and not seen[ny][nx]
                                and img[ny][nx] >= thresh):
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            boxes.append({"x": min(xs), "y": min(ys),
                          "w": max(xs) - min(xs) + 1,
                          "h": max(ys) - min(ys) + 1,
                          "pixels": len(xs)})
    return boxes


def main() -> int:
    img = fake_scene()
    boxes = detect(img)
    print("检测到连通域:", len(boxes))
    for b in boxes:
        print(f"  bbox=({b['x']},{b['y']},{b['w']}x{b['h']}) "
              f"像素={b['pixels']} 类别=杯(高灰度阈值)")
    print("说明：真实检测 = 特征提取 + 分类器 + NMS；"
          "本 Demo 演示定位的最小机制。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
