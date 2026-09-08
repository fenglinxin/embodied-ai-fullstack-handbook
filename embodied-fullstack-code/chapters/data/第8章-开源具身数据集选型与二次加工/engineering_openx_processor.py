# -*- coding: utf-8 -*-
"""第8章 L2 工业工程版：开源数据集目录加工（语言统一/任务筛选/动作空间登记）。

输入目录约定：
  <input>/<source>/episodes.json   （数组；字段见 demo_openx_mini）
输出：
  processed_manifest.json（统一 language/source/action_space/requires_ik）
  processing_report.json（来源统计/命中任务/动作空间分布/需IK数量）

运行：
  python engineering_openx_processor.py --input-dir ./sample_sources --out-dir out
  （--make-sample 可在空目录先生成演示样例）
"""
from __future__ import annotations

import argparse, json, logging, sys
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger("openx_processor")

LANG_KEYS = ("instruction_text", "task_desc", "language_instruction",
             "language", "instruction")
ACTION_KEYS = ("action_delta", "ee_delta", "joint_positions", "actions")
LANG_TARGET = "instruction"


def make_sample(root: Path) -> None:
    (root / "openx_a").mkdir(parents=True, exist_ok=True)
    (root / "openx_b").mkdir(parents=True, exist_ok=True)
    a = [{"episode_id": "a-0001", "instruction_text": "pick red cup",
          "action_delta": [[0.01 * i, 0, 0, 0] for i in range(5)],
          "success": True},
         {"episode_id": "a-0002", "instruction_text": "place red cup on tray",
          "action_delta": [[0.0, 0.01 * i, 0, 0] for i in range(5)],
          "success": True}]
    b = [{"episode_id": "b-0001", "task_desc": "pick red cup",
          "joint_positions": [[0.1, 0.2, 0.3] for _ in range(5)],
          "success": True},
         {"episode_id": "b-0002", "task_desc": "wipe table",
          "joint_positions": [[0.1, 0.2, 0.4] for _ in range(5)],
          "success": False}]
    (root / "openx_a" / "episodes.json").write_text(
        json.dumps(a, ensure_ascii=False), encoding="utf-8")
    (root / "openx_b" / "episodes.json").write_text(
        json.dumps(b, ensure_ascii=False), encoding="utf-8")


def detect(ep: dict) -> tuple[str, int | None, str | None]:
    """返回 (动作空间, 维度, 动作字段名)。"""
    for key in ACTION_KEYS:
        if key in ep and ep[key]:
            return ("ee_delta" if "delta" in key or key == "ee_delta"
                    else "joint_abs", len(ep[key][0]), key)
    return ("unknown", None, None)


def main() -> int:
    ap = argparse.ArgumentParser(description="开源数据加工(工程版)")
    ap.add_argument("--input-dir", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--task-keywords", nargs="*", default=[])
    ap.add_argument("--make-sample", action="store_true")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample and not any(args.input_dir.glob("*")):
            make_sample(args.input_dir)
            logger.info("已生成演示 sources: %s", args.input_dir)
        out_list: list[dict] = []
        stats: dict[str, Any] = {"per_source": Counter(), "space": Counter(),
                                 "keywords_hit": Counter()}
        for src_dir in sorted(p for p in args.input_dir.iterdir() if p.is_dir()):
            ep_file = src_dir / "episodes.json"
            if not ep_file.exists():
                continue
            eps = json.loads(ep_file.read_text(encoding="utf-8"))
            for ep in eps:
                lang = next((str(ep[k]) for k in LANG_KEYS if ep.get(k)), "")
                if args.task_keywords and not any(
                        kw.lower() in lang.lower() for kw in args.task_keywords):
                    continue
                space, dim, key = detect(ep)
                stats["per_source"][src_dir.name] += 1
                stats["space"][space] += 1
                if args.task_keywords:
                    stats["keywords_hit"]["match"] += 1
                out_list.append({
                    "episode_id": ep["episode_id"],
                    "source": src_dir.name,
                    "instruction": lang,
                    "action_space": space,
                    "action_dim": dim,
                    "requires_ik": space == "joint_abs",
                    "success": ep.get("success"),
                    "ts_ns": [int(i * 33_333_333) for i in range(
                        len(ep.get(key, [])))],
                })
        if not out_list:
            raise RuntimeError("处理后为空（检查 task-keywords 或输入结构）")
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "processed_manifest.json").write_text(
        json.dumps(out_list, ensure_ascii=False, indent=2), encoding="utf-8")
    stats["total"] = len(out_list)
    (args.out_dir / "processing_report.json").write_text(
        json.dumps({k: dict(v) if isinstance(v, Counter) else v
                    for k, v in stats.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"加工完成: {stats['total']} 条 (需IK/本体无关化处理: "
          f"{sum(1 for r in out_list if r['requires_ik'])})")
    print("动作空间分布:", dict(stats["space"]))
    print(f"报告: {(args.out_dir / 'processing_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
