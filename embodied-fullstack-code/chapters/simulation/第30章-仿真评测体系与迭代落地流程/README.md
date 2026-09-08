# 第30章《仿真评测体系与迭代落地流程》代码落地包

> 配套文章：【具身智能全栈工程·第30章】仿真分数是会骗人的

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_eval_protocol.py | L1 | 评测协议五要素生成器（场景集×样本量×种子×初始分布×判定规则） |
| engineering_regression_runner.py | L2 | 回归基准 runner：逐场景 Δ 对比，超 -5% 标 REGRESSION 并 blocked |
| advanced_simreal_calibration.py | L3 | 仿真-真机锚点线性拟合+Pearson r，r>0.7 才允许用仿真分当筛选器 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_eval_protocol.py
python engineering_regression_runner.py --make-sample sample
python engineering_regression_runner.py --baseline sample/baseline.json --new sample/new.json --out-dir out
python advanced_simreal_calibration.py --make-sample sample
python advanced_simreal_calibration.py --input sample/anchors_pairs.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：6 组合×20 次=120 次评测协议生成

L2：warehouse Δ-0.15 -> REGRESSION -> blocked（防修A坏B）

L3：拟合 real≈0.85*sim-0.15，r=1.0 -> sim-filter-usable

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| EPISODES_PER_SCENE | 20 | 样本量 |
| TOL | 0.05 | 回归容忍 |
| r 阈值 | 0.7 | 仿真筛选器可用性 |
| seeds | 3 组 | 方差估计 |

## 6. Top5 踩坑

1. 只测固定摆位：协议场景集要含变体。
2. 只看平均不看场景：回归逐场景（L2）。
3. 仿真 95% 真机 30%：先做锚点校准（L3）。
4. 评测集过拟合：定期换变体。
5. 无回归基准：改一处毁一片。

## 7. 改造指南

- 协议 JSON 供各训练实验引用；
- 回归 runner 接 CI/发布门禁；
- 校准系数进版本报告，用于仿真分换算。

## 8. 进阶方向：锚点样本自动扩充、分层测试金字塔、评测即文档（每版带报告）。
