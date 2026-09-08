# -*- coding: utf-8 -*-
"""第32章 L2 工业工程版：算力/功耗/电池预算计算器。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("budget")


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    cfg = {"models": [{"name": "detector", "vram_gb": 1.0, "fps": 30},
                      {"name": "vla", "vram_gb": 8.0, "fps": 3}],
           "sensors_mbps": [{"name": "rgb", "mbps": 250},
                            {"name": "depth", "mbps": 120}],
           "motor_peak_w": 600, "compute_avg_w": 90,
           "runtime_h": 4.0, "battery_eff": 0.8, "vram_headroom": 1.25,
           "power_headroom": 1.3}
    (root / "budget.json").write_text(json.dumps(cfg), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="整机预算(工程版)")
    ap.add_argument("--config", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
        vram = sum(m["vram_gb"] for m in cfg["models"]) * cfg["vram_headroom"]
        bandwidth = sum(s["mbps"] for s in cfg["sensors_mbps"]) / 1000.0
        peak_power = (cfg["motor_peak_w"] + cfg["compute_avg_w"]) *             cfg["power_headroom"]
        avg_power = cfg["motor_peak_w"] * 0.3 + cfg["compute_avg_w"]
        battery_wh = avg_power * cfg["runtime_h"] / cfg["battery_eff"]
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"vram_need_gb": round(vram, 1), "peak_power_w": round(peak_power, 0),
           "bandwidth_gbps": round(bandwidth, 2),
           "battery_wh": round(battery_wh, 0),
           "advice": "先定模型延迟预算再选卡；供电按峰值"}
    (args.out_dir / "budget_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in rep.items():
        if k != "advice":
            print(f"{k}: {v}")
    print("建议:", rep["advice"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
