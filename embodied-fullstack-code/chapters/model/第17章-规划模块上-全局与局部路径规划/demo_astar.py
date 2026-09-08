# -*- coding: utf-8 -*-
"""第17章 L1 极简 Demo：栅格 A*（纯 Python + heapq）。

运行：python demo_astar.py
"""
from __future__ import annotations
import heapq, sys

GRID = [
    [0, 0, 0, 0, 1, 0, 0],
    [0, 1, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0],
]
START, GOAL = (0, 0), (4, 6)


def astar(grid, s, g):
    h, w = len(grid), len(grid[0])
    open_h = [(0, s)]
    came, gcost = {}, {s: 0}
    while open_h:
        _, cur = heapq.heappop(open_h)
        if cur == g:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            return path[::-1], len(gcost)
        x, y = cur
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < h and 0 <= ny < w) or grid[nx][ny]:
                continue
            ng = gcost[cur] + 1
            if ng < gcost.get((nx, ny), 1e18):
                gcost[(nx, ny)] = ng
                came[(nx, ny)] = cur
                f = ng + abs(nx - g[0]) + abs(ny - g[1])
                heapq.heappush(open_h, (f, (nx, ny)))
    return None, len(gcost)


def main() -> int:
    path, expanded = astar(GRID, START, GOAL)
    if path is None:
        print("无路径")
        return 1
    print(f"A* 路径 {len(path)} 步，扩展 {expanded} 节点:")
    for i, p in enumerate(path):
        print(f"  {i}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
