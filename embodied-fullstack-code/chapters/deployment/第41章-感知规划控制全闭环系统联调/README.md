# 第41章《感知-规划-控制全闭环系统联调》代码落地包

> 配套文章：【具身智能全栈工程·第41章】模块都通，整机乱套

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_contract_audit.py | L1 | 接口契约审计（生产者/消费者/频率/超时/字段） |
| engineering_state_machine.py | L2 | L0-L3 异常分级状态机：lost×3 降级、急停 SAFE_STOP |
| advanced_replay_check.py | L3 | 回放一致性：时间单调/最大间隔/单位统一 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_contract_audit.py
python engineering_state_machine.py
python advanced_replay_check.py --make-sample sample
python advanced_replay_check.py --input sample/replay.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：三个接口契约字段齐全

L2：lost 连续3次 -> DEGRADED；estop -> SAFE_STOP

L3：perception 时间倒流/plan 间隔100ms>80ms -> FAIL 拦截

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 超时 | 50-200ms | 接口契约 |
| L2 触发 | 连续3次 | 降级 |
| MAX_GAP | 80ms | 回放间隔 |
| 单位 | m/mm 统一 | 语义一致 |

## 6. Top5 踩坑

1. 各模块状态各管各：仲裁状态机。
2. 坐标系/单位不一致：三一致检查。
3. 跳过回放直接真机：L3 拦截。
4. 异常没有恢复路径：L2 演练。
5. 修A坏B：回归回放集。

## 7. 改造指南

- 契约表来自架构图（第32/37章）；
- 状态机事件接各模块回调；
- 回放文件=rosbag 转 JSON。

## 8. 进阶方向：状态可视化审计、影子模式切换、启动自检自动化。
