# -*- coding: utf-8 -*-
"""第23章 L2 工业工程版：世界模型可信度评测（状态误差+事件指标+衰减）。

输入 wm_eval.json: [{case, pred:[x..], gt:[x..], event_pred:bool, event_true:bool}]
输出：按 horizon 的 RMSE、事件准确率/精确率/召回率、末段衰减。

运行：
  python engineering_wm_eval.py --make-sample sample
  python engineering_wm_eval.py --input sample/wm_eval.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path

logger = logging.getLogger("wm_eval")


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    cases = [
        {"case": "c1", "pred": [0.4, 0.8, 1.1, 1.5, 1.9],
         "gt": [0.4, 0.8, 1.2, 1.6, 2.0], "event_pred": False,
         "event_true": False},
        {"case": "c2", "pred": [0.4, 0.9, 1.4, 1.9, 2.5],
         "gt": [0.4, 0.8, 1.2, 1.6, 2.0], "event_pred": True,
         "event_true": False},
    ]
    (root / "wm_eval.json").write_text(json.dumps(cases), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="世界模型评测(工程版)")
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
        cases = json.loads(args.input.read_text(encoding="utf-8"))
        n = max(len(c["gt"]) for c in cases)
        step_err = [0.0] * n
        counts = [0] * n
        tp = fp = fn = tn = 0
        for c in cases:
            for i, (p, g) in enumerate(zip(c["pred"], c["gt"])):
                step_err[i] += (p - g) ** 2
                counts[i] += 1
            ep, et = c["event_pred"], c["event_true"]
            tp += ep and et
            fp += ep and not et
            fn += (not ep) and et
            tn += (not ep) and (not et)
        rmse = [round(math.sqrt(step_err[i] / max(1, counts[i])), 4)
                for i in range(n)]
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        base = max(rmse[0], rmse[1], 1e-9)
        report = {"rmse_per_step": rmse,
                  "horizon_decay": round(rmse[-1] / base, 3),
                  "event": {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                            "accuracy": round((tp + tn) / max(1, tp + tn + fp + fn), 3),
                            "precision": round(prec, 3),
                            "recall": round(rec, 3)}}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "wm_eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RMSE 逐步:", rmse)
    print("事件指标:", report["event"])
    print("长时程衰减:", report["horizon_decay"],
          "（预测越远越差是正常，看斜率是否可用）")
    print(f"报告: {(args.out_dir / 'wm_eval_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
