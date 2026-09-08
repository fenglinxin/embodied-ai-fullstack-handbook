# -*- coding: utf-8 -*-
"""第15章 L3 高阶优化版：模态消融 + 掉线降级分析。

回答文章问题：每路输入贡献多少？缺一路会怎样？
  * joint-only / imu-only / both 三种组合跑同一批测量
  * 输出各组合 RMSE（可量化消融）
  * 检测测量源的间隙（掉线），给出降级策略

运行：
  python engineering_state_estimator.py --make-sample sample
  python advanced_modality_ablation.py --input sample/measurements.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path

from engineering_state_estimator import run_filter, rmse

logger = logging.getLogger("modality_ablation")
DROP_GAP_S = 0.5


def gaps(rows, source):
    ts = [m["t"] for m in rows if m["source"] == source]
    return [round(ts[i + 1] - ts[i], 3) for i in range(len(ts) - 1)]


def main() -> int:
    ap = argparse.ArgumentParser(description="模态消融与掉线分析(L3)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        rows = json.loads(args.input.read_text(encoding="utf-8"))
        rows.sort(key=lambda m: m["t"])
        combos = {"both": {"joint", "imu"},
                  "joint_only": {"joint"},
                  "imu_only": {"imu"}}
        results = {}
        for name, use in combos.items():
            est = run_filter(rows, use)
            results[name] = {"rmse_pos": rmse(est, "pos"),
                             "rmse_vel": rmse(est, "vel")}
        drop = {}
        for src in ("joint", "imu"):
            g = gaps(rows, src)
            over = [x for x in g if x > DROP_GAP_S]
            drop[src] = {"max_gap_s": max(g) if g else None,
                         "over_0_5s_count": len(over)}
        both = results["both"]["rmse_pos"]
        only = results["joint_only"]["rmse_pos"]
        report = {"ablation": results,
                  "degradation_joint_only_pos": round(
                      only / both, 2) if both else None,
                  "dropout": drop,
                  "advice": ("两路融合必要：joint_only 位置误差显著升高，"
                             "imu 掉线时保持位置更新；任一模态掉线须降级限速"
                             if only and both and only / both > 1.5
                             else "融合收益在当前数据上有限，检查传感器噪声比")}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "modality_ablation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, r in results.items():
        print(f"{name:<12} RMSE_pos={r['rmse_pos']} RMSE_vel={r['rmse_vel']}")
    print("掉线间隙:", drop)
    print("建议:", report["advice"])
    print(f"报告: {(args.out_dir / 'modality_ablation.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
