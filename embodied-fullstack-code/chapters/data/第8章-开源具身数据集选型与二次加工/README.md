# 第8章《开源具身数据集选型与二次加工》代码落地包

> 配套公众号文章：【具身智能全栈工程·第8章】开源数据集到底怎么选、怎么用？
> 落地目标：异构开源数据统一加工（语言/动作空间/需IK登记）+ 领域-开源混合策略。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_openx_mini.py` | L1 | 两个异构"开源子集"样例：语言字段别名统一、动作空间探测（ee_delta/joint_abs）与风险提示 |
| `engineering_openx_processor.py` | L2 | 目录级批量加工：语言统一为 instruction、任务关键词筛选、动作空间/维度/需IK登记、ts_ns 占位、processing_report |
| `advanced_mix_strategy.py` | L3 | 领域:开源混合（目标比例可配 2:1~4:1）、来源域标签、episode_id 碰撞检测、weighted manifest 输出 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。真实 OXE/RLDS 转换建议加 tensorflow/RLDS 工具（本包为纯 Python 骨架，可在 L2 之后接入）。

## 3. 快速运行

```bash
cd 第8章-开源具身数据集选型与二次加工
python demo_openx_mini.py --out mini_openx.json
python engineering_openx_processor.py --input-dir sample_sources --out-dir out \
    --task-keywords pick --make-sample
python advanced_mix_strategy.py --open out/processed_manifest.json \
    --domain ../第1章-具身数据全链路地基/demo_data --out-dir out --ratio 3
```

## 4. 标准运行结果（本机实测）

L1：
```text
a-0001: ee_delta dim=4 lang=pick cup
b-0002: joint_abs dim=7 lang=place cup on tray <- 需运动学/本体无关化处理
```

L2：
```text
加工完成: 2 条 (需IK/本体无关化处理: 1)
动作空间分布: {'ee_delta': 1, 'joint_abs': 1}
```

L3：
```text
混合清单: 领域 3 + 开源 2 (实际比例 1.5:1, 目标 3.0:1)
episode_id 碰撞: 0 ok
```
> 演示数据量小导致实际比例不足目标——真实项目以"补领域数据或降开源比例"收敛，这正是报告的意义。

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| task-keywords | 无（全量） | 按技能树筛 | 空=不筛选 |
| ratio | 3.0（2~4 可调） | 领域为主 | <1 会被开源淹没 |
| 语言目标字段 | instruction | 统一训练 | 保留原始字段做血缘 |
| 动作登记 | ee_delta/joint_abs | 预训练选末端增量 | joint_abs 需 IK 或本体无关化 |
| 碰撞检测 | 必开 | 多来源合并 | 关闭会静默污染 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 语言字段缺失全空 | 只认 instruction | LANG_KEYS 别名表（本包已含 5 种） |
| 2. 关节角当末端增量用 | 未探测动作空间 | L1/L2 自动登记 + requires_ik 标记 |
| 3. 任务筛选没生效 | 关键词大小写/中英 | 统一 lower()；必要时双语词表 |
| 4. 混合后领域被淹没 | 开源量大 | ratio 权重 + 域标签分层采样 |
| 5. 两个数据集 id 撞车 | 无碰撞检测 | L3 自动拦截并报告 |

## 7. 改造指南

- 真实 OXE 接入：把 RLDS 读取器（官方工具）的输出映射成 `instruction/action_* /success` 即可复用 L2/L3；
- 动作空间转换：joint_abs→ee_delta 需要机器人 URDF/运动学，输出 requires_ik 清单交给第24章适配层；
- 合规：合并前对每个 source 记录 license（第6章脱敏/授权字段可追加到 manifest）。

## 8. 进阶方向

把 L3 混合清单接入第24章"先预训练后领域微调"两阶段训练；用第30章评测协议对比不同 ratio 的领域任务成功率，找到最优混合比。
