# -*- coding: utf-8 -*-
"""第30章 L1 极简 Demo：评测协议五要素生成。"""
from __future__ import annotations
import json, sys

TASKS = ["pick_cup", "place_cup"]
SCENES = ["kitchen_light", "kitchen_shadow", "warehouse"]
EPISODES_PER_SCENE = 20
SEEDS = [101, 202, 303]


def build_protocol():
    return {
        "scenario_set": [{"task": t, "scene": s,
                          "episodes": EPISODES_PER_SCENE}
                         for t in TASKS for s in SCENES],
        "total_episodes": len(TASKS) * len(SCENES) * EPISODES_PER_SCENE,
        "random_seeds": SEEDS,
        "initial_state_dist": "物体摆位/光照按场景分布采样",
        "judge_rules": {"success": "任务判定函数", "timeout_s": 30,
                        "retry": 0},
    }


def main() -> int:
    p = build_protocol()
    print(f"场景组合 {len(p['scenario_set'])}，总评测 {p['total_episodes']} 次")
    print("五要素: 场景集/样本量/多种子/初始分布/判定规则 已生成")
    print(json.dumps(p, ensure_ascii=False, indent=2)[:400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
