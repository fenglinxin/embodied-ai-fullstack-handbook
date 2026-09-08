# -*- coding: utf-8 -*-
"""第39章 L2 工业工程版：逐层量化误差定位（先找到敏感层再混合精度）。"""
from __future__ import annotations

import argparse, json, math, logging, random, sys
from pathlib import Path

logger = logging.getLogger("layer_quant")

LAYERS = ["conv1", "conv2", "attention_q", "attention_out", "action_head"]


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1)
    data = {}
    for name in LAYERS:
        # 权重分布差异：attention_q 含离群值更敏感
        w = ([rng.gauss(0, 0.3) for _ in range(200)]
             + ([12.0, -9.0] if name in ("attention_q", "attention_out")
                else []))
        data[name] = {"weights": w, "act_scale": rng.uniform(0.5, 2.0)}
    (root / "layers.json").write_text(json.dumps(data), encoding="utf-8")


def quant_layer(w, bits=8):
    qmax = 2 ** (bits - 1) - 1
    scale = max(abs(x) for x in w) / qmax
    err = sum((x - round(x / scale) * scale) ** 2 for x in w)
    return math.sqrt(err / max(1, len(w)))


def main() -> int:
    ap = argparse.ArgumentParser(description="分层量化误差(L2)")
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
        rows = []
        for name, d in data.items():
            err = quant_layer(d["weights"])
            rows.append({"layer": name, "rmse": round(err, 4)})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: -r["rmse"])
    (args.out_dir / "layer_quant_report.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['layer']:<16} RMSE {r['rmse']:.4f}")
    print("敏感层 -> 进混合精度名单（先保这层）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
