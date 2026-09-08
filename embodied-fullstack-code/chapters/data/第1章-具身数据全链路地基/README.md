# 第1章《具身数据全链路地基》代码落地包

> 配套公众号文章：【具身智能全栈工程·第1章】机器人"越训越笨"？先别换模型，看看你的数据
> 本包把"数据是什么/六步流水线/质量打分"落地为可运行代码，实现 **能看懂 → 能跑通 → 能改造 → 能上项目**。

## 1. 文件说明与三层结构

| 文件 | 层 | 定位 |
| --- | --- | --- |
| `demo_data_pipeline.py` | L1 极简 Demo | 纯标准库：合成 Episode + 通道/时间戳/同步体检 |
| `engineering_data_pipeline.py` | L2 工业工程版 | 五维质量打分、硬门禁剔除、JSON 报告、CI 退出码 |
| `advanced_quality_engine.py` | L3 高阶优化版 | 去重候选、任务×场景覆盖矩阵、场景级防泄漏切分、数据卡 |
| `requirements.txt` | 依赖 | 零第三方依赖（Python 3.9+ 标准库） |

## 2. 环境依赖与安装

- Python **3.9+**（本包在 3.13 实测通过）；无需 CUDA/第三方库
- 一键安装：`pip install -r requirements.txt`（当前为空清单，仅为流水线占位，后续接入 numpy/opencv 时在此追加）

## 3. 快速运行（复制即跑）

```bash
cd 第1章-具身数据全链路地基

# L1：自动生成演示数据（3 条，含 1 条脏数据）并体检
python demo_data_pipeline.py --make-demo-data demo_data

# L2：五维质量打分 + 门禁（输出 out/quality_report.json）
python engineering_data_pipeline.py --data-dir demo_data --out-dir out

# L3：去重/覆盖/防泄漏切分/数据卡（输出 out/advanced_report.json）
python advanced_quality_engine.py --data-dir demo_data --out-dir out
```

## 4. 标准运行结果示例（本机 3.13.3 实测）

### L1 输出（节选）
```text
==============================================================
episode_id success 同步ms    结论
--------------------------------------------------------------
ep-0000   True    3.33     可入训练集
ep-0001   True    346.67   丢弃/返工
    [HARD] 时间戳非单调(违规1处)
    [HARD] 观测-动作错位347ms>50ms
    [soft] 黑帧占比8%>5%
ep-0002   True    3.33     可入训练集
--------------------------------------------------------------
汇总: 3 条，可入训练集 2 条。
```

### L2 输出
```text
Episode 总数=3 保留=2 剔除=1
加权质量分=0.96 结论=review
报告: ...\out\quality_report.json
```
> 退出码 1 = 门禁未通过（存在剔除项），可用于 CI 拦截；清洗后可复跑验证。

### L3 输出
```text
数据卡: 3条/任务1/场景3 成功率100%
重复候选组: 0 组 (0 条冗余)
欠覆盖组合: 0 个
场景级切分: train=1 val=1 test=1
门禁: review
```

## 5. 核心参数白皮书

| 参数 | 代码位置 | 默认值/工程起点 | 适配场景 | 禁忌场景 |
| --- | --- | --- | --- | --- |
| 必需通道 | `REQUIRED_CHANNELS` | rgb/joint/action | 桌面操作 | 只做导航时需改为 lidar/odom |
| 同步错位阈值 | `sync_gap_ms` | 50ms | 常规操作 | 高速动态抓取需收紧到 10–20ms |
| 黑帧占比 | `black_ratio_max` | 5% | 固定工位采集 | 光照频繁变化场景先修曝光再降阈值 |
| 最短时长 | `min_duration_s` | 0.3s | 通用 | 长任务分段时单独设置 |
| 五维权重 | `weights` | 25/30/15/20/10 | 第1章默认 | 力控任务应提高正确性权重 |
| 多样性期望 | expected_tasks/scenes/objects | 1/1/1 | 教学演示 | 项目按第5章场景矩阵填写 |
| 切分比例 | DEFAULT_SPLIT | train/val/test=80/10/10 | 通用 | 小数据(<100条)建议按场景留出法 |

## 6. Top5 高频踩坑与一键修复

| 报错/现象 | 根因 | 一键修复 |
| --- | --- | --- |
| 1. `json.JSONDecodeError` | 采集端写了非 UTF-8 或损坏 JSON | 采集端统一 `encoding="utf-8"`；L2 建议增加 try/except 单文件跳过并记日志 |
| 2. 全部 Episode 被判"丢弃" | 时间戳字段为字符串或非单调 | 采集驱动统一 `float` 硬件时间戳；`ts = [float(x) for x in ts]` 后重跑 |
| 3. 同步错位全部超 50ms | rgb 30Hz 与 action 100Hz 未插值对齐 | 以 action 主时间轴对 rgb 做最近邻/线性插值后再入库（第3章代码包提供） |
| 4. 门禁永远 review | 演示数据故意含脏样本 | 清洗后重跑；或用 `--config` 关闭 `hard_drop` 仅标记 |
| 5. L3 场景切分 val/test 为空 | 场景数 < 3 | 增加场景多样性（第5章场景矩阵）；小样本时改用留一场景验证 |

## 7. 二次开发与项目适配指南

1. **接真实采集数据**：把第2/3章采集产物转换为本包输入格式——每个 `episode_id.json` 含 `channels.<name>.ts`（秒，float）与可选 `black/cmds` 字段；`success` 必须存在。
2. **自定义体检规则**：在 `engineering_data_pipeline.py` 的 `inspect_episode()` 中追加规则函数（如深度 NaN 率、力传感器零漂），并接入 `issues_hard/issues_soft`。
3. **接入 CI 流水线**：L2 退出码 0/1/2 可直接进 GitLab CI/GitHub Actions；`quality_report.json` 可对接第11章数据管道。
4. **升级数据卡**：L3 `build_data_card()` 增加"授权状态/脱敏记录/清洗规则版本"字段即满足第7章数据卡规范。
5. **加大规模**：Episode 上万后，把 JSON 批量读写换为 RLDS/WebDataset（第11章），本包规则函数可直接复用。

## 8. 进阶迭代方向（下一阶段改造）

- 把同步体检升级为"插值+延迟补偿"（第3章）；把去重升级为 DTW/嵌入聚类（第5章）；
- 把质量分接入训练加权采样（第12章"低分难例适度保留"）；
- 把本包 CI 化进第11章数据管道，形成 采→检→洗→发 自动闭环。
