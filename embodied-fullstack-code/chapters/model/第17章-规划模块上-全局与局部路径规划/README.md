# 第17章《全局与局部路径规划》代码落地包

> 配套文章：【具身智能全栈工程·第17章】"全局会绕、局部会卡"

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_astar.py | L1 | 栅格 A*（4 邻域+heapq）11 步路径 |
| engineering_path_planner.py | L2 | 代价地图：膨胀/A*(8邻域)/Dijkstra/平滑，样例窄缝地图 |
| advanced_dwa_sim.py | L3 | DWA 速度采样：碰撞淘汰+打分，卡死触发 replan |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_astar.py
python engineering_path_planner.py --make-sample sample
python engineering_path_planner.py --map sample/map.json --start 0 0 --goal 4 8 --algo astar --inflate 0 --out-dir out
python engineering_path_planner.py --map sample/map.json --start 0 0 --goal 4 8 --algo dijkstra --inflate 0 --out-dir out
python advanced_dwa_sim.py
```

## 4. 标准运行结果（本机实测）

L1：A* 路径 11 步，扩展 23 节点

L2：
```text
astar:    路径 9 -> 平滑 5 步, 扩展 9 节点
dijkstra: 路径 9 -> 平滑 5 步, 扩展 47 节点
```

L3：DWA 障碍前连续无进展 -> step31 触发全局重规划

> 教学点：样例墙缝仅 1 格，--inflate 1 会把缝堵死（膨胀过大=过不去）。

## 5. 参数白皮书

| 参数 | 默认 | 适配 | 禁忌 |
| inflate | 1 | 机器人半径栅格化 | 窄门按区域降膨胀 |
| 邻域 | 8 | 全局 | 阿克曼需运动学约束 |
| DWA 分辨率 | v0.1/w0.4 | 教学仿真 | 真机按控制器 |
| 卡死阈值 | 连续5次 v<0.05 | 触发重规划 | 过小误触发 |

## 6. Top5 踩坑

1. A* 找不到路但 Dijkstra 找到：过期节点判断误用 f 值（本包修复）。
2. 膨胀后窄门全堵：分区域膨胀。
3. 局部原地抽搐：加 stuck 计数 replan。
4. 路径绕远：检查代价层。
5. 平滑后穿墙：平滑后重跑碰撞校验。

## 7. 改造指南

- 真实地图 occupancy grid 存 map.json；
- ROS2/Nav2：path 转 nav_msgs/Path；
- 接第16章：预测假设注入局部代价再跑 DWA。

## 8. 进阶方向：Hybrid A*、TEB/MPC、卡死重规划接入第41章状态机。
