# -*- coding: utf-8 -*-
"""第12章 L2 工业工程版：失败归因 + 补采任务书生成。

输入：
  eval_results.json   评测 trials（success/failure_mode/scene/task）
  dataset_manifest.json 当前数据集（episode_id/task/scene/object）
输出：
  loop_report.json     失败率/桶级错误率/Pareto
  collection_tasks.json 补采任务书（按 失败次数×业务权重 排序）

运行：
  python demo_error_mining.py --out eval_results.json
  python engineering_loop_runner.py --eval eval_results.json \
      --dataset dataset_manifest.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger("loop_runner")

BUSINESS_WEIGHT = {"place_cup": 1.5, "pick_cup": 1.0}   # 业务失败代价


def load(p: Path, default: list | None = None) -> list:
    if p.exists():
        raw = json.loads(p.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    return default or []


def main() -> int:
    ap = argparse.ArgumentParser(description="失败归因与补采(工程版)")
    ap.add_argument("--eval", required=True, type=Path)
    ap.add_argument("--dataset", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        trials = load(args.eval)
        dataset = load(args.dataset)
        if not trials or not dataset:
            raise RuntimeError("评测/数据集为空")
        fails = [t for t in trials if not t.get("success")]
        total = len(trials)
        modes = Counter(t.get("failure_mode") or "unknown" for t in fails)
        bucket_eval = Counter((t.get("scene"), t.get("task")) for t in trials)
        bucket_fail = Counter((t.get("scene"), t.get("task")) for t in fails)
        bucket_data = Counter((e.get("scene"), e.get("task"))
                              for e in dataset)
        tasks = []
        for (scene, task), fail_n in bucket_fail.items():
            eval_n = bucket_eval[(scene, task)]
            weight = BUSINESS_WEIGHT.get(task, 1.0)
            tasks.append({"scene": scene, "task": task,
                          "eval_trials": eval_n, "eval_failures": fail_n,
                          "error_rate": round(fail_n / max(1, eval_n), 3),
                          "dataset_count": bucket_data.get((scene, task), 0),
                          "priority_score": round(fail_n * weight, 2)})
        tasks.sort(key=lambda r: -r["priority_score"])
        report = {"eval_total": total, "failure_total": len(fails),
                  "failure_rate": round(len(fails) / total, 3),
                  "failure_modes": dict(modes.most_common()),
                  "collection_tasks": tasks,
                  "advice": ("优先补采Top桶+失败模式对应场景"
                             if tasks else "无失败样本，检查评测分布")}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "loop_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"失败率 {report['failure_rate']:.0%}，"
          f"失败模式 {report['failure_modes']}")
    for t in tasks[:3]:
        print(f"  补采 {t['task']}@{t['scene']}: 失败{t['eval_failures']}次 "
              f"现数据{t['dataset_count']}条 score={t['priority_score']}")
    print(f"报告: {(args.out_dir / 'loop_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
