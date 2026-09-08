# -*- coding: utf-8 -*-
"""第9章 L3 高阶优化版：双人盲审一致性 + 自动-人工校准 + 版本趋势。

实现文章第4章/第9章的质量运营要求：
  * 两位评审对同批打分的"一致性"（分差<=0.1 视为一致）
  * 自动分 vs 人工分校准偏差（bias）与边缘区抽审建议
  * 与上一版 quality report 对比（avg/边缘区数量趋势）

运行：
  python engineering_quality_engine.py --input records.json \
      --review reviewers_a.json --out-dir out
  python advanced_quality_ops.py --report out/quality_engine_report.json \
      --reviewer-a reviewers_a.json --reviewer-b reviewers_b.json \
      --previous old_report.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("quality_ops")
AGREE_TOL = 0.10


def load_scores(p: Path | None) -> dict[str, float]:
    if not p:
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {str(r["episode_id"]): float(r["score_manual"])
                for r in raw if "episode_id" in r}
    return {str(k): float(v) for k, v in raw.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description="质量运营分析(L3)")
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--reviewer-a", type=Path)
    ap.add_argument("--reviewer-b", type=Path)
    ap.add_argument("--previous", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        rep = json.loads(args.report.read_text(encoding="utf-8"))
        a = load_scores(args.reviewer_a)
        b = load_scores(args.reviewer_b)
        common = sorted(set(a) & set(b))
        agree = [k for k in common if abs(a[k] - b[k]) <= AGREE_TOL]
        auto_map = {str(r["episode_id"]): r["total"] for r in rep["per_episode"]}
        shared = sorted(set(a) & set(auto_map))
        gaps = [{"episode_id": k, "auto": auto_map[k], "human": a[k],
                 "gap": round(auto_map[k] - a[k], 3)} for k in shared
                if abs(auto_map[k] - a[k]) > 0.15]
        trend = None
        if args.previous and args.previous.exists():
            prev = json.loads(args.previous.read_text(encoding="utf-8"))
            trend = {"avg_delta": round(rep["avg_score"] - prev.get("avg_score", 0), 4),
                     "edge_delta": (rep.get("edge_zone_count", 0)
                                    - prev.get("edge_zone_count", 0))}
        ops = {"reviewer_agreement": {"pairs": len(common),
                                      "agree": len(agree),
                                      "rate": round(len(agree) / max(1, len(common)), 3)
                                      if common else None,
                                      "disagree_ids": [k for k in common
                                                       if k not in agree]},
               "auto_human_calibration": {"gaps_over_0_15": gaps},
               "trend_vs_previous": trend,
               "advice": ("细则需要修订：双人一致率<0.9"
                          if common and len(agree) / len(common) < 0.9
                          else ("校准建议：自动分与人工分偏差>0.15 共 " + str(len(gaps)) + " 条，需用人工分校准规则阈值" if gaps else "评审细则可用"))}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "quality_ops_report.json").write_text(
        json.dumps(ops, ensure_ascii=False, indent=2), encoding="utf-8")
    print("双人一致率:",
          ops["reviewer_agreement"]["rate"] or "无共同样本")
    if ops["reviewer_agreement"]["disagree_ids"]:
        print("不一致样本:", ops["reviewer_agreement"]["disagree_ids"][:5])
    print("自动-人工偏差>0.15:", len(gaps), "条")
    if trend:
        print(f"趋势: avg {trend['avg_delta']:+.3f} "
              f"边缘区 {trend['edge_delta']:+d}")
    print("建议:", ops["advice"])
    print(f"报告: {(args.out_dir / 'quality_ops_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
