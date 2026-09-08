# 第36章《标定、线缆与可靠性工程》代码落地包

> 配套文章：【具身智能全栈工程·第36章】量产机器人的命是"标定+线缆+可靠性"给的

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_calib_gate.py | L1 | 标定版本门禁：无版本=没标定，缺项拦截 |
| engineering_factory_qa.py | L2 | 出厂直通率 + 故障 Pareto（Top2 进设计/工艺改进） |
| advanced_env_matrix.py | L3 | 环境试验矩阵（温度×电压×振动 27 组合）边界筛选 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_calib_gate.py
python engineering_factory_qa.py --make-sample sample
python engineering_factory_qa.py --input sample/units.json --out-dir out
python advanced_env_matrix.py --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：cam_intrinsic 无版本被拦

L2：直通率 70%，Pareto Top=线缆松脱/标定散差

L3：27 组合中 3 组失败（50°C×90%电压）→ 边界筛选

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 直通率目标 | ≥90% | 出厂门禁 |
| Pareto | Top2 | 改进闭环 |
| 环境级别 | 温度20-50/电压90-110%/振动0.5-2g | 按规格 |

## 6. Top5 踩坑

1. 每台手调标定：流程化+版本入库。
2. 故障当个案：Pareto 闭环（L2）。
3. 只做常温测试：环境矩阵边界。
4. 线缆半年断：线束管理+快换。
5. 出厂无老化：早期失效率。

## 7. 改造指南

- 标定清单来自产线工装；
- 出厂数据自动入 QA 系统；
- 环境矩阵按目标市场标准扩展（IP/盐雾等）。

## 8. 进阶方向：标定数据上云、环境试验 DOE、浴盆曲线放量决策。
