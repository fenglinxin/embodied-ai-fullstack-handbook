# 第27章《仿真传感器与虚拟数据生成》代码落地包

> 配套文章：【具身智能全栈工程·第27章】仿真数据为什么"一眼假"

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_sensor_noise.py | L1 | 相机噪声合成（高斯+椒盐坏点），均值/分布变化观察 |
| engineering_dr_sampler.py | L2 | 域随机化参数采样器：亮度/对比度/噪声/摩擦/尺寸/相机倾角，种子可复现 Manifest |
| advanced_dist_compare.py | L3 | 虚拟-真机直方图对比：交叠度与均值差，gap 触发调噪建议 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_sensor_noise.py
python engineering_dr_sampler.py --n 10 --out out
python advanced_dist_compare.py --make-sample sample
python advanced_dist_compare.py --sim sample/sim_hist.json --real sample/real_hist.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：含椒盐噪声图均值基本不变但像素分布变宽（只看均值会骗人）

L2：10 组参数含 seed，范围 亮度±30/噪声0-8/摩擦0.3-0.9 等

L3：直方图交叠 0.601 < 0.7 -> gap-needs-noise-tuning（提示调 L2 参数）

## 5. 参数白皮书

| 参数 | 默认范围 | 说明 |
| brightness_delta | ±30 | 光照扰动 |
| noise_sigma | 0-8 | 相机噪声 |
| friction | 0.3-0.9 | 接触随机 |
| camera_tilt_deg | ±3 | 标定误差鲁棒 |
| 直方图阈值 | 0.7 | 分布可接受线 |

## 6. Top5 踩坑

1. 只调均值不调分布：看直方图（L3）。
2. 随机范围乱开：物理语义不能随。
3. 未记录 seed：不可复现。
4. 仿真噪声与真机统计脱节：用真机短录统计标定噪声参数。
5. 对比只用一种指标：交叠度+均值差+失败模式。

## 7. 改造指南

- 真实深度：把 L1 噪声模型换成你相机规格+短录统计；
- DR 参数表按第26章变量矩阵配置；
- L3 接第28章真机锚点迁移评测。

## 8. 进阶方向：课程式DR（前期小范围后期拉大）、真机统计驱动噪声建模、对抗难例DR。
