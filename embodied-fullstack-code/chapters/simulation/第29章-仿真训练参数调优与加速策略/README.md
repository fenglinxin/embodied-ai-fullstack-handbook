# 第29章《仿真训练参数调优与加速》代码落地包

> 配套文章：【具身智能全栈工程·第29章】训练一天只够别人一小时

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_throughput.py | L1 | 训练产能估算（步速×并行×利用率）→ 小时数 |
| engineering_hyper_search.py | L2 | 小网格超参搜索（lr×entropy×envs，固定预算+种子） |
| advanced_train_monitor.py | L3 | 训练监控：reward 平线/entropy 崩塌/成功率≈0，early-fail 判定 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_throughput.py
python engineering_hyper_search.py
python advanced_train_monitor.py --make-sample sample
python advanced_train_monitor.py --input sample/healthy.json --out-dir out
python advanced_train_monitor.py --input sample/flat.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：1env=15.4h vs 64env=0.2h vs 256env≈0h（并行威力）

L2：18 组最优 lr=3e-4/ent=0/envs=128，success 99.1%

L3：healthy=healthy；flat 触发 2 条告警 -> early-fail

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| lr 网格 | 1e-4~1e-3 | 以 3e-4 为中心 |
| entropy | 0/0.01/0.1 | 探索-稳定 |
| envs | 32/128 | GPU 并行 |
| 早期判定 | 2 条告警 | 15 分钟止损 |

## 6. Top5 踩坑

1. 先调参再提吞吐：先并行/渲染优化。
2. 超参一次全改：单变量+固定预算。
3. 只看 loss 不看成功率：用任务成功率决策。
4. entropy 崩了还硬跑：early-fail。
5. 种子不固定：实验不可比。

## 7. 改造指南

- 真实训练：simulate() 换成真训练+评测；
- 监控接 wandb/MLflow 日志；
- throughput 参数按实际框架 benchmark 填写。

## 8. 进阶方向：Optuna 搜索、异步采样训练、课程学习、训练-仿真-真机三角回归。
