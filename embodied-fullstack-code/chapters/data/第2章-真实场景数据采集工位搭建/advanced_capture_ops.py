# -*- coding: utf-8 -*-
"""第2章 L3 高阶优化版：采集运营质量分析（多操作者一致性/漂移/覆盖）。

解决文章进阶优化中的三个量产问题：
  1) 多操作者风格差异 -> 一致性监测（成功率极差）
  2) "采着采着就松了"  -> 时间漂移分析（滚动窗口成功率趋势）
  3) 采集矩阵偏科       -> 场景×操作者覆盖矩阵

运行：
  python advanced_capture_ops.py --input session.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("capture_ops")

# 工程经验阈值（可按项目覆盖）
CONSISTENCY_MAX_GAP = 0.15    # 操作者成功率最大允许极差
DRIFT_WINDOW = 20             # 漂移检测窗口
DRIFT_MAX_DROP = 0.10         # 尾窗相对头窗最大允许下降


def load_trials(p: Path) -> list[dict]:
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("输入必须为 Trial JSON 数组")
    return [t for t in raw if isinstance(t, dict) and "episode_id" in t]


def operator_consistency(trials: list[dict]) -> dict[str, Any]:
    """每个操作者的成功率与一致性告警。"""
    stats: dict[str, list[bool]] = defaultdict(list)
    for t in trials:
        stats[t.get("operator") or "unknown"].append(bool(t.get("success")))
    per = {op: round(sum(v) / len(v), 4) for op, v in stats.items()}
    gap = (max(per.values()) - min(per.values())) if len(per) > 1 else 0.0
    return {"per_operator_success": per, "max_gap": round(gap, 4),
            "alert": gap > CONSISTENCY_MAX_GAP,
            "suggestion": "安排低分操作者重新通过20条一致性测试"
                          if gap > CONSISTENCY_MAX_GAP else "操作者一致性正常"}


def drift_analysis(trials: list[dict]) -> dict[str, Any]:
    """按采集顺序切窗口，观察成功率是否随时间下滑（疲劳/流程松懈）。"""
    ordered = [bool(t.get("success")) for t in trials]
    n = len(ordered)
    if n < DRIFT_WINDOW * 2:
        return {"windows": [], "alert": False,
                "suggestion": "样本不足，暂不评估漂移"}
    wins: list[dict[str, Any]] = []
    for start in range(0, n - DRIFT_WINDOW + 1, DRIFT_WINDOW):
        chunk = ordered[start:start + DRIFT_WINDOW]
        wins.append({"start": start, "end": start + len(chunk),
                     "success_rate": round(sum(chunk) / len(chunk), 4)})
    drop = wins[0]["success_rate"] - wins[-1]["success_rate"]
    return {"windows": wins, "head_tail_drop": round(drop, 4),
            "alert": drop > DRIFT_MAX_DROP,
            "suggestion": "检查后半程是否出现疲劳/操作SOP走样，安排轮换与抽检"
                          if drop > DRIFT_MAX_DROP else "无显著漂移"}


def coverage_matrix(trials: list[dict], min_per_cell: int = 10) -> dict[str, Any]:
    """场景×操作者矩阵与欠覆盖告警。"""
    matrix: dict[tuple[str, str], int] = defaultdict(int)
    for t in trials:
        matrix[(t.get("scene") or "?", t.get("operator") or "?")] += 1
    under = [{"scene": s, "operator": o, "count": c}
             for (s, o), c in sorted(matrix.items()) if c < min_per_cell]
    return {"cells": [{"scene": s, "operator": o, "count": c}
                      for (s, o), c in sorted(matrix.items())],
            "under_covered": under, "min_per_cell": min_per_cell}


def main() -> int:
    ap = argparse.ArgumentParser(description="采集运营质量分析(L3)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        trials = load_trials(args.input)
        if not trials:
            raise RuntimeError("输入为空")
        rep = {"consistency": operator_consistency(trials),
               "drift": drift_analysis(trials),
               "coverage": coverage_matrix(trials)}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "capture_ops_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("操作者成功率:", rep["consistency"]["per_operator_success"],
          "告警:", rep["consistency"]["alert"])
    print("漂移头尾差:", rep["drift"].get("head_tail_drop"),
          "告警:", rep["drift"]["alert"])
    print("覆盖欠佳格:", len(rep["coverage"]["under_covered"]))
    print(f"报告: {(args.out_dir / 'capture_ops_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
