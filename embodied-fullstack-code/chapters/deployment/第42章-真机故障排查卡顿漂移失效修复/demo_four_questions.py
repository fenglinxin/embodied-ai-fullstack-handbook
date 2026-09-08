# -*- coding: utf-8 -*-
"""第42章 L1 极简 Demo：现象四问（把玄学变可复现）。"""
from __future__ import annotations
import argparse, json, sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symptom", default="末端漂移")
    ap.add_argument("--when", default="满载运行2小时后")
    ap.add_argument("--condition", default="温度40°C，重复搬运")
    ap.add_argument("--repro", default="概率100%")
    a = ap.parse_args()
    ticket = {"现象": a.symptom, "何时开始": a.when,
              "条件": a.condition, "能否复现": a.repro,
              "提示": "现象可测量+条件可记录=排障范围缩小80%"}
    print(json.dumps(ticket, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
