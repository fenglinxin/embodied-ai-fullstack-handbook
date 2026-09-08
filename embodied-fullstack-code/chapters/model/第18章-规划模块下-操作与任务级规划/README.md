# 第18章《操作与任务级规划》代码落地包

> 配套文章：【具身智能全栈工程·第18章】从"走到桌前"到"把螺丝拧进去"

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_behavior_tree.py | L1 | 行为树：Sequence/Selector/Retry，抓取失败自动重试 |
| engineering_task_runner.py | L2 | 技能库执行器：前置条件/重试/超时语义/失败分类，task_report.json |
| advanced_tamp_search.py | L3 | 简化 TAMP：清障->抓取->放置的顺序搜索 + 运动可行性门 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_behavior_tree.py
python engineering_task_runner.py --make-sample sample
python engineering_task_runner.py --plan sample/plan.json --seed 7 --out-dir out
python advanced_tamp_search.py
```

## 4. 标准运行结果（本机实测）

L1：approach OK -> grasp FAIL -> grasp OK -> place OK -> 整树 SUCCESS

L2：approach/grasp/place 全部一次 OK，任务 SUCCESS

L3：
```text
TAMP 规划结果:  clear B -> pick A -> place A
运动可行性检查: 全部通过
```

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| MAX_RETRY | 2 | 可恢复失败重试上限 |
| MAX_SKILL_S | 10s | 技能超时（模拟） |
| 技能前置 | pre 函数 | 防止乱序执行 |
| feasible 集合 | A/C | 运动可行性门（TAMP 概念） |

## 6. Top5 踩坑

1. pick 后目标从状态里消失导致 place 永不触发（本包修复：pick 保留待交付集合）。
2. 技能无前置条件乱序：每个技能声明 pre。
3. 重试无状态复位：失败先回安全位再重试。
4. 只做任务搜索不管运动：TAMP 需逐候选过运动可行性。
5. 固定流程硬编码：先用 FSM/行为树，组合复杂再上搜索。

## 7. 改造指南

- 技能库接入真实控制：run 函数换成 MoveIt/控制接口，pre 换成状态回读；
- 任务树可换 JSON 配置驱动；
- TAMP 候选过多时用任务层先剪枝再运动验证。

## 8. 进阶方向：行为树状态可视化、HTN、与 VLA 意图层混合（VLA 出意图，规划器兑现）。
