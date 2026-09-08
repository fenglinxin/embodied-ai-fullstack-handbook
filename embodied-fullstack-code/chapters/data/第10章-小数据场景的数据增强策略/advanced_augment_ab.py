# -*- coding: utf-8 -*-
"""第10章 L3 高阶优化版：增强 A/B 评测骨架（代理指标，可接真模型）。

每个策略生成变体后计算两个代理指标：
  invariance = 1 - 平均像素变化/255   （守真）
  diversity  = 变体间平均像素标准差   （增量信息）
score = w*invariance + (1-w)*diversity；与 baseline(不增强) 对比。
把 run_model_eval() 换成你的成功率评测即可做真 A/B（文章第6步）。

运行：
  python engineering_augment_pipeline.py --input-dir sample --out-dir out --make-sample
  python advanced_augment_ab.py --input-dir sample --out-dir out
"""
from __future__ import annotations

import argparse, json, random, statistics, sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ABConfig:
    variants_per_strategy: int = 5
    w_invariance: float = 0.6      # 守真权重
    seed: int = 1


def mean_px(img) -> float:
    return statistics.mean(v for row in img for v in row)


def generate(img, op: str, rng: random.Random):
    """按策略生成一张变体（与 L2 同规则，独立实现便于 A/B 对比）。"""
    size = len(img)
    if op == "brightness":
        d = rng.randint(-25, 25)
        return [[max(0, min(255, v + d)) for v in row] for row in img]
    if op == "contrast":
        f = rng.uniform(0.85, 1.25)
        m = mean_px(img)
        return [[max(0, min(255, int(m + (v - m) * f))) for v in row]
                for row in img]
    if op == "noise":
        s = rng.uniform(0, 6)
        return [[max(0, min(255, v + int(rng.gauss(0, s)))) for v in row]
                for row in img]
    if op == "mix":
        out = img
        for sub in ("brightness", "contrast", "noise"):
            out = generate(out, sub, rng)
        return out
    raise ValueError(op)


def evaluate_strategy(images, op: str, cfg: ABConfig) -> dict:
    variants_per_episode = []
    for img in images:
        rng = random.Random(cfg.seed)
        outs = [generate(img, op, rng) for _ in range(cfg.variants_per_strategy)]
        inv = []
        for out in outs:
            diffs = [abs(x - y) for ra, rb in zip(img, out) for x, y in zip(ra, rb)]
            inv.append(1.0 - (sum(diffs) / len(diffs)) / 255.0)
        # 多样性：逐像素跨变体标准差均值
        divs = []
        for y in range(len(img)):
            for x in range(len(img[0])):
                vals = [o[y][x] for o in outs]
                divs.append(statistics.pstdev(vals))
        variants_per_episode.append({
            "invariance": statistics.mean(inv),
            "diversity": statistics.mean(divs)})
    inv_mean = statistics.mean(v["invariance"] for v in variants_per_episode)
    div_mean = statistics.mean(v["diversity"] for v in variants_per_episode)
    score = cfg.w_invariance * inv_mean + (1 - cfg.w_invariance) * div_mean / 80.0
    return {"strategy": op, "invariance": round(inv_mean, 4),
            "diversity": round(div_mean, 2),
            "score": round(score, 4)}


def run_model_eval(_rows) -> float:
    """A/B 接入点：换成你的黄金评测集成功率；这里返回占位 0.5。"""
    return 0.5


def main() -> int:
    ap = argparse.ArgumentParser(description="增强A/B评测(L3)")
    ap.add_argument("--input-dir", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    try:
        images = []
        for f in sorted(args.input_dir.glob("*.json")):
            ep = json.loads(f.read_text(encoding="utf-8"))
            images.append(ep["image"])
        if not images:
            raise RuntimeError("输入为空")
        cfg = ABConfig()
        rows = [evaluate_strategy(images, op, cfg)
                for op in ("brightness", "contrast", "noise", "mix")]
        # baseline 无增强：invariance=1, diversity=0
        rows.insert(0, {"strategy": "baseline_none", "invariance": 1.0,
                        "diversity": 0.0, "score": cfg.w_invariance})
        rows.sort(key=lambda r: -r["score"])
        best = rows[0]
        # 真模型评测接入点（此处占位，跑通骨架）
        model_gain = run_model_eval(rows)
        report = {"rows": rows, "best": best["strategy"],
                  "model_gain_placeholder": model_gain,
                  "advice": ("优先保留 " + best["strategy"] +
                             "（代理分最高；最终以真模型评测为准）")}
    except Exception as exc:
        print("执行失败:", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "augment_ab_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['strategy']:<14} invariance={r['invariance']:.3f} "
              f"diversity={r['diversity']:.1f} score={r['score']:.4f}")
    print("建议:", report["advice"])
    print(f"报告: {(args.out_dir / 'augment_ab_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
