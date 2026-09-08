# -*- coding: utf-8 -*-
"""评测工程 L3 高阶优化版：泛化矩阵 + 稳定性 + 多版本趋势（综合决策）。

量产评测三件套：
1. 泛化矩阵：同一任务 x 环境扰动(光照/遮挡/物品变体/距离)，逐格成功率，
   找出"一换条件就垮"的退化单元 -> 反推补数据方向；
2. 稳定性：基准条件下重复多轮的成功率波动(极差)，波动大=玄学成功不可交付；
3. 版本趋势：跨版本逐场景成功率，识别 提升/持平/回退，输出 放行/观望/回滚。
"""
from __future__ import annotations
import argparse, json, sys

# 泛化矩阵：行=扰动维度，列=条件(键以"基准-"开头的是该维度参照线)，值=成功率%
GEN_MATRIX: dict[str, dict[str, float]] = {
    "光照":    {"基准-标准光": 96.0, "强逆光": 88.0, "暗光": 91.0},
    "遮挡":    {"基准-无遮挡": 96.0, "浅遮挡": 93.0, "深遮挡": 79.0},
    "物品变体": {"基准-标准杯": 96.0, "异形瓶": 90.0, "半透明袋": 84.0},
    "距离":    {"基准-0.5m": 96.0, "0.8m": 94.0, "1.2m": 97.0},
}
DROP_LIMIT = 8.0     # 比该维度基准低 8pp 以上 = 退化单元

# 多版本成功率%（每场景每版本）
VERSIONS: dict[str, dict[str, float]] = {
    "v1.3": {"抓取-透明杯": 84.0, "避障-动态行人": 82.0, "插拔-定位精度": 90.0},
    "v1.4": {"抓取-透明杯": 92.0, "避障-动态行人": 86.0, "插拔-定位精度": 92.0},
    "v1.5": {"抓取-透明杯": 96.0, "避障-动态行人": 93.0, "插拔-定位精度": 96.0},
}
TREND_DROP = 3.0    # 单个场景最新版本比上一版回退 >3pp 标红


def gen_report() -> dict:
    rows, degraded = [], []
    for dim, conds in GEN_MATRIX.items():
        base = next(v for k, v in conds.items() if k.startswith("基准-"))
        for cond, rate in conds.items():
            if cond.startswith("基准-"):
                continue
            drop = base - rate
            bad = drop > DROP_LIMIT
            rows.append({"维度": dim, "条件": cond, "成功率%": rate,
                         "比基准pp": round(drop, 1), "退化": bad})
            if bad:
                degraded.append(dim + "/" + cond)
    # 每维度最差条件 -> 补数据建议
    worst = []
    for dim, conds in GEN_MATRIX.items():
        conds2 = {k: v for k, v in conds.items() if not k.startswith("基准-")}
        wc, wr = min(conds2.items(), key=lambda kv: kv[1])
        worst.append(dim + " 最差: " + wc + "(" + str(wr) + "%)")
    return {"退化单元": degraded, "明细": rows,
            "补数据建议": worst,
            "结论": "存在退化单元：禁止直接量产，按维度补真实场景数据后复测(第7/10章)"
                    if degraded else "泛化达标"}


def stability_report() -> dict:
    # 基准条件 5 轮重复评测的成功率%（模拟发布前 A/B 复测）
    rounds = [96.0, 92.0, 96.0, 87.0, 96.0]
    span = max(rounds) - min(rounds)
    return {"5轮成功率%": rounds, "极差pp": span, "判定线pp": DROP_LIMIT,
            "结论": "波动大：成功率忽高忽低，先查环境条件一致性/任务判定标准，再谈发布"
                    if span > DROP_LIMIT else "稳定性可接受"}


def trend_report() -> dict:
    rows = []
    regress = []
    all_ver = list(VERSIONS)
    for scene in VERSIONS[all_ver[-1]]:
        seq = {v: VERSIONS[v].get(scene) for v in all_ver}
        last_delta = seq[all_ver[-1]] - seq[all_ver[-2]]
        if last_delta < -TREND_DROP:
            regress.append(scene)
        rows.append({"场景": scene, "各版本成功率%": seq, "最新增量pp": round(last_delta, 1)})
    return {"趋势明细": rows, "回退场景": regress,
            "决策": "回滚/修复后重测" if regress else "最新版本可进入发布与验收(第43/44章)"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="all", choices=["all", "gen", "stab", "trend"])
    a = ap.parse_args()
    label = {"gen": "泛化矩阵", "stab": "稳定性", "trend": "版本趋势"}
    parts = {"gen": gen_report, "stab": stability_report, "trend": trend_report}
    keys = ["gen", "stab", "trend"] if a.part == "all" else [a.part]
    out = {label[name]: parts[name]() for name in keys}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
