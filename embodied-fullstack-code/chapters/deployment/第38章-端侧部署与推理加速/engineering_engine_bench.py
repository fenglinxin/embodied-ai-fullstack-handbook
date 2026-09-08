# -*- coding: utf-8 -*-
"""第38章 L2 工业工程版：推理引擎基准评测（延迟/显存/精度对照）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("engine_bench")

ENGINES = {
    "pytorch_fp32": {"p50_ms": 48.0, "p99_ms": 62.0, "vram_gb": 2.4,
                     "acc": 0.990},
    "onnx_fp16": {"p50_ms": 31.0, "p99_ms": 40.0, "vram_gb": 1.4,
                  "acc": 0.989},
    "tensorrt_fp16": {"p50_ms": 18.0, "p99_ms": 24.0, "vram_gb": 1.1,
                      "acc": 0.988},
    "tensorrt_int8": {"p50_ms": 11.0, "p99_ms": 16.0, "vram_gb": 0.6,
                      "acc": 0.970},
}


def main() -> int:
    ap = argparse.ArgumentParser(description="引擎基准(工程版)")
    ap.add_argument("--max-p99", type=float, default=20.0)
    ap.add_argument("--max-vram", type=float, default=1.2)
    ap.add_argument("--min-acc", type=float, default=0.97)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    rows = []
    for name, m in ENGINES.items():
        ok = (m["p99_ms"] <= args.max_p99 and m["vram_gb"] <= args.max_vram
              and m["acc"] >= args.min_acc)
        rows.append({"engine": name, **m, "meets_budget": ok})
    rows.sort(key=lambda r: r["p50_ms"])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "engine_bench.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['engine']:<16} p50={r['p50_ms']:>4}ms "
              f"p99={r['p99_ms']:>4}ms vram={r['vram_gb']}GB "
              f"acc={r['acc']:.3f} [{'PASS' if r['meets_budget'] else 'FAIL'}]")
    best = next((r for r in rows if r["meets_budget"]), None)
    print("推荐:", best["engine"] if best else "预算内无满足项，需量化/蒸馏")
    return 0 if best else 1


if __name__ == "__main__":
    sys.exit(main())
