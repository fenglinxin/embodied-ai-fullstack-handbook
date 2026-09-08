# -*- coding: utf-8 -*-
"""第3章 L2 工业工程版：多通道时间对齐/重采样流水线（纯标准库）。

能力：
  * 扫描 Episode 目录，识别通道 ts+values（支持标量与向量值）
  * 以 master 通道时间轴为基准，对每个从通道做 nearest/linear 重采样
  * 对齐前质量体检：时间戳单调、最大/平均时间间隔
  * 输出对齐后 JSON + 对齐报告（接入第1章数据包之前使用）

运行：
  python demo_time_align.py --make-data demo_aligned.json   # 生成单通道演示(仅L1用)
  python engineering_time_align.py --data-dir ./demo_data --out-dir ./out
"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("time_align")
MONOTONIC_TOL = 1e-9


def _monotonic(ts: list[float]) -> bool:
    return all(b - a > MONOTONIC_TOL for a, b in zip(ts, ts[1:]))


def _is_vector(values: list) -> bool:
    return bool(values) and isinstance(values[0], (list, tuple))


def _lerp(a: list[float] | float, b: list[float] | float, w: float):
    if isinstance(a, (list, tuple)):
        return [x * (1 - w) + y * w for x, y in zip(a, b)]
    return a * (1 - w) + b * w


def resample(ch: dict, target_ts: list[float], method: str) -> list:
    """把 ch 重采样到 target_ts；method: nearest | linear。"""
    ts, vals = ch["ts"], ch["values"]
    out = []
    n = len(ts)
    for t in target_ts:
        if t <= ts[0]:
            out.append(vals[0]); continue
        if t >= ts[-1]:
            out.append(vals[-1]); continue
        # 找 t 左侧最近索引（二分）
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if ts[mid] <= t: lo = mid
            else: hi = mid
        if method == "nearest":
            out.append(vals[lo] if t - ts[lo] <= ts[hi] - t else vals[hi])
        else:
            w = (t - ts[lo]) / max(1e-9, ts[hi] - ts[lo])
            out.append(_lerp(vals[lo], vals[hi], w))
    return out


def align_episode(ep: dict, master: str, method: str) -> dict[str, Any]:
    chans: dict = ep.get("channels") or {}
    if master not in chans:
        raise ValueError(f"缺少主通道 {master}")
    master_ch = chans[master]
    if not _monotonic(master_ch["ts"]):
        raise ValueError(f"{master} 时间戳非单调，先修采集端")
    target_ts = master_ch["ts"]
    aligned: dict[str, Any] = {}
    gaps: dict[str, dict[str, float]] = {}
    for name, ch in chans.items():
        if name == master:
            aligned[name] = master_ch["values"]; continue
        if not _monotonic(ch["ts"]):
            raise ValueError(f"{name} 时间戳非单调")
        aligned[name] = resample(ch, target_ts, method)
        # 对齐前通道相对主通道的时间间隔统计（毫秒）
        diffs = []
        for t in target_ts:
            d = min(abs(t - x) for x in ch["ts"])
            diffs.append(d * 1000.0)
        gaps[name] = {"mean_ms": round(sum(diffs) / max(1, len(diffs)), 2),
                      "max_ms": round(max(diffs), 2)}
    return {"episode_id": ep.get("episode_id"), "master": master,
            "method": method, "master_ts": target_ts,
            "aligned": aligned, "gap_stats_ms": gaps}


def main() -> int:
    ap = argparse.ArgumentParser(description="多通道时间对齐(工程版)")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--master", default="joint")
    ap.add_argument("--method", choices=["nearest", "linear"], default="linear")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    files = sorted(args.data_dir.glob("*.json"))
    if not files:
        logger.error("目录无 JSON: %s", args.data_dir)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    failed = []
    for f in files:
        ep = json.loads(f.read_text(encoding="utf-8"))
        try:
            res = align_episode(ep, args.master, args.method)
        except Exception as exc:
            logger.warning("跳过 %s: %s", f.name, exc)
            failed.append({"file": f.name, "reason": str(exc)})
            continue
        out_f = args.out_dir / f"aligned_{res['episode_id']}.json"
        out_f.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        gaps = res["gap_stats_ms"]
        summary.append({"episode_id": res["episode_id"],
                        "gap_mean_ms": {k: v["mean_ms"] for k, v in gaps.items()},
                        "gap_max_ms": {k: v["max_ms"] for k, v in gaps.items()}})
    report = {"master": args.master, "method": args.method,
              "episodes_ok": len(summary), "episodes_failed": failed,
              "per_episode": summary}
    (args.out_dir / "alignment_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"对齐完成: 成功 {len(summary)} / 失败 {len(failed)} (主通道={args.master}, {args.method})")
    for s in summary[:5]:
        print(" ", s)
    print(f"报告: {(args.out_dir / 'alignment_report.json').resolve()}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
