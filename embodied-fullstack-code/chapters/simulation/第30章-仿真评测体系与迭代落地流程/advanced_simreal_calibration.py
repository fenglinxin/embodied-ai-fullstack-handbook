# -*- coding: utf-8 -*-
"""第30章 L3 高阶优化版：仿真-真机锚点校准（分数相关性）。"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path

logger = logging.getLogger("simreal_calib")


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    pairs = [{"task": "pick_cup", "sim": 0.90, "real": 0.62},
             {"task": "place_cup", "sim": 0.85, "real": 0.58},
             {"task": "push_box", "sim": 0.70, "real": 0.45},
             {"task": "insert", "sim": 0.50, "real": 0.28}]
    (root / "anchors_pairs.json").write_text(json.dumps(pairs), encoding="utf-8")


def fit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    var = sum((x - mx) ** 2 for x in xs) / n
    b = cov / var if var else 0.0
    a = my - b * mx
    if var == 0 or (sum((y - my) ** 2 for y in ys) == 0):
        r = 1.0
    else:
        r = cov / math.sqrt(var * sum((y - my) ** 2 for y in ys) / n)
    return a, b, r


def main() -> int:
    ap = argparse.ArgumentParser(description="仿真-真机校准(L3)")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        pairs = json.loads(args.input.read_text(encoding="utf-8"))
        xs = [p["sim"] for p in pairs]
        ys = [p["real"] for p in pairs]
        a, b, r = fit(xs, ys)
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"n": len(pairs), "slope": round(b, 3), "intercept": round(a, 3),
           "pearson_r": round(r, 3),
           "verdict": "sim-filter-usable" if r > 0.7 else "sim-score-weak"}
    (args.out_dir / "calibration.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"拟合 real ≈ {b:.2f}*sim + {a:.2f}, Pearson r={r:.3f}")
    print("结论:", rep["verdict"],
          "(r>0.7 时仿真分才适合当筛选器)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
