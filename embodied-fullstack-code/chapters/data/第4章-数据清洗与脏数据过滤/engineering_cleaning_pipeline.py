# -*- coding: utf-8 -*-
"""第4章 L2 工业工程版：规则化清洗流水线（P0删/P1人工/P2保留）。

输入：记录 JSON 数组（demo 输出或真实数据汇总卡字段）
输出：cleaned_manifest.json（每条决策+原因）+ removed.json + 分布对比

运行：
  python demo_cleaning_rules.py --out records.json
  python engineering_cleaning_pipeline.py --input records.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("cleaning")

P2_REASONS = ("失败样本",)          # 语义标记：P2 保留


@dataclass
class CleanConfig:
    black_ratio_max: float = 0.05
    action_empty_max: float = 0.80
    flag_on_inconsistent: bool = True
    keep_failures: bool = True       # 失败样本永远不删（困难池）
    required_fields: tuple[str, ...] = ("episode_id", "task", "scene", "success")


def load_config(p: Path | None) -> CleanConfig:
    cfg = CleanConfig()
    if p:
        raw = json.loads(p.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    return cfg


def decide(r: dict, cfg: CleanConfig) -> tuple[str, list[str]]:
    """返回 (decision, reasons)；decision ∈ KEEP/P1_FLAG/P0_DROP。"""
    reasons: list[str] = []
    if not r.get("ts_monotonic", True):
        return "P0_DROP", ["时间戳非单调"]
    if float(r.get("black_ratio", 0.0)) > cfg.black_ratio_max:
        reasons.append(f"黑帧{float(r['black_ratio']):.0%}")
    if float(r.get("action_empty_ratio", 0.0)) > cfg.action_empty_max:
        reasons.append("空动作")
    if reasons:
        return "P0_DROP", reasons
    if cfg.flag_on_inconsistent and r.get("success_consistent") is False:
        return "P1_FLAG", ["成功标记与末端位置矛盾(送人工)"]
    if cfg.keep_failures and r.get("success") is False:
        return "P2_KEEP", list(P2_REASONS)
    return "KEEP", []


def distributions(recs: list[dict]) -> dict[str, Any]:
    return {"total": len(recs),
            "success": sum(1 for r in recs if r.get("success") is True),
            "failure": sum(1 for r in recs if r.get("success") is False),
            "by_task": dict(Counter(r.get("task") for r in recs)),
            "by_scene": dict(Counter(r.get("scene") for r in recs))}


def main() -> int:
    ap = argparse.ArgumentParser(description="规则化清洗流水线(工程版)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--config", type=Path)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        cfg = load_config(args.config)
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        recs = [r for r in raw if isinstance(r, dict)]
        if not recs:
            raise ValueError("输入为空")
        before = distributions(recs)
        manifest = []
        for r in recs:
            decision, reasons = decide(r, cfg)
            manifest.append({**r, "decision": decision, "reasons": reasons})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "cleaned_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    removed = [m for m in manifest if m["decision"] == "P0_DROP"]
    flagged = [m for m in manifest if m["decision"] == "P1_FLAG"]
    kept = [m for m in manifest if m["decision"] in ("KEEP", "P2_KEEP")]
    after = distributions(kept)
    (args.out_dir / "removed.json").write_text(
        json.dumps(removed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"清洗统计: 总数{before['total']} -> 保留{len(kept)} "
          f"(P0删除{len(removed)}, P1人工{len(flagged)})")
    print(f"分布变化: task {before['by_task']} -> {after['by_task']}")
    print(f"失败样本: {before['failure']} -> {after['failure']} "
          f"(困难池保护={cfg.keep_failures})")
    print(f"报告: {(args.out_dir / 'cleaned_manifest.json').resolve()}")
    return 0 if not removed else 1


if __name__ == "__main__":
    sys.exit(main())
