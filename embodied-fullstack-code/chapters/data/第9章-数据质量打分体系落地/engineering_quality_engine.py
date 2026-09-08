# -*- coding: utf-8 -*-
"""第9章 L2 工业工程版：规则化五维质量引擎（配置权重/批量/门禁/人工校准）。"""
from __future__ import annotations

import argparse, json, logging, sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("quality_engine")

Rule = tuple[str, Callable[[dict], tuple[float, list[str]]]]


@dataclass
class QualityConfig:
    weights: dict[str, float] = field(default_factory=lambda: {
        "completeness": 0.25, "correctness": 0.30, "effectiveness": 0.15,
        "diversity": 0.20, "reproducibility": 0.10})
    gate_score: float = 0.75
    edge_low: float = 0.55
    edge_high: float = 0.85
    expected_tasks: int = 2
    expected_scenes: int = 3
    expected_objects: int = 2


def load_cfg(p: Path | None) -> QualityConfig:
    cfg = QualityConfig()
    if p:
        raw = json.loads(p.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    return cfg


def rules() -> list[Rule]:
    def r_complete(ep):
        score = 1.0
        reasons = []
        if float(ep.get("black_ratio", 0)) > 0.05:
            score, reasons = 0.4, ["黑帧超标"]
        if not ep.get("channels_ok", True):
            score, reasons = 0.0, ["通道缺失"]
        return score, reasons

    def r_correct(ep):
        if not ep.get("ts_ok", True):
            return 0.0, ["时间戳断裂"]
        if float(ep.get("empty_ratio", 0)) > 0.8:
            return 0.3, ["空动作>80%"]
        return 1.0, []

    def r_effect(ep):
        if ep.get("success") is True and ep.get("success_consistent", True):
            return 1.0, []
        return 0.3, ["成功标记存疑/未完成"]

    def r_repro(ep):
        fields = [bool(ep.get("has_language")), bool(ep.get("operator")),
                  bool(ep.get("calib"))]
        return sum(fields) / len(fields), []

    return [("completeness", r_complete), ("correctness", r_correct),
            ("effectiveness", r_effect), ("reproducibility", r_repro)]


def per_episode(ep: dict) -> dict:
    dims, issues = {}, []
    for name, fn in rules():
        score, why = fn(ep)
        dims[name] = round(float(score), 3)
        issues.extend(why)
    return {"episode_id": ep["episode_id"], "dims": dims, "issues": issues}


def diversity(eps: list[dict], cfg: QualityConfig) -> float:
    t = min(1.0, len({e.get("task") for e in eps}) / cfg.expected_tasks)
    s = min(1.0, len({e.get("scene") for e in eps}) / cfg.expected_scenes)
    o = min(1.0, len({e.get("object") for e in eps if e.get("object")})
            / cfg.expected_objects)
    return round(0.4 * t + 0.4 * s + 0.2 * o, 3)


def main() -> int:
    ap = argparse.ArgumentParser(description="五维质量引擎(工程版)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--review", type=Path, default=None,
                    help="人工评审JSON：[{episode_id, score_manual}]")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--config", type=Path)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        cfg = load_cfg(args.config)
        eps = json.loads(args.input.read_text(encoding="utf-8"))
        per = [per_episode(e) for e in eps]
        div = diversity(eps, cfg)
        manual = {}
        if args.review:
            for r in json.loads(args.review.read_text(encoding="utf-8")):
                manual[str(r["episode_id"])] = float(r["score_manual"])
        rows = []
        for e, p in zip(eps, per):
            auto_dim_total = (sum(p["dims"].get(k, 0) * cfg.weights[k]
                                  for k in ("completeness", "correctness",
                                            "effectiveness", "reproducibility"))
                              + div * cfg.weights["diversity"])
            total = round(auto_dim_total, 3)
            man = manual.get(str(e["episode_id"]))
            calib_gap = round(abs(man - total), 3) if man is not None else None
            zone = ("edge" if cfg.edge_low <= total <= cfg.edge_high else
                    ("low" if total < cfg.edge_low else "high"))
            rows.append({"episode_id": e["episode_id"], "dims": p["dims"],
                         "issues": p["issues"], "total": total,
                         "manual_score": man, "calib_gap": calib_gap,
                         "zone": zone})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    avg = round(sum(r["total"] for r in rows) / len(rows), 3)
    low = [r for r in rows if r["zone"] == "low"]
    report = {"avg_score": avg, "diversity": div,
              "edge_zone_count": sum(1 for r in rows if r["zone"] == "edge"),
              "low_zone": low,
              "calibration_gaps": [r for r in rows if r["calib_gap"] is not None
                                   and r["calib_gap"] > 0.15],
              "gate": "pass" if avg >= cfg.gate_score else "review",
              "per_episode": rows}
    (args.out_dir / "quality_engine_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"平均质量分 {avg} | 多样性 {div} | 门禁: {report['gate']}")
    print(f"边缘区 {report['edge_zone_count']} 条(建议人工全审) "
          f"低分区 {len(low)} 条")
    gaps = report["calibration_gaps"]
    if gaps:
        print("自动分与人工分偏差>0.15：", [g["episode_id"] for g in gaps])
    print(f"报告: {(args.out_dir / 'quality_engine_report.json').resolve()}")
    return 0 if report["gate"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
