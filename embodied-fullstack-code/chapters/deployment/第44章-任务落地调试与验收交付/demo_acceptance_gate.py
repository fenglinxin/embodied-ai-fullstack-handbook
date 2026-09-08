# -*- coding: utf-8 -*-
"""第44章 L1 极简 Demo：验收门禁（验收项 × 实测值 → PASS/FAIL → 放行与否）。

落地项目收尾 = 逐条对照验收指标，任何阻塞项不通过都禁止进入交付。
本 Demo 演示"指标卡"打勾逻辑，改改结果数据就能当你的验收模板。
"""
from __future__ import annotations
import argparse, json, sys

# 验收指标卡：字段 = (目标值, 比较方向, 单位说明)
# 方向: "le"=实测≤目标通过, "ge"=实测≥目标通过
CRITERIA: dict[str, tuple[float, str, str]] = {
    "任务成功率": (0.95, "ge", "≥95%"),
    "单次循环节拍": (60.0, "le", "≤60s"),
    "抓取位置误差": (10.0, "le", "≤10mm"),
    "安全事件数": (0.0, "le", "=0"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="", help="JSON 文件：{任务成功率:0.96,...}")
    a = ap.parse_args()
    if a.results:
        with open(a.results, encoding="utf-8") as fh:
            results: dict = json.load(fh)
    else:  # 内置一份"1 项未达标"的验收数据，方便直接看门禁效果
        results = {"任务成功率": 0.92, "单次循环节拍": 55.0,
                   "抓取位置误差": 8.5, "安全事件数": 0}
    rows = []
    for name, (target, direction, note) in CRITERIA.items():
        actual = results.get(name)
        if actual is None:
            rows.append({"验收项": name, "要求": note, "实测": "缺失", "判定": "FAIL-无数据"})
            continue
        ok = actual >= target if direction == "ge" else actual <= target
        rows.append({"验收项": name, "要求": note, "实测": actual,
                     "判定": "PASS" if ok else "FAIL"})
    failed = [r["验收项"] for r in rows if r["判定"].startswith("FAIL")]
    gate = {"验收结果": rows, "未通过项": failed,
            "门禁结论": "禁止交付：先修复再复测" if failed else "验收通过，允许交付",
            "放行": not failed}
    print(json.dumps(gate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
