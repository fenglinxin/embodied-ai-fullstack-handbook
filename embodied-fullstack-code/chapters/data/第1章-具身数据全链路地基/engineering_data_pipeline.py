# -*- coding: utf-8 -*-
"""第1章 L2 工业工程版：具身数据质量体检与门禁（纯标准库，可接流水线）。

能力：
  * 批量扫描 Episode JSON 目录（兼容第2/3章采集产物）
  * 五维质量打分：完整性/正确性/有效性/多样性(数据集级)/可复现性
  * 硬门禁：时间戳断裂、缺通道、观测-动作错位超限 -> 自动剔除清单
  * 输出 quality_report.json + 人读摘要，退出码可供 CI 使用

运行示例：
  python engineering_data_pipeline.py --data-dir ../demo_data \
      --out-dir ./out --config config.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("data_quality")


# ---------------------------------------------------------------- 配置
@dataclass
class QualityConfig:
    """质量门禁配置（默认值=工程起点；按第1章参数白皮书覆盖）。"""
    required_channels: list[str] = field(default_factory=lambda: ["rgb", "joint", "action"])
    weights: dict[str, float] = field(default_factory=lambda: {
        "completeness": 0.25, "correctness": 0.30, "effectiveness": 0.15,
        "diversity": 0.20, "reproducibility": 0.10})
    sync_gap_ms: float = 50.0          # 观测-动作最大错位
    black_ratio_max: float = 0.05      # 黑帧占比上限
    min_duration_s: float = 0.3        # 最短有效时长
    min_episodes: int = 1              # 数据目录最少 Episode 数
    hard_drop: bool = True             # 硬伤是否直接剔除
    # 多样性期望基数（数据集级打分用）
    expected_tasks: int = 1
    expected_scenes: int = 1
    expected_objects: int = 1


def load_config(path: Path | None) -> QualityConfig:
    """从 JSON 覆盖默认配置；校验权重和为 1。"""
    cfg = QualityConfig()
    if path:
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    total = sum(cfg.weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"权重之和必须为1，当前{total}")
    return cfg


# ---------------------------------------------------------------- 单条体检
def _monotonic_bad(ts: list[float]) -> int:
    return sum(1 for a, b in zip(ts, ts[1:]) if b <= a)


def _nearest_gap_ms(query: list[float], ref: list[float]) -> float:
    """query 每点在 ref 中最近邻的最大间隔（毫秒）。"""
    worst = 0.0
    j = 0
    for t in query:
        while j + 1 < len(ref) and abs(ref[j + 1] - t) <= abs(ref[j] - t):
            j += 1
        worst = max(worst, abs(ref[j] - t))
    return worst * 1000.0


def _span_s(ch: dict) -> float:
    ts = ch.get("ts") or []
    return (ts[-1] - ts[0]) if len(ts) >= 2 else 0.0


def inspect_episode(ep: dict, cfg: QualityConfig) -> dict[str, Any]:
    """返回单条 Episode 的分维度得分与硬/软问题。"""
    chans: dict = ep.get("channels") or {}
    issues_hard: list[str] = []
    issues_soft: list[str] = []

    # --- 完整性（25分制内部 0-1）
    present = [c for c in cfg.required_channels if c in chans]
    completeness = len(present) / max(1, len(cfg.required_channels))
    rgb = chans.get("rgb") or {}
    black = rgb.get("black") or []
    black_ratio = sum(black) / max(1, len(rgb.get("ts") or black or [1]))
    if black_ratio > cfg.black_ratio_max:
        completeness = min(completeness, 0.5)
        issues_soft.append(f"黑帧占比{black_ratio:.1%}")

    # --- 正确性（时间轴与同步）
    mono_bad = sum(_monotonic_bad((chans.get(c) or {}).get("ts") or []) for c in present)
    sync_ms = _nearest_gap_ms((rgb.get("ts") or []),
                              (chans.get("action") or {}).get("ts") or [])
    correctness = 1.0
    if mono_bad:
        correctness = 0.0
        issues_hard.append(f"时间戳非单调{mono_bad}处")
    if sync_ms > cfg.sync_gap_ms:
        correctness = min(correctness, 0.4)
        issues_hard.append(f"观测-动作错位{sync_ms:.0f}ms")

    # --- 有效性（任务是否真完成 + 时长可用）
    duration = max((_span_s(chans.get(c) or {}) for c in present), default=0.0)
    effectiveness = 1.0 if ep.get("success") is True else 0.0
    if duration < cfg.min_duration_s:
        effectiveness = min(effectiveness, 0.5)
        issues_soft.append(f"时长过短{duration:.2f}s")

    # --- 可复现性（元数据齐全性，缺字段按比例扣分）
    meta_fields = ("task", "scene", "language", "success")
    meta = ep
    repro_ok = sum(1 for k in meta_fields if meta.get(k) is not None)
    repro = repro_ok / len(meta_fields)

    # --- 汇总
    hard = bool(issues_hard)
    score = (0.25 * completeness + 0.30 * correctness + 0.15 * effectiveness
             + 0.30 * repro)
    if hard:
        score = min(score, 0.35)                 # 硬伤压制总分
    return {"episode_id": ep.get("episode_id"),
            "task": ep.get("task"), "scene": ep.get("scene"),
            "success": ep.get("success"), "duration_s": round(duration, 3),
            "completeness": round(completeness, 3),
            "correctness": round(correctness, 3),
            "effectiveness": round(effectiveness, 3),
            "reproducibility": round(repro, 3),
            "sync_gap_ms": round(sync_ms, 2),
            "issues_hard": issues_hard, "issues_soft": issues_soft,
            "verdict": "drop" if hard and cfg.hard_drop else "keep"}


# ---------------------------------------------------------------- 数据集级
def diversity_score(eps: list[dict], cfg: QualityConfig) -> float:
    """多样性：任务/场景/物体种类相对期望基数的覆盖度（0-1）。"""
    tasks = {e.get("task") for e in eps}
    scenes = {e.get("scene") for e in eps}
    objs = {e.get("object") for e in eps if e.get("object")}
    score = (min(1.0, len(tasks) / max(1, cfg.expected_tasks)) * 0.4
             + min(1.0, len(scenes) / max(1, cfg.expected_scenes)) * 0.4
             + min(1.0, len(objs) / max(1, cfg.expected_objects)) * 0.2)
    return round(score, 3)


def run_pipeline(data_dir: Path, cfg: QualityConfig) -> dict[str, Any]:
    """主流程：扫描 -> 单条体检 -> 数据集打分 -> 报告。"""
    eps_files = sorted(data_dir.glob("*.json"))
    if len(eps_files) < cfg.min_episodes:
        raise RuntimeError(f"Episode 不足 {cfg.min_episodes} 条: {data_dir}")
    episodes = [json.loads(f.read_text(encoding="utf-8")) for f in eps_files]
    logger.info("扫描到 %d 条 Episode", len(episodes))

    per = [inspect_episode(ep, cfg) for ep in episodes]
    keeps = [r for r in per if r["verdict"] == "keep"]
    drops = [r for r in per if r["verdict"] == "drop"]

    def avg(key: str) -> float:
        vals = [r[key] for r in keeps] if keeps else [0.0]
        return round(sum(vals) / len(vals), 3)

    avg_scores = {"completeness": avg("completeness"),
                  "correctness": avg("correctness"),
                  "effectiveness": avg("effectiveness"),
                  "reproducibility": avg("reproducibility")}
    div = diversity_score(episodes, cfg)
    weighted = (avg_scores["completeness"] * cfg.weights["completeness"]
                + avg_scores["correctness"] * cfg.weights["correctness"]
                + avg_scores["effectiveness"] * cfg.weights["effectiveness"]
                + div * cfg.weights["diversity"]
                + avg_scores["reproducibility"] * cfg.weights["reproducibility"])
    report = {
        "data_dir": str(data_dir),
        "episode_total": len(episodes),
        "episode_keep": len(keeps), "episode_drop": len(drops),
        "avg_dimension_scores": avg_scores,
        "diversity_score": div,
        "weighted_quality_score": round(weighted, 3),
        "quality_verdict": "pass" if weighted >= 0.8 and not drops else "review",
        "per_episode": per,
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="具身数据五维质量体检(工程版)")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        cfg = load_config(args.config)
        if not args.data_dir.is_dir():
            raise NotADirectoryError(f"数据目录不存在: {args.data_dir}")
        report = run_pipeline(args.data_dir, cfg)
    except Exception as exc:                     # 参数/环境错误统一出口
        logger.error("执行失败: %s", exc)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Episode 总数={report['episode_total']} "
          f"保留={report['episode_keep']} 剔除={report['episode_drop']}")
    print(f"加权质量分={report['weighted_quality_score']} "
          f"结论={report['quality_verdict']}")
    print(f"报告: {(args.out_dir / 'quality_report.json').resolve()}")
    return 0 if report["quality_verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
