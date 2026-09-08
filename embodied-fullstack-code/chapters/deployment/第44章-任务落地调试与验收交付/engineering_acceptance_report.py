# -*- coding: utf-8 -*-
"""第44章 L2 工程标准版：验收报告生成器（三态判定 + 证据链 + Markdown 交付物）。

工程验收规范要求：每一项结论必须有"证据"，不能只有数字。
三态判定：
  PASS — 达标（实测满足目标线，且证据文件存在）；
  EDGE — 黄区：距目标 5% 内的临界区（略低于/略高于目标），需复核后放行；
  FAIL — 未达标，或数据达标但没有证据文件（一律按不通过处理）。
自动生成 Markdown 验收报告：判定汇总 / 黄区清单 / 遗留阻塞项 / 签署区。
"""
from __future__ import annotations
import argparse, json, os, sys
from dataclasses import dataclass
from datetime import date

EDGE_BAND = 0.05   # 黄区宽度：距目标 5% 内未达标 -> EDGE 复核


@dataclass
class Item:
    name: str
    target: float
    direction: str          # "ge" 或 "le"
    unit: str = ""          # 单位；"%"(目标为小数比例) 时自动按百分比显示
    evidence_required: bool = True


@dataclass
class Trial:
    item: Item
    measured: float | None
    evidence: str           # 证据文件路径/录像编号


def verdict(t: Trial) -> tuple[str, str]:
    """三态判定：达标=PASS；黄区(距目标5%内未达标)=EDGE 需复核；其余 FAIL。"""
    if t.measured is None:
        return "FAIL", "无实测数据"
    if t.item.evidence_required and not t.evidence.strip():
        return "FAIL", "数据达标但无证据文件，按不通过处理"
    m, tg = t.measured, t.item.target
    if tg == 0:  # 目标=0 的项（如安全事件数）：0 通过，非 0 直接 FAIL
        return ("PASS", "达标(目标为0，实测为0)") if m == 0 else ("FAIL", f"实测{m}，目标为0")
    if t.item.direction == "ge":
        if m >= tg:
            return "PASS", f"达标(超出目标{(m - tg) / tg * 100:.1f}%)"
        if m >= tg * (1 - EDGE_BAND):
            return "EDGE", f"黄区:距目标仅{(tg - m) / tg * 100:.1f}%，需复核"
        return "FAIL", f"未达标(差{(tg - m) / tg * 100:.1f}%)"
    if m <= tg:
        return "PASS", f"达标(富余{(tg - m) / tg * 100:.1f}%)"
    if m <= tg * (1 + EDGE_BAND):
        return "EDGE", f"黄区:超上限{(m - tg) / tg * 100:.1f}%，需复核"
    return "FAIL", f"未达标(超{(m - tg) / tg * 100:.1f}%)"


def fmt_req(it: Item) -> str:
    sym = ">=" if it.direction == "ge" else "<="
    if it.unit == "%" and it.target <= 1:
        return f"{sym}{it.target * 100:.0f}%"
    return f"{sym}{it.target}{it.unit}"


def fmt_val(v: float | None, it: Item) -> str:
    if v is None:
        return "缺失"
    if it.unit == "%" and it.target <= 1:
        return f"{v * 100:.1f}%"
    return f"{v}{it.unit}"


def build_report(trials: list[Trial], project: str, version: str, out_dir: str) -> dict:
    rows, fails = [], []
    for t in trials:
        v, note = verdict(t)
        rows.append({"验收项": t.item.name,
                     "要求": fmt_req(t.item),
                     "实测": fmt_val(t.measured, t.item),
                     "证据": t.evidence or "无",
                     "判定": v, "说明": note})
        if v == "FAIL":
            fails.append(t.item.name)
    edge = [r["验收项"] for r in rows if r["判定"] == "EDGE"]
    os.makedirs(out_dir, exist_ok=True)
    lines = [
        f"# {project} 验收报告",
        "",
        f"- 版本：{version}",
        f"- 验收日期：{date.today().isoformat()}",
        f"- 结果：{'通过' if not fails else '不通过'}（PASS {sum(1 for r in rows if r['判定'] == 'PASS')}"
        f" / EDGE {len(edge)} / FAIL {len(fails)}）",
        "",
        "| 验收项 | 要求 | 实测 | 证据 | 判定 | 说明 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(f"| {r['验收项']} | {r['要求']} | {r['实测']} | {r['证据']} | {r['判定']} | {r['说明']} |")
    if edge:
        lines += ["", "## 黄区复核项（EDGE）", ""] + [f"- {n}" for n in edge]
    if fails:
        lines += ["", "## 遗留阻塞项（未修复禁止交付）", ""] + [f"- {n}" for n in fails]
    lines += ["", "## 签署区", "",
              "| 角色 | 结论 | 签字 | 日期 |", "| --- | --- | --- | --- |",
              "| 项目负责人 | 同意/驳回 | | |", "| 质量 | 同意/驳回 | | |",
              "| 客户/交付经理 | 同意/驳回 | | |", ""]
    out_path = os.path.join(out_dir, "acceptance_report.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return {"报告文件": out_path,
            "汇总": {"PASS": sum(1 for r in rows if r["判定"] == "PASS"),
                     "EDGE": len(edge), "FAIL": len(fails)},
            "遗留阻塞项": fails, "黄区项": edge,
            "门禁结论": "驳回：修复后重测" if fails
                        else ("通过(黄区项需限期复核)" if edge else "通过")}


def default_trials() -> list[Trial]:
    """演示数据：1 个黄区(成功率 0.93) + 1 个 FAIL(位置误差 13mm)，其余达标。"""
    specs = [
        Item("任务成功率", 0.95, "ge", "%"),
        Item("单次循环节拍", 60.0, "le", "s"),
        Item("抓取位置误差", 10.0, "le", "mm"),
        Item("安全事件数", 0.0, "le", "次"),
        Item("连续无故障运行", 8.0, "ge", "h"),
    ]
    data = [0.93, 58.0, 13.0, 0, 9.0]
    evid = ["rec-0421-run03.mp4", "log/cycle.csv", "log/pos_err.csv", "safety.log", "run/uptime.log"]
    return [Trial(s, d, e) for s, d, e in zip(specs, data, evid)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="分拣抓取一体机 v0.9 验收")
    ap.add_argument("--version", default="v0.9.2")
    ap.add_argument("--out-dir", default="out")
    a = ap.parse_args()
    report = build_report(default_trials(), a.project, a.version, a.out_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
