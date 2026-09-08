# -*- coding: utf-8 -*-
"""第1章 L1 极简 Demo：具身数据体检（零依赖，Python>=3.9 直接运行）。

核心机制演示：
  1) 具身 Episode 的必备通道（rgb/joint/action/success）；
  2) 每个通道的时间戳单调性检查（时序是具身数据生命线）；
  3) 观测-动作不同频时的"半帧错位"近似检测；
  4) 输出"能训/需清洗/丢弃"三类结论，复现第1章六步流水线的体检环节。

运行：
  python demo_data_pipeline.py                # 自动生成演示数据并体检
  python demo_data_pipeline.py --make-demo-data demo_data
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

REQUIRED_CHANNELS = ("rgb", "joint", "action")   # 最小三件套（观测/本体/动作）
MAX_SYNC_GAP_S = 0.05                            # 观测与动作最大允许半帧错位（秒）


# ---------------------------------------------------------------- 合成演示数据
def _gen_ts(start: float, fps: float, n: int, jitter: bool = False,
            broken: bool = False) -> list[float]:
    """按 fps 生成时间戳；broken=True 时人为制造一次非单调跳变。"""
    out: list[float] = []
    t = start
    for i in range(n):
        out.append(t)
        step = 1.0 / fps
        if jitter:
            step *= random.uniform(0.9, 1.1)
        t += step
    if broken and len(out) > 4:                  # 制造"时间倒流"脏数据
        out[3] = out[2] - 0.01
    return out


def make_demo_episode(ep_id: str, *, clean: bool = True, scene: str = "kitchen_a") -> dict:
    """生成一条带时间戳的合成 Episode（仅用于教学演示）。"""
    rng = random.Random(ep_id)
    n_rgb, fps_rgb = 12, 30.0
    n_joint, fps_joint = 40, 100.0
    rgb_ts = _gen_ts(0.0, fps_rgb, n_rgb)
    joint_ts = _gen_ts(0.0, fps_joint, n_joint)
    action_ts = [round(t, 6) for t in joint_ts]  # 动作与关节同频对齐
    black = [0] * n_rgb
    if not clean:
        black[2] = 1                              # 第3帧黑帧
        action_ts = _gen_ts(0.0, fps_joint, n_joint, broken=True)  # 动作时间戳断裂
    return {
        "episode_id": ep_id,
        "task": "pick_cup", "scene": scene, "success": True,
        "language": "把红色马克杯放到托盘上",
        "channels": {
            "rgb":   {"ts": [round(t, 6) for t in rgb_ts], "black": black},
            "joint": {"ts": [round(t, 6) for t in joint_ts]},
            "action": {"ts": action_ts},
        },
    }


def build_demo_dataset(dst: Path, n: int = 3) -> Path:
    """生成 n 条演示 Episode（含 1 条脏数据）。"""
    dst.mkdir(parents=True, exist_ok=True)
    scenes = ["kitchen_a", "kitchen_b", "kitchen_c"]
    for i in range(n):
        ep = make_demo_episode(f"ep-{i:04d}", clean=(i % 2 == 0), scene=scenes[i % len(scenes)])
        (dst / f"{ep['episode_id']}.json").write_text(
            json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst


# ---------------------------------------------------------------- 核心检查
def check_monotonic(ts: list[float]) -> tuple[bool, int]:
    """时间戳必须严格单调递增；返回(是否通过, 违规次数)。"""
    bad = sum(1 for a, b in zip(ts, ts[1:]) if b <= a)
    return (bad == 0, bad)


def check_channels(ep: dict) -> list[str]:
    """通道完整性检查：缺 rgb/joint/action 直接判不可训。"""
    channels = ep.get("channels", {})
    missing = [c for c in REQUIRED_CHANNELS if c not in channels]
    if "success" not in ep:
        missing.append("success标记")
    return missing


def check_sync_gap(ep: dict) -> float:
    """观测/动作跨通道同步：以 rgb 时间戳为基准，找 action 最近帧的最大间隔。"""
    rgb = ep["channels"]["rgb"]["ts"]
    act = ep["channels"]["action"]["ts"]
    if not rgb or not act:
        return float("inf")
    worst = 0.0
    j = 0
    for t in rgb:                                 # 双指针找最近邻，O(n)
        while j + 1 < len(act) and abs(act[j + 1] - t) <= abs(act[j] - t):
            j += 1
        worst = max(worst, abs(act[j] - t))
    return worst


def inspect_episode(ep: dict) -> dict:
    """对单条 Episode 做体检，输出结构化结论。"""
    ch = ep["channels"]
    missing = check_channels(ep)
    mono_ok, mono_bad = check_monotonic(ch["rgb"]["ts"])
    joint_ok, joint_bad = check_monotonic(ch["joint"]["ts"])
    act_ok, act_bad = check_monotonic(ch["action"]["ts"])
    black_ratio = sum(ch["rgb"].get("black", [])) / max(1, len(ch["rgb"]["ts"]))
    sync_gap = check_sync_gap(ep)

    hard_issues: list[str] = []
    soft_issues: list[str] = []
    if missing:
        hard_issues.append("缺通道: " + ",".join(missing))
    if not (mono_ok and joint_ok and act_ok):
        hard_issues.append(f"时间戳非单调(违规{mono_bad + joint_bad + act_bad}处)")
    if sync_gap > MAX_SYNC_GAP_S:
        hard_issues.append(f"观测-动作错位{sync_gap * 1000:.0f}ms>50ms")
    if black_ratio > 0.05:
        soft_issues.append(f"黑帧占比{black_ratio:.0%}>5%")

    if hard_issues:
        verdict = "丢弃/返工"
    elif soft_issues:
        verdict = "需清洗"
    else:
        verdict = "可入训练集"
    return {"episode_id": ep.get("episode_id"),
            "success": ep.get("success"),
            "hard_issues": hard_issues, "soft_issues": soft_issues,
            "sync_gap_ms": round(sync_gap * 1000, 2),
            "black_ratio": round(black_ratio, 4),
            "verdict": verdict}


def main() -> int:
    parser = argparse.ArgumentParser(description="具身数据极简体检 Demo")
    parser.add_argument("--make-demo-data", default="demo_data",
                        help="生成演示数据目录（默认 demo_data）")
    args = parser.parse_args()

    data_dir = Path(args.make_demo_data)
    if not any(data_dir.glob("*.json")):
        build_demo_dataset(data_dir, n=3)
        print(f"[demo] 已生成演示数据: {data_dir}")

    print("=" * 62)
    print(f"{'episode_id':<10}{'success':<8}{'同步ms':<9}{'结论':<12}")
    print("-" * 62)
    results = []
    for f in sorted(data_dir.glob("*.json")):
        ep = json.loads(f.read_text(encoding="utf-8"))
        r = inspect_episode(ep)
        results.append(r)
        print(f"{r['episode_id']:<10}{str(r['success']):<8}"
              f"{r['sync_gap_ms']:<9}{r['verdict']:<12}")
        for tag, items in (("HARD", r["hard_issues"]), ("soft", r["soft_issues"])):
            for it in items:
                print(f"    [{tag}] {it}")
    ok = sum(1 for r in results if r["verdict"] == "可入训练集")
    print("-" * 62)
    print(f"汇总: {len(results)} 条，可入训练集 {ok} 条。")
    print("结论：脏数据第一道关卡=通道齐全+时间戳单调+观测动作同步。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
