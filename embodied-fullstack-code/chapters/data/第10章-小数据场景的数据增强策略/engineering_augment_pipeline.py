# -*- coding: utf-8 -*-
"""第10章 L2 工业工程版：可配置观测增强流水线（纯标准库）。

输入：<input>/*.json，每个 Episode 含 image(灰度矩阵 0-255) 与 action(不扰动)。
增强目录：brightness / contrast / noise，参数区间来自 config。
守则：只增强观测；动作原样；输出每变体参数与身份保持指标。

运行：
  python engineering_augment_pipeline.py --input-dir sample --out-dir out \
      --augments-per-episode 6 --make-sample
"""
from __future__ import annotations

import argparse, json, logging, random, statistics, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("augment_pipeline")


@dataclass
class AugConfig:
    brightness_range: tuple[int, int] = (-25, 25)
    contrast_range: tuple[float, float] = (0.85, 1.25)
    noise_sigma_max: float = 6.0
    max_mean_delta: float = 45.0
    seed: int = 42


def sample_image(size: int = 24, seed: int = 0) -> list[list[int]]:
    rng = random.Random(seed)
    img = [[rng.randint(0, 70) for _ in range(size)] for _ in range(size)]
    for y in range(size // 3, size * 2 // 3):
        for x in range(size // 3, size * 2 // 3):
            img[y][x] = 210
    return img


def make_sample(root: Path, n: int = 2) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        ep = {"episode_id": f"ep-{i:04d}", "task": "pick", "scene": "a",
              "action": [[0.01, 0.0, 0.0] for _ in range(5)],
              "image": sample_image(seed=i)}
        (root / f"ep-{i:04d}.json").write_text(
            json.dumps(ep, ensure_ascii=False), encoding="utf-8")


def _clip(v: int) -> int:
    return max(0, min(255, v))


def apply_op(img, name: str, cfg: AugConfig, rng: random.Random) -> list[list[int]]:
    if name == "brightness":
        d = rng.randint(*cfg.brightness_range)
        return [[_clip(v + d) for v in row] for row in img], {"delta": d}
    if name == "contrast":
        f = rng.uniform(*cfg.contrast_range)
        mean = sum(sum(r) for r in img) / (len(img) * len(img[0]))
        return [[_clip(int(mean + (v - mean) * f)) for v in row]
                for row in img], {"factor": round(f, 3)}
    if name == "noise":
        s = rng.uniform(0, cfg.noise_sigma_max)
        return [[_clip(v + int(rng.gauss(0, s))) for v in row]
                for row in img], {"sigma": round(s, 2)}
    raise ValueError("未知增强: " + name)


def mean_abs_delta(a, b) -> float:
    diffs = [abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb)]
    return sum(diffs) / len(diffs)


def main() -> int:
    ap = argparse.ArgumentParser(description="增强流水线(工程版)")
    ap.add_argument("--input-dir", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--augments-per-episode", type=int, default=6)
    ap.add_argument("--ops", nargs="*", default=["brightness", "contrast", "noise"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--make-sample", action="store_true")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    cfg = AugConfig(seed=args.seed)
    try:
        if args.make_sample and not any(args.input_dir.glob("*.json")):
            make_sample(args.input_dir)
            logger.info("生成样例: %s", args.input_dir)
        manifests, stats = [], {"count": 0, "over_boundary": 0}
        rng = random.Random(cfg.seed)
        for f in sorted(args.input_dir.glob("*.json")):
            ep = json.loads(f.read_text(encoding="utf-8"))
            img = ep["image"]
            for k in range(args.augments_per_episode):
                name = args.ops[k % len(args.ops)]
                out, params = apply_op(img, name, cfg, rng)
                delta = mean_abs_delta(img, out)
                over = delta > cfg.max_mean_delta
                stats["count"] += 1
                if over:
                    stats["over_boundary"] += 1
                manifests.append({"episode_id": ep["episode_id"],
                                  "variant": f"{ep['episode_id']}-a{k:03d}",
                                  "op": name, "params": params,
                                  "mean_abs_delta": round(delta, 2),
                                  "over_identity_boundary": over,
                                  "action_untouched": True})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "augment_manifest.json").write_text(
        json.dumps(manifests, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "augment_report.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成增强变体 {stats['count']} 个，越界 {stats['over_boundary']} 个")
    print(f"报告: {(args.out_dir / 'augment_report.json').resolve()}")
    return 0 if stats["over_boundary"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
