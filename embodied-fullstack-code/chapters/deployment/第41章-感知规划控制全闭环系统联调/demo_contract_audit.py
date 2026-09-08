# -*- coding: utf-8 -*-
"""第41章 L1 极简 Demo：接口契约审计。"""
from __future__ import annotations
import sys

IFACES = [
    {"name": "perception_target", "producer": "perception",
     "consumer": "planner", "fields": ["x", "y", "frame"], "freq_hz": 15,
     "timeout_ms": 100},
    {"name": "plan_trajectory", "producer": "planner",
     "consumer": "controller", "fields": ["points"], "freq_hz": 10,
     "timeout_ms": 200},
    {"name": "cmd_vel", "producer": "controller", "consumer": "chassis",
     "fields": ["vx", "vyaw"], "freq_hz": 50, "timeout_ms": 50},
]


def main() -> int:
    issues = []
    for it in IFACES:
        if it["freq_hz"] <= 0 or it["timeout_ms"] <= 0 or not it["fields"]:
            issues.append(it["name"])
        print(f"{it['name']:<18} {it['producer']}->{it['consumer']} "
              f"{it['freq_hz']}Hz 超时{it['timeout_ms']}ms")
    print("审计:", "OK" if not issues else f"问题: {issues}")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
