# -*- coding: utf-8 -*-
"""第28章 L3 高阶优化版：真机锚点迁移矩阵（差距热力图+迭代建议）。"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path

logger = logging.getLogger("anchor_matrix")
GAP_TOL = 0.15


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    data = {
        "behaviors": {
            "悬停漂移": {"sim": 0.95, "real": 0.85},
            "推方块到位": {"sim": 0.95, "real": 0.55},
            "抓马克杯": {"sim": 0.90, "real": 0.40},
            "直线跟踪": {"sim": 0.98, "real": 0.90},
        }}
    (root / "anchors.json").write_text(json.dumps(data), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="锚点迁移矩阵(L3)")
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
        data = json.loads(args.input.read_text(encoding="utf-8"))
        rows = []
        for name, m in data["behaviors"].items():
            gap = m["sim"] - m["real"]
            rows.append({"behavior": name, "sim": m["sim"], "real": m["real"],
                         "gap": round(gap, 3),
                         "verdict": "OK" if gap <= GAP_TOL else "GAP"})
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: -r["gap"])
    report = {"gap_tolerance": GAP_TOL, "rows": rows,
              "priority": [r["behavior"] for r in rows if r["verdict"] == "GAP"]}
    (args.out_dir / "anchor_matrix.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        bar = "#" * int(r["gap"] * 50)
        print(f"{r['behavior']:<10} sim={r['sim']:.2f} real={r['real']:.2f} "
              f"gap={r['gap']:.2f} [{r['verdict']}] {bar}")
    print("优先级(按差距):", report["priority"] or "无")
    print("动作：差距大->回仿真补系统辨识/DR/真机微调(第28章组合拳)")
    return 0 if not report["priority"] else 1


if __name__ == "__main__":
    sys.exit(main())
