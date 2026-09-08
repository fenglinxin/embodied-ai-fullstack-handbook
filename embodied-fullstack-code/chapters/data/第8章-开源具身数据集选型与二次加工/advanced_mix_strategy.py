# -*- coding: utf-8 -*-
"""第8章 L3 高阶优化版：领域-开源混合策略（域标签+权重+碰撞检测）。

对应文章第5步"混合与采样策略"：
  领域:开源 = 2:1~4:1、来源域打标签、episode_id 碰撞检测。
输出 merged_train_manifest.json：episode_id,domain,weight,task,scene。

运行：
  python engineering_openx_processor.py --input-dir ./sample_sources \
      --task-keywords pick --out-dir out --make-sample
  python advanced_mix_strategy.py --open out/processed_manifest.json \
      --domain ../第1章-.../demo_data --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("mix_strategy")

DOMAIN_RATIO = 3.0      # 领域:开源 = 3:1（文章建议 2:1~4:1）


def load_json_list(p: Path) -> list[dict]:
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{p} 必须为 JSON 数组")
    return [r for r in raw if isinstance(r, dict)]


def main() -> int:
    ap = argparse.ArgumentParser(description="领域-开源混合策略(L3)")
    ap.add_argument("--open", required=True, type=Path)
    ap.add_argument("--domain", required=True, type=Path, help="domain Episode 目录")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--ratio", type=float, default=DOMAIN_RATIO)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        open_eps = load_json_list(args.open)
        domain_eps = []
        for f in sorted(args.domain.glob("*.json")):
            ep = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(ep, dict) and ep.get("episode_id"):
                domain_eps.append(ep)
        if not open_eps or not domain_eps:
            raise RuntimeError("开源或领域数据为空")
        seen: dict[str, str] = {}
        collisions = []
        rows: list[dict[str, Any]] = []
        for ep in domain_eps:
            eid = str(ep["episode_id"])
            if eid in seen:
                collisions.append({"id": eid, "between": ["domain", seen[eid]]})
                continue
            seen[eid] = "domain"
            rows.append({"episode_id": eid, "domain": "domain",
                         "weight": 1.0, "task": ep.get("task"),
                         "scene": ep.get("scene")})
        for ep in open_eps:
            eid = str(ep["episode_id"])
            if eid in seen:
                collisions.append({"id": eid, "between": ["open", seen[eid]]})
                continue
            seen[eid] = "open"
            # 开源数据降权，且训练期按 inverse 采样可再乘 1/ratio
            rows.append({"episode_id": eid, "domain": "open",
                         "weight": round(1.0 / args.ratio, 4),
                         "task": ep.get("task") or ep.get("instruction"),
                         "scene": ep.get("scene") or ep.get("source")})
        n_domain = sum(1 for r in rows if r["domain"] == "domain")
        n_open = sum(1 for r in rows if r["domain"] == "open")
        ratio_real = round(n_domain / max(1, n_open), 2)
        report = {"domain_episodes": n_domain, "open_episodes": n_open,
                  "real_ratio": ratio_real,
                  "target_ratio": args.ratio,
                  "collisions": collisions,
                  "verdict": "ok" if not collisions else "collision-found"}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "merged_train_manifest.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "mix_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"混合清单: 领域 {n_domain} + 开源 {n_open} "
          f"(实际比例 {ratio_real}:1, 目标 {args.ratio}:1)")
    print("episode_id 碰撞:", len(collisions), report["verdict"])
    print(f"输出: {(args.out_dir / 'merged_train_manifest.json').resolve()}")
    return 0 if report["verdict"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
