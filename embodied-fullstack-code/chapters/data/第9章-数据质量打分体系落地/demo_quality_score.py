# -*- coding: utf-8 -*-
"""第9章 L1 极简 Demo：五维质量打分（完整/正确/有效/多样/可复现）。

运行：python demo_quality_score.py
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def samples() -> list[dict]:
    return [
        {"episode_id": "ep-0000", "task": "pick", "scene": "a", "object": "mug",
         "success": True, "success_consistent": True, "ts_ok": True,
         "black_ratio": 0.0, "empty_ratio": 0.0, "has_language": True,
         "operator": "alice", "calib": "v3"},
        {"episode_id": "ep-0001", "task": "pick", "scene": "a", "object": "mug",
         "success": True, "success_consistent": False, "ts_ok": True,
         "black_ratio": 0.0, "empty_ratio": 0.0, "has_language": True,
         "operator": "bob", "calib": "v3"},
        {"episode_id": "ep-0002", "task": "pick", "scene": "b", "object": "box",
         "success": False, "success_consistent": True, "ts_ok": False,
         "black_ratio": 0.3, "empty_ratio": 0.0, "has_language": False,
         "operator": "alice", "calib": ""},
        {"episode_id": "ep-0003", "task": "place", "scene": "c", "object": "mug",
         "success": True, "success_consistent": True, "ts_ok": True,
         "black_ratio": 0.0, "empty_ratio": 0.9, "has_language": True,
         "operator": "carol", "calib": "v2"},
    ]


def score_ep(ep: dict) -> dict:
    comp = 1.0 if ep["black_ratio"] <= 0.05 else 0.4
    corr = 1.0 if ep["ts_ok"] and ep["empty_ratio"] <= 0.8 else 0.0
    eff = 1.0 if ep["success"] and ep["success_consistent"] else 0.3
    repro = sum([ep["has_language"], bool(ep["operator"]), bool(ep["calib"])]) / 3
    return {"completeness": comp, "correctness": corr,
            "effectiveness": eff, "reproducibility": repro}


def main() -> int:
    ap = argparse.ArgumentParser(description="五维打分Demo")
    ap.add_argument("--out", type=Path, default=Path("records.json"))
    args = ap.parse_args()
    eps = samples()
    rows = []
    for ep in eps:
        d = score_ep(ep)
        total = 0.25 * d["completeness"] + 0.30 * d["correctness"]             + 0.15 * d["effectiveness"] + 0.30 * d["reproducibility"]
        rows.append({"episode_id": ep["episode_id"], **d,
                     "quality_total": round(total, 3)})
        print(f"{ep['episode_id']}: 完整{d['completeness']:.2f} "
              f"正确{d['correctness']:.2f} 有效{d['effectiveness']:.2f} "
              f"可复现{d['reproducibility']:.2f} => {total:.3f}")
    args.out.write_text(json.dumps(eps, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print("规则：黑帧>5%或空动作>80%或时间戳断裂 => 正确性/完整性直接压分")
    return 0


if __name__ == "__main__":
    sys.exit(main())
