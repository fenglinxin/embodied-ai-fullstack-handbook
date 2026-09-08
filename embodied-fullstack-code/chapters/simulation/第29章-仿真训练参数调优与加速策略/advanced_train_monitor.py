# -*- coding: utf-8 -*-
"""第29章 L3 高阶优化版：训练监控与 15 分钟早期失败检测。"""
from __future__ import annotations

import argparse, json, logging, statistics, sys
from pathlib import Path

logger = logging.getLogger("train_monitor")


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    def gen(good: bool):
        rows = []
        for i in range(60):
            rows.append({
                "step": i * 10_000,
                "reward": round(0.2 + (0.8 if good else 0.01) *
                                (1 - (1 - i / 60) ** 2), 3),
                "entropy": round(max(0.005, 0.5 - 0.4 * i / 60)
                                 if good else 0.001, 4),
                "success": round(0.1 + 0.85 * i / 60 if good else 0.05, 3)})
        return rows
    (root / "healthy.json").write_text(json.dumps(gen(True)), encoding="utf-8")
    (root / "flat.json").write_text(json.dumps(gen(False)), encoding="utf-8")


def analyze(rows):
    n = len(rows)
    if n < 10:
        return {"alerts": ["样本不足"], "verdict": "unknown"}
    tail = rows[-max(2, n // 10):]
    head = rows[:max(2, n // 10)]
    reward_gain = statistics.mean(r["reward"] for r in tail) -         statistics.mean(r["reward"] for r in head)
    min_entropy = min(r["entropy"] for r in tail)
    succ_last = rows[-1]["success"]
    alerts = []
    if reward_gain < 0.02:
        alerts.append("reward 长期平线(15分钟无进展)")
    if min_entropy < 0.01:
        alerts.append("entropy 崩塌到0(策略过早确定)")
    if succ_last < 0.05:
        alerts.append("成功率≈0(任务不可学/评测bug)")
    return {"reward_gain": round(reward_gain, 3),
            "min_entropy_tail": min_entropy, "final_success": succ_last,
            "alerts": alerts,
            "verdict": "early-fail" if len(alerts) >= 2 else
                       ("warning" if alerts else "healthy")}


def main() -> int:
    ap = argparse.ArgumentParser(description="训练监控(L3)")
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
        rows = json.loads(args.input.read_text(encoding="utf-8"))
        rep = analyze(rows)
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "monitor_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"reward增益 {rep['reward_gain']} 尾熵 {rep['min_entropy_tail']} "
          f"末成功率 {rep['final_success']}")
    for a in rep["alerts"]:
        print("  [!]", a)
    print("判定:", rep["verdict"])
    print(f"报告: {(args.out_dir / 'monitor_report.json').resolve()}")
    return 1 if rep["verdict"] == "early-fail" else 0


if __name__ == "__main__":
    sys.exit(main())
