# -*- coding: utf-8 -*-
"""第16章 L2 工业工程版：轨迹预测评测（minADE/minFDE + CV基线）。

输入 predictions.json:
  [{"case":"case1","gt":[[x,y],...future], "history":[[x,y],...],
    "hypotheses":[{"traj":[[x,y],...], "prob":0.6}, ...]}]
指标：minADE/minFDE（对多假设取最优），并用 CV 基线做对比。

运行：
  python engineering_prediction_eval.py --make-sample sample
  python engineering_prediction_eval.py --input sample/predictions.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path

logger = logging.getLogger("pred_eval")


def cv_predict(history, n):
    dx = history[-1][0] - history[-2][0]
    dy = history[-1][1] - history[-2][1]
    return [[history[-1][0] + dx * i, history[-1][1] + dy * i]
            for i in range(1, n + 1)]


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    gt = [[0.1 * i, 0.0] for i in range(6)]
    h = [[0.0, 0.0], [0.1, 0.0]]
    hyp = [{"traj": gt, "prob": 0.9},
           {"traj": [[0.1 * i, 0.2 * i] for i in range(6)], "prob": 0.1}]
    (root / "predictions.json").write_text(json.dumps(
        [{"case": "c1", "history": h, "gt": gt, "hypotheses": hyp}]),
        encoding="utf-8")
    (root / "ego_path.json").write_text(json.dumps(
        [[0.1 * i, 0.1] for i in range(6)]), encoding="utf-8")
def main() -> int:
    ap = argparse.ArgumentParser(description="预测评测(工程版)")
    ap.add_argument("--input", type=Path)
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
        cases = json.loads(args.input.read_text(encoding="utf-8"))
        rows = []
        for c in cases:
            gt = c["gt"]
            n = len(gt)
            best_ade = best_fde = float("inf")
            for h in c["hypotheses"]:
                traj = h["traj"]
                ade = sum(math.dist(a, b) for a, b in zip(traj, gt)) / n
                fde = math.dist(traj[-1], gt[-1])
                best_ade = min(best_ade, ade)
                best_fde = min(best_fde, fde)
            cv = cv_predict(c["history"], n)
            cv_ade = sum(math.dist(a, b) for a, b in zip(cv, gt)) / n
            cv_fde = math.dist(cv[-1], gt[-1])
            rows.append({"case": c.get("case"), "minADE": round(best_ade, 3),
                         "minFDE": round(best_fde, 3),
                         "cv_ADE": round(cv_ade, 3),
                         "cv_FDE": round(cv_fde, 3),
                         "beats_cv": best_ade <= cv_ade})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {"per_case": rows,
              "avg_minADE": round(sum(r["minADE"] for r in rows) / len(rows), 3),
              "avg_cv_ADE": round(sum(r["cv_ADE"] for r in rows) / len(rows), 3)}
    (args.out_dir / "prediction_eval.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['case']}: minADE={r['minADE']} (CV={r['cv_ADE']}) "
              f"minFDE={r['minFDE']} beats_cv={r['beats_cv']}")
    print("升级判据：复杂模型必须显著赢过 CV 基线才部署。")
    print(f"报告: {(args.out_dir / 'prediction_eval.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
