# 第22章《VLA 模型原理与工程拆解》代码落地包

> 配套文章：【具身智能全栈工程·第22章】把"看懂听懂"变成"会做"

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_action_chunk.py | L1 | 动作 token 化(2cm桶)与还原、动作块概念 |
| engineering_vla_adapter.py | L2 | VLA 训练样本适配器：Prompt 模板+归一化+分块+场景级 train/val 切分，输出 JSONL |
| advanced_vla_safety_shell.py | L3 | 真机安全壳：限速/边界/低置信回退（fallback-stop/last） |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_action_chunk.py
python engineering_vla_adapter.py --make-sample sample
python engineering_vla_adapter.py --input-dir sample --out-dir out --chunk-size 5 --stride 2
python advanced_vla_safety_shell.py
```

## 4. 标准运行结果（本机实测）

L1：动作块量化 token [1,2,3,4,5]，最大量化误差 0.001m

L2：样本 4（train=2/val=2，场景级防泄漏），输出 train.jsonl/val.jsonl

L3：执行 3/4，超速 0.3→0.2 被限速，conf=0.30 触发 fallback-last

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| BIN | 0.02m | 动作量化桶 |
| chunk-size | 5 | 动作块长度 |
| stride | 2 | 分块步长 |
| scale | 100 | 归一化整数化 |
| MAX_SPEED | 0.2 | 安全壳限速 |
| CONF_FALLBACK | 0.6 | 低置信回退 |

## 6. Top5 踩坑

1. 动作空间/单位没对齐：先归一化并记录 scale。
2. train/val 同场景泄漏：场景级切分（L2）。
3. VLA 高频下发：动作块+滚动执行。
4. 低置信还硬执行：安全壳回退（L3）。
5. 只有图像没有本体状态：输入协议加 proprio。

## 7. 改造指南

- 真实训练：把 JSONL 交给 VLA 微调框架（如 OpenVLA/LLaVA 动作头）；
- 观测：把 image_id 替换为实际帧路径或特征；
- 安全壳接控制层：输出限速后的末端增量给第19章控制器。

## 8. 进阶方向：扩散/流匹配动作头；后训练偏好优化；蒸馏到端侧（第24章）。
