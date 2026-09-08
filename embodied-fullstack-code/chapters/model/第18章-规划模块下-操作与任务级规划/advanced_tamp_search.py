# -*- coding: utf-8 -*-
"""第18章 L3 高阶优化版：简化 TAMP（任务顺序搜索+运动可行性验证）。

问题：目标物件 A 被挡板 B 压住；需要规划 清障->抓A->放A，且每个抓取
动作必须通过"运动可行性检查"（TAMP 中任务层与运动层商量着来）。

运行：python advanced_tamp_search.py
"""
from __future__ import annotations
import sys
from collections import deque


class Problem:
    def __init__(self):
        self.targets = {"A"}
        self.blockers = {"B"}
        self.block_map = {"A": {"B"}}      # A 被 B 挡住
        self.feasible = {"A", "C"}          # 只有 A/C 的运动轨迹可行


def motion_feasible(prob, obj):
    return obj in prob.feasible


def search(prob):
    """BFS over (remaining frozenset, cleared frozenset, holding)。"""
    start = (frozenset(prob.targets), frozenset(), None)
    q = deque([(start, [])])
    seen = {start}
    while q:
        (remaining, cleared, holding), plan = q.popleft()
        if not remaining and holding is None:
            return plan
        # 清障动作
        for b in prob.blockers:
            if b not in cleared and holding is None:
                ns = (remaining, cleared | {b}, None)
                if ns not in seen:
                    seen.add(ns)
                    q.append((ns, plan + [("clear", b)]))
        # 抓取动作（需清障完成+运动可行）
        for t in remaining:
            if not prob.block_map.get(t, set()) - cleared:
                if holding is None and motion_feasible(prob, t):
                    ns = (remaining, cleared, t)
                    if ns not in seen:
                        seen.add(ns)
                        q.append((ns, plan + [("pick", t)]))
                elif holding == t:
                    ns = (remaining - {t}, cleared, None)
                    if ns not in seen:
                        seen.add(ns)
                        q.append((ns, plan + [("place", t)]))
    return None


def main() -> int:
    prob = Problem()
    plan = search(prob)
    if plan is None:
        print("无可行任务序列")
        return 1
    print("TAMP 规划结果:")
    for step in plan:
        print("  ", step)
    feasible = all(motion_feasible(prob, obj) for act, obj in plan
                   if act == "pick")
    print("运动可行性检查:", "全部通过" if feasible else "有动作不可行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
