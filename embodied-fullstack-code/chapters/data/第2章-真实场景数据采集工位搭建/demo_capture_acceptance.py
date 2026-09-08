# -*- coding: utf-8 -*-
"""第2章 L1 极简 Demo：首100条 Episode 采集验收（纯标准库）。

对应文章：首 100 条不是数量里程碑，是系统验收。
演示机制：模拟"采集会话"（每条含 场景/操作者/成功/时长/通道完整），
统计通过率并对照首100条验收清单逐项打钩。

运行：python demo_capture_acceptance.py
"""
from __future__ import annotations
import argparse, json, random, sys
from pathlib import Path
from dataclasses import dataclass, asdict

GATES = {  # 首100条验收清单（工程起点，可按项目调）
    "min_episodes": 100,
    "min_success_rate": 0.90,
    "min_failure_ratio": 0.10,
    "min_scenes": 3,
    "max_missing_channel_ratio": 0.02,
}


@dataclass
class Trial:
    """一次采集尝试的记录。"""
    episode_id: str
    scene: str
    operator: str
    success: bool
    duration_s: float
    channels_ok: bool


def simulate_session(seed: int = 7, n: int = 100) -> list[Trial]:
    """模拟一个采集会话：场景覆盖、~10% 失败、偶发通道缺失。"""
    rng = random.Random(seed)
    scenes = ["scene_a", "scene_b", "scene_c"]
    out = []
    for i in range(n):
        out.append(Trial(
            episode_id=f"ep-{i:04d}",
            scene=scenes[i % len(scenes)],
            operator=rng.choice(["alice", "bob"]),
            success=(i % 10) != 1,                             # 确定性 90% 成功率（10 条失败）
            duration_s=round(rng.uniform(3.0, 12.0), 1),
            channels_ok=rng.random() > 0.01,                  # ~1% 通道缺失
        ))
    return out


def check(trials: list[Trial]) -> dict:
    n = len(trials)
    ok = sum(t.success for t in trials)
    fail = n - ok
    scenes = {t.scene for t in trials}
    bad_ch = sum(1 for t in trials if not t.channels_ok)
    checks = {
        "总数>=100": n >= GATES["min_episodes"],
        "成功率>=90%": (ok / n) >= GATES["min_success_rate"],
        "失败样本>=10%": (fail / n) >= GATES["min_failure_ratio"],
        "场景覆盖>=3": len(scenes) >= GATES["min_scenes"],
        "通道缺失<=2%": (bad_ch / n) <= GATES["max_missing_channel_ratio"],
    }
    return {"total": n, "success": ok, "failure": fail,
            "scenes": sorted(scenes), "missing_channel": bad_ch,
            "checks": checks, "pass_all": all(checks.values())}


def main() -> int:
    ap = argparse.ArgumentParser(description="首100条采集验收Demo")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", type=Path, default=Path("session_demo.json"))
    args = ap.parse_args()
    trials = simulate_session(n=args.n)
    rep = check(trials)
    print(f"会话共 {rep['total']} 条：成功 {rep['success']} / 失败 {rep['failure']}"
          f" / 场景 {len(rep['scenes'])} / 通道缺失 {rep['missing_channel']}")
    for name, passed in rep["checks"].items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(">>> 验收结论：", "通过，可进入规模化采集" if rep["pass_all"] else "不通过，先修复短板")
    args.out.write_text(json.dumps([asdict(t) for t in trials], ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if rep["pass_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
