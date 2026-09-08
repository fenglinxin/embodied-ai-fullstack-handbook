# -*- coding: utf-8 -*-
"""第3章 L3 高阶优化版：恒定延迟估计 + 抖动体检 + 自动补偿建议。

针对文章第7章进阶：不要相信纸面延迟，用互相关实测。
原理：把 joint 与 action 重采样到公共 100Hz 网格后做互相关，
估计 action 相对 joint 的整步延迟；再评估补偿后残余抖动。

运行：
  python demo_time_align.py --make-episodes demo_data
  python advanced_delay_estimator.py --data-dir demo_data --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, math, sys, statistics
from pathlib import Path
from typing import Any

logger = logging.getLogger("delay_est")


def _grid_uniform(eps: list[float], fps: float = 100.0) -> list[float]:
    t0, t1 = min(eps), max(eps)
    return [t0 + i / fps for i in range(int((t1 - t0) * fps) + 1)]


def _sample(ch: dict, ts: list[float]) -> list[float]:
    """在 ts 网格上线性插值（标量）。"""
    raw_ts, vals = ch["ts"], ch["values"]
    out = []
    n = len(raw_ts)
    for t in ts:
        if t <= raw_ts[0]: out.append(vals[0]); continue
        if t >= raw_ts[-1]: out.append(vals[-1]); continue
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if raw_ts[mid] <= t: lo = mid
            else: hi = mid
        w = (t - raw_ts[lo]) / max(1e-9, raw_ts[hi] - raw_ts[lo])
        out.append(vals[lo] * (1 - w) + vals[hi] * w)
    return out


def xcorr_delay(a: list[float], b: list[float], max_lag: int = 30) -> dict[str, Any]:
    """估计 b 相对 a 的延迟（正= b 滞后）。归一化互相关，返回整步滞后。"""
    n = len(a)
    best_lag, best_score = 0, -1e18
    for lag in range(-max_lag, max_lag + 1):
        score = 0.0
        cnt = 0
        for i in range(n):
            j = i + lag
            if 0 <= j < n:
                score += a[i] * b[j]; cnt += 1
        if cnt:
            score /= cnt
            if score > best_score:
                best_score, best_lag = score, lag
    return {"lag_steps": best_lag, "lag_ms": round(best_lag * 10.0, 1),
            "score": round(best_score, 4)}


def gap_stats(a_ts: list[float], b_ts: list[float]) -> dict[str, float]:
    """公共网格上最近邻间隔统计（毫秒），用于抖动体检。"""
    diffs = []
    for t in a_ts:
        diffs.append(min(abs(t - x) for x in b_ts) * 1000.0)
    return {"mean_ms": round(statistics.mean(diffs), 3),
            "max_ms": round(max(diffs), 3),
            "std_ms": round(statistics.stdev(diffs) if len(diffs) > 1 else 0.0, 3)}


def analyze(ep: dict, fps: float = 100.0) -> dict[str, Any]:
    chans: dict = ep.get("channels") or {}
    joint, action = chans.get("joint"), chans.get("action")
    if not joint or not action:
        raise ValueError("缺少 joint/action 通道")
    grid = _grid_uniform(joint["ts"], fps)
    ja, ac = _sample(joint, grid), _sample(action, grid)
    est = xcorr_delay(ja, ac)
    # 补偿建议：如果 action 滞后 lag>0，应把 action 时间轴前移 lag*10ms
    delay_s = est["lag_steps"] / fps
    corr_action_ts = [round(t - delay_s, 6) for t in action["ts"]]
    before = gap_stats(grid, action["ts"])
    after = gap_stats(grid, corr_action_ts)
    return {"episode_id": ep.get("episode_id"),
            "estimate": est,
            "corrected_ts_shift_s": round(delay_s, 6),
            "gap_before_ms": before, "gap_after_ms": after,
            "verdict": "需要补偿" if abs(est["lag_steps"]) >= 2 else "无需补偿"}


def main() -> int:
    ap = argparse.ArgumentParser(description="恒定延迟估计与抖动体检(L3)")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--fps", type=float, default=100.0)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    files = sorted(args.data_dir.glob("*.json"))
    if not files:
        logger.error("无 Episode JSON: %s", args.data_dir); return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    results, failed = [], []
    for f in files:
        ep = json.loads(f.read_text(encoding="utf-8"))
        try:
            results.append(analyze(ep, args.fps))
        except Exception as exc:
            logger.warning("跳过 %s: %s", f.name, exc)
            failed.append({"file": f.name, "reason": str(exc)})
    rep = {"per_episode": results, "failed": failed,
           "need_compensation": sum(1 for r in results if r["verdict"] == "需要补偿")}
    (args.out_dir / "delay_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['episode_id']}: 估计延迟 {r['estimate']['lag_ms']}ms "
              f"-> {r['verdict']} (补偿后max gap "
              f"{r['gap_after_ms']['max_ms']}ms)")
    print(f"需补偿: {rep['need_compensation']}/{len(results)}")
    print(f"报告: {(args.out_dir / 'delay_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
