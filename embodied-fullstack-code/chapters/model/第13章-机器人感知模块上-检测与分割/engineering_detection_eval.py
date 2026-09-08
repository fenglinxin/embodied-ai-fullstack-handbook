# -*- coding: utf-8 -*-
"""第13章 L2 工业工程版：检测评测（mAP/P/R/F1 + 延迟统计）。

输入：ground_truth.json / predictions.json（YOLO 等任意检测器输出均可）：
  [{"image_id":0,"class":"mug","bbox":[x,y,w,h],"conf":0.9,
    "latency_ms":12.5}]
计算：IoU>=0.5 匹配，逐类 AP、mAP、P/R/F1；延迟 P50/P95。

运行：
  python engineering_detection_eval.py --make-sample sample
  python engineering_detection_eval.py --gt sample/gt.json \
      --pred sample/pred.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, statistics, sys
from pathlib import Path

logger = logging.getLogger("det_eval")
IOU_TH = 0.5


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    gt = [{"image_id": 0, "class": "mug", "bbox": [10, 10, 12, 12]},
          {"image_id": 0, "class": "mug", "bbox": [30, 30, 10, 10]},
          {"image_id": 1, "class": "box", "bbox": [20, 5, 8, 8]}]
    pred = [{"image_id": 0, "class": "mug", "bbox": [10, 10, 12, 12],
             "conf": 0.95, "latency_ms": 11.0},
            {"image_id": 0, "class": "mug", "bbox": [32, 31, 9, 9],
             "conf": 0.80, "latency_ms": 13.0},
            {"image_id": 1, "class": "mug", "bbox": [20, 5, 8, 8],
             "conf": 0.60, "latency_ms": 14.0}]
    (root / "gt.json").write_text(json.dumps(gt), encoding="utf-8")
    (root / "pred.json").write_text(json.dumps(pred), encoding="utf-8")


def iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / max(1e-9, union)


def main() -> int:
    ap = argparse.ArgumentParser(description="检测评测(工程版)")
    ap.add_argument("--gt", type=Path)
    ap.add_argument("--pred", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        gt = json.loads(args.gt.read_text(encoding="utf-8"))
        preds = json.loads(args.pred.read_text(encoding="utf-8"))
        classes = sorted({g["class"] for g in gt})
        per_class = {}
        for cls in classes:
            g_cls = [g for g in gt if g["class"] == cls]
            p_cls = sorted([p for p in preds if p["class"] == cls],
                           key=lambda p: -p.get("conf", 0))
            tp = fp = 0
            used = set()
            ap_sum, ap_n = 0.0, 0
            for rank, p in enumerate(p_cls, start=1):
                best = max(((i, iou(p["bbox"], g["bbox"]))
                            for i, g in enumerate(g_cls)
                            if i not in used), key=lambda t: t[1],
                           default=(-1, 0.0))
                if best[1] >= IOU_TH:
                    tp += 1; used.add(best[0])
                else:
                    fp += 1
                precision = tp / (tp + fp)
                ap_sum += precision
                ap_n += 1
            fn = len(g_cls) - len(used)
            p = tp / max(1, tp + fp)
            r = tp / max(1, tp + fn)
            per_class[cls] = {"tp": tp, "fp": fp, "fn": fn,
                              "precision": round(p, 3), "recall": round(r, 3),
                              "f1": round(2 * p * r / max(1e-9, p + r), 3),
                              "AP": round(ap_sum / max(1, ap_n), 3)}
        lat = [p.get("latency_ms", 0) for p in preds if "latency_ms" in p]
        report = {"per_class": per_class,
                  "mAP": round(sum(v["AP"] for v in per_class.values())
                               / max(1, len(per_class)), 3),
                  "latency_ms": {"p50": round(statistics.median(lat), 2),
                                 "p95": round(sorted(lat)[
                                     min(len(lat) - 1,
                                         int(len(lat) * 0.95))], 2)
                                 if lat else None}}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "detection_eval.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("mAP:", report["mAP"])
    for cls, m in per_class.items():
        print(f"  {cls}: AP={m['AP']} P={m['precision']} R={m['recall']} "
              f"F1={m['f1']} (TP{ m['tp']}/FP{m['fp']}/FN{m['fn']})")
    print("延迟ms:", report["latency_ms"])
    print(f"报告: {(args.out_dir / 'detection_eval.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
