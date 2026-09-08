# -*- coding: utf-8 -*-
"""第17章 L2 工业工程版：代价地图全局规划（膨胀+A*/Dijkstra+平滑）。

输入 map.json: {"w":cols,"h":rows,"cost":[[0/1..]]}，start/goal。
流程：1) 障碍膨胀(inflation) 2) A*(启发)或 Dijkstra 3) 路径平滑(剪枝)。
输出 path.json + report。

运行：
  python engineering_path_planner.py --make-sample sample
  python engineering_path_planner.py --map sample/map.json --start 0 0 \
      --goal 4 8 --algo astar --inflate 1 --out-dir out
"""
from __future__ import annotations

import argparse, heapq, json, logging, math, sys
from pathlib import Path

logger = logging.getLogger("planner")
NEIGH = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
COST8 = math.sqrt(2)


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    cost = [[0] * 10 for _ in range(6)]
    for r in range(6):          # 一堵墙(留缺口)
        for c in (3, 4):
            if r != 2:
                cost[r][c] = 1
    (root / "map.json").write_text(json.dumps(
        {"w": 10, "h": 6, "cost": cost}), encoding="utf-8")


def inflate(cost, radius):
    h, w = len(cost), len(cost[0])
    out = [row[:] for row in cost]
    obs = [(r, c) for r in range(h) for c in range(w) if cost[r][c] > 0]
    for r, c in obs:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and out[nr][nc] == 0:
                    out[nr][nc] = 2   # 膨胀层
    return out


def plan(cost, s, g, algo):
    h, w = len(cost), len(cost[0])
    def heu(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) if algo == "astar" else 0.0
    pq = [(0.0, s)]
    came, gcost = {}, {s: 0.0}
    expanded = 0
    while pq:
        _, cur = heapq.heappop(pq)
        expanded += 1
        if cur == g:
            p = [cur]
            while cur in came:
                cur = came[cur]; p.append(cur)
            return p[::-1], expanded
        r, c = cur
        for dr, dc in NEIGH:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or cost[nr][nc] != 0:
                continue
            step = 1.0 if dr == 0 or dc == 0 else COST8
            ng = gcost[cur] + step + 0.01 * cost[nr][nc]
            if ng < gcost.get((nr, nc), 1e18):
                gcost[(nr, nc)] = ng
                came[(nr, nc)] = cur
                heapq.heappush(pq, (ng + heu((nr, nc), g), (nr, nc)))
    return None, expanded


def smooth(path):
    if not path:
        return []
    out = [path[0]]
    i = 0
    while i < len(path) - 1:
        # 找能直线到达的最远点（栅格无碰撞检测简化为单调性检查）
        j = len(path) - 1
        while j > i + 1:
            r1, c1 = path[i]; r2, c2 = path[j]
            if abs(r2 - r1) <= 1 or abs(c2 - c1) <= 1:
                break
            j -= 1
        out.append(path[j])
        i = j
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="全局规划(工程版)")
    ap.add_argument("--map", type=Path)
    ap.add_argument("--start", nargs=2, type=int)
    ap.add_argument("--goal", nargs=2, type=int)
    ap.add_argument("--algo", choices=["astar", "dijkstra"], default="astar")
    ap.add_argument("--inflate", type=int, default=1)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        if not args.start or not args.goal:
            raise ValueError("规划模式需要 --start 与 --goal")
        data = json.loads(args.map.read_text(encoding="utf-8"))
        cost = inflate(data["cost"], args.inflate)
        s = tuple(args.start); g = tuple(args.goal)
        path, expanded = plan(cost, s, g, args.algo)
        if path is None:
            raise RuntimeError("无可行路径（膨胀过大或地图封闭）")
        smooth_path = smooth(path)
    except Exception as exc:
        logger.error("规划失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"algo": args.algo, "path_len": len(path),
           "smooth_len": len(smooth_path), "expanded": expanded,
           "path": path, "smoothed_path": smooth_path}
    (args.out_dir / "path_plan.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.algo}: 路径 {len(path)} -> 平滑 {len(smooth_path)} 步, "
          f"扩展 {expanded} 节点")
    print(f"报告: {(args.out_dir / 'path_plan.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
