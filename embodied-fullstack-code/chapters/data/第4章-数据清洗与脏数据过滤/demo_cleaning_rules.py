# -*- coding: utf-8 -*-
"""第4章 L1 极简 Demo：三类脏数据分级（损坏删/语义修/困难留）。

用合成记录演示第4章核心规则分级：
  P0 物理损坏 -> 删除/返工
  P1 语义可疑 -> 标记送人工
  P2 困难/失败 -> 必须保留（防"洗太干净"）

运行：python demo_cleaning_rules.py --out records.json
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def synthetic_records() -> list[dict]:
    """制造 8 条覆盖 P0/P1/P2 的演示记录。"""
    return [
        {"episode_id": "ep-0000", "task": "pick", "scene": "a", "success": True,
         "black_ratio": 0.0, "ts_monotonic": True, "action_empty_ratio": 0.0,
         "success_consistent": True},
        {"episode_id": "ep-0001", "task": "pick", "scene": "a", "success": True,
         "black_ratio": 0.30, "ts_monotonic": True, "action_empty_ratio": 0.0,
         "success_consistent": True},     # P0 花屏
        {"episode_id": "ep-0002", "task": "pick", "scene": "b", "success": True,
         "black_ratio": 0.0, "ts_monotonic": False, "action_empty_ratio": 0.0,
         "success_consistent": True},     # P0 时间戳断裂
        {"episode_id": "ep-0003", "task": "pick", "scene": "b", "success": True,
         "black_ratio": 0.0, "ts_monotonic": True, "action_empty_ratio": 0.95,
         "success_consistent": True},     # P0 空动作
        {"episode_id": "ep-0004", "task": "place", "scene": "c", "success": True,
         "black_ratio": 0.0, "ts_monotonic": True, "action_empty_ratio": 0.0,
         "success_consistent": False},    # P1 成功标记可疑
        {"episode_id": "ep-0005", "task": "place", "scene": "c", "success": False,
         "black_ratio": 0.0, "ts_monotonic": True, "action_empty_ratio": 0.0,
         "success_consistent": True},     # P2 失败样本（保留）
        {"episode_id": "ep-0006", "task": "place", "scene": "d", "success": True,
         "black_ratio": 0.02, "ts_monotonic": True, "action_empty_ratio": 0.0,
         "success_consistent": True},     # 干净
        {"episode_id": "ep-0007", "task": "pick", "scene": "d", "success": True,
         "black_ratio": 0.0, "ts_monotonic": True, "action_empty_ratio": 0.0,
         "success_consistent": True},     # 干净
    ]


def classify(r: dict) -> tuple[str, list[str]]:
    level, reasons = "KEEP", []
    if not r["ts_monotonic"]:
        level, reasons = "P0_DROP", ["时间戳非单调"]
    elif r["black_ratio"] > 0.05:
        level, reasons = "P0_DROP", [f"黑帧{ r['black_ratio']:.0%}>5%"]
    elif r["action_empty_ratio"] > 0.8:
        level, reasons = "P0_DROP", ["空动作>80%"]
    elif not r["success_consistent"]:
        level, reasons = "P1_FLAG", ["成功标记与末端位置矛盾(送人工)"]
    elif r["success"] is False:
        level, reasons = "P2_KEEP", ["失败样本-保留进困难池"]
    return level, reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="脏数据分级 Demo")
    ap.add_argument("--out", type=Path, default=Path("records.json"))
    args = ap.parse_args()
    recs = synthetic_records()
    dec = []
    print(f"{'episode_id':<10}{'级别':<10}原因")
    for r in recs:
        level, reasons = classify(r)
        dec.append({**r, "decision": level, "reasons": reasons})
        print(f"{r['episode_id']:<10}{level:<10}{';'.join(reasons)}")
    kept = [d for d in dec if d["decision"] in ("P2_KEEP", "KEEP")]
    print(f"\n保留 {len(kept)}/{len(dec)}；P0 物理损坏删除，P1 送人工，P2 困难样本必须留。")
    args.out.write_text(json.dumps(dec, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
