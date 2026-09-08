# 第34章《机械臂、灵巧手与驱动器调试》代码落地包

> 配套文章：【具身智能全栈工程·第34章】"指哪打哪"是调出来的

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_tcp_calib.py | L1 | TCP 四点法最小实现（旋转矩阵求逆+平均） |
| engineering_precision_analyzer.py | L2 | 重复精度/背隙/绝对误差分析（正反逼近区分） |
| advanced_hand_debug.py | L3 | 灵巧手自由度清单自检 + 滑觉分级增力联动 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_tcp_calib.py
python engineering_precision_analyzer.py --make-sample sample
python engineering_precision_analyzer.py --input sample/trials.json --out-dir out
python advanced_hand_debug.py
```

## 4. 标准运行结果（本机实测）

L1：四点法标定出 TCP（示例数据验证流程，真机用实测法兰位姿）

L2：repeatability 0.45mm / backlash 0.81mm / 绝对误差 0.75mm

L3：index_PIP 与 ring_PIP 反馈异常被检出（2 个关节 ERR）

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| DOF_TOL | 0.05 rad | 关节反馈容忍 |
| GRIP_STEP | 1.3 | 滑觉增力档 |
| 背隙判据 | fwd-rev 差 | 需补偿 |

## 6. Top5 踩坑

1. 换工具不重标 TCP：版本化门禁。
2. 背隙当绝对误差调：先分 fwd/rev。
3. 灵巧手某指没力：单指自检（L3）。
4. 滑觉一次加满握力：分级。
5. 精度问题先查机械：螺丝/背隙。

## 7. 改造指南

- 四点法用真实法兰位姿（激光/千分表）；
- 精度 trials 由自动到位实验生成；
- 手驱动反馈来自各指编码器/电流。

## 8. 进阶方向：自动标定工装、热漂移补偿、精度护照出厂报告。
