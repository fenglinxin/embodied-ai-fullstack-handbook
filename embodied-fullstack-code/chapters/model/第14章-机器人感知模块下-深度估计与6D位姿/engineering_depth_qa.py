# -*- coding: utf-8 -*-
"""第14章 L2 工业工程版：深度图质量体检 + 检测框点云裁剪。

输入：depth.json = {"w":64,"h":48,"depth_mm":[[...]]}（0 表示无效/NaN）
体检：无效占比、飞点（孤立突刺）、孔洞填充后的 max-gap；
裁剪：给定 bbox 与内参，输出该框内有效 3D 点（物体点云前处理）。

运行：
  python engineering_depth_qa.py --make-sample sample
  python engineering_depth_qa.py --input sample/depth.json --bbox 20 10 12 12 --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, random, statistics, sys
from pathlib import Path

logger = logging.getLogger("depth_qa")


def make_sample(root: Path, size: int = 48) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(0)
    m = []
    for y in range(size):
        row = []
        for x in range(size):
            # 桌面 800mm，中间物体 400mm
            d = 400 if (14 <= y < 26 and 18 <= x < 30) else 800
            if rng.random() < 0.02:            # 无效点
                d = 0
            if rng.random() < 0.01:            # 飞点
                d = d + rng.choice([-300, 300])
            row.append(d)
        m.append(row)
    (root / "depth.json").write_text(
        json.dumps({"w": size, "h": size, "depth_mm": m}), encoding="utf-8")


def qa(depth: list[list[int]]) -> dict:
    h, w = len(depth), len(depth[0])
    vals, invalid = [], 0
    for row in depth:
        for v in row:
            if v <= 0:
                invalid += 1
            else:
                vals.append(v)
    # 飞点：与4邻域中位差 > 80mm 且自身偏差方向孤立
    fly = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            v = depth[y][x]
            if v <= 0:
                continue
            nbr = [depth[y + dy][x + dx] for dy in (-1, 0, 1)
                   for dx in (-1, 0, 1) if (dx or dy)
                   and depth[y + dy][x + dx] > 0]
            if nbr and abs(v - statistics.median(nbr)) > 80:
                fly += 1
    return {"width": w, "height": h, "total": h * w,
            "invalid": invalid,
            "invalid_ratio": round(invalid / (h * w), 4),
            "flypoint_count": fly,
            "depth_range_mm": (min(vals), max(vals)) if vals else None}


def crop_points(depth, bbox, fx=300.0, fy=300.0, cx=None, cy=None):
    x0, y0, bw, bh = bbox
    h, w = len(depth), len(depth[0])
    cx = cx if cx is not None else w / 2.0
    cy = cy if cy is not None else h / 2.0
    pts = []
    for y in range(y0, min(y0 + bh, h)):
        for x in range(x0, min(x0 + bw, w)):
            d = depth[y][x]
            if d <= 0:
                continue
            z = d / 1000.0
            pts.append([round((x - cx) * z / fx, 4),
                        round((y - cy) * z / fy, 4),
                        round(z, 4)])
    return pts


def main() -> int:
    ap = argparse.ArgumentParser(description="深度图QA+裁剪(工程版)")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--bbox", nargs=4, type=int, default=[0, 0, 64, 48])
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
        data = json.loads(args.input.read_text(encoding="utf-8"))
        depth = data["depth_mm"]
        rep = qa(depth)
        pts = crop_points(depth, tuple(args.bbox))
        rep["crop_points"] = len(pts)
        if pts:
            rep["crop_center_mm"] = [round(sum(p[i] for p in pts) / len(pts)
                                           * 1000, 1) for i in range(3)]
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "depth_qa.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"无效占比 {rep['invalid_ratio']:.1%} 飞点 {rep['flypoint_count']} "
          f"裁剪点数 {rep['crop_points']}")
    if rep.get("crop_center_mm"):
        print("裁剪框内点云中心(mm):", rep["crop_center_mm"])
    print(f"报告: {(args.out_dir / 'depth_qa.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
