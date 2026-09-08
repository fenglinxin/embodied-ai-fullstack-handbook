# 第31章《零样本仿真迁移真机实战技巧》代码落地包（仿真层收官）

> 配套文章：【具身智能全栈工程·第31章】"零样本"迁移不是碰运气

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_readiness.py | L1 | 迁移就绪度评审（4 项不达标即拦截"零样本"说法） |
| engineering_first_run.py | L2 | 首跑分级扩测执行器：precheck→空跑→最小变体→全速，每级 exit 门槛 |
| advanced_failure_triage.py | L3 | 失败归因决策：fix-sim / fix-adapter / retrain-finetune 分流 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_readiness.py
python engineering_first_run.py --seed 5 --out-dir out
python advanced_failure_triage.py --make-sample sample
python advanced_failure_triage.py --input sample/failures.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：感知链路不一致 -> 拦截（先补课）

L2：dryrun 70% < exit90% -> STOP（分级拦截生效）

L3：grasp_slip->fix-sim；光照漏检/latency->fix-adapter；random->retrain

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 分级 exit | 0.8-0.9 | 逐级门槛 |
| speed | 0.2→1.0 | 保守放开 |
| 归因规则 | 关键词表 | 可扩展 |

## 6. Top5 踩坑

1. 就绪度不过就上真机：L1 拦截。
2. 一次成功宣布成功：分级统计。
3. 失败先重训：先按 L3 归因（查现场/适配）。
4. 现场参数改了不同步仿真：版本管理。
5. 传感器静默失效：健康监控。

## 7. 改造指南

- 就绪度清单按第28章矩阵定制；
- 分级门槛按业务成功率定义；
- 归因规则接入第42章排障流程。

## 8. 进阶方向：影子部署对比、失败模式驱动仿真补课、渐进自动化放量。
