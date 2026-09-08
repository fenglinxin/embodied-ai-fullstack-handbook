# -*- coding: utf-8 -*-
"""第34章 L2 工业工程版：重复精度/背隙/绝对误差分析。"""
from __future__ import annotations

import argparse, json, logging, math, statistics, sys
from pathlib import Path

logger = logging.getLogger("precision")


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    # 20 次到位：前10正向逼近，后10反向逼近；含背隙0.8mm
    pts = []
    for i in range(20):
        d = 0.0 if i < 10 else 0.8
        pts.append({"approach": "fwd" if i < 10 else "rev",
                    "x_mm": 500.3 + d + (i % 3) * 0.05,
                    "y_mm": 0.05 * (i % 2), "z_mm": 0.0})
    (root / "trials.json").write_text(json.dumps(pts), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="精度分析(工程版)")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--command", nargs=3, type=float, default=[500.0, 0.0, 0.0])
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        pts = json.loads(args.input.read_text(encoding="utf-8"))
        c = args.command
        # 相对质心
        cx = statistics.mean(p["x_mm"] for p in pts)
        cy = statistics.mean(p["y_mm"] for p in pts)
        cz = statistics.mean(p["z_mm"] for p in pts)
        radii = [math.dist((p["x_mm"], p["y_mm"], p["z_mm"]), (cx, cy, cz))
                 for p in pts]
        repeatability = max(radii)     # ISO 简化
        fwd = [p for p in pts if p["approach"] == "fwd"]
        rev = [p for p in pts if p["approach"] == "rev"]
        backlash = abs(statistics.mean(p["x_mm"] for p in fwd)
                       - statistics.mean(p["x_mm"] for p in rev))
        abs_err = statistics.mean(math.dist(
            (p["x_mm"], p["y_mm"], p["z_mm"]), c) for p in pts)
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"repeatability_mm": round(repeatability, 3),
           "backlash_mm": round(backlash, 3),
           "mean_abs_error_mm": round(abs_err, 3)}
    (args.out_dir / "precision_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in rep.items():
        print(f"{k}: {v} mm")
    print("结论: 重复精度差查机械/驱动；背隙大需补偿或单向逼近；"
          "绝对差大查运动学/TCP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
