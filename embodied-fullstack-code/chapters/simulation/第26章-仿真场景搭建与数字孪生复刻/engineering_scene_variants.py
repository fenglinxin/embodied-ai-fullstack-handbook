# -*- coding: utf-8 -*-
"""第26章 L2 工业工程版：程序化场景变体生成器（可复现随机）。"""
from __future__ import annotations

import argparse, hashlib, itertools, json, logging, random, sys
from pathlib import Path

logger = logging.getLogger("scene_gen")

SPACE = {"objects": ["mug_red", "box_blue", "can"],
         "positions": ["left", "center", "right"],
         "light": ["normal", "shadow", "bright"],
         "table": ["wood", "dark"]}


def make_variants(n):
    rng = random.Random(0)
    keys = list(SPACE)
    grid = list(itertools.product(*(SPACE[k] for k in keys)))
    out = []
    for i in range(n):
        combo = grid[i % len(grid)]
        params = dict(zip(keys, combo))
        # 位置加微扰（种子记录保证可复现）
        jitter = {"seed": i, "dx": round(rng.uniform(-0.02, 0.02), 3),
                  "dy": round(rng.uniform(-0.02, 0.02), 3)}
        scene_hash = hashlib.sha1(
            json.dumps({**params, **jitter}, sort_keys=True).encode()
        ).hexdigest()[:12]
        out.append({"variant_id": f"v{i:04d}", "params": params,
                    "jitter": jitter, "scene_hash": scene_hash})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="场景变体生成(工程版)")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        variants = make_variants(args.n)
        uniq = len({v["scene_hash"] for v in variants})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "variants.json").write_text(
        json.dumps(variants, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成 {len(variants)} 个变体，唯一场景 {uniq} 个")
    for v in variants[:3]:
        print("  ", v["variant_id"], v["params"], v["scene_hash"])
    print("种子已记录 -> 可复现的随机才是好随机（数据卡可追溯）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
