# 第11章《数据管道自动化搭建》代码落地包

> 配套公众号文章：【具身智能全栈工程·第11章】别再用 U 盘拷贝管数据
> 落地目标：DAG 执行、幂等重跑、断点续跑、checksum 血缘与可复现验证。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_pipeline_dag.py` | L1 | ingest→clean→quality 三节点 DAG 概念演示（依赖递归、缓存思想） |
| `engineering_pipeline_runner.py` | L2 | 文件级 DAG：拓扑排序、config_hash 幂等 SKIP、产物 checksum、run_report 血缘 |
| `advanced_pipeline_resume.py` | L3 | 故障断点续跑（--fail-at 注入故障）、SKIP 已成功节点、双目录 checksum 一致=可复现 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第11章-数据管道自动化搭建
python demo_pipeline_dag.py
python engineering_pipeline_runner.py --work-dir out     # 首次 RUN
python engineering_pipeline_runner.py --work-dir out     # 幂等 SKIP
python advanced_pipeline_resume.py --work-dir out1 --fail-at clean  # 模拟故障
python advanced_pipeline_resume.py --work-dir out1                  # 续跑
python advanced_pipeline_resume.py --work-dir out2                  # 干净重跑对比
```

## 4. 标准运行结果（本机实测）

L1：ingest→clean→quality 顺序执行，quality score=0.667
L2 首次：`{'ingest':'RUN','clean':'RUN','quality':'RUN'}`
L2 二次：`{'ingest':'SKIP','clean':'SKIP','quality':'SKIP'}`（幂等命中）
L3 故障→续跑：
```text
（fail）管道中断: 模拟故障: clean 阶段异常（修复后重跑即可续点）
（resume）节点: {'ingest': 'SKIP', 'clean': 'RUN', 'quality': 'RUN'}
checksum: ingest=857cc848de64 clean=c721a53a0bf6 quality=347d3e813c79
（干净重跑 out2）checksum 与 out1 完全一致 = 可复现 ✅
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 作用 | 禁忌 |
| --- | --- | --- | --- |
| NODE_VERSION | 1.0.0 | 节点代码版本（改逻辑必须升版本） | 忘升版=假幂等 |
| config_hash | 节点+版本+参数 | SKIP 判定 | 排除时间戳等随机量 |
| checksum | sha256[:12] | 可复现/血缘 | 输出含随机时先固定 seed |
| --force | 关 | 强制重跑 | CI 常规禁用 |
| work_dir 产物 | node.json | 断点续跑 | 禁止人工编辑 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 重跑结果不一样 | 节点含隐藏状态/随机 | 固定 seed；config_hash 覆盖参数 |
| 2. 改代码后 SKIP 了 | 忘升 NODE_VERSION | 每次改函数体升版本号 |
| 3. 断点续跑数据对不上 | 下游读错上游输出键 | 依赖按节点名取（本包开发中真实修复） |
| 4. 覆盖式写产物 | 原地写 | 版本目录+校验和 |
| 5. 故障后手工补跑乱套 | 无续跑机制 | L3 resume：已成功节点自动 SKIP |

## 7. 改造指南

- 接入真实流水线：把 TASKS 的 run 函数替换为 清洗/去重/脱敏/打包 各章代码包入口，输出统一 JSON 即可；
- 企业级：节点数>10 时把本包 DAG 迁移到 Dagster/Prefect（编排层），保留 config_hash/checksum 语义；
- 血缘：run_report 对接 MLflow/数据资产地图（第7章 registry）。

## 8. 进阶方向

加"发布门禁"节点：质量分/脱敏证书/切分校验不过则整体 FAIL（第9/6章产物做输入）；做增量+定期全量双轨，历史 bug 可全量重建版本。
