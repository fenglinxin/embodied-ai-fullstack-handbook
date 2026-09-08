# -*- coding: utf-8 -*-
"""第12章 L3 高阶优化版：数据集版本回归对比（ship/no-ship 决策）。

对两个数据集版本分别用同一评测 trials 计算：
  * 总体成功率
  * 关键桶(worst bucket)错误率
  * 版本差 delta
决策：总体提升 且 关键桶不退化超过 tol => ship；否则回炉补采。

运行：
  python advanced_loop_regression.py --make-sample sample
  python advanced_loop_regression.py --sample-dir sample --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, random, sys
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger("loop_regression")
TOL_BUCKET_REGRESSION = 0.05   # 关键桶允许退化幅度


def make_sample(root: Path) -> None:
    rng = random.Random(1)
    def gen_eval(improve_bucket: bool):
        trials = []
        for i in range(120):
            scene = "warehouse" if i % 3 == 0 else "kitchen_light"
            task = "pick_cup"
            # 关键桶 warehouse：v1 中补采后成功率提升
            hard = scene == "warehouse"
            p_ok = 0.95 if (not hard) else (0.85 if improve_bucket else 0.65)
            ok = rng.random() < p_ok
            trials.append({"trial_id": f"t-{i:04d}", "scene": scene,
                           "task": task, "success": ok})
        return trials

    def gen_dataset(n, extra_warehouse=0):
        eps = []
        for i in range(n):
            eps.append({"episode_id": f"ep-{i:04d}", "task": "pick_cup",
                        "scene": "warehouse" if i % 3 == 0 else "kitchen_light"})
        for i in range(extra_warehouse):
            eps.append({"episode_id": f"ep-w{i:04d}", "task": "pick_cup",
                        "scene": "warehouse"})
        return eps

    root.mkdir(parents=True, exist_ok=True)
    (root / "v0_trials.json").write_text(
        json.dumps(gen_eval(False)), encoding="utf-8")
    (root / "v0_dataset.json").write_text(
        json.dumps(gen_dataset(30)), encoding="utf-8")
    (root / "v1_trials.json").write_text(
        json.dumps(gen_eval(True)), encoding="utf-8")
    (root / "v1_dataset.json").write_text(
        json.dumps(gen_dataset(30, extra_warehouse=30)), encoding="utf-8")


def metrics(trials: list[dict]) -> dict[str, Any]:
    fails = [t for t in trials if not t.get("success")]
    bucket_fail = Counter((t.get("scene"), t.get("task")) for t in fails)
    bucket_all = Counter((t.get("scene"), t.get("task")) for t in trials)
    rates = {f"{s}|{t}": round(f / max(1, bucket_all[(s, t)]), 3)
             for (s, t), f in bucket_fail.items()}
    return {"total": len(trials),
            "success_rate": round((len(trials) - len(fails)) / len(trials), 4),
            "bucket_error_rates": rates}


def main() -> int:
    ap = argparse.ArgumentParser(description="数据集版本回归(L3)")
    ap.add_argument("--sample-dir", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例生成:", args.make_sample)
            return 0
        d = args.sample_dir or Path("sample")
        v0 = metrics(json.loads((d / "v0_trials.json").read_text(
            encoding="utf-8")))
        v1 = metrics(json.loads((d / "v1_trials.json").read_text(
            encoding="utf-8")))
        key_bucket = max(v0["bucket_error_rates"],
                         key=lambda k: v0["bucket_error_rates"][k])
        delta_all = v1["success_rate"] - v0["success_rate"]
        delta_key = (v1["bucket_error_rates"].get(key_bucket, 0)
                     - v0["bucket_error_rates"][key_bucket])
        ship = delta_all > 0 and delta_key <= TOL_BUCKET_REGRESSION
        rep = {"version_metrics": {"v0": v0, "v1": v1},
               "key_bucket": key_bucket,
               "overall_delta": round(delta_all, 4),
               "key_bucket_error_delta": round(delta_key, 4),
               "tolerance": TOL_BUCKET_REGRESSION,
               "decision": "ship-v1" if ship else "collect-more"}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "regression_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"总体成功率: v0={v0['success_rate']:.1%} -> "
          f"v1={v1['success_rate']:.1%} (Δ{delta_all:+.1%})")
    print(f"关键桶 {key_bucket} 错误率变化 Δ{delta_key:+.1%}")
    print("决策:", rep["decision"])
    print(f"报告: {(args.out_dir / 'regression_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
