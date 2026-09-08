# -*- coding: utf-8 -*-
"""第7章 L3 高阶优化版：数据集注册表 + 就绪度评分 + 版本对比。

能力：
  * --add 把 data_card.json 注册为带 tag 的数据集版本
  * 就绪度评分：覆盖率/成功率/失败样本/元数据 四维加权
  * 版本对比：与上一版本 diff（Episode 数/任务/场景/成功率）
  * 输出 registry_status.json + 下一轮采集建议

运行：
  python engineering_dataset_builder.py --data-dir ... --out-dir out
  python advanced_data_registry.py --registry reg --add out/data_card.json --tag v0.1
"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("data_registry")

WEIGHTS = {"coverage": 0.4, "success": 0.2, "failure": 0.2, "metadata": 0.2}


def readiness(card: dict) -> dict[str, Any]:
    ov = card.get("overview", {})
    dist = card.get("distribution", {})
    q = card.get("quality", {})
    eps = max(1, ov.get("episodes", 0))
    n_scenes = max(1, ov.get("scenes", 0))
    n_tasks = max(1, ov.get("tasks", 0))
    coverage = min(1.0, (n_scenes * n_tasks) / 4.0)     # 简单 2x2 覆盖目标
    success = dist.get("success_rate", 0.0)
    failure = 1.0 - success
    failure_ok = min(1.0, failure / 0.1)                # 目标失败占比>=10%
    metadata_ok = 1.0 if q.get("validation_problems", 1) == 0 else 0.0
    dims = {"coverage": round(coverage, 3), "success": round(min(1.0, success / 0.9), 3),
            "failure": round(failure_ok, 3), "metadata": metadata_ok}
    score = sum(dims[k] * WEIGHTS[k] for k in WEIGHTS)
    return {"dims": dims, "score": round(score, 3),
            "verdict": "ready" if score >= 0.75 else "collect-more"}


def diff_card(prev: dict, cur: dict) -> dict[str, Any]:
    po, co = prev.get("overview", {}), cur.get("overview", {})
    pd, cd = prev.get("distribution", {}), cur.get("distribution", {})
    return {"episodes": co.get("episodes", 0) - po.get("episodes", 0),
            "tasks": co.get("tasks", 0) - po.get("tasks", 0),
            "scenes": co.get("scenes", 0) - po.get("scenes", 0),
            "success_rate_delta": round(
                cd.get("success_rate", 0.0) - pd.get("success_rate", 0.0), 4)}


def main() -> int:
    ap = argparse.ArgumentParser(description="数据集注册表(L3)")
    ap.add_argument("--registry", required=True, type=Path)
    ap.add_argument("--add", type=Path, default=None, help="待注册的 data_card.json")
    ap.add_argument("--tag", default="untagged")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        args.registry.mkdir(parents=True, exist_ok=True)
        card = json.loads(args.add.read_text(encoding="utf-8")) if args.add else {}
        if not card:
            raise ValueError("--add 指向的 data_card.json 为空/缺失")
        rd = readiness(card)
        prev = None
        tags = sorted(args.registry.glob("data_card_*.json"))
        if tags:
            prev = json.loads(tags[-1].read_text(encoding="utf-8"))
        diff = diff_card(prev, card) if prev else None
        out_name = args.registry / f"data_card_{args.tag}.json"
        out_name.write_text(json.dumps(card, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        status = {"tag": args.tag, "readiness": rd,
                  "diff_vs_previous": diff,
                  "latest": str(out_name),
                  "suggestion": ("补采欠覆盖组合与失败样本后再注册"
                                 if rd["verdict"] == "collect-more"
                                 else "可进入训练/评测阶段")}
        (args.registry / "registry_status.json").write_text(
            json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    print(f"注册 {args.tag}: 就绪度 {rd['score']} ({rd['verdict']})")
    if diff:
        print(f"较上一版: Episode{ diff['episodes']:+d} "
              f"场景{diff['scenes']:+d} 成功率{diff['success_rate_delta']:+.1%}")
    print("建议:", status["suggestion"])
    print(f"状态: {(args.registry / 'registry_status.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
