# 第3章《多模态数据融合与时间对齐》代码落地包

> 配套公众号文章：【具身智能全栈工程·第3章】RGB、点云、关节角、力传感为什么总是"打架"？
> 落地目标：时间同步三方案中的"软件打戳+离线插值"，以及"LED 事件实测延迟"的代码化。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_time_align.py` | L1 | 合成 30Hz/100Hz 通道，对比 RAW/最近邻/线性插值读取误差，并生成标准 Episode 目录 |
| `engineering_time_align.py` | L2 | 以主通道为时间轴批量重采样（nearest/linear，支持向量值），输出对齐 JSON+间隔统计报告 |
| `advanced_delay_estimator.py` | L3 | 互相关估计恒定延迟（事件脉冲法）、补偿建议、补偿前后抖动体检 |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。

## 3. 快速运行

```bash
cd 第3章-多模态数据融合与时间对齐
# L1：误差对比 + 生成 3 条含 30/35/40ms 延迟的 Episode
python demo_time_align.py --make-episodes demo_data

# L2：以 joint 为主通道线性重采样 rgb/action
python engineering_time_align.py --data-dir demo_data --master joint --method linear --out-dir out

# L3：互相关估计每条延迟并给出补偿建议
python advanced_delay_estimator.py --data-dir demo_data --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：
```text
方法      平均误差    最大误差
raw       0.0795      0.1462
nearest   0.0696      0.1304
linear    0.0708      0.1225
结论：动作内容延迟 35ms 时，RAW 读取误差最大，线性插值最接近真值
```

L2（节选）：
```text
对齐完成: 成功 3 / 失败 0 (主通道=joint, linear)
  {'episode_id': 'ep-0000', 'gap_mean_ms': {'rgb': 8.4, 'action': 0.0}, ...}
```
> 注：action 与 joint 时间轴一致后 gap≈0；内容延迟由 L3 检测。

L3：
```text
ep-0000: 估计延迟 30.0ms -> 需要补偿
ep-0001: 估计延迟 40.0ms -> 需要补偿
ep-0002: 估计延迟 40.0ms -> 需要补偿
需补偿: 3/3
```
（真值 30/35/40ms，整步量化误差 ≤10ms——对应"实测延迟，不信纸面数字"。）

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| master 主通道 | joint | 操作任务高频本体通道 | 视觉主导任务可改 rgb 需先评估 |
| method | linear | 连续量（关节/末端） | 深度/点云建议 nearest 防插出假点 |
| 网格 FPS（L3） | 100Hz | 关节级同步 | 力觉任务需 500-1000Hz |
| max_lag | 30 步 | 常量延迟估计 | 大抖动场景先用事件法分段 |
| 时间戳单位 | 秒 float | 统一 | 禁止混用 ms/ns |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 插值后动作"假平滑" | 对动作通道做线性插值 | 动作通道保留原始采样，只插观测（代码改为 master=joint 后仍会插 action——生产版应把动作标记 no_interp） |
| 2. 估计延迟=0 | 信号平滑且无事件 | 加 LED/敲击事件再互相关（demo 已内置 spike） |
| 3. 全通道 gap 超大 | 时间戳用了墙上时钟 | 采集端改单调时钟，见 L2 非单调检查 |
| 4. depth 插出假点 | nearest 策略错误 | depth/点云用 nearest |
| 5. 换驱动后延迟变了 | 未重测 | 每次驱动/曝光变更重跑 L3 并更新补偿表 |

## 7. 改造指南

- 真实通道：把采集端 JSON 的 channels 对齐为 `{"ts":[...],"values":[...]}`（向量值支持逐分量插值）；
- 力觉 500-1000Hz 场景：L3 `--fps 1000`，max_lag 相应调大；
- 接入第1章数据包：先跑本包 L2，再送 `engineering_data_pipeline.py` 体检。

## 8. 进阶方向

把 L3 估计出的每通道延迟写入数据卡标定文件（版本化）；在线对齐时直接查表补偿 + 残余抖动门禁，形成"标定-对齐-体检"闭环。
