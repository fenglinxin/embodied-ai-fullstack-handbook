# -*- coding: utf-8 -*-
"""第30章 L2 工业工程版：回归基准集 runner（防"修A坏B"）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("regression")
TOL = 0.05


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    scenes = ["kitchen_light", "kitchen_shadow", "warehouse"]
    def gen(drop_warehouse: bool):
        out = {}
        for s in scenes:
            base = 0.95 if s != "warehouse" else (0.90 if not drop_warehouse
                                                  else 0.75)
            out[s] = {"success_rate": base, "trials": 40}
        return out
    (root / "baseline.json").write_text(json.dumps(gen(False)), encoding="utf-8")
    (root / "new.json").write_text(json.dumps(gen(True)), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="回归评测(工程版)")
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--new", type=Path)
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
        base = json.loads(args.baseline.read_text(encoding="utf-8"))
        new = json.loads(args.new.read_text(encoding="utf-8"))
        rows, regressions = [], []
        for scene, b in base.items():
            n = new.get(scene, {})
            delta = n.get("success_rate", 0) - b["success_rate"]
            bad = delta < -TOL
            rows.append({"scene": scene, "baseline": b["success_rate"],
                         "new": n.get("success_rate"),
                         "delta": round(delta, 3), "regression": bad})
            if bad:
                regressions.append(scene)
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"rows": rows, "regressions": regressions,
           "verdict": "pass" if not regressions else "blocked"}
    (args.out_dir / "regression_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['scene']:<16} base={r['baseline']:.2f} new={r['new']:.2f} "
              f"Δ{r['delta']:+.2f} [{'REGRESSION' if r['regression'] else 'OK'}]")
    print("结论:", rep["verdict"])
    return 0 if rep["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
