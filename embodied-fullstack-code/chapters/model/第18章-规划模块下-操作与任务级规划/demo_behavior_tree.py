# -*- coding: utf-8 -*-
"""第18章 L1 极简 Demo：行为树（Sequence/Selector/Retry）。

场景：接近->抓取(失败重试一次)->放置；演示任务层的失败处理长在树结构里。

运行：python demo_behavior_tree.py
"""
from __future__ import annotations
import sys

SUCCESS, FAILURE, RUNNING = "SUCCESS", "FAILURE", "RUNNING"


class Node:
    def tick(self, ctx): raise NotImplementedError


class Seq(Node):
    def __init__(self, children): self.children = children
    def tick(self, ctx):
        for c in self.children:
            st = c.tick(ctx)
            if st != SUCCESS:
                return st
        return SUCCESS


class Sel(Node):
    def __init__(self, children): self.children = children
    def tick(self, ctx):
        for c in self.children:
            st = c.tick(ctx)
            if st == SUCCESS:
                return SUCCESS
        return FAILURE


class Retry(Node):
    def __init__(self, child, n): self.child, self.n = child, n
    def tick(self, ctx):
        for _ in range(self.n):
            if self.child.tick(ctx) == SUCCESS:
                return SUCCESS
        return FAILURE


class Cond(Node):
    def __init__(self, fn): self.fn = fn
    def tick(self, ctx): return SUCCESS if self.fn(ctx) else FAILURE


class Act(Node):
    def __init__(self, name, fn): self.name, self.fn = name, fn
    def tick(self, ctx):
        ok = self.fn(ctx)
        print(f"  [act] {self.name} -> {'OK' if ok else 'FAIL'}")
        return SUCCESS if ok else FAILURE


def main() -> int:
    # 直接构造：接近 -> 重试抓取(第一次失败) -> 放置
    def grasp(ctx):
        ctx["tries"] = ctx.get("tries", 0) + 1
        return ctx["tries"] >= 2        # 第二次成功
    tree = Seq([
        Act("approach", lambda c: True),
        Retry(Act("grasp", grasp), 3),
        Act("place", lambda c: c.get("tries", 0) >= 2),
    ])
    ctx = {}
    st = tree.tick(ctx)
    print("整树结果:", st)
    return 0 if st == SUCCESS else 1


if __name__ == "__main__":
    sys.exit(main())
