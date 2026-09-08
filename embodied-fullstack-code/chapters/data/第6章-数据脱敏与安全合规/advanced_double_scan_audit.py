# -*- coding: utf-8 -*-
"""第6章 L3 高阶优化版：双检测器审计 + 稳定打码 + 脱敏证书。"""
from __future__ import annotations

import argparse, hashlib, json, logging, re, sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("privacy_audit")

A_PATTERNS = [("id_cn", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
              ("mobile_cn", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
              ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"))]
B_DIGIT_RUN = re.compile(r"\d{11,}")


def scan_a(text: str) -> list[str]:
    return [name for name, pat in A_PATTERNS if pat.search(text)]


def scan_b(text: str) -> list[str]:
    return ["digit_run_heuristic"] if B_DIGIT_RUN.search(text) else []


def mask_value(v: str) -> str:
    """结构化打码：身份证/手机保留前3后4，中间哈希；邮箱打星。"""
    def _rep(m):
        raw = m.group(0)
        if "@" in raw:
            local, _, domain = raw.partition("@")
            return local[:2] + "***@" + domain
        if len(raw) < 8:
            return "*" * len(raw)
        digest = hashlib.sha1(raw.encode()).hexdigest()[:6]
        return raw[:3] + digest + raw[-4:]
    out = v
    for _, pat in A_PATTERNS:
        out = pat.sub(_rep, out)
    return out


def mask_tree(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: mask_tree(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask_tree(v) for v in obj]
    if isinstance(obj, str):
        return mask_value(obj)
    return obj


def collect_strings(obj: Any, path: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(collect_strings(v, path + "." + str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(collect_strings(v, path + "[" + str(i) + "]"))
    elif isinstance(obj, str):
        out.append((path, obj))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="双检审计与脱敏证书(L3)")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        strings = collect_strings(raw, "root")
        hits, disagreements = [], []
        for field, text in strings:
            a = scan_a(text)
            b = scan_b(text)
            if a or b:
                hits.append({"field": field, "detector_a": a, "detector_b": b})
            if b and not a:
                disagreements.append({"field": field, "text": text[:60],
                                      "reason": "B检出A未检出"})
        final = mask_tree(raw)
        payload = json.dumps({"hits": hits, "disagreements": disagreements},
                             ensure_ascii=False, sort_keys=True)
        cert = {"detectors": ["regex(A)", "digit_run_heuristic(B)"],
                "hit_count": len(hits),
                "disagreement_count": len(disagreements),
                "disagreements": disagreements,
                "risk_level": "P0" if disagreements else "P1",
                "verdict": "release-blocked" if disagreements else "pass",
                "checksum": hashlib.sha256(payload.encode()).hexdigest()[:16],
                "note": "存在 disagreement 时必须人工复核后才可发布"}
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "redacted_final.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "redaction_cert.json").write_text(
        json.dumps(cert, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"双检审计: 命中 {cert['hit_count']} 处, "
          f"A/B不一致 {cert['disagreement_count']} 处")
    for d in disagreements[:5]:
        print("  待人工:", d["field"], d["reason"])
    print("结论:", cert["verdict"], "| 证书 checksum:", cert["checksum"])
    print(f"输出: {(args.out_dir / 'redaction_cert.json').resolve()}")
    return 0 if cert["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
