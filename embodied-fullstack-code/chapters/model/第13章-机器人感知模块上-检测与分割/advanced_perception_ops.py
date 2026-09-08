# -*- coding: utf-8 -*-
"""第13章 L3 高阶优化版：真机感知稳定性体检（抖动/闪烁/EMA平滑）。

输入：连续帧检测结果（含 frame_id, class, bbox, conf）
输出：
  * 目标中心抖动统计（均值/中位/P95）
  * 闪烁（目标丢失帧数）
  * EMA 平滑前后抖动对比（工程技巧代码化）

运行：
  python engineering_detection_eval.py --make-sample sample
  python advanced_perception_ops.py --input sample/pred.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, statistics, sys
from pathlib import Path

logger = logging.getLogger("perception_ops")
EMA_ALPHA = 0.5


def center(b):
    x, y, w, h = b
    return (x + w / 2.0, y + h / 2.0)


def main() -> int:
    ap = argparse.ArgumentParser(description="感知稳定性体检(L3)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--target-class", default="mug")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        preds = json.loads(args.input.read_text(encoding="utf-8"))
        frames = {}
        for p in preds:
            if p.get("class") != args.target_class:
                continue
            frames.setdefault(p.get("frame_id", 0), []).append(p)
        ids = sorted(frames)
        if len(ids) < 3:
            raise RuntimeError("帧数不足，无法做稳定性分析")
        deltas = []
        prev = None
        missing = 0
        for fid in ids:
            # 每帧取置信度最高的框
            box = max(frames[fid], key=lambda p: p.get("conf", 0))["bbox"]
            c = center(box)
            if prev is not None:
                deltas.append(((c[0] - prev[0]) ** 2
                               + (c[1] - prev[1]) ** 2) ** 0.5)
            prev = c
        # 闪烁：相对上一帧存在性（模拟相邻帧 id）
        all_ids = set(ids)
        missing = sum(1 for i in range(ids[0], ids[-1] + 1) if i not in all_ids)
        # EMA 平滑对比：直接对中心序列平滑
        seq = [center(max(frames[f], key=lambda p: p.get("conf", 0))["bbox"])
               for f in ids]
        ema = []
        last = None
        for x, y in seq:
            if last is None:
                last = (x, y)
            else:
                last = (EMA_ALPHA * x + (1 - EMA_ALPHA) * last[0],
                        EMA_ALPHA * y + (1 - EMA_ALPHA) * last[1])
            ema.append(last)
        ema_d = [((ema[i][0] - ema[i - 1][0]) ** 2
                  + (ema[i][1] - ema[i - 1][1]) ** 2) ** 0.5
                 for i in range(1, len(ema))]
        def stats(v):
            return {"mean": round(statistics.mean(v), 3),
                    "p95": round(sorted(v)[min(len(v) - 1,
                                               int(len(v) * 0.95))], 3)}
        report = {"frames": len(ids), "missing_frames": missing,
                  "jitter_raw_px": stats(deltas),
                  "jitter_ema_px": stats(ema_d) if ema_d else None,
                  "advice": ("框跳变明显：启用跟踪/EMA(α≈0.5-0.7)"
                             if statistics.mean(deltas) > 5 else "抖动可接受")}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "perception_ops_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"帧数 {report['frames']} 丢失帧 {report['missing_frames']}")
    print("原始抖动:", report["jitter_raw_px"], "EMA后:",
          report["jitter_ema_px"])
    print("建议:", report["advice"])
    print(f"报告: {(args.out_dir / 'perception_ops_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
