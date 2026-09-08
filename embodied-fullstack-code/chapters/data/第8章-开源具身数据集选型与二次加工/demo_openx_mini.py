# -*- coding: utf-8 -*-
"""第8章 L1 极简 Demo：异构开源 Episode 的格式统一与动作空间探测。

演示两大翻车点：
  1) 语言字段命名不一（instruction/language_text/task_desc）
  2) 动作空间不一（末端增量 4 维 vs 关节角 7 维）——只做"归一化记录+告警"，
     真实转换需机器人运动学（见 L2/L3 与第24章适配思想）。

运行：python demo_openx_mini.py
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

# 两个"开源子集"的最小样例（字段故意不一致）
SAMPLE = [
    {"source": "openx_a", "episode_id": "a-0001", "instruction_text": "pick cup",
     "obs": {"img": 1}, "action_delta": [[0.01, 0.0, 0.0, 0.0] for _ in range(5)],
     "success": True},
    {"source": "openx_b", "episode_id": "b-0002", "task_desc": "place cup on tray",
     "obs": {"img": 1}, "joint_positions": [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
                                             for _ in range(5)],
     "success": False},
]


def language_of(ep: dict) -> str:
    for k in ("instruction_text", "task_desc", "language_instruction"):
        if ep.get(k):
            return str(ep[k])
    return ""


def action_space(ep: dict) -> str:
    if "action_delta" in ep:
        return "ee_delta"
    if "joint_positions" in ep:
        return "joint_abs"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="开源数据异构探测Demo")
    ap.add_argument("--out", type=Path, default=Path("mini_openx.json"))
    args = ap.parse_args()
    unified = []
    for ep in SAMPLE:
        lang = language_of(ep)
        space = action_space(ep)
        dim = None
        for key in ("action_delta", "joint_positions"):
            if ep.get(key):
                dim = len(ep[key][0])
        rec = {"episode_id": ep["episode_id"], "source": ep["source"],
               "language": lang, "action_space": space, "action_dim": dim,
               "success": ep.get("success")}
        unified.append(rec)
        warn = ""
        if space == "joint_abs":
            warn = " <- 需运动学/本体无关化处理(预训练建议末端增量)"
        print(f"{rec['episode_id']}: {space} dim={dim} "
              f"lang={lang or '(缺失)'}{warn}")
    args.out.write_text(json.dumps(unified, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"统一清单已写入: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
