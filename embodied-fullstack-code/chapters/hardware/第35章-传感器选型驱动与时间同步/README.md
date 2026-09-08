# 第35章《传感器驱动与时间同步》代码落地包

> 配套文章：【具身智能全栈工程·第35章】传感器不是"插上就能用"

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_bandwidth.py | L1 | 相机带宽预算（1080p30≈498Mbps），余量纪律 |
| engineering_driver_check.py | L2 | 驱动接入六项检查（枚举/帧率/硬件时间戳/单位/供电/自动恢复） |
| advanced_sync_accept.py | L3 | 事件法同步验收：偏差中位/抖动/常数补偿建议 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_bandwidth.py
python engineering_driver_check.py --make-sample sample
python engineering_driver_check.py --input sample/sensors.json --out-dir out
python advanced_sync_accept.py --make-sample sample
python advanced_sync_accept.py --input sample/events.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：合计 608Mbps，USB3 余量 81%

L2：rgb_cam 缺 auto_recover 被拦（自动恢复是量产必备）

L3：rgb 偏差 7.3ms/抖动 0.3ms；depth 11.3ms/0.3ms -> PASS（补偿可写配置）

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 带宽占用 | ≤70-80% | 总线预算 |
| 六项检查 | 全 True | 驱动门禁 |
| MAX_JITTER | 2ms | 抖动容忍 |
| 常数补偿 | 偏差中位 | 对齐配置 |

## 6. Top5 踩坑

1. USB 顶格用：多相机丢帧（L1）。
2. 时间戳用到达时间：要求驱动硬件戳。
3. 掉线不恢复：auto_recover 检查（L2）。
4. 换了驱动延迟变：重跑 L3 事件法。
5. 常数偏差不补偿：只查抖动不查中位。

## 7. 改造指南

- 带宽表用真实相机参数；
- 驱动清单由各驱动自检脚本填充；
- 事件数据来自 LED/敲击同步实验。

## 8. 进阶方向：触发线同步相机、PTP 网络时钟、传感器抽象层统一接口。
