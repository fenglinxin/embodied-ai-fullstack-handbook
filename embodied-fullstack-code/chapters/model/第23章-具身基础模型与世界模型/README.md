# 第23章《具身基础模型与世界模型》代码落地包

> 配套文章：【具身智能全栈工程·第23章】让机器人在脑海里"预演"

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_world_model.py | L1 | 1D 世界模型 rollout 与"预测=物理直觉"最小演示 |
| engineering_wm_eval.py | L2 | WM 可信度评测：逐步 RMSE、事件 TP/FP/FN/TN、长时程衰减 |
| advanced_imagination_plan.py | L3 | 想象式规划（rollout 选最优 v）+ 置信度红线回退保守策略 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_world_model.py
python engineering_wm_eval.py --make-sample sample
python engineering_wm_eval.py --input sample/wm_eval.json --out-dir out
python advanced_imagination_plan.py                 # 红线回退
python advanced_imagination_plan.py --use-model     # 想象式规划
```

## 4. 标准运行结果（本机实测）

L1：预测与真值误差 0（1D 常速辨识）

L2：RMSE 逐步 0→0.36 单调增长（长时程衰减 5.1 可见）；事件 FP=1（误报碰撞）

L3：use-model -> v=0.4 cost=0.04 直达目标；默认 -> 不确定性红线回退 v=0.2

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| HORIZON | 5 | 预测时域 |
| noise | 0 | rollout 不确定性 |
| 红线条件 | noise>0.3 | 置信度红线 |
| 事件指标 | TP/FP/FN/TN | 别只看画质 |

## 6. Top5 踩坑

1. 用画质判断世界模型：要事件级指标（L2）。
2. 预测越远越离谱当故障：看衰减曲线定可用时域。
3. 想象规划直接执行：保留置信度红线与安全壳。
4. 把 WM 当物理引擎：它是统计预测。
5. 仿真里神真机崩：域差距按第28章处理。

## 7. 改造指南

- 真实 WM 输出接 L2 schema（pred/gt/event）；
- 接入第22章 VLA：VLA 出候选动作、WM 批量评估选优；
- 生产只先做"软提示/离线分析"，想象规划最后上。

## 8. 进阶方向：事件级 WM 优先、仿真预训练+真机微调、作数据工厂生成对抗难例。
