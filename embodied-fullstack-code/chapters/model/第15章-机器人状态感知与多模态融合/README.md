# 第15章《机器人状态感知与多模态融合》代码落地包

> 配套公众号文章：【具身智能全栈工程·第15章】机器人不仅要"看世界"，还要"感知自己"
> 落地目标：1D 卡尔曼直观 Demo、双状态(位置+速度)矩阵 KF、模态消融与掉线分析。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_kalman1d.py` | L1 | 一维卡尔曼：正弦真值+高斯噪声，滤波前后误差对比（1.7× 降噪） |
| `engineering_state_estimator.py` | L2 | 常速模型矩阵卡尔曼（pos+vel）：joint→位置更新、imu→速度更新、按源配 R，输出 RMSE 报告 |
| `advanced_modality_ablation.py` | L3 | both/joint-only/imu-only 消融 + 测量间隙（掉线）检测 + 降级建议 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第15章-机器人状态感知与多模态融合
python demo_kalman1d.py
python engineering_state_estimator.py --make-sample sample
python engineering_state_estimator.py --input sample/measurements.json --out-dir out
python advanced_modality_ablation.py --input sample/measurements.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：原始误差 0.849 → 卡尔曼 0.490（**降噪 1.7×**）
L2：
```text
估计点数 90 RMSE_pos=0.0003 RMSE_vel=0.0115
```
L3：
```text
both        RMSE_pos=0.0003 RMSE_vel=0.0115
joint_only  RMSE_pos=0.0004 RMSE_vel=None (无速度源)
imu_only    RMSE_pos=None   RMSE_vel=0.0128
掉线间隙: joint max=0.05s / imu max=0.1s（无>0.5s 掉线）
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| R.joint | 1e-4 | 高精度编码器 | 打滑场景调大 |
| R.imu | 1e-2 | 通用 IMU 速度 | 振动大场景调大 |
| Q_SCALE | 1e-4 | 常速模型 | 加减速频繁需加速度模型 |
| dt | 按时间戳 | 非等间隔测量 | 勿假设固定周期 |
| 掉线阈值 | 0.5s | 降级触发 | 控制频率高时收紧 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 滤波比原始还差 | Q/R 与信号不匹配 | 用噪声实测标定 Q/R（L1 调参经验） |
| 2. 速度 RMSE 巨大 | 拿位置真值比速度 | truth_pos/truth_vel 分字段（本包已修） |
| 3. 缺一路就崩 | 无降级 | L3 掉线检测+保守模式 |
| 4. 协方差越算越乱 | 手推公式错 | 用矩阵乘法统一实现（L2） |
| 5. imu 掉线位置仍漂 | 无位置源兜底 | 视觉/轮速融合（文章多源方案） |

## 7. 改造指南

- 真实通道：把 measurements.json 换成驱动输出的 joint/imu 时间戳流；
- 加轮速/视觉位姿：在 run_filter 中按 kind 扩展 H 与 R（如 kind="pose"）；
- 量产：估计输出带协方差置信度，超过阈值触发重定位（文章）。

## 8. 进阶方向

升为 6D 姿态 EKF（四元数状态+陀螺预测+加速度/视觉更新）；把消融自动化接入第30章评测，量化每路传感的边际贡献。
