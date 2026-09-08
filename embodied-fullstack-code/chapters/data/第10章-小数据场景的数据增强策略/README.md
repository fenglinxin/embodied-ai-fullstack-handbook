# 第10章《小数据场景的数据增强策略》代码落地包

> 配套公众号文章：【具身智能全栈工程·第10章】只有 300 条数据怎么训机器人？
> 落地目标：L1 观测扰动保真校验、L2 可配置增强流水线、L3 增强 A/B 评测骨架。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_augment.py` | L1 | 灰度矩阵 亮度/对比度/噪声 三类扰动 + "身份边界"校验 + 动作不扰动红线 |
| `engineering_augment_pipeline.py` | L2 | 可配置增强目录与参数区间、按 Episode 批量生成变体、逐变体 mean-delta 越界门禁、manifest+report |
| `advanced_augment_ab.py` | L3 | 策略 A/B：invariance（守真）与 diversity（增量）双代理指标，baseline 对比 + 真模型评测接入点 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第10章-小数据场景的数据增强策略
python demo_augment.py
python engineering_augment_pipeline.py --input-dir sample --out-dir out \
    --augments-per-episode 6 --make-sample
python advanced_augment_ab.py --input-dir sample --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：
```text
brightness+20   +20.0  OK
contrast*1.2    +31.0  OK
noise_sigma5    +0.7   OK
动作通道不参与扰动（物理语义红线）。
```

L2：
```text
生成增强变体 12 个，越界 0 个
```

L3（A/B 排序）：
```text
brightness     invariance=0.941 diversity=15.9 score=0.6440
mix            invariance=0.954 diversity=13.1 score=0.6381
contrast       invariance=0.985 diversity=4.0  score=0.6109
noise          invariance=0.999 diversity=0.4  score=0.6014
baseline_none  invariance=1.000 diversity=0.0  score=0.6000
建议: 优先保留 brightness（代理分最高；最终以真模型评测为准）
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| brightness_range | ±25 | 通用 | 超过 ±50 会破坏身份 |
| contrast_range | 0.85~1.25 | 通用 | >1.6 高光截断失真 |
| noise_sigma_max | 6.0 | RGB 灰度 | 彩色需按通道同种子 |
| max_mean_delta | 45.0 | 身份门禁 | 小物体应更严 |
| w_invariance | 0.6 | 代理A/B | 真模型评测优先于代理 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 增强后模型更差 | 扰动越界/动了动作 | 打开身份门禁；动作通道只读 |
| 2. 噪声加太大看不出物体 | sigma 无上限 | noise_sigma_max 收敛到 3~6 |
| 3. A/B 分不出胜负 | 评测集与增强维度无关 | 用探针任务（新光照/新位置） |
| 4. 变体间重复度高 | 种子固定复用 | 每 Episode 不同种子/记录种子 |
| 5. 只增图像不增物理变化 | L1 局限 | 补 L2 参数变体/仿真（第10章层级） |

## 7. 改造指南

- 真实图像：把矩阵换成 numpy/OpenCV 通道；或把本包作为"纯 Python 参考实现"后用 Pillow/OpenCV 加速；
- 加策略：在 L2 `apply_op` 与 L3 `generate` 同步加（如 平移/缩放需保持标定一致）；
- 真模型 A/B：替换 L3 `run_model_eval()` 为你的黄金评测成功率即可。

## 8. 进阶方向

与第12章失败挖掘联动：按模型失败场景定向增强（失败位置 ±、失败光照 ±），把增强预算花在"不会的"桶上；增强配方按第30章评测协议沉淀。
