# -*- coding: utf-8 -*-
"""第15章 L2 工业工程版：常速模型卡尔曼估计器（位置+速度，矩阵版）。"""
from __future__ import annotations

import argparse, json, logging, math, sys
from pathlib import Path

logger = logging.getLogger("state_estimator")

R = {"joint": 1e-4, "imu": 1e-2}
Q_SCALE = 1e-4


def mat_mul(a, b):
    return [[sum(x * y for x, y in zip(ra, cb)) for cb in zip(*b)]
            for ra in a]


def mat_add(a, b):
    return [[x + y for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def mat_trans(a):
    return [list(r) for r in zip(*a)]


def mat_scale(a, s):
    return [[x * s for x in row] for row in a]


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    truth = 0.0
    vel = 0.5
    for i in range(60):
        truth += vel * 0.05
        vel = 0.5 + 0.02 * math.sin(i / 5.0)
        rows.append({"t": round(i * 0.05, 3), "source": "joint",
                     "kind": "pos", "value": round(truth, 4),
                     "truth_pos": round(truth, 4)})
        if i % 2 == 0:
            rows.append({"t": round(i * 0.05, 3), "source": "imu",
                         "kind": "vel", "value": round(vel, 4),
                         "truth_vel": round(vel, 4)})
    (root / "measurements.json").write_text(
        json.dumps(rows), encoding="utf-8")


def run_filter(rows, use):
    x = [0.0, 0.0]
    P = [[1.0, 0.0], [0.0, 1.0]]
    out = []
    prev_t = None
    for m in rows:
        if m["source"] not in use:
            continue
        t = m["t"]
        dt = (t - prev_t) if prev_t is not None else 0.05
        prev_t = t
        F = [[1.0, dt], [0.0, 1.0]]
        x = [F[0][0] * x[0] + F[0][1] * x[1],
             F[1][0] * x[0] + F[1][1] * x[1]]
        P = mat_add(mat_mul(mat_mul(F, P), mat_trans(F)),
                    mat_scale([[1.0, 0.0], [0.0, 1.0]], Q_SCALE))
        H = [1.0, 0.0] if m["kind"] == "pos" else [0.0, 1.0]
        r = R[m["source"]]
        ph = [P[0][0] * H[0] + P[0][1] * H[1],
              P[1][0] * H[0] + P[1][1] * H[1]]
        s = ph[0] * H[0] + ph[1] * H[1] + r
        K = [ph[0] / s, ph[1] / s]
        innov = m["value"] - (H[0] * x[0] + H[1] * x[1])
        x[0] += K[0] * innov
        x[1] += K[1] * innov
        KH = [[K[0] * H[0], K[0] * H[1]], [K[1] * H[0], K[1] * H[1]]]
        Pn = [[(1.0 if c == r_ else 0.0) - KH[r_][c]
               for c in range(2)] for r_ in range(2)]
        P = mat_mul(Pn, P)
        out.append({"t": t, "pos": round(x[0], 4),
                    "vel": round(x[1], 4),
                    "truth_pos": m.get("truth_pos"),
                    "truth_vel": m.get("truth_vel")})
    return out


def rmse(est, key):
    field = "truth_pos" if key == "pos" else "truth_vel"
    pairs = [(e[key], e[field]) for e in est if e.get(field) is not None]
    if not pairs:
        return None
    return round(math.sqrt(sum((a - b) ** 2 for a, b in pairs) / len(pairs)), 4)


def main() -> int:
    ap = argparse.ArgumentParser(description="状态估计器(工程版)")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--sources", nargs="*", default=["joint", "imu"])
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
        rows = json.loads(args.input.read_text(encoding="utf-8"))
        rows.sort(key=lambda m: m["t"])
        est = run_filter(rows, set(args.sources))
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "estimates.json").write_text(
        json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
    rep = {"estimates": len(est), "sources": args.sources,
           "rmse_pos": rmse(est, "pos"), "rmse_vel": rmse(est, "vel")}
    (args.out_dir / "estimate_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"估计点数 {len(est)} RMSE_pos={rep['rmse_pos']} "
          f"RMSE_vel={rep['rmse_vel']}")
    print(f"报告: {(args.out_dir / 'estimate_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
