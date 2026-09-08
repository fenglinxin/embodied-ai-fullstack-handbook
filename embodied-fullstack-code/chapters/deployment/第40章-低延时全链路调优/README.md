# 第40章《低延时全链路调优》代码落地包

> 配套文章：【具身智能全栈工程·第40章】从摄像头到电机：把每一毫秒都管起来

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_data_age.py | L1 | 数据年龄分析（P95=150ms 揭示"感觉慢"来源） |
| engineering_pipeline_parallel.py | L2 | 串行 vs 流水线并行（51ms→25ms 稳态节拍） |
| advanced_action_chunk_advisor.py | L3 | P99 预算核对 + 动作块长度建议（500ms/20ms→25步） |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_data_age.py
python engineering_pipeline_parallel.py
python advanced_action_chunk_advisor.py
```

## 4. 标准运行结果（本机实测）

L1：均值 59ms 但 P95=150ms（偶发才是元凶）

L2：串行 51ms → 并行稳态 25ms

L3：动作块 25 步覆盖 500ms 推理周期

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 数据年龄 | P95 口径 | 真实延迟 |
| 稳态节拍 | max(单段) | 并行目标 |
| chunk | ceil(推理/控制) | 动作块 |
| 预算 | 70ms | 任务定 |

## 6. Top5 踩坑

1. 只看平均延迟：P95/P99。
2. 每段都快整机慢：排队。
3. 控制等 AI：阻塞抖动。
4. 无动作块：低频推理断流。
5. 同步点等慢传感器：数据年龄。

## 7. 改造指南

- 数据年龄由端到端打点生成；
- 流水线接真线程/进程；
- chunk 建议给 VLA 部署配置。

## 8. 进阶方向：预测补偿延迟、关键路径最短化、回放驱动延迟回归。
