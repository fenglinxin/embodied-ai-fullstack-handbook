# 第20章《灵巧手与全身运动控制》代码落地包

> 配套文章：【具身智能全栈工程·第20章】从"夹得住"到"捻得动"

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_grip_force.py | L1 | 两指握力最小需求（质量×摩擦），安全系数概念 |
| engineering_force_distribution.py | L2 | 多指力分配（按权重）、目标力反算、滑觉分级增力(1.15/1.35/1.6) |
| advanced_com_monitor.py | L3 | 全身重心-支撑域监控：多边形内判、内缩安全域、stable/shift-hip/stop |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_grip_force.py
python engineering_force_distribution.py --make-sample sample
python engineering_force_distribution.py --input sample/grasp.json --out-dir out
python advanced_com_monitor.py
```

## 4. 标准运行结果（本机实测）

L1：0.5kg/μ0.3 最小握力 8.18N；μ0.8 仅需 3.07N

L2：min_hold 3.27N -> thumb 1.64/index 0.98/middle 0.65；滑觉后总力 3.76→4.42N

L3：
```text
中立        -> stable
伸手取物      -> shift-hip (边距0.6cm<内缩2cm)
过度前伸(危险)  -> stop-task (CoM越界)
```

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 安全系数 | 1.5~2 | 最小握力×系数 |
| SLIP_STEPS | 1.15/1.35/1.6 | 滑觉分级增力 |
| INSET | 2cm | CoM 安全内缩 |
| 手指权重 | 按接触法向 | 力分配 |

## 6. Top5 踩坑

1. 五指各抓各的：先力分配再逐指执行。
2. 握力只按位置闭环：接触任务要有力/电流目标。
3. 滑觉响应一次加满：应分级（本包 3 档）。
4. 站姿伸手不管重心：CoM 越界会倒——先停任务。
5. 全身优化全任务等权：优先级 平衡>限位>操作。

## 7. 改造指南

- 真手：per_finger 输出按手指运动学映射为关节力矩；
- 触觉滑觉：用电流/触觉事件替换模拟事件；
- 全身：CoM 由多体动力学算（本包为监控/决策层），接 WBC 求解器。

## 8. 进阶方向：力位混合分层控制；滑觉-握力闭环增益调度；WBC 任务零空间投影。
