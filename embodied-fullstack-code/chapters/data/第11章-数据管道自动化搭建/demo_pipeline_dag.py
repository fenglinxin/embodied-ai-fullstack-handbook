# -*- coding: utf-8 -*-
"""第11章 L1 极简 Demo：数据管道 DAG 概念（纯标准库）。

演示：采集->清洗->评分 三个节点按依赖顺序执行，
每个节点只依赖输入参数，输出可预测（幂等概念雏形）。

运行：python demo_pipeline_dag.py
"""
from __future__ import annotations
import json, sys
from typing import Callable


def fn_ingest(prev: dict) -> dict:
    """原料：一批 Episode 摘要。"""
    return {"episodes": [{"id": f"ep-{i:04d}", "dirty": i % 3 == 0}
                         for i in range(9)]}


def fn_clean(prev: dict) -> dict:
    return {"cleaned": [e for e in prev["ingest"]["episodes"] if not e["dirty"]],
            "dropped": sum(1 for e in prev["ingest"]["episodes"] if e["dirty"])}


def fn_quality(prev: dict) -> dict:
    n = len(prev["clean"]["cleaned"])
    return {"total": n, "score": round(1.0 - prev["clean"]["dropped"] / 9.0, 3)}


DAG: dict[str, dict] = {
    "ingest": {"fn": fn_ingest, "deps": []},
    "clean": {"fn": fn_clean, "deps": ["ingest"]},
    "quality": {"fn": fn_quality, "deps": ["clean"]},
}


def run(node_id: str, results: dict) -> dict:
    """按依赖递归执行（教学简化版，真实版见 L2/L3）。"""
    node = DAG[node_id]
    for dep in node["deps"]:
        run(dep, results)
    if node_id not in results:
        inputs = {dep: results[dep] for dep in node["deps"]}
        results[node_id] = node["fn"](inputs)
        print(f"[run] {node_id} <- 依赖 {node['deps'] or '无'}")
    return results[node_id]


def main() -> int:
    results: dict = {}
    for node_id in DAG:
        run(node_id, results)
    print("结果:", json.dumps({k: v for k, v in results.items()
                               if k != "ingest"}, ensure_ascii=False))
    print("幂等测试: 再次运行 clean 是否重算? ->",
          "不重算(缓存)" if "clean" in results else "重算")
    return 0


if __name__ == "__main__":
    sys.exit(main())
