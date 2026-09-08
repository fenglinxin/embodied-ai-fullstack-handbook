# -*- coding: utf-8 -*-
"""第25章 L3 高阶优化版：仿真选型 30 分钟冒烟检查（环境自动探测）。"""
from __future__ import annotations

import argparse, importlib, json, shutil, sys
from pathlib import Path


def check_python():
    v = sys.version_info
    return ("PASS", f"{v.major}.{v.minor}.{v.micro}") if v >= (3, 9)         else ("FAIL", str(v))


def check_cmd(cmd):
    p = shutil.which(cmd)
    return ("PASS", p) if p else ("WARN", "未安装(选装)")


def check_import(name):
    try:
        importlib.import_module(name)
        return "PASS", "可导入"
    except Exception:
        return "WARN", "未安装(选装，按选型决定)"


def check_urdf(base):
    found = list(Path(base).rglob("*.urdf"))[:3] if base.exists() else []
    return ("PASS", f"{len(found)} 个") if found else         ("WARN", "未找到 URDF(仅作物理冒烟素材检查)")


def main() -> int:
    ap = argparse.ArgumentParser(description="仿真冒烟检查(L3)")
    ap.add_argument("--asset-dir", type=Path, default=Path("."))
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    args = ap.parse_args()
    checks = [
        ("python", check_python()),
        ("nvidia-smi(GPU)", check_cmd("nvidia-smi")),
        ("git", check_cmd("git")),
        ("mujoco(python)", check_import("mujoco")),
        ("URDF 素材", check_urdf(args.asset_dir)),
    ]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {"checks": [{"name": n, "status": s, "detail": d}
                         for n, (s, d) in checks]}
    (args.out_dir / "smoke_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, (status, detail) in checks:
        print(f"  [{status:<4}] {name}: {detail}")
    fails = sum(1 for _, (s, _) in checks if s == "FAIL")
    print("FAIL 数:", fails, "| WARN=按目标仿真器选装")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
