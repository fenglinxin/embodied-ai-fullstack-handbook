# -*- coding: utf-8 -*-
"""第43章 L2 工程标准版：灰度发布 + 自动回滚执行器。

流程：金丝雀 5% → 观察窗比对基线(失败率/P99) → 通过则 20%→50%→100% 放量。
三档判定：
  PASS     — 指标与基线无显著差异，继续放量；
  WATCH    — 软越界(单点抖动/轻微超差)：本次放量不打断，下个观察窗强制复核，
             连续两个 WATCH 或转硬越界即回滚；
  ROLLBACK — 硬越界(失败率差>5pp 或 P99 差>150ms)：立即回滚并输出动作清单。
内置三套场景：healthy(全通过) / bad(劣化回滚) / flaky(抖动自愈，WATCH 后继续)。
"""
from __future__ import annotations
import argparse, json, sys
from dataclasses import dataclass, field

FR_SOFT = 0.02     # 失败率软红线：比基线高 ≤2pp 允许观察
FR_HARD = 0.05     # 失败率硬红线：高 >5pp 直接回滚
P99_SOFT = 40.0    # P99 软红线：高 ≤40ms 允许观察
P99_HARD = 150.0   # P99 硬红线：高 >150ms 直接回滚
WATCH_LIMIT = 2    # 连续 WATCH 上限，达到即回滚


@dataclass
class Stage:
    ratio: float          # 放量比例
    minutes: int = 5      # 观察窗长度


@dataclass
class ReleaseConfig:
    app: str = "grasp-pipeline"
    new_version: str = "v1.4.2"
    baseline_version: str = "v1.4.1"
    stages: list = field(default_factory=lambda: [
        Stage(0.05, 5), Stage(0.20, 5), Stage(0.50, 5), Stage(1.00, 5)])


# 基线指标：(分钟, 失败率小数, P99ms)
BASELINE = [(0, .010, 128), (1, .012, 135), (2, .009, 130), (3, .011, 132),
            (4, .013, 138), (5, .010, 131), (6, .012, 136), (7, .011, 129),
            (8, .009, 133), (9, .012, 137), (10, .010, 130), (11, .011, 134)]

SCENARIOS: dict[str, list[tuple[int, float, float]]] = {
    # healthy：与基线几乎无差异 -> 全程放量成功
    "healthy": [(0, .011, 130), (1, .010, 133), (2, .012, 129), (3, .009, 135),
                (4, .011, 131), (5, .012, 134), (6, .010, 130), (7, .009, 128),
                (8, .011, 132), (9, .010, 136), (10, .012, 131), (11, .011, 133)],
    # bad：第 3 分钟起失败率飙到 8%+、P99 超 400ms -> 硬越界立即回滚
    "bad": [(0, .011, 131), (1, .012, 136), (2, .013, 134), (3, .082, 412),
            (4, .091, 455), (5, .078, 388), (6, .085, 420), (7, .090, 431),
            (8, .081, 402), (9, .088, 450), (10, .086, 428), (11, .083, 415)],
    # flaky：第 3~4 分钟 P99 单点尖峰(软越界 WATCH)，第 5 分钟起自愈 -> 继续放量
    "flaky": [(0, .011, 132), (1, .012, 130), (2, .010, 136), (3, .014, 205),
              (4, .015, 218), (5, .013, 134), (6, .010, 129), (7, .011, 133),
              (8, .012, 137), (9, .009, 130), (10, .011, 134), (11, .010, 131)],
}


def window_stats(series: list[tuple[int, float, float]], start: int, length: int) -> tuple[float, float]:
    seg = series[start:start + length]
    if not seg:
        return 0.0, 0.0
    return (sum(r[1] for r in seg) / len(seg), max(r[2] for r in seg))


def verdict(d_fr: float, d_p99: float) -> tuple[str, list[str]]:
    """返回 (判定, 越界项列表)。先判硬越界，再判软越界。"""
    hard = []
    if d_fr > FR_HARD:
        hard.append(f"失败率+{d_fr * 100:.1f}pp(硬)")
    if d_p99 > P99_HARD:
        hard.append(f"P99+{d_p99:.0f}ms(硬)")
    if hard:
        return "ROLLBACK", hard
    soft = []
    if d_fr > FR_SOFT:
        soft.append(f"失败率+{d_fr * 100:.1f}pp")
    if d_p99 > P99_SOFT:
        soft.append(f"P99+{d_p99:.0f}ms")
    return ("WATCH" if soft else "PASS"), soft


def check_window(canary: list[tuple[int, float, float]], start: int,
                 base: list[tuple[int, float, float]], st: Stage) -> dict:
    c_fr, c_p99 = window_stats(canary, start, st.minutes)
    b_fr, b_p99 = window_stats(base, start, st.minutes)
    v, items = verdict(c_fr - b_fr, c_p99 - b_p99)
    return {"窗起点分钟": start, "金丝雀失败率%": round(c_fr * 100, 2),
            "基线失败率%": round(b_fr * 100, 2), "金丝雀P99ms": c_p99,
            "基线P99ms": b_p99, "判定": v, "越界项": items}


def run_release(scenario: str, cfg: ReleaseConfig) -> dict:
    canary = SCENARIOS[scenario]
    log: list[dict] = []
    rolled_back = False
    idx = 0
    watch_streak = 0
    for si, st in enumerate(cfg.stages):
        check = check_window(canary, idx, BASELINE, st)
        v = check["判定"]
        if v == "WATCH":
            watch_streak += 1
            check["连续WATCH"] = watch_streak
            if watch_streak >= WATCH_LIMIT:
                v = "ROLLBACK"
                check["判定"] = v
                check["越界项"] = check["越界项"] + ["连续WATCH达上限"]
        else:
            watch_streak = 0
        if v == "ROLLBACK":
            rolled_back = True
            log.append({"阶段": si + 1, "放量": f"{st.ratio * 100:.0f}%",
                        "结果": "回滚", **check})
            break
        idx += st.minutes
        log.append({"阶段": si + 1, "放量": f"{st.ratio * 100:.0f}%",
                    "结果": "放量继续" if v == "PASS" else "放量继续(WATCH复核)", **check})
    return {"应用": cfg.app, "发布版本": cfg.new_version, "场景": scenario,
            "过程": log,
            "最终结论": ("硬越界或连续WATCH → 自动回滚到 " + cfg.baseline_version +
                        "；动作: ①流量切回旧版 ②停新版本号 ③保留灰度日志 ④复盘归因")
                        if rolled_back else "全部观察窗通过 → 全量发布完成",
            "回滚": rolled_back}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="bad", choices=sorted(SCENARIOS),
                    help="healthy=正常发布 / bad=劣化回滚 / flaky=抖动但自愈")
    a = ap.parse_args()
    print(json.dumps(run_release(a.scenario, ReleaseConfig()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
