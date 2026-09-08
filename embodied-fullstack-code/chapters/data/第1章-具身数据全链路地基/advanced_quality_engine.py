# -*- coding: utf-8 -*-
"""第1章 L3 高阶优化版：数据集级去重/覆盖/切分/数据卡（数据资产化）。

相对 L2 增加：
  1) 动作指纹去重候选识别（含"元数据级重复"兜底）
  2) 任务×场景覆盖矩阵与欠覆盖告警（第5章场景矩阵思想的代码化）
  3) 按场景整体切分 train/val/test，杜绝数据泄漏
  4) 数据卡(data card)自动生成（第7章数据卡字段落地）
  5) 质量门禁汇总（接 L2 五维分）

依赖：仅标准库；复用同目录 engineering_data_pipeline 的体检函数。
运行：
  python advanced_quality_engine.py --data-dir ../demo_data --out-dir ./out
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from engineering_data_pipeline import QualityConfig, inspect_episode, load_config

logger = logging.getLogger("data_advanced")

DEFAULT_SPLIT = {"train": 0.8, "val": 0.1, "test": 0.1}
MIN_COVERAGE = 1          # 任务×场景组合最少条数（演示数据用小值，项目按需求调大）


def load_episodes(data_dir: Path) -> list[dict]:
    files = sorted(data_dir.glob("*.json"))
    if not files:
        raise RuntimeError(f"目录无 Episode JSON: {data_dir}")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


# ---------------------------------------------------------------- 1. 去重候选
def _action_fingerprint(ep: dict) -> str | None:
    """动作增量量化后的滚动指纹；无动作向量时返回 None 走元数据兜底。"""
    act = (ep.get("channels") or {}).get("action") or {}
    cmds = act.get("cmds")
    if not cmds:
        return None
    quant = []
    for cmd in cmds:
        try:
            vals = [round(float(v) / 0.02) for v in cmd]   # 2cm/2deg 量化桶
            quant.append(",".join(str(int(v)) for v in vals))
        except (TypeError, ValueError):
            return None
    digest = hashlib.sha1("|".join(quant).encode()).hexdigest()[:16]
    return digest


def meta_fingerprint(ep: dict) -> str:
    """元数据级指纹：同任务+同场景+同物体视为重复候选（保守兜底）。"""
    s = f"{ep.get('task')}|{ep.get('scene')}|{ep.get('object')}"
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def find_duplicate_candidates(eps: list[dict]) -> list[dict[str, Any]]:
    """返回重复候选组（动作指纹优先，缺失时退化为元数据指纹）。"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for ep in eps:
        fp = _action_fingerprint(ep) or ("meta:" + meta_fingerprint(ep))
        groups[fp].append(ep)
    out = []
    for fp, members in groups.items():
        if len(members) > 1:
            out.append({"fingerprint": fp,
                        "episodes": [m["episode_id"] for m in members],
                        "kind": "action" if not fp.startswith("meta:") else "metadata"})
    return sorted(out, key=lambda g: -len(g["episodes"]))


# ---------------------------------------------------------------- 2. 覆盖矩阵
def coverage_report(eps: list[dict]) -> dict[str, Any]:
    matrix: Counter = Counter((e.get("task"), e.get("scene")) for e in eps)
    under: list[dict[str, Any]] = []
    for (task, scene), count in sorted(matrix.items()):
        if count < MIN_COVERAGE:
            under.append({"task": task, "scene": scene, "count": count})
    empty_scenes = sorted({e.get("scene") for e in eps}
                          - {s for (_, s) in matrix})
    return {"matrix": [{"task": t, "scene": s, "count": c}
                       for (t, s), c in sorted(matrix.items())],
            "under_covered": under,
            "scenes_without_task": empty_scenes}


