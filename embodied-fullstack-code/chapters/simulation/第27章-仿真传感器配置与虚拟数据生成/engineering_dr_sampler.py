# -*- coding: utf-8 -*-
"""第27章 L2 工业工程版：域随机化参数采样器（可复现 Manifest）。"""
from __future__ import annotations

import argparse, json, logging, random, sys
from pathlib import Path

logger = logging.getLogger("dr_sampler")

RANGES = {
    "brightness_delta": (-30, 30),
    "contrast": (0.8, 1.3),
    "noise_sigma": (0, 8),
    "friction": (0.3, 0.9),
    "object_scale": (0.95, 1.08),
    "camera_tilt_deg": (-3, 3),
}


def sample(rng):
    return {k: round(rng.uniform(*v), 4) for k, v in RANGES.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description="域随机化采样(工程版)")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        rng = random.Random(args.seed)
        items = []
        for i in range(args.n):
            p = sample(rng)
            p["seed"] = args.seed + i
            items.append({"sample_id": f"dr-{i:04d}", "params": p})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "dr_manifest.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"采样 {args.n} 组参数(种子 {args.seed})，见 dr_manifest.json")
    print("范围:", {k: list(v) for k, v in RANGES.items()})
    print("纪律：物理语义(重力/动作)绝不随机；每样本记录 seed 供复现")
    return 0


if __name__ == "__main__":
    sys.exit(main())
