# -*- coding: utf-8 -*-
"""评测工程 L2 工程标准版：评测运行器（Wilson 置信区间 + 延时分位 + 版本回归）。

覆盖规范第(7)类指标：任务成功率、循环节拍(延时类)、控制精度、安全事件，
并支持 --baseline 对比历史版本：逐场景输出成功率 delta 与 REGRESS 标记，
结果 JSON 落盘，供第44章验收与第43章发布门禁直接引用。

用法示范：
  先跑旧版本存基线: python engineering_eval_runner.py --version v1.4.3 --legacy --json-out base_v14.json
  再跑新版本对比:   python engineering_eval_runner.py --version v1.5.0 --baseline base_v14.json
"""
from __future__ import annotations
import argparse, json, math, os, sys
from dataclasses import dataclass, field
from datetime import date

Z95 = 1.96  # 95% 置信区间 z 值
PASS_RATE = 0.90
REGRESS_RATE_PP = 5.0   # 成功率比基线下降 >5pp 判回归
REGRESS_P95_PCT = 10.0  # P95 延时比基线恶化 >10% 判回归


@dataclass
class Scenario:
    name: str
    kind: str            # grasp / nav / precision
    trials: list  # [(success:int, metric:float)] metric: 循环秒 或 位置误差mm
    target_rate: float = PASS_RATE


@dataclass
class Config:
    scenarios: list = field(default_factory=list)


def wilson_ci(success: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson 分数区间：小样本下比正态近似更稳，评测报告标配。"""
    if n == 0:
        return 0.0, 0.0
    p = success / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)


def pct(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def eval_scenario(sc: Scenario) -> dict:
    n = len(sc.trials)
    success = sum(1 for t in sc.trials if t[0] == 1)
    vals = sorted(t[1] for t in sc.trials)
    rate = success / n
    lo, hi = wilson_ci(success, n)
    return {"场景": sc.name, "试次": n, "成功": success,
            "成功率": round(rate, 4), "CI95": [lo, hi],
            "P50": round(pct(vals, 0.5), 1), "P95": round(pct(vals, 0.95), 1),
            "判定": "PASS" if rate >= sc.target_rate else "FAIL",
            "单位说明": "P50/P95为位置误差(mm)" if sc.kind == "precision" else "P50/P95为循环秒"}


def default_config(legacy: bool = False) -> Config:
    if legacy:  # v1.4.3: 两场景 73.3%，未达标
        return Config([
            Scenario("抓取-透明杯", "grasp",
                     [(1, 8.4), (1, 8.0), (0, 13.1), (1, 8.3), (0, 12.6),
                      (1, 8.9), (1, 8.2), (0, 12.8), (1, 8.7), (1, 8.5),
                      (1, 8.1), (0, 12.2), (1, 8.6), (1, 8.8), (1, 8.3)]),
            Scenario("避障-动态行人", "nav",
                     [(1, 15.6), (1, 16.9), (0, 21.3), (1, 15.8), (0, 20.7),
                      (1, 16.1), (1, 15.4), (0, 21.9), (1, 16.2), (1, 15.2),
                      (1, 15.7), (0, 20.4), (1, 16.0), (1, 15.9), (1, 16.3)]),
            Scenario("插拔-定位精度", "precision",
                     [(1, 4.9), (1, 5.6), (1, 4.8), (0, 8.9), (1, 5.0),
                      (1, 5.2), (1, 5.5), (1, 4.7), (1, 6.1), (1, 4.6)]),
        ])
    return Config([  # v1.5.0: 两场景 93.3%，达标
        Scenario("抓取-透明杯", "grasp",
                 [(1, 8.2), (1, 7.9), (0, 12.4), (1, 8.0), (1, 8.8),
                  (1, 9.1), (1, 8.3), (1, 8.7), (1, 8.6), (1, 8.4),
                  (1, 8.1), (1, 7.8), (1, 8.5), (1, 8.9), (1, 8.2)]),
        Scenario("避障-动态行人", "nav",
                 [(1, 15.2), (1, 16.8), (0, 20.1), (1, 15.9), (1, 14.8),
                  (1, 16.2), (1, 15.5), (1, 15.9), (1, 16.0), (1, 15.1),
                  (1, 15.8), (1, 16.1), (1, 14.9), (1, 15.6), (1, 16.3)]),
        Scenario("插拔-定位精度", "precision",
                 [(1, 4.2), (1, 5.1), (1, 4.8), (1, 6.0), (1, 4.5),
                  (1, 4.9), (1, 5.3), (1, 4.6), (1, 5.8), (1, 4.4)]),
    ])


def scenario_map(report: dict) -> tuple[str, dict]:
    """把落盘报告转成 {场景名: 场景result}，返回 (版本, 映射)。"""
    ver = report.get("版本", "未知")
    mapping = {}
    for r in report.get("场景结果", []):
        mapping[r["场景"]] = r
    return ver, mapping


def compare(base_report: dict, cur_report: dict) -> dict:
    b_ver, base = scenario_map(base_report)
    _, cur = scenario_map(cur_report)
    rows = []
    for name, c in cur.items():
        b = base.get(name)
        if not b:
            rows.append({"场景": name, "对比": "新增场景(无基线)", "回归": False})
            continue
        dr = (c["成功率"] - b["成功率"]) * 100
        dp = (c["P95"] - b["P95"]) / max(b["P95"], 1e-9) * 100
        regress = dr < -REGRESS_RATE_PP or dp > REGRESS_P95_PCT
        rows.append({"场景": name, "成功率差pp": round(dr, 2), "P95变化%": round(dp, 1),
                     "回归": regress})
    return {"对比基线": b_ver, "对比结果": rows,
            "结论": "存在回归项，禁止发布；先定位再复测" if any(r["回归"] for r in rows)
                    else "无回归，版本可继续走发布流程(第43章)"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1.5.0")
    ap.add_argument("--legacy", action="store_true", help="使用 v1.4.3 历史数据集(用于生成基线)")
    ap.add_argument("--baseline", default="", help="历史结果 JSON(本脚本 --json-out 产物)")
    ap.add_argument("--json-out", default="")
    a = ap.parse_args()
    results = []
    failed = []
    for sc in default_config(a.legacy).scenarios:
        r = eval_scenario(sc)
        results.append(r)
        if r["判定"] == "FAIL":
            failed.append(sc.name)
    report = {"评测日期": date.today().isoformat(), "版本": a.version,
              "数据集": "v1.4.3历史数据(73.3%)" if a.legacy else "v1.5.0当前数据(93.3%)",
              "场景结果": results, "未达标场景": failed,
              "门禁": "未通过：存在未达标场景" if failed else "通过：全部场景达标"}
    if a.baseline:
        if not os.path.exists(a.baseline):
            print("基线文件不存在: " + a.baseline, file=sys.stderr)
            return 2
        with open(a.baseline, encoding="utf-8") as fh:
            report["回归对比"] = compare(json.load(fh), report)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
