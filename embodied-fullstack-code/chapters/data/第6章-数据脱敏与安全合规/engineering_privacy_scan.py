# -*- coding: utf-8 -*-
"""第6章 L2 工业工程版：结构化记录 PII 扫描与脱敏（批量+可配置）。"""
from __future__ import annotations

import argparse, json, logging, re, sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("privacy_scan")

PATTERNS = {
    "id_cn": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "mobile_cn": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
}
RISK = {"id_cn": "P0", "mobile_cn": "P0", "email": "P1"}


def sanitize_value(v: str) -> tuple[str, list[dict]]:
    hits: list[dict] = []

    def _rep(m, name=""):
        hits.append({"type": name, "value": m.group(0)})
        return "[" + name + "]"

    out = v
    for name, pat in PATTERNS.items():
        out = pat.sub(lambda m, name=name: _rep(m, name), out)
    return out, hits


def walk(obj: Any, path: str, out_obj: Any) -> list[dict]:
    hits_all: list[dict] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child_path = path + "." + str(k)
            if isinstance(v, str):
                clean, hits = sanitize_value(v)
                out_obj[k] = clean
                for h in hits:
                    h["field"] = child_path
                hits_all.extend(hits)
            else:
                child: Any = {} if isinstance(v, dict) else (
                    [] if isinstance(v, list) else v)
                out_obj[k] = child
                hits_all.extend(walk(v, child_path, child))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            child_path = path + "[" + str(i) + "]"
            if isinstance(v, str):
                clean, hits = sanitize_value(v)
                out_obj.append(clean)
                for h in hits:
                    h["field"] = child_path
                hits_all.extend(hits)
            else:
                child = {} if isinstance(v, dict) else (
                    [] if isinstance(v, list) else v)
                out_obj.append(child)
                hits_all.extend(walk(v, child_path, child))
    return hits_all


def main() -> int:
    ap = argparse.ArgumentParser(description="PII 扫描脱敏(工程版)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        out_root: Any = [] if isinstance(raw, list) else {}
        hits = walk(raw, "root", out_root)
        remaining = len(sanitize_value(
            json.dumps(out_root, ensure_ascii=False))[1])
        if not hits:
            logger.warning("未发现 PII（建议第二套检测器复核，见 L3）")
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "sanitized_records.json").write_text(
        json.dumps(out_root, ensure_ascii=False, indent=2), encoding="utf-8")
    p0 = [h for h in hits if RISK.get(h["type"]) == "P0"]
    risk = ("residual-risk" if remaining else
            ("clean-after-sanitize" if hits else "no-pii"))
    report = {"record_count": len(raw) if isinstance(raw, list) else 1,
              "hits": hits, "hit_count": len(hits),
              "p0_count": len(p0), "residual_hits": remaining,
              "risk": risk}
    (args.out_dir / "pii_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"扫描完成: 命中 {len(hits)} 处 (P0={len(p0)}, 残留={remaining})")
    for h in hits[:8]:
        print(f"  [{h['type']}] {h['field']}: {h['value']} -> [已替换]")
    print(f"风险: {risk}")
    print(f"报告: {(args.out_dir / 'pii_report.json').resolve()}")
    return 0 if remaining == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
