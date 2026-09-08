# -*- coding: utf-8 -*-
"""第11章 L3 高阶优化版：故障断点续跑 + 可复现性校验。

场景：clean 阶段失败（如磁盘/规则bug），修复后重跑——
  * ingest 已成功：SKIP（幂等）
  * clean/quality：继续执行
  * 两次全成功运行的 checksum 完全一致（可复现证明）

运行：
  python advanced_pipeline_resume.py --work-dir out1 --fail-at clean
  python advanced_pipeline_resume.py --work-dir out1            # resume
  python advanced_pipeline_resume.py --work-dir out2            # 干净重跑
"""
from __future__ import annotations

import argparse, hashlib, json, logging, sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("pipeline_resume")

VERSION = "1.0.0"


def fn_ingest(work: Path) -> dict:
    return {"episodes": [{"id": f"ep-{i:04d}", "dirty": i % 3 == 0}
                         for i in range(9)]}


def fn_clean(work: Path, prev: dict) -> dict:
    eps = prev["ingest"]["episodes"]
    return {"cleaned_count": sum(1 for e in eps if not e["dirty"])}


def fn_quality(work: Path, prev: dict) -> dict:
    return {"score": round(prev["clean"]["cleaned_count"] / 9.0, 3)}


TASKS: dict[str, dict[str, Any]] = {
    "ingest": {"deps": [], "run": fn_ingest},
    "clean": {"deps": ["ingest"], "run": fn_clean},
    "quality": {"deps": ["clean"], "run": fn_quality},
}


def topo() -> list[str]:
    done: list[str] = []
    while len(done) < len(TASKS):
        for nid in TASKS:
            if nid not in done and all(d in done for d in TASKS[nid]["deps"]):
                done.append(nid)
    return done


def cfg_hash(nid: str) -> str:
    return hashlib.sha256(json.dumps(
        {"n": nid, "v": VERSION}, sort_keys=True).encode()).hexdigest()[:12]


def run_pipeline(work: Path, fail_at: str | None) -> dict[str, Any]:
    work.mkdir(parents=True, exist_ok=True)
    outs: dict[str, Any] = {}
    report: dict[str, Any] = {}
    for nid in topo():
        art = work / (nid + ".json")
        meta = {"node": nid, "version": VERSION, "config_hash": cfg_hash(nid)}
        if art.exists():
            cached = json.loads(art.read_text(encoding="utf-8"))
            if cached.get("config_hash") == meta["config_hash"]:
                outs[nid] = cached["data"]
                report[nid] = {"status": "SKIP",
                               "checksum": cached["checksum"]}
                logger.info("%s SKIP", nid)
                continue
        if nid == fail_at:
            raise RuntimeError(f"模拟故障: {nid} 阶段异常(已修复后可重跑)")
        prev = {d: outs[d] for d in TASKS[nid]["deps"]}
        data = TASKS[nid]["run"](work, prev) if prev else TASKS[nid]["run"](work)
        checksum = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
        body = {**meta, "data": data, "checksum": checksum}
        art.write_text(json.dumps(body, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        outs[nid] = data
        report[nid] = {"status": "RUN", "checksum": checksum}
        logger.info("%s RUN", nid)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="断点续跑+可复现校验(L3)")
    ap.add_argument("--work-dir", required=True, type=Path)
    ap.add_argument("--fail-at", choices=["clean", "quality"], default=None)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        report = run_pipeline(args.work_dir, args.fail_at)
    except RuntimeError as exc:
        logger.error("管道中断: %s（修复后重跑即可续点）", exc)
        return 1
    (args.work_dir / "run_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("节点:", {k: v["status"] for k, v in report.items()})
    print("checksum:", {k: v["checksum"] for k, v in report.items()})
    print("说明: 相同配置重跑时 SKIP 节点不重算；两个干净 work 目录的 "
          "checksum 一致=可复现。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
