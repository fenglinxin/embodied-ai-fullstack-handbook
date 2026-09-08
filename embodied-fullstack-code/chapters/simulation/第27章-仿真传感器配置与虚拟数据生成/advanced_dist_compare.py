# -*- coding: utf-8 -*-
"""第27章 L3 高阶优化版：虚拟-真机分布对比（迁移前必做）。"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path

logger = logging.getLogger("dist_compare")


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    # 像素亮度直方图（0-255, 32 bin）示意
    def gauss(mean, sd):
        return [max(0.0, math.exp(-((i - mean) ** 2) / (2 * sd * sd)))
                for i in range(32)]
    sim = gauss(150, 18)      # 仿真偏干净亮
    real = gauss(128, 30)     # 真机更暗更散
    (root / "sim_hist.json").write_text(json.dumps(sim), encoding="utf-8")
    (root / "real_hist.json").write_text(json.dumps(real), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="分布对比(L3)")
    ap.add_argument("--sim", type=Path)
    ap.add_argument("--real", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        a = json.loads(args.sim.read_text(encoding="utf-8"))
        b = json.loads(args.real.read_text(encoding="utf-8"))
        n = min(len(a), len(b))
        sa, sb = sum(a[:n]), sum(b[:n])
        na, nb = [x / sa for x in a[:n]], [x / sb for x in b[:n]]
        inter = sum(min(x, y) for x, y in zip(na, nb))
        mean_abs = sum(abs(x - y) for x, y in zip(na, nb)) / n
        ok = inter >= args.threshold
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"histogram_intersection": round(inter, 4),
           "mean_abs_diff": round(mean_abs, 4), "threshold": args.threshold,
           "verdict": "distribution-close" if ok else "gap-needs-noise-tuning"}
    (args.out_dir / "dist_compare.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"直方图交叠 {inter:.3f} (阈值 {args.threshold}) "
          f"-> {rep['verdict']}")
    if not ok:
        print("建议：调亮度/对比度/噪声参数(见 L2 采样器)后重测")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
