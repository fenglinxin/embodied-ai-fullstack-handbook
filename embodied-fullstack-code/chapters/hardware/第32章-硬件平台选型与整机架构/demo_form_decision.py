# -*- coding: utf-8 -*-
"""第32章 L1 极简 Demo：任务特征 -> 本体形态决策。"""
from __future__ import annotations
import sys

# 形态画像: [移动, 越障/上楼, 灵巧双手, 载荷大, 交互]
FORMS = {
    "固定机械臂": {"mobile": 0, "stairs": 0, "hands": 1, "payload": 5, "interact": 1},
    "移动底座+臂": {"mobile": 5, "stairs": 1, "hands": 1, "payload": 3, "interact": 2},
    "双足人形": {"mobile": 5, "stairs": 5, "hands": 5, "payload": 2, "interact": 5},
}
WEIGHTS = {"mobile": 3, "stairs": 5, "hands": 3, "payload": 1, "interact": 2}


def main() -> int:
    # 场景需求示例：桌面抓取（移动0，上楼0，双手1，载荷1，交互1）
    need = {"mobile": 0, "stairs": 0, "hands": 1, "payload": 1, "interact": 1}
    rows = []
    for name, cap in FORMS.items():
        score = sum((min(cap[k], need[k]) - 0.2 * max(0, cap[k] - need[k]))
                  * WEIGHTS[k] for k in WEIGHTS)
        rows.append((score, name, cap))
    rows.sort(key=lambda r: (-r[0], sum(r[2].values())))
    print("桌面抓取需求 -> 形态推荐:")
    for s, n, _ in rows:
        print(f"  {n:<12} 匹配分 {s}")
    print("结论: 能用车轮别用腿；形态复杂度=成本与故障率")
    return 0


if __name__ == "__main__":
    sys.exit(main())
