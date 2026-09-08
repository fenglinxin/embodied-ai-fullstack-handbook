# -*- coding: utf-8 -*-
"""第42章 L2 工程标准版：分层排查执行器（环境→通信→算法→机械，证据加权决策）。

排查真机"卡顿/漂移/执行失效"类故障时按层自底向上收集证据，
每条证据有成本与信息量，先查便宜项再查贵项，避免一上来就拆机。
"""
from __future__ import annotations
import argparse, json
from dataclasses import dataclass, field


@dataclass
class Check:
    id: str            # 证据编号
    layer: str         # 所属层：环境/通信/算法/机械
    name: str
    cmd: str           # 怎么查（伪命令，真机上换成对应工具）
    cost: int          # 排查成本 1~10
    severity: int      # 该层证据对症状解释力 1~10
    evidence: bool     # 是否命中异常
    note: str = ""


PLAN: list[Check] = [
    Check("E1", "环境", "供电电压波动", "万用表量 24V 母线±5%", 1, 7, False),
    Check("E2", "环境", "关节/控制柜温度", "热像仪或温度计", 1, 5, False),
    Check("C1", "通信", "EtherCAT/串口丢包率", "抓包统计丢包", 3, 8, False),
    Check("C2", "通信", "指令周期抖动", "打点测总线周期 jitter", 3, 7, False),
    Check("A1", "算法", "目标检测置信度", "可视化中间帧与置信度", 5, 6, False),
    Check("A2", "算法", "滤波/控制参数异常", "导出日志检查增益与误差", 5, 8, False),
    Check("M1", "机械", "减速器背隙/异响", "空载正反转手测间隙", 7, 9, False),
    Check("M2", "机械", "编码器/线缆磨损", "外观检查+信号质量测试", 7, 8, False),
]


def run_checklist(flags: list[str]) -> tuple[dict, list[dict]]:
    hit = set(flags)
    results = []
    for c in PLAN:
        c.evidence = c.id in hit
        results.append({"id": c.id, "layer": c.layer, "name": c.name,
                        "cmd": c.cmd, "evidence": c.evidence})
    return {"per_layer": summarize(results)}, results


def summarize(results: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for r in results:
        layer = r["layer"]
        d = out.setdefault(layer, {"hits": 0, "total": 0, "weight": 0})
        d["total"] += 1
        if r["evidence"]:
            d["hits"] += 1
    return out


def decide(results: list[dict], symptom: str) -> dict:
    """证据→嫌疑分层排序；同分时按成本低优先复查。"""
    layer_weight = {}
    layer_cost = {}
    for c in PLAN:
        layer_weight[c.layer] = layer_weight.get(c.layer, 0) + (c.severity if c.evidence else 0)
        layer_cost[c.layer] = layer_cost.get(c.layer, 0) + (c.cost if c.evidence else 0)
    rank = sorted(layer_weight.items(), key=lambda kv: (-kv[1], layer_cost.get(kv[0], 99)))
    top = rank[0][0] if rank and rank[0][1] > 0 else "算法(默认先看日志)"
    tips = {"环境": "查电源与温升：稳压源/换粗线/加散热。",
            "通信": "查总线配置与网线屏蔽：降波特率验证、换屏蔽线、加看门狗。",
            "算法": "回放录包定位：关滤波对比、恢复出厂参数、加输入前校验。",
            "机械": "拆机前先空载对比：紧固/换减速器/查编码器线缆。"}
    return {"症状": symptom, "嫌疑层排序": rank, "最高嫌疑层": top,
            "处置建议": tips.get(top.split("(")[0], "结合录包回放复核")}


def main() -> int:
    ap = argparse.ArgumentParser(description="分层排查：--hit 传证据编号，如 --hit C1 --hit A2")
    ap.add_argument("--symptom", default="关节卡顿+偶发漂移")
    ap.add_argument("--hit", action="append", default=[])
    a = ap.parse_args()
    layer_stats, results = run_checklist(a.hit)
    report = {
        "checklist": results,
        "layer_summary": layer_stats,
        "decision": decide(results, a.symptom),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
