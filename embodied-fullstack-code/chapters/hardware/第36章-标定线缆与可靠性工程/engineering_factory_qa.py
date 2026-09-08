# -*- coding: utf-8 -*-
"""第36章 L2 工业工程版：出厂直通率与故障 Pareto。"""
from __future__ import annotations

import argparse, json, logging, sys
from collections import Counter
from pathlib import Path

logger = logging.getLogger("factory_qa")


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    units = []
    reasons = ["线缆松脱", "标定散差", "驱动报警", "相机歪", "线缆松脱",
               "标定散差", "OK", "OK", "OK", "OK", "OK", "OK", "OK", "OK",
               "OK", "OK", "OK", "OK", "OK", "OK"]
    for i in range(len(reasons)):
        units.append({"serial": f"R-{i:04d}", "pass": reasons[i] == "OK",
                      "reason": None if reasons[i] == "OK" else reasons[i]})
    (root / "units.json").write_text(json.dumps(units), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="出厂QA(工程版)")
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
        units = json.loads(args.input.read_text(encoding="utf-8"))
        n = len(units)
        passed = sum(1 for u in units if u["pass"])
        reasons = Counter(u["reason"] for u in units if not u["pass"])
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    top = reasons.most_common()
    rep = {"total": n, "pass": passed, "first_pass_yield": round(passed / n, 3),
           "failure_pareto": [{"reason": r, "count": c} for r, c in top]}
    (args.out_dir / "factory_qa.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"直通率 {passed}/{n} = {passed/n:.0%}")
    for r, c in top:
        print(f"  {r}: {c}")
    print("行动：Pareto 前2项进设计/工艺改进，别当个案")
    return 0 if passed / n >= 0.9 else 1


if __name__ == "__main__":
    sys.exit(main())
