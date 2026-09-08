# -*- coding: utf-8 -*-
"""第11章 L2 工业工程版：文件级 DAG 管道（幂等/哈希/血缘报告）。

内置节点：ingest -> clean -> quality（替换函数即可接入你的流水线）。
幂等策略：每个节点产物写入 work/<node>.json，
         产物内记录 config_hash；相同配置重跑直接 SKIP。

运行：
  python engineering_pipeline_runner.py --work-dir out        # 第一次全跑
  python engineering_pipeline_runner.py --work-dir out        # 第二次全 SKIP
  python engineering_pipeline_runner.py --work-dir out --force # 强制重跑
"""
from __future__ import annotations

import argparse, hashlib, json, logging, sys
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("pipeline_runner")

NODE_VERSION = "1.0.0"


def fn_ingest(work: Path) -> dict:
    """原料：模拟一批 Episode 摘要（确定性生成）。"""
    return {"episodes": [{"id": f"ep-{i:04d}", "dirty": i % 3 == 0}
                         for i in range(9)]}


def fn_clean(work: Path, prev: dict) -> dict:
    eps = prev["ingest"]["episodes"]
    cleaned = [e for e in eps if not e["dirty"]]
    return {"cleaned_count": len(cleaned),
            "dropped": [e["id"] for e in eps if e["dirty"]]}


def fn_quality(work: Path, prev: dict) -> dict:
    n = prev["clean"]["cleaned_count"]
    return {"total": n, "score": round(n / 9.0, 3)}


TASKS: dict[str, dict[str, Any]] = {
    "ingest": {"deps": [], "run": fn_ingest, "params": {}},
    "clean": {"deps": ["ingest"], "run": fn_clean, "params": {}},
    "quality": {"deps": ["clean"], "run": fn_quality, "params": {}},
}


def topo_order() -> list[str]:
    done: list[str] = []
    while len(done) < len(TASKS):
        for nid in TASKS:
            if nid not in done and all(d in done for d in TASKS[nid]["deps"]):
                done.append(nid)
    return done


def config_hash(nid: str) -> str:
    blob = json.dumps({"node": nid, "version": NODE_VERSION,
                       "params": TASKS[nid]["params"]}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def artifact_path(work: Path, nid: str) -> Path:
    return work / (nid + ".json")


def main() -> int:
    ap = argparse.ArgumentParser(description="数据管道DAG执行器(工程版)")
    ap.add_argument("--work-dir", type=Path, default=Path("out"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        outputs: dict[str, Any] = {}
        status: dict[str, str] = {}
        lineage: dict[str, dict[str, Any]] = {}
        for nid in topo_order():
            meta = {"config_hash": config_hash(nid),
                    "version": NODE_VERSION, "node": nid}
            art = artifact_path(args.work_dir, nid)
            if art.exists() and not args.force:
                cached = json.loads(art.read_text(encoding="utf-8"))
                if cached.get("config_hash") == meta["config_hash"]:
                    outputs[nid] = cached["data"]
                    status[nid] = "SKIP"
                    lineage[nid] = {"action": "skip",
                                    "checksum": cached.get("checksum")}
                    logger.info("%s SKIP(幂等命中)", nid)
                    continue
            prev = {dep: outputs[dep] for dep in TASKS[nid]["deps"]}
            task = TASKS[nid]["run"]
            data = task(args.work_dir, prev) if prev else task(args.work_dir)
            body = {**meta, "data": data,
                    "checksum": hashlib.sha256(
                        json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]}
            art.write_text(json.dumps(body, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            outputs[nid] = data
            status[nid] = "RUN"
            lineage[nid] = {"action": "run", "checksum": body["checksum"],
                            "deps": TASKS[nid]["deps"]}
            logger.info("%s RUN", nid)
    except Exception as exc:
        logger.error("管道执行失败: %s", exc)
        return 1
    report = {"status": status, "lineage": lineage}
    (args.work_dir / "run_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("节点状态:", status)
    print(f"血缘报告: {(args.work_dir / 'run_report.json').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
