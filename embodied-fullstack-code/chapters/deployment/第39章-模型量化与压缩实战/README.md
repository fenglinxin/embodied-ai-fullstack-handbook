# 第39章《模型量化与压缩实战》代码落地包

> 配套文章：【具身智能全栈工程·第39章】INT8/INT4 不是"压一压"那么简单

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_quant_error.py | L1 | INT8/6/4 量化 SNR 对比（41.8/29.2/16.4dB） |
| engineering_layer_quant.py | L2 | 逐层量化误差定位：含离群值的 attention 层最敏感 |
| advanced_mixed_precision.py | L3 | 混合精度贪心：按"单位显存误差收益"选 FP16 层 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_quant_error.py
python engineering_layer_quant.py --make-sample sample
python engineering_layer_quant.py --input sample/layers.json --out-dir out
python advanced_mixed_precision.py
```

## 4. 标准运行结果（本机实测）

L1：INT8 SNR 41.8dB vs INT4 16.4dB（掉点根源可见）

L2：attention_out/q RMSE 0.028 最高 -> 先进混合精度名单

L3：误差预算 0.35 只需把 attention_q 提为 FP16（+30MB）

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 位宽 | 8/6/4 | 按红线选 |
| 离群值 | max-abs scale | 需 percentile |
| ERR_BUDGET | 0.35 | 混合精度目标 |
| FP16 额外 | 0.5B/参数 | 显存账 |

## 6. Top5 踩坑

1. 校准集缺难例：掉点后先修校准集。
2. INT4 直接崩：离群值处理/混合。
3. 全层 INT8 掉点就 QAT：先敏感层。
4. 只算显存不算误差：帕累托。
5. 换框架量化结果不同：以引擎实测。

## 7. 改造指南

- 真实权重来自 checkpoint；
- 分层误差用中间激活余弦/MSE；
- 混合名单喂给 TensorRT 精度模式。

## 8. 进阶方向：SmoothQuant 离群拆分、INT4 权重+高精度激活、量化档案化。