# ---------------------------------------------------------------- 3. 场景级切分
def _split_plan(total: int, ratios: dict[str, float]) -> dict[str, int]:
    """按比例规划各 split 场景数；样本少时保证每类至少 1 个场景。"""
    keys = list(ratios)
    if total < len(keys):
        return {"train": total, "val": 0, "test": 0}
    counts = {k: 1 for k in keys}                       # 先保证三类都有
    rem = total - len(keys)
    if rem > 0:
        alloc = {k: int(rem * ratios[k]) for k in keys}
        left = rem - sum(alloc.values())
        for k in keys:
            counts[k] += alloc[k]
        # 余量按小数部分从大到小分配（确定性：固定顺序决胜负）
        order = sorted(keys, key=lambda k: (-(rem * ratios[k] - alloc[k]), k))
        for i in range(left):
            counts[order[i % len(order)]] += 1
    return counts


def scene_split(eps: list[dict], ratios: dict[str, float]) -> dict[str, Any]:
    """按 scene 整体切分：同一个 scene 只会进入一个集合，防泄漏。"""
    scene_ids = sorted({e["scene"] for e in eps})
    if len(scene_ids) < len(ratios):
        logger.warning("场景数 %d 少于切分数 %d，部分集合可能为空",
                       len(scene_ids), len(ratios))
    counts = _split_plan(len(scene_ids), ratios)
    buckets: dict[str, list[str]] = {k: [] for k in ratios}
    idx = 0
    for k in ["val", "test", "train"]:                 # val/test 先取，train 收尾
        for _ in range(counts.get(k, 0)):
            if idx < len(scene_ids):
                buckets[k].append(scene_ids[idx]); idx += 1
    out: dict[str, list[str]] = {}
    for k, scenes in buckets.items():
        bucket_scenes = set(scenes)
        out[k] = [e["episode_id"] for e in eps if e["scene"] in bucket_scenes]
    return {"ratios": ratios, "scenes_per_split": {k: len(v) for k, v in buckets.items()},
            "episodes_per_split": {k: len(v) for k, v in out.items()},
            "split": out}


# ---------------------------------------------------------------- 4. 数据卡
def build_data_card(eps: list[dict], per: list[dict]) -> dict[str, Any]:
    scenes = {e.get("scene") for e in eps}
    tasks = {e.get("task") for e in eps}
    success_rate = (sum(1 for e in eps if e.get("success") is True)
                    / max(1, len(eps)))
    black_total = 0
    frame_total = 0
    for e in eps:
        rgb = (e.get("channels") or {}).get("rgb") or {}
        blk = rgb.get("black") or []
        black_total += sum(blk)
        frame_total += len(rgb.get("ts") or blk)
    hard = sum(len(r["issues_hard"]) for r in per)
    return {
        "episodes": len(eps), "tasks": len(tasks), "scenes": len(scenes),
        "success_rate": round(success_rate, 4),
        "black_frame_ratio": round(black_total / max(1, frame_total), 4),
        "hard_issue_count": hard,
        "checksum": hashlib.sha256(
            json.dumps([e.get("episode_id") for e in eps],
                       ensure_ascii=False).encode()).hexdigest()[:16],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="具身数据集高级质检(去重/覆盖/切分/数据卡)")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        cfg: QualityConfig = load_config(args.config)
        eps = load_episodes(args.data_dir)
        per = [inspect_episode(e, cfg) for e in eps]
        report = {
            "duplicate_candidates": find_duplicate_candidates(eps),
            "coverage": coverage_report(eps),
            "scene_split": scene_split(eps, DEFAULT_SPLIT),
            "data_card": build_data_card(eps, per),
            "quality_verdict": "pass" if not any(r["issues_hard"] for r in per)
                               else "review",
        }
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "advanced_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    dc = report["data_card"]
    dup = report["duplicate_candidates"]
    cov = report["coverage"]
    print(f"数据卡: {dc['episodes']}条/任务{dc['tasks']}/场景{dc['scenes']} "
          f"成功率{dc['success_rate']:.0%}")
    print(f"重复候选组: {len(dup)} 组 "
          f"({sum(len(g['episodes']) - 1 for g in dup)} 条冗余)")
    print(f"欠覆盖组合: {len(cov['under_covered'])} 个")
    sp = report["scene_split"]["episodes_per_split"]
    print(f"场景级切分: train={sp['train']} val={sp['val']} test={sp['test']}")
    print(f"门禁: {report['quality_verdict']}")
    print(f"报告: {(args.out_dir / 'advanced_report.json').resolve()}")
    return 0 if report["quality_verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
