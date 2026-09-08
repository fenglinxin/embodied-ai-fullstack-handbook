# -*- coding: utf-8 -*-
"""第7章 L2 工业工程版：领域数据集打包 + 数据卡生成器。

输入：Episode JSON 目录（第1/2章产物），自动：
  * 校验必填元数据（episode_id/task/scene/success/language）
  * 生成数据卡（概览/授权/分布/质量/划分/已知问题/复现）
  * 按场景整体切分 train/val/test（防泄漏，复用第1章L3思想）

运行：见 README；示例数据可用第1章 demo 生成。
"""
from __future__ import annotations

import argparse, hashlib, json, logging, sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("dataset_builder")

REQUIRED = ("episode_id", "task", "scene", "success", "language")


@dataclass
class BuilderConfig:
    split_ratios: dict[str, float] = None  # type: ignore[assignment]
    auth: str = "internal-license"
    pipeline_version: str = "0.1.0"


def make_config() -> BuilderConfig:
    cfg = BuilderConfig()
    cfg.split_ratios = {"train": 0.8, "val": 0.1, "test": 0.1}
    return cfg


def plan_scenes(n_scenes: int, ratios: dict[str, float]) -> dict[str, int]:
    keys = list(ratios)
    if n_scenes < len(keys):
        return {"train": n_scenes, "val": 0, "test": 0}
    counts = {k: 1 for k in keys}
    rem = n_scenes - len(keys)
    if rem > 0:
        alloc = {k: int(rem * ratios[k]) for k in keys}
        left = rem - sum(alloc.values())
        for k in keys:
            counts[k] += alloc[k]
        order = sorted(keys, key=lambda k: (-(rem * ratios[k] - alloc[k]), k))
        for i in range(left):
            counts[order[i % len(order)]] += 1
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description="数据集打包与数据卡(工程版)")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--dataset-name", default="domain-embodied-v0")
    ap.add_argument("--auth", default="internal-license")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        files = sorted(args.data_dir.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"无 Episode JSON: {args.data_dir}")
        eps = [json.loads(f.read_text(encoding="utf-8")) for f in files]
        problems = []
        valid = []
        for ep in eps:
            missing = [k for k in REQUIRED if ep.get(k) is None]
            if missing:
                problems.append({"episode_id": ep.get("episode_id"),
                                 "missing": missing})
            else:
                valid.append(ep)
        cfg = make_config()
        cfg.auth = args.auth
        # 分布统计
        tasks = Counter(e["task"] for e in valid)
        scenes = Counter(e["scene"] for e in valid)
        success_rate = (sum(1 for e in valid if e["success"] is True)
                        / max(1, len(valid)))
        # 场景级切分
        scene_ids = sorted({e["scene"] for e in valid})
        counts = plan_scenes(len(scene_ids), cfg.split_ratios)
        buckets: dict[str, list[str]] = {k: [] for k in cfg.split_ratios}
        idx = 0
        for k in ["val", "test", "train"]:
            for _ in range(counts[k]):
                if idx < len(scene_ids):
                    buckets[k].append(scene_ids[idx]); idx += 1
        split = {k: [e["episode_id"] for e in valid if e["scene"] in set(v)]
                 for k, v in buckets.items()}
        card = {
            "dataset_name": args.dataset_name,
            "overview": {"episodes": len(valid), "tasks": len(tasks),
                         "scenes": len(scenes),
                         "raw_files": len(files)},
            "authorization": {"status": cfg.auth},
            "distribution": {"by_task": dict(tasks), "by_scene": dict(scenes),
                             "success_rate": round(success_rate, 4)},
            "processing": {"pipeline_version": cfg.pipeline_version},
            "quality": {"validation_problems": len(problems)},
            "split": {k: len(v) for k, v in split.items()},
            "known_issues": [f"{len(problems)} 条记录缺元数据"],
            "reproducibility": {
                "checksum": hashlib.sha256(
                    json.dumps([e["episode_id"] for e in valid],
                               ensure_ascii=False).encode()).hexdigest()[:16]},
        }
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "data_card.json").write_text(
        json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "split_manifest.json").write_text(
        json.dumps(split, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"数据卡: {card['dataset_name']} "
          f"{card['overview']['episodes']}条/任务{card['overview']['tasks']}"
          f"/场景{card['overview']['scenes']} 成功率{success_rate:.0%}")
    print(f"切分: {card['split']} | 元数据问题: {len(problems)}")
    print(f"输出: {(args.out_dir / 'data_card.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
