# -*- coding: utf-8 -*-
"""评测工程 L1 极简 Demo：任务成功率评测（分场景统计 + 阈值放行）。

评测的本质 = 固定任务集 + 重复试验 + 结果统计。
本 Demo 手写三场景试跑结果：成功/失败 + 循环时长，输出场景表与整体判定。
"""
from __future__ import annotations
import argparse, json, sys

# 每个场景的 (结果, 循环秒)；1=成功 0=失败
TRIALS: dict[str, list[tuple[int, float]]] = {
    "抓取-透明杯": [(1, 8.2), (1, 7.9), (0, 12.4), (1, 8.0), (1, 8.8),
                   (1, 9.1), (1, 8.3), (0, 11.9), (1, 8.6), (1, 8.4)],
    "抓取-纸盒":   [(1, 6.1), (1, 6.8), (1, 6.5), (1, 6.0), (1, 6.9),
                   (1, 6.3), (0, 9.8), (1, 6.6), (1, 6.2), (1, 6.4)],
    "避障-动态行人": [(1, 15.2), (1, 16.8), (0, 20.1), (1, 15.9), (1, 14.8),
                    (1, 16.2), (1, 15.5), (0, 22.3), (1, 16.0), (1, 15.1)],
}
MIN_RATE = 0.90   # 场景放行线：成功率 ≥90%


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-rate", type=float, default=MIN_RATE)
    a = ap.parse_args()
    rows = []
    for scene, runs in TRIALS.items():
        ok = sum(r for r, _ in runs)
        rate = ok / len(runs)
        avg = sum(t for _, t in runs if True) / len(runs)  # 全部试次平均循环
        rows.append({"场景": scene, "试次": len(runs), "成功": ok,
                     "成功率%": round(rate * 100, 1),
                     "平均循环s": round(avg, 1),
                     "判定": "PASS" if rate >= a.min_rate else "FAIL"})
    failed = [r["场景"] for r in rows if r["判定"] == "FAIL"]
    print(json.dumps({"放行线": f"成功率≥{a.min_rate * 100:.0f}%", "场景结果": rows,
                      "未达标场景": failed,
                      "整体结论": "评测未通过：禁止发布" if failed else "全部场景达标，可进入验收(第44章)"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
