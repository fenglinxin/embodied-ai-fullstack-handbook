# 第4章《数据清洗与脏数据过滤》代码落地包

> 配套公众号文章：【具身智能全栈工程·第4章】清洗不是"删脏东西"
> 落地目标：P0/P1/P2 三级规则、清洗流水线、以及"过度清洗防护"三道闸。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_cleaning_rules.py` | L1 | 8 条合成记录，演示 损坏删/语义送人工/困难样本必须留 的分级 |
| `engineering_cleaning_pipeline.py` | L2 | 规则化批量清洗（P0删/P1人工/P2保留）、分布对比、cleaned_manifest/removed 双报告、CI 退出码 |
| `advanced_overclean_guard.py` | L3 | 过度清洗防护：桶保底、失败样本保底、task 分布漂移 KL 审计 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第4章-数据清洗与脏数据过滤
python demo_cleaning_rules.py --out records.json
python engineering_cleaning_pipeline.py --input records.json --out-dir out
python advanced_overclean_guard.py --input records.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：
```text
episode_id 级别      原因
ep-0001   P0_DROP   黑帧30%>5%
ep-0002   P0_DROP   时间戳非单调
ep-0004   P1_FLAG   成功标记与末端位置矛盾(送人工)
ep-0005   P2_KEEP   失败样本-保留进困难池
保留 4/8；P0 物理损坏删除，P1 送人工，P2 困难样本必须留。
```

L2：
```text
清洗统计: 总数8 -> 保留4 (P0删除3, P1人工1)
分布变化: task {'pick': 5, 'place': 3} -> {'pick': 2, 'place': 2}
失败样本: 1 -> 1 (困难池保护=True)
```

L3（重点：规则之外的保护闸）：
```text
过洗防护: 规则删除后自动恢复 1 条 (桶保底+失败保底), 最终 6 条
task 分布漂移 KL=0.03158 失败占比=0.1667
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| black_ratio_max | 0.05 | 固定工位 RGB | 先修曝光再收紧 |
| action_empty_max | 0.80 | 通用 | 长任务空段按片段截断而非整删 |
| flag_on_inconsistent | True | 有末端位姿记录时 | 无位姿先验请关掉防误标 |
| keep_failures | True | 全场景 | 关掉=自毁泛化 |
| min_bucket(L3) | 1 | 小数据 | 大数据按任务×物体≥10 |
| min_failure_ratio(L3) | 0.10 | 通用 | 困难任务按第5章上调 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 清洗后模型变差 | 规则误删难例/多样性 | 开 L3 防护闸并看分布漂移 KL |
| 2. 同批数据两次清洗结果不同 | 规则无版本 | 规则配置+版本号入库（本包 config 化） |
| 3. 失败样本被"均衡"删掉 | 过滤条件含 success=False | keep_failures=True 强制保护 |
| 4. 空动作整段误删 | 阈值过低 | action_empty_max 按片段统计后重试 |
| 5. L2 退出码 1 阻塞流水线 | 正常拦截 | CI 中 P0 删除即为拦截目标，修复数据后重跑 |

## 7. 改造指南

- 真实数据接入：把采集数据汇总为记录卡（字段见 synthetic_records），清洗规则函数 `decide()` 可无限扩展；
- 自定义规则：在 L2 `decide()` 增加"力传感零漂/深度NaN"等分支，reasons 自动进报告；
- 规则 A/B：L3 报告中的分布漂移 KL 可作为"清洗影响"量化指标，接入第9章质量门禁。

## 8. 进阶方向

与第9章质量打分打通：清洗规则命中记录直接生成质量分扣分项；与第12章闭环打通：清洗剔除清单自动生成"补采/修复任务单"。
