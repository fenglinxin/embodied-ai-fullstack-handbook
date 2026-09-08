# 第37章《上下位机架构与实时性设计》代码落地包（硬件层收官）

> 配套文章：【具身智能全栈工程·第37章】智能是"上"出来的，命是"下"保的

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_latency_budget.py | L1 | 端到端延迟预算表（感知/规划/通信/控制） |
| engineering_failsafe.py | L2 | 指令超时看门狗→安全停车模拟（50ms 超时/200ms 斜坡） |
| advanced_jitter_monitor.py | L3 | 通信抖动监控：P50/P99/Max vs 周期 20% 预算 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_latency_budget.py
python engineering_failsafe.py
python advanced_jitter_monitor.py --make-sample sample
python advanced_jitter_monitor.py --input sample/latency_ms.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：合计 57ms < 预算 80ms 达标

L2：t=300ms 断连 -> 看门狗触发 -> 200ms 安全停稳

L3：P99=8.57ms > 周期20%(2ms) -> 超预算告警（RT 调优建议）

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 端到端预算 | 80ms | 按任务 |
| WATCHDOG | 50ms | 指令过期 |
| STOP_RAMP | 200ms | 安全停车 |
| 抖动预算 | 周期20% | P99 口径 |

## 6. Top5 踩坑

1. 控制等 AI：实时层绝不阻塞。
2. 指令迟到当新指令：过期丢弃。
3. 安全链依赖上位机：独立回路。
4. 只看平均延迟：P99 抖动。
5. 上下位机时间不对：PTP。

## 7. 改造指南

- 延迟表来自各模块实测；
- 看门狗接入真机安全回路；
- 抖动日志来自 DDS 遥测。

## 8. 进阶方向：影子模式热切换、状态机下沉、链路ID全链路追踪。
