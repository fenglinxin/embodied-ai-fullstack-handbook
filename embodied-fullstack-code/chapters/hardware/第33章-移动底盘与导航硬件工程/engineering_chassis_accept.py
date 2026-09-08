# -*- coding: utf-8 -*-
"""第33章 L2 工业工程版：底盘验收实验记录器（六项实验+门禁）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("chassis_accept")

TARGETS = {
    "straight_drift_cm": 2.0,
    "spin_error_deg": 2.0,
    "step_oscillation": 0.3,
    "bump_pulse_loss": 0,
    "load_current_ok": True,
    "endurance_h": 2.0,
}


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    results = {"straight_drift_cm": 1.2, "spin_error_deg": 1.5,
               "step_oscillation": 0.15, "bump_pulse_loss": 2,
               "load_current_ok": True, "endurance_h": 2.5}
    (root / "results.json").write_text(json.dumps(results), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="底盘验收(工程版)")
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
        res = json.loads(args.input.read_text(encoding="utf-8"))
        rows = []
        for k, target in TARGETS.items():
            v = res.get(k)
            if isinstance(target, bool):
                ok = v == target
            elif isinstance(target, int) and "loss" in k:
                ok = v == target
            elif isinstance(target, float) and k.endswith("_h"):
                ok = v >= target
            else:
                ok = v <= target
            rows.append({"item": k, "value": v, "target": target, "pass": ok})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {"rows": rows,
              "pass_all": all(r["pass"] for r in rows)}
    (args.out_dir / "chassis_accept.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['item']:<22} value={r['value']} "
              f"[{'PASS' if r['pass'] else 'FAIL'}]")
    print("结论:", "验收通过-可接导航" if report["pass_all"] else "不通过-先修")
    return 0 if report["pass_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
