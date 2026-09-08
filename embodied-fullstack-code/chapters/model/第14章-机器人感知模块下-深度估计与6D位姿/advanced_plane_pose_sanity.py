# -*- coding: utf-8 -*-
"""第14章 L3 高阶优化版：桌面平面RANSAC去除 + 物体尺寸/位姿 sanity 校验。

工程意义：6D 位姿/抓取前先"去桌面"，剩余点云估计物体 3D 包围盒；
若实测尺寸与 CAD 期望不符 -> 位姿估计可疑，拒绝执行（文章第4步验算）。

运行：
  python engineering_depth_qa.py --make-sample sample
  python advanced_plane_pose_sanity.py --input sample/depth.json \
      --bbox 18 14 12 12 --expected 60 120 60 --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, random, statistics, sys
from pathlib import Path

logger = logging.getLogger("pose_sanity")


def median_filter(depth: list[list[int]]) -> list[list[int]]:
    """3x3 中值滤波：修复孤立飞点（保留真实边缘）。"""
    import statistics as _st
    h, w = len(depth), len(depth[0])
    out = [row[:] for row in depth]
    for y in range(h):
        for x in range(w):
            nbr = [depth[yy][xx] for yy in range(max(0, y - 1), min(h, y + 2))
                   for xx in range(max(0, x - 1), min(w, x + 2))
                   if depth[yy][xx] > 0]
            if depth[y][x] <= 0 or (nbr and abs(depth[y][x] - _st.median(nbr)) > 80):
                out[y][x] = int(_st.median(nbr)) if nbr else depth[y][x]
    return out


def crop_points(depth, bbox, fx=300.0, fy=300.0):
    x0, y0, bw, bh = bbox
    h, w = len(depth), len(depth[0])
    cx, cy = w / 2.0, h / 2.0
    pts = []
    for y in range(y0, min(y0 + bh, h)):
        for x in range(x0, min(x0 + bw, w)):
            d = depth[y][x]
            if d <= 0:
                continue
            z = d / 1000.0
            pts.append([(x - cx) * z / fx, (y - cy) * z / fy, z])
    return pts


def fit_plane_ransac(pts, iters=80, thresh_mm=12.0):
    """平面 z=ax+by+c 的最小二乘内点拟合（简化RANSAC）。"""
    best = None
    thresh = thresh_mm / 1000.0
    for _ in range(iters):
        s = random.sample(pts, 3)
        (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = s
        denom = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
        if abs(denom) < 1e-12:
            continue
        a = ((y2 - y1) * (z3 - z1) - (y3 - y1) * (z2 - z1)) / denom
        b = ((x3 - x1) * (z2 - z1) - (x2 - x1) * (z3 - z1)) / denom
        c = z1 - a * x1 - b * y1
        inl = [p for p in pts if abs(p[2] - (a * p[0] + b * p[1] + c)) <= thresh]
        if best is None or len(inl) > len(best[0]):
            best = (inl, (a, b, c))
    return best


def bbox_dims(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    def rng(v):
        return max(v) - min(v)
    return [rng(xs) * 1000, rng(ys) * 1000, rng(zs) * 1000], [
        sum(xs) / len(xs) * 1000, sum(ys) / len(ys) * 1000,
        sum(zs) / len(zs) * 1000]


def main() -> int:
    ap = argparse.ArgumentParser(description="桌面去除+位姿sanity(L3)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--bbox", nargs=4, type=int, required=True)
    ap.add_argument("--expected", nargs=3, type=float, required=True,
                    help="CAD 期望尺寸 mm [长,宽,高]")
    ap.add_argument("--tol", type=float, default=0.25,
                    help="尺寸容差比例(如0.25=±25%)")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        depth_f = median_filter(data["depth_mm"])
        pts = crop_points(depth_f, tuple(args.bbox))
        if len(pts) < 10:
            raise RuntimeError("裁剪点云过少")
        inliers, plane = fit_plane_ransac(pts)
        in_set = set(map(tuple, inliers))
        obj = [p for p in pts if tuple(p) not in in_set]
        if len(obj) < 5:
            raise RuntimeError("桌面去除后物体点过少(平面参数或bbox不对)")
        dims, center = bbox_dims(obj)
        ratios = [abs(dims[i] - args.expected[i]) / max(1e-6, args.expected[i])
                  for i in range(3) if args.expected[i] > 0]
        ok = max(ratios) <= args.tol
        rep = {"plane_coeff": [round(v, 4) for v in plane],
               "plane_inliers": len(inliers), "object_points": len(obj),
               "object_dims_mm": [round(v, 1) for v in dims],
               "expected_mm": list(args.expected),
               "dim_ratios": [round(v, 3) for v in ratios],
               "object_center_mm": [round(v, 1) for v in center],
               "verdict": "pose-ok" if ok else "reject-check-pose"}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "pose_sanity.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"桌面内点 {len(inliers)}，物体点 {len(obj)}")
    print("物体实测尺寸(mm):", rep["object_dims_mm"], "期望:",
          rep["expected_mm"])
    print("判定:", rep["verdict"])
    print(f"报告: {(args.out_dir / 'pose_sanity.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
