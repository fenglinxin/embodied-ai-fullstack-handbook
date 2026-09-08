# -*- coding: utf-8 -*-
"""第22章 L2 工业工程版：VLA 训练样本适配器（JSONL 生成）。

输入 Episode（instruction/actions/场景字段）-> 输出模型样本：
  {"text": 指令模板, "action_tokens":[...], "scene":..., "episode":...}
按场景哈希切 train/val（防泄漏）；动作归一化缩放可配。

运行：
  python engineering_vla_adapter.py --make-sample sample
  python engineering_vla_adapter.py --input-dir sample --out-dir out \
      --chunk-size 5 --stride 2
"""
from __future__ import annotations

import argparse, hashlib, json, logging, sys
from pathlib import Path

logger = logging.getLogger("vla_adapter")
PROMPT = "Human: 请执行：{instruction}\nAssistant: 动作:"


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    eps = [
        {"episode_id": "ep-0001", "scene": "kitchen_a",
         "instruction": "把红色马克杯放到托盘",
         "actions": [[0.02 * i, 0.0, 0.0, 0] for i in range(8)]},
        {"episode_id": "ep-0002", "scene": "kitchen_b",
         "instruction": "抓取蓝色方块",
         "actions": [[0.0, 0.02 * i, 0.0, 1] for i in range(8)]},
    ]
    for e in eps:
        (root / (e["episode_id"] + ".json")).write_text(
            json.dumps(e, ensure_ascii=False), encoding="utf-8")


def normalize(acts, scale=100.0):
    return [[round(v * scale) for v in a] for a in acts]


def main() -> int:
    ap = argparse.ArgumentParser(description="VLA 适配器(工程版)")
    ap.add_argument("--input-dir", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--chunk-size", type=int, default=5)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--scale", type=float, default=100.0)
    ap.add_argument("--val-ratio", type=float, default=0.2)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        if args.chunk_size <= 0 or args.stride <= 0:
            raise ValueError("chunk/stride 必须>0")
        samples = []
        for f in sorted(args.input_dir.glob("*.json")):
            ep = json.loads(f.read_text(encoding="utf-8"))
            acts = normalize(ep["actions"], args.scale)
            text = PROMPT.format(instruction=ep["instruction"])
            for start in range(0, len(acts) - args.chunk_size + 1, args.stride):
                chunk = acts[start:start + args.chunk_size]
                samples.append({"text": text, "action_tokens": chunk,
                                "scene": ep.get("scene", "?"),
                                "episode": ep["episode_id"]})
        if not samples:
            raise RuntimeError("无样本（动作长度不足 chunk？）")
        train, val = [], []
        for s in samples:
            h = int(hashlib.sha1(s["scene"].encode()).hexdigest(), 16)
            (val if (h % 100) / 100.0 < args.val_ratio else train).append(s)
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    nl = chr(10)
    (args.out_dir / "train.jsonl").write_text(
        nl.join(json.dumps(s, ensure_ascii=False) for s in train), encoding="utf-8")
    (args.out_dir / "val.jsonl").write_text(
        nl.join(json.dumps(s, ensure_ascii=False) for s in val), encoding="utf-8")
    rep = {"samples": len(samples), "train": len(train), "val": len(val),
           "chunk_size": args.chunk_size, "prompt": PROMPT}
    (args.out_dir / "adapter_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("样本 " + str(len(samples)) + ": train=" + str(len(train)) + " val=" + str(len(val)) + " (场景级切分, 防泄漏)")
    print("输出: " + str((args.out_dir / "train.jsonl").resolve()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
