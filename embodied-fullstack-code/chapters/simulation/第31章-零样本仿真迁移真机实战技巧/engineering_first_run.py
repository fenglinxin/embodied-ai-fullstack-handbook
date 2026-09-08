# -*- coding: utf-8 -*-
"""第31章 L2 工业工程版：首跑分级扩测执行器（8步清单的程序化版）。"""
from __future__ import annotations

import argparse, json, logging, random, sys
from pathlib import Path

logger = logging.getLogger("first_run")

STAGES = [
    {"stage": "precheck", "speed": 0.2, "trials": 5, "exit": 0.8,
     "desc": "现场一致性+链路预检"},
    {"stage": "dryrun_no_object", "speed": 0.3, "trials": 10, "exit": 0.9,
     "desc": "空跑不带物体"},
    {"stage": "minimal_variant", "speed": 0.4, "trials": 30, "exit": 0.7,
     "desc": "最简单变体统计"},
    {"stage": "full_speed", "speed": 1.0, "trials": 50, "exit": 0.85,
     "desc": "全速扩测"},
]


def simulate_stage(stage_cfg, seed):
    rng = random.Random(seed)
    # 阶段越难真实成功率越低（最小变体后回升）
    base = {"precheck": 0.95, "dryrun_no_object": 0.92,
            "minimal_variant": 0.75, "full_speed": 0.88}[stage_cfg["stage"]]
    return sum(1 for _ in range(stage_cfg["trials"])
               if rng.random() < base)


def main() -> int:
    ap = argparse.ArgumentParser(description="首跑分级扩测(工程版)")
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        report = []
        blocked = None
        for s in STAGES:
            ok_n = simulate_stage(s, args.seed)
            rate = ok_n / s["trials"]
            passed = rate >= s["exit"]
            report.append({"stage": s["stage"], "desc": s["desc"],
                           "speed": s["speed"], "trials": s["trials"],
                           "success": ok_n, "rate": round(rate, 3),
                           "exit": s["exit"], "pass": passed})
            if not passed:
                blocked = s["stage"]
                break
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "first_run_report.json").write_text(
        json.dumps({"report": report, "blocked_at": blocked},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    for r in report:
        print(f"{r['stage']:<20} rate={r['rate']:.0%} "
              f"(exit {r['exit']:.0%}) [{'PASS' if r['pass'] else 'STOP'}]")
    print("结论:", "全部通过->正式验证" if blocked is None
          else f"在 {blocked} 拦截->回仿真补课/降难度")
    return 0 if blocked is None else 1


if __name__ == "__main__":
    sys.exit(main())
