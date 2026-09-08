# -*- coding: utf-8 -*-
"""第36章 L1 极简 Demo：标定版本门禁（无记录=没标定）。"""
from __future__ import annotations
import sys

CALIB = {
    "robot_zero": {"version": "v3.2", "ok": True},
    "tcp": {"version": "v1.0", "ok": True},
    "cam_intrinsic": {"version": "", "ok": False},
    "cam_extrinsic": {"version": "v2.1", "ok": True},
}


def main() -> int:
    bad = []
    for name, c in CALIB.items():
        ok = c["ok"] and c["version"]
        if not ok:
            bad.append(name)
        print(f"{name:<16} {c['version'] or '(无版本)'} "
              f"[{'PASS' if ok else 'FAIL'}]")
    print("结论:", "全部已标定" if not bad else f"缺标定: {bad}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
