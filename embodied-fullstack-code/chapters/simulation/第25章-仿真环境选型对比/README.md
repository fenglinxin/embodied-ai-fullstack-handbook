# 第25章《仿真环境选型对比》代码落地包

> 配套文章：【具身智能全栈工程·第25章】Isaac、MuJoCo、Gazebo……到底选哪个

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_physics_dt.py | L1 | 物理步长与穿透关系（dt=0.1→48mm 穿透；0.005→1.5mm） |
| engineering_sim_scorer.py | L2 | 五维画像×任务权重打分（画像可编辑），输出推荐与排序 JSON |
| advanced_smoke_harness.py | L3 | 30 分钟冒烟自动化：Python/GPU/mujoco/URDF 素材探测报告 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_physics_dt.py
python engineering_sim_scorer.py --task vision_manip --out-dir out
python engineering_sim_scorer.py --task rl --out-dir out
python advanced_smoke_harness.py --asset-dir . --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：dt=0.1→穿透48mm / 0.02→8.9mm / 0.005→1.5mm

L2（内置画像，供编辑）：rl 任务排序 isaac 8.45 > mujoco 7.65 > genesis 7.05

L3：python PASS；nvidia-smi/mujoco WARN（未安装=按选型装）

## 5. 参数白皮书

| 参数 | 说明 |
| PROFILES 画像 | 官方文档复核后编辑（0-10） |
| WEIGHTS | 任务权重（rl/vision/nav/dexterous 预设） |
| dt | 接触任务 1ms 级 |

## 6. Top5 踩坑

1. 只看渲染宣传：物理/RL 接口/许可都要画像。
2. 画像不更新：按官方最新文档维护。
3. 贪大 dt 快：接触任务穿透（L1 演示）。
4. 一个仿真器打天下：多仿真器组合常见。
5. 跳过冒烟直接全量迁移：先跑 L3 再决策。

## 7. 改造指南

- 编辑 PROFILES 成你的需求（或从 JSON 加载）；
- 冒烟项按你的候选仿真器扩展 import 检查；
- 通过 L2/L3 后再做第26章场景搭建。

## 8. 进阶方向：多仿真器组合策略（算法MuJoCo/视觉Isaac/联调Gazebo）、物理校准实验集。
