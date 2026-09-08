# 第28章《Sim2Real 核心方案与差异消除》代码落地包

> 配套文章：【具身智能全栈工程·第28章】仿真里99%、真机就1%

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_sysid.py | L1 | 摩擦系数最小二乘辨识（真0.6→估0.589） |
| engineering_dr_robustness.py | L2 | DR 鲁棒性对比：基线 26% vs DR 75%（区间化） |
| advanced_anchor_matrix.py | L3 | 真机锚点迁移矩阵：gap 热力图、优先级与动作建议 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_sysid.py
python engineering_dr_robustness.py
python advanced_anchor_matrix.py --make-sample sample
python advanced_anchor_matrix.py --input sample/anchors.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：辨识 μ=0.589（真 0.6）

L2：基线 26% vs DR 75%（μ∈[0.3,0.9]）

L3：抓马克杯 gap=0.50、推方块 gap=0.40 标 GAP 并排优先级

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| DR 区间 | 0.3-0.9 | 中心=辨识值 |
| GAP_TOL | 0.15 | 锚点容忍 |
| 样本数 | 2000 | 统计意义 |

## 6. Top5 踩坑

1. DR 中心不是真机值：先系统辨识。
2. 零样本一次成功当成功：统计 20-50 次。
3. 只调物理不调感知：矩阵分 动力学/感知/执行 三类。
4. 差距不回流仿真：失败模式→随机化参数。
5. 没做迁移回归：每次改动跑锚点矩阵。

## 7. 改造指南

- 真机实验数据按锚点 JSON 记录；
- DR 参数接第27章采样器；
- 矩阵脚本化接 CI 做"迁移回归自动化"。

## 8. 进阶方向：自动DR(ADR)、影子模式回放、分层迁移（先控制后策略）。
