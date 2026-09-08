# -*- coding: utf-8 -*-
"""第43章 L1 极简 Demo：健康度监控打点（成功率/P99/抖动阈值告警）。

监控的本质 = 指标 + 阈值 + 动作。本 Demo 用一组手写实测样本演示：
窗口滚动统计 → 阈值越界 → 输出告警，让你 5 分钟看懂线上监控最小闭环。
"""
from __future__ import annotations
import argparse, json, sys

# (分钟, 成功数, 失败数, P99延时ms) —— 手工构造：第 8~10 分钟模拟一次抖动
SAMPLE: list[tuple[int, int, int, int]] = [
    (0, 98, 0, 120), (1, 97, 1, 132), (2, 99, 0, 118), (3, 96, 0, 141),
    (4, 98, 0, 128), (5, 97, 1, 135), (6, 99, 0, 122), (7, 95, 0, 145),
    (8, 60, 38, 610), (9, 70, 29, 590), (10, 88, 9, 260),   # 抖动窗口
    (11, 97, 1, 138), (12, 99, 0, 121), (13, 96, 0, 133),
    (14, 98, 0, 127), (15, 99, 0, 119), (16, 97, 1, 140),
    (17, 98, 0, 130), (18, 99, 0, 124), (19, 96, 0, 142),
]
FAIL_RATE_MAX = 0.05   # 失败率红线 5%
P99_MAX = 200          # P99 延时红线 200ms


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=5, help="滚动窗口分钟数")
    ap.add_argument("--json-out", default="", help="可选：结果 JSON 输出路径")
    a = ap.parse_args()
    alerts: list[dict] = []
    last_ok = True
    for i in range(len(SAMPLE)):
        win = SAMPLE[max(0, i - a.window + 1): i + 1]
        ok = sum(r[1] for r in win)
        bad = sum(r[2] for r in win)
        fail_rate = bad / (ok + bad)
        p99 = max(r[3] for r in win)   # 极简近似：取窗口内最大延时
        minute = win[-1][0]
        if fail_rate > FAIL_RATE_MAX or p99 > P99_MAX:
            if last_ok:  # 防抖：只在状态翻转时记一条告警，避免刷屏
                alerts.append({"分钟": minute, "失败率%": round(fail_rate * 100, 1),
                               "P99ms": p99,
                               "触发": "失败率越界" if fail_rate > FAIL_RATE_MAX else "P99越界"})
            last_ok = False
        else:
            last_ok = True
    report = {"监控窗口": f"{a.window}分钟滚动", "红线": {"失败率%": 5.0, "P99ms": 200},
              "告警条数": len(alerts), "告警明细": alerts,
              "结论": "命中抖动窗口8~10分钟，其余时段健康" if alerts else "全部健康"}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
