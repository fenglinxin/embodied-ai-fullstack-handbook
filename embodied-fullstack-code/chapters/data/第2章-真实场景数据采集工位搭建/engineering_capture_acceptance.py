# -*- coding: utf-8 -*-
"""第2章 L2 工业工程版：采集会话验收门禁（可直接用于项目采集站）。

功能：
  * 读取采集记录（JSON 数组文件），兼容 demo 输出与真实采集日志
  * 验收门禁：总数/成功率/失败占比/场景覆盖/通道缺失率/操作者一致性
  * 失败原因归因统计（真实采集时由采集端写入 failure_reason）
  * 输出 session_report.json + 人读摘要，退出码 0=放行 1=拦截 2=配置错

运行：
  python demo_capture_acceptance.py --n 100 --out session.json
  python engineering_capture_acceptance.py --input session.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from collections import Counter

logger = logging.getLogger("capture_acceptance")


@dataclass
class GateConfig:
    min_episodes: int = 100
    min_success_rate: float = 0.90
    min_failure_ratio: float = 0.10
    min_scenes: int = 3
    min_operators: int = 1
    max_missing_channel_ratio: float = 0.02
    min_duration_s: float = 2.0


def load_config(p: Path | None) -> GateConfig:
    cfg = GateConfig()
    if p:
        raw = json.loads(p.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    return cfg


def validate_trials(trials: list[dict]) -> tuple[list[dict], list[str]]:
    """逐条校验字段并归一化，返回(有效记录, 问题清单)。"""
    ok, problems = [], []
    for i, t in enumerate(trials):
        try:
            rec = {
                "episode_id": str(t["episode_id"]),
                "scene": str(t.get("scene") or "unknown"),
                "operator": str(t.get("operator") or "unknown"),
                "success": bool(t.get("success")),
                "duration_s": float(t.get("duration_s") or 0.0),
                "channels_ok": bool(t.get("channels_ok", True)),
                "failure_reason": t.get("failure_reason") or "",
            }
            ok.append(rec)
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"第{i + 1}条字段非法: {exc}")
    return ok, problems


def evaluate(trials: list[dict], cfg: GateConfig) -> dict[str, Any]:
    n = len(trials)
    succ = [t for t in trials if t["success"]]
    fail = [t for t in trials if not t["success"]]
    scenes = {t["scene"] for t in trials}
    ops = {t["operator"] for t in trials}
    bad_ch = [t for t in trials if not t["channels_ok"]]
    short = [t for t in trials if t["duration_s"] < cfg.min_duration_s]

    success_rate = len(succ) / max(1, n)
    failure_ratio = len(fail) / max(1, n)
    checks = {
        "总数": {"pass": n >= cfg.min_episodes,
                 "value": n, "need": f">={cfg.min_episodes}"},
        "成功率": {"pass": success_rate >= cfg.min_success_rate,
                   "value": round(success_rate, 4),
                   "need": f">={cfg.min_success_rate}"},
        "失败样本占比": {"pass": failure_ratio >= cfg.min_failure_ratio,
                     "value": round(failure_ratio, 4),
                     "need": f">={cfg.min_failure_ratio}"},
        "场景覆盖数": {"pass": len(scenes) >= cfg.min_scenes,
                   "value": len(scenes), "need": f">={cfg.min_scenes}"},
        "操作者数": {"pass": len(ops) >= cfg.min_operators,
                 "value": len(ops), "need": f">={cfg.min_operators}"},
        "通道缺失率": {"pass": len(bad_ch) / max(1, n) <= cfg.max_missing_channel_ratio,
                   "value": round(len(bad_ch) / max(1, n), 4),
                   "need": f"<={cfg.max_missing_channel_ratio}"},
        "短时长条数": {"pass": len(short) == 0,
                   "value": len(short), "need": "0"},
    }
    reasons = Counter(t["failure_reason"] or "未填写" for t in fail)
    return {"total": n, "success": len(succ), "failure": len(fail),
            "success_rate": round(success_rate, 4),
            "failure_ratio": round(failure_ratio, 4),
            "scenes": sorted(scenes), "scene_count": len(scenes),
            "operators": sorted(ops), "operator_count": len(ops),
            "missing_channel_count": len(bad_ch),
            "short_duration_count": len(short),
            "failure_reasons": dict(reasons.most_common()),
            "checks": checks,
            "pass_all": all(c["pass"] for c in checks.values())}


def main() -> int:
    ap = argparse.ArgumentParser(description="采集会话验收门禁(工程版)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--config", type=Path)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        cfg = load_config(args.config)
        if not args.input.is_file():
            raise FileNotFoundError(f"输入文件不存在: {args.input}")
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("输入 JSON 必须为数组（Trial 记录列表）")
        trials, problems = validate_trials(raw)
        if len(trials) == 0:
            raise RuntimeError(f"无有效记录（问题 {len(problems)} 条）")
        report = evaluate(trials, cfg)
        report["schema_problems"] = problems
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "session_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"有效记录={report['total']} 成功={report['success']} "
          f"失败={report['failure']} 场景={report['scene_count']} "
          f"操作者={report['operator_count']}")
    for name, c in report["checks"].items():
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {name}: "
              f"{c['value']} (需{c['need']})")
    print("失败原因:", report["failure_reasons"])
    print("验收结论:", "PASS-可规模化采集" if report["pass_all"] else "FAIL-先修复短板")
    print(f"报告: {(args.out_dir / 'session_report.json').resolve()}")
    return 0 if report["pass_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
