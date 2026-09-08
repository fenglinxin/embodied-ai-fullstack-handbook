# -*- coding: utf-8 -*-
"""第5章 L2 工业工程版：轨迹指纹去重 + 欠覆盖报告。

能力：
  * 动作序列量化指纹（可配桶大小）分组
  * 每组保留 1 成功 + N 失败（失败保护），其余进 removed
  * task×scene 覆盖统计与补采任务单（欠覆盖提示）

运行：
  python demo_dedup_balance.py --out records.json
  python engineering_dedup_balance.py --input records.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("dedup_balance")


@dataclass
class DedupConfig:
    quant: float = 0.02          # 动作量化桶（米/弧度）
    keep_failures_per_group: int = 2   # 每组最多保留的失败样本数
    min_per_bucket: int = 3      # task×scene 覆盖底线
    max_per_bucket: int = 10     # 单桶上限（超出进 redundant）


def load_config(p: Path | None) -> DedupConfig:
    cfg = DedupConfig()
    if p:
        raw = json.loads(p.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    return cfg


def fingerprint(traj, q: float) -> str:
    parts = []
    for pnt in traj:
        parts.append(",".join(str(int(round(float(v) / q))) for v in pnt))
    return "|".join(parts)


def bucket_key(r: dict) -> tuple[str, str]:
    return (str(r.get("task")), str(r.get("scene")))


def run(recs: list[dict], cfg: DedupConfig) -> dict[str, Any]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        fp = fingerprint(r.get("trajectory", []), cfg.quant)
        groups[str(r.get("task")) + "|" + str(r.get("scene")) + "|" + fp].append(r)
    kept, removed = [], []
    for members in groups.values():
        suc = [m for m in members if m.get("success") is True]
        fail = [m for m in members if m.get("success") is False]
        keep_now = suc[:1] + fail[:cfg.keep_failures_per_group]
        if not keep_now:
            keep_now = members[:1]
        kept.extend(keep_now)
        removed.extend(m for m in members if m not in keep_now)
    # 单桶上限（防"同一个故事讲50遍"）
    counts: Counter = Counter(bucket_key(r) for r in kept)
    overflow = []
    for r in list(kept):
        if counts[bucket_key(r)] > cfg.max_per_bucket:
            kept.remove(r)
            removed.append(r)
            overflow.append(r["episode_id"])
            counts[bucket_key(r)] -= 1
    after = Counter(bucket_key(r) for r in kept)
    under = [{"task": t, "scene": s, "count": c}
             for (t, s), c in sorted(after.items()) if c < cfg.min_per_bucket]
    return {"input": len(recs), "output": len(kept),
            "removed": [r["episode_id"] for r in removed],
            "overflow_removed": overflow,
            "failure_before": sum(1 for r in recs if r.get("success") is False),
            "failure_after": sum(1 for r in kept if r.get("success") is False),
            "bucket_distribution": {f"{t}|{s}": c for (t, s), c in sorted(after.items())},
            "under_covered": under,
            "kept": kept}


def main() -> int:
    ap = argparse.ArgumentParser(description="去重与均衡(工程版)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--config", type=Path)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        cfg = load_config(args.config)
        recs = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(recs, list):
            raise ValueError("输入须为数组")
        rep = run([r for r in recs if isinstance(r, dict)], cfg)
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = [{"episode_id": r["episode_id"], "task": r["task"],
                 "scene": r["scene"], "success": r["success"],
                 "status": "kept"} for r in rep["kept"]]
    (args.out_dir / "dedup_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "dedup_report.json").write_text(
        json.dumps({k: v for k, v in rep.items() if k != "kept"},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"去重: {rep['input']} -> {rep['output']} "
          f"(冗余 {len(rep['removed'])})")
    print(f"失败样本: {rep['failure_before']} -> {rep['failure_after']} (保护生效)")
    print(f"欠覆盖组合: {len(rep['under_covered'])} 个 -> 建议补采")
    for u in rep["under_covered"][:5]:
        print("  ", u)
    print(f"报告: {(args.out_dir / 'dedup_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
