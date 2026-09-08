# 第14章《感知（下）：深度估计与 6D 位姿》代码落地包

> 配套公众号文章：【具身智能全栈工程·第14章】2D 框不够用了
> 落地目标：针孔投影/反投影、深度图体检（无效/飞点）、检测框点云裁剪、桌面去除+位姿 sanity。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_pinhole.py` | L1 | 内参投影与深度反投影最小实现（往返误差 ~1e-17 m） |
| `engineering_depth_qa.py` | L2 | 深度图质量体检：无效占比/孤立飞点统计/深度范围；bbox→3D 点云裁剪与质心（含样例生成） |
| `advanced_plane_pose_sanity.py` | L3 | 3×3 中值滤波（修飞点）→ RANSAC 桌面去除 → 物体 3D 包围盒 vs CAD 期望尺寸 → pose-ok/reject |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。真实点云处理可换 Open3D/OpenCV（README 附接入点）。

## 3. 快速运行

```bash
cd 第14章-机器人感知模块下-深度估计与6D位姿
python demo_pinhole.py
python engineering_depth_qa.py --make-sample sample
python engineering_depth_qa.py --input sample/depth.json --bbox 18 14 12 12 --out-dir out
python advanced_plane_pose_sanity.py --input sample/depth.json \
    --bbox 8 4 32 36 --expected 16 16 0 --out-dir out
```
> bbox 必须包含桌面背景，RANSAC 才能分离桌面与物体；高度维度单视角不可观测，期望填 0 即跳过。

## 4. 标准运行结果（本机实测）

L1：3D→像素→反投影误差 5e-17 m（公式闭环正确）
L2：无效占比 1.8%、飞点 25、裁剪点 138，点云中心约 (-0.8,-5.9,397.8)mm
L3：
```text
桌面内点 1012，物体点 140
物体实测尺寸(mm): [14.7, 14.7, 0.0] 期望: [16.0, 16.0, 0.0]
判定: pose-ok
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| fx/fy | 300（样例） | 以标定内参为准 | 禁止沿用样例值上真机 |
| 飞点阈值 | 80mm vs 邻域中值 | 深度相机 | 近距任务收紧 |
| RANSAC 迭代 | 80 | 桌面场景 | 点云>10k 用 PCL/Open3D |
| 平面阈值 | 12mm | 桌面 | 不平桌面需分段 |
| 期望尺寸=0 | 跳过该维 | 单视角不可观测 | 多视角时仍应校验高度 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. bbox 只框物体，桌面去不掉 | RANSAC 无平面样本 | bbox 扩大含桌面（本包实测教训） |
| 2. 实测尺寸被飞点撑大 | 未滤波 | L3 先 3×3 中值滤波 |
| 3. 反投影尺寸对不上 | 内参不是标定值 | 用第2章标定内参 |
| 4. 单视角高度乱报 | 高度不可观测 | 期望=0 跳过该维 |
| 5. 反光/透明深度全是洞 | 主动深度失效 | 多视角/RGB 位姿补盲（文章） |

## 7. 改造指南

- 真实相机：把 depth_mm 换成你的深度图（uint16 mm），内参用标定文件；
- Open3D 替换：RANSAC 平面可用 `segment_plane`，点云裁剪用 `select_by_index`；
- 接第18章抓取：pose sanity 通过后输出 object_center_mm 给抓取点生成。

## 8. 进阶方向

多视角融合补高度/背面；把 sanity 判定接入第43章监控（每帧检测失败/尺寸异常告警）；对称物体位姿用 4/5D 表示降低旋转歧义。
