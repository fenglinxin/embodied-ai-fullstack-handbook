# 第16章《预测模块》代码落地包

> 配套公众号文章：【具身智能全栈工程·第16章】会预判的机器人才安全
> 落地目标：CV 基线、多假设预测评测（minADE/minFDE）、预测-规划概率安全门。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_constant_velocity.py` | L1 | 匀速外推 vs 保持静止基线（行人转向场景暴露基线局限） |
| `engineering_prediction_eval.py` | L2 | 多假设 minADE/minFDE + CV 基线对比、beats_cv 升级判据（含样例与 ego 路径生成） |
| `advanced_safety_gate.py` | L3 | 多假设×自车路径逐时刻最小间距、碰撞概率合计、stop/slow/continue 分级决策 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第16章-预测模块-动态物体与交互预测
python demo_constant_velocity.py
python engineering_prediction_eval.py --make-sample sample
python engineering_prediction_eval.py --input sample/predictions.json --out-dir out
python advanced_safety_gate.py --ego sample/ego_path.json \
    --pred sample/predictions.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：行人 0.6s 后转向，匀速误差 0.441m / 静止 0.332m —— 提示"任何预测模型先赢过 CV 基线"
L2：
```text
c1: minADE=0.0 (CV=0.2) minFDE=0.0 beats_cv=True
```
L3：
```text
hyp prob=0.9 min_dist=0.1m collide=True
hyp prob=0.1 min_dist=0.1m collide=True
碰撞概率合计 1.0 -> 动作: stop
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| SAFE_DIST | 0.5m | 移动机器人 | 高速场景按制动距离放大 |
| SLOW_PROB / STOP_PROB | 0.2 / 0.5 | 分级决策 | 人机共融更保守 |
| horizon | 1s（L1） | 按制动距离反推 | 过长误差爆炸 |
| minADE/minFDE | 多假设取最优 | 评测口径 | 需同时报告 CV 基线 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 学习模型没赢过 CV | 数据不足/场景不匹配 | 难例子集评测（文章） |
| 2. 多假设全是同一条 | 模型坍缩 | 加多样性与概率校准 |
| 3. 把每条假设当必然 | 无概率门 | L3 概率分级 |
| 4. 预测坐标系没补偿自身运动 | ego 未处理 | 全局系预测+ego 补偿 |
| 5. minFDE 只看终点被长尾骗 | 只看终点 | ADE+FDE+碰撞率一起看 |

## 7. 改造指南

- 真实预测器输出按 hypotheses JSON 格式接入 L2/L3；
- CV 基线生成函数可直接做"地板"，任何新模型对比它；
- L3 动作输出可接第17章局部规划器（减速/让行语义）。

## 8. 进阶方向

多智能体交互建模（相对位置特征）；世界模型预测（第23章）接入本评测；把 safety_gate 概率阈值按场景参数化并进第30章评测协议。
