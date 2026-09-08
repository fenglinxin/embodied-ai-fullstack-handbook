# -*- coding: utf-8 -*-
"""第7章 L1 极简 Demo：任务树 -> 场景矩阵 -> MVP 数据规划。

把文章"三层设计法"变成可执行规划：
  业务约束 -> 任务树叶子 -> 变体矩阵 -> 采集配额/MVP建议

运行：python demo_dataset_planner.py
"""
from __future__ import annotations
import argparse, itertools, json, sys
from pathlib import Path


def sample_scenario() -> dict:
    """仓库 B 区料箱搬运的简化规划模型。"""
    return {
        "scenario": "仓库B区料箱搬运",
        "constraints": {"节拍_s": 20, "成功率": 0.99,
                        "物体规格": ["3种料箱"], "人车共线": True},
        "task_tree": [
            {"skill": "grasp", "variants": {
                "box": ["s", "m", "l"], "position": ["left", "center", "right"],
                "light": ["normal", "shadow"]}},
            {"skill": "place", "variants": {
                "rack": ["low", "high"], "precision": ["normal"]}},
        ],
        "quota_per_combo": 10,     # 每组合至少10条（工程起点）
        "mvp": {"leaves": 1, "variants": 3, "per": 10},   # 最小有效集
    }


def matrix_of(skill: dict) -> list[dict]:
    keys = list(skill["variants"])
    combos = list(itertools.product(*(skill["variants"][k] for k in keys)))
    return [dict(zip(keys, c)) for c in combos]


def main() -> int:
    ap = argparse.ArgumentParser(description="领域数据集规划 Demo")
    ap.add_argument("--out", type=Path, default=Path("collection_plan.json"))
    args = ap.parse_args()
    plan = sample_scenario()
    total = 0
    rows = []
    for skill in plan["task_tree"]:
        combos = matrix_of(skill)
        need = len(combos) * plan["quota_per_combo"]
        total += need
        rows.append({"skill": skill["skill"], "combos": len(combos),
                     "need": need})
    mvp_need = plan["mvp"]["leaves"] * plan["mvp"]["variants"] * plan["mvp"]["per"]
    print(f"场景: {plan['scenario']}")
    for r in rows:
        print(f"  {r['skill']}: {r['combos']} 个变体组合 x "
              f"{plan['quota_per_combo']} 条 = {r['need']} 条")
    print(f"完整矩阵合计约 {total} 条")
    print(f"建议：先做 MVP {mvp_need} 条（1技能x3变体x10条）"
          "跑通闭环，再按矩阵补采")
    args.out.write_text(json.dumps({"plan": plan, "rows": rows,
                                    "total_need": total,
                                    "mvp_need": mvp_need},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"规划已写入: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
