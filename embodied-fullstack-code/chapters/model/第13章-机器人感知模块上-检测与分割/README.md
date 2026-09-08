# 第13章《机器人感知模块（上）：检测与分割》代码落地包

> 配套公众号文章：【具身智能全栈工程·第13章】机器人的"眼睛"和 CV 竞赛不一样
> 落地目标：检测定位最小机制 + 工业评测（mAP/P/R/F1/延迟）+ 真机稳定性体检。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_color_detector.py` | L1 | 阈值化+8-连通域 BFS → bbox，讲清"检测=定位+分类"最小机制 |
| `engineering_detection_eval.py` | L2 | 任意检测器输出评测：IoU≥0.5 匹配、逐类 AP/P/R/F1、mAP、延迟 P50/P95（含样例生成器） |
| `advanced_perception_ops.py` | L3 | 真机感知体检：连续帧中心抖动（mean/P95）、丢失帧（闪烁）、EMA 平滑前后对比 |
| `sample_seq_pred.json` | 数据 | L3 静态时序样例（5 帧，含 1 帧丢失） |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。接真实模型：YOLO/RT-DETR 输出转成 `{image_id,class,bbox,conf,latency_ms}` 即可复用 L2。

## 3. 快速运行

```bash
cd 第13章-机器人感知模块上-检测与分割
python demo_color_detector.py
python engineering_detection_eval.py --make-sample sample
python engineering_detection_eval.py --gt sample/gt.json --pred sample/pred.json --out-dir out
python advanced_perception_ops.py --input sample_seq_pred.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：检测到高灰度连通域 bbox=(12,10,5x12) 像素=60
L2：
```text
mAP: 0.445
  mug: AP=0.889 P=0.667 R=1.0 F1=0.8 (TP2/FP1/FN0)
  box: AP=0.0 (FN1：把 box 错检成 mug 的代价)
延迟ms: p50=13.0 p95=14.0
```
L3：
```text
帧数 5 丢失帧 1
原始抖动 mean=2.0px p95=2.8px；EMA后 mean=1.57px p95=2.25px
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| IOU_TH | 0.5 | mAP 通用口径 | 精密抓取评测用 0.75 |
| conf 排序 | 降序 | AP 计算 | 缺失 conf 需补 |
| EMA_ALPHA | 0.5 | 框平滑 | 动态目标用 0.6-0.7 |
| 阈值化（L1） | 180 | 教学演示 | 真实场景禁用纯阈值 |
| 抖动告警 | mean>5px | 静止目标 | 移动目标按速度归一 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. mAP 高真机漏检 | 评测集视角单一 | 加真机斜视/遮挡回归集 |
| 2. 框在视频里跳 | 无时序约束 | L3 EMA/跟踪 |
| 3. FP 全集中某类 | 类别不平衡 | 补该类负样本/难例 |
| 4. 缺 conf 无法算 AP | 推理未输出 | 检测器输出带 conf 字段 |
| 5. 帧率够但延迟抖动大 | 只看平均 | 报告 P95/P99 |

## 7. 改造指南

- 接 YOLO：把模型输出批量转 JSON（image_id/class/bbox/conf/latency_ms）后直接跑 L2；
- 抓取场景：bbox 下游接第14章位姿/第18章抓取点；
- 量产回归：L3 报告接入第43章监控，每版模型跑同一时序样本集。

## 8. 进阶方向

检测+跟踪（ByteTrack）一体化降低框跳变；状态（空/满杯）拆分做进类别；把 L2 评测接入第30章黄金评测协议，让感知与整机成功率联动。
