# -*- coding: utf-8 -*-
"""第35章 L2 工业工程版：驱动接入六项检查（枚举/帧率/时间戳/单位/供电/恢复）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("driver_check")
CHECKS = ["enumerate", "stable_fps", "hw_timestamp", "units_ok",
          "power_ok", "auto_recover"]


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    sensors = [
        {"name": "rgb_cam", "enumerate": True, "stable_fps": True,
         "hw_timestamp": True, "units_ok": True, "power_ok": True,
         "auto_recover": False},
        {"name": "lidar", "enumerate": True, "stable_fps": True,
         "hw_timestamp": True, "units_ok": True, "power_ok": True,
         "auto_recover": True},
    ]
    (root / "sensors.json").write_text(json.dumps(sensors), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="驱动检查(工程版)")
    ap.add_argument("--input", type=Path)
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
        sensors = json.loads(args.input.read_text(encoding="utf-8"))
        rows = []
        for s in sensors:
            miss = [c for c in CHECKS if s.get(c) is not True]
            rows.append({"name": s["name"], "missing": miss,
                         "pass": not miss})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"rows": rows, "pass_all": all(r["pass"] for r in rows)}
    (args.out_dir / "driver_check.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['name']:<10} [{'PASS' if r['pass'] else 'FAIL'}] "
              f"缺: {','.join(r['missing']) or '无'}")
    print("结论:", "全部达标" if rep["pass_all"] else "修复后重测")
    return 0 if rep["pass_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
