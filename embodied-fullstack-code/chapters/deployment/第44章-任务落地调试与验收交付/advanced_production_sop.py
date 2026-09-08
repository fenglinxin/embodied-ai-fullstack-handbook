# -*- coding: utf-8 -*-
"""第44章 L3 高阶优化版：量产 SOP 门禁追踪（阶段门 + 责任矩阵 + 风险看板）。

量产流程把"验收一次"升级为"关卡制度"：G0 方案冻结 → G1 α样机 → G2 β小批 →
G3 试产爬坡 → G4 量产放行。每一关有阻塞项(不通过=停线)、责任人和签名矩阵；
本脚本对指定关卡输出就绪度、超期阻塞项与风险Top，驱动例会逐条清零。
"""
from __future__ import annotations
import argparse, json, sys
from dataclasses import dataclass, field

PHASES = ["G0 方案冻结", "G1 α样机", "G2 β小批", "G3 试产爬坡", "G4 量产放行"]


@dataclass
class Task:
    name: str
    phase: str
    owner: str
    blocking: bool
    status: str          # open / done / waived
    due_day: int         # 距今天数(负数=已超期)
    note: str = ""


TASKS: list[Task] = [
    Task("需求与验收指标冻结", "G0 方案冻结", "产品", True, "done", -5),
    Task("安全风险评估(功能安全)", "G0 方案冻结", "安全", True, "done", -5),
    Task("方案评审与预算批准", "G0 方案冻结", "研发", False, "done", -3),
    Task("α样机装配与冒烟", "G1 α样机", "硬件", True, "done", 0),
    Task("感知-规划-控制联调(第41章)", "G1 α样机", "算法", True, "done", 0),
    Task("α可靠性摸底 1000 循环", "G1 α样机", "测试", False, "waived", 0, "延期至β阶段补测"),
    Task("β 小批 10 台产线试点", "G2 β小批", "生产", True, "open", -2),
    Task("量产工艺文件发布", "G2 β小批", "工艺", True, "open", -2),
    Task("备件与维修 SOP", "G2 β小批", "售后", False, "open", 5),
    Task("试产爬坡至 20台/日", "G3 试产爬坡", "生产", True, "open", 10),
    Task("直通率 ≥97% 连续两周", "G3 试产爬坡", "质量", True, "open", 12),
    Task("客户现场验收签字", "G4 量产放行", "交付", True, "open", 20),
]

SIGNERS: dict[str, list[str]] = {
    "G0 方案冻结": ["研发", "质量", "产品"],
    "G1 α样机": ["研发", "测试"],
    "G2 β小批": ["生产", "质量", "工艺"],
    "G3 试产爬坡": ["质量", "生产", "研发"],
    "G4 量产放行": ["质量", "交付", "生产"],
}


def snapshot(phase: str) -> dict:
    gate_idx = PHASES.index(phase)
    tasks = [t for t in TASKS if PHASES.index(t.phase) <= gate_idx]
    open_blocking = [t.name for t in tasks if t.blocking and t.status == "open"]
    overdue = [{"任务": t.name, "owner": t.owner, "超期天数": -t.due_day,
                "阻塞": t.blocking} for t in tasks if t.status == "open" and t.due_day < 0]
    done_cnt = sum(1 for t in tasks if t.status == "done")
    waived = [t.name for t in tasks if t.status == "waived"]
    signed = sum(1 for _ in SIGNERS[phase])
    readiness = 100.0 * done_cnt / len(tasks)
    blockers = [t.name for t in tasks if t.blocking and t.status != "done"]
    return {"关卡": phase, "任务总数": len(tasks), "完成数": done_cnt,
            "就绪度%": round(readiness, 1),
            "阻塞项未关": open_blocking,
                        "需要签名": SIGNERS[phase],
            "超期项": overdue,
            "豁免项": waived,
            "放行判定": ("放行：无未关闭锁项" if not open_blocking
                         else "卡关：以下阻塞项未闭环 → " + "、".join(open_blocking)),
            "风险提示": ("存在豁免项，需在下一关卡前完成补测，否则风险上移"
                        if waived else "无豁免，风险可控")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="G2 β小批", choices=PHASES)
    a = ap.parse_args()
    print(json.dumps(snapshot(a.phase), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
