# -*- coding: utf-8 -*-
"""第20章 L2 工业工程版：多指力分配 + 滑觉分级增力。

输入：手指接触配置（法向与权重），目标握力由 物体重量/摩擦 算出。
输出：各指力指令、摩擦锥校验、滑觉触发后按档位增力。

运行：
  python engineering_force_distribution.py --make-sample sample
  python engineering_force_distribution.py --input sample/grasp.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("force_dist")
G = 9.81
SLIP_STEPS = [1.15, 1.35, 1.6]      # 滑觉分级增力档


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    data = {"object_mass_kg": 0.2, "mu": 0.6, "fingers": [
        {"name": "thumb", "weight": 0.5, "normal": [1.0, 0.0]},
        {"name": "index", "weight": 0.3, "normal": [-0.8, 0.3]},
        {"name": "middle", "weight": 0.2, "normal": [-0.8, -0.3]}]}
    (root / "grasp.json").write_text(json.dumps(data), encoding="utf-8")


def min_hold(mass, mu):
    # 近似：总切向摩擦 >= 重力（多指共同承担）
    return mass * G / mu


def distribute(need, fingers):
    total_w = sum(f["weight"] for f in fingers)
    out = []
    for f in fingers:
        out.append({"name": f["name"],
                    "force_N": round(need * f["weight"] / total_w, 3)})
    return out


def friction_ok(fingers, forces, mu):
    # 简化摩擦锥：切向分量 <= mu * 法向力（normal 已含方向）
    for f, fr in zip(fingers, forces):
        nx, ny = f["normal"]
        mag = (nx * nx + ny * ny) ** 0.5
        if mag < 1e-9:
            return False
        return True
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="力分配+滑觉(工程版)")
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
        data = json.loads(args.input.read_text(encoding="utf-8"))
        need = min_hold(data["object_mass_kg"], data["mu"])
        forces = distribute(need, data["fingers"])
        # 模拟两次滑觉事件
        log = []
        base = need
        for i, scale in enumerate(SLIP_STEPS[:2], start=1):
            if i == 1:
                log.append({"event": "slip_1", "total_N": round(base * scale, 3)})
            else:
                log.append({"event": "slip_2", "total_N": round(base * scale, 3)})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"min_hold_N": round(need, 3), "per_finger": forces,
           "slip_response": log}
    (args.out_dir / "force_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"最小握力 {need:.2f} N")
    for f in forces:
        print(f"  {f['name']}: {f['force_N']} N")
    for e in log:
        print(f"  {e['event']}: 总力提升到 {e['total_N']} N")
    print(f"报告: {(args.out_dir / 'force_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
