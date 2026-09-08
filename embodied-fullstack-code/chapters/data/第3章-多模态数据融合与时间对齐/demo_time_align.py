# -*- coding: utf-8 -*-
"""第3章 L1 极简 Demo：观测-动作时间对齐（纯标准库）。

机制演示：rgb 30Hz / joint 100Hz / action 100Hz(内容延迟35ms)
对比三种读取方式在 rgb 时刻得到的动作值误差：
  raw(取最近已到帧) / nearest(最近邻) / linear(线性插值)

运行：python demo_time_align.py
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path


def gen_signals(fps_rgb=30.0, fps_act=100.0, delay_s=0.035, n_act=200, seed=1):
    """合成"目标连续动作"并采样：rgb 低速、action 高速但内容延迟。"""
    rng = __import__("random").Random(seed)

    def truth(t: float) -> float:                    # 物理真值（连续函数）
        return math.sin(2 * math.pi * 0.5 * t) + 0.05 * t

    joint_ts = [i / fps_act for i in range(n_act)]
    action_delayed_ts = [t + delay_s for t in joint_ts]   # 动作"内容"晚到
    rgb_ts = [i / fps_rgb for i in range(int(n_act * fps_rgb / fps_act))]
    return {
        "fps_rgb": fps_rgb, "fps_act": fps_act,
        "rgb_ts": rgb_ts,
        "joint": {"ts": joint_ts,
                  "values": [truth(t) + rng.gauss(0, 0.01) for t in joint_ts]},
        "action": {"ts": action_delayed_ts,
                   "values": [truth(t) + rng.gauss(0, 0.01) for t in joint_ts]},
    }


def make_episodes(dst: Path, n: int = 3) -> Path:
    """生成 L2/L3 可消费的 Episode 目录（channels 标准 schema，含同步事件）。"""
    import random as _r
    import math as _m
    dst.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        delay = 0.030 + 0.005 * i
        d = gen_signals(seed=i, delay_s=delay)
        rng = _r.Random(i)
        joint_ts = d["joint"]["ts"]
        # 同步事件：t=0.8s 处的窄脉冲（模拟 LED 闪/敲击事件）
        def spike(t: float) -> float:
            return 1.2 * _m.exp(-((t - 0.8) / 0.008) ** 2)
        def truth(t: float) -> float:
            return _m.sin(2 * _m.pi * 0.5 * t) + 0.05 * t
        joint = {"ts": list(joint_ts),
                 "values": [truth(t) + spike(t) + rng.gauss(0, 0.01)
                            for t in joint_ts]}
        action = {"ts": list(joint_ts),
                  "values": [truth(t - delay) + spike(t - delay) + rng.gauss(0, 0.01)
                             for t in joint_ts]}
        rgb_ts = d["rgb_ts"]
        ep = {"episode_id": "ep-%04d" % i, "channels": {
            "rgb": {"ts": rgb_ts,
                    "values": [truth(t) + rng.gauss(0, 0.02) for t in rgb_ts]},
            "joint": joint,
            "action": action,
        }}
        (dst / ("ep-%04d.json" % i)).write_text(
            json.dumps(ep, ensure_ascii=False), encoding="utf-8")
    return dst


def _nearest_idx(ts: list[float], t: float) -> int:
    j = 0
    while j + 1 < len(ts) and abs(ts[j + 1] - t) <= abs(ts[j] - t):
        j += 1
    return j


def read_raw(ch: dict, t: float) -> float:
    """RAW：取'此刻之前最近已到达'的动作值（模拟未对齐的工程实现）。"""
    j = 0
    while j + 1 < len(ch["ts"]) and ch["ts"][j + 1] <= t:
        j += 1
    return ch["values"][j]


def read_nearest(ch: dict, t: float) -> float:
    return ch["values"][_nearest_idx(ch["ts"], t)]


def read_linear(ch: dict, t: float) -> float:
    ts, vs = ch["ts"], ch["values"]
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    j = _nearest_idx(ts, t)
    if ts[j] > t:
        j -= 1
    k = j + 1
    w = (t - ts[j]) / max(1e-9, ts[k] - ts[j])
    return vs[j] * (1 - w) + vs[k] * w


def main() -> int:
    ap = argparse.ArgumentParser(description="时间对齐最小演示")
    ap.add_argument("--make-data", type=Path, default=Path("demo_aligned.json"))
    ap.add_argument("--make-episodes", type=Path, default=None,
                    help="同时生成 L2/L3 标准 Episode 目录")
    args = ap.parse_args()
    data = gen_signals()
    args.make_data.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    if args.make_episodes:
        make_episodes(args.make_episodes, n=3)
        print("[demo] Episode 目录: " + str(args.make_episodes))

    truth = lambda t: math.sin(2 * math.pi * 0.5 * t) + 0.05 * t
    errs = {"raw": [], "nearest": [], "linear": []}
    for t in data["rgb_ts"]:
        errs["raw"].append(abs(read_raw(data["action"], t) - truth(t)))
        errs["nearest"].append(abs(read_nearest(data["action"], t) - truth(t)))
        errs["linear"].append(abs(read_linear(data["action"], t) - truth(t)))

    print("方法      平均误差    最大误差")
    for k, arr in errs.items():
        mean = sum(arr) / len(arr)
        print(f"{k:<9} {mean:.4f}      {max(arr):.4f}")
    print("结论：动作内容延迟 35ms 时，RAW 读取误差最大，"
          "线性插值最接近真值——先同步后插值是数据对齐的基本功。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
