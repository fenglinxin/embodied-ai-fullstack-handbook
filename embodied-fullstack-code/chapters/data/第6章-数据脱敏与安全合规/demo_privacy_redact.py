# -*- coding: utf-8 -*-
"""第6章 L1 极简 Demo：文本 PII 扫描打码 + 区域矩阵模糊（纯标准库）。"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

TEXT_PATTERNS = {
    "id_cn": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "mobile_cn": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
}


def redact_text(text: str) -> tuple[str, list[str]]:
    hits = []
    for name, pat in TEXT_PATTERNS.items():
        def _rep(m, name=name):
            hits.append({"type": name, "value": m.group(0)})
            return "[" + name + "]"
        text = pat.sub(_rep, text)
    return text, hits


def box_blur(matrix, box, k=3):
    h, w = len(matrix), len(matrix[0])
    x0, y0, bw, bh = box
    out = [row[:] for row in matrix]
    for y in range(y0, min(y0 + bh, h)):
        for x in range(x0, min(x0 + bw, w)):
            s = c = 0
            for dy in range(-k, k + 1):
                for dx in range(-k, k + 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w:
                        s += matrix[yy][xx]; c += 1
            out[y][x] = s // max(1, c)
    return out


def fake_frame():
    import random
    rng = random.Random(1)
    m = [[rng.randint(0, 40) for _ in range(64)] for _ in range(48)]
    for y in range(18, 30):
        for x in range(28, 38):
            m[y][x] = 220
    return m, [(28, 18, 10, 12), (50, 40, 10, 6)]


def main() -> int:
    ap = argparse.ArgumentParser(description="脱敏最小演示")
    ap.add_argument("--out", type=Path, default=Path("sample_records.json"))
    args = ap.parse_args()
    sample = ("操作者 alice 电话 13800138000，身份证 110101199003071234，"
              "邮箱 a@b.com 已授权")
    redacted, hits = redact_text(sample)
    print("原文:", sample)
    print("脱敏:", redacted)
    print("命中:", json.dumps(hits, ensure_ascii=False))
    m, boxes = fake_frame()
    m2 = box_blur(m, boxes[0], k=5)
    changed = sum(1 for a, b in zip(m[18], m2[18]) if a != b)
    print(f"区域打码: 框内首行变化像素 {changed}/10")
    records = [{"episode_id": "ep-0001", "scene": "office",
                "operator_note": "访客 13912345678 在门口等待",
                "language": "把快递给 13800138000 用户",
                "file_name": "IMG_20260101_110101199003071234.jpg",
                "log_ref": "批次号 202601010000123"}]
    args.out.write_text(json.dumps(records, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"L2 样例已写入: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
