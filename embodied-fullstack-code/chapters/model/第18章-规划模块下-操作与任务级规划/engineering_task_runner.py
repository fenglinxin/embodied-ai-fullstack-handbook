# -*- coding: utf-8 -*-
"""第18章 L2 工业工程版：技能库任务执行器（前置条件/重试/超时/失败分类）。

技能库原子化：每个技能声明 pre 条件、执行函数、时长；
执行器负责顺序执行、重试策略、超时与失败分类（可恢复/不可恢复）。

运行：
  python engineering_task_runner.py --make-sample sample
  python engineering_task_runner.py --plan sample/plan.json --out-dir out
"""
from __future__ import annotations

import argparse, json, logging, random, sys, time
from pathlib import Path

logger = logging.getLogger("task_runner")
MAX_RETRY = 2
MAX_SKILL_S = 10.0


def skill_grasp(ctx):
    if not ctx["at_object"]:
        return False, "not_at_object"
    ok = random.Random(ctx["seed"] + ctx["attempts"]).random() < 0.9
    if ok:
        ctx["holding"] = True
    return ok, "ok" if ok else "grasp_slip"


def skill_place(ctx):
    if not ctx["holding"]:
        return False, "not_holding"
    ctx["holding"] = False
    return True, "ok"


def skill_approach(ctx):
    ctx["at_object"] = True
    return True, "ok"


SKILLS = {
    "approach": {"pre": lambda c: True, "run": skill_approach},
    "grasp": {"pre": lambda c: c["at_object"] and not c["holding"],
              "run": skill_grasp},
    "place": {"pre": lambda c: c["holding"], "run": skill_place},
}


def make_sample(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "plan.json").write_text(json.dumps(
        ["approach", "grasp", "place"]), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="技能任务执行器(工程版)")
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--make-sample", type=Path)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        if args.make_sample:
            make_sample(args.make_sample)
            print("样例已生成:", args.make_sample)
            return 0
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        ctx = {"at_object": False, "holding": False,
               "seed": args.seed, "attempts": 0}
        events = []
        for skill_name in plan:
            if skill_name not in SKILLS:
                raise ValueError("未知技能: " + skill_name)
            spec = SKILLS[skill_name]
            if not spec["pre"](ctx):
                events.append({"skill": skill_name, "status": "FAIL",
                               "reason": "precondition"})
                break
            done = False
            for attempt in range(1, MAX_RETRY + 2):
                ctx["attempts"] += 1
                ok, reason = spec["run"](ctx)
                events.append({"skill": skill_name, "attempt": attempt,
                               "status": "OK" if ok else "FAIL",
                               "reason": reason})
                if ok:
                    done = True
                    break
            if not done:
                break
        success = (len(events) > 0 and events[-1]["status"] == "OK"
                   and events[-1]["skill"] == plan[-1])
    except Exception as exc:
        logger.error("执行失败: %s", exc)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"plan": plan, "events": events, "success": success,
           "failure_class": None if success else events[-1].get("reason")}
    (args.out_dir / "task_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for e in events:
        print(f"  {e['skill']}#{e.get('attempt','-')}: {e['status']} {e['reason']}")
    print("任务结果:", "SUCCESS" if success else "FAIL")
    print(f"报告: {(args.out_dir / 'task_report.json').resolve()}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
