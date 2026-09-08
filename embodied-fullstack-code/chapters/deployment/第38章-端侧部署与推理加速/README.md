# 第38章《端侧部署与推理加速》代码落地包

> 配套文章：【具身智能全栈工程·第38章】模型"能跑"和"能实时跑"是两回事

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_waterfall.py | L1 | 延迟瀑布剖析：60% 在模型推理 -> 先优化瓶颈 |
| engineering_engine_bench.py | L2 | 引擎基准：P50/P99/显存/精度 vs 预算（推荐 tensorrt_int8） |
| advanced_soak_monitor.py | L3 | 长跑稳定性：显存泄漏/PP99 漂移检测 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_waterfall.py
python engineering_engine_bench.py --out-dir out
python advanced_soak_monitor.py --make-sample sample
python advanced_soak_monitor.py --input sample/soak.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：模型推理 45ms 占 60% -> 首要优化目标

L2：tensorrt_int8（11/16ms、0.6GB、acc0.97）通过预算

L3：显存漂移 0.49MB/分 + P99 漂移 2.4ms -> leak-or-drift

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| p99 预算 | 20ms | 任务定 |
| 显存预算 | 1.2GB | 平台定 |
| LEAK_MA | 0.02MB/分 | 泄漏判定 |
| 精度底线 | 0.97 | 红线 |

## 6. Top5 踩坑

1. 只看平均延迟：P99。
2. 预处理在 CPU：移到设备。
3. 显存每帧分配：池化。
4. 引擎 fallback 算子：看日志。
5. 长跑不测：泄漏/降频。

## 7. 改造指南

- 瀑布各段接真实计时；
- 引擎数据来自本机 benchmark；
- soak 日志来自部署遥测。

## 8. 进阶方向：多模型共享上下文、模型-引擎联合编译、部署实验室回归。
