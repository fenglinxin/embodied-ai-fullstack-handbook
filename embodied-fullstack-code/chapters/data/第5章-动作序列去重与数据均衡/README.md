# 第5章《动作序列去重与数据均衡》代码落地包

> 配套公众号文章：【具身智能全栈工程·第5章】500 条"复制粘贴"不如 50 个场景各 10 条
> 落地目标：轨迹指纹去重（限定 task×scene 桶）、失败样本保护、欠覆盖补采清单、分层采样权重。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_dedup_balance.py` | L1 | 17 条合成轨迹（含微抖动重复+失败样本），桶内指纹去重+失败保护 |
| `engineering_dedup_balance.py` | L2 | 可配量化桶/失败保留数/桶上下限；输出 dedup_manifest + 欠覆盖报告 |
| `advanced_balance_sampling.py` | L3 | 逆频分层采样权重（限幅3.0）、熵均衡度、train_manifest.csv 训练直用 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第5章-动作序列去重与数据均衡
python demo_dedup_balance.py --out records.json
python engineering_dedup_balance.py --input records.json --out-dir out
python advanced_balance_sampling.py --input out/dedup_manifest.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：
```text
去重: 17 -> 6 (冗余 11)
失败样本保护: 去重前后失败数 3 -> 2
task×scene 分布(前->后):
  ('pick', 'scene_0'): 5 -> 2
  ('place', 'scene_1'): 4 -> 2
```

L2（含"去重必须限定桶"的工程修正）：
```text
去重: 17 -> 7 (冗余 10)
失败样本: 3 -> 3 (保护生效)
欠覆盖组合: 3 个 -> 建议补采
   {'task': 'pick', 'scene': 'scene_2', 'count': 1}
   {'task': 'place', 'scene': 'scene_1', 'count': 2}
   {'task': 'place', 'scene': 'scene_3', 'count': 1}
```

L3：
```text
train_manifest: 7 条 / 4 桶 均衡度=0.9212
最小桶=1 -> 建议先补采小桶，训练期分层采样只能兜底
输出: out\train_manifest.csv
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| quant | 0.02（米/弧度） | 通用 | 精密任务 0.005–0.01 |
| keep_failures_per_group | 2 | 通用 | 全失败组可放宽 |
| min_per_bucket | 3 | 小数据起步 | 项目按任务×物体≥10 |
| max_per_bucket | 10 | 防"同一故事讲50遍" | 先粗去重再调 |
| WEIGHT_CAP | 3.0 | 欠采桶加权 | 过高会过拟合小桶 |
| 分组键 | task+scene+指纹 | 防跨场景误删 | 禁止只用动作指纹 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 去重把场景多样性删了 | 只按动作指纹分组（本包初版真实踩坑） | 分组键=task+scene+指纹 |
| 2. 失败样本被删 | 同组多失败只留 1 | L2 keep_failures_per_group=2 |
| 3. 量化桶太小=没去重 | 噪声让指纹全不同 | quant 按采集噪声放大 |
| 4. 欠覆盖没发现 | 无分布报告 | L2 自动输出补采任务单 |
| 5. 加权采样过拟合小桶 | weight_cap 无限 | 限幅 3.0 + 优先补采 |

## 7. 改造指南

- 轨迹为关节序列：直接替换 trajectory 数据即可；更高精度可换 DTW（见文章，建议接 `tslearn` 时在本包外加层）；
- 真实补采闭环：把 L2 under_covered 转成第2章采集任务书；
- 训练接入：L3 CSV 直接供 PyTorch WeightedRandomSampler / TF sample_weight。

## 8. 进阶方向

接入第12章失败挖掘：把模型失败桶的权重再上调一档；把 L3 均衡度纳入第9章质量报告作为"多样性"维度量化指标。
