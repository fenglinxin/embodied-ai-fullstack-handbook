# -*- coding: utf-8 -*-
"""第5章 L1 极简 Demo：重复轨迹识别 + 失败样本保护去重。

机制：把动作序列量化成指纹(2cm/2度桶)，同指纹=重复候选；
每组最多保留 success/失败 各一条，避免误删失败样本。

运行：python demo_dedup_balance.py --out records.json
"""
from __future__ import annotations
import argparse, json, math, random, sys
from pathlib import Path
from collections import defaultdict

QUANT = 0.02   # 量化桶：2cm / 2deg


def make_traj(base: list[list[float]], rng: random.Random, jitter=0.005) -> list[list[float]]:
    """给基础轨迹加微小抖动，模拟"重复采集但略有噪声"。"""
    return [[x + rng.uniform(-jitter, jitter),
             y + rng.uniform(-jitter, jitter),
             g] for x, y, g in base]


def base_traj(kind: str) -> list[list[float]]:
    if kind == "pick":
        return [[0.1 + 0.02 * i, 0.2, 0] for i in range(10)]
    return [[0.3, 0.1 + 0.02 * i, 1] for i in range(10)]


def make_records() -> list[dict]:
    rng = random.Random(42)
    out = []
    for i in range(16):
        kind = "pick" if i % 2 == 0 else "place"
        scene = f"scene_{i % 4}"
        traj = make_traj(base_traj(kind), rng)
        out.append({"episode_id": f"ep-{i:04d}", "task": kind, "scene": scene,
                    "success": (i % 9 != 0),
                    "trajectory": traj})
    out.append({"episode_id": "ep-fail-1", "task": "pick", "scene": "scene_0",
                "success": False, "trajectory": make_traj(base_traj("pick"), rng)})
    return out


def fingerprint(traj: list[list[float]]) -> str:
    q = [f"{round(x / QUANT)},{round(y / QUANT)},{g}" for x, y, g in traj]
    return "|".join(q)


def dedupe(recs: list[dict]) -> tuple[list[dict], list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        key = r["task"] + "|" + r["scene"] + "|" + fingerprint(r["trajectory"])
        groups[key].append(r)
    kept, removed = [], []
    for members in groups.values():
        success = [m for m in members if m.get("success") is True]
        fail = [m for m in members if m.get("success") is False]
        keep_now = (success[:1] + fail[:1]) or members[:1]
        kept.extend(keep_now)
        removed.extend(m for m in members if m not in keep_now)
    return kept, removed


def main() -> int:
    ap = argparse.ArgumentParser(description="去重+失败保护Demo")
    ap.add_argument("--out", type=Path, default=Path("records.json"))
    args = ap.parse_args()
    recs = make_records()
    kept, removed = dedupe(recs)
    before = defaultdict(int)
    after = defaultdict(int)
    for r in recs:
        before[(r["task"], r["scene"])] += 1
    for r in kept:
        after[(r["task"], r["scene"])] += 1
    print(f"去重: {len(recs)} -> {len(kept)} (冗余 {len(removed)})")
    print("失败样本保护: 去重前后失败数 "
          f"{sum(1 for r in recs if not r['success'])} -> "
          f"{sum(1 for r in kept if not r['success'])}")
    print("task×scene 分布(前->后):")
    for k in sorted(set(before) | set(after)):
        print(f"  {k}: {before[k]} -> {after[k]}")
    args.out.write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
