# -*- coding: utf-8 -*-
"""第32章 L3 高阶优化版：整机架构接口审计（带宽/供电/字段完整性）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("arch_audit")
BUS_BUDGET_MBPS = 2000
POWER_BUDGET_W = 800
FIELDS = ("bandwidth_mbps", "power_w", "protocol")


def main() -> int:
    ap = argparse.ArgumentParser(description="架构审计(L3)")
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    if args.config:
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
    else:
        cfg = {"components": [
            {"name": "rgb_cam", "bandwidth_mbps": 400, "power_w": 5,
             "protocol": "usb3"},
            {"name": "lidar", "bandwidth_mbps": 300, "power_w": 12,
             "protocol": "eth"},
            {"name": "ai_box", "power_w": 300, "protocol": "pcie",
             "bandwidth_mbps": 0},
            {"name": "arm_ctrl", "power_w": 400},
        ]}
    try:
        missing, bw, pw = [], 0, 0
        for c in cfg["components"]:
            miss = [f for f in FIELDS if c.get(f) is None]
            if miss:
                missing.append({"name": c["name"], "missing": miss})
            bw += c.get("bandwidth_mbps", 0)
            pw += c.get("power_w", 0)
        checks = {"bus_over_budget": bw > BUS_BUDGET_MBPS * 0.8,
                  "power_over_budget": pw > POWER_BUDGET_W,
                  "missing_fields": missing}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"total_bandwidth_mbps": bw, "bus_budget_mbps": BUS_BUDGET_MBPS,
           "total_power_w": pw, "power_budget_w": POWER_BUDGET_W, **checks}
    (args.out_dir / "arch_audit.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"带宽 {bw}/{BUS_BUDGET_MBPS*0.8:.0f}Mbps "
          f"{'超标!' if checks['bus_over_budget'] else 'OK'}")
    print(f"功耗 {pw}/{POWER_BUDGET_W}W "
          f"{'超标!' if checks['power_over_budget'] else 'OK'}")
    if missing:
        print("字段缺失:", missing)
    return 0 if not checks["bus_over_budget"] and not checks["power_over_budget"]         and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
