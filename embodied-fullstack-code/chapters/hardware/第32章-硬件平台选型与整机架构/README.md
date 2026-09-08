# 第32章《硬件平台选型与整机架构》代码落地包

> 配套文章：【具身智能全栈工程·第32章】先选算法再买硬件

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_form_decision.py | L1 | 任务特征→形态打分（含过配置惩罚），桌面抓取推荐固定臂 |
| engineering_budget_calc.py | L2 | 算力/显存/带宽/峰值功耗/电池 Wh 预算计算器 |
| advanced_arch_audit.py | L3 | 整机接口审计：带宽/功耗超限与字段缺失检查 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_form_decision.py
python engineering_budget_calc.py --make-sample sample
python engineering_budget_calc.py --config sample/budget.json --out-dir out
python advanced_arch_audit.py --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：固定臂 5.2 > 移动+臂 1.2 > 人形 -6.2（过配惩罚生效）

L2：VRAM 11.2GB、峰值功率 897W、电池 1350Wh

L3：带宽 700/1600Mbps OK、功耗 717/800W OK，但 arm_ctrl 缺字段被拦截

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 过配惩罚 | 0.2 | 形态不要过度设计 |
| vram_headroom | 1.25 | 显存余量 |
| power_headroom | 1.3 | 峰值余量 |
| BUS/POWER 预算 | 1600Mbps/800W | 按平台改 |

## 6. Top5 踩坑

1. 需求没量化就买：先 L1 打分。
2. 先买卡再定模型：L2 预算表先行。
3. 按平均功耗选电池：按峰值+余量。
4. 接口清单缺字段：L3 审计拦。
5. 形态越复杂越酷：成本/故障率惩罚。

## 7. 改造指南

- 形态画像按你的任务改；
- budget.json 填真实模型/传感器数据；
- 架构清单来自第37章接口契约表。

## 8. 进阶方向：平台化多SKU、数字孪生先行验证、量产DFM前置。
