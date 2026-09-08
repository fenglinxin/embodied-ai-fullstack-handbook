# -*- coding: utf-8 -*-
"""第5章 L3 高阶优化版：分层采样权重 + 均衡度指标（训练直接可用）。

输出 train_manifest.csv：
  episode_id,task,scene,success,weight
权重规则：每桶等权(逆频) -> 归一化 -> 限幅(weight_cap)；
并输出均衡度(熵)与补采缺口，支撑"补采任务单"。

运行：
  python engineering_dedup_balance.py --input records.json --out-dir out
  python advanced_balance_sampling.py --input out/dedup_manifest.json --out-dir out
"""
from __future__ import annotations

import argparse, csv, json, logging, math, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("balance")

WEIGHT_CAP = 3.0


def entropy(p: list[float]) -> float:
    return -sum(x * math.log(x) for x in p if x > 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="分层采样权重生成(L3)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        recs = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(recs, list) or not recs:
            raise ValueError("输入须为非空数组(kept manifest)")
        counts: Counter = Counter((r["task"], r["scene"]) for r in recs)
        n_buckets = len(counts)
        # 每桶等权：逆频权重
        inv: dict[tuple, float] = {k: 1.0 / max(1, c) for k, c in counts.items()}
        mean_inv = sum(inv.values()) / n_buckets
        weights = {k: min(WEIGHT_CAP, v / mean_inv) for k, v in inv.items()}
        rows = []
        for r in recs:
            rows.append({"episode_id": r["episode_id"], "task": r["task"],
                         "scene": r["scene"], "success": r.get("success"),
                         "weight": round(weights[(r["task"], r["scene"])], 4)})
        # 均衡度：bucket 分布熵(归一化)
        probs = [c / len(recs) for c in counts.values()]
        balance = entropy(probs) / math.log(max(2, n_buckets))
        min_count = min(counts.values())
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_dir / "train_manifest.csv"
    with out_csv.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    report = {"episodes": len(rows), "buckets": n_buckets,
              "min_bucket_count": min_count,
              "balance_index_entropy": round(balance, 4),
              "weight_cap": WEIGHT_CAP,
              "weight_sample": {f"{k[0]}|{k[1]}": round(v, 3)
                                for k, v in list(weights.items())[:8]},
              "suggestion": ("建议先补采小桶，训练期分层采样只能兜底"
                             if min_count < 3 else "分布健康")}
    (args.out_dir / "balance_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"train_manifest: {report['episodes']} 条 / {report['buckets']} 桶 "
          f"均衡度={report['balance_index_entropy']}")
    print(f"最小桶={report['min_bucket_count']} -> {report['suggestion']}")
    print(f"输出: {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
