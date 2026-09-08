# -*- coding: utf-8 -*-
"""第26章 L1 极简 Demo：场景资产质量检查（缺什么一目了然）。"""
from __future__ import annotations
import sys

REQUIRED = ("mesh", "mass", "friction", "collision", "material")

ASSETS = [
    {"name": "mug_red", "mesh": "mug.obj", "mass": 0.25,
     "friction": 0.6, "collision": True, "material": "ceramic"},
    {"name": "box_blue", "mesh": "", "mass": 0.5,
     "friction": 0.4, "collision": False, "material": ""},
    {"name": "table", "mesh": "table.fbx", "mass": 30.0,
     "friction": 0.5, "collision": True, "material": "wood"},
]


def main() -> int:
    for a in ASSETS:
        missing = [k for k in REQUIRED if not a.get(k)]
        status = "OK" if not missing else "MISSING " + ",".join(missing)
        print(f"{a['name']:<10} {status}")
    print("规则：缺 mesh/mass/friction/collision 的资产不进仿真库（质量门禁）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
