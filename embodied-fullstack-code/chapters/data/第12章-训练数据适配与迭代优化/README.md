# 第12章《训练数据适配与迭代优化》代码落地包（数据层收官）

> 配套公众号文章：【具身智能全栈工程·第12章】数据不是采完就结束
> 落地目标：失败挖掘 → 补采任务书 → 数据集版本回归 ship/no-ship 决策。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_error_mining.py` | L1 | 100 次评测模拟：失败模式聚类（not_found/occluded/grasp_slip）与失败桶 Top 建议 |
| `engineering_loop_runner.py` | L2 | 失败归因：桶级错误率 + 数据集存量对照 + 业务加权**补采任务书**（loop_report/collection_tasks） |
| `advanced_loop_regression.py` | L3 | 数据集版本回归：总体成功率 Δ + 关键桶错误率 Δ，ship-v1 / collect-more 决策 + 样例生成器 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第12章-训练数据适配与迭代优化
python demo_error_mining.py --out eval_results.json
python engineering_loop_runner.py --eval eval_results.json \
    --dataset dataset_manifest.json --out-dir out
python advanced_loop_regression.py --make-sample sample
python advanced_loop_regression.py --sample-dir sample --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：失败率 24%，Top 模式 not_found×10 / occluded×8，建议补采 kitchen_shadow@pick_cup
L2：
```text
补采 pick_cup@kitchen_shadow: 失败8次 现数据0条 score=8.0
补采 place_cup@kitchen_light: 失败5次 现数据0条 score=7.5
```
L3：
```text
总体成功率: v0=86.7% -> v1=90.0% (Δ+3.3%)
关键桶 warehouse|pick_cup 错误率变化 Δ-12.5%
决策: ship-v1
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| BUSINESS_WEIGHT | place 1.5 / pick 1.0 | 按业务损失定价 | 不填=纯频次排序 |
| priority_score | 失败次数×权重 | 补采排序 | 别忽略数据存量 |
| TOL_BUCKET_REGRESSION | 0.05 | 关键桶退化容忍 | 量产任务收严到 0.02 |
| ship 条件 | 总体升 & 关键桶不退化 | 版本放行 | 只看总体会掩盖桶退化 |
| 评测 trials | ≥100 | 统计意义 | 过少靠运气 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 失败模式没记录 | 采集端没写 failure_mode | 评测器强制字段（L1 结构） |
| 2. 补采补在已经会的桶 | 只看总量不看桶 | L2 用"失败次数-数据存量"双维 |
| 3. 总体涨了关键桶崩了 | 只对比均值 | L3 关键桶容忍判定 |
| 4. 版本对比用的不是同一评测 | trials 不同 | 同一黄金评测集（第30章） |
| 5. 迭代 20 轮没进展 | 无 ship 门禁 | L3 collect-more 止损并回审评测 |

## 7. 改造指南

- 真实接入：eval_results 由第30章自动评测输出；dataset_manifest 用第7章 data_card 的分布段；
- 适配层问题：若全桶失败先查第12章"适配三问"（适配/覆盖/质量），再决定是否补采；
- 训练引用：版本回归通过后记录 数据集版本+模型版本+评测版本 三元组（文章要求）。

## 8. 进阶方向（数据层完结）

把 L2 补采任务书自动派发到第2章采集工位；L3 回归接入第11章发布门禁节点，形成 采→检→练→评→补 的完全自动闭环。
