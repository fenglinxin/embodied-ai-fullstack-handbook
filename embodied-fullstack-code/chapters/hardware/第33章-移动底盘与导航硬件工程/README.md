# 第33章《移动底盘与导航硬件工程》代码落地包

> 配套文章：【具身智能全栈工程·第33章】底盘选错，导航白做

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_odom_calib.py | L1 | 里程计直行/旋转比例标定计算 |
| engineering_chassis_accept.py | L2 | 六项验收实验记录器（漂移/旋转/阶跃/颠簸/电流/续航） |
| advanced_slip_fusion.py | L3 | 轮速-IMU 打滑检测与融合（打滑切 IMU 积分） |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_odom_calib.py
python engineering_chassis_accept.py --make-sample sample
python engineering_chassis_accept.py --input sample/results.json --out-dir out
python advanced_slip_fusion.py
```

## 4. 标准运行结果（本机实测）

L1：直行比例 1.0417、旋转轮距 1.0286

L2：六项中 bump_pulse_loss=2 未达标 -> 拦截（门禁示例）

L3：
```text
纯轮速误差 110cm；融合误差 -1.0cm（打滑50次被正确检测）
```

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 直行漂移 | <2cm/10m | 标定验收 |
| 旋转误差 | <2° | 标定验收 |
| SLIP_TH | 0.3 m/s | 轮速-IMU 矛盾阈值 |
| 续航 | ≥2h | 满载 |

## 6. Top5 踩坑

1. 换轮/胎后不重标：L1 重跑。
2. 过减速带丢脉冲没人管：验收 bump 项。
3. 打滑还信轮速：L3 融合检测。
4. 只看平均功耗选电池：按峰值。
5. 全向轮不清缠线：维护项。

## 7. 改造指南

- 标定数据来自真机直行/旋转测试；
- 验收结果接第43章监控；
- 融合器输出 odom 供第17章导航。

## 8. 进阶方向：多源EKF（轮速+IMU+视觉/激光）、打滑自适应降速、底盘健康监控。
