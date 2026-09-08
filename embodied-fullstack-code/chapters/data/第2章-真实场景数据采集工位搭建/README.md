# 第2章《真实场景数据采集工位搭建》代码落地包

> 配套公众号文章：【具身智能全栈工程·第2章】真机数据采集工位搭建全攻略
> 落地目标：把"首 100 条 Episode 验收 SOP / 多操作者一致性 / 采集漂移监控"变成可运行代码。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_capture_acceptance.py` | L1 | 模拟 100 条采集会话并按验收清单（总数/成功率/失败占比/场景/通道）逐项打钩 |
| `engineering_capture_acceptance.py` | L2 | 读取真实采集记录 JSON，七项门禁+失败原因归因+JSON 报告+CI 退出码 |
| `advanced_capture_ops.py` | L3 | 多操作者一致性监测、时间漂移分析（滚动窗口）、场景×操作者覆盖矩阵 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）；`pip install -r requirements.txt` 为空清单占位。

## 3. 快速运行

```bash
cd 第2章-真实场景数据采集工位搭建
python demo_capture_acceptance.py --n 100 --out session.json        # L1：生成并验收
python engineering_capture_acceptance.py --input session.json --out-dir out
python advanced_capture_ops.py --input session.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：
```text
会话共 100 条：成功 90 / 失败 10 / 场景 3 / 通道缺失 0
  [PASS] 总数>=100
  [PASS] 成功率>=90%
  [PASS] 失败样本>=10%
  [PASS] 场景覆盖>=3
  [PASS] 通道缺失<=2%
>>> 验收结论： 通过，可进入规模化采集
```

L2（关键段）：
```text
有效记录=100 成功=90 失败=10 场景=3 操作者=2
  [PASS] 成功率: 0.9 (需>=0.9)
  [PASS] 失败样本占比: 0.1 (需>=0.1)
验收结论: PASS-可规模化采集
失败原因: {'未填写': 10}
```

L3：
```text
操作者成功率: {'bob': 0.9149, 'alice': 0.8868} 告警: False
漂移头尾差: 0.0 告警: False
覆盖欠佳格: 0
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| min_episodes | 100 | 首100条验收 | 长任务可下调但需统计意义 |
| min_success_rate | 0.90 | 通用 | 精密任务需 0.95+ |
| min_failure_ratio | 0.10 | 防过拟合"顺利场景" | 难任务按第5章上调 |
| min_scenes | 3 | 多样性 | 单场景产品也需 ≥1 但应补干扰变体 |
| CONSISTENCY_MAX_GAP | 0.15 | 多操作者轮换 | 单人采集不适用 |
| DRIFT_WINDOW/MAX_DROP | 20 条 / 0.10 | 疲劳监控 | 采集顺序必须=真实时间顺序 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 验收永远 FAIL | 成功率 89.9% 差一点点 | 先查失败原因归因（L2 报告），修 SOP 而非调阈值 |
| 2. 失败原因全是"未填写" | 采集端没记录失败原因 | 采集界面强制下拉选择，字段必填 |
| 3. 操作者 A 明显比 B 差 | 未做一致性测试 | L3 告警后安排 20 条一致性测试与 SOP 复训 |
| 4. 后 50 条成功率下滑 | 疲劳/流程松懈 | L3 漂移窗口定位起点，轮换操作者 |
| 5. 通道缺失静默发生 | 采集端无实时校验 | channels_ok 字段由采集端实时写入（第2章实时体检） |

## 7. 改造指南

- 真实采集站：把采集端每条 Trial 追加 `failure_reason` 与 `channels_ok` 后写入同一 JSON 即可复用 L2；
- 自定义门禁：`--config config.json` 覆盖任一 GateConfig 字段；
- 接入流水线：L2 退出码接 CI；L3 报告接"采集运营看板"。

## 8. 进阶方向

把本包与第3章时间对齐、第4章清洗规则打通：采集会话验收通过 → 自动触发对齐与清洗流水线，形成"采-验-洗-发"闭环。
