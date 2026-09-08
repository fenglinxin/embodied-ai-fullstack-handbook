# 第7章《领域专属数据集构建方法论》代码落地包

> 配套公众号文章：【具身智能全栈工程·第7章】别抄别人的数据集
> 落地目标：任务树→场景矩阵规划、数据卡生成器、数据集版本注册与就绪度评分。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_dataset_planner.py` | L1 | 从业务场景样例生成 任务树叶子×变体矩阵，输出采集配额与 MVP 建议 |
| `engineering_dataset_builder.py` | L2 | Episode 目录打包：必填元数据校验、数据卡（概览/授权/分布/质量/切分/已知问题/复现）、场景级防泄漏切分 |
| `advanced_data_registry.py` | L3 | 数据集注册表：四维就绪度评分（覆盖/成功率/失败占比/元数据）、版本对比、下一轮采集建议 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第7章-领域专属数据集构建方法论
python demo_dataset_planner.py --out collection_plan.json            # L1
# L2：复用第1章演示数据
python ..\..\data\第1章-具身数据全链路地基\demo_data_pipeline.py --make-demo-data demo_data
python engineering_dataset_builder.py --data-dir demo_data --out-dir out \
    --dataset-name domain-pick-v0
python advanced_data_registry.py --registry reg --add out/data_card.json --tag v0.1
```

## 4. 标准运行结果（本机实测）

L1：
```text
场景: 仓库B区料箱搬运
  grasp: 18 个变体组合 x 10 条 = 180 条
  place: 2 个变体组合 x 10 条 = 20 条
完整矩阵合计约 200 条
建议：先做 MVP 30 条（1技能x3变体x10条）跑通闭环
```

L2：
```text
数据卡: domain-pick-v0 3条/任务1/场景3 成功率100%
切分: {'train': 1, 'val': 1, 'test': 1} | 元数据问题: 0
```

L3：
```text
注册 v0.1: 就绪度 0.7 (collect-more)
较上一版: (首个版本无对比)
建议: 补采欠覆盖组合与失败样本后再注册
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| quota_per_combo | 10 | 每变体起点 | 难任务上调到 20+ |
| MVP 规模 | 1技能×3变体×10 | 验证设计 | 别跳过直接全量 |
| split_ratios | 80/10/10 | 通用 | 小数据按场景留出 |
| 就绪度阈值 | 0.75 | 训练放行 | 量产任务要求更高 |
| 覆盖目标 | 2 任务×2 场景 | 简版 | 按第5章矩阵自定义 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 数据卡只有概览没分布 | 只填了 overview | L2 自动统计 task/scene/success 分布 |
| 2. 切分泄漏 | 按文件随机切 | L2 按场景整体切分 |
| 3. 换了本体没法溯源 | 数据卡无复现字段 | 卡片含 pipeline_version+checksum |
| 4. 就绪度虚高 | 只看总量 | L3 四维评分含失败占比/元数据 |
| 5. 版本越积越乱 | 无注册表 | L3 registry 带 tag + diff |

## 7. 改造指南

- 真实业务：把 sample_scenario() 换成你的 任务树/变体矩阵 JSON；
- 数据卡加字段：在第7章规范基础上追加"授权记录/脱敏证书/清洗规则版本"（接第6章）；
- 资产地图：L3 registry 目录即团队数据资产地图，可挂到 Git 仓库版本管理。

## 8. 进阶方向

把 L3 就绪度接入第12章迭代闭环：就绪度不足自动生成"补采任务书"；多个版本卡做回归对比，量化"这版数据比上版好在哪"。
