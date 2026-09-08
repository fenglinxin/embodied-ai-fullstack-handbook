# -*- coding: utf-8 -*-
"""第43章 L3 高阶优化版：SLO 错误预算 + 燃烧率告警 + 故障复盘闭环。

量产级稳定性不止"挂了能回滚"，还要回答三个问题：
1) 可靠性承诺还剩多少余量？        -> SLO/错误预算
2) 现在烧钱(预算)速度危险吗？      -> 燃烧率分档告警
3) 故障有没有系统性根因？多久修好？ -> 复盘 MTTR/复发/整改项
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter, defaultdict

SLO_OK = 0.999           # 目标可用性 99.9%
MONTH_SECONDS = 30 * 24 * 3600
BUDGET_SECONDS = int(MONTH_SECONDS * (1 - SLO_OK))   # 30天错误预算 ≈ 2592s

# 本月每天的服务不可用秒数（0=无故障）；第 5 天发布事故、第 18 天网络事故
DAILY_OUTAGE: list[int] = [0, 0, 0, 0, 420, 0, 0, 0, 0, 0,
                           0, 0, 15, 0, 0, 0, 0, 540, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 60, 0, 0]

INCIDENTS: list[dict] = [
    {"id": "INC-001", "date": 5,  "category": "发布", "root": "灰度未走完即全量",
     "mttr_hours": 3.2, "reopen": False, "action": "发布门禁强制灰度≥2观察窗"},
    {"id": "INC-002", "date": 12, "category": "网络", "root": "公网链路抖动",
     "mttr_hours": 0.8, "reopen": False, "action": "双链路冗余"},
    {"id": "INC-003", "date": 18, "category": "配置", "root": "参数表误上线",
     "mttr_hours": 1.5, "reopen": False, "action": "配置预发校验+回滚演练"},
    {"id": "INC-004", "date": 26, "category": "网络", "root": "公网链路抖动(复发)",
     "mttr_hours": 2.1, "reopen": True, "action": "升级为长期改造项：链路质量SLA"},
]


def burn_rate_check(days_left: int, used: int) -> dict:
    """按 Google SRE 多窗口燃烧率思想简化为单窗口评估。"""
    remain = BUDGET_SECONDS - used
    allowed_per_day = remain / max(days_left, 1)
    recent = sum(DAILY_OUTAGE[:5])
    burn = recent / max(allowed_per_day * 5, 1e-9)
    if burn >= 14.4:
        level, advise = "P0 立即止血", "停止发布+全链路降级预案+值班拉群"
    elif burn >= 3.6:
        level, advise = "P1 高消耗", "暂停灰度放量+定位根因+限流"
    elif burn >= 1.0:
        level, advise = "P2 关注", "持续监控+准备回滚方案"
    else:
        level, advise = "正常", "常规值班节奏"
    return {"剩余预算秒": remain, "日均可用预算秒": round(allowed_per_day, 1),
            "近5日消耗秒": recent, "燃烧率": round(burn, 2),
            "档位": level, "动作": advise}


def postmortem(incidents: list[dict]) -> dict:
    by_cat = Counter(i["category"] for i in incidents)
    mttr = sum(i["mttr_hours"] for i in incidents) / len(incidents)
    reopens = [i for i in incidents if i["reopen"]]
    cat_mttr: dict[str, list] = defaultdict(list)
    for i in incidents:
        cat_mttr[i["category"]].append(i["mttr_hours"])
    top_cat = max(cat_mttr.items(), key=lambda kv: len(kv[1]))
    return {"事故数": len(incidents),
            "分类分布": [{"类": k, "次数": v} for k, v in by_cat.most_common()],
            "平均MTTR(小时)": round(mttr, 2),
            "复发事故": [{"id": i["id"], "类": i["category"], "根因": i["root"]} for i in reopens],
            "Top整改类": top_cat[0],
            "复盘结论": "复发=上次整改未闭环；禁止关单，必须挂长期改造项并设责任人"
                        if reopens else "无复发，整改闭环良好"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, default=22, help="本月第几天做检查")
    a = ap.parse_args()
    if not 1 <= a.day <= 30:
        print("day 必须在 1~30", file=sys.stderr)
        return 2
    used = sum(DAILY_OUTAGE[:a.day])
    report = {"SLO": SLO_OK, "月错误预算秒": BUDGET_SECONDS,
              "检查日": a.day, "已消耗秒": used,
              "燃烧率评估": burn_rate_check(30 - a.day, used),
              "故障复盘": postmortem(INCIDENTS)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
