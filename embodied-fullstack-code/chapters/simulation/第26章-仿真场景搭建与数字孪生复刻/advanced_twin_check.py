# -*- coding: utf-8 -*-
"""第26章 L3 高阶优化版：数字孪生一致性核对（真机 vs 仿真）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("twin_check")

DIMS = ["table_width_mm", "table_height_mm", "robot_base_x_mm",
        "camera_height_mm"]
TOL_MM = {"table_width_mm": 10, "table_height_mm": 5,
          "robot_base_x_mm": 5, "camera_height_mm": 10}


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    real = {"table_width_mm": 1200, "table_height_mm": 750,
            "robot_base_x_mm": 0, "camera_height_mm": 900}
    sim = {"table_width_mm": 1205, "table_height_mm": 762,
           "robot_base_x_mm": 3, "camera_height_mm": 900}
    (root / "real.json").write_text(json.dumps(real), encoding="utf-8")
    (root / "sim.json").write_text(json.dumps(sim), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="孪生一致性核对(L3)")
    ap.add_argument("--real", type=Path)
    ap.add_argument("--sim", type=Path)
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
        real = json.loads(args.real.read_text(encoding="utf-8"))
        sim = json.loads(args.sim.read_text(encoding="utf-8"))
        rows = []
        for d in DIMS:
            diff = abs(real[d] - sim[d])
            tol = TOL_MM.get(d, 10)
            rows.append({"dim": d, "real_mm": real[d], "sim_mm": sim[d],
                         "diff_mm": diff, "tol_mm": tol,
                         "pass": diff <= tol})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {"rows": rows,
              "pass_all": all(r["pass"] for r in rows),
              "advice": None if all(r["pass"] for r in rows)
              else "按差异项修正仿真布局/相机高度后重测"}
    (args.out_dir / "twin_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['dim']:<20} 真{r['real_mm']:>5} 仿{r['sim_mm']:>5} "
              f"差{r['diff_mm']:>3}mm [{'PASS' if r['pass'] else 'FAIL'}]")
    print("结论:", "孪生一致" if report["pass_all"] else report["advice"])
    return 0 if report["pass_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
