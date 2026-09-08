# -*- coding: utf-8 -*-
"""第42章 L3 高阶优化版：故障案例库（根因率统计 + 复发追踪 + 预防闭环）。

量产团队靠"案例库"而非个人记忆排障：每条故障记录根因层/根因/修复/预防，
定期统计根因分布、抓出复发项、把 Top 预防动作固化成检查清单。
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter, defaultdict

CASES: list[dict] = [
    {"id": "C-001", "date": "2025-03-02", "symptom": "末端漂移", "layer": "机械",
     "root": "减速器背隙超差", "fix": "更换减速器并标定", "prevent": "每季度背隙抽检", "closed": True},
    {"id": "C-002", "date": "2025-03-05", "symptom": "通信卡顿", "layer": "通信",
     "root": "网线屏蔽层破损丢包", "fix": "更换屏蔽网线", "prevent": "线缆走线槽+定期摇测", "closed": True},
    {"id": "C-003", "date": "2025-03-09", "symptom": "执行失效", "layer": "算法",
     "root": "抓取位姿用了旧标定外参", "fix": "重标定相机并上版本锁", "prevent": "标定文件纳入版本管理", "closed": True},
    {"id": "C-004", "date": "2025-03-14", "symptom": "末端漂移", "layer": "机械",
     "root": "减速器背隙超差（复发）", "fix": "更换减速器+加装状态监测", "prevent": "振动传感器在线监测", "closed": False},
    {"id": "C-005", "date": "2025-03-20", "symptom": "运行卡顿", "layer": "环境",
     "root": "供电电压跌落", "fix": "更换大功率稳压电源", "prevent": "母线电压监控+告警", "closed": True},
]


def analyze(cases: list[dict]) -> dict:
    layer_count = Counter(c["layer"] for c in cases)
    root_count = Counter(c["root"] for c in cases)
    symptom_map: dict[str, list[dict]] = defaultdict(list)
    for c in cases:
        symptom_map[(c["symptom"], c["layer"])].append(c)
    recurrence = []
    for key, items in sorted(symptom_map.items(), key=lambda kv: -len(kv[1])):
        if len(items) >= 2:
            recurrence.append({"症状": key[0], "层": key[1], "次数": len(items),
                               "ids": [c["id"] for c in items]})
    open_cases = sum(1 for c in cases if not c.get("closed"))
    top_layers = layer_count.most_common(3)
    top_prevent = [c["prevent"] for c in sorted(cases, key=lambda c: c["date"], reverse=True)
                   if c.get("prevent")][:5]
    return {"案例总数": len(cases), "未闭环数": open_cases,
            "根因层分布": [{"层": k, "案例数": v,
                         "占比%": round(v * 100 / len(cases), 1)} for k, v in top_layers],
            "Top根因": [{"根因": k, "次数": v} for k, v in root_count.most_common(3)],
            "复发追踪": recurrence,
            "建议固化预防项": top_prevent,
            "复盘结论": "同层同症状≥2次=系统性缺陷，禁止只修个案，必须补预防措施"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases-json", default="", help="可选：外部案例 JSON 文件路径")
    a = ap.parse_args()
    cases = CASES
    if a.cases_json:
        with open(a.cases_json, encoding="utf-8") as fh:
            extra = json.load(fh)
            cases = CASES + (extra if isinstance(extra, list) else [extra])
    print(json.dumps(analyze(cases), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
