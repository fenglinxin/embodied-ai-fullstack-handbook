# -*- coding: utf-8 -*-
"""第4章 L3 高阶优化版：过度清洗防护（多样性/失败样本保底 + 分布漂移审计）。

工程痛点（文章核心）：洗得太干净比脏更危险。
本脚本在 L2 规则之上加三道闸：
  1) 桶保底：任何 (task,scene) 桶不得低于 min_bucket
  2) 失败保底：全量失败占比不得低于 min_failure_ratio
  3) 漂移审计：输出清洗前后分布 JS 散度(KL 简化) 供人决策

依赖：同目录 demo_cleaning_rules.classify 仅用于演示；真实项目可换成 L2 decide。
运行：
  python engineering_cleaning_pipeline.py --input records.json --out-dir out
  python advanced_overclean_guard.py --input records.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger("overclean_guard")


@dataclass
class GuardConfig:
    min_bucket: int = 1                # 每个 task×scene 桶最少保留条数
    min_failure_ratio: float = 0.10    # 失败样本保底占比
    black_max: float = 0.05
    empty_max: float = 0.80


def kl_div(p: dict[str, float], q: dict[str, float]) -> float:
    """分布差异（加平滑防除零）。"""
    keys = set(p) | set(q)
    eps = 1e-9
    out = 0.0
    for k in keys:
        pk = p.get(k, 0.0) + eps
        qk = q.get(k, 0.0) + eps
        out += pk * math.log(pk / qk)
    return out


def bucket_id(r: dict) -> str:
    return f"{r.get('task')}|{r.get('scene')}"


def guard(rules_out: list[dict], cfg: GuardConfig) -> tuple[list[dict], list[str]]:
    """对规则结果做保底恢复；返回(最终清单, 恢复记录)。"""
    # 先按规则意愿分类
    by_id = {m["episode_id"]: m for m in rules_out}
    drop_ids = {m["episode_id"] for m in rules_out if m["decision"] == "P0_DROP"}
    # 桶保底：每个桶至少 min_bucket 条（优先恢复非空动作、时间戳正常的）
    buckets: dict[str, list[dict]] = defaultdict(list)
    for m in rules_out:
        if m["episode_id"] not in drop_ids or m.get("success") is False:
            buckets[bucket_id(m)].append(m)
        else:
            buckets[bucket_id(m)].append(m)   # 先把所有人放桶里再决定
    final = [m for m in rules_out if m["episode_id"] not in drop_ids]
    restored: list[str] = []
    # 统计每桶实际保留
    final_by_bucket: Counter = Counter(bucket_id(m) for m in final)
    for m in sorted(rules_out, key=lambda x: x["episode_id"]):
        bid = bucket_id(m)
        if m["episode_id"] not in drop_ids:
            continue
        if final_by_bucket[bid] < cfg.min_bucket and m.get("success") is False:
            # 桶太空：优先恢复失败样本（困难池），再恢复普通
            pass
    # 简化稳健实现：逐桶处理
    for bid in sorted(set(bucket_id(m) for m in rules_out)):
        members = [m for m in rules_out if bucket_id(m) == bid]
        keep_cnt = sum(1 for m in members if m["episode_id"] not in drop_ids)
        for m in sorted(members, key=lambda x: (x.get("success") is True, x["episode_id"])):
            if keep_cnt >= cfg.min_bucket:
                break
            if m["episode_id"] in drop_ids:
                m["decision"] = "KEEP"
                m["reasons"] = ["过洗保护-桶保底恢复"]
                restored.append(m["episode_id"])
                keep_cnt += 1
    final = [m for m in rules_out if m["decision"] != "P0_DROP"]
    # 失败保底
    fail_cnt = sum(1 for m in final if m.get("success") is False)
    ratio = fail_cnt / max(1, len(final))
    if ratio < cfg.min_failure_ratio:
        for m in sorted(rules_out,
                        key=lambda x: (x.get("success") is True, x["episode_id"])):
            if m["decision"] == "P0_DROP" and m.get("success") is False:
                m["decision"] = "P2_KEEP"
                m["reasons"] = ["过洗保护-失败样本保底"]
                restored.append(m["episode_id"])
                fail_cnt += 1
                ratio = fail_cnt / max(1, len(final) + (len(restored)))
                if ratio >= cfg.min_failure_ratio:
                    break
    final = [m for m in rules_out if m["decision"] != "P0_DROP"]
    return final, restored


def main() -> int:
    ap = argparse.ArgumentParser(description="过度清洗防护审计(L3)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        rules_out = []
        for r in raw:
            if not isinstance(r, dict):
                continue
            ts_ok = r.get("ts_monotonic", True)
            black = float(r.get("black_ratio", 0.0))
            empty = float(r.get("action_empty_ratio", 0.0))
            if not ts_ok or black > GuardConfig().black_max or empty > GuardConfig().empty_max:
                decision = "P0_DROP"
                reasons = ["规则命中"]
            elif r.get("success_consistent") is False:
                decision = "P1_FLAG"; reasons = ["语义可疑"]
            elif r.get("success") is False:
                decision = "P2_KEEP"; reasons = ["失败样本"]
            else:
                decision = "KEEP"; reasons = []
            rules_out.append({**r, "decision": decision, "reasons": reasons})
        cfg = GuardConfig()
        final, restored = guard(rules_out, cfg)
    except Exception as exc:
        logger.error("执行失败: %s", exc); return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    before = Counter(bucket_id(m) for m in raw if isinstance(m, dict))
    after = Counter(bucket_id(m) for m in final)
    # 分布漂移 KL（task 维度）
    def norm(c: Counter) -> dict[str, float]:
        t = sum(c.values()) or 1
        return {k: v / t for k, v in c.items()}
    drift = kl_div(norm(Counter(m.get("task") for m in raw if isinstance(m, dict))),
                   norm(Counter(m.get("task") for m in final)))
    report = {"before_total": len(raw), "after_total": len(final),
              "restored_count": len(restored), "restored": restored,
              "bucket_before": dict(before), "bucket_after": dict(after),
              "task_distribution_kl": round(drift, 5),
              "failure_ratio_after": round(
                  sum(1 for m in final if m.get("success") is False) / max(1, len(final)), 4),
              "final": final}
    (args.out_dir / "overclean_guard_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"过洗防护: 规则删除后自动恢复 {len(restored)} 条 "
          f"(桶保底+失败保底), 最终 {len(final)} 条")
    print(f"task 分布漂移 KL={report['task_distribution_kl']} "
          f"失败占比={report['failure_ratio_after']}")
    print(f"报告: {(args.out_dir / 'overclean_guard_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
